"""Constrained HTTP access for approved official recruitment sources."""

import time
from urllib.parse import urlparse

import requests


ALLOWED_HOSTS = {
    'employmentnews.gov.in', 'www.employmentnews.gov.in',
    'ssc.gov.in', 'www.ssc.gov.in',
    'rrbcdg.gov.in', 'www.rrbcdg.gov.in', 'rrbapply.gov.in', 'www.rrbapply.gov.in',
    'upsc.gov.in', 'www.upsc.gov.in', 'upsconline.nic.in', 'www.upsconline.nic.in',
    'mha.gov.in', 'www.mha.gov.in',
    'tgprb.in', 'www.tgprb.in', 'doc.tgprb.in',
    'indiapost.gov.in', 'www.indiapost.gov.in',
    'indiapostgdsonline.gov.in', 'www.indiapostgdsonline.gov.in',
    'isro.gov.in', 'www.isro.gov.in',
    'ncs.gov.in', 'www.ncs.gov.in',
}
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
MAX_ATTEMPTS = 3
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
RETRY_DELAYS_SECONDS = (0.0, 0.6, 1.5)


class OfficialSourceUnavailable(RuntimeError):
    """A temporary upstream failure that should not invalidate cached notices."""


def validate_official_url(url):
    parsed = urlparse(str(url or ''))
    if parsed.scheme != 'https' or parsed.hostname not in ALLOWED_HOSTS or parsed.username or parsed.password:
        raise ValueError('Job source URL is not on the approved official HTTPS allowlist.')
    return url


def _read_safe_response(response):
    validate_official_url(response.url)
    content_type = (response.headers.get('Content-Type') or '').lower()
    if content_type and not any(kind in content_type for kind in ('text/html', 'application/xhtml+xml', 'application/json', 'text/json', 'text/plain')):
        raise ValueError('Official source returned an unsupported content type.')
    chunks = []
    size = 0
    for chunk in response.iter_content(chunk_size=65536):
        if not chunk:
            continue
        size += len(chunk)
        if size > MAX_RESPONSE_BYTES:
            raise ValueError('Official source response exceeded the safe size limit.')
        chunks.append(chunk)
    encoding = response.encoding or 'utf-8'
    return b''.join(chunks).decode(encoding, errors='replace')


def fetch_official_page(url, session=None):
    """Fetch an allowlisted official page with bounded transient retries.

    Safety/validation errors are never retried. Timeouts, connection failures and
    explicitly retryable HTTP status codes receive a few short attempts. This
    keeps one temporary government-site outage from breaking the verified feed.
    """
    validate_official_url(url)
    client = session or requests.Session()
    last_reason = 'temporary network error'
    for attempt in range(MAX_ATTEMPTS):
        if attempt:
            time.sleep(RETRY_DELAYS_SECONDS[attempt])
        try:
            response = client.get(
                url,
                timeout=(8, 25),
                allow_redirects=True,
                stream=True,
                headers={'User-Agent': 'PublicOnlineServiceProvider/1.0 (+independent job-notice index)'},
            )
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_reason = 'timeout' if isinstance(exc, requests.Timeout) else 'connection failure'
            if attempt + 1 < MAX_ATTEMPTS:
                continue
            raise OfficialSourceUnavailable(
                f'Official source is temporarily unavailable after {MAX_ATTEMPTS} attempts ({last_reason}).'
            ) from None

        # Validate every redirect destination before processing its body. A
        # redirect outside the approved host set is a safety error, not a
        # transient failure, and must fail immediately.
        validate_official_url(response.url)
        status_code = getattr(response, 'status_code', 200)
        if status_code in RETRYABLE_STATUS_CODES:
            last_reason = f'HTTP {status_code}'
            if attempt + 1 < MAX_ATTEMPTS:
                try:
                    response.close()
                except Exception:
                    pass
                continue
            raise OfficialSourceUnavailable(
                f'Official source is temporarily unavailable after {MAX_ATTEMPTS} attempts ({last_reason}).'
            ) from None
        response.raise_for_status()
        return _read_safe_response(response)

    raise OfficialSourceUnavailable(f'Official source is temporarily unavailable ({last_reason}).')
