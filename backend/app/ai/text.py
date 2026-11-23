"""Safe, provider-neutral response extraction helpers."""


def extract_openai_text(payload):
    if not isinstance(payload, dict):
        return ""
    for item in payload.get("output", []) or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []) or []:
            if isinstance(content, dict) and content.get("type") in {"output_text", "text"} and content.get("text"):
                return content["text"]
    return ""


def extract_gemini_text(payload):
    if not isinstance(payload, dict):
        return ""
    for candidate in payload.get("candidates", []) or []:
        if not isinstance(candidate, dict) or candidate.get("finishReason") not in (None, "STOP"):
            continue
        content = candidate.get("content") or {}
        if not isinstance(content, dict):
            continue
        for part in content.get("parts", []) or []:
            if isinstance(part, dict) and not part.get("thought") and part.get("text"):
                return part["text"]
    return ""
