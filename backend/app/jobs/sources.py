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
    allow_missing_deadline: bool = False
    missing_deadline_max_age_days: int = 45


def clean(value):
    return re.sub(r'\s+', ' ', str(value or '')).strip()


def parse_date(value):
    text = clean(value).replace(',', ' ')
    if not text:
        return None
    for pattern in (
        r'(?<!\d)(20\d{2})-(\d{1,2})-(\d{1,2})(?!\d)',
        r'\b(\d{1,2})[/-](\d{1,2})[/-](20\d{2})\b',
        r'\b(\d{1,2})\s+([A-Za-z]{3,9})\s+(20\d{2})\b',
        r'\b([A-Za-z]{3,9})\s+(\d{1,2})\s+(20\d{2})\b',
    ):
        match = re.search(pattern, text, re.I)
        if not match:
            continue
        raw = ' '.join(match.groups())
        for fmt in ('%Y %m %d', '%d %m %Y', '%d %b %Y', '%d %B %Y', '%b %d %Y', '%B %d %Y'):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                pass
    return None


def parse_all_dates(value):
    text = clean(value).replace(',', ' ')
    candidates = re.findall(
        r'20\d{2}-\d{1,2}-\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]20\d{2}|'
        r'\d{1,2}\s+[A-Za-z]{3,9}\s+20\d{2}|[A-Za-z]{3,9}\s+\d{1,2}\s+20\d{2}',
        text,
        re.I,
    )
    return [parsed for parsed in (parse_date(candidate) for candidate in candidates) if parsed]


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


def _visible_text(html):
    """Return compact visible text for official pages without a data table."""
    value = re.sub(r'<(?:script|style)\b[^>]*>.*?</(?:script|style)>', ' ', str(html or ''), flags=re.I | re.S)
    value = re.sub(r'<[^>]+>', ' ', value)
    return clean(unescape(value))


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


def _row_url(record, base_url):
    hrefs = [href for cell in record.get('_row', []) for href in cell.get('hrefs', []) if href]
    if not hrefs:
        return None
    preferred = next((href for href in hrefs if re.search(r'\.pdf(?:$|\?)|attachment|notice|notification', href, re.I)), hrefs[0])
    return urljoin(base_url, preferred)


def _record_dates(record):
    values = ' '.join(record.get('_values', []))
    return parse_all_dates(values)


def _deep_strings(value):
    if isinstance(value, dict):
        for child in value.values():
            yield from _deep_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _deep_strings(child)
    elif isinstance(value, str):
        yield clean(unescape(value))


def _record_url(record, base_url, attachment_root=None):
    candidates = []
    for value in _deep_strings(record):
        if re.search(r'https?://|^/|\.pdf(?:$|\?)|attachment', value, re.I):
            candidates.append(value)
    preferred = next((value for value in candidates if re.search(r'\.pdf(?:$|\?)|attachment', value, re.I)), None)
    if not preferred:
        preferred = next((value for value in candidates if value.startswith(('https://', '/'))), None)
    if not preferred:
        return None
    if attachment_root and re.fullmatch(r'[^/]+\.pdf', preferred, re.I):
        return urljoin(attachment_root, preferred)
    return urljoin(base_url, preferred)


def _looks_like_initial_recruitment(text):
    lowered = clean(text).lower()
    excluded = (
        'result', 'answer key', 'admission certificate', 'admit card', 'exam city',
        'city of examination', 'response sheet', 'marks of', 'allocation', 'schedule',
        'corrigendum', 'addendum', 'cancellation', 'cancelled', 'shortlisted',
        'physical test', 'document verification', 'typing test', 'skill test',
    )
    if any(term in lowered for term in excluded):
        return False
    return bool(re.search(
        r'centralis(?:ed|zed) employment notice|detailed employment notice|'
        r'^(?:notice (?:of|for) )?.+ examination,?\s*20\d{2}(?:\s*[-–—:].*)?$|'
        r'notice of .+ examination|recruitment (?:notice|notification)|(?:direct )?recruitment for|'
        r'notification for .*(?:post|recruitment)|advertisement for|filling up .+ post|'
        r'vacanc(?:y|ies)|selection posts? examination',
        lowered,
    ))


