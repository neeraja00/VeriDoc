"""Main FastAPI application entrypoint."""
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from backend.app.config import settings
from backend.app.api.routes_documents import router as documents_router
from backend.app.api.routes_rag import router as rag_router
from backend.app.api.routes_system import router as system_router

app = FastAPI(
    title="VeriDoc AI: Verified Document Intelligence API",
    description="End-to-end RAG knowledge engine with ChromaDB, Sentence Transformers, and Gemini.",
    version="1.0.0",
)

# CORS middleware for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(documents_router)
app.include_router(rag_router)
app.include_router(system_router)

# Mount frontend web assets
WEB_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "web"
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_ui():
        """Serves the primary web dashboard interface."""
        index_file = WEB_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return JSONResponse({"message": "VeriDoc AI API is running. UI files not found."})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global fallback exception handler to return clean JSON error responses."""
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )
