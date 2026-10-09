from app import ai_core


def test_configured_model_defaults_to_gpt_61_sol(monkeypatch):
    monkeypatch.delenv("POSP_AI_MODEL", raising=False)
    assert ai_core.configured_model() == "gpt-6.1-sol"


def test_configured_model_respects_environment(monkeypatch):
    monkeypatch.setenv("POSP_AI_MODEL", "custom-model-id")
    assert ai_core.configured_model() == "custom-model-id"


def test_reasoning_effort_defaults_to_medium(monkeypatch):
    monkeypatch.delenv("POSP_AI_REASONING_EFFORT", raising=False)
    assert ai_core.configured_reasoning_effort() == "medium"


def test_invalid_reasoning_effort_falls_back_to_medium(monkeypatch):
    monkeypatch.setenv("POSP_AI_REASONING_EFFORT", "surprise")
    assert ai_core.configured_reasoning_effort() == "medium"


def test_reasoning_effort_accepts_supported_setting(monkeypatch):
    monkeypatch.setenv("POSP_AI_REASONING_EFFORT", "high")
    assert ai_core.configured_reasoning_effort() == "high"
