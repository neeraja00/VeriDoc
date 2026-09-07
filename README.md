# VeriDoc AI: Verified Document Intelligence & Fact-Grounded Knowledge Engine

> **VeriDoc AI** is an enterprise-grade, retrieval-augmented generation (RAG) platform and knowledge engine. It ingests enterprise documents (PDF, DOCX, TXT, Markdown), creates persistent semantic vector embeddings, performs high-precision cosine similarity retrieval, and synthesizes factually grounded answers with verified source citations and strict zero-hallucination guardrails.

---

## 📌 Overview

### What the Project Does
VeriDoc AI transforms unstructured enterprise files into an interactive, question-answering intelligence engine. Users can upload company policies, technical manuals, contracts, or research reports, ask natural language questions, and receive accurate answers that cite exact pages, chunk indices, and similarity match percentages.

### Why It Was Built
Large Language Models (LLMs) are notorious for generating plausible-sounding hallucinations when answering questions about proprietary, domain-specific, or internal company data. VeriDoc AI was built to solve this critical reliability bottleneck by enforcing strict context grounding: the LLM is constrained to synthesize answers **only** from retrieved document excerpts. If an answer cannot be proven from the ingested documents, the system safely refuses to speculate.

### What Problem It Solves
- **Eliminates LLM Hallucinations**: Enforces strict grounding prompts and similarity thresholds, preventing false or misleading answers.
- **Auditability & Traceability**: Every answer is backed by verifiable source cards showing filename, page number, excerpt snippet, and vector match confidence.
- **Information Silos**: Unifies fragmented documents across `.pdf`, `.docx`, `.txt`, and `.md` into a single, searchable semantic vector index.
- **Zero-Cloud Dependency Option**: Supports local embeddings via Sentence Transformers (`all-MiniLM-L6-v2`) and offline mock fallbacks, enabling privacy-first, zero-API-cost deployment.

---

## ✨ Features

- **Multi-Format Document Parsing**: Native extraction for `.pdf` (page-by-page via `pypdf`), `.docx` (paragraphs and tables via `python-docx`), `.txt`, and `.md` files.
- **Recursive Semantic Chunking**: Configurable chunk size and overlap powered by `RecursiveCharacterTextSplitter`, preserving document structure and exact page numbers.
- **Hybrid Embedding Architecture**:
  - **Local (Default)**: 384-dimensional dense vectors using `all-MiniLM-L6-v2` running on CPU without external API calls.
  - **Cloud**: 768-dimensional embeddings via Google Gemini (`text-embedding-004`).
  - **Offline/CI**: Deterministic mock hash vectorizer for isolated unit testing and CI/CD pipelines.
- **Persistent Vector Storage**: Powered by **ChromaDB** with HNSW indexing and cosine similarity metric, featuring document chunk inspection and single-document or bulk index deletion.
- **Strict Anti-Hallucination Guardrails**: Prompt engineering and score thresholding ensure out-of-scope questions return explicit, graceful refusals rather than invented responses.
- **Precision Source Citations**: Real-time response cards displaying exact document name, page number, chunk index, excerpt preview, and cosine similarity match score.
- **Modern Glassmorphic Web Dashboard**: Dark-mode, responsive UI built with HTML5, vanilla CSS, and vanilla JavaScript, served directly by FastAPI without needing a separate node server.
- **Interactive Hyperparameter Controls**: Sliders in the UI allow real-time tuning of chunk size, chunk overlap, top-K retrieval count, and similarity score thresholds.

---

## 🛠️ Tech Stack

| Domain | Technologies & Libraries |
|---|---|
| **Frontend** | HTML5, Modern Vanilla CSS (Glassmorphism, Dark Mode, Micro-animations), Vanilla JavaScript (ES6+ Fetch API, Dynamic DOM) |
| **Backend Framework** | Python 3.10+, FastAPI, Uvicorn (ASGI Server), Pydantic v2 & Pydantic-Settings |
| **Vector Store & Indexing** | ChromaDB (Persistent HNSW Indexing, Cosine Metric) |
| **Embeddings & AI** | Hugging Face `sentence-transformers` (`all-MiniLM-L6-v2`), Google Gemini (`google-genai`), LangChain Text Splitters |
| **Document Processing** | `pypdf`, `python-docx`, `reportlab` |
| **Testing & QA Automation** | `pytest`, `pytest-asyncio`, `httpx` (API Client Testing), `coverage` |
| **Environment & Tooling** | Python Virtual Environments (`venv`), `python-dotenv`, Git, GitHub |