def parse_ssc(html, base_url):
    """Read SSC's public notice-board JSON and keep recruitment openings only."""
    try:
        payload = json.loads(html)
    except (TypeError, ValueError):
        return []
    items = []
    seen = set()
    for record in _walk_json(payload):
        headline = _pick(record, 'headline', 'title', 'noticeTitle', 'subject')
        if not headline or not _looks_like_initial_recruitment(headline):
            continue
        notice_url = _record_url(
            record,
            base_url,
            attachment_root='https://ssc.gov.in/api/attachment/uploads/masterData/NoticeBoards/',
        )
        if not notice_url or notice_url in seen:
            continue
        seen.add(notice_url)
        deadline_text = _pick(record, 'lastDate', 'closingDate', 'applicationEndDate', 'deadline')
        deadline = parse_date(deadline_text)
        issue_date = parse_date(_pick(record, 'createdAt', 'publishedAt', 'startDate', 'date'))
        items.append(JobItem(
            external_id=_pick(record, 'id', 'noticeId', 'examId') or notice_url,
            title=headline,
            organization='Staff Selection Commission (SSC)',
            official_notice_url=notice_url,
            location='India',
            issue_date=issue_date,
            deadline=deadline,
            application_url='https://ssc.gov.in/login',
            summary='Official SSC recruitment notice. Confirm post-wise qualifications, age limits, vacancies, fees and dates in the linked notice.',
            confidence=0.92 if deadline else 0.84,
            warnings=[] if deadline else ['The closing date must be confirmed in the official SSC notice.'],
        ))
    return items


def parse_rrb(html, base_url):
    """Read new Centralised Employment Notices from an official RRB board."""
    document = parse_html(html)
    items = []
    seen = set()
    for record in _table_records(document):
        text = clean(' '.join(record.get('_values', [])))
        if not re.search(r'\bCEN\s*\d{1,2}/20\d{2}\b', text, re.I):
            continue
        if not _looks_like_initial_recruitment(text):
            continue
        notice_url = _row_url(record, base_url)
        if not notice_url or notice_url in seen:
            continue
        seen.add(notice_url)
        cen = re.search(r'\bCEN\s*\d{1,2}/20\d{2}\b', text, re.I)
        title_match = re.search(
            r'(?:Employment Notice|Notice)\s*:\s*(.+?)(?:Application Link|Link\s*/|$)',
            text,
            re.I,
        )
        title = clean(title_match.group(1)) if title_match else f'{cen.group(0).upper()} Railway Recruitment'
        dates = _record_dates(record)
        issue_date = dates[0] if dates else None
        deadline = dates[-1] if len(dates) > 1 and dates[-1] != issue_date else None
        items.append(JobItem(
            external_id=cen.group(0).upper().replace(' ', ''),
            title=title[:500],
            organization='Railway Recruitment Board (RRB)',
            official_notice_url=notice_url,
            location='India',
            issue_date=issue_date,
            deadline=deadline,
            application_url=notice_url,
            summary='Official Railway Recruitment Board employment notice. Confirm the participating RRB, posts, eligibility, fee and dates in the notice.',
            confidence=0.92 if deadline else 0.84,
            warnings=[] if deadline else ['The closing date must be confirmed in the official RRB notice.'],
        ))
    return items


def parse_mha_ib(html, base_url):
    """Read current Intelligence Bureau vacancies published by MHA."""
    document = parse_html(html)
    items = []
    seen = set()
    for index, record in enumerate(_table_records(document), start=1):
        text = clean(' '.join(record.get('_values', [])))
        if not re.search(r'intelligence bureau|\bIB\b', text, re.I):
            continue
        notice_url = _row_url(record, base_url)
        if not notice_url or notice_url in seen:
            continue
        seen.add(notice_url)
        title = _first(record, ('keyword', 'title', 'vacancy', 'subject')) or text
        dates = _record_dates(record)
        issue_date = dates[0] if dates else None
        deadline = parse_date(_first(record, ('last date', 'closing date', 'deadline')))
        if deadline is None and re.search(r'last date|closing date|deadline', text, re.I) and dates:
            deadline = dates[-1]
        items.append(JobItem(
            external_id=f'mha-ib-{index}-{notice_url}',
            title=title[:500],
            organization='Intelligence Bureau / Ministry of Home Affairs',
            official_notice_url=notice_url,
            location='India',
            issue_date=issue_date,
            deadline=deadline,
            application_url=notice_url,
            summary='Official Intelligence Bureau or MHA vacancy circular. Confirm recruitment mode, eligibility and closing date in the linked document.',
            confidence=0.9 if deadline else 0.83,
            warnings=[] if deadline else ['The closing date must be confirmed in the official MHA notice.'],
        ))
    return items


