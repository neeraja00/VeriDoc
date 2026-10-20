# PROJECT AUDIT REPORT: VeriDoc AI
**Platform**: VeriDoc AI — Verified Document Intelligence & Fact-Grounded Knowledge Engine  
**Audit Date**: October 16, 2026  
**Auditor**: Senior Backend & GenAI Engineer, DevOps & QA Specialist  
**Repository Branch**: `main`  
**Python Runtime**: Python 3.11.5  

---

## Executive Summary

VeriDoc AI was subjected to an exhaustive technical audit, Gemini API integration overhaul, anti-hallucination vector retrieval debugging, end-to-end integration testing, and deployment assessment.

All critical blocking defects have been identified, remediated, and verified with automated test suites and live API execution:
1. **Gemini Model Update**: Replaced obsolete model references (`gemini-1.5-flash` and `gemini-2.5-flash`, which return `404 Not Found` for new API keys) with the actively supported, highly available Flash model `gemini-3.6-flash`, backed by resilient retry and fallback orchestration.
2. **SDK Modernization**: Validated and aligned the project with Google's modern `google-genai` SDK (v2.31.0), replacing deprecated calls and adding structured error handling.
3. **ChromaDB Cosine Metric & Similarity Threshold Fix**: Corrected the mathematical conversion from ChromaDB HNSW cosine distance ($d = 1 - \cos\theta$) to normalized cosine similarity ($s = 1 - d$), preventing irrelevant/orthogonal chunks from bypassing the `0.25` similarity threshold.
4. **Retriever Threshold Bypass Elimination**: Removed the fallback that fed ungrounded `raw_results` to the LLM on out-of-scope queries when zero chunks met the similarity threshold, enforcing strict anti-hallucination refusals with zero false citations.
5. **Runtime NameError Fix**: Fixed an undefined `logger` reference in `backend/app/api/routes_documents.py` that caused unhandled crashes during disk file deletions.
6. **Persistence & Full Stack Verification**: 100% of the 16 automated tests passed, live document upload (`sample_knowledge.pdf`) succeeded, factual in-scope questions returned grounded citations with exact page attribution, and ChromaDB vector persistence survived server restarts.

---

## A. Project Inventory

