"""VeriDoc AI Configuration and environment variables management."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # LLM Settings
    LLM_PROVIDER: str = "gemini"  # "gemini", "openai", "anthropic", "mock"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # Embedding Settings
    EMBEDDING_PROVIDER: str = "sentence-transformers"  # "sentence-transformers", "gemini", "mock"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Vector Store & Storage
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / "data" / "chroma_db")
    UPLOAD_DIR: str = str(BASE_DIR / "data" / "uploads")
    COLLECTION_NAME: str = "knowledge_assistant"

    # RAG Parameters
    DEFAULT_CHUNK_SIZE: int = 800
    DEFAULT_CHUNK_OVERLAP: int = 150
    DEFAULT_TOP_K: int = 4
    SIMILARITY_SCORE_THRESHOLD: float = 0.25

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

# Ensure required directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