class ContextLinkParser(HTMLParser):
    """Collect links with the latest visible heading at each heading level."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.headings = {}
        self._heading = None
        self._heading_text = []
        self._link = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag in {'h1', 'h2', 'h3', 'h4'}:
            self._heading = tag
            self._heading_text = []
        elif tag == 'a':
            context = ' — '.join(self.headings[key] for key in ('h1', 'h2', 'h3', 'h4') if self.headings.get(key))
            self._link = {'href': attributes.get('href', ''), 'text': [], 'context': context}

    def handle_data(self, data):
        if self._heading:
            self._heading_text.append(data)
        if self._link:
            self._link['text'].append(data)

    def handle_endtag(self, tag):
        if tag == self._heading:
            self.headings[tag] = clean(' '.join(self._heading_text))
            level = int(tag[1])
            for deeper in range(level + 1, 5):
                self.headings.pop(f'h{deeper}', None)
            self._heading = None
            self._heading_text = []
        elif tag == 'a' and self._link:
            self._link['text'] = clean(' '.join(self._link['text']))
            self.links.append(self._link)
            self._link = None


def parse_tgprb(html, base_url):
    """Read active recruitment notification links from the TGPRB homepage."""
    document = ContextLinkParser()
    document.feed(html)
    document.close()
    items = []
    seen = set()
    for index, link in enumerate(document.links, start=1):
        label = clean(link['text'])
        context = clean(link['context'])
        if not re.fullmatch(r'(?:recruitment\s+)?notification', label, re.I):
            continue
        if 'supplementary' in label.lower() or not context or 'recruitment' not in context.lower():
            continue
        notice_url = urljoin(base_url, link['href'])
        if not link['href'] or notice_url in seen:
            continue
        seen.add(notice_url)
        headings = [part.strip() for part in context.split(' — ') if part.strip()]
        specific = next((part for part in reversed(headings) if not re.fullmatch(r'.*recruitment\s*[—-]?\s*20\d{2}', part, re.I)), headings[-1])
        title = specific if 'recruitment' in specific.lower() else f'{specific} Recruitment'
        items.append(JobItem(
            external_id=f'tgprb-{index}-{notice_url}',
            title=title[:500],
            organization='Telangana Police Recruitment Board (TGPRB)',
            official_notice_url=notice_url,
            location='Telangana',
            application_url=notice_url,
            summary='Official Telangana Police recruitment notification. Confirm post codes, qualifications, age, fee, vacancies and dates in the linked notice.',
            confidence=0.84,
            warnings=['The closing date must be confirmed in the official TGPRB notification.'],
        ))
    return items


def parse_india_post_vacancies(html, base_url):
    """Read recent recruitment notices from India Post's official vacancy table."""
    document = parse_html(html)
    items = []
    seen = set()
    for index, record in enumerate(_table_records(document), start=1):
        title = _first(record, ('title', 'vacancy', 'recruitment', 'subject'))
        if not title:
            values = record.get('_values', [])
            title = values[1] if len(values) > 1 else None
        if not title or not _looks_like_initial_recruitment(title):
            continue
        issue_date = parse_date(_first(record, ('published date', 'publication date', 'date')))
        if issue_date is None:
            dates = _record_dates(record)
            issue_date = dates[-1] if dates else None
        # An undated row cannot be safely treated as a current opening.
        if issue_date is None:
            continue
        notice_url = _row_url(record, base_url)
        if not notice_url or notice_url in seen:
            continue
        seen.add(notice_url)
        items.append(JobItem(
            external_id=f'india-post-{issue_date.isoformat()}-{index}-{title[:80]}',
            title=title[:500],
            organization='Department of Posts (India Post)',
            official_notice_url=notice_url,
            location='India',
            issue_date=issue_date,
            application_url=notice_url,
            summary='Official India Post vacancy notice. Confirm post-wise eligibility, age, fee, vacancies, application method and closing date in the linked notice.',
            confidence=0.84,
            warnings=['The closing date must be confirmed in the official India Post vacancy notice.'],
        ))
    return items


