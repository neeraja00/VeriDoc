"""Comprehensive unit and integration tests for Gemini integration, API error handling,
offline mode fallback, and FastAPI endpoints.
"""
import os
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.main import app
from backend.app.core.llm import (
    get_llm_provider,
    GeminiLLMProvider,
    MockLLMProvider,
)
from backend.app.schemas.rag import SourceCitation


client = TestClient(app)


def test_offline_mode_fallback():
    """Verifies that missing or placeholder GEMINI_API_KEY activates MockLLMProvider."""
    with patch.object(settings, "GEMINI_API_KEY", ""):
        provider = get_llm_provider("gemini")
        assert isinstance(provider, MockLLMProvider)
        assert provider.provider_name == "mock"

    with patch.object(settings, "GEMINI_API_KEY", "your_gemini_api_key_here"):
        provider = get_llm_provider("gemini")
        assert isinstance(provider, MockLLMProvider)
        assert provider.provider_name == "mock"


def test_invalid_llm_provider_raises():
    """Verifies that an unsupported provider name raises a ValueError."""
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        get_llm_provider("unsupported_ai_vendor")


def test_gemini_error_handling_mappings():
    """Verifies that google.genai API errors are translated into clean, actionable exceptions."""
    from google.genai.errors import APIError

    sample_citation = SourceCitation(
        document_name="doc.txt",
        page_number=1,
        chunk_index=0,
        chunk_id="doc_p1_c0",
        similarity_score=0.9,
        content="Sample content",
        excerpt="Sample excerpt"
    )

    provider = GeminiLLMProvider(api_key="mock_key_test", model_name="gemini-3.6-flash")

    # 401 Unauthorized
    with patch.object(provider, "_get_client") as mock_get_client:
        mock_client = MagicMock()
        err_401 = APIError("API key not valid", None)
        err_401.code = 401
        mock_client.models.generate_content.side_effect = err_401
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="authentication failed"):
            provider.generate_answer("test question", [sample_citation], "context")

    # 404 Model Not Found
    with patch.object(provider, "_get_client") as mock_get_client:
        mock_client = MagicMock()
        err_404 = APIError("Model not found", None)
        err_404.code = 404
        mock_client.models.generate_content.side_effect = err_404
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="not found"):
            provider.generate_answer("test question", [sample_citation], "context")

    # 429 Quota Exhausted
    with patch.object(provider, "_get_client") as mock_get_client:
        mock_client = MagicMock()
        err_429 = APIError("Resource exhausted", None)
        err_429.code = 429
        mock_client.models.generate_content.side_effect = err_429
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="quota exhausted"):
            provider.generate_answer("test question", [sample_citation], "context")


def test_gemini_ssl_verification_setting(monkeypatch):
    """Verifies that SSL certificate verification is enabled by default, configurable via VERIFY_SSL,
    correctly parsed from environment variables, and fails loudly rather than silently bypassing settings.
    """
    from backend.app.config import Settings
    from backend.app.core.embeddings import GeminiEmbeddingProvider

    # 1. Default Settings check: VERIFY_SSL must be True
    s_default = Settings()
    assert s_default.VERIFY_SSL is True

    # 2. Environment variable parsing check for "false" / "true"
    monkeypatch.setenv("VERIFY_SSL", "false")
    s_false = Settings()
    assert s_false.VERIFY_SSL is False

    monkeypatch.setenv("VERIFY_SSL", "true")
    s_true = Settings()
    assert s_true.VERIFY_SSL is True

    # 3. Provider instance default and overrides
    p_default = GeminiLLMProvider(api_key="mock_key")
    assert p_default._verify_ssl is True

    p_custom = GeminiLLMProvider(api_key="mock_key", verify_ssl=False)
    assert p_custom._verify_ssl is False

    # 4. Verify client creation passes the verify option to HttpOptions
    with patch("google.genai.Client") as mock_genai_client:
        mock_instance = MagicMock()
        mock_genai_client.return_value = mock_instance

        # Test verify=True
        p_true = GeminiLLMProvider(api_key="mock_key", verify_ssl=True)
        client = p_true._get_client()
        assert client is mock_instance
        call_kwargs = mock_genai_client.call_args.kwargs
        assert call_kwargs["api_key"] == "mock_key"
        assert "http_options" in call_kwargs
        assert getattr(call_kwargs["http_options"], "client_args", {}).get("verify") is True

        # Test verify=False
        p_false = GeminiLLMProvider(api_key="mock_key", verify_ssl=False)
        p_false._get_client()
        call_kwargs_false = mock_genai_client.call_args.kwargs
        assert getattr(call_kwargs_false["http_options"], "client_args", {}).get("verify") is False

    # 5. Verify that client initialization failures raise RuntimeError and do not silently fall back
    with patch("google.genai.Client", side_effect=Exception("Connection handshake error")):
        p_fail = GeminiLLMProvider(api_key="mock_key", verify_ssl=True)
        with pytest.raises(RuntimeError, match="Failed to initialize Gemini client with VERIFY_SSL=True"):
            p_fail._get_client()

        p_emb_fail = GeminiEmbeddingProvider(api_key="mock_key", verify_ssl=True)
        with pytest.raises(RuntimeError, match="Failed to initialize Gemini embeddings client with VERIFY_SSL=True"):
            p_emb_fail._get_client()


