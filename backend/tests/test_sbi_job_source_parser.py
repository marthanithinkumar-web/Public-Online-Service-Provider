from datetime import date

from app.jobs.official_fetch import validate_official_url
from app.jobs.priority_sources import parse_sbi


def test_sbi_parser_pairs_current_title_advertisement_and_apply_url():
    html = """
    <html><body>
      <p>ENGAGEMENT OF SPECIALIST CADRE OFFICERS ON FIXED TERM EMPLOYMENT BASIS (Apply Online from 19.10.2026 TO 09.11.2026)</p>
      <p>ADVERTISEMENT NO: CRPD/SCO/2026-27/30</p>
      <ul>
        <li><a href="https://sbi.bank.in/documents/CRPD-SCO-2026-27-30.pdf">DOWNLOAD ADVERTISEMENT English (796 KB)</a></li>
        <li><a href="https://recruitment.sbi.bank.in/crpd-sco-2026-27-30/apply">APPLY ONLINE (19.10.2026 TO 09.11.2026)</a></li>
      </ul>
    </body></html>
    """
    items = parse_sbi(html, "https://sbi.bank.in/web/careers/current-openings")
    assert len(items) == 1
    item = items[0]
    assert item.title == "ENGAGEMENT OF SPECIALIST CADRE OFFICERS ON FIXED TERM EMPLOYMENT BASIS"
    assert item.external_id == "CRPD/SCO/2026-27/30"
    assert item.deadline == date(2026, 11, 9)
    assert item.application_start_date == date(2026, 10, 19)
    assert item.official_notice_url == "https://sbi.bank.in/documents/CRPD-SCO-2026-27-30.pdf"
    assert item.application_url == "https://recruitment.sbi.bank.in/crpd-sco-2026-27-30/apply"
    validate_official_url(item.official_notice_url)
    validate_official_url(item.application_url)


def test_sbi_parser_rejects_expired_and_result_only_openings():
    html = """
    <html><body>
      <p>ENGAGEMENT OF SPECIALIST CADRE OFFICER (Apply Online from 01.08.2026 TO 15.08.2026)</p>
      <p>ADVERTISEMENT NO: CRPD/SCO/2026-27/10</p>
      <ul>
        <li><a href="https://sbi.bank.in/documents/old-advertisement.pdf">DOWNLOAD ADVERTISEMENT English</a></li>
        <li><a href="https://recruitment.sbi.bank.in/crpd-sco-2026-27-10/apply">APPLY ONLINE (01.08.2026 TO 15.08.2026)</a></li>
      </ul>
      <p>RECRUITMENT OF OFFICERS (FINAL RESULT ANNOUNCED)</p>
      <p>ADVERTISEMENT NO: CRPD/SCO/2026-27/09</p>
      <ul>
        <li><a href="https://sbi.bank.in/documents/result-advertisement.pdf">DOWNLOAD ADVERTISEMENT English</a></li>
        <li><a href="https://recruitment.sbi.bank.in/crpd-sco-2026-27-09/apply">APPLY ONLINE (01.10.2026 TO 31.10.2026)</a></li>
      </ul>
    </body></html>
    """
    assert parse_sbi(html, "https://sbi.bank.in/web/careers/current-openings") == []