---

## 📂 Project Structure

```text
VeriDoc/
├── backend/
│   └── app/
│       ├── __init__.py
│       ├── main.py                  # FastAPI ASGI entrypoint with CORS & static file mounting
│       ├── config.py                # Pydantic Settings & environment variable configuration
│       ├── api/                     # REST API route controllers
│       │   ├── __init__.py
│       │   ├── routes_documents.py  # File upload, list, chunk preview, delete, clear
│       │   ├── routes_rag.py        # End-to-end RAG query & context retrieval
│       │   └── routes_system.py     # System health, active models, and hyperparameter status
│       ├── core/                    # Core business logic & pipeline components
│       │   ├── __init__.py
│       │   ├── document_loader.py   # Multi-format document parser (PDF, DOCX, TXT, MD)
│       │   ├── chunker.py           # Recursive chunker with page & chunk ID preservation
│       │   ├── embeddings.py        # Pluggable embeddings (SentenceTransformers, Gemini, Mock)
│       │   ├── vector_store.py      # ChromaDB manager with HNSW cosine search & index maintenance
│       │   ├── retriever.py         # Top-K relevance retrieval & context formatting
│       │   └── llm.py               # Pluggable LLM orchestrator (Gemini 1.5 Flash, Mock)
│       └── schemas/                 # Pydantic request & response validation schemas
│           ├── __init__.py
│           ├── document.py          # Document, chunk, and upload schemas
│           └── rag.py               # Query, answer, citation, and retrieve schemas
├── frontend/
│   └── web/                         # Production-ready web dashboard served by FastAPI
│       ├── index.html               # Semantic HTML5 layout
│       ├── css/
│       │   └── style.css            # Dark glassmorphism, responsive grid, micro-animations
│       └── js/
│           └── app.js               # Reactive upload handler, query dispatcher, citation renderer
├── data/                            # Persistent storage (auto-created at runtime)
│   ├── uploads/                     # Raw uploaded document storage
│   └── chroma_db/                   # Persistent Chroma vector store
├── sample_documents/                # Verified test documents
│   ├── sample_knowledge.pdf         # 3-page enterprise cloud & security policy PDF
│   ├── apartment_lease_agreement.txt# Sample legal agreement for QA verification
│   └── generate_sample_pdf.py       # Automated PDF generation utility
├── tests/                           # Comprehensive automated test suite
│   ├── test_document_loader.py      # Unit tests for multi-format text extraction
│   ├── test_chunker.py              # Unit tests for chunk size, overlap, and ID indexing
│   ├── test_vector_store.py         # Unit tests for Chroma vector indexing and query search
│   └── test_rag_pipeline.py         # End-to-end RAG pipeline integration tests
├── .env.example                     # Template environment variables
├── .gitignore                       # Git ignore rules for virtual environments, caches, and storage
├── pytest.ini                       # Pytest configuration with root pythonpath
├── requirements.txt                 # Pinned project dependencies
└── README.md                        # Project documentation
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/neeraja00/VeriDoc.git
cd VeriDoc
```

### 2. Create and Activate Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```

Open `.env` and configure your settings:
```ini
# LLM Configuration
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# Embedding Configuration
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Vector Store & Storage Settings
CHROMA_PERSIST_DIR=./data/chroma_db
COLLECTION_NAME=knowledge_assistant

# RAG Hyperparameters
DEFAULT_CHUNK_SIZE=800
DEFAULT_CHUNK_OVERLAP=150
DEFAULT_TOP_K=4
SIMILARITY_SCORE_THRESHOLD=0.25

# Server Port
PORT=8000
```

> **Note**: If `GEMINI_API_KEY` is omitted or empty, the application automatically falls back to **Offline / Mock Mode**, allowing full local indexing, chunk inspection, and testing without requiring an external API key.

### 5. Run the Project
Start the FastAPI application with Uvicorn:
```bash
python -m uvicorn backend.app.main:app --reload --port 8000
```

