from datetime import date

from app.jobs.priority_sources import parse_sbi
from app.jobs.sources import SOURCE_BY_KEY


def test_sbi_source_uses_current_official_openings_page():
    assert SOURCE_BY_KEY['sbi'].listing_url == 'https://sbi.bank.in/web/careers/current-openings1'


def test_sbi_parser_publishes_ad29_engineer_fire_from_current_official_page():
    source = SOURCE_BY_KEY['sbi']
    html = '''
      <p>RECRUITMENT OF SPECIALIST CADRE OFFICERS ON REGULAR BASIS FOR THE POST OF ASSISTANT MANAGER – ENGINEER (FIRE) (Apply Online from 04.11.2026 TO 25.11.2026)</p>
      <p>ADVERTISEMENT NO: CRPD/SCO/2026-27/29</p>
      <ul>
        <li><a href="https://sbi.bank.in/documents/77530/57941334/04112026_FINAL_DRAFT_ADVERTISEMENT_CRPD-SCO_29_ENGINEER.pdf/document-id?t=1">DOWNLOAD ADVERTISEMENT English (1 MB)</a></li>
        <li><a href="https://ibpsreg.ibps.in/sbiameoct26/">APPLY ONLINE (04.11.2026 to 25.11.2026)</a></li>
      </ul>
    '''

    items = parse_sbi(html, source.listing_url)

    assert len(items) == 1
    item = items[0]
    assert 'ASSISTANT MANAGER' in item.title
    assert item.deadline == date(2026, 11, 25)
    assert item.official_notice_url.startswith('https://sbi.bank.in/documents/')
    assert item.application_url == 'https://ibpsreg.ibps.in/sbiameoct26/'
