"""Shared AI provider layer for POSP customer and administrator workflows.

This module centralizes model configuration and provider calls. Permission checks,
context construction, and tool access remain in their owning routes.
"""
import os

import requests


def configured_model():
    """Return the configured OpenAI model, defaulting to the migration target."""
    return (os.getenv("POSP_AI_MODEL") or "gpt-6.1-sol").strip()


def configured_reasoning_effort():
    """Return a supported reasoning-effort setting for Responses API calls."""
    effort = (os.getenv("POSP_AI_REASONING_EFFORT") or "medium").strip().lower()
    return effort if effort in {"low", "medium", "high", "xhigh", "max"} else "medium"


def is_configured():
    """Whether a provider key is configured; never returns the key itself."""
    return bool((os.getenv("OPENAI_API_KEY") or "").strip())


def _extract_response_text(payload):
    for item in payload.get("output", []):
        for content in item.get("content", []) or []:
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                return content["text"]
    return ""


def call_model(instructions, prompt, max_output_tokens=900):
    """Call the configured Responses API model and return (text, safe_error)."""
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        return None, "AI is not configured on the backend."
    try:
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
                "reasoning": {"effort": configured_reasoning_effort()},
                "max_output_tokens": max_output_tokens,
            },
            timeout=45,
        )
        if response.status_code >= 400:
            return None, "AI provider request failed."
        answer = _extract_response_text(response.json())
        return (answer, None) if answer else (None, "AI returned no text response.")
    except (requests.RequestException, ValueError, TypeError):
        return None, "AI provider could not be reached."
