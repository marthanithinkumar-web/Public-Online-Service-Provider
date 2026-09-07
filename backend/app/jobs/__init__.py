"""Verified public job-notification ingestion."""

# Use the Ministry of Railways' central Railway Recruitment Control Board
# employment-notice page as the single RRB authority for the public feed.
from . import sources as _sources
from .private_sources import PRIVATE_SOURCES
from .priority_sources import PRIORITY_OFFICIAL_SOURCES
from .rrb_central import RRCB_SOURCE

# Employment News' generic "All Jobs" page is intentionally excluded. The
# public feed should prefer first-party recruiting organisations (SSC, RRB,
# UPSC, RBI, SBI, NVS, Sainik Schools, KVS, SEBI, IBPS, DRDO/RAC, etc.).
_base_sources = tuple(
    RRCB_SOURCE if source.key == 'rrb' else source
    for source in _sources.SOURCE_DEFINITIONS
    if source.key != 'employment_news'
)

_existing_keys = {source.key for source in _base_sources}
_priority_sources = tuple(source for source in PRIORITY_OFFICIAL_SOURCES if source.key not in _existing_keys)

_sources.SOURCE_DEFINITIONS = _priority_sources + _base_sources + PRIVATE_SOURCES
_sources.SOURCE_BY_KEY.clear()
_sources.SOURCE_BY_KEY.update({source.key: source for source in _sources.SOURCE_DEFINITIONS})
