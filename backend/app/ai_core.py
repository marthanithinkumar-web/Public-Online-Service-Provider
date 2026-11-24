"""Provider-neutral compatibility facade for POSP AI workflows."""

from dataclasses import dataclass
import os
import re
import threading

from .ai.providers import AIProvider, GeminiProvider, OpenAIProvider, ProviderError
from .ai.text import extract_gemini_text as _extract_gemini_text
from .ai.text import extract_openai_text as _extract_openai_text


_PROVIDERS: dict[str, AIProvider] = {"openai": OpenAIProvider(), "gemini": GeminiProvider()}
_DEFAULT_MODELS = {"openai": "gpt-5", "gemini": "gemini-3.5-flash-lite"}
_MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_health_lock = threading.Lock()
_last_provider_state: dict[str, str] = {}


@dataclass(frozen=True)
class AISettings:
    enabled: bool
    provider: str | None
    model: str | None
    error: str | None = None


def settings() -> AISettings:
    """Load explicit provider settings; never choose a provider from keys alone."""
    enabled_value = os.getenv("POSP_AI_ENABLED", "true").strip().lower()
    if enabled_value not in {"true", "false", "1", "0", "yes", "no"}:
        return AISettings(False, None, None, "POSP_AI_ENABLED must be a boolean value.")
    enabled = enabled_value in {"true", "1", "yes"}
    selected = (os.getenv("POSP_AI_PROVIDER") or "").strip().lower()
    if not enabled or selected == "disabled":
        return AISettings(False, None, None)
    if selected == 'builtin' or os.getenv('RENDER', '').lower() == 'true':
        return AISettings(True, 'builtin', 'posp-knowledge')
    if not selected:
        return AISettings(False, None, None, "POSP_AI_PROVIDER must explicitly select openai or gemini.")
    if selected not in _PROVIDERS:
        return AISettings(False, None, None, "POSP_AI_PROVIDER must be openai, gemini, or disabled.")

    model = (
        os.getenv(f"POSP_{selected.upper()}_MODEL")
        or os.getenv("POSP_AI_MODEL")
        or _DEFAULT_MODELS[selected]
    ).strip()
    wrong_provider = (selected == "gemini" and not model.startswith("gemini-")) or (
        selected == "openai" and model.startswith("gemini-")
    )
    if not _MODEL_RE.fullmatch(model) or wrong_provider:
        return AISettings(False, selected, None, f"POSP_AI_MODEL is invalid for the selected {selected} provider.")
    return AISettings(True, selected, model)


def configured_provider():
    return settings().provider


def configured_model():
    return settings().model


def is_configured():
    config = settings()
    if config.provider == 'builtin':
        return True
    return bool(config.enabled and config.provider and _PROVIDERS[config.provider].is_configured())


def provider_health():
    """Report configuration and last observed request status without a paid probe."""
    config = settings()
    providers = {}
    for name, adapter in _PROVIDERS.items():
        key_configured = adapter.is_configured()
        selected = config.provider == name
        if not config.enabled and not config.error:
            state = "disabled"
        elif selected and (config.error or not key_configured):
            state = "unavailable"
        elif selected:
            with _health_lock:
                state = _last_provider_state.get(name, "configured")
        else:
            state = "configured" if key_configured else "disabled"
        providers[name] = {
            "state": state,
            "configured": key_configured,
            "available": state == "available",
            "selected": selected,
            "model": config.model if selected else None,
        }
    if config.provider == 'builtin':
        providers['builtin'] = {'state': 'available', 'configured': True, 'available': True, 'selected': True, 'model': config.model}
        for name in _PROVIDERS:
            providers[name]['state'] = 'disabled'
    state = (
        providers[config.provider]["state"] if config.provider in providers
        else ("disabled" if not config.enabled and not config.error else "unavailable")
    )
    return {"enabled": config.enabled, "provider": config.provider, "model": config.model,
            "state": state, "error": config.error, "providers": providers}


def call_model(instructions, prompt, max_output_tokens=900):
    """Retain the existing (answer, safe_error) route contract."""
    config = settings()
    if config.error:
        return None, config.error
    if not config.enabled:
        return None, "AI is disabled."
    if config.provider == 'builtin':
        return None, 'External AI is disabled by the zero-cost policy.'
    provider = _PROVIDERS[config.provider]
    if not provider.is_configured():
        return None, f"{provider.display_name} AI is not configured on the backend."
    try:
        answer = provider.generate(instructions=instructions, prompt=prompt, model=config.model,
                                   max_output_tokens=max_output_tokens)
        if answer and answer.strip():
            with _health_lock:
                _last_provider_state[config.provider] = "available"
            return answer.strip(), None
        with _health_lock:
            _last_provider_state[config.provider] = "unavailable"
        return None, f"{provider.display_name} returned no text response."
    except ProviderError as exc:
        with _health_lock:
            _last_provider_state[config.provider] = "unavailable"
        return None, exc.safe_message
    except Exception:
        with _health_lock:
            _last_provider_state[config.provider] = "unavailable"
        return None, f"{provider.display_name} AI is temporarily unavailable."


def redact_sensitive_text(value):
    """Remove common direct identifiers before client-authored text leaves POSP."""
    text = str(value or "")
    text = re.sub(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "[email removed]", text, flags=re.I)
    text = re.sub(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{9}(?!\d)", "[phone removed]", text)
    text = re.sub(r"\b[A-Z]{5}\d{4}[A-Z]\b", "[identifier removed]", text, flags=re.I)
    text = re.sub(r"\b(?:aadhaar|aadhar|uid)\s*(?:number|no\.?|#)?\s*[:#-]?\s*(?:\d[ -]?){11}\d\b", "[identifier removed]", text, flags=re.I)
    return text
