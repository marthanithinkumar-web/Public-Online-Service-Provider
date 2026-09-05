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
    'tribal.nic.in',
    'www.tribal.nic.in',
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


def is_official_url(url):
    try:
        parsed = urlparse(str(url or ''))
    except ValueError:
        return False
    return parsed.scheme == 'https' and (parsed.hostname or '').lower().rstrip('.') in OFFICIAL_HOSTS


def source_key_for_url(url):
    host = (urlparse(str(url or '')).hostname or '').lower().rstrip('.')
    if host == 'scholarships.gov.in':
        return 'nsp'
    if host == 'telanganaepass.cgg.gov.in':
        return 'tg_epass'
    if host == 'jnanabhumi.ap.gov.in':
        return 'ap_jnanabhumi'
    if host in {'socialjustice.gov.in', 'www.socialjustice.gov.in'}:
        return 'social_justice'
    if host in {'tribal.nic.in', 'www.tribal.nic.in'}:
        return 'tribal_affairs'
    return None


def _education_level(title):
    text = title.lower()
    if 'pre matric' in text or 'pre-matric' in text or 'school' in text:
        return 'School / Pre Matric'
    if 'post matric' in text or 'post-matric' in text:
        return 'Post Matric'
    if 'diploma' in text:
        return 'Technical Diploma'
    if 'degree' in text:
        return 'Degree / Technical Degree'
    if 'post graduate' in text or 'postgraduate' in text or 'pg ' in f'{text} ':
        return 'Post Graduate'
    if 'higher education' in text or 'college' in text or 'university' in text:
        return 'Higher Education'
    if 'overseas' in text:
        return 'Higher Education / Overseas'
    return 'Students'


def _region(title):
    text = title.lower()
    if 'north eastern' in text or ' ner ' in f' {text} ' or 'ishan uday' in text:
        return 'North Eastern Region'
    if 'jammu' in text and 'kashmir' in text:
        return 'Jammu & Kashmir / Ladakh'
    return 'India'


def official_item(title, provider, source, *, deadline=None, category=None, region='India', education_level=None,
                  eligibility=None, application_url=None, academic_year=None, now=None, record_type='scholarship'):
    stamp = (now or datetime.now(timezone.utc)).isoformat()
    source_url = source['url']
    return {
        'id': f"{source['key']}-{slugify(title)}",
        'slug': slugify(title),
        'title': re.sub(r'\s+', ' ', title).strip(),
        'provider': provider,
        'source_name': source['name'],
        'source_url': source_url,
        'application_url': application_url or source_url,
        'deadline': deadline,
        'region': region,
        'education_level': education_level or _education_level(title),
        'category': category or 'Scholarship',
        'eligibility': eligibility or 'Apply only if you meet the current eligibility criteria published by the official provider.',
        'status': 'active',
        'source_key': source['key'],
        'source_type': 'official',
        'is_official': True,
        'record_type': record_type,
        'academic_year': academic_year,
        'discovery_method': 'official_page',
        'verified_at': stamp,
        'last_seen_at': stamp,
    }


def _academic_year(text):
    match = re.search(r'(20\d{2}\s*[-–]\s*\d{2})', text)
    return re.sub(r'\s+', '', match.group(1)).replace('–', '-') if match else None


def _provider_before(lines, index):
    provider_markers = ('ministry ', 'department ', 'all india council', 'north eastern council', 'ugc', 'aicte')
    for candidate in reversed(lines[max(0, index - 24):index]):
        lower = candidate.lower()
        if lower.startswith(provider_markers) and len(candidate) <= 160:
            return candidate
    return 'Government of India (via National Scholarship Portal)'


