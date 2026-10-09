from __future__ import annotations

from urllib.parse import urlparse

from ..jobs.official_fetch import ALLOWED_HOSTS


class OfficialSourcePolicyError(ValueError):
    """Raised when autonomous publication is not backed by an approved official host."""


def require_official_https(url: str) -> str:
    parsed = urlparse(str(url or ''))
    if parsed.scheme != 'https' or parsed.hostname not in ALLOWED_HOSTS or parsed.username or parsed.password:
        raise OfficialSourcePolicyError('Autonomous POSP publication requires an approved official HTTPS source.')
    return url


def validate_publication_sources(*urls: str | None) -> None:
    """Validate every authoritative/target URL before autonomous publication."""
    for url in urls:
        if url:
            require_official_https(url)


def is_autonomous_publication_allowed(*urls: str | None) -> bool:
    try:
        validate_publication_sources(*urls)
        return True
    except OfficialSourcePolicyError:
        return False
