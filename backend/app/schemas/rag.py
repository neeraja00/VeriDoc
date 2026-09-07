"""Pydantic schemas for RAG query, retrieval, and answers."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="The user's question to answer from documents")
    top_k: Optional[int] = Field(default=None, ge=1, le=20, description="Number of context chunks to retrieve")
    score_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Relevance score threshold")
    document_filter: Optional[List[str]] = Field(default=None, description="Optional filter to specific document filenames")
    stream: bool = Field(default=False, description="Whether to stream response tokens")


class SourceCitation(BaseModel):
    document_name: str
    page_number: int
    chunk_index: int
    chunk_id: str
    similarity_score: float
    content: str = ""
    excerpt: str


class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[SourceCitation]
    total_sources_found: int
    llm_provider: str
    model_name: str
    is_grounded: bool
    processing_time_ms: float


class ContextRetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=4, ge=1, le=20)
    document_filter: Optional[List[str]] = None


class ContextRetrievalResponse(BaseModel):
    query: str
    retrieved_chunks: List[SourceCitation]
    total_retrieved: int