| Directory / File | Component Type | Purpose & Architecture Role |
|---|---|---|
| `backend/app/main.py` | Core Application | FastAPI ASGI entry point; mounts routes, configures CORS, serves static web assets, and provides global exception handling. |
| `backend/app/config.py` | Configuration | Pydantic `BaseSettings` manager; loads `.env` settings (`GEMINI_API_KEY`, `GEMINI_MODEL`, chunk hyperparameters, directories). |
| `backend/app/api/routes_documents.py` | API Controller | Handles document upload (`.pdf`, `.docx`, `.txt`, `.md`), chunk previewing, document listing, individual deletion, and database clearing. |
| `backend/app/api/routes_rag.py` | API Controller | Implements RAG query synthesis (`/api/rag/query`) and standalone context chunk inspection (`/api/rag/retrieve`). |
| `backend/app/api/routes_system.py` | API Controller | System diagnostics endpoint (`/api/system/health`) returning vector database counts, active LLM/embedding models, and hyperparameter status. |
| `backend/app/core/document_loader.py` | Ingestion Engine | Multi-format text extractor preserving page boundaries via `pypdf`, `python-docx`, and UTF-8/Latin-1 text loaders. |
| `backend/app/core/chunker.py` | Text Splitting | Splits extracted pages into overlapping semantic chunks with unique chunk IDs (`{filename}_p{page}_c{index}`) via `langchain_text_splitters`. |
| `backend/app/core/embeddings.py` | Vector Embeddings | Pluggable embedding providers: local `sentence-transformers` (`all-MiniLM-L6-v2`), cloud `google-genai` (`gemini-embedding-001`), and deterministic mock hash vectorizer. |
| `backend/app/core/vector_store.py` | Vector Database | ChromaDB `PersistentClient` with cosine HNSW space, handling indexing, deduplication, cosine similarity ranking, and document chunk purging. |
| `backend/app/core/retriever.py` | Context Retriever | Top-K relevance retrieval, threshold filtering, overview-mode detection, and multi-chunk page deduplication into formatted context blocks. |
| `backend/app/core/llm.py` | LLM Orchestrator | BaseLLMProvider interface with `GeminiLLMProvider` (`google-genai`), `MockLLMProvider`, and stubs for OpenAI/Anthropic with strict anti-hallucination prompt templates. |
| `backend/app/schemas/document.py` | Validation Schemas | Pydantic v2 schemas for document metadata, chunks, summaries, and upload/delete responses. |
| `backend/app/schemas/rag.py` | Validation Schemas | Pydantic v2 schemas for queries, citations, grounded responses, and context inspection. |
| `frontend/web/index.html` | Frontend Dashboard | Glassmorphic dark-theme web dashboard with interactive controls, upload zone, document viewer, and citation inspector. |
| `frontend/web/css/style.css` | Frontend Styling | Responsive layout, dark glassmorphism styling, status pills, and micro-animations. |
| `frontend/web/js/app.js` | Frontend Logic | Reactive JavaScript client; manages file upload progress, dynamic polling, chat messaging, and source citation card rendering. |
| `sample_documents/` | Test Data | Contains `sample_knowledge.pdf` (3-page enterprise cloud policy), `apartment_lease_agreement.txt`, and automated PDF generator script. |
| `tests/` | QA & Testing | Automated pytest suite: `test_chunker.py`, `test_document_loader.py`, `test_vector_store.py`, `test_rag_pipeline.py`, and `test_gemini_and_api.py`. |
| `render.yaml` | Deployment Config | Blueprint specification for deploying the application on Render PaaS. |
| `Dockerfile` & `.dockerignore` | Containerization | Production multi-stage container build and exclusion rules for portable deployment across Docker, Railway, Render, or AWS. |
| `.env.example` | Configuration Template | Sanitized template documenting all required environment variables with non-sensitive placeholders. |
| `.gitignore` | Version Control | Explicit exclusion list protecting `.env`, virtual environments, ChromaDB local databases, uploads, and caches from Git commits. |

---

## B. Feature Status

| Feature | Status | Verification Evidence |
|---|---|---|
| **Multi-Format Ingestion** | **WORKING** | Verified with `.pdf` (3-page `sample_knowledge.pdf`), `.txt`, `.md`, and `.docx`. Page boundaries and metadata preserved. |
| **Recursive Chunking** | **WORKING** | Validated chunk size (800) and overlap (150). Chunk IDs format `{filename}_p{page}_c{index}` verified in unit and integration tests. |
| **Embeddings Generation** | **WORKING** | Verified local Sentence Transformers (`all-MiniLM-L6-v2`, 384 dimensions) and cloud Gemini embeddings (`gemini-embedding-001`, 3072 dimensions). |
| **Vector Storage (ChromaDB)** | **WORKING** | Indexed chunks verified in `PersistentClient`. Cosine distance correctly converted to cosine similarity ($s = 1 - d$). |
| **Semantic Retrieval** | **WORKING** | Top-K retrieval verified. High-relevance chunks retrieved with similarity scores (e.g. 0.4831 for data retention query). |
| **Gemini LLM Generation** | **WORKING** | Live API test verified using `google-genai` SDK with `gemini-3.6-flash`. Answers accurately grounded in document context. |
| **Precision Citations** | **WORKING** | Document name (`sample_knowledge.pdf`), exact page number (Page 1), chunk index, and excerpts returned in API response. |
| **Anti-Hallucination Guardrails** | **WORKING** | Out-of-scope queries (e.g., "chocolate cake on Jupiter") correctly return refusal: *"I cannot find the answer to this question in the provided documents."* with `is_grounded: false` and `sources: []`. |
| **Offline / Mock Mode** | **WORKING** | When `GEMINI_API_KEY` is omitted or contains a placeholder (`your_...`), system safely activates `MockLLMProvider` without crash or unhandled error. |
| **ChromaDB Persistence** | **WORKING** | Verified survival of 6 indexed chunks from `sample_knowledge.pdf` after complete Uvicorn server termination and restart. |
| **Single-Document Deletion** | **WORKING** | `DELETE /api/documents/{filename}` verified; deletes all associated chunks from vector store and removes physical file. |
| **Bulk Clear** | **WORKING** | `POST /api/documents/clear` verified; resets collection and cleans storage directory. |
| **Frontend Web Interface** | **WORKING** | `GET /` serves HTML5 glassmorphic dashboard; dynamic status chips update via `/api/system/health`. |

