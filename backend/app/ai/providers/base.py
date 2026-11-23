"""Shared provider transport with connection reuse and bounded safe retries."""

import os
import time
from threading import local

import requests

from .errors import ProviderError


_HTTP_LOCAL = local()


def _http_session():
    session = getattr(_HTTP_LOCAL, "session", None)
    if session is None:
        session = requests.Session()
        _HTTP_LOCAL.session = session
    return session


class ProviderAdapter:
    name = "provider"
    key_env = ""
    endpoint = ""
    timeout = (3.05, 15)
    max_attempts = 2

    @property
    def display_name(self):
        return "OpenAI" if self.name == "openai" else self.name.title()

    def api_key(self):
        return (os.getenv(self.key_env) or "").strip()

    def is_configured(self):
        return bool(self.api_key())

    def post_json(self, *, headers, payload, endpoint=None):
        for attempt in range(self.max_attempts):
            try:
                response = _http_session().post(
                    endpoint or self.endpoint, headers=headers, json=payload,
                    timeout=self.timeout, allow_redirects=False,
                )
            except requests.ConnectTimeout:
                if attempt + 1 < self.max_attempts:
                    time.sleep(0.1)
                    continue
                raise ProviderError("timeout", f"{self.display_name} AI timed out.") from None
            except requests.Timeout:
                # A read timeout can mean the model already generated a billable answer.
                raise ProviderError("timeout", f"{self.display_name} AI timed out.") from None
            except requests.RequestException:
                raise ProviderError("unavailable", f"{self.display_name} AI could not be reached.") from None

            if response.status_code == 429 or 500 <= response.status_code < 600:
                if attempt + 1 < self.max_attempts:
                    try:
                        delay = min(1.0, max(0.0, float(response.headers.get("Retry-After", "0"))))
                    except (TypeError, ValueError):
                        delay = 0
                    time.sleep(delay if delay else 0.1)
                    continue
            if response.status_code == 429:
                raise ProviderError("rate_limited", f"{self.display_name} AI is temporarily rate limited.")
            if response.status_code in {401, 403}:
                raise ProviderError("authentication", f"{self.display_name} AI rejected its configured credentials.")
            if response.status_code >= 500:
                raise ProviderError("provider_error", f"{self.display_name} AI is temporarily unavailable.")
            if response.status_code >= 300:
                raise ProviderError("request_rejected", f"{self.display_name} AI rejected the request.")
            try:
                return response.json()
            except (ValueError, TypeError):
                raise ProviderError("invalid_response", f"{self.display_name} returned an invalid response.") from None
        raise ProviderError("unavailable", f"{self.display_name} AI could not be reached.")