def parse_nsp(document, source, now=None):
    lines = html_lines(document)
    year = _academic_year(' '.join(lines[:80]))
    items = []
    seen = set()
    title_words = ('scholarship', 'fellowship', 'financial assistance for education', 'stipend scheme')
    for index, line in enumerate(lines):
        if 'student application open till' not in line.lower():
            continue
        window = ' '.join(lines[index:index + 3])
        deadline = iso_date(window)
        if not deadline:
            continue
        title = None
        title_index = index
        for offset in range(index - 1, max(-1, index - 12), -1):
            candidate = lines[offset]
            lower = candidate.lower()
            if any(word in lower for word in title_words) and 'student application' not in lower and 'scheme open from' not in lower:
                title = candidate
                title_index = offset
                break
        if not title:
            continue
        title = re.sub(r'\s*\((?:Merit|Welfare) Based Scheme\)\s*$', '', title, flags=re.I).strip()
        key = slugify(title)
        if key in seen:
            continue
        seen.add(key)
        nearby = ' '.join(lines[max(0, title_index - 2):index + 1])
        category = 'Welfare Based' if 'welfare based scheme' in nearby.lower() else ('Merit Based' if 'merit based scheme' in nearby.lower() else 'Scholarship')
        items.append(official_item(
            title,
            _provider_before(lines, title_index),
            source,
            deadline=deadline,
            category=category,
            region=_region(title),
            academic_year=year,
            application_url='https://scholarships.gov.in/Students',
            now=now,
        ))
    return items


def parse_tg_postmatric(document, source, now=None):
    text = ' '.join(html_lines(document))
    year = _academic_year(text)
    if not year:
        return []
    items = []
    if re.search(r'Postmatric Scholarships For Fresh Registration\s*\(?\s*' + re.escape(year), text, re.I):
        items.append(official_item(
            f'Telangana ePASS Post-Matric Scholarship - Fresh Registration {year}',
            'Social Welfare Department, Government of Telangana', source,
            region='Telangana', education_level='Post Matric', category='Welfare Based', academic_year=year,
            eligibility='Eligible Telangana post-matric students must verify department, course, caste/category and current ePASS requirements.',
            now=now,
        ))
    if re.search(r'Postmatric Scholarships For Renewal Registration\s*\(?\s*' + re.escape(year), text, re.I):
        items.append(official_item(
            f'Telangana ePASS Post-Matric Scholarship - Renewal {year}',
            'Social Welfare Department, Government of Telangana', source,
            region='Telangana', education_level='Post Matric', category='Welfare Based', academic_year=year,
            eligibility='Existing eligible Telangana ePASS beneficiaries should verify current renewal requirements on the official portal.',
            now=now,
        ))
    if 'Other State Students Pre-Registration' in text and year in text:
        items.append(official_item(
            f'Telangana ePASS Other-State Post-Matric Scholarship Registration {year}',
            'Social Welfare Department, Government of Telangana', source,
            region='Telangana / Students studying outside Telangana', education_level='Post Matric', category='Welfare Based', academic_year=year,
            eligibility='For eligible Telangana students studying outside the state; verify current ePASS other-state conditions.',
            now=now,
        ))
    return items


def parse_tg_prematric(document, source, now=None):
    text = ' '.join(html_lines(document))
    year = _academic_year(text)
    if not year:
        return []
    items = []
    if 'Prematric Scholarships For SC/ST/PWD Students Fresh Registration' in text:
        items.append(official_item(
            f'Telangana ePASS Pre-Matric Scholarship - Fresh Registration {year}',
            'Social Welfare Department, Government of Telangana', source,
            region='Telangana', education_level='School / Pre Matric', category='Welfare Based', academic_year=year,
            eligibility='Eligible SC, ST and PwD school students should verify current class and welfare-department criteria.',
            now=now,
        ))
    if 'Prematric Scholarships For SC/ST/BC Renewal Registration' in text:
        items.append(official_item(
            f'Telangana ePASS Pre-Matric Scholarship - Renewal {year}',
            'Social Welfare Department, Government of Telangana', source,
            region='Telangana', education_level='School / Pre Matric', category='Welfare Based', academic_year=year,
            eligibility='Existing eligible SC, ST and BC pre-matric beneficiaries should verify current renewal requirements.',
            now=now,
        ))
    return items


