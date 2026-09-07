"""Vector store manager using ChromaDB with persistence and in-memory fallback."""
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.app.config import settings
from backend.app.core.chunker import DocumentChunk
from backend.app.core.embeddings import BaseEmbeddingProvider, get_embedding_provider

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages document chunk indexing, retrieval, and deletion in ChromaDB."""

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
    ):
        self.persist_dir = persist_directory or settings.CHROMA_PERSIST_DIR
        self.collection_name = collection_name or settings.COLLECTION_NAME
        self.embedding_provider = embedding_provider or get_embedding_provider()

        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        self._init_client()

    def _init_client(self):
        """Initializes Chroma PersistentClient with cosine distance metadata."""
        try:
            self.client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Connected to ChromaDB collection '{self.collection_name}' at {self.persist_dir}")
        except Exception as e:
            logger.warning(f"Failed to initialize persistent ChromaDB: {e}. Falling back to EphemeralClient.")
            self.client = chromadb.EphemeralClient()
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

    def add_chunks(self, chunks: List[DocumentChunk]) -> int:
        """
        Embeds and stores a batch of document chunks in the vector collection.
        Returns the number of chunks added.
        """
        if not chunks:
            return 0

        # Delete any pre-existing chunks for this document to avoid stale duplicates
        first_chunk = chunks[0]
        self.delete_document(first_chunk.source_filename)

        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]

        # Generate embeddings
        embeddings = self.embedding_provider.embed_documents(documents)

        # Batch insert into Chroma
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        logger.info(f"Indexed {len(chunks)} chunks for document '{first_chunk.source_filename}'.")
        return len(chunks)

    def similarity_search(
        self,
        query: str,
        top_k: int = 4,
        document_filter: Optional[List[str]] = None,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Searches the collection using semantic query embedding.
        Returns a list of (metadata_dict, similarity_score) tuples sorted by relevance descending.
        """
        if self.count() == 0:
            return []

        query_embedding = self.embedding_provider.embed_query(query)

        where_clause = None
        if document_filter and len(document_filter) > 0:
            if len(document_filter) == 1:
                where_clause = {"filename": document_filter[0]}
            else:
                where_clause = {"filename": {"$in": document_filter}}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.count()),
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )

        output: List[Tuple[Dict[str, Any], float]] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return output

        ids = results["ids"][0]
        metadatas = results["metadatas"][0]
        documents = results["documents"][0]
        distances = results["distances"][0]

        for chunk_id, meta, doc_text, dist in zip(ids, metadatas, documents, distances):
            # Chroma with cosine metric returns cosine distance (0 = identical, 2 = opposite).
            # Convert to similarity score between 0.0 and 1.0
            similarity = max(0.0, min(1.0, 1.0 - float(dist)))
            record = {
                "chunk_id": chunk_id,
                "content": doc_text,
                **meta
            }
            output.append((record, round(similarity, 4)))

        # Sort descending by similarity
        output.sort(key=lambda item: item[1], reverse=True)
        return output

    def delete_document(self, filename: str) -> int:
        """Deletes all indexed chunks originating from a specific filename."""
        try:
            records = self.collection.get(where={"filename": filename})
            if records and records["ids"]:
                self.collection.delete(ids=records["ids"])
                deleted_count = len(records["ids"])
                logger.info(f"Deleted {deleted_count} chunks for filename '{filename}'.")
                return deleted_count
        except Exception as e:
            logger.error(f"Error deleting document '{filename}': {e}")
        return 0

    def get_indexed_documents(self) -> List[Dict[str, Any]]:
        """Returns metadata and chunk counts for all distinct documents in the store."""
        count = self.count()
        if count == 0:
            return []

        all_records = self.collection.get(include=["metadatas"])
        if not all_records or not all_records["metadatas"]:
            return []

        doc_map: Dict[str, Dict[str, Any]] = {}
        for meta in all_records["metadatas"]:
            fname = meta.get("filename", "unknown")
            if fname not in doc_map:
                doc_map[fname] = {
                    "filename": fname,
                    "file_type": meta.get("file_type", Path(fname).suffix.lstrip(".")),
                    "total_chunks": 0,
                    "file_size_bytes": meta.get("file_size_bytes", 0),
                    "uploaded_at": meta.get("uploaded_at", "N/A"),
                }
            doc_map[fname]["total_chunks"] += 1

        return list(doc_map.values())

    def count(self) -> int:
        """Returns total number of chunks currently indexed in the vector store."""
        try:
            return self.collection.count()
        except Exception:
            return 0

    def clear(self) -> None:
        """Clears all documents and resets the collection."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Cleared and reset vector store collection.")
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")


# Singleton instance
_vector_store_instance = None


def get_vector_store() -> VectorStoreManager:
    """Returns the shared vector store manager singleton."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStoreManager()
    return _vector_store_instance
