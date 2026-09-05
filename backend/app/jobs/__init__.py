"""Verified public job-notification ingestion."""

# Use the Ministry of Railways' central Railway Recruitment Control Board
# employment-notice page as the single RRB authority for the public feed.
from . import sources as _sources
from .private_sources import PRIVATE_SOURCES
from .rrb_central import RRCB_SOURCE

_sources.SOURCE_DEFINITIONS = tuple(
    RRCB_SOURCE if source.key == 'rrb' else source
    for source in _sources.SOURCE_DEFINITIONS
) + PRIVATE_SOURCES
_sources.SOURCE_BY_KEY.clear()
_sources.SOURCE_BY_KEY.update({source.key: source for source in _sources.SOURCE_DEFINITIONS})