def parse_tg_overseas(document, source, now=None):
    text = ' '.join(html_lines(document))
    definitions = (
        ('Ambedkar Overseas Vidya Nidhi', 'SC students', 'Ambedkar Overseas Vidya Nidhi for SC Students'),
        ("Chief Minister's Overseas Scholarship Scheme for Minorities", 'minority students', "Chief Minister's Overseas Scholarship Scheme for Minority Students"),
        ('Mahatma Jyothiba Phule Overseas Vidya Nidhi', 'BC and EBC students', 'Mahatma Jyothiba Phule Overseas Vidya Nidhi for BC/EBC Students'),
    )
    positions = [(text.lower().find(marker.lower()), marker, audience, title) for marker, audience, title in definitions]
    positions = sorted([entry for entry in positions if entry[0] >= 0])
    items = []
    for pos_index, (start, marker, audience, title) in enumerate(positions):
        end = positions[pos_index + 1][0] if pos_index + 1 < len(positions) else len(text)
        block = text[start:end]
        if 'registrations closed' in block.lower():
            continue
        if 'registration' not in block.lower():
            continue
        deadline_match = re.search(r'Last Date[^\d]{0,80}(\d{1,2}[-/.]\d{1,2}[-/.]20\d{2})', block, re.I)
        deadline = iso_date(deadline_match.group(1)) if deadline_match else None
        items.append(official_item(
            title,
            'Government of Telangana', source,
            deadline=deadline, region='Telangana', education_level='Higher Education / Overseas', category='Welfare Based',
            eligibility=f'For eligible {audience}; verify income, academic, admission, country and current session conditions on Telangana ePASS.',
            now=now,
        ))
    return items


def parse_ap_jnanabhumi(document, source, now=None):
    text = ' '.join(html_lines(document))
    if 'Post Matric Scholarships(RTF/MTF)' not in text and 'Post Matric Scholarships (RTF/MTF)' not in text:
        return []
    return [official_item(
        'Andhra Pradesh JnanaBhumi Post-Matric Scholarships (RTF/MTF)',
        'Directorate of Social Welfare, Government of Andhra Pradesh', source,
        region='Andhra Pradesh', education_level='Post Matric', category='Welfare Based',
        eligibility='Eligible SC, ST, BC, EBC, Kapu, Minority and Differently Abled students should verify current JnanaBhumi income, attendance and course conditions.',
        application_url='https://jnanabhumi.ap.gov.in/', now=now,
    )]


def parse_social_justice(document, source, now=None):
    lines = html_lines(document)
    items = []
    seen = set()
    for index, line in enumerate(lines):
        lower = line.lower()
        if not any(term in lower for term in ('scholarship', 'top class education', 'national overseas')):
            continue
        if len(line) < 12 or len(line) > 260 or lower.startswith(('news / events', 'showing ')):
            continue
        title = re.sub(r'^\d+\s+', '', line).strip()
        key = slugify(title)
        if key in seen:
            continue
        seen.add(key)
        date_window = ' '.join(lines[index:index + 4])
        published = iso_date(date_window)
        item = official_item(
            title,
            'Department of Social Justice & Empowerment, Government of India', source,
            category='Official Scholarship Notice', education_level=_education_level(title),
            eligibility='Review the linked official notice and current application portal for exact eligibility and dates.',
            record_type='official_notice', now=now,
        )
        if published:
            item['published_date'] = published
        items.append(item)
    return items[:12]


