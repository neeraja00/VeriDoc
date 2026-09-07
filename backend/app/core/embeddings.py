"""Pluggable embeddings provider module supporting Sentence Transformers, Gemini, and mock fallbacks."""
from abc import ABC, abstractmethod
from typing import List
import math
import hashlib
from backend.app.config import settings


class BaseEmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a batch of documents."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Generates embedding for a single query."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector dimensionality."""
        pass


class SentenceTransformerEmbeddingProvider(BaseEmbeddingProvider):
    """Local Sentence Transformers embeddings (e.g. all-MiniLM-L6-v2)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._dimension = 384

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            if hasattr(self._model, "get_embedding_dimension"):
                self._dimension = self._model.get_embedding_dimension()
            else:
                self._dimension = self._model.get_sentence_embedding_dimension()
        return self._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        model = self._get_model()
        embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        model = self._get_model()
        embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return embedding.tolist()

    @property
    def dimension(self) -> int:
        if self._model is None:
            return 384
        return self._dimension


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """Google Gemini Embeddings provider (text-embedding-004)."""

    def __init__(self, api_key: str = None, model_name: str = "text-embedding-004"):
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini embeddings.")
        self.model_name = model_name
        self._client = None
        self._dimension = 768

    def _get_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        client = self._get_client()
        result = client.models.embed_content(
            model=self.model_name,
            contents=texts,
        )
        return [e.values for e in result.embeddings]

    def embed_query(self, text: str) -> List[float]:
        client = self._get_client()
        result = client.models.embed_content(
            model=self.model_name,
            contents=text,
        )
        return result.embeddings[0].values

    @property
    def dimension(self) -> int:
        return self._dimension


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic hash-based normalized vector embedding for offline testing."""

    def __init__(self, dimension: int = 128):
        self._dim = dimension

    def _embed_text(self, text: str) -> List[float]:
        vec = [0.0] * self._dim
        words = text.lower().split()
        if not words:
            return vec

        for word in words:
            # Deterministic hash to bucket
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            vec[idx] += 1.0

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_text(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed_text(text)

    @property
    def dimension(self) -> int:
        return self._dim


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Stub for OpenAI Embeddings."""

    def __init__(self, api_key: str = None):
        raise NotImplementedError(
            "OpenAI embedding provider is not configured. "
            "Please set OPENAI_API_KEY in your .env file to enable OpenAI embeddings."
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass

    def embed_query(self, text: str) -> List[float]:
        pass

    @property
    def dimension(self) -> int:
        return 1536


# Singleton cache for providers
_PROVIDER_CACHE = {}


def get_embedding_provider(provider_name: str = None) -> BaseEmbeddingProvider:
    """Factory function returning the configured embedding provider singleton."""
    provider = (provider_name or settings.EMBEDDING_PROVIDER).lower().strip()

    if provider in _PROVIDER_CACHE:
        return _PROVIDER_CACHE[provider]

    if provider == "sentence-transformers":
        instance = SentenceTransformerEmbeddingProvider(model_name=settings.EMBEDDING_MODEL)
    elif provider == "gemini":
        if not settings.GEMINI_API_KEY:
            import logging
            logging.getLogger(__name__).warning(
                "GEMINI_API_KEY is not set for Gemini embeddings. Using MockEmbeddingProvider for low-memory mode."
            )
            instance = MockEmbeddingProvider()
        else:
            instance = GeminiEmbeddingProvider()
    elif provider == "mock":
        instance = MockEmbeddingProvider()
    elif provider == "openai":
        instance = OpenAIEmbeddingProvider()
    else:
        raise ValueError(f"Unsupported embedding provider: '{provider}'. Supported: sentence-transformers, gemini, mock")

    _PROVIDER_CACHE[provider] = instance
    return instance
