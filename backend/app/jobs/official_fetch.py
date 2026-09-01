"""Constrained HTTP access for approved official recruitment sources."""

from urllib.parse import urlparse

import requests


ALLOWED_HOSTS = {
    'employmentnews.gov.in', 'www.employmentnews.gov.in',
    'upsc.gov.in', 'www.upsc.gov.in', 'upsconline.nic.in', 'www.upsconline.nic.in',
    'ncs.gov.in', 'www.ncs.gov.in',
}
MAX_RESPONSE_BYTES = 4 * 1024 * 1024


def validate_official_url(url):
    parsed = urlparse(str(url or ''))
    if parsed.scheme != 'https' or parsed.hostname not in ALLOWED_HOSTS or parsed.username or parsed.password:
        raise ValueError('Job source URL is not on the approved official HTTPS allowlist.')
    return url


def fetch_official_page(url, session=None):
    validate_official_url(url)
    client = session or requests.Session()
    response = client.get(
        url,
        timeout=(8, 25),
        allow_redirects=True,
        stream=True,
        headers={'User-Agent': 'PublicOnlineServiceProvider/1.0 (+independent job-notice index)'},
    )
    response.raise_for_status()
    validate_official_url(response.url)
    content_type = (response.headers.get('Content-Type') or '').lower()
    if content_type and not any(kind in content_type for kind in ('text/html', 'application/xhtml+xml')):
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
