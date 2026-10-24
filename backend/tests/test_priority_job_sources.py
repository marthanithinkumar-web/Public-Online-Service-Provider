from app.jobs import sources
from app.jobs.priority_sources import parse_rbi
from datetime import date, datetime, timezone

from app.jobs import snapshot
from app.jobs.sources import JobItem, SOURCE_DEFINITIONS, parse_all_dates, parse_date, parse_explicit_deadline


def test_employment_news_all_jobs_is_removed_and_priority_sources_are_registered():
    keys = [source.key for source in sources.SOURCE_DEFINITIONS]

    assert 'employment_news' not in keys
    for key in ('ssc', 'rrb', 'upsc', 'rbi', 'sbi', 'nvs', 'sainik_schools', 'kvs', 'sebi', 'ibps', 'drdo_rac'):
        assert key in keys

    assert keys.index('rbi') < keys.index('ssc')
    assert keys.index('sbi') < keys.index('ssc')
    assert all('employmentnews.gov.in/NewEmp/AllJobs.aspx' not in source.listing_url for source in sources.SOURCE_DEFINITIONS)


def test_priority_parser_keeps_recruitment_notice_and_excludes_results():
    html = '''
    <ul>
      <li><a href="/Scripts/bs_viewcontent.aspx?Id=5001">Direct Recruitment for Officers Grade B 2026 - Last date 30 October 2026</a></li>
      <li><a href="/Scripts/bs_viewcontent.aspx?Id=5002">Final Result - Recruitment for Officers Grade B 2026</a></li>
      <li><a href="/Scripts/CallLetters.aspx">Call Letter for Recruitment Examination</a></li>
    </ul>
    '''

    items = parse_rbi(html, 'https://opportunities.rbi.org.in/Scripts/Vacancies.aspx')

    assert len(items) == 1
    assert items[0].organization == 'Reserve Bank of India (RBI)'
    assert items[0].deadline.isoformat() == '2026-10-30'
    assert items[0].official_notice_url == 'https://opportunities.rbi.org.in/Scripts/bs_viewcontent.aspx?Id=5001'


def test_dotted_numeric_dates_are_parsed_from_official_deadline_text():
    assert parse_date('09.11.2026').isoformat() == '2026-11-09'
    dates = parse_all_dates('Apply online from 19.10.2026 to 09.11.2026')
    assert [value.isoformat() for value in dates] == ['2026-10-19', '2026-11-09']



def test_deadline_requires_an_explicit_application_closing_label():
    assert parse_explicit_deadline('Recruitment notice issued on 12 October 2026; exam on 20 November 2026') is None
    assert parse_explicit_deadline('Last date 30 October 2026') == date(2026, 10, 30)
    assert parse_explicit_deadline('Online applications from 19.10.2026 to 09.11.2026') == date(2026, 11, 9)


def test_snapshot_enriches_official_notice_before_deadline_validation(monkeypatch):
    source = next(item for item in SOURCE_DEFINITIONS if item.key == 'sbi')
    item = JobItem(
        external_id='sbi-official-test',
        title='Recruitment for Specialist Officer',
        organization='State Bank of India',
        official_notice_url=source.listing_url,
        deadline=None,
        confidence=0.95,
    )
    from dataclasses import replace
    source = replace(source, parser=lambda html, url: [item])
    monkeypatch.setattr(snapshot, 'SOURCE_DEFINITIONS', (source,))
    monkeypatch.setattr(snapshot, 'fetch_official_page', lambda url, session=None: '<html>listing</html>')

    def enrich(candidate, session=None):
        candidate.deadline = date(2026, 11, 9)
        return candidate

    monkeypatch.setattr(snapshot, 'enrich_job_item', enrich)
    result = snapshot.build_snapshot(now=datetime(2026, 10, 24, tzinfo=timezone.utc))

    assert result['count'] == 1
    assert result['items'][0]['deadline'] == '2026-11-09'
    assert result['items'][0]['official_notice_url'] == source.listing_url


def test_snapshot_does_not_publish_result_only_notice(monkeypatch):
    source = next(item for item in SOURCE_DEFINITIONS if item.key == 'sbi')
    item = JobItem(
        external_id='sbi-result-test',
        title='Recruitment for Specialist Officer',
        organization='State Bank of India',
        official_notice_url=source.listing_url,
        deadline=None,
        confidence=0.95,
    )
    from dataclasses import replace
    source = replace(source, parser=lambda html, url: [item])
    monkeypatch.setattr(snapshot, 'SOURCE_DEFINITIONS', (source,))
    monkeypatch.setattr(snapshot, 'fetch_official_page', lambda url, session=None: '<html>listing</html>')

    def enrich(candidate, session=None):
        candidate.deadline = date(2026, 11, 9)
        candidate.warnings.append('notice_excluded_result_only')
        return candidate

    monkeypatch.setattr(snapshot, 'enrich_job_item', enrich)
    result = snapshot.build_snapshot(now=datetime(2026, 10, 24, tzinfo=timezone.utc))

    assert result['count'] == 0