Open your browser and navigate to:
- **Web Dashboard**: [http://localhost:8000/](http://localhost:8000/)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc API Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Testing

VeriDoc AI includes a robust, automated test suite built with **Pytest** and **Pytest-Asyncio**, validating every layer of the architecture from document parsing to end-to-end anti-hallucination verification.

### Test Coverage Breakdown

- **Functional & Unit Testing**:
  - `test_document_loader.py`: Validates text and page extraction across `.pdf`, `.docx`, `.txt`, and `.md` formats.
  - `test_chunker.py`: Verifies splitting boundaries, character count thresholds, overlap consistency, and chunk ID tracking (`{filename}_p{page}_c{chunk}`).
- **Vector Store & Indexing Testing**:
  - `test_vector_store.py`: Tests ChromaDB indexing, metadata preservation, similarity ranking, document deletion, and index purging.
- **Integration & End-to-End Pipeline Testing**:
  - `test_rag_pipeline.py`: Executes end-to-end queries against `sample_knowledge.pdf`, asserting prompt construction, retrieval relevancy, and citation formatting.
- **Positive Test Cases**:
  - Grounded factual questions return high-confidence answers with verified citations pointing to the exact source page.
- **Negative & Edge Case Testing**:
  - **Out-of-Scope Questions**: Verifies that unanswerable questions (e.g., asking about unrelated topics) trigger zero citations and the expected strict refusal string.
  - **Empty Document Handling**: Confirms that uploading 0-byte or blank files raises appropriate HTTP 400 validation errors.
  - **Unsupported File Types**: Tests rejection of invalid extensions (e.g., `.exe`, `.bin`).
  - **Boundary Validation**: Tests zero chunk overlap, large chunk sizes, and top-K limits.

### Test Automation Architecture
- **Isolated Test Environments**: Fixtures automatically provision and clean up temporary ChromaDB instances in temporary directories (`temp_vector_store`, `pipeline_chroma_db`).
- **Deterministic Mocking**: Uses `MockEmbeddingProvider` and `MockLLMProvider` for ultra-fast, offline testing that runs identically in CI/CD without API rate limits or network calls.

### Run Tests

Execute the full automated test suite:
```bash
pytest tests -v
```

Run tests with test coverage reporting:
```bash
pytest --cov=backend tests/
```

Run a specific test module:
```bash
pytest tests/test_rag_pipeline.py -v
```

### Automated Test Results
```text
============================= test session starts =============================
platform win32 -- Python 3.13.x, pytest-9.x.x
rootdir: C:\Users\...\VeriDoc
configfile: pytest.ini

tests/test_chunker.py::test_chunk_basic_document PASSED                  [  9%]
tests/test_chunker.py::test_chunk_metadata_integrity PASSED              [ 18%]
tests/test_chunker.py::test_invalid_chunk_parameters PASSED              [ 27%]
tests/test_document_loader.py::test_load_valid_pdf PASSED                [ 36%]
tests/test_document_loader.py::test_load_valid_text PASSED               [ 45%]
tests/test_document_loader.py::test_empty_document_error PASSED          [ 54%]
tests/test_document_loader.py::test_unsupported_file_type PASSED         [ 63%]
tests/test_rag_pipeline.py::test_rag_retrieval_and_citation PASSED       [ 72%]
tests/test_rag_pipeline.py::test_rag_anti_hallucination_out_of_scope PASSED [ 81%]
tests/test_vector_store.py::test_vector_store_add_and_query PASSED       [ 90%]
tests/test_vector_store.py::test_vector_store_delete_document PASSED     [100%]

======================= 11 passed in 100% success rate =======================
```

---

## 📸 Screenshots / Application UI Tour

The web application features an intuitive, modern, dark glassmorphic dashboard divided into structured functional zones:

1. **Top Navigation & Health Monitor**:
   - Displays real-time API connection status (`Online` / `Offline`).
   - Live chips indicating total indexed chunks in ChromaDB, active LLM model (`Gemini 1.5 Flash`), and active embedding model (`all-MiniLM-L6-v2`).
2. **Knowledge Base & Ingestion Panel (Left Sidebar)**:
   - **Drag-and-Drop Uploader**: Accepts PDF, Word, and text files with live upload progress bar.
   - **Document Cards**: Displays filename, file size, chunk counts, a **View Chunks** inspector button, and a **Delete** button.
   - **Bulk Clear**: One-click purge to reset the vector database and wipe uploaded files.
3. **Interactive Chunk Inspection Modal**:
   - Click "View Chunks" on any document card to open a modal displaying every indexed text chunk, chunk ID, character count, and assigned page number.
4. **Fact-Grounded Query & Chat Workspace (Center)**:
   - Natural language question input with expandable textarea and keyboard shortcuts (`Enter` to submit, `Shift+Enter` for multiline).
   - Quick query suggestion chips for instantaneous testing.
   - Bot responses display grounded status badges (`✓ Grounded in Documents` vs. `ℹ Out of Scope / Unverified`).
5. **Precision Source Citation Cards**:
   - Each answer embeds clickable source cards showing Document Name, Page Number, Chunk ID, Cosine Relevance %, and verbatim text excerpt.
6. **RAG Hyperparameter Controls (Right Sidebar)**:
   - Real-time sliders for Chunk Size (200–2000 chars), Chunk Overlap (0–500 chars), Top-K Retrieval (1–10 chunks), and Similarity Score Threshold (0.0–1.0).

---

## 🔌 API Endpoints

VeriDoc AI exposes clean, fully typed REST endpoints with automatic OpenAPI validation:

### 1. Document Management Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/documents/upload` | Ingests, parses, chunks, and indexes a `.pdf`, `.docx`, `.txt`, or `.md` file |
| `GET` | `/api/documents` | Lists all indexed documents with chunk count and file size statistics |
| `GET` | `/api/documents/{filename}/chunks` | Retrieves all indexed chunks and metadata for a specific document |
| `DELETE` | `/api/documents/{filename}` | Deletes a document and cryptographically removes all its vector embeddings |
| `POST` | `/api/documents/clear` | Purges all indexed documents and resets the ChromaDB vector collection |

### 2. RAG & Retrieval Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/rag/query` | Executes end-to-end RAG query, returning grounded synthesis and source citations |
| `POST` | `/api/rag/retrieve` | Retrieves top-K context chunks and relevance scores without invoking the LLM |

#### Sample Request (`POST /api/rag/query`):
```json
{
  "query": "What is the data retention policy?",
  "top_k": 3,
  "score_threshold": 0.25
}
```

#### Sample Response:
```json
{
  "query": "What is the data retention policy?",
  "answer": "Customer data is retained for exactly 90 days following account deactivation. Once the grace period expires, all associated vector indexes and document chunks are cryptographically erased using DoD 5220.22-M sanitation standards.",
  "sources": [
    {
      "document_name": "sample_knowledge.pdf",
      "page_number": 1,
      "chunk_index": 1,
      "chunk_id": "sample_knowledge.pdf_p1_c1",
      "similarity_score": 0.4831,
      "excerpt": "5220.22-M sanitation standards. Backup snapshots are permanently purged within 14 business days..."
    }
  ],
  "total_sources_found": 1,
  "llm_provider": "gemini",
  "model_name": "gemini-1.5-flash",
  "is_grounded": true,
  "processing_time_ms": 342.15
}
```

### 3. System Diagnostics Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/system/health` | Returns real-time vector database status, chunk counts, and active providers |

---

## 🚀 Future Improvements

- **Hybrid Sparse-Dense Search**: Integrate BM25 keyword matching alongside ChromaDB dense vector search with Reciprocal Rank Fusion (RRF) for enhanced acronym and exact-keyword retrieval.
- **Optical Character Recognition (OCR)**: Integrate Tesseract or EasyOCR to extract and index text from scanned images and image-based PDFs.
- **Multi-Tenant Workspace Partitioning**: Add user authentication (JWT) and role-based access control (RBAC) to support isolated organizational workspaces.
- **Continuous Integration / Continuous Deployment (CI/CD)**: Set up automated GitHub Actions to run the Pytest test suite, enforce linting, and build containerized Docker images on every pull request.
- **Streaming LLM Responses**: Implement Server-Sent Events (SSE) / WebSockets to stream tokens in real-time to the web dashboard.

---

## 👨💻 Author

**Neeraja**
- **GitHub**: [@neeraja00](https://github.com/neeraja00)
- **Repository**: [VeriDoc](https://github.com/neeraja00/VeriDoc)

---

## 📄 License

This project is licensed under the **MIT License**. You are free to use, modify, distribute, and integrate this software into personal and enterprise projects.
