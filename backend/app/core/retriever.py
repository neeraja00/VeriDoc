"""Context retriever module for RAG pipeline."""
from typing import List, Optional, Tuple
from backend.app.config import settings
from backend.app.core.vector_store import VectorStoreManager, get_vector_store
from backend.app.schemas.rag import SourceCitation


class ContextRetriever:
    """Retrieves relevant document chunks and formats them into context for LLM generation."""

    def __init__(self, vector_store: Optional[VectorStoreManager] = None):
        self.vector_store = vector_store or get_vector_store()

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        document_filter: Optional[List[str]] = None,
    ) -> List[SourceCitation]:
        """
        Retrieves top-k relevant chunks matching the query that meet the score threshold.
        """
        k = top_k or settings.DEFAULT_TOP_K
        threshold = score_threshold if score_threshold is not None else settings.SIMILARITY_SCORE_THRESHOLD

        raw_results = self.vector_store.similarity_search(
            query=query,
            top_k=k,
            document_filter=document_filter
        )

        citations: List[SourceCitation] = []
        for record, score in raw_results:
            if score < threshold:
                continue

            content = record.get("content", "").strip()
            # Extract clean excerpt (up to 250 characters for citation preview)
            excerpt = content[:250] + ("..." if len(content) > 250 else "")

            citations.append(
                SourceCitation(
                    document_name=record.get("filename", record.get("source", "unknown")),
                    page_number=record.get("page_number", 1),
                    chunk_index=record.get("chunk_index", 0),
                    chunk_id=record.get("chunk_id", "chunk"),
                    similarity_score=score,
                    content=content,
                    excerpt=excerpt,
                )
            )

        return citations

    def format_context_block(self, citations: List[SourceCitation]) -> str:
        """
        Constructs a structured context string from retrieved citations for the LLM prompt.
        """
        if not citations:
            return ""

        context_parts = []
        for idx, cite in enumerate(citations, 1):
            text_to_show = cite.content if cite.content else cite.excerpt
            context_parts.append(
                f"--- [Source {idx}]: {cite.document_name} (Page {cite.page_number}, Chunk #{cite.chunk_index}) ---\n"
                f"{text_to_show}\n"
            )

        return "\n".join(context_parts)
