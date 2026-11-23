class ProviderError(Exception):
    """Normalized provider error that contains no prompts or credentials."""

    def __init__(self, code: str, safe_message: str):
        super().__init__(safe_message)
        self.code = code
        self.safe_message = safe_message
