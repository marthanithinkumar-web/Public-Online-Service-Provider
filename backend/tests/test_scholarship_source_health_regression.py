from datetime import datetime, timezone

from app.scholarships.discovery import SOURCE_DEFINITIONS, human_date, is_official_url, parse_social_justice, parse_tribal_affairs
from app.scholarships import discovery


NOW = datetime(2026, 9, 5, 3, 0, tzinfo=timezone.utc)


def _source(key, name, url, parser):
    return {'key': key, 'name': name, 'url': url, 'parser': parser}


def test_first_party_source_urls_use_dedicated_official_portals():
    sources = {source['key']: source for source in SOURCE_DEFINITIONS}
    assert sources['social_justice']['url'] == 'https://nosmsje.gov.in/public/'
    assert sources['tribal_affairs']['url'] == 'https://overseas.tribal.gov.in/AboutUs.aspx'
    assert is_official_url(sources['social_justice']['url'])
    assert is_official_url(sources['tribal_affairs']['url'])


def test_human_date_reads_ordinal_month_deadlines():
    assert human_date('New Deadline: 15th July 2026') == '2026-07-15'
    assert human_date('Deadline: 31st October 2026') == '2026-10-31'
    assert human_date('open till 30-06-2026') == '2026-06-30'


def test_tribal_nos_parser_does_not_publish_expired_selection_year():
    html = '<div>National Overseas Scholarship (NOS) for ST Candidates 2026-27. New Deadline: 15th July 2026.</div>'
    source = _source('tribal_affairs', 'Ministry of Tribal Affairs', 'https://overseas.tribal.gov.in/AboutUs.aspx', 'tribal_affairs')
    assert parse_tribal_affairs(html, source, now=NOW) == []


def test_tribal_nos_parser_publishes_only_future_explicit_deadline():
    html = '<div>National Overseas Scholarship (NOS) for ST Candidates 2026-27. New Deadline: 31st October 2026.</div>'
    source = _source('tribal_affairs', 'Ministry of Tribal Affairs', 'https://overseas.tribal.gov.in/AboutUs.aspx', 'tribal_affairs')
    items = parse_tribal_affairs(html, source, now=NOW)
    assert len(items) == 1
    assert items[0]['deadline'] == '2026-10-31'
    assert items[0]['academic_year'] == '2026-27'


def test_social_justice_nos_portal_is_parseable_as_official_notice():
    html = '<div>National Overseas Scholarship Scheme for SC etc. Candidates Selection Year 2026-27</div>'
    source = _source('social_justice', 'Department of Social Justice & Empowerment', 'https://nosmsje.gov.in/public/', 'social_justice')
    items = parse_social_justice(html, source, now=NOW)
    assert len(items) == 1
    assert items[0]['is_official'] is True
    assert items[0]['record_type'] == 'official_notice'


def test_source_outage_uses_official_fallback_and_records_actual_provenance(monkeypatch):
    primary = next(source for source in SOURCE_DEFINITIONS if source['key'] == 'social_justice')
    calls = []

    def fetch(source, session=None, attempts=3):
        calls.append(source['url'])
        if source['url'] == primary['url']:
            raise RuntimeError('primary source unavailable')
        return '<div>National Overseas Scholarship Scheme for SC Candidates 2026-27</div>'

    monkeypatch.setattr(discovery, 'fetch_source', fetch)
    items, health = discovery.discover_official_scholarships(sources=[primary], now=NOW)
    fallback = primary['fallback_urls'][0]
    assert calls == [primary['url'], fallback]
    assert items[0]['source_url'] == fallback
    assert health['social_justice']['ok'] is True
    assert health['social_justice']['source_url'] == primary['url']
    assert health['social_justice']['fetched_url'] == fallback
    assert health['social_justice']['used_fallback'] is True


def test_all_source_outages_remain_unhealthy(monkeypatch):
    def unavailable(*args, **kwargs):
        raise RuntimeError('source unavailable')

    monkeypatch.setattr(discovery, 'fetch_source', unavailable)
    primary = next(source for source in SOURCE_DEFINITIONS if source['key'] == 'tribal_affairs')
    items, health = discovery.discover_official_scholarships(sources=[primary], now=NOW)
    assert items == []
    assert health['tribal_affairs']['ok'] is False


def test_fallback_fetch_keeps_official_host_boundary():
    import pytest

    with pytest.raises(ValueError, match='not allow-listed'):
        discovery.fetch_source({'key': 'untrusted', 'url': 'https://example.com/scholarships'}, attempts=1)

