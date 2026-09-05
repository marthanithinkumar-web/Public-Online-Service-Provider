from datetime import datetime, timezone

from app.scholarships.discovery import SOURCE_DEFINITIONS, human_date, is_official_url, parse_social_justice, parse_tribal_affairs


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
