"""Scholarship feed helpers."""

# Prefer stable, server-rendered pages on the same allow-listed government hosts.
# The discovery module still enforces the official HTTPS host allow-list.
from . import discovery as _discovery

_STABLE_SOURCE_URLS = {
    'social_justice': 'https://socialjustice.gov.in/whats-new/1493',
    'tribal_affairs': 'https://tribal.nic.in/',
}

_discovery.SOURCE_DEFINITIONS = tuple(
    {**source, 'url': _STABLE_SOURCE_URLS.get(source['key'], source['url'])}
    for source in _discovery.SOURCE_DEFINITIONS
)
