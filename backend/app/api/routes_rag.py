"""API routes for RAG context retrieval and question answering."""
import time
from fastapi import APIRouter, HTTPException, status
from backend.app.config import settings
from backend.app.core.vector_store import get_vector_store
from backend.app.core.retriever import ContextRetriever
from backend.app.core.llm import get_llm_provider
from backend.app.schemas.rag import (
    RAGQueryRequest,
    RAGQueryResponse,
    ContextRetrievalRequest,
    ContextRetrievalResponse,
)

router = APIRouter(prefix="/api/rag", tags=["RAG"])


@router.post("/query", response_model=RAGQueryResponse)
def query_rag(request: RAGQueryRequest):
    """
    Executes the end-to-end RAG pipeline:
    1. Embeds question and retrieves top-k relevant document chunks.
    2. Filters context by score threshold.
    3. Synthesizes a grounded answer via the configured LLM provider.
    4. Attaches precise source citations.
    """
    start_time = time.perf_counter()
    vector_store = get_vector_store()

    # Guard: Empty vector store
    if vector_store.count() == 0:
        return RAGQueryResponse(
            query=request.query,
            answer="No documents have been uploaded yet. Please upload a PDF, DOCX, or TXT document to begin asking questions.",
            sources=[],
            total_sources_found=0,
            llm_provider=settings.LLM_PROVIDER,
            model_name=settings.GEMINI_MODEL,
            is_grounded=False,
            processing_time_ms=round((time.perf_counter() - start_time) * 1000, 2),
        )

    retriever = ContextRetriever(vector_store)
    citations = retriever.retrieve(
        query=request.query,
        top_k=request.top_k,
        score_threshold=request.score_threshold,
        document_filter=request.document_filter,
    )

    # Format context block
    context_block = retriever.format_context_block(citations)

    # Initialize LLM provider
    try:
        llm = get_llm_provider()
        answer = llm.generate_answer(
            question=request.query,
            citations=citations,
            context_block=context_block,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM Generation failed: {str(e)}"
        )

    # Check if the answer is grounded or unanswerable
    is_grounded = bool(citations) and (
        "cannot find the answer" not in answer.lower()
        and "not mentioned in the provided" not in answer.lower()
    )

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return RAGQueryResponse(
        query=request.query,
        answer=answer,
        sources=citations,
        total_sources_found=len(citations),
        llm_provider=llm.provider_name,
        model_name=llm.model_name,
        is_grounded=is_grounded,
        processing_time_ms=elapsed_ms,
    )


@router.post("/retrieve", response_model=ContextRetrievalResponse)
def retrieve_context(request: ContextRetrievalRequest):
    """
    Retrieves and inspects top-k chunks directly without invoking the LLM.
    Useful for relevance debugging and context inspection.
    """
    retriever = ContextRetriever()
    citations = retriever.retrieve(
        query=request.query,
        top_k=request.top_k,
        document_filter=request.document_filter,
    )

    return ContextRetrievalResponse(
        query=request.query,
        retrieved_chunks=citations,
        total_retrieved=len(citations),
    )
