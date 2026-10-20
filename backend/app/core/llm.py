"""Pluggable LLM orchestrator with strict anti-hallucination prompt templates."""
from abc import ABC, abstractmethod
from typing import List, Optional
import logging
from backend.app.config import settings
from backend.app.schemas.rag import SourceCitation

logger = logging.getLogger(__name__)

RAG_SYSTEM_PROMPT = """You are VeriDoc AI, a precise, factual document verification and knowledge assistant.
Your mission is to answer user questions truthfully and accurately based EXCLUSIVELY on the provided document context.

CORE RULES:
1. STRICT GROUNDING: Use ONLY the facts directly mentioned in the Context below. Do NOT use outside world knowledge or extrapolate.
2. CITATION & SOURCES: Accurately cite facts referencing the specific source document and page number in parentheses (e.g. [Document.pdf, Page 1]).
3. NO HALLUCINATION: If the Context does not provide sufficient information to answer the question, state clearly and concisely:
   "I cannot find the answer to this question in the provided documents."
4. NO CROSS-DOCUMENT CONFUSION: Attribute facts clearly to their respective documents without conflating or confusing separate sources.
5. STRUCTURE & CLARITY: Present the answer clearly, using structured sections or bullet points where appropriate."""

RAG_ISOLATED_SYSTEM_PROMPT_TEMPLATE = """You are VeriDoc AI, running in STRICT SINGLE-DOCUMENT ISOLATED MODE.
You are evaluating user questions EXCLUSIVELY against the selected document: '{target_document}'.

CORE RULES:
1. TARGET DOCUMENT EXCLUSIVITY: Your answer must be derived SOLELY and STRICTLY from '{target_document}'.
2. ZERO MERGING / NO CROSS-TALK: Under NO circumstances should you include, cite, mention, or merge information or facts from any other documents.
3. ABSENCE OF INFORMATION: If the requested information is not explicitly found in '{target_document}', state clearly:
   "The selected document '{target_document}' does not contain information to answer this question."
4. CITATIONS: Always cite the exact page and chunk from '{target_document}' (e.g. [{target_document}, Page X])."""


RAG_USER_PROMPT_TEMPLATE = """Context from uploaded documents:
{context_block}

User Question: {question}

Answer based strictly on the context above:"""


class BaseLLMProvider(ABC):
    """Abstract interface for LLM backends."""

    @abstractmethod
    def generate_answer(
        self,
        question: str,
        citations: List[SourceCitation],
        context_block: str,
        target_document: Optional[str] = None,
    ) -> str:
        """Generates a grounded answer from the question and retrieved context."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the underlying LLM model."""
        pass


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini LLM provider using the google-genai SDK."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        verify_ssl: Optional[bool] = None,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self._model_name = model_name or settings.GEMINI_MODEL
        self._verify_ssl = settings.VERIFY_SSL if verify_ssl is None else verify_ssl
        self._client = None

    def _get_client(self):
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Please add GEMINI_API_KEY to your .env file."
            )
        if self._client is None:
            from google import genai
            from google.genai import types
            try:
                # SSL verification enabled by default. Can be disabled via VERIFY_SSL=false for local proxy setups.
                http_opts = types.HttpOptions(client_args={"verify": self._verify_ssl})
                self._client = genai.Client(api_key=self.api_key, http_options=http_opts)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client (verify_ssl={self._verify_ssl}): {e}")
                raise RuntimeError(
                    f"Failed to initialize Gemini client with VERIFY_SSL={self._verify_ssl}: {e}"
                ) from e
        return self._client

    def generate_answer(
        self,
        question: str,
        citations: List[SourceCitation],
        context_block: str,
        target_document: Optional[str] = None,
    ) -> str:
        if not citations or not context_block.strip():
            if target_document:
                return f"The selected document '{target_document}' does not contain information to answer this question."
            return "I cannot find the answer to this question in the provided documents."

        user_content = RAG_USER_PROMPT_TEMPLATE.format(
            context_block=context_block,
            question=question
        )

        system_instruction = (
            RAG_ISOLATED_SYSTEM_PROMPT_TEMPLATE.format(target_document=target_document)
            if target_document
            else RAG_SYSTEM_PROMPT
        )

        import time
        from google.genai import errors

        models_to_try = [self._model_name]
        # If the requested model is gemini-3.8-flash, include gemini-3.6-flash as a resilience fallback on 503 spikes
        if self._model_name != "gemini-3.6-flash":
            models_to_try.append("gemini-3.6-flash")

        last_error = None
        for current_model in models_to_try:
            for attempt in range(2):
                try:
                    client = self._get_client()
                    response = client.models.generate_content(
                        model=current_model,
                        contents=user_content,
                        config={
                            "system_instruction": system_instruction,
                            "temperature": 0.1,
                        }
                    )
                    text = (response.text or "").strip()
                    if text:
                        return text
                except errors.APIError as e:
                    last_error = e
                    status_code = getattr(e, "code", getattr(e, "status_code", None))
                    # If high demand 503, pause briefly before retry
                    if status_code == 503 and attempt == 0:
                        time.sleep(1.0)
                        continue
                    # If 503 and we have a fallback model, break to try fallback
                    if status_code == 503:
                        break
                    # If 401 or 403, invalid key
                    if status_code in (401, 403):
                        raise RuntimeError(
                            f"Gemini API authentication failed ({status_code}): Invalid GEMINI_API_KEY. "
                            "Please check your API key in Google AI Studio and update your .env file."
                        ) from e
                    # If 404, unsupported/not found model
                    if status_code == 404:
                        if len(models_to_try) > 1 and current_model != models_to_try[-1]:
                            logger.warning(f"Model '{current_model}' returned 404, trying fallback '{models_to_try[-1]}'")
                            break
                        raise RuntimeError(
                            f"Gemini model '{current_model}' not found (404). "
                            "Please check GEMINI_MODEL in your .env file (recommended: gemini-3.6-flash)."
                        ) from e
                    # If 429, quota exhausted
                    if status_code == 429:
                        raise RuntimeError(
                            "Gemini API quota exhausted (429): Rate limit exceeded. "
                            "Please verify your API quota in Google AI Studio or retry in a few moments."
                        ) from e
                    raise RuntimeError(f"Gemini API error ({status_code}): {str(e)}") from e
                except Exception as e:
                    last_error = e
                    err_str = str(e)
                    if "RemoteProtocolError" in err_str or "Server disconnected" in err_str:
                        if attempt == 0:
                            time.sleep(0.5)
                            continue
                        raise RuntimeError(
                            f"Gemini API network connection dropped: {err_str}. Please retry your query."
                        ) from e
                    raise RuntimeError(f"Gemini API generation error: {err_str}") from e

        # If all attempts and fallbacks were exhausted
        logger.error(f"Gemini API generation failed: {last_error}")
        raise RuntimeError(
            f"Gemini API service temporarily unavailable: {str(last_error)}. "
            "The model experienced high demand spikes. Please try again."
        ) from last_error

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model_name


