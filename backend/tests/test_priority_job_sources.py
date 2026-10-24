from app.jobs import sources
from app.jobs.priority_sources import parse_drdo, parse_kvs, parse_rbi, parse_sbi
from app.jobs import snapshot, notice_enrichment
from app.jobs.sources import JobItem, SOURCE_DEFINITIONS, parse_all_dates, parse_date, parse_explicit_deadline
from datetime import date, datetime, timezone


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



def test_dotted_dates_and_explicit_deadline_labels():
    assert parse_date('09.11.2026').isoformat() == '2026-11-09'
    assert [value.isoformat() for value in parse_all_dates('19.10.2026 to 09.11.2026')] == ['2026-10-19', '2026-11-09']
    assert parse_explicit_deadline('Notice issued 12 October 2026; exam on 20 November 2026') is None
    assert parse_explicit_deadline('Last date 30 October 2026') == date(2026, 10, 30)
    assert parse_explicit_deadline('Last date for submission of online applications: 09.11.2026') == date(2026, 11, 9)
    assert parse_explicit_deadline('Online applications from 19.10.2026 to 09.11.2026') == date(2026, 11, 9)


def test_html_notice_supplies_explicit_dotted_deadline(monkeypatch):
    source = next(item for item in SOURCE_DEFINITIONS if item.key == 'sbi')
    item = JobItem(
        external_id='html-notice-date', title='Recruitment for Specialist Officer',
        organization='State Bank of India', official_notice_url=source.listing_url, confidence=0.95,
    )
    monkeypatch.setattr(notice_enrichment, 'fetch_official_page', lambda url, session=None:
        '<html><title>Specialist Officer Recruitment</title><body><p>Last date to apply: 09.11.2026</p></body></html>')
    enriched = notice_enrichment.enrich_job_item(item)
    assert enriched.deadline == date(2026, 11, 9)


def test_html_result_page_is_marked_not_for_publication(monkeypatch):
    source = next(item for item in SOURCE_DEFINITIONS if item.key == 'sbi')
    item = JobItem(
        external_id='html-result-notice', title='Recruitment for Specialist Officer',
        organization='State Bank of India', official_notice_url=source.listing_url, confidence=0.95,
    )
    monkeypatch.setattr(notice_enrichment, 'fetch_official_page', lambda url, session=None:
        '<html><title>Final Result for Specialist Officer Recruitment</title><body>Selected candidates list</body></html>')
    enriched = notice_enrichment.enrich_job_item(item)
    assert 'notice_excluded_result_only' in enriched.warnings


def test_snapshot_enriches_notice_before_deadline_validation(monkeypatch):
    from dataclasses import replace
    source = next(item for item in SOURCE_DEFINITIONS if item.key == 'sbi')
    item = JobItem(
        external_id='sbi-official-test', title='Recruitment for Specialist Officer',
        organization='State Bank of India', official_notice_url='https://sbi.bank.in/web/careers/current-openings/notice-2026.pdf', confidence=0.95,
    )
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


def test_snapshot_skips_result_only_notices(monkeypatch):
    from dataclasses import replace
    source = next(item for item in SOURCE_DEFINITIONS if item.key == 'sbi')
    item = JobItem(
        external_id='sbi-result-test', title='Recruitment for Specialist Officer',
        organization='State Bank of India', official_notice_url='https://sbi.bank.in/web/careers/current-openings/notice-2026.pdf', deadline=date(2026, 11, 9), confidence=0.95,
    )
    source = replace(source, parser=lambda html, url: [item])
    monkeypatch.setattr(snapshot, 'SOURCE_DEFINITIONS', (source,))
    monkeypatch.setattr(snapshot, 'fetch_official_page', lambda url, session=None: '<html>listing</html>')
    def enrich(candidate, session=None):
        candidate.warnings.append('notice_excluded_result_only')
        return candidate
    monkeypatch.setattr(snapshot, 'enrich_job_item', enrich)
    result = snapshot.build_snapshot(now=datetime(2026, 10, 24, tzinfo=timezone.utc))
    assert result['count'] == 0



def test_application_portal_url_is_not_mislabelled_as_notice_url():
    listing = 'https://opportunities.rbi.org.in/Scripts/Vacancies.aspx'
    items = parse_rbi(
        '<ul><li><a href="/Scripts/ApplyOnline.aspx">Apply Online for Officers Grade B Recruitment</a></li></ul>',
        listing,
    )
    assert len(items) == 1
    assert items[0].official_notice_url == listing
    assert items[0].application_url == 'https://opportunities.rbi.org.in/Scripts/ApplyOnline.aspx'
    assert 'notice_is_listing_page' in items[0].warnings



def test_application_deadline_formats_seen_in_official_notices():
    assert parse_explicit_deadline(
        'Applications are invited on or before 17.00 hrs on November 13, 2026'
    ) == date(2026, 11, 13)
    assert parse_explicit_deadline(
        'Online Registration Extended till 31.10.2026'
    ) == date(2026, 10, 31)
    assert parse_explicit_deadline(
        'APPLY ONLINE (19.10.2026 TO 09.11.2026)'
    ) == date(2026, 11, 9)
    assert parse_explicit_deadline(
        'The written examination will be held on November 13, 2026'
    ) is None