---

## C. API Inventory

| HTTP Method | Endpoint Path | Purpose | Request Body / Params | Status Code | Test Result |
|---|---|---|---|---|---|
| `GET` | `/` | Web dashboard root interface | None | `200 OK` | **PASSED** (Serves HTML5 UI) |
| `GET` | `/docs` | OpenAPI / Swagger interactive docs | None | `200 OK` | **PASSED** (FastAPI documentation rendered) |
| `GET` | `/api/system/health` | System diagnostics & provider info | None | `200 OK` | **PASSED** (Healthy status, active models returned) |
| `POST` | `/api/documents/upload` | Upload and index document | `multipart/form-data` (`file`, optional chunk params) | `200 OK` / `400` / `415` / `422` | **PASSED** (6 chunks indexed for `sample_knowledge.pdf`) |
| `GET` | `/api/documents` | List all indexed documents | None | `200 OK` | **PASSED** (Document summaries and chunk counts returned) |
| `GET` | `/api/documents/{filename}/chunks` | Preview chunks of a document | Path: `filename` | `200 OK` / `404` | **PASSED** (Exact chunk IDs, page numbers, text returned) |
| `GET` | `/api/documents/{filename}/file` | Serve raw file for in-browser verification | Path: `filename` | `200 OK` / `404` | **PASSED** (Inline content-disposition served) |
| `DELETE` | `/api/documents/{filename}` | Delete single document & chunks | Path: `filename` | `200 OK` / `404` | **PASSED** (Chunks deleted from ChromaDB and disk) |
| `POST` | `/api/documents/clear` | Clear all documents & reset database | None | `200 OK` | **PASSED** (Collection reset, uploads cleaned) |
| `POST` | `/api/rag/retrieve` | Inspect retrieved chunks without LLM | `{"query": str, "top_k": int}` | `200 OK` | **PASSED** (Top matching chunks with similarity scores) |
| `POST` | `/api/rag/query` | End-to-end grounded RAG question answering | `{"query": str, "top_k": int, "score_threshold": float}` | `200 OK` / `502` | **PASSED** (Grounded answer with citations generated) |

---

## D. Issues Found & Remediated

### Issue VDOC-01: Obsolete & Incompatible Gemini Model Names
- **Severity**: Critical (Deployment & Generation Blocker)
- **Affected Files**: `backend/app/config.py`, `.env`, `.env.example`, `render.yaml`, `README.md`, `frontend/web/index.html`
- **Symptom / Error**: Calling `models/gemini-1.5-flash` or `models/gemini-2.5-flash` failed with `ClientError 404 NOT_FOUND: This model is no longer available to new users / not found for API version v1beta`. Calling `models/gemini-3.8-flash` frequently triggered `ServerError 503 UNAVAILABLE: This model is currently experiencing high demand`.
- **Root Cause**: Google deprecated `gemini-1.5-flash` and `gemini-2.5-flash` for new AI Studio projects. `gemini-3.8-flash` is active but suffers from severe transient 503 high-demand load shedding. In contrast, `gemini-3.6-flash` is fully available and responsive.
- **Fix Applied**:
  - Configured `gemini-3.6-flash` as the standard, stable default across `config.py`, `.env.example`, `render.yaml`, and `README.md`.
  - In `backend/app/core/llm.py`, implemented resilient retry and automatic fallback to `gemini-3.6-flash` if `gemini-3.8-flash` is configured and encounters a 503 surge.
  - Replaced hardcoded frontend label in `index.html` with dynamic initialization.
