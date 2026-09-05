"""Daily discovery of current scholarships from authoritative Indian portals.

The public snapshot is intentionally generated from allow-listed sources only. A
source outage is recorded in health metadata instead of turning arbitrary web
content into a scholarship listing.
"""

import re
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urlparse

import requests

OFFICIAL_HOSTS = {
    'scholarships.gov.in',
    'telanganaepass.cgg.gov.in',
    'jnanabhumi.ap.gov.in',
    'socialjustice.gov.in',
    'www.socialjustice.gov.in',
    'nosmsje.gov.in',
    'www.nosmsje.gov.in',
    'tribal.nic.in',
    'www.tribal.nic.in',
    'tribal.gov.in',
    'www.tribal.gov.in',
    'overseas.tribal.gov.in',
}

USER_AGENT = 'PublicOnlineServiceProvider-ScholarshipDiscovery/1.0 (+https://public-online-service-provider-india.onrender.com)'

SOURCE_DEFINITIONS = (
    {'key': 'nsp', 'name': 'National Scholarship Portal', 'url': 'https://scholarships.gov.in/All-Scholarships', 'parser': 'nsp'},
    {'key': 'tg_epass_postmatric', 'name': 'Telangana ePASS - Post Matric', 'url': 'https://telanganaepass.cgg.gov.in/epassonlinelinks.jsp', 'parser': 'tg_postmatric'},
    {'key': 'tg_epass_prematric', 'name': 'Telangana ePASS - Pre Matric', 'url': 'https://telanganaepass.cgg.gov.in/PrematricLinks.do', 'parser': 'tg_prematric'},
    {'key': 'tg_epass_overseas', 'name': 'Telangana ePASS - Overseas Scholarships', 'url': 'https://telanganaepass.cgg.gov.in/OverseasLinks.do', 'parser': 'tg_overseas'},
    {'key': 'ap_jnanabhumi', 'name': 'Andhra Pradesh JnanaBhumi', 'url': 'https://jnanabhumi.ap.gov.in/', 'parser': 'ap_jnanabhumi'},
    {'key': 'social_justice', 'name': 'Department of Social Justice & Empowerment', 'url': 'https://socialjustice.gov.in/schemes', 'parser': 'social_justice'},
    {'key': 'tribal_affairs', 'name': 'Ministry of Tribal Affairs', 'url': 'https://tribal.nic.in/WhatsNewsArchives.aspx', 'parser': 'tribal_affairs'},
)


