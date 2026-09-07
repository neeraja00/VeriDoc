"""Unit tests for document chunker module."""
import pytest
from backend.app.core.document_loader import DocumentPage
from backend.app.core.chunker import DocumentChunker


def test_chunk_basic_document():
    pages = [
        DocumentPage(page_number=1, text="Paragraph one. " * 30),
        DocumentPage(page_number=2, text="Paragraph two. " * 30),
    ]

    chunker = DocumentChunker(chunk_size=300, chunk_overlap=50)
    chunks = chunker.chunk_pages(pages, "policy.pdf")

    assert len(chunks) > 2
    for chunk in chunks:
        assert chunk.source_filename == "policy.pdf"
        assert chunk.page_number in (1, 2)
        assert len(chunk.content) <= 350  # Allows boundary padding
        assert chunk.chunk_id.startswith("policy.pdf_p")


def test_chunk_metadata_integrity():
    pages = [DocumentPage(page_number=1, text="Hello world! This is a test chunk with important facts.")]
    chunker = DocumentChunker(chunk_size=500, chunk_overlap=50)
    chunks = chunker.chunk_pages(pages, "doc_test.txt")

    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].page_number == 1
    assert chunks[0].metadata["filename"] == "doc_test.txt"
    assert chunks[0].metadata["chunk_id"] == "doc_test.txt_p1_c0"


def test_invalid_chunk_parameters():
    with pytest.raises(ValueError):
        DocumentChunker(chunk_size=0)

    with pytest.raises(ValueError):
        DocumentChunker(chunk_size=200, chunk_overlap=200)

    with pytest.raises(ValueError):
        DocumentChunker(chunk_size=200, chunk_overlap=250)
