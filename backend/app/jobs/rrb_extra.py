"""Additional official Railway Recruitment Board source definitions.

Keep regional RRBs independent so a temporary outage at one board does not
remove railway recruitment coverage from the verified feed.
"""

import re
from html import unescape
from urllib.parse import urljoin, urlparse

from .sources import JobItem, SourceDefinition, clean, parse_all_dates


_CEN_RE = re.compile(r'\bCEN\s*(?:No\.?\s*)?(\d{1,2})[/-](20\d{2})\b', re.I)
_EXCLUDED = re.compile(
    r'answer key|admit card|e[ -]?call|exam(?:ination)? (?:city|schedule)|result|score card|'
    r'application status|response|objection|document verification|medical examination|'
    r'corrigendum|addendum|migration|faq|frequently asked',
    re.I,
)
_INITIAL = re.compile(
    r'detailed\s+central(?:is|iz)ed\s+(?:employment\s+)?notification|'
    r'detailed\s+central(?:is|iz)ed\s+employment\s+notice|'
    r'central(?:is|iz)ed\s+employment\s+(?:notification|notice)|'
    r'recruitment\s+(?:to|for)\s+the\s+posts?',
    re.I,
)


def _text(fragment):
    fragment = re.sub(r'<(?:script|style)\b[^>]*>.*?</(?:script|style)>', ' ', fragment, flags=re.I | re.S)
    fragment = re.sub(r'<img\b[^>]*(?:alt|title)=["\']([^"\']+)["\'][^>]*>', r' \1 ', fragment, flags=re.I)
    fragment = re.sub(r'<[^>]+>', ' ', fragment)
    return clean(unescape(fragment))


def parse_rrb_regional(html, base_url):
    """Extract initial CEN recruitment notices from card/link based RRB pages."""
    raw = str(html or '')
    board_host = (urlparse(base_url).hostname or '').lower()
    board = 'Secunderabad' if 'secunderabad' in board_host else 'Chennai' if 'chennai' in board_host else 'Regional'
    items = []
    seen = set()

    anchors = list(re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>.*?</a>', raw, re.I | re.S))
    for match in anchors:
        href = clean(match.group(1))
        if not href or href.startswith(('#', 'javascript:', 'mailto:')):
            continue
        start = max(0, match.start() - 900)
        end = min(len(raw), match.end() + 450)
        context = _text(raw[start:end])
        cen = _CEN_RE.search(context)
        if not cen or _EXCLUDED.search(context) or not _INITIAL.search(context):
            continue
        key = f'CEN{int(cen.group(1)):02d}/{cen.group(2)}'
        if key in seen:
            continue
        notice_url = urljoin(base_url, href)
        if not notice_url.startswith('https://'):
            continue
        seen.add(key)
        dates = parse_all_dates(context)
        issue_date = dates[0] if dates else None
        title_match = re.search(
            r'(CEN\s*(?:No\.?\s*)?\d{1,2}[/-]20\d{2}[^.]{0,260}?(?:posts?|categories|ALP|Technician|Controller|JE|DMS)[^.]*)',
            context,
            re.I,
        )
        title = clean(title_match.group(1)) if title_match else f'{key} Railway Recruitment'
        items.append(JobItem(
            external_id=f'{board.lower()}-{key}'.replace('/', '-'),
            title=title[:500],
            organization=f'Railway Recruitment Board (RRB) {board}',
            official_notice_url=notice_url,
            location=board,
            issue_date=issue_date,
            application_url=notice_url,
            summary=f'Official RRB {board} Centralised Employment Notice. Confirm posts, eligibility, vacancies, fees and application dates in the linked official notice.',
            confidence=0.84,
            warnings=['The closing date must be confirmed in the official RRB notice.'],
        ))
    return items


EXTRA_RRB_SOURCES = (
    SourceDefinition(
        'rrb_secunderabad',
        'Railway Recruitment Board — Secunderabad',
        'https://rrbsecunderabad.gov.in/employment-notice/',
        parse_rrb_regional,
        allow_missing_deadline=True,
        missing_deadline_max_age_days=60,
    ),
    SourceDefinition(
        'rrb_chennai',
        'Railway Recruitment Board — Chennai',
        'https://www.rrbchennai.gov.in/',
        parse_rrb_regional,
        allow_missing_deadline=True,
        missing_deadline_max_age_days=60,
    ),
)
