from datetime import date

from app.jobs.priority_sources import parse_sbi
from app.jobs.sources import SOURCE_BY_KEY


def test_sbi_source_uses_current_official_openings_page():
    assert SOURCE_BY_KEY['sbi'].listing_url == 'https://sbi.bank.in/web/careers/current-openings1'


def test_sbi_parser_publishes_all_current_openings_and_excludes_expired_extension(monkeypatch):
    monkeypatch.setattr('app.jobs.priority_sources.india_today', lambda: date(2026, 11, 17))
    source = SOURCE_BY_KEY['sbi']

    def section(title, advertisement, notice_url, application_url, application_label):
        return f'''
          <p>{title}</p>
          <p>ADVERTISEMENT NO: {advertisement}</p>
          <ul>
            <li><a href="{notice_url}">DOWNLOAD ADVERTISEMENT English (1 MB)</a></li>
            <li><a href="{application_url}">{application_label}</a></li>
          </ul>
        '''

    html = ''.join([
        section(
            'RECRUITMENT OF SPECIALIST CADRE OFFICERS ON REGULAR BASIS FOR THE POST OF ASSISTANT MANAGER – ENGINEER (FIRE) (Apply Online from 04.11.2026 TO 25.11.2026)',
            'CRPD/SCO/2026-27/29',
            'https://sbi.bank.in/documents/77530/57941334/04112026_FINAL+DRAFT+ADVERTISEMENT+CRPD-SCO_29_ENGINEER.pdf/4d1be5a0-727d-61b5-1ea4-85570f437345?t=1793788834905',
            'https://ibpsreg.ibps.in/sbiameoct26/',
            'APPLY ONLINE (04.11.2026 to 25.11.2026)',
        ),
        section(
            'RECRUITMENT OF SPECIALIST CADRE OFFICERS ON REGULAR BASIS FOR THE POST OF MANAGER (SECURITY)/DEPUTY MANAGER (SECURITY) (Apply Online from 04.11.2026 TO 25.11.2026)',
            'CRPD/SCO/2026-27/28',
            'https://sbi.bank.in/documents/77530/57941334/03112026_1_ADV_Security%2BOfficer.pdf/69e017fe-5e1c-6312-c285-8855f9882102?t=1793713497818',
            'https://ibpsreg.ibps.in/sbirscooct26/',
            'APPLY ONLINE (04.11.2026 to 25.11.2026)',
        ),
        section(
            'RECRUITMENT OF SPECIALIST CADRE OFFICER ON REGULAR BASIS FOR THE POSTS OF CHIEF MANAGER (PRODUCT &amp; RESEARCH - FOREX &amp; RUPEE DERIVATIVES) &amp; MANAGER (PRODUCT &amp; RESEARCH ANALYST) (Apply Online from 02.11.2026 TO 23.11.2026)',
            'CRPD/SCO/2026-27/26',
            'https://sbi.bank.in/documents/77530/57941334/FINAL+ADVT+CRPD+_SCO_2026-27_26_GMU.pdf/ade1acc4-609b-5c9a-ed89-670e70d0a82c?t=1793600742622',
            'https://recruitment.sbi.bank.in/crpd-sco-2026-27-26/apply',
            'APPLY ONLINE (02.11.2026 TO 23.11.2026)',
        ),
        section(
            'RECRUITMENT OF SPECIALIST CADRE OFFICER ON REGULAR BASIS (POST : RISK SPECIALIST) (Apply Online from 02.11.2026 TO 23.11.2026)',
            'CRPD/SCO/2026-27/27',
            'https://sbi.bank.in/documents/77530/57941334/DETAILED+ADV_RMD_SCO_2026-27_27.pdf/fff268f5-f55d-3ec8-b1ca-b7a51e705e0e?t=1793599952659',
            'https://recruitment.sbi.bank.in/crpd-sco-2026-27-27/apply',
            'APPLY ONLINE (02.11.2026 TO 23.11.2026)',
        ),
        section(
            'ENGAGEMENT OF SPECIALIST CADRE OFFICERS ON FIXED TERM EMPLOYMENT BASIS (Online Registration Extended till 16.11.2026)',
            'CRPD/SCO/2026-27/30',
            'https://sbi.bank.in/documents/77530/57941334/SBI%2B-%2BCRPD-SCO-2026-27_30%2B-%2BHindi.pdf/d8e4a24c-d80a-23dd-8676-d71c267b979f?t=1793615990478',
            'https://recruitment.sbi.bank.in/crpd-sco-2026-27-30/apply',
            'APPLY ONLINE (Online Registration Extended till 16.11.2026)',
        ),
    ])

    items = parse_sbi(html, source.listing_url)

    assert len(items) == 4
    by_title = {item.title: item for item in items}
    fire = next(item for title, item in by_title.items() if 'ASSISTANT MANAGER' in title)
    security = next(item for title, item in by_title.items() if 'MANAGER (SECURITY)' in title)
    product_research = next(item for title, item in by_title.items() if 'CHIEF MANAGER (PRODUCT' in title)
    risk = next(item for title, item in by_title.items() if 'RISK SPECIALIST' in title)

    assert fire.deadline == security.deadline == date(2026, 11, 25)
    assert product_research.deadline == risk.deadline == date(2026, 11, 23)
    assert fire.application_url == 'https://ibpsreg.ibps.in/sbiameoct26/'
    assert security.application_url == 'https://ibpsreg.ibps.in/sbirscooct26/'
    assert product_research.application_url == 'https://recruitment.sbi.bank.in/crpd-sco-2026-27-26/apply'
    assert risk.application_url == 'https://recruitment.sbi.bank.in/crpd-sco-2026-27-27/apply'
    assert all(item.official_notice_url.startswith('https://sbi.bank.in/documents/') for item in items)
    assert not any('FIXED TERM EMPLOYMENT' in item.title for item in items)