def parse_india_post_gds(html, base_url):
    """Read the single active GDS engagement and its application dates."""
    text = _visible_text(html)
    title_match = re.search(
        r'(Gramin Dak Sevak\s*\(GDS\)\s*Online Engagement.*?20\d{2})',
        text,
        re.I,
    )
    application_section = re.search(
        r'Application Submission(.*?)(?:Edit\s*/?\s*Correction Window|Click Here|Important Notice|$)',
        text,
        re.I,
    )
    if not title_match or not application_section:
        return []
    application_dates = parse_all_dates(application_section.group(1))
    if len(application_dates) < 2:
        return []
    start_date, deadline = application_dates[0], application_dates[-1]
    if deadline < date.today():
        return []

    document = parse_html(html)
    notice_url = next(
        (urljoin(base_url, href) for href, label in document.links if href and re.search(r'notification|descriptive', label, re.I)),
        base_url,
    )
    application_url = next(
        (urljoin(base_url, href) for href, label in document.links if href and re.search(r'\b(?:register|apply)\b', label, re.I)),
        base_url,
    )
    title = clean(title_match.group(1)).rstrip(' -–—:')
    return [JobItem(
        external_id=re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-'),
        title=title[:500],
        organization='Department of Posts (India Post)',
        official_notice_url=notice_url,
        location='India',
        application_start_date=start_date,
        deadline=deadline,
        application_url=application_url,
        summary='Active official India Post Gramin Dak Sevak engagement. Confirm circle-wise vacancies, eligibility, fee, reservation rules and documents on the official portal.',
        confidence=0.96,
    )]


def parse_isro_opportunities(html, base_url):
    """Read currently open recruitment rows from ISRO's consolidated official table."""
    document = parse_html(html)
    items = []
    seen = set()
    today = date.today()
    for record in _table_records(document):
        title = _first(record, ('post', 'position', 'recruitment'))
        advert = _first(record, ('advertisement number', 'advertisement no', 'advt'))
        deadline = parse_date(_first(record, ('last date', 'closing date', 'deadline')))
        if not title or not advert or not deadline or deadline < today:
            continue
        notice_url = _row_url(record, base_url)
        if not notice_url or notice_url in seen:
            continue
        seen.add(notice_url)
        centre = _first(record, ('location', 'centre', 'center'))
        opening_date = parse_date(_first(record, ('opening date', 'start date')))
        items.append(JobItem(
            external_id=advert,
            title=title[:500],
            organization='Indian Space Research Organisation (ISRO)',
            official_notice_url=notice_url,
            location=centre or 'India',
            issue_date=opening_date,
            application_start_date=opening_date,
            deadline=deadline,
            application_url=notice_url,
            summary='Current opportunity listed by ISRO. Confirm the centre, qualifications, age, vacancies, fee and application instructions in the official notice.',
            confidence=0.95,
        ))
    return items


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
            confidence=0.9 if deadline else 0.84,
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
    SourceDefinition(
        'ssc',
        'Staff Selection Commission',
        'https://ssc.gov.in/api/general-website/portal/notice-boards?page=1&limit=100&contentType=notice-boards&key=createdAt&order=DESC&isAttachment=true&language=english&attributes=id%2Cheadline%2CexamId%2CcontentType%2CredirectUrl%2CstartDate%2CendDate%2Clanguage%2CcreatedAt',
        parse_ssc,
        allow_missing_deadline=True,
    ),
    SourceDefinition('rrb', 'Railway Recruitment Board', 'https://www.rrbcdg.gov.in/', parse_rrb, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('upsc', 'Union Public Service Commission', 'https://www.upsc.gov.in/recruitment/recruitment-advertisement', parse_upsc, allow_missing_deadline=True),
    SourceDefinition('mha_ib', 'Intelligence Bureau / Ministry of Home Affairs', 'https://www.mha.gov.in/en/notifications/vacancies?title=Intelligence%20Bureau', parse_mha_ib, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('tgprb', 'Telangana Police Recruitment Board', 'https://www.tgprb.in/', parse_tgprb, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('india_post_gds', 'India Post — GDS Online Engagement', 'https://www.indiapost.gov.in/gdsonlineengagement', parse_india_post_gds),
    SourceDefinition('india_post', 'Department of Posts — Vacancies', 'https://www.indiapost.gov.in/vacancies', parse_india_post_vacancies, allow_missing_deadline=True, missing_deadline_max_age_days=45),
    SourceDefinition('isro', 'Indian Space Research Organisation', 'https://www.isro.gov.in/ViewAllOpportunities.html', parse_isro_opportunities),
    SourceDefinition('ncs', 'National Career Service', 'https://www.ncs.gov.in/job-listing', parse_ncs),
)

SOURCE_BY_KEY = {source.key: source for source in SOURCE_DEFINITIONS}
