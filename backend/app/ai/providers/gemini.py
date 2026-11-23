from .base import ProviderAdapter
from ..text import extract_gemini_text


class GeminiProvider(ProviderAdapter):
    name = "gemini"
    key_env = "GEMINI_API_KEY"
    endpoint_template = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def generate(self, *, instructions, prompt, model, max_output_tokens):
        payload = self.post_json(
            headers={"x-goog-api-key": self.api_key(), "Content-Type": "application/json"},
            endpoint=self.endpoint_template.format(model=model),
            payload={
                "systemInstruction": {"parts": [{"text": instructions}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": max_output_tokens, "temperature": 0.2},
            },
        )
        return extract_gemini_text(payload)