def test_sbi_grouped_parser_preserves_titles_notice_urls_and_application_urls():
    html = '''
      <p>ENGAGEMENT OF SPECIALIST CADRE OFFICERS ON FIXED TERM EMPLOYMENT BASIS (Apply Online from 19.10.2026 TO 09.11.2026)</p>
      <p>ADVERTISEMENT NO: CRPD/SCO/2026-27/30</p>
      <ul>
        <li><a href="/documents/adv30.pdf/abc123">DOWNLOAD ADVERTISEMENT English</a></li>
        <li><a href="https://recruitment.sbi.bank.in/crpd-sco-2026-27-30/apply">APPLY ONLINE (19.10.2026 TO 09.11.2026)</a></li>
      </ul>
      <p>ENGAGEMENT OF SPECIALIST CADRE OFFICERS ON CONTRACT BASIS (Online Registration Extended till 31.10.2026)</p>
      <p>ADVERTISEMENT NO: CRPD/SCO/2026-27/25</p>
      <ul>
        <li><a href="/documents/adv25.pdf/abc125">DOWNLOAD ADVERTISEMENT English</a></li>
        <li><a href="https://recruitment.sbi.bank.in/crpd-sco-2026-27-25/apply">APPLY ONLINE (Online Registration Extended till 31.10.2026)</a></li>
      </ul>
      <p>ENGAGEMENT OF SPECIALIST CADRE OFFICERS ON CONTRACT BASIS (Registration Extended till 16.10.2026)</p>
      <p>ADVERTISEMENT NO: CRPD/SCO/2026-27/20</p>
      <ul>
        <li><a href="/documents/adv20.pdf/abc120">DOWNLOAD ADVERTISEMENT English</a></li>
        <li><a href="https://recruitment.sbi.bank.in/crpd-sco-2026-27-20/apply">APPLY ONLINE</a></li>
      </ul>
      <p>ENGAGEMENT OF SPECIALIST CADRE OFFICER ON CONTRACT BASIS (INTERVIEW SCHEDULE ANNOUNCED)</p>
      <p>ADVERTISEMENT NO: CRPD/SCO/2026-27/21</p>
      <ul><li><a href="/documents/adv21.pdf/abc121">DOWNLOAD ADVERTISEMENT English</a></li></ul>
    '''

    items = parse_sbi(html, 'https://sbi.bank.in/web/careers/current-openings')

    assert len(items) == 2
    fixed_term = next(item for item in items if item.deadline == date(2026, 11, 9))
    extension = next(item for item in items if item.deadline == date(2026, 10, 31))
    assert fixed_term.title.startswith('ENGAGEMENT OF SPECIALIST CADRE OFFICERS ON FIXED TERM')
    assert fixed_term.official_notice_url == 'https://sbi.bank.in/documents/adv30.pdf/abc123'
    assert fixed_term.application_url == 'https://recruitment.sbi.bank.in/crpd-sco-2026-27-30/apply'
    assert extension.title.startswith('ENGAGEMENT OF SPECIALIST CADRE OFFICERS ON CONTRACT BASIS')
    assert extension.official_notice_url == 'https://sbi.bank.in/documents/adv25.pdf/abc125'
    assert extension.application_url == 'https://recruitment.sbi.bank.in/crpd-sco-2026-27-25/apply'



def test_rbi_application_arrival_deadline_after_prior_sentence():
    text = (
        "Applications are invited from eligible candidates to fill up two posts of Part-Time "
        "Bank’s Medical Consultant on contract basis in Thiruvananthapuram. "
        "Application in a sealed cover should reach the Regional Director, Human Resource "
        "Management Department, Reserve Bank of India, Bakery Junction, PB No.6507, "
        "Thiruvananthapuram – 695 033 on or before 17.00 hrs on November 13, 2026."
    )
    assert parse_explicit_deadline(text) == date(2026, 11, 13)


def test_sbi_grouped_parser_finds_advertisement_anchor_outside_list_item():
    html = '''
      <p>ENGAGEMENT OF SPECIALIST CADRE OFFICERS ON FIXED TERM EMPLOYMENT BASIS (Apply Online from 19.10.2026 TO 09.11.2026)</p>
      <p>ADVERTISEMENT NO: CRPD/SCO/2026-27/30</p>
      <div><a href="https://sbi.bank.in/documents/adv30.pdf/document-id?t=1">DOWNLOAD ADVERTISEMENT English</a></div>
      <ul>
        <li><a href="https://recruitment.sbi.bank.in/crpd-sco-2026-27-30/apply">APPLY ONLINE (19.10.2026 TO 09.11.2026)</a></li>
      </ul>
    '''
    items = parse_sbi(html, 'https://sbi.bank.in/web/careers/current-openings')
    assert len(items) == 1
    assert items[0].official_notice_url == 'https://sbi.bank.in/documents/adv30.pdf/document-id?t=1'
    assert items[0].application_url == 'https://recruitment.sbi.bank.in/crpd-sco-2026-27-30/apply'


