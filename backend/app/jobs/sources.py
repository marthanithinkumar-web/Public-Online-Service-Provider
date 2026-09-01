import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from html import unescape
from html.parser import HTMLParser
from typing import Callable
from urllib.parse import urljoin


@dataclass
class JobItem:
    external_id: str | None
    title: str
    organization: str
    official_notice_url: str
    job_type: str = 'government'
    appointment_type: str | None = None
    location: str | None = None
    qualification: str | None = None
    age_limit: str | None = None
    application_fee: str | None = None
    vacancies: str | None = None
    salary: str | None = None
    summary: str | None = None
    issue_date: date | None = None
    application_start_date: date | None = None
    deadline: date | None = None
    application_url: str | None = None
    confidence: float = 0.0
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SourceDefinition:
    key: str
    name: str
    listing_url: str
    parser: Callable[[str, str], list[JobItem]]


def clean(value):
    return re.sub(r'\s+', ' ', str(value or '')).strip()


def parse_date(value):
    text = clean(value).replace(',', ' ')
    if not text:
        return None
    for pattern in (
        r'\b(\d{1,2})[/-](\d{1,2})[/-](20\d{2})\b',
        r'\b(\d{1,2})\s+([A-Za-z]{3,9})\s+(20\d{2})\b',
        r'\b([A-Za-z]{3,9})\s+(\d{1,2})\s+(20\d{2})\b',
    ):
        match = re.search(pattern, text, re.I)
        if not match:
            continue
        raw = ' '.join(match.groups())
        for fmt in ('%d %m %Y', '%d %b %Y', '%d %B %Y', '%b %d %Y', '%B %d %Y'):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                pass
    return None


class OfficialHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.links = []
        self.scripts = []
        self.blocks = []
        self._table_depth = 0
        self._table = None
        self._row = None
        self._cell = None
        self._link = None
        self._script = None
        self._block = None
        self._block_depth = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == 'table':
            if self._table_depth == 0:
                self._table = []
            self._table_depth += 1
        elif tag == 'tr' and self._table_depth and self._row is None:
            self._row = []
        elif tag in {'td', 'th'} and self._row is not None:
            self._cell = {'text': [], 'hrefs': []}
        elif tag == 'a':
            self._link = {'href': attributes.get('href', ''), 'text': []}
            if self._cell is not None and attributes.get('href'):
                self._cell['hrefs'].append(attributes['href'])
            if self._block is not None and attributes.get('href'):
                self._block['hrefs'].append(attributes['href'])
        elif tag == 'script':
            self._script = {'type': attributes.get('type', ''), 'id': attributes.get('id', ''), 'text': []}
        elif tag == 'li':
            if self._block is None:
                self._block = {'text': [], 'hrefs': []}
                self._block_depth = 1
            else:
                self._block_depth += 1
        elif tag == 'br':
            self.handle_data(' ')

    def handle_data(self, data):
        if self._cell is not None:
            self._cell['text'].append(data)
        if self._link is not None:
            self._link['text'].append(data)
        if self._script is not None:
            self._script['text'].append(data)
        if self._block is not None:
            self._block['text'].append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self._link is not None:
            self.links.append((self._link['href'], clean(' '.join(self._link['text']))))
            self._link = None
        elif tag in {'td', 'th'} and self._cell is not None:
            self._cell['text'] = clean(' '.join(self._cell['text']))
            self._row.append(self._cell)
            self._cell = None
        elif tag == 'tr' and self._row is not None:
            if self._table is not None and self._row:
                self._table.append(self._row)
            self._row = None
        elif tag == 'table' and self._table_depth:
            self._table_depth -= 1
            if self._table_depth == 0:
                if self._table:
                    self.tables.append(self._table)
                self._table = None
        elif tag == 'script' and self._script is not None:
            self._script['text'] = ''.join(self._script['text'])
            self.scripts.append(self._script)
            self._script = None
        elif tag == 'li' and self._block is not None:
            self._block_depth -= 1
            if self._block_depth == 0:
                self._block['text'] = clean(' '.join(self._block['text']))
                self.blocks.append(self._block)
                self._block = None


def parse_html(html):
    parser = OfficialHTMLParser()
    parser.feed(html)
    parser.close()
    return parser


def _table_records(document):
    for table in document.tables:
        rows = table
        if len(rows) < 2:
            continue
        headers = [clean(cell['text']).lower() for cell in rows[0]]
        if not headers:
            continue
        for row in rows[1:]:
            cells = row
            if len(cells) < 2:
                continue
            values = [clean(cell['text']) for cell in cells]
            record = {headers[i] if i < len(headers) else f'column_{i}': value for i, value in enumerate(values)}
            record['_row'] = row
            record['_values'] = values
            yield record


def _first(record, terms):
    for key, value in record.items():
        if key.startswith('_'):
            continue
        if any(term in key for term in terms) and clean(value):
            return clean(value)
    return None


