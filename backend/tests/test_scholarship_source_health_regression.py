from datetime import datetime, timezone

from app.scholarships.discovery import SOURCE_DEFINITIONS, human_date, parse_social_justice, parse_tribal_affairs


NOW = datetime(2026, 9, 5, 3, 0, tzinfo=timezone.utc)


def _source(key, name, url, parser):
    return {'key': key, 'name': name, 'url': url, 'parser': parser}


def test_first_party_source_urls_use_current_stable_pages():
    sources = {source['key']: source for source in SOURCE_DEFINITIONS}
    assert sources['social_justice']['url'] == 'https://socialjustice.gov.in/schemes'
    assert sources['tribal_affairs']['url'] == 'https://tribal.nic.in/WhatsNewsArchives.aspx'


def test_human_date_reads_ordinal_month_deadlines():
    assert human_date('New Deadline: 15th July 2026') == '2026-07-15'
    assert human_date('Deadline: 31st October 2026') == '2026-10-31'
    assert human_date('open till 30-06-2026') == '2026-06-30'


def test_tribal_nos_parser_does_not_publish_expired_selection_year():
    html = '''
    <div>Last Date Extended! Apply for National Overseas Scholarship (NOS) for ST Candidates 2026-27.</div>
    <div>New Deadline: 15th July 2026, 5:30 PM.</div>
    <div>Ministry invites online application for the National Overseas Scholarship Scheme (NOS) for ST candidates for the selection year 2026-27.</div>
    <div>The portal is open till 30-06-2026, 5:00 PM.</div>
    '''
    source = _source('tribal_affairs', 'Ministry of Tribal Affairs', 'https://tribal.nic.in/WhatsNewsArchives.aspx', 'tribal_affairs')
    assert parse_tribal_affairs(html, source, now=NOW) == []


def test_tribal_nos_parser_publishes_only_future_explicit_deadline():
    html = '''
    <div>Last Date Extended! Apply for National Overseas Scholarship (NOS) for ST Candidates 2026-27.</div>
    <div>New Deadline: 31st October 2026, 5:30 PM.</div>
    '''
    source = _source('tribal_affairs', 'Ministry of Tribal Affairs', 'https://tribal.nic.in/WhatsNewsArchives.aspx', 'tribal_affairs')
    items = parse_tribal_affairs(html, source, now=NOW)
    assert len(items) == 1
    assert items[0]['deadline'] == '2026-10-31'
    assert items[0]['academic_year'] == '2026-27'
    assert items[0]['status'] == 'active'


def test_social_justice_stable_scheme_page_is_parseable_as_official_notices():
    html = '''
    <h3>Educational Schemes</h3>
    <div>Central Sector Scholarship of Top Class Education for SC Students</div>
    <div>National Overseas Scholarship (NOS) for SC etc. Candidates</div>
    <div>Post-Matric Scholarship for SC students</div>
    '''
    source = _source('social_justice', 'Department of Social Justice & Empowerment', 'https://socialjustice.gov.in/schemes', 'social_justice')
    items = parse_social_justice(html, source, now=NOW)
    assert len(items) == 3
    assert all(item['is_official'] is True for item in items)
    assert all(item['record_type'] == 'official_notice' for item in items)
