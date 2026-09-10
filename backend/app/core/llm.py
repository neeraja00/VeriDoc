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

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self._model_name = model_name or settings.GEMINI_MODEL
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
                # Protect against local corporate/antivirus SSL proxy verification issues on Windows
                http_opts = types.HttpOptions(client_args={"verify": False})
                self._client = genai.Client(api_key=self.api_key, http_options=http_opts)
            except Exception:
                self._client = genai.Client(api_key=self.api_key)
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

        try:
            client = self._get_client()
            response = client.models.generate_content(
                model=self._model_name,
                contents=user_content,
                config={
                    "system_instruction": system_instruction,
                    "temperature": 0.1,
                }
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini API generation error: {e}")
            raise RuntimeError(f"Gemini API error: {str(e)}") from e

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
        # Fall back to mock if Gemini key is completely absent and user hasn't configured it yet
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set. Using MockLLMProvider for offline mode.")
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