def parse_tribal_affairs(document, source, now=None):
    lines = html_lines(document)
    today = (now or datetime.now(timezone.utc)).date()
    candidates = []
    for index, line in enumerate(lines):
        lower = line.lower()
        if 'national overseas scholarship' not in lower and 'nos for st' not in lower:
            continue
        window = ' '.join(lines[max(0, index - 1):index + 3])
        year_match = re.search(r'(20\d{2}-\d{2})', window)
        if not year_match:
            continue
        deadline = None
        extended = re.search(r'new deadline\s*:\s*([^,.;]{4,40})', window, re.I)
        if extended:
            deadline = human_date(extended.group(1))
        if not deadline:
            till = re.search(r'(?:open\s+till|deadline\s*:?|last date[^:]{0,30}:)\s*([^,.;]{4,40})', window, re.I)
            if till:
                deadline = human_date(till.group(1))
        if not deadline:
            deadline = human_date(window)
        if not deadline:
            continue
        candidates.append((year_match.group(1), deadline))

    if not candidates:
        return []
    year = sorted({year for year, _ in candidates}, reverse=True)[0]
    deadlines = [deadline for candidate_year, deadline in candidates if candidate_year == year]
    deadline = max(deadlines)
    if datetime.fromisoformat(deadline).date() < today:
        return []
    return [official_item(
        f'National Overseas Scholarship for ST Students {year}',
        'Ministry of Tribal Affairs, Government of India', source,
        deadline=deadline, region='India', education_level='Higher Education / Overseas', category='Welfare Based', academic_year=year,
        eligibility='ST students should verify the current National Overseas Scholarship selection-year rules and application conditions on the official portal.',
        application_url=source['url'], record_type='scholarship', now=now,
    )]


PARSERS = {
    'nsp': parse_nsp,
    'tg_postmatric': parse_tg_postmatric,
    'tg_prematric': parse_tg_prematric,
    'tg_overseas': parse_tg_overseas,
    'ap_jnanabhumi': parse_ap_jnanabhumi,
    'social_justice': parse_social_justice,
    'tribal_affairs': parse_tribal_affairs,
}


def fetch_source(source, session=None, attempts=3):
    if not is_official_url(source['url']):
        raise ValueError(f"Source URL is not allow-listed: {source['key']}")
    client = session or requests.Session()
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            response = client.get(
                source['url'],
                headers={'User-Agent': USER_AGENT, 'Accept': 'text/html,application/xhtml+xml'},
                timeout=(7, 30),
                allow_redirects=True,
            )
            if not is_official_url(response.url):
                raise ValueError(f"Source redirected outside the official allow-list: {source['key']}")
            response.raise_for_status()
            if len(response.content) > 5_000_000:
                raise ValueError(f"Source response is unexpectedly large: {source['key']}")
            return response.text
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(2 * attempt)
    raise RuntimeError(f"{source['key']} fetch failed: {type(last_error).__name__}")


def dedupe_items(items):
    selected = {}
    for item in items:
        title_key = slugify(item.get('title'))
        region_key = slugify(item.get('region') or 'india')
        key = (title_key, region_key)
        existing = selected.get(key)
        if existing is None:
            selected[key] = item
            continue
        # Prefer an application record with a known deadline over a notice-only duplicate.
        existing_score = (existing.get('record_type') == 'scholarship', bool(existing.get('deadline')), existing.get('source_key') == 'nsp')
        candidate_score = (item.get('record_type') == 'scholarship', bool(item.get('deadline')), item.get('source_key') == 'nsp')
        if candidate_score > existing_score:
            selected[key] = item
    return list(selected.values())


def discover_official_scholarships(session=None, now=None, sources=None):
    checked_at = (now or datetime.now(timezone.utc)).isoformat()
    items = []
    health = {}
    for source in sources or SOURCE_DEFINITIONS:
        started = time.monotonic()
        try:
            document = fetch_source(source, session=session)
            parsed = PARSERS[source['parser']](document, source, now=now)
            parsed = [item for item in parsed if item.get('title') and is_official_url(item.get('source_url')) and is_official_url(item.get('application_url'))]
            items.extend(parsed)
            health[source['key']] = {
                'ok': True,
                'source_name': source['name'],
                'source_url': source['url'],
                'count': len(parsed),
                'checked_at': checked_at,
                'elapsed_ms': int((time.monotonic() - started) * 1000),
            }
        except Exception as exc:
            health[source['key']] = {
                'ok': False,
                'source_name': source['name'],
                'source_url': source['url'],
                'count': 0,
                'checked_at': checked_at,
                'error': f'{type(exc).__name__}: {str(exc)[:180]}',
                'elapsed_ms': int((time.monotonic() - started) * 1000),
            }
    return dedupe_items(items), health
