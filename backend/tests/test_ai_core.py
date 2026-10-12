import requests
import pytest

from app import ai_core


class FakeResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self.payload = {} if payload is None else payload

    def json(self):
        return self.payload


def configure_gemini(monkeypatch):
    monkeypatch.setenv("POSP_AI_PROVIDER", "gemini")
    monkeypatch.setenv("POSP_AI_MODEL", "gemini-2.5-flash")
    monkeypatch.setenv("GEMINI_API_KEY", "dummy")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def test_gemini_success(monkeypatch):
    configure_gemini(monkeypatch)
    monkeypatch.setattr(ai_core.requests, "post", lambda *a, **k: FakeResponse(
        200, {"candidates": [{"content": {"parts": [{"text": "POSP is ready."}]}}]}
    ))
    answer, error = ai_core.call_model("instructions", "prompt")
    assert answer == "POSP is ready."
    assert error is None


@pytest.mark.parametrize(
    ("status_code", "expected"),
    [(401, "authentication failed"), (403, "access was denied"),
     (404, "not found or is not accessible"), (429, "free-tier quota"),
     (503, "temporarily unavailable")],
)
def test_provider_http_errors_are_safe(monkeypatch, status_code, expected):
    configure_gemini(monkeypatch)
    monkeypatch.setattr(ai_core.requests, "post", lambda *a, **k: FakeResponse(
        status_code, {"error": {"message": "provider detail must not leak"}}
    ))
    answer, error = ai_core.call_model("instructions", "prompt")
    assert answer is None
    assert expected in error
    assert "provider detail must not leak" not in error
    assert "dummy" not in error


def test_provider_timeout_is_safe(monkeypatch):
    configure_gemini(monkeypatch)
    monkeypatch.setattr(ai_core.requests, "post", lambda *a, **k: (_ for _ in ()).throw(requests.Timeout()))
    answer, error = ai_core.call_model("instructions", "prompt")
    assert answer is None
    assert "timed out" in error


def test_malformed_gemini_response_returns_empty_text(monkeypatch):
    configure_gemini(monkeypatch)
    monkeypatch.setattr(ai_core.requests, "post", lambda *a, **k: FakeResponse(200, []))
    answer, error = ai_core.call_model("instructions", "prompt")
    assert answer is None
    assert "no text response" in error


def test_probe_reports_supported_generate_content_method(monkeypatch):
    configure_gemini(monkeypatch)
    monkeypatch.setattr(ai_core.requests, "get", lambda *a, **k: FakeResponse(200, {
        "name": "models/gemini-2.5-flash",
        "supportedGenerationMethods": ["generateContent", "countTokens"],
    }))
    result = ai_core.probe_provider_access()
    assert result["ready"] is True
    assert result["status"] == "ready"
    assert "generateContent" in result["supported_methods"]


def test_probe_lists_available_text_model_after_404(monkeypatch):
    configure_gemini(monkeypatch)
    def fake_get(url, **kwargs):
        if url.endswith("/models/gemini-2.5-flash"):
            return FakeResponse(404, {"error": {"message": "not public"}})
        return FakeResponse(200, {"models": [
            {"name": "models/gemini-3.5-flash", "supportedGenerationMethods": ["generateContent"]},
            {"name": "models/gemini-2.5-flash-image", "supportedGenerationMethods": ["generateContent"]},
        ]})
    monkeypatch.setattr(ai_core.requests, "get", fake_get)
    result = ai_core.probe_provider_access()
    assert result["status"] == "model_unavailable"
    assert result["available_models"] == ["gemini-3.5-flash"]
    assert "not public" not in result["message"]


def test_probe_never_calls_openai(monkeypatch):
    monkeypatch.setenv("POSP_AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    calls = []
    monkeypatch.setattr(ai_core.requests, "get", lambda *a, **k: calls.append(a))
    result = ai_core.probe_provider_access()
    assert result["status"] == "not_probed"
    assert calls == []


def test_automatic_provider_prefers_gemini_when_both_keys_exist(monkeypatch):
    monkeypatch.delenv("POSP_AI_PROVIDER", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "dummy")
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    assert ai_core.configured_provider() == "gemini"
