from typing import Protocol


class AIProvider(Protocol):
    name: str
    display_name: str

    def is_configured(self) -> bool: ...

    def generate(self, *, instructions: str, prompt: str, model: str, max_output_tokens: int) -> str: ...
