"""API routes for document upload, listing, previewing chunks, and deletion."""
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import FileResponse
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


@router.delete("/{filename:path}", response_model=DocumentDeleteResponse)
def delete_document(filename: str):
    """Deletes an indexed document from the vector store and removes its uploaded file."""
    import urllib.parse
    decoded_filename = urllib.parse.unquote(filename)

    vector_store = get_vector_store()
    deleted_chunks = vector_store.delete_document(filename)
    if deleted_chunks == 0 and decoded_filename != filename:
        deleted_chunks = vector_store.delete_document(decoded_filename)

    # Remove uploaded file if present on disk
    file_removed = False
    for fn in {filename, decoded_filename}:
        file_path = Path(settings.UPLOAD_DIR) / fn
        if file_path.exists():
            try:
                file_path.unlink()
                file_removed = True
            except Exception as e:
                logger.warning(f"Failed to delete disk file {file_path}: {e}")

    if deleted_chunks == 0 and not file_removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{decoded_filename}' not found in vector store or storage."
        )

    return DocumentDeleteResponse(
        success=True,
        filename=decoded_filename,
        deleted_chunks=deleted_chunks,
        message=f"Successfully deleted {deleted_chunks} chunks for '{decoded_filename}'."
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


@router.get("/{filename}/file")
def get_document_file(filename: str):
    """
    Serves the raw document file for in-browser page viewing as verified proof.
    Supports PDF (#page=N), TXT, MD, DOCX.
    """
    file_path = Path(settings.UPLOAD_DIR) / filename
    if not file_path.exists():
        # Fallback to sample_documents directory
        sample_path = Path(settings.BASE_DIR) / "sample_documents" / filename
        if sample_path.exists():
            file_path = sample_path
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document file '{filename}' not found."
            )

    ext = file_path.suffix.lower()
    media_types = {
        ".pdf": "application/pdf",
        ".txt": "text/plain; charset=utf-8",
        ".md": "text/plain; charset=utf-8",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
        content_disposition_type="inline"
    )