def test_sbi_grouped_parser_prefers_direct_ad_pdf_when_anchor_label_is_only_language_or_size():
    html = '''
      <p>ENGAGEMENT OF SPECIALIST CADRE OFFICERS ON FIXED TERM EMPLOYMENT BASIS (Apply Online from 19.10.2026 TO 09.11.2026)</p>
      <p>ADVERTISEMENT NO: CRPD/SCO/2026-27/30</p>
      <div><a href="https://sbi.bank.in/documents/77530/57941334/17102026_Detail_ADV_CRPD_SCO_2026-27_30.pdf/document-id?t=1">English (796 KB)</a></div>
      <ul>
        <li><a href="https://recruitment.sbi.bank.in/crpd-sco-2026-27-30/apply">APPLY ONLINE (19.10.2026 TO 09.11.2026)</a></li>
        <li><a href="https://sbi.bank.in/documents/77530/57941334/17102026_BIODATA_SCO-30.pdf/document-id">English (Biodata)</a></li>
        <li><a href="https://sbi.bank.in/documents/77530/57941334/17102026_CTC_Form_SCO-30.pdf/document-id">English (CTC Form)</a></li>
      </ul>
    '''
    items = parse_sbi(html, 'https://sbi.bank.in/web/careers/current-openings')
    assert len(items) == 1
    assert items[0].official_notice_url == 'https://sbi.bank.in/documents/77530/57941334/17102026_Detail_ADV_CRPD_SCO_2026-27_30.pdf/document-id?t=1'
    assert items[0].application_url == 'https://recruitment.sbi.bank.in/crpd-sco-2026-27-30/apply'


def test_kvs_parser_uses_current_official_table_and_direct_pdf():
    html = '''
      <table>
        <tr><th>Name</th><th>Published On</th><th>View / Download</th></tr>
        <tr>
          <td>Advertisement No. 05/2026 – Filling up the post of Deputy Commissioner through Direct Recruitment in Kendriya Vidyalaya Sangathan</td>
          <td>01/10/2026</td>
          <td><a href="https://cdnbbsr.s3waas.gov.in/s32d2ca7eedf739ef4c3800713ec482e1a/uploads/2026/10/2026101962.pdf">View / Download</a></td>
        </tr>
        <tr>
          <td>Final result of recruitment for a previous examination</td>
          <td>01/10/2026</td>
          <td><a href="https://cdnbbsr.s3waas.gov.in/s32d2ca7eedf739ef4c3800713ec482e1a/uploads/2026/10/result.pdf">View / Download</a></td>
        </tr>
      </table>
    '''
    items = parse_kvs(html, 'https://kvs.gov.in/en/interview-notice/')
    assert len(items) == 1
    assert items[0].organization == 'Kendriya Vidyalaya Sangathan (KVS)'
    assert items[0].official_notice_url == 'https://cdnbbsr.s3waas.gov.in/s32d2ca7eedf739ef4c3800713ec482e1a/uploads/2026/10/2026101962.pdf'
    assert items[0].issue_date == date(2026, 10, 1)


def test_drdo_vacancy_parser_keeps_individual_official_vacancy_page():
    html = '''
      <a href="/drdo/offerings/vacancies/npol-kochi-invites-application-consultant">
        NPOL, Kochi invites application from retired Government officials as Consultant on contract basis
      </a>
      <a href="/drdo/offerings/vacancies/selected-candidates-jrf">
        List of selected candidates for awarding JRF
      </a>
    '''
    items = parse_drdo(html, 'https://drdo.gov.in/drdo/offerings/vacancies')
    assert len(items) == 1
    assert items[0].organization == 'Defence Research and Development Organisation (DRDO)'
    assert items[0].official_notice_url == 'https://drdo.gov.in/drdo/offerings/vacancies/npol-kochi-invites-application-consultant'


def test_drdo_end_date_is_used_only_on_official_drdo_vacancy_detail(monkeypatch):
    item = JobItem(
        external_id='drdo-npol-consultant',
        title='NPOL, Kochi invites application from retired Government officials as Consultant',
        organization='Defence Research and Development Organisation (DRDO)',
        official_notice_url='https://drdo.gov.in/drdo/offerings/vacancies/npol-kochi-consultant',
        confidence=0.95,
        warnings=[],
    )
    monkeypatch.setattr(
        notice_enrichment,
        'fetch_official_page',
        lambda url, session=None: '<html><title>NPOL vacancy</title><p>Published Date 18/10/2026</p><p>Start Date 18/10/2026</p><p>End Date 09/11/2026</p></html>',
    )
    notice_enrichment.enrich_job_item(item)
    assert item.deadline == date(2026, 11, 9)
