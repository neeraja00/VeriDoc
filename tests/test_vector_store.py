"""Unit tests for vector store manager with Chroma."""
import pytest
import shutil
from pathlib import Path
from backend.app.core.chunker import DocumentChunk
from backend.app.core.embeddings import MockEmbeddingProvider
from backend.app.core.vector_store import VectorStoreManager

TEST_PERSIST_DIR = Path(__file__).resolve().parent / "test_chroma_db"


@pytest.fixture
def temp_vector_store():
    # Setup clean test store
    if TEST_PERSIST_DIR.exists():
        shutil.rmtree(TEST_PERSIST_DIR, ignore_errors=True)

    manager = VectorStoreManager(
        persist_directory=str(TEST_PERSIST_DIR),
        collection_name="test_collection",
        embedding_provider=MockEmbeddingProvider(dimension=64)
    )
    yield manager

    # Teardown
    manager.clear()
    if TEST_PERSIST_DIR.exists():
        shutil.rmtree(TEST_PERSIST_DIR, ignore_errors=True)


def test_vector_store_add_and_query(temp_vector_store):
    chunks = [
        DocumentChunk(
            chunk_id="test_doc_p1_c0",
            chunk_index=0,
            source_filename="test_doc.pdf",
            page_number=1,
            content="Acme AI retains customer data for 90 days before cryptographic erasure.",
            char_count=71,
            metadata={"filename": "test_doc.pdf", "page_number": 1, "chunk_index": 0}
        ),
        DocumentChunk(
            chunk_id="test_doc_p2_c1",
            chunk_index=1,
            source_filename="test_doc.pdf",
            page_number=2,
            content="Encryption protocols mandate AES-256-GCM for all stored artifacts.",
            char_count=67,
            metadata={"filename": "test_doc.pdf", "page_number": 2, "chunk_index": 1}
        ),
    ]

    added = temp_vector_store.add_chunks(chunks)
    assert added == 2
    assert temp_vector_store.count() == 2

    # Query matching chunk 1
    results = temp_vector_store.similarity_search("retention policy 90 days", top_k=2)
    assert len(results) > 0
    top_record, score = results[0]
    assert "90 days" in top_record["content"]
    assert score > 0.0


def test_vector_store_delete_document(temp_vector_store):
    chunks = [
        DocumentChunk(
            chunk_id="doc1_c0",
            chunk_index=0,
            source_filename="doc1.pdf",
            page_number=1,
            content="Some text in doc 1.",
            char_count=20,
            metadata={"filename": "doc1.pdf", "page_number": 1, "chunk_index": 0}
        ),
        DocumentChunk(
            chunk_id="doc2_c0",
            chunk_index=0,
            source_filename="doc2.pdf",
            page_number=1,
            content="Some text in doc 2.",
            char_count=20,
            metadata={"filename": "doc2.pdf", "page_number": 1, "chunk_index": 0}
        ),
    ]
    temp_vector_store.add_chunks(chunks)
    assert temp_vector_store.count() == 2

    deleted = temp_vector_store.delete_document("doc1.pdf")
    assert deleted == 1
    assert temp_vector_store.count() == 1

    docs = temp_vector_store.get_indexed_documents()
    assert len(docs) == 1
    assert docs[0]["filename"] == "doc2.pdf"
