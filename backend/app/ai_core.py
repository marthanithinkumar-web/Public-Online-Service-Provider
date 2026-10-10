"""Shared AI provider layer for POSP customer and administrator workflows.

Provider selection is server-side. Keep API keys in Render environment variables.
"""
import os
import requests

def configured_provider():
    """Return configured provider, preserving OpenAI as the legacy default."""
    provider = (os.getenv("POSP_AI_PROVIDER") or "openai").strip().lower()
    return provider if provider in {"gemini", "openai"} else "openai"

def configured_model():
    """Return a provider-appropriate model name."""
    configured = (os.getenv("POSP_AI_MODEL") or "").strip()
    if configured:
        return configured
    return "gemini-2.5-flash" if configured_provider() == "gemini" else "gpt-6-luna"

def is_configured():
    """Whether selected provider has a key configured; never return the key."""
    key_name = "GEMINI_API_KEY" if configured_provider() == "gemini" else "OPENAI_API_KEY"
    return bool((os.getenv(key_name) or "").strip())

def _extract_openai_text(payload):
    for item in payload.get("output", []):
        for content in item.get("content", []) or []:
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                return content["text"]
    return ""

def _call_openai(api_key, model, instructions, prompt, max_output_tokens):
    response = requests.post(
        "https://api.openai.com/v1/responses",
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
        json={"model": model, "instructions": instructions, "input": prompt, "max_output_tokens": max_output_tokens},
        timeout=25,
    )
    if response.status_code >= 400:
        return None, "AI provider request failed. Check the provider key, model, and account limits."
    answer = _extract_openai_text(response.json())
    return (answer, None) if answer else (None, "AI returned no text response.")

def _call_gemini(api_key, model, instructions, prompt, max_output_tokens):
    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent",
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        json={
            "system_instruction": {"parts": [{"text": instructions}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_output_tokens},
        },
        timeout=25,
    )
    if response.status_code >= 400:
        return None, "Gemini request failed. Check GEMINI_API_KEY, POSP_AI_MODEL, and Gemini API quota."
    payload = response.json()
    candidates = payload.get("candidates") or []
    parts = ((candidates[0].get("content") or {}).get("parts") or []) if candidates else []
    answer = "\n".join(part.get("text", "") for part in parts if part.get("text")).strip()
    return (answer, None) if answer else (None, "Gemini returned no text response.")

def call_model(instructions, prompt, max_output_tokens=900):
    """Call selected provider and return (text, safe_error)."""
    provider = configured_provider()
    key_name = "GEMINI_API_KEY" if provider == "gemini" else "OPENAI_API_KEY"
    api_key = (os.getenv(key_name) or "").strip()
    if not api_key:
        return None, "AI is not configured: add " + key_name + " to the backend environment."
    try:
        if provider == "gemini":
            return _call_gemini(api_key, configured_model(), instructions, prompt, max_output_tokens)
        return _call_openai(api_key, configured_model(), instructions, prompt, max_output_tokens)
    except (requests.RequestException, ValueError, TypeError, KeyError, IndexError):
        return None, "AI provider could not be reached or returned an invalid response."
