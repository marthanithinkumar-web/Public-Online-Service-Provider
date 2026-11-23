from .base import ProviderAdapter
from ..text import extract_openai_text


class OpenAIProvider(ProviderAdapter):
    name = "openai"
    key_env = "OPENAI_API_KEY"
    endpoint = "https://api.openai.com/v1/responses"

    def generate(self, *, instructions, prompt, model, max_output_tokens):
        payload = self.post_json(
            headers={"Authorization": f"Bearer {self.api_key()}", "Content-Type": "application/json"},
            payload={"model": model, "instructions": instructions, "input": prompt,
                     "max_output_tokens": max_output_tokens},
        )
        return extract_openai_text(payload)