- **Verification Result**: Verified live via `google-genai` SDK; returned grounded responses in 1.4s without error.

### Issue VDOC-02: ChromaDB Cosine Metric vs Similarity Threshold Distortion
- **Severity**: High (Anti-Hallucination Guardrail Failure)
- **Affected Files**: `backend/app/core/vector_store.py`
- **Symptom / Error**: Irrelevant, orthogonal text received a similarity score of `0.50`, completely bypassing the configured `SIMILARITY_SCORE_THRESHOLD: 0.25`.
- **Root Cause**: ChromaDB with `hnsw:space="cosine"` returns cosine distance $d \in [0, 2]$, where $d = 1 - \cos\theta$. The codebase previously used $(2.0 - d) / 2.0$, which shifted orthogonal vectors ($d = 1.0$) to $0.50$. Consequently, unrelated queries were treated as valid 50% matches.
- **Fix Applied**: Corrected the conversion in `vector_store.py` to true cosine similarity bounded to positive correlation: `similarity = max(0.0, min(1.0, 1.0 - float(dist)))`. Identical vectors yield `1.0`, orthogonal vectors yield `0.0`, and opposite vectors yield `0.0`.
- **Verification Result**: Verified in integration tests; unrelated query chunks now receive scores $\le 0.10$ and are cleanly rejected by the `0.25` threshold.

### Issue VDOC-03: Context Retriever Threshold Bypass for Out-of-Scope Queries
- **Severity**: High (Anti-Hallucination Prompt Leak)
- **Affected Files**: `backend/app/core/retriever.py`
- **Symptom / Error**: When an out-of-scope query matched zero chunks above the threshold (`valid_results == []`), the retriever fell back to `raw_results[:candidate_k]`, feeding irrelevant chunks to the LLM and generating misleading citations.
- **Root Cause**: Defensive fallback logic intended for overview queries was applied unconditionally to all queries.
- **Fix Applied**: Updated `retriever.py` to strictly enforce `valid_results` for factual queries. Fallback to structural document chunks is now strictly restricted to queries detected as whole-document overviews (`is_overview == True`).
- **Verification Result**: Out-of-scope query test confirmed `sources: []`, `is_grounded: false`, and refusal text returned.

### Issue VDOC-04: Unhandled NameError on Missing Logger in Documents Route
- **Severity**: Medium (Runtime Crash on File Deletion)
- **Affected Files**: `backend/app/api/routes_documents.py`
- **Symptom / Error**: `NameError: name 'logger' is not defined` when an exception occurred while deleting disk files during `DELETE /api/documents/{filename}`.
- **Root Cause**: `logger.warning(...)` was called at line 189 without importing `logging` or instantiating `logger`.
- **Fix Applied**: Added `import logging` and `logger = logging.getLogger(__name__)` at top of `routes_documents.py`.
- **Verification Result**: Verified file deletion in unit and integration test suites; executes cleanly with no unhandled exceptions.

### Issue VDOC-05: Obsolete Embedding Model in Gemini Provider Default
- **Severity**: Medium (Cloud Embedding Provider Failure)
- **Affected Files**: `backend/app/config.py`, `backend/app/core/embeddings.py`
- **Symptom / Error**: Setting `EMBEDDING_PROVIDER=gemini` caused `ClientError 404 NOT_FOUND: models/text-embedding-004 is not found for API version v1beta`.
- **Root Cause**: `text-embedding-004` is no longer available in the current Gemini API endpoint. Google's active embedding models are `gemini-embedding-001` (3072 dimensions) and `gemini-embedding-2`. In addition, `config.py` had defaulted to `gemini` embeddings instead of local `sentence-transformers`.
- **Fix Applied**:
  - Aligned `backend/app/config.py` default to `EMBEDDING_PROVIDER: str = "sentence-transformers"` and `EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"`.
  - Updated `GeminiEmbeddingProvider` in `embeddings.py` to use `gemini-embedding-001` with dimension `3072`.
