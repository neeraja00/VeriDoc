"""End-to-end RAG pipeline integration tests using sample_knowledge.pdf."""
import pytest
import shutil
from pathlib import Path
from backend.app.core.document_loader import DocumentLoader
from backend.app.core.chunker import DocumentChunker
from backend.app.core.embeddings import SentenceTransformerEmbeddingProvider
from backend.app.core.vector_store import VectorStoreManager
from backend.app.core.retriever import ContextRetriever
from backend.app.core.llm import MockLLMProvider

SAMPLE_PDF = Path(__file__).resolve().parent.parent / "sample_documents" / "sample_knowledge.pdf"
PIPELINE_STORE_DIR = Path(__file__).resolve().parent / "pipeline_chroma_db"


@pytest.fixture(scope="module")
def rag_pipeline():
    """Sets up an isolated, populated RAG pipeline instance."""
    assert SAMPLE_PDF.exists(), f"Sample PDF must exist at {SAMPLE_PDF}"

    if PIPELINE_STORE_DIR.exists():
        shutil.rmtree(PIPELINE_STORE_DIR, ignore_errors=True)

    # 1. Initialize Vector Store with SentenceTransformer Embeddings
    vstore = VectorStoreManager(
        persist_directory=str(PIPELINE_STORE_DIR),
        collection_name="pipeline_test",
        embedding_provider=SentenceTransformerEmbeddingProvider()
    )

    # 2. Extract Document
    with open(SAMPLE_PDF, "rb") as f:
        pdf_bytes = f.read()
    pages, meta = DocumentLoader.load(pdf_bytes, "sample_knowledge.pdf")

    # 3. Chunk
    chunker = DocumentChunker(chunk_size=600, chunk_overlap=100)
    chunks = chunker.chunk_pages(pages, "sample_knowledge.pdf")
    vstore.add_chunks(chunks)

    # 4. Retriever & LLM
    retriever = ContextRetriever(vector_store=vstore)
    llm = MockLLMProvider()

    yield {"store": vstore, "retriever": retriever, "llm": llm}

    # Cleanup
    vstore.clear()
    if PIPELINE_STORE_DIR.exists():
        shutil.rmtree(PIPELINE_STORE_DIR, ignore_errors=True)


def test_rag_retrieval_and_citation(rag_pipeline):
    retriever = rag_pipeline["retriever"]
    llm = rag_pipeline["llm"]

    # Inquire about data retention
    query = "What is the customer data retention policy and erasure standard?"
    citations = retriever.retrieve(query, top_k=3, score_threshold=0.1)

    assert len(citations) > 0, "Should retrieve at least one matching citation"

    top_citation = citations[0]
    assert top_citation.document_name == "sample_knowledge.pdf"
    assert top_citation.page_number in (1, 2, 3)
    assert top_citation.similarity_score > 0.1

    # Verify context block generation
    context_block = retriever.format_context_block(citations)
    assert "sample_knowledge.pdf" in context_block

    # Generate answer
    answer = llm.generate_answer(query, citations, context_block)
    assert "sample_knowledge.pdf" in answer
    assert "90 days" in context_block or "DoD" in context_block


def test_rag_anti_hallucination_out_of_scope(rag_pipeline):
    retriever = rag_pipeline["retriever"]
    llm = rag_pipeline["llm"]

    # Question completely unrelated to document
    unrelated_query = "What is the secret recipe for quantum chocolate cake on Jupiter?"

    # Retrieval with higher threshold
    citations = retriever.retrieve(unrelated_query, top_k=2, score_threshold=0.5)

    if not citations:
        context_block = ""
    else:
        context_block = retriever.format_context_block(citations)

    answer = llm.generate_answer(unrelated_query, citations, context_block)

    # Must refuse to hallucinate
    expected_refusal = "I cannot find the answer to this question in the provided documents."
    assert expected_refusal in answer, f"Expected refusal statement, got: {answer}"
