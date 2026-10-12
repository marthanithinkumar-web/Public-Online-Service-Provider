"""Shared AI provider layer for POSP customer and administrator workflows.

Provider selection supports Gemini and OpenAI. Credentials remain server-side.
"""
import os

import requests


def configured_provider():
    """Choose an explicitly configured provider, or auto-detect from available keys."""
    requested = (os.getenv("POSP_AI_PROVIDER") or "").strip().lower()
    if requested in {"gemini", "openai"}:
        return requested
    if (os.getenv("GEMINI_API_KEY") or "").strip():
        return "gemini"
    if (os.getenv("OPENAI_API_KEY") or "").strip():
        return "openai"
    return "gemini"


def configured_model():
    """Return the configured model, with a provider-appropriate default."""
    model = (os.getenv("POSP_AI_MODEL") or "").strip()
    provider = configured_provider()
    if provider == "gemini":
        return model if model.startswith("gemini-") else "gemini-2.5-flash"
    return model if model and not model.startswith("gemini-") else "gpt-6-luna"


def is_configured():
    """Whether the selected provider has a key configured."""
    if configured_provider() == "gemini":
        return bool((os.getenv("GEMINI_API_KEY") or "").strip())
    return bool((os.getenv("OPENAI_API_KEY") or "").strip())


def _extract_openai_text(payload):
    if not isinstance(payload, dict):
        return ""
    for item in payload.get("output", []) or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []) or []:
            if isinstance(content, dict) and content.get("type") in {"output_text", "text"} and content.get("text"):
                return content["text"]
    return ""


def _extract_gemini_text(payload):
    if not isinstance(payload, dict):
        return ""
    for candidate in payload.get("candidates", []) or []:
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content") or {}
        if not isinstance(content, dict):
            continue
        for part in content.get("parts", []) or []:
            if isinstance(part, dict) and isinstance(part.get("text"), str) and part["text"].strip():
                return part["text"]
    return ""


def _safe_provider_error(provider, status_code):
    """Classify provider failures without exposing raw provider payloads."""
    if provider == "gemini":
        if status_code == 400:
            return "Gemini rejected the request (HTTP 400). Check request format and model configuration."
        if status_code == 401:
            return "Gemini authentication failed (HTTP 401). Check API key configuration."
        if status_code == 403:
            return "Gemini access was denied (HTTP 403). Check project permissions and API restrictions."
        if status_code == 404:
            return "Gemini model was not found or is not accessible to this API key (HTTP 404). Check model availability for this key."
        if status_code == 429:
            return "Gemini rate limit or free-tier quota was reached (HTTP 429). Check quota and retry later."
        if status_code >= 500:
            return f"Gemini is temporarily unavailable (HTTP {status_code}). Please retry later."
    return f"{provider.title()} request failed (HTTP {status_code})."