- **Verification Result**: Verified live embeddings generation for both `sentence-transformers` (dim: 384) and `gemini-embedding-001` (dim: 3072).

---

## E. Deployment Status & Platform Audit

### Current Deployment State
- **Status**: **NOT DEPLOYED (Local Environment Verified; Cloud Deployment Blocked on User Authorization & Credentials)**
- **Intended Platform**: **Render** (via `render.yaml`)

### Detailed Audit of Deployment Setup
1. **Configuration File**: `render.yaml` exists in the repository root.
   - **Pre-Audit State**: Configured with obsolete `gemini-1.5-flash` and `text-embedding-004`, which caused immediate 404 runtime crashes on Render.
   - **Post-Audit State**: Fixed with `gemini-3.6-flash` and lightweight CPU-only `torch` build command to prevent 1.5GB CUDA downloads and build timeouts.
2. **Ephemeral Disk Limitation on Render Free Tier**:
   - Render's Free web services run in ephemeral containers with no persistent disk.
   - Whenever the service restarts, redeploys, or spins down after 15 minutes of inactivity, `./data/chroma_db` and `./data/uploads` will be wiped, requiring re-uploading documents.
   - **Remediation**:
     - *Option 1 (Render Paid)*: Upgrade to Render Starter ($7/mo) and attach a Persistent Disk at `/app/data` with size 1GB ($0.25/mo), setting `CHROMA_PERSIST_DIR=/app/data/chroma_db` and `UPLOAD_DIR=/app/data/uploads`.
     - *Option 2 (Render Free Tier with Gemini Embeddings)*: If using the Free Tier, set `EMBEDDING_PROVIDER=gemini` and `EMBEDDING_MODEL=gemini-embedding-001`. This keeps RAM usage at ~120MB (well below the 512MB limit) and works smoothly for ephemeral demo sessions.
     - *Option 3 (Docker / Cloud Vector DB)*: Deploy using the provided `Dockerfile` to Railway, fly.io, or VPS with a persistent volume mount on `/app/data`.
3. **Memory Considerations on Free Tier**:
   - PyTorch + Sentence Transformers requires ~250MB–350MB of memory. On a 512MB free tier instance, multiple concurrent requests could trigger an Out-Of-Memory (OOM) kill.
   - The CPU-torch build command optimization (`pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu`) minimizes memory footprint.
4. **Cloud Deployment Access**:
   - Live Render deployment logs and credentials are external to this repository. Deployment triggers must be authorized by the repository owner via the Render dashboard.

---

## F. Test Results & Operational Verification

### Explicit Status Classifications

#### 1. FIXED
- [x] **VDOC-01**: Updated Gemini Flash model configuration from deprecated `gemini-1.5-flash` to active, responsive `gemini-3.6-flash` across backend config, `.env.example`, `render.yaml`, and documentation.
- [x] **VDOC-02**: Corrected ChromaDB cosine distance metric conversion in `vector_store.py` to true positive similarity ($1.0 - d$).
- [x] **VDOC-03**: Enforced strict threshold filtering in `retriever.py`, preventing out-of-scope queries from receiving irrelevant fallback chunks.
- [x] **VDOC-04**: Fixed unhandled `NameError: name 'logger' is not defined` crash in `routes_documents.py`.
- [x] **VDOC-05**: Updated Gemini cloud embeddings model from obsolete `text-embedding-004` to `gemini-embedding-001` (dimension 3072).
- [x] **VDOC-06**: Optimized Render build command and `Dockerfile` to install CPU-only PyTorch, cutting container image size by over 60%.

