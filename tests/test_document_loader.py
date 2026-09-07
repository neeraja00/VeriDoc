"""Unit tests for document loader module."""
import pytest
from pathlib import Path
from backend.app.core.document_loader import (
    DocumentLoader,
    EmptyDocumentError,
    UnsupportedFileTypeError,
)

SAMPLE_PDF_PATH = Path(__file__).resolve().parent.parent / "sample_documents" / "sample_knowledge.pdf"


def test_load_valid_pdf():
    assert SAMPLE_PDF_PATH.exists(), f"Sample PDF must exist at {SAMPLE_PDF_PATH}"
    with open(SAMPLE_PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    pages, meta = DocumentLoader.load(pdf_bytes, "sample_knowledge.pdf")
    assert len(pages) == 3, f"Expected 3 pages, got {len(pages)}"
    assert meta["file_type"] == "pdf"
    assert meta["total_pages"] == 3
    assert meta["total_characters"] > 500

    # Verify content in page 1
    assert "Acme Global AI Architecture" in pages[0].text
    assert "5220.22-M" in pages[0].text
    assert "DoD" in pages[0].text

    # Verify content in page 2
    assert "AES-256-GCM" in pages[1].text
    assert "SOC 2 Type II" in pages[1].text

    # Verify content in page 3
    assert "5,000 queries per minute" in pages[2].text


def test_load_valid_text():
    text_content = b"This is a test document.\nIt contains two lines of text."
    pages, meta = DocumentLoader.load(text_content, "notes.txt")
    assert len(pages) == 1
    assert meta["file_type"] == "txt"
    assert "test document" in pages[0].text


def test_empty_document_error():
    with pytest.raises(EmptyDocumentError):
        DocumentLoader.load(b"", "empty.txt")

    with pytest.raises(EmptyDocumentError):
        DocumentLoader.load(b"   \n\t  ", "blank.txt")


def test_unsupported_file_type():
    with pytest.raises(UnsupportedFileTypeError):
        DocumentLoader.load(b"fake data", "image.jpg")

    with pytest.raises(UnsupportedFileTypeError):
        DocumentLoader.load(b"fake binary", "program.exe")
