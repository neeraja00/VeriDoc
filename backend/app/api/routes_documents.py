"""API routes for document upload, listing, previewing chunks, and deletion."""
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from backend.app.config import settings
from backend.app.core.document_loader import (
    DocumentLoader,
    DocumentLoaderError,
    UnsupportedFileTypeError,
    EmptyDocumentError,
    CorruptedFileError,
)
from backend.app.core.chunker import DocumentChunker
from backend.app.core.vector_store import get_vector_store
from backend.app.schemas.document import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentSummary,
    DocumentDeleteResponse,
    ChunkInfo,
)

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: Optional[int] = Form(None),
    chunk_overlap: Optional[int] = Form(None),
):
    """
    Uploads a document (PDF, DOCX, TXT, MD), extracts its content, chunks it,
    and indexes it in the vector database.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided in upload."
        )

    # Read file bytes
    try:
        content_bytes = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {str(e)}"
        )

    # Validate and load document
    try:
        pages, doc_meta = DocumentLoader.load(content_bytes, file.filename)
    except UnsupportedFileTypeError as e:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(e))
    except EmptyDocumentError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CorruptedFileError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except DocumentLoaderError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Chunk the document
    c_size = chunk_size or settings.DEFAULT_CHUNK_SIZE
    c_overlap = chunk_overlap or settings.DEFAULT_CHUNK_OVERLAP

    try:
        chunker = DocumentChunker(chunk_size=c_size, chunk_overlap=c_overlap)
        chunks = chunker.chunk_pages(pages, file.filename)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error chunking document: {str(e)}"
        )

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate chunks for '{file.filename}'."
        )

    # Attach timestamp & metadata to all chunks
    upload_time = datetime.now().isoformat()
    for chunk in chunks:
        chunk.metadata["uploaded_at"] = upload_time
        chunk.metadata["file_size_bytes"] = doc_meta["file_size_bytes"]
        chunk.metadata["file_type"] = doc_meta["file_type"]

    # Index into Vector Store
    vector_store = get_vector_store()
    try:
        indexed_count = vector_store.add_chunks(chunks)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index chunks in vector store: {str(e)}"
        )

    # Save physical copy for preview / downloads
    dest_path = Path(settings.UPLOAD_DIR) / file.filename
    try:
        with open(dest_path, "wb") as f:
            f.write(content_bytes)
    except Exception:
        pass

    return DocumentUploadResponse(
        success=True,
        filename=file.filename,
        file_type=doc_meta["file_type"],
        total_pages=doc_meta["total_pages"],
        total_chunks=indexed_count,
        total_characters=doc_meta["total_characters"],
        message=f"Successfully extracted, chunked, and indexed {indexed_count} chunks from '{file.filename}'."
    )


@router.get("", response_model=DocumentListResponse)
def list_documents():
    """Returns all currently indexed documents with summary statistics."""
    vector_store = get_vector_store()
    raw_docs = vector_store.get_indexed_documents()
    summaries = [DocumentSummary(**d) for d in raw_docs]
    total_chunks = vector_store.count()

    return DocumentListResponse(
        documents=summaries,
        total_documents=len(summaries),
        total_chunks=total_chunks
    )


@router.get("/{filename}/chunks", response_model=List[ChunkInfo])
def get_document_chunks(filename: str):
    """Fetches all chunk details and content for a given document."""
    vector_store = get_vector_store()
    try:
        results = vector_store.collection.get(
            where={"filename": filename},
            include=["documents", "metadatas"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not results or not results["ids"]:
        raise HTTPException(status_code=404, detail=f"No chunks found for document '{filename}'.")

    chunk_list = []
    for chunk_id, content, meta in zip(results["ids"], results["documents"], results["metadatas"]):
        chunk_list.append(
            ChunkInfo(
                chunk_id=chunk_id,
                chunk_index=meta.get("chunk_index", 0),
                page_number=meta.get("page_number", 1),
                char_count=meta.get("char_count", len(content)),
                content=content,
                metadata=meta
            )
        )

    chunk_list.sort(key=lambda x: x.chunk_index)
    return chunk_list


@router.delete("/{filename}", response_model=DocumentDeleteResponse)
def delete_document(filename: str):
    """Deletes an indexed document from the vector store and removes its uploaded file."""
    vector_store = get_vector_store()
    deleted_chunks = vector_store.delete_document(filename)

    if deleted_chunks == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{filename}' not found in vector store."
        )

    # Remove uploaded file if present
    file_path = Path(settings.UPLOAD_DIR) / filename
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception:
            pass

    return DocumentDeleteResponse(
        success=True,
        filename=filename,
        deleted_chunks=deleted_chunks,
        message=f"Successfully deleted {deleted_chunks} chunks for '{filename}'."
    )


@router.post("/clear")
def clear_all_documents():
    """Resets the vector database and removes all uploaded files."""
    vector_store = get_vector_store()
    vector_store.clear()

    # Clear uploads directory
    for f in Path(settings.UPLOAD_DIR).iterdir():
        if f.is_file() and f.name != ".gitkeep":
            try:
                f.unlink()
            except Exception:
                pass

    return {"success": True, "message": "All documents and vector store records have been cleared."}