class MockLLMProvider(BaseLLMProvider):
    """
    Mock LLM provider for deterministic offline testing and CI environments.
    Checks whether key terms from the question exist in the context block.
    """

    def __init__(self, model_name: str = "mock-grounded-rag"):
        self._model_name = model_name

    def generate_answer(
        self,
        question: str,
        citations: List[SourceCitation],
        context_block: str,
        target_document: Optional[str] = None,
    ) -> str:
        if not citations or not context_block.strip():
            if target_document:
                return f"The selected document '{target_document}' does not contain information to answer this question."
            return "I cannot find the answer to this question in the provided documents."

        # Extract words from question
        q_words = set(w.lower().strip("?,.!") for w in question.split() if len(w) > 3)
        context_lower = context_block.lower()

        # Check if question has semantic overlap with context
        has_overlap = any(w in context_lower for w in q_words)

        if not has_overlap:
            if target_document:
                return f"The selected document '{target_document}' does not contain information to answer this question."
            return "I cannot find the answer to this question in the provided documents."

        primary_source = citations[0]
        prefix = f"[Document Scope: {target_document}]\n" if target_document else ""
        return (
            f"{prefix}Based on {primary_source.document_name} (Page {primary_source.page_number}):\n"
            f"{primary_source.excerpt}\n\n"
            f"(Answer grounded strictly in {len(citations)} chunks from {primary_source.document_name})"
        )

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return self._model_name


class OpenAILLMProvider(BaseLLMProvider):
    """Stub for OpenAI LLM provider."""

    def __init__(self, api_key: Optional[str] = None):
        raise NotImplementedError(
            "OpenAI LLM provider is not configured. "
            "Please configure OPENAI_API_KEY in your .env file to enable OpenAI models."
        )

    def generate_answer(self, question: str, citations: List[SourceCitation], context_block: str, target_document: Optional[str] = None) -> str:
        pass

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return "gpt-4o-mini"


class AnthropicLLMProvider(BaseLLMProvider):
    """Stub for Anthropic LLM provider."""

    def __init__(self, api_key: Optional[str] = None):
        raise NotImplementedError(
            "Anthropic LLM provider is not configured. "
            "Please configure ANTHROPIC_API_KEY in your .env file to enable Anthropic models."
        )

    def generate_answer(self, question: str, citations: List[SourceCitation], context_block: str, target_document: Optional[str] = None) -> str:
        pass

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return "claude-3-5-sonnet"


def get_llm_provider(provider_name: Optional[str] = None) -> BaseLLMProvider:
    """Factory function returning the configured LLM provider instance."""
    provider = (provider_name or settings.LLM_PROVIDER).lower().strip()

    if provider == "gemini":
        # Fall back to mock if Gemini key is completely absent or placeholder and user hasn't configured it yet
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.startswith("your_"):
            logger.warning("GEMINI_API_KEY not set or placeholder. Using MockLLMProvider for offline mode.")
            return MockLLMProvider()
        return GeminiLLMProvider()
    elif provider == "mock":
        return MockLLMProvider()
    elif provider == "openai":
        return OpenAILLMProvider()
    elif provider == "anthropic":
        return AnthropicLLMProvider()
    else:
        raise ValueError(
            f"Unsupported LLM provider: '{provider}'. Supported: gemini, mock, openai, anthropic"
        )