class _VisibleText(HTMLParser):
    block_tags = {'article', 'br', 'button', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'p', 'section', 'td', 'th', 'tr'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style', 'noscript'}:
            self.hidden += 1
        elif not self.hidden and tag in self.block_tags:
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in {'script', 'style', 'noscript'} and self.hidden:
            self.hidden -= 1
        elif not self.hidden and tag in self.block_tags:
            self.parts.append('\n')

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def html_lines(document):
    parser = _VisibleText()
    parser.feed(document or '')
    raw = ''.join(parser.parts).replace('\xa0', ' ')
    lines = []
    for part in raw.splitlines():
        cleaned = re.sub(r'\s+', ' ', part).strip(' \t|')
        if cleaned and cleaned.lower() not in {'image', 'view', 'click here'}:
            lines.append(cleaned)
    return lines


def slugify(value):
    value = re.sub(r'[^a-z0-9]+', '-', str(value or '').lower()).strip('-')
    return value[:150] or 'scholarship'


def iso_date(value):
    match = re.search(r'(?<!\d)(\d{1,2})[-/.](\d{1,2})[-/.](20\d{2})(?!\d)', str(value or ''))
    if not match:
        return None
    day, month, year = map(int, match.groups())
    try:
        return datetime(year, month, day).date().isoformat()
    except ValueError:
        return None


_MONTHS = {
    'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
    'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
    'aug': 8, 'august': 8, 'sep': 9, 'sept': 9, 'september': 9, 'oct': 10,
    'october': 10, 'nov': 11, 'november': 11, 'dec': 12, 'december': 12,
}


def human_date(value):
    numeric = iso_date(value)
    if numeric:
        return numeric
    match = re.search(
        r'(?<!\d)(\d{1,2})(?:st|nd|rd|th)?\s+'
        r'(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
        r'[,\s]+(20\d{2})(?!\d)',
        str(value or ''), re.I,
    )
    if not match:
        return None
    day = int(match.group(1))
    month = _MONTHS[match.group(2).lower()]
    year = int(match.group(3))
    try:
        return datetime(year, month, day).date().isoformat()
    except ValueError:
        return None


def deadline_from_text(value):
    return human_date(value)


def _base_item(source, title, deadline, region='India', education_level='Students', category='Scholarship', eligibility='Verify eligibility on the official source.'):
    return {
        'id': f"{source['key']}-{slugify(title)}",
        'slug': slugify(title),
        'title': title,
        'provider': source['name'],
        'source_name': source['name'],
        'source_url': source['url'],
        'application_url': source['url'],
        'deadline': deadline,
        'region': region,
        'education_level': education_level,
        'category': category,
        'eligibility': eligibility,
        'status': 'active',
        'source_key': source['key'],
        'source_type': 'official',
        'is_official': True,
        'record_type': 'scholarship',
        'academic_year': None,
        'discovery_method': 'official_page',
    }


def _year_hint(text):
    match = re.search(r'20\d{2}\s*[-/]\s*\d{2}', str(text or ''))
    return match.group(0).replace(' ', '').replace('/', '-') if match else None


def parse_nsp(document, source, now=None):
    lines = html_lines(document)
    items = []
    seen = set()
    current_provider = 'Government of India (via National Scholarship Portal)'
    current_category = 'Scholarship'
    current_level = 'Students'
    for line in lines:
        lower = line.lower()
        if lower.startswith('ministry of ') or lower.startswith('department of '):
            current_provider = line[:180]
            continue
        if 'scholarship' not in lower and 'fellowship' not in lower:
            continue
        if len(line) < 12 or len(line) > 260:
            continue
        title = line
        marker = title.lower()
        if marker in seen:
            continue
        seen.add(marker)
        deadline = human_date(line)
        item = _base_item(source, title, deadline, education_level=current_level, category=current_category)
        item['provider'] = current_provider
        item['application_url'] = 'https://scholarships.gov.in/Students'
        item['academic_year'] = _year_hint(line) or '2026-27'
        items.append(item)
    return items


def parse_telangana(document, source, now=None):
    lines = html_lines(document)
    items = []
    seen = set()
    for line in lines:
        lower = line.lower()
        if not any(token in lower for token in ('scholarship', 'vidya', 'fee reimbursement', 'epass')):
            continue
        if len(line) < 10 or len(line) > 260:
            continue
        marker = line.lower()
        if marker in seen:
            continue
        seen.add(marker)
        item = _base_item(source, line, human_date(line), region='Telangana', category='Welfare Based')
        item['provider'] = 'Government of Telangana'
        items.append(item)
    return items


def parse_ap_jnanabhumi(document, source, now=None):
    lines = html_lines(document)
    items = []
    seen = set()
    for line in lines:
        lower = line.lower()
        if 'scholarship' not in lower and 'fee reimbursement' not in lower:
            continue
        if len(line) < 10 or len(line) > 260:
            continue
        if line.lower() in seen:
            continue
        seen.add(line.lower())
        item = _base_item(source, line, human_date(line), region='Andhra Pradesh', category='Welfare Based')
        item['provider'] = 'Government of Andhra Pradesh'
        items.append(item)
    return items


def parse_social_justice(document, source, now=None):
    now = now or datetime.now(timezone.utc)
    lines = html_lines(document)
    items = []
    seen = set()
    for line in lines:
        lower = line.lower()
        if not any(token in lower for token in ('scholarship', 'fellowship', 'overseas')):
            continue
        if len(line) < 12 or len(line) > 320:
            continue
        if line.lower() in seen:
            continue
        seen.add(line.lower())
        deadline = human_date(line)
        if deadline and deadline < now.date().isoformat():
            continue
        item = _base_item(source, line, deadline, category='Welfare Based')
        item['provider'] = 'Department of Social Justice & Empowerment'
        item['record_type'] = 'official_notice'
        item['academic_year'] = _year_hint(line)
        items.append(item)
    return items


def parse_tribal_affairs(document, source, now=None):
    now = now or datetime.now(timezone.utc)
    text = ' '.join(html_lines(document))
    if 'national overseas scholarship' not in text.lower():
        return []
    deadline_candidates = []
    for match in re.finditer(r'(?:deadline|open till|last date)[^.!?]{0,100}', text, re.I):
        parsed = human_date(match.group(0))
        if parsed:
            deadline_candidates.append(parsed)
    deadline = max(deadline_candidates) if deadline_candidates else None
    if deadline and deadline < now.date().isoformat():
        return []
    title = 'National Overseas Scholarship (NOS) for ST Candidates'
    item = _base_item(
        source,
        title,
        deadline,
        category='Welfare Based',
        eligibility='For eligible Scheduled Tribe candidates; verify income, academic, admission, country and current selection-year conditions on the Ministry of Tribal Affairs portal.',
    )
    item['provider'] = 'Ministry of Tribal Affairs'
    item['academic_year'] = _year_hint(text)
    return [item]


PARSERS = {
    'nsp': parse_nsp,
    'tg_postmatric': parse_telangana,
    'tg_prematric': parse_telangana,
    'tg_overseas': parse_telangana,
    'ap_jnanabhumi': parse_ap_jnanabhumi,
    'social_justice': parse_social_justice,
    'tribal_affairs': parse_tribal_affairs,
}


def validate_source_url(url):
    parsed = urlparse(str(url or ''))
    if parsed.scheme != 'https' or parsed.hostname not in OFFICIAL_HOSTS:
        raise ValueError('Scholarship discovery only permits approved official HTTPS hosts.')
    return url


def fetch_source(source, *, timeout=8):
    url = validate_source_url(source['url'])
    response = requests.get(
        url,
        headers={
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml',
            'Cache-Control': 'no-cache',
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.text


def discover_source(source, *, now=None, timeout=8):
    now = now or datetime.now(timezone.utc)
    started = time.monotonic()
    try:
        document = fetch_source(source, timeout=timeout)
        parser = PARSERS[source['parser']]
        items = parser(document, source, now=now)
        return {
            'ok': True,
            'source_name': source['name'],
            'source_url': source['url'],
            'count': len(items),
            'items': items,
            'checked_at': now.isoformat(),
            'elapsed_ms': int((time.monotonic() - started) * 1000),
        }
    except Exception as exc:
        return {
            'ok': False,
            'source_name': source['name'],
            'source_url': source['url'],
            'count': 0,
            'items': [],
            'checked_at': now.isoformat(),
            'error': f'{type(exc).__name__}: {source["key"]} fetch failed: {type(exc).__name__.replace("Error", "").replace("Exception", "").strip() or "error"}',
            'elapsed_ms': int((time.monotonic() - started) * 1000),
        }


def discover_all(*, now=None, timeout=8):
    now = now or datetime.now(timezone.utc)
    source_health = {}
    items = []
    for source in SOURCE_DEFINITIONS:
        result = discover_source(source, now=now, timeout=timeout)
        health = {key: value for key, value in result.items() if key != 'items'}
        source_health[source['key']] = health
        items.extend(result['items'])
    return items, source_health
