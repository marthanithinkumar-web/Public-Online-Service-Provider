"""Verified public job-notification ingestion."""

# Regional RRBs are registered here rather than duplicated in the core parser
# module. Importing app.jobs always runs this package initializer before
# app.jobs.sources is consumed by the snapshot and database sync paths.
from . import sources as _sources
from .rrb_extra import EXTRA_RRB_SOURCES

_existing_keys = {source.key for source in _sources.SOURCE_DEFINITIONS}
_new_sources = tuple(source for source in EXTRA_RRB_SOURCES if source.key not in _existing_keys)
if _new_sources:
    _sources.SOURCE_DEFINITIONS = _sources.SOURCE_DEFINITIONS + _new_sources
    _sources.SOURCE_BY_KEY.update({source.key: source for source in _new_sources})
