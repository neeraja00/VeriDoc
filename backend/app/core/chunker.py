"""Text chunking module using RecursiveCharacterTextSplitter with metadata preservation."""
from typing import List, Dict, Any
from dataclasses import dataclass, field
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.app.core.document_loader import DocumentPage


@dataclass
class DocumentChunk:
    """Represents an individual text chunk ready for embedding and vector storage."""
    chunk_id: str
    chunk_index: int
    source_filename: str
    page_number: int
    content: str
    char_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentChunker:
    """Splits document pages into semantically cohesive chunks with overlapping boundaries."""

    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
        separators: List[str] = None,
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len,
        )

    def chunk_pages(self, pages: List[DocumentPage], filename: str) -> List[DocumentChunk]:
        """
        Splits pages into chunks while preserving page numbers and attaching unique chunk IDs.
        """
        chunks: List[DocumentChunk] = []
        global_chunk_index = 0

        # Sanitize filename for chunk_id
        safe_filename = filename.replace(" ", "_").replace("/", "_").replace("\\", "_")

        for page in pages:
            raw_text = page.text.strip()
            if not raw_text:
                continue

            split_texts = self._splitter.split_text(raw_text)
            for split_text in split_texts:
                clean_content = split_text.strip()
                if not clean_content:
                    continue

                chunk_id = f"{safe_filename}_p{page.page_number}_c{global_chunk_index}"
                chunk_meta = {
                    "source": filename,
                    "filename": filename,
                    "page_number": int(page.page_number),
                    "chunk_index": int(global_chunk_index),
                    "chunk_id": chunk_id,
                    "char_count": len(clean_content),
                    **page.metadata
                }

                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        chunk_index=global_chunk_index,
                        source_filename=filename,
                        page_number=page.page_number,
                        content=clean_content,
                        char_count=len(clean_content),
                        metadata=chunk_meta,
                    )
                )
                global_chunk_index += 1

        return chunks
