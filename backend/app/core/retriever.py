"""Context retriever module for RAG pipeline with balanced multi-document retrieval."""
from typing import List, Optional, Tuple, Dict, Any
from backend.app.config import settings
from backend.app.core.vector_store import VectorStoreManager, get_vector_store
from backend.app.schemas.rag import SourceCitation


class ContextRetriever:
    """Retrieves relevant document chunks and formats them into context for LLM generation."""

    def __init__(self, vector_store: Optional[VectorStoreManager] = None):
        self.vector_store = vector_store or get_vector_store()

    @staticmethod
    def is_overview_query(query: str) -> bool:
        """Detects broad, whole-document summary or overview questions."""
        q = query.lower().strip()
        whole_doc_phrases = [
            "what is this document all about",
            "what is this document about",
            "what is the document about",
            "what is this doc about",
            "what is this document",
            "what is this file about",
            "what does this document cover",
            "overview of the document",
            "overview of the doc",
            "overview of this document",
            "summary of the document",
            "summary of this document",
            "summarize the document",
            "summarize this document",
            "summarize this file",
            "document summary",
            "doc summary",
            "give me an overview of the document",
            "give me an overview of this document",
            "give me an overview of the doc",
            "tell me what this document is about",
            "what are the contents of this document",
        ]
        if q in {"overview", "summary", "summarize", "document overview", "doc overview", "what is this", "what is this document"}:
            return True
        return any(phrase in q for phrase in whole_doc_phrases)

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        document_filter: Optional[List[str]] = None,
    ) -> List[SourceCitation]:
        """
        Retrieves top-k relevant chunks matching the query.
        Uses semantic vector similarity to rank the most relevant pages first.
        """
        k = top_k or settings.DEFAULT_TOP_K
        threshold = score_threshold if score_threshold is not None else settings.SIMILARITY_SCORE_THRESHOLD

        # If searching across multiple documents or all documents, fetch a broader candidate pool
        candidate_k = max(k * 3, 24) if (not document_filter or len(document_filter) > 1) else max(k * 2, 10)

        # Semantic similarity search using query embedding
        raw_results = self.vector_store.similarity_search(
            query=query,
            top_k=candidate_k,
            document_filter=document_filter
        )

        valid_results = [(rec, sc) for rec, sc in raw_results if sc >= threshold]
        is_overview = self.is_overview_query(query)

        # If a specific single document filter was applied
        if document_filter and len(document_filter) == 1:
            target_fn = document_filter[0]

            # Only if the user explicitly asked for a broad whole-document overview
            # AND semantic search yielded zero valid chunks, fall back to structural chunks.
            if is_overview and not valid_results:
                try:
                    direct_records = self.vector_store.collection.get(
                        where={"filename": target_fn},
                        include=["documents", "metadatas"]
                    )
                    if direct_records and direct_records.get("ids"):
                        doc_chunks = []
                        for cid, text, meta in zip(
                            direct_records["ids"],
                            direct_records["documents"],
                            direct_records["metadatas"]
                        ):
                            rec = {"chunk_id": cid, "content": text, **meta}
                            doc_chunks.append(rec)
                        doc_chunks.sort(key=lambda c: c.get("chunk_index", 0))
                        candidate_results = [(rec, 0.75) for rec in doc_chunks]
                    else:
                        candidate_results = raw_results
                except Exception:
                    candidate_results = raw_results
            else:
                # Always prioritize the actual semantic vector search results
                candidate_results = valid_results if valid_results else raw_results

            return self._deduplicate_and_build_citations(candidate_results, top_k=k, is_overview=is_overview)
        else:
            # Multi-document search: prioritize vector similarity matches
            candidate_pool = valid_results if valid_results else raw_results[:candidate_k]
            return self._deduplicate_and_build_citations(candidate_pool, top_k=k, is_overview=is_overview)

    def _deduplicate_and_build_citations(
        self,
        candidate_results: List[Tuple[Dict[str, Any], float]],
        top_k: int,
        is_overview: bool = False
    ) -> List[SourceCitation]:
        """
        Deduplicates retrieved chunks strictly by (document_name, page_number).
        Guarantees that no page of any document is repeated in citations.
        Chunks belonging to the same page are cleanly merged together.
        """
        if not candidate_results:
            return []

        # Map (document_name, page_number) -> grouped page record
        page_map: Dict[Tuple[str, int], Dict[str, Any]] = {}
        for rec, score in candidate_results:
            doc_name = rec.get("filename", rec.get("source", "unknown"))
            page_no = int(rec.get("page_number", 1))
            key = (doc_name, page_no)

            if key not in page_map:
                page_map[key] = {
                    "document_name": doc_name,
                    "page_number": page_no,
                    "best_score": score,
                    "chunks": [rec],
                    "first_chunk_index": rec.get("chunk_index", 0),
                    "chunk_id": rec.get("chunk_id", "chunk"),
                }
            else:
                if score > page_map[key]["best_score"]:
                    page_map[key]["best_score"] = score
                existing_cids = {c.get("chunk_id") for c in page_map[key]["chunks"]}
                if rec.get("chunk_id") not in existing_cids:
                    page_map[key]["chunks"].append(rec)

        grouped_pages = list(page_map.values())
        if is_overview:
            # Order sequentially by page number for cohesive overview reading
            grouped_pages.sort(key=lambda p: (p["document_name"], p["page_number"]))
        else:
            # Order by highest similarity score descending
            grouped_pages.sort(key=lambda p: p["best_score"], reverse=True)

        selected_pages = grouped_pages[:top_k]

        citations: List[SourceCitation] = []
        for page_info in selected_pages:
            sorted_chunks = sorted(
                page_info["chunks"],
                key=lambda c: c.get("chunk_index", 0)
            )

            # Combine distinct chunk contents on this page without duplicate text
            combined_parts = []
            for c in sorted_chunks:
                txt = c.get("content", "").strip()
                if txt and txt not in combined_parts:
                    combined_parts.append(txt)

            merged_content = "\n\n".join(combined_parts)
            first_text = sorted_chunks[0].get("content", "").strip()
            excerpt = first_text[:250] + ("..." if len(first_text) > 250 else "")

            citations.append(
                SourceCitation(
                    document_name=page_info["document_name"],
                    page_number=page_info["page_number"],
                    chunk_index=page_info["first_chunk_index"],
                    chunk_id=page_info["chunk_id"],
                    similarity_score=round(page_info["best_score"], 4),
                    content=merged_content,
                    excerpt=excerpt,
                )
            )

        return citations

    def format_context_block(self, citations: List[SourceCitation]) -> str:
        """
        Constructs a structured context string from retrieved citations for the LLM prompt.
        Highlights document names and page numbers for clear LLM attribution.
        """
        if not citations:
            return ""

        context_parts = []
        for idx, cite in enumerate(citations, 1):
            text_to_show = cite.content if cite.content else cite.excerpt
            context_parts.append(
                f"--- [Source {idx}]: {cite.document_name} (Page {cite.page_number}) ---\n"
                f"{text_to_show}\n"
            )

        return "\n".join(context_parts)