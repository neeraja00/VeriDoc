"""Pydantic schemas for document models and responses."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    filename: str
    file_type: str
    file_size_bytes: int
    total_pages: int
    total_characters: int
    uploaded_at: str


class ChunkInfo(BaseModel):
    chunk_id: str
    chunk_index: int
    page_number: int
    char_count: int
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentUploadResponse(BaseModel):
    success: bool
    filename: str
    file_type: str
    total_pages: int
    total_chunks: int
    total_characters: int
    message: str


class DocumentSummary(BaseModel):
    filename: str
    file_type: str
    total_chunks: int
    file_size_bytes: int
    uploaded_at: str


class DocumentListResponse(BaseModel):
    documents: List[DocumentSummary]
    total_documents: int
    total_chunks: int


class DocumentDeleteResponse(BaseModel):
    success: bool
    filename: str
    deleted_chunks: int
    message: str