def test_real_gemini_live_call():
    """Integration test that performs an actual generation call via Gemini if configured."""
    api_key = settings.GEMINI_API_KEY
    if not api_key or api_key.startswith("your_"):
        pytest.skip("GEMINI_API_KEY not configured for live Gemini API integration test.")

    try:
        provider = GeminiLLMProvider(api_key=api_key, model_name="gemini-3.6-flash")
        citation = SourceCitation(
            document_name="test_memo.txt",
            page_number=1,
            chunk_index=0,
            chunk_id="test_memo_p1_c0",
            similarity_score=0.95,
            content="Project Apollo was launched in May 1961 by President John F. Kennedy.",
            excerpt="Project Apollo was launched..."
        )
        context = "--- [Source 1]: test_memo.txt (Page 1) ---\nProject Apollo was launched in May 1961 by President John F. Kennedy."
        answer = provider.generate_answer(
            question="When was Project Apollo launched and by whom?",
            citations=[citation],
            context_block=context
        )
        assert "1961" in answer
        assert "Kennedy" in answer
    except Exception as e:
        err_msg = str(e)
        if "quota" in err_msg.lower() or "503" in err_msg.lower() or "rate" in err_msg.lower():
            pytest.skip(f"Live Gemini API rate limit or high demand: {err_msg}")
        raise


def test_api_endpoints_workflow():
    """Tests the full API endpoint suite via FastAPI TestClient."""
    with patch("backend.app.api.routes_rag.get_llm_provider", return_value=MockLLMProvider()):
        # 1. Health check
        res = client.get("/api/system/health")
        assert res.status_code == 200
        health_data = res.json()
        assert health_data["status"] == "healthy"
        assert "vector_store" in health_data
        assert "providers" in health_data

        # 2. UI root endpoint
        res_ui = client.get("/")
        assert res_ui.status_code == 200
        assert "text/html" in res_ui.headers.get("content-type", "")

        # 3. Document upload
        sample_text = (
            "Lease Agreement Summary:\n"
            "Monthly rent is $2,400 due on the first day of each calendar month.\n"
            "Security deposit is $2,400 refundable within 30 days of move out.\n"
            "Quiet hours are strictly enforced between 10:00 PM and 7:00 AM."
        )
        files = {"file": ("lease_agreement_test.txt", sample_text.encode("utf-8"), "text/plain")}
        res_upload = client.post("/api/documents/upload", files=files)
        assert res_upload.status_code == 200
        upload_data = res_upload.json()
        assert upload_data["success"] is True
        assert upload_data["filename"] == "lease_agreement_test.txt"
        assert upload_data["total_chunks"] >= 1

        # 4. List documents
        res_list = client.get("/api/documents")
        assert res_list.status_code == 200
        list_data = res_list.json()
        assert any(d["filename"] == "lease_agreement_test.txt" for d in list_data["documents"])

        # 5. Get document chunks
        res_chunks = client.get("/api/documents/lease_agreement_test.txt/chunks")
        assert res_chunks.status_code == 200
        chunks_data = res_chunks.json()
        assert len(chunks_data) >= 1
        assert "rent is $2,400" in chunks_data[0]["content"]

        # 6. Retrieve context
        res_retrieve = client.post("/api/rag/retrieve", json={"query": "What is the monthly rent amount?"})
        assert res_retrieve.status_code == 200
        ret_data = res_retrieve.json()
        assert ret_data["total_retrieved"] >= 1

        # 7. RAG Query (in-scope question)
        res_query = client.post("/api/rag/query", json={"query": "What is the monthly rent?"})
        assert res_query.status_code == 200
        query_data = res_query.json()
        assert query_data["is_grounded"] is True
        assert len(query_data["sources"]) >= 1
        assert "2,400" in query_data["answer"] or "$2,400" in query_data["answer"]

        # 8. RAG Query (out-of-scope question - anti-hallucination)
        res_out = client.post(
            "/api/rag/query",
            json={"query": "What is the capital city of Mars?", "score_threshold": 0.4}
        )
        assert res_out.status_code == 200
        out_data = res_out.json()
        assert out_data["is_grounded"] is False
        assert "cannot find the answer" in out_data["answer"].lower()

        # 9. Delete document
        res_del = client.delete("/api/documents/lease_agreement_test.txt")
        assert res_del.status_code == 200
        assert res_del.json()["success"] is True

        # 10. Clear documents
        res_clear = client.post("/api/documents/clear")
        assert res_clear.status_code == 200
        assert res_clear.json()["success"] is True
