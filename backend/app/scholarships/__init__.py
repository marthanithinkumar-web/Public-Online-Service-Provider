"""Scholarship feed helpers."""

# These dedicated scholarship portals are first-party Government of India/NIC
# services and remain subject to the discovery module's strict HTTPS host check.
from . import discovery as _discovery

_discovery.OFFICIAL_HOSTS.update({
    'nosmsje.gov.in',
    'www.nosmsje.gov.in',
    'overseas.tribal.gov.in',
})

_STABLE_SOURCE_URLS = {
    'social_justice': 'https://nosmsje.gov.in/public/',
    'tribal_affairs': 'https://overseas.tribal.gov.in/AboutUs.aspx',
}

_discovery.SOURCE_DEFINITIONS = tuple(
    {**source, 'url': _STABLE_SOURCE_URLS.get(source['key'], source['url'])}
    for source in _discovery.SOURCE_DEFINITIONS
)