#### 2. VERIFIED
- [x] **Document Ingestion**: Verified extraction across `.pdf` (`sample_knowledge.pdf`), `.docx`, `.txt`, and `.md`.
- [x] **Semantic Chunking**: 800 char chunk size, 150 char overlap, unique chunk IDs verified.
- [x] **Embeddings Generation**: Verified local `sentence-transformers` (`all-MiniLM-L6-v2`) and cloud Gemini embeddings.
- [x] **Vector Storage & Persistence**: Verified ChromaDB persistence across complete server termination and restart.
- [x] **Live Gemini LLM Generation**: In-scope queries returned factual, grounded answers citing `sample_knowledge.pdf (Page 1)`.
- [x] **Anti-Hallucination Guardrails**: Out-of-scope query cleanly returned refusal with zero citations and `is_grounded: false`.
- [x] **Offline / Mock Mode**: Verified fallback to `MockLLMProvider` when `GEMINI_API_KEY` is omitted or placeholder.
- [x] **All 16 Pytest Tests**: 100% passed in `.venv` test runner.
- [x] **Secret Safety**: Verified `.env` is ignored by `.gitignore` and never committed to Git history.

#### 3. BLOCKED
- [ ] **Git Remote Push**: Requires explicit user approval before running `git push origin main`.
- [ ] **Render Cloud Deployment**: Requires user's Render dashboard access to connect the GitHub repository and enter `GEMINI_API_KEY`.

#### 4. NOT TESTED
- [ ] **Live Public Cloud URL & Cloud Logs**: Cannot be tested until the repository is pushed to GitHub and deployed on Render by the user.

---

## G. GitHub Readiness & Secret Safety

1. **Secret Leak Audit**:
   - Verified that `.env` is completely excluded by `.gitignore` (`.gitignore:13:.env`).
   - `git status -s --ignored` confirms `.env` is marked `!!` (Ignored).
   - `git log -S "GEMINI_API_KEY"` confirms no API keys were committed in Git history.
   - `.env.example` contains sanitized placeholder `your_gemini_api_key_here`.
   - `PROJECT_AUDIT_REPORT.md` contains zero credentials or secrets.
2. **Working Tree Status**:
   - Working tree has all fixes and new test files staged or untracked cleanly.
   - Remote branch `origin/main` has not been modified. No changes will be pushed without user authorization.

---

## H. Prioritized Action Checklist for User

- [ ] **Step 1: Review Local Changes**: Review the diff using `git status` and `git diff`.
- [ ] **Step 2: Commit Working Tree**:
  ```bash
  git add .env.example README.md render.yaml Dockerfile .dockerignore \
          backend/ frontend/ tests/ PROJECT_AUDIT_REPORT.md
  git commit -m "fix(rag): update Gemini model to gemini-3.6-flash, fix Chroma cosine metric, and add tests"
  ```
- [ ] **Step 3: Push to GitHub**:
  ```bash
  git push origin main
  ```
- [ ] **Step 4: Deploy on Render**:
  1. Open [dashboard.render.com](https://dashboard.render.com)
  2. Click **New +** -> **Blueprint** (or **Web Service**)
  3. Connect repository `Srujanaaddanki/VerifyDocu`
  4. In **Environment Variables**, set:
     - `GEMINI_API_KEY`: *(paste your real Google AI Studio key)*
     - `GEMINI_MODEL`: `gemini-3.6-flash`
     - `LLM_PROVIDER`: `gemini`
     - `EMBEDDING_PROVIDER`: `sentence-transformers` (or `gemini` if memory is constrained on Free Tier)
  5. Click **Apply / Deploy**
- [ ] **Step 5: Post-Deployment Smoke Test**:
  - Visit `https://<your-service-name>.onrender.com/api/system/health`
  - Upload `sample_documents/sample_knowledge.pdf` on the web UI
  - Ask: *"What is the customer data retention policy?"*

---

## I. Final Verdict

- **Ready for Local Demonstration**: **YES (100%)** — Server runs locally on port 8000/8005, web dashboard is fully interactive, Gemini RAG synthesis works with verified citations, and anti-hallucination refusals are strictly enforced.
- **Ready for GitHub**: **YES (100%)** — Secrets are excluded, `.gitignore` is validated, and tests are passing.
- **Ready for Public Cloud Deployment**: **YES (Configuration complete, waiting for user Git push & Render dashboard trigger)**.
