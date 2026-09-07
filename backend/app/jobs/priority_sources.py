import re
from datetime import date
from urllib.parse import urljoin

from .sources import JobItem, SourceDefinition, clean, parse_all_dates, parse_html

_EXCLUDED = (
    'result', 'results', 'admit card', 'call letter', 'answer key', 'interview schedule',
    'shortlisted', 'selected candidates', 'selection list', 'marks', 'score card',
    'corrigendum', 'addendum', 'cancellation', 'cancelled', 'document verification',
    'exam city', 'response sheet', 'notice regarding exam', 'final result',
)

_RECRUITMENT = re.compile(
    r'\b(recruitment|vacanc(?:y|ies)|current openings?|career opportunities?|'
    r'engagement of|applications? invited|apply online|advertisement|advt\.?|'
    r'probationary officer|junior associate|specialist cadre|officer grade|'
    r'assistant manager|manager grade|teaching posts?|non[- ]teaching posts?|'
    r'faculty posts?|staff recruitment)\b',
    re.I,
)


def _generic_official_parser(organization, summary):
    def parse(html, base_url):
        document = parse_html(html)
        items = []
        seen = set()
        today = date.today()

        candidates = []
        for block in document.blocks:
            text = clean(block.get('text'))
            for href in block.get('hrefs', []):
                candidates.append((href, text))
        candidates.extend(document.links)

        for index, (href, text) in enumerate(candidates, start=1):
            text = clean(text)
            lowered = text.lower()
            if not href or len(text) < 8 or not _RECRUITMENT.search(text):
                continue
            if any(term in lowered for term in _EXCLUDED):
                continue
            notice_url = urljoin(base_url, href)
            if not notice_url.startswith('https://'):
                continue
            identity = (text.lower(), notice_url)
            if identity in seen:
                continue
            seen.add(identity)
            dates = parse_all_dates(text)
            deadline = dates[-1] if dates else None
            if deadline and deadline < today:
                continue
            items.append(JobItem(
                external_id=f'{organization.lower().replace(" ", "-")}-{index}-{text[:80]}',
                title=text[:500],
                organization=organization,
                official_notice_url=notice_url,
                location='India',
                deadline=deadline,
                application_url=notice_url,
                summary=summary,
                confidence=0.92 if deadline else 0.84,
                warnings=[] if deadline else ['Confirm the closing date and post-specific eligibility in the official recruitment notice.'],
            ))
        return items

    return parse


parse_rbi = _generic_official_parser(
    'Reserve Bank of India (RBI)',
    'Official RBI recruitment opportunity. Confirm eligibility, vacancies, fee, dates and application instructions on the RBI opportunities portal.',
)
parse_sbi = _generic_official_parser(
    'State Bank of India (SBI)',
    'Official SBI recruitment opening. Confirm cadre, eligibility, vacancies, fee, dates and application instructions on SBI Careers.',
)
parse_nvs = _generic_official_parser(
    'Navodaya Vidyalaya Samiti (NVS)',
    'Official NVS recruitment notice. Confirm teaching/non-teaching post details, eligibility, vacancies, fee and dates in the official notice.',
)
parse_sainik = _generic_official_parser(
    'Sainik Schools Society',
    'Official Sainik Schools recruitment notice. Confirm school/post-specific eligibility, employment terms and closing date in the official notice.',
)
parse_kvs = _generic_official_parser(
    'Kendriya Vidyalaya Sangathan (KVS)',
    'Official KVS recruitment notice. Confirm teaching/non-teaching eligibility, vacancies, fee and dates in the official notice.',
)
parse_sebi = _generic_official_parser(
    'Securities and Exchange Board of India (SEBI)',
    'Official SEBI recruitment opportunity. Confirm stream, eligibility, vacancies, fee, dates and application instructions in the official notice.',
)
parse_ibps = _generic_official_parser(
    'Institute of Banking Personnel Selection (IBPS)',
    'Official IBPS recruitment process notice. Confirm participating organisations, eligibility, vacancies, fee and dates in the official notification.',
)
parse_drdo = _generic_official_parser(
    'DRDO Recruitment and Assessment Centre (RAC)',
    'Official DRDO/RAC recruitment opportunity. Confirm discipline, eligibility, vacancies, fee and dates in the official notice.',
)


PRIORITY_OFFICIAL_SOURCES = (
    SourceDefinition('rbi', 'Reserve Bank of India', 'https://opportunities.rbi.org.in/Scripts/Vacancies.aspx', parse_rbi, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('sbi', 'State Bank of India — Careers', 'https://sbi.co.in/web/careers/current-openings', parse_sbi, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('nvs', 'Navodaya Vidyalaya Samiti', 'https://navodaya.gov.in/nvs/en/Recruitment/', parse_nvs, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('sainik_schools', 'Sainik Schools Society', 'https://sainikschoolsociety.in/', parse_sainik, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('kvs', 'Kendriya Vidyalaya Sangathan', 'https://kvsangathan.nic.in/en/recruitment/', parse_kvs, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('sebi', 'Securities and Exchange Board of India', 'https://www.sebi.gov.in/sebiweb/other/careerdetail.jsp?careerId=1', parse_sebi, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('ibps', 'Institute of Banking Personnel Selection', 'https://www.ibps.in/', parse_ibps, allow_missing_deadline=True, missing_deadline_max_age_days=45),
    SourceDefinition('drdo_rac', 'DRDO Recruitment and Assessment Centre', 'https://rac.gov.in/', parse_drdo, allow_missing_deadline=True, missing_deadline_max_age_days=60),
)