def parse_employment_news(html, base_url):
    document = parse_html(html)
    items = []
    for index, record in enumerate(_table_records(document), start=1):
        organization = _first(record, ('organization', 'department', 'employer', 'company', 'ministry'))
        title = _first(record, ('post', 'vacancy', 'job title', 'position', 'recruitment'))
        deadline_text = _first(record, ('last date', 'closing date', 'deadline'))
        if not organization or not title:
            values = record['_values']
            if len(values) >= 4:
                organization = organization or values[1]
                title = title or values[2]
                deadline_text = deadline_text or values[-1]
        if not organization or not title or len(title) < 3:
            continue
        href = next((href for cell in record['_row'] for href in cell.get('hrefs', []) if href), None)
        notice_url = urljoin(base_url, href) if href else base_url
        external = _first(record, ('advertisement', 'advt', 'reference', 'serial', 's.no')) or f'row-{index}-{organization[:40]}-{title[:40]}'
        method = _first(record, ('method', 'mode', 'apply'))
        issue = _first(record, ('issue date', 'issued date', 'published', 'date of publication'))
        deadline = parse_date(deadline_text)
        confidence = 0.9 if deadline else 0.62
        items.append(JobItem(
            external_id=external,
            title=title,
            organization=organization,
            official_notice_url=notice_url,
            appointment_type=method,
            issue_date=parse_date(issue),
            deadline=deadline,
            application_url=notice_url,
            summary='Recruitment notice listed by Employment News. Check the official notice for complete eligibility, documents and fee details.',
            confidence=confidence,
            warnings=[] if deadline else ['Deadline was not available in the listing.'],
        ))
    return items


def parse_upsc(html, base_url):
    document = parse_html(html)
    items = []
    seen = set()
    candidates = []
    for block in document.blocks:
        candidates.extend((href, block['text']) for href in block['hrefs'])
    if not candidates:
        candidates = document.links
    for index, (link, text) in enumerate(candidates, start=1):
        context = text
        if not re.search(r'advertisement\s*(?:no\.?|number)', f'{text} {context}', re.I):
            continue
        href = urljoin(base_url, link)
        signature = (text.lower(), href)
        if signature in seen or len(text) < 5:
            continue
        seen.add(signature)
        advert = re.search(r'(?:advt\.?|advertisement)\s*(?:no\.?|number)?\s*[:.-]?\s*([A-Za-z0-9/.-]+)', context, re.I)
        deadline = parse_date(context) if re.search(r'last date|closing date|deadline', context, re.I) else None
        items.append(JobItem(
            external_id=advert.group(1) if advert else f'upsc-{index}-{text[:60]}',
            title=text,
            organization='Union Public Service Commission (UPSC)',
            official_notice_url=href,
            deadline=deadline,
            application_url='https://upsconline.nic.in/',
            summary='Official UPSC recruitment advertisement. Review the notice for post-specific eligibility, age limits, vacancies and fees.',
            confidence=0.86 if deadline else 0.64,
            warnings=[] if deadline else ['Post-specific deadline and eligibility require review of the official advertisement.'],
        ))
    return items


def _walk_json(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _pick(record, *keys):
    lowered = {str(key).lower(): value for key, value in record.items()}
    for key in keys:
        value = lowered.get(key.lower())
        if value is not None and clean(value):
            return clean(value)
    return None


def parse_ncs(html, base_url):
    """Read only explicit server-embedded NCS records; never infer jobs from page chrome."""
    document = parse_html(html)
    items = []
    seen = set()
    payloads = []
    for script in document.scripts:
        script_type = (script.get('type') or '').lower()
        body = unescape(script.get('text') or '')
        if 'json' in script_type:
            try:
                payloads.append(json.loads(body))
            except (TypeError, ValueError):
                pass
        for marker in ('__NEXT_DATA__', '__INITIAL_STATE__'):
            if marker in body:
                match = re.search(rf'{marker}\s*=\s*(\{{.*?\}})\s*;?\s*$', body, re.S)
                if match:
                    try:
                        payloads.append(json.loads(match.group(1)))
                    except ValueError:
                        pass
    for payload in payloads:
        for record in _walk_json(payload):
            title = _pick(record, 'jobTitle', 'job_title', 'title', 'vacancyName')
            organization = _pick(record, 'organizationName', 'employerName', 'companyName', 'organization')
            external_id = _pick(record, 'jobId', 'job_id', 'vacancyId', 'id')
            if not title or not organization or not external_id:
                continue
            identity = (external_id, title.lower(), organization.lower())
            if identity in seen:
                continue
            seen.add(identity)
            url = _pick(record, 'jobUrl', 'detailUrl', 'url')
            notice_url = urljoin(base_url, url) if url else base_url
            deadline = parse_date(_pick(record, 'lastDate', 'closingDate', 'deadline'))
            sector = _pick(record, 'sector', 'employerType', 'jobType') or ''
            job_type = 'government' if re.search(r'government|public sector|psu', sector, re.I) else 'private'
            items.append(JobItem(
                external_id=external_id,
                title=title,
                organization=organization,
                official_notice_url=notice_url,
                job_type=job_type,
                appointment_type=_pick(record, 'employmentType', 'appointmentType'),
                location=_pick(record, 'location', 'district', 'state'),
                qualification=_pick(record, 'qualification', 'education'),
                age_limit=_pick(record, 'ageLimit', 'age'),
                salary=_pick(record, 'salary', 'salaryRange'),
                deadline=deadline,
                application_url=notice_url,
                summary=_pick(record, 'description', 'summary') or 'Job listing supplied through the official National Career Service portal.',
                confidence=0.88 if deadline else 0.68,
                warnings=[] if deadline else ['Closing date was not present in the server-provided listing data.'],
            ))
    return items


SOURCE_DEFINITIONS = (
    SourceDefinition('employment_news', 'Employment News', 'https://employmentnews.gov.in/NewEmp/AllJobs.aspx?k=All', parse_employment_news),
    SourceDefinition('upsc', 'Union Public Service Commission', 'https://www.upsc.gov.in/recruitment/recruitment-advertisement', parse_upsc),
    SourceDefinition('ncs', 'National Career Service', 'https://www.ncs.gov.in/job-listing', parse_ncs),
)

SOURCE_BY_KEY = {source.key: source for source in SOURCE_DEFINITIONS}
