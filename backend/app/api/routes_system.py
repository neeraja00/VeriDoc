"""API routes for system diagnostics and configuration."""
from fastapi import APIRouter
from backend.app.config import settings
from backend.app.core.vector_store import get_vector_store

router = APIRouter(prefix="/api/system", tags=["System"])


@router.get("/health")
def get_system_health():
    """Returns vector store health, document counts, and active providers."""
    vector_store = get_vector_store()
    count = vector_store.count()
    docs = vector_store.get_indexed_documents()

    has_gemini_key = bool(settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("your_"))
    has_openai_key = bool(settings.OPENAI_API_KEY)
    has_anthropic_key = bool(settings.ANTHROPIC_API_KEY)

    return {
        "status": "healthy",
        "vector_store": {
            "type": "ChromaDB",
            "persist_directory": settings.CHROMA_PERSIST_DIR,
            "total_chunks": count,
            "total_documents": len(docs),
        },
        "providers": {
            "llm": {
                "configured": settings.LLM_PROVIDER,
                "active_model": settings.GEMINI_MODEL if settings.LLM_PROVIDER == "gemini" else "mock",
                "has_gemini_key": has_gemini_key,
                "has_openai_key": has_openai_key,
                "has_anthropic_key": has_anthropic_key,
            },
            "embeddings": {
                "configured": settings.EMBEDDING_PROVIDER,
                "model": settings.EMBEDDING_MODEL,
            },
        },
        "hyperparameters": {
            "chunk_size": settings.DEFAULT_CHUNK_SIZE,
            "chunk_overlap": settings.DEFAULT_CHUNK_OVERLAP,
            "top_k": settings.DEFAULT_TOP_K,
            "similarity_threshold": settings.SIMILARITY_SCORE_THRESHOLD,
        }
    }
