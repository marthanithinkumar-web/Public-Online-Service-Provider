"""Central Railway Recruitment Control Board source."""

import re
from urllib.parse import urljoin

from .sources import JobItem, SourceDefinition, clean, parse_html, _table_records, _row_url

_CEN_RE = re.compile(r'\bCEN\s+(?:RPF\s+)?\d{1,2}/20\d{2}\b|\bCEN\s+RRC\s+\d{1,2}/20\d{2}\b', re.I)


def parse_rrcb(html, base_url):
    """Read centrally published CEN entries from RRCB, New Delhi."""
    document = parse_html(html)
    items = []
    seen = set()
    for record in _table_records(document):
        text = clean(' '.join(record.get('_values', [])))
        match = _CEN_RE.search(text)
        if not match:
            continue
        cen = clean(match.group(0)).upper()
        if cen in seen:
            continue
        seen.add(cen)
        notice_url = _row_url(record, base_url) or base_url
        title = text
        title = re.sub(r'^\d+\s+', '', title).strip()
        items.append(JobItem(
            external_id=cen.replace(' ', '-').replace('/', '-'),
            title=title[:500],
            organization='Railway Recruitment Control Board (RRCB), Ministry of Railways',
            official_notice_url=urljoin(base_url, notice_url),
            location='India',
            application_url='https://www.rrbapply.gov.in/',
            summary='Central employment notification published by the Railway Recruitment Control Board, Ministry of Railways. Check the linked CEN for participating RRBs, posts, eligibility, vacancies, fees and dates.',
            confidence=0.86,
            warnings=['The closing date and post-specific details must be confirmed in the official CEN.'],
        ))
    return items


RRCB_SOURCE = SourceDefinition(
    'rrb',
    'Railway Recruitment Control Board (RRCB)',
    'https://www.rrcb.gov.in/Employment_notices.html',
    parse_rrcb,
    allow_missing_deadline=True,
    missing_deadline_max_age_days=120,
)
