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
    if (os.getenv("GEMINI_API_KEY") or "").strip() and not (os.getenv("OPENAI_API_KEY") or "").strip():
        return "gemini"
    return "openai"


def configured_model():
    """Return the configured model, with a provider-appropriate default."""
    model = (os.getenv("POSP_AI_MODEL") or "").strip()
    if model:
        return model
    return "gemini-2.5-flash" if configured_provider() == "gemini" else "gpt-6-luna"


def is_configured():
    """Whether the selected provider has a key configured."""
    if configured_provider() == "gemini":
        return bool((os.getenv("GEMINI_API_KEY") or "").strip())
    return bool((os.getenv("OPENAI_API_KEY") or "").strip())


def _extract_openai_text(payload):
    for item in payload.get("output", []):
        for content in item.get("content", []) or []:
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                return content["text"]
    return ""


def _extract_gemini_text(payload):
    for candidate in payload.get("candidates", []) or []:
        content = candidate.get("content") or {}
        for part in content.get("parts", []) or []:
            if part.get("text"):
                return part["text"]
    return ""


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
                return None, f"Gemini request failed (HTTP {response.status_code})."
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
                return None, f"OpenAI request failed (HTTP {response.status_code})."
            answer = _extract_openai_text(response.json())

        return (answer.strip(), None) if answer and answer.strip() else (None, f"{provider.title()} returned no text response.")
    except (requests.RequestException, ValueError, TypeError):
        return None, f"{provider.title()} could not be reached or returned an invalid response."