def probe_provider_access():
    """Read-only Gemini model metadata check; it never generates content."""
    provider = configured_provider()
    model = configured_model()
    if not is_configured():
        return {"provider": provider, "model": model, "configured": False, "ready": False,
                "status": "not_configured", "message": f"{provider.title()} API key is not configured.",
                "supported_methods": [], "available_models": []}
    if provider != "gemini":
        return {"provider": provider, "model": model, "configured": True, "ready": False,
                "status": "not_probed",
                "message": "No OpenAI request was made; this read-only check only probes Gemini model metadata.",
                "supported_methods": [], "available_models": []}
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    headers = {"x-goog-api-key": api_key}
    try:
        response = requests.get(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}",
            headers=headers, timeout=(3, 10),
        )
        if response.status_code == 404:
            available = []
            try:
                listing = requests.get(
                    "https://generativelanguage.googleapis.com/v1beta/models",
                    headers=headers, timeout=(3, 10),
                )
                if listing.status_code == 200:
                    payload = listing.json()
                    for item in payload.get("models", []) if isinstance(payload, dict) else []:
                        if not isinstance(item, dict):
                            continue
                        name = str(item.get("name") or "").removeprefix("models/")
                        methods = item.get("supportedGenerationMethods") or []
                        if (name.startswith("gemini-") and isinstance(methods, list)
                                and "generateContent" in methods
                                and not any(word in name.lower() for word in ("image", "tts", "live", "audio", "transcribe", "embedding"))):
                            available.append(name)
            except (requests.RequestException, ValueError, TypeError):
                available = []
            available = sorted(set(available))[:50]
            message = _safe_provider_error(provider, 404)
            if available:
                message += " Available text models are listed below; no model was changed automatically."
            return {"provider": provider, "model": model, "configured": True, "ready": False,
                    "status": "model_unavailable", "message": message,
                    "supported_methods": [], "available_models": available}
        if response.status_code >= 400:
            status = "authentication_error" if response.status_code == 401 else "permission_denied" if response.status_code == 403 else "rate_limited" if response.status_code == 429 else "provider_error"
            return {"provider": provider, "model": model, "configured": True, "ready": False,
                    "status": status, "message": _safe_provider_error(provider, response.status_code),
                    "supported_methods": [], "available_models": []}
        payload = response.json()
        if not isinstance(payload, dict):
            return {"provider": provider, "model": model, "configured": True, "ready": False,
                    "status": "invalid_response", "message": "Gemini returned invalid model metadata.",
                    "supported_methods": [], "available_models": []}
        methods = payload.get("supportedGenerationMethods") or []
        methods = sorted(set(str(method) for method in methods if isinstance(method, str))) if isinstance(methods, list) else []
        ready = "generateContent" in methods
        return {"provider": provider, "model": model, "configured": True, "ready": ready,
                "status": "ready" if ready else "unsupported_method",
                "message": "Configured Gemini model is accessible and supports generateContent." if ready else "Configured model does not advertise generateContent.",
                "supported_methods": methods, "available_models": []}
    except requests.Timeout:
        return {"provider": provider, "model": model, "configured": True, "ready": False,
                "status": "timeout", "message": "Gemini model-access check timed out. Retry later.",
                "supported_methods": [], "available_models": []}
    except requests.RequestException:
        return {"provider": provider, "model": model, "configured": True, "ready": False,
                "status": "network_error", "message": "Gemini model-access check could not reach the provider.",
                "supported_methods": [], "available_models": []}
    except (ValueError, TypeError):
        return {"provider": provider, "model": model, "configured": True, "ready": False,
                "status": "invalid_response", "message": "Gemini returned invalid model metadata.",
                "supported_methods": [], "available_models": []}


def call_model(instructions, prompt, max_output_tokens=900):
    """Call the selected provider and return (answer, safe_error)."""
    provider = configured_provider()
    if not is_configured():
        return None, f"{provider.title()} AI is not configured on the backend."

    try:
        if provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY", "").strip()
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{configured_model()}:generateContent",
                headers={
                    "x-goog-api-key": api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "systemInstruction": {"parts": [{"text": instructions}]},
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": max_output_tokens},
                },
                timeout=45,
            )
            if response.status_code >= 400:
                # Keep credentials and provider response details out of client-visible errors.
                return None, _safe_provider_error(provider, response.status_code)
            answer = _extract_gemini_text(response.json())
        else:
            api_key = os.getenv("OPENAI_API_KEY", "").strip()
            response = requests.post(
                "https://api.openai.com/v1/responses",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": configured_model(),
                    "instructions": instructions,
                    "input": prompt,
                    "max_output_tokens": max_output_tokens,
                },
                timeout=45,
            )
            if response.status_code >= 400:
                return None, _safe_provider_error(provider, response.status_code)
            answer = _extract_openai_text(response.json())

        return (answer.strip(), None) if answer and answer.strip() else (None, f"{provider.title()} returned no text response.")
    except requests.Timeout:
        return None, f"{provider.title()} request timed out. Please retry."
    except requests.RequestException:
        return None, f"{provider.title()} could not be reached. Please retry."
    except (ValueError, TypeError):
        return None, f"{provider.title()} returned an invalid response."
