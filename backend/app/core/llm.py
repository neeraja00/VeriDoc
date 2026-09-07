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
2. NO HALLUCINATION: If the Context does not provide sufficient information to answer the question, state clearly and concisely:
   "I cannot find the answer to this question in the provided documents."
3. SOURCE CITATIONS: When providing facts, cite the source document and page number in parentheses (e.g. [Document.pdf, Page 1]).
4. CLARITY: Present the answer clearly, using bullet points or paragraphs where appropriate."""


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
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def generate_answer(
        self,
        question: str,
        citations: List[SourceCitation],
        context_block: str,
    ) -> str:
        if not citations or not context_block.strip():
            return "I cannot find the answer to this question in the provided documents."

        user_content = RAG_USER_PROMPT_TEMPLATE.format(
            context_block=context_block,
            question=question
        )

        try:
            client = self._get_client()
            response = client.models.generate_content(
                model=self._model_name,
                contents=user_content,
                config={
                    "system_instruction": RAG_SYSTEM_PROMPT,
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
    ) -> str:
        if not citations or not context_block.strip():
            return "I cannot find the answer to this question in the provided documents."

        # Extract words from question
        q_words = set(w.lower().strip("?,.!") for w in question.split() if len(w) > 3)
        context_lower = context_block.lower()

        # Check if question has semantic overlap with context
        has_overlap = any(w in context_lower for w in q_words)

        if not has_overlap:
            return "I cannot find the answer to this question in the provided documents."

        primary_source = citations[0]
        return (
            f"Based on {primary_source.document_name} (Page {primary_source.page_number}):\n"
            f"{primary_source.excerpt}\n\n"
            f"(Answer synthesized from {len(citations)} retrieved source chunks)"
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

    def generate_answer(self, question: str, citations: List[SourceCitation], context_block: str) -> str:
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

    def generate_answer(self, question: str, citations: List[SourceCitation], context_block: str) -> str:
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
