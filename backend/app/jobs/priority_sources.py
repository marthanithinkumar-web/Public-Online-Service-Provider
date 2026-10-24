import re
from html.parser import HTMLParser
from datetime import date
from urllib.parse import urljoin, urlparse

from .official_fetch import validate_official_url
from .sources import JobItem, SourceDefinition, _first, _looks_like_initial_recruitment, _row_url, _table_records, clean, parse_all_dates, parse_date, parse_explicit_deadline, parse_html

_EXCLUDED = (
    'result', 'results', 'admit card', 'call letter', 'answer key', 'interview schedule',
    'shortlisted', 'selected candidates', 'selection list', 'marks', 'score card',
    'corrigendum', 'addendum', 'cancellation', 'cancelled', 'document verification',
    'exam city', 'response sheet', 'notice regarding exam', 'final result',
)

_RECRUITMENT = re.compile(
    r'\b(recruitment|vacanc(?:y|ies)|current openings?|career opportunities?|'
    r'engagement of|invites? applications?|applications? invited|apply online|advertisement|advt\.?|'
    r'probationary officer|junior associate|specialist cadre|officer grade|'
    r'assistant manager|manager grade|teaching posts?|non[- ]teaching posts?|'
    r'faculty posts?|staff recruitment)\b',
    re.I,
)


class _GroupedOfficialListingsParser(HTMLParser):
    """Pair recruitment heading paragraphs with links in the following list."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.paragraphs = []
        self.sections = []
        self.paragraph = None
        self.list_items = None
        self.list_depth = 0
        self.list_item = None
        self.anchor = None
        self.all_links = []

    @staticmethod
    def _extra_urls(attrs):
        urls = []
        for key in ('data-href', 'data-url', 'data-file-url', 'data-download-url', 'data-document-url', 'data-resource-url'):
            value = clean(attrs.get(key, ''))
            if value and value != '#' and not value.lower().startswith('javascript:'):
                urls.append(value)
        onclick = str(attrs.get('onclick') or '')
        for value in re.findall(r'''[\"']([^\"']+)[\"']''', onclick):
            value = clean(value)
            if value and (value.startswith(('https://', 'http://', '/', '../')) or re.search(r'\.pdf(?:/|$|\?)', value, re.I)) and value != '#':
                urls.append(value)
        return list(dict.fromkeys(urls))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {'p', 'h2', 'h3', 'h4'}:
            self.paragraph = []
        elif tag == 'ul':
            if self.list_depth == 0:
                self.list_items = []
            self.list_depth += 1
        elif tag == 'li' and self.list_depth > 0:
            self.list_item = {'text': [], 'links': []}
        elif tag == 'a':
            self.anchor = {
                'href': attrs.get('href', ''),
                'text': [],
                'context': list(self.paragraphs),
                'extra_urls': self._extra_urls(attrs),
            }
        # Keep non-anchor CMS download controls attached to their current row.
        # Anchor data-* and onclick URLs are added with the anchor's label below,
        # even when the control sits just outside the list item.
        if self.list_item is not None and tag != 'a':
            for url in self._extra_urls(attrs):
                self.list_item['links'].append((url, ''))

    def handle_data(self, data):
        if self.paragraph is not None:
            self.paragraph.append(data)
        if self.list_item is not None:
            self.list_item['text'].append(data)
        if self.anchor is not None:
            self.anchor['text'].append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.anchor is not None:
            label = clean(' '.join(self.anchor['text']))
            context = self.anchor.get('context', [])
            if self.anchor.get('href'):
                self.all_links.append((self.anchor['href'], label, context))
                if self.list_item is not None:
                    self.list_item['links'].append((self.anchor['href'], label))
            for extra_url in self.anchor.get('extra_urls', []):
                self.all_links.append((extra_url, label, context))
                if self.list_item is not None and (extra_url, label) not in self.list_item['links']:
                    self.list_item['links'].append((extra_url, label))
            self.anchor = None
        elif tag == 'li' and self.list_item is not None:
            self.list_item['text'] = clean(' '.join(self.list_item['text']))
            if self.list_items is not None:
                self.list_items.append(self.list_item)
            self.list_item = None
        elif tag in {'p', 'h2', 'h3', 'h4'} and self.paragraph is not None:
            paragraph = clean(' '.join(self.paragraph))
            if paragraph and self.list_depth == 0:
                self.paragraphs.append(paragraph)
            self.paragraph = None
        elif tag == 'ul' and self.list_depth:
            self.list_depth -= 1
            if self.list_depth == 0:
                if self.list_items:
                    self.sections.append({
                        'context': list(self.paragraphs),
                        'items': list(self.list_items),
                    })
                self.list_items = None
                self.paragraphs = []


def _grouped_official_parser(organization, summary, fallback=None):
    def parse(html, base_url):
        document = _GroupedOfficialListingsParser()
        document.feed(html)
        document.close()
        items = []
        today = date.today()
        recognized_section = False

        for index, section in enumerate(document.sections, start=1):
            context = section['context']
            title = next((
                text for text in reversed(context)
                if _RECRUITMENT.search(text)
                and not re.search(r'\badvertisement\s*(?:no|number)\s*:', text, re.I)
                and len(text) >= 12
            ), None)
            if not title:
                continue

            links = [
                (href, label or row.get('text', ''))
                for row in section['items'] for href, label in row.get('links', [])
            ]
            # Some SBI CMS components place the advertisement anchors outside the
            # <li> node even though their text appears with the group. Retain all
            # anchors carrying this group's surrounding title/ad-number context.
            for href, label, link_context in document.all_links:
                if link_context == context and href and (href, label) not in links:
                    links.append((href, label))
            application_candidates = [
                (href, label) for href, label in links
                if re.search(r'\b(apply online|apply now|online application|online registration|registration portal)\b', label, re.I)
            ]
            notice_candidates = [
                (href, label) for href, label in links
                if re.search(r'\b(download\s+advertisement|advertisement|download\s+notification|notification|official\s+notice|notice)\b', label, re.I)
                and not any(term in label.lower() for term in _EXCLUDED)
            ]
            auxiliary_pdf = re.compile(
                r'biodata|bio.?data|ctc|undertaking|guideline|scribe|result|'
                r'answer.?key|admit.?card|hindi|faq|format|call.?letter|'
                r'selection|syllabus|handbook|brochure',
                re.I,
            )
            pdf_candidates = [
                (href, label) for href, label in links
                if re.search(r'\.pdf(?:/|$)', urlparse(urljoin(base_url, href)).path, re.I)
                and not auxiliary_pdf.search(f'{label} {href}')
            ]
            if not application_candidates and not notice_candidates and not pdf_candidates:
                continue
            recognized_section = True
            if not _RECRUITMENT.search(title) or any(term in title.lower() for term in _EXCLUDED):
                continue

            def allowed_candidate(candidates):
                for href, label in candidates:
                    raw_href = str(href or '').strip()
                    if not raw_href or raw_href == '#' or raw_href.startswith('#') or raw_href.lower().startswith(('javascript:', 'data:')):
                        continue
                    absolute = urljoin(base_url, raw_href)
                    if absolute.split('#', 1)[0].rstrip('/') == base_url.split('#', 1)[0].rstrip('/') and not re.search(r'\.pdf(?:/|$|\?)', absolute, re.I):
                        continue
                    try:
                        validate_official_url(absolute)
                    except ValueError:
                        continue
                    return absolute
                return None

            application_url = allowed_candidate(application_candidates)
            official_notice_url = allowed_candidate(pdf_candidates) or allowed_candidate(notice_candidates) or base_url
            deadline = parse_explicit_deadline(title)
            if deadline is None:
                for _, label in application_candidates:
                    deadline = parse_explicit_deadline(label)
                    if deadline:
                        break
            if deadline is not None and deadline < today:
                continue

            ad_number = next((
                re.sub(r'\s+', '', re.sub(r'^.*?advertisement\s*(?:no|number)\s*:\s*', '', text, flags=re.I))
                for text in reversed(context)
                if re.search(r'\badvertisement\s*(?:no|number)\s*:', text, re.I)
            ), '')
            items.append(JobItem(
                external_id=f'{organization.lower().replace(" ", "-")}-{ad_number or index}-{title[:80]}',
                title=title[:500],
                organization=organization,
                official_notice_url=official_notice_url,
                location='India',
                deadline=deadline,
                application_url=application_url,
                summary=summary,
                confidence=0.96,
                warnings=[] if deadline else ['Confirm the closing date in the official recruitment notice.'],
            ))

        if recognized_section or fallback is None:
            return items
        return fallback(html, base_url)

    return parse


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
            try:
                validate_official_url(notice_url)
            except ValueError:
                continue
            identity = (text.lower(), notice_url)
            if identity in seen:
                continue
            seen.add(identity)
            deadline = parse_explicit_deadline(text)
            if deadline and deadline < today:
                continue
            is_application_link = bool(re.search(r'\b(apply online|apply now|online application|registration portal)\b', text, re.I))
            application_url = notice_url if is_application_link else None
            items.append(JobItem(
                external_id=f'{organization.lower().replace(" ", "-")}-{index}-{text[:80]}',
                title=text[:500],
                organization=organization,
                official_notice_url=base_url if is_application_link else notice_url,
                location='India',
                deadline=deadline,
                application_url=application_url,
                summary=summary,
                confidence=0.92 if deadline else 0.84,
                warnings=(['notice_is_listing_page'] if is_application_link else []) + ([] if deadline else ['Confirm the closing date and post-specific eligibility in the official recruitment notice.']),
            ))
        return items

    return parse


parse_rbi = _generic_official_parser(
    'Reserve Bank of India (RBI)',
    'Official RBI recruitment opportunity. Confirm eligibility, vacancies, fee, dates and application instructions on the RBI opportunities portal.',
)
parse_sbi = _grouped_official_parser(
    'State Bank of India (SBI)',
    'Official SBI recruitment opening. Confirm cadre, eligibility, vacancies, fee, dates and application instructions on SBI Careers.',
    fallback=_generic_official_parser(
        'State Bank of India (SBI)',
        'Official SBI recruitment opening. Confirm cadre, eligibility, vacancies, fee, dates and application instructions on SBI Careers.',
    ),
)
parse_nvs = _generic_official_parser(
    'Navodaya Vidyalaya Samiti (NVS)',
    'Official NVS recruitment notice. Confirm teaching/non-teaching post details, eligibility, vacancies, fee and dates in the official notice.',
)
parse_sainik = _generic_official_parser(
    'Sainik Schools Society',
    'Official Sainik Schools recruitment notice. Confirm school/post-specific eligibility, employment terms and closing date in the official notice.',
)
def parse_kvs(html, base_url):
    """Read KVS recruitment rows and preserve their direct official PDF notices."""
    document = parse_html(html)
    items = []
    seen = set()
    for index, record in enumerate(_table_records(document), start=1):
        title = _first(record, ('name', 'title', 'subject', 'document'))
        if not title or not _looks_like_initial_recruitment(title):
            continue
        notice_url = _row_url(record, base_url)
        if not notice_url or notice_url in seen:
            continue
        try:
            validate_official_url(notice_url)
        except ValueError:
            continue
        seen.add(notice_url)
        published_text = _first(record, ('published on', 'published date', 'publication date', 'date'))
        issue_date = parse_date(published_text)
        deadline = parse_explicit_deadline(title)
        if deadline is not None and deadline < date.today():
            continue
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:72]
        items.append(JobItem(
            external_id=f'kvs-{slug or index}',
            title=title[:500],
            organization='Kendriya Vidyalaya Sangathan (KVS)',
            official_notice_url=notice_url,
            location='India',
            issue_date=issue_date,
            deadline=deadline,
            summary='Official KVS recruitment notice. Confirm post-specific eligibility, closing date and application instructions in the linked official notice.',
            confidence=0.95 if deadline else 0.9,
            warnings=[] if deadline else ['Closing date must be confirmed in the linked official KVS notice.'],
        ))
    return items
parse_sebi = _generic_official_parser(
    'Securities and Exchange Board of India (SEBI)',
    'Official SEBI recruitment opportunity. Confirm stream, eligibility, vacancies, fee, dates and application instructions in the official notice.',
)
parse_ibps = _generic_official_parser(
    'Institute of Banking Personnel Selection (IBPS)',
    'Official IBPS recruitment process notice. Confirm participating organisations, eligibility, vacancies, fee and dates in the official notification.',
)
parse_drdo = _generic_official_parser(
    'Defence Research and Development Organisation (DRDO)',
    'Official DRDO vacancy notice. Confirm discipline, eligibility, vacancies, application deadline and instructions in the linked official notice.',
)


PRIORITY_OFFICIAL_SOURCES = (
    SourceDefinition('rbi', 'Reserve Bank of India', 'https://opportunities.rbi.org.in/Scripts/Vacancies.aspx', parse_rbi, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('sbi', 'State Bank of India — Careers', 'https://sbi.bank.in/web/careers/current-openings', parse_sbi, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('nvs', 'Navodaya Vidyalaya Samiti', 'https://navodaya.gov.in/nvs/en/Recruitment/', parse_nvs, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('sainik_schools', 'Sainik Schools Society', 'https://sainikschoolsociety.in/', parse_sainik, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('kvs', 'Kendriya Vidyalaya Sangathan', 'https://kvs.gov.in/en/interview-notice/', parse_kvs, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('sebi', 'Securities and Exchange Board of India', 'https://www.sebi.gov.in/sebiweb/other/careerdetail.jsp?careerId=1', parse_sebi, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('ibps', 'Institute of Banking Personnel Selection', 'https://www.ibps.in/', parse_ibps, allow_missing_deadline=True, missing_deadline_max_age_days=45),
    SourceDefinition('drdo_rac', 'Defence Research and Development Organisation (DRDO) — Vacancies', 'https://drdo.gov.in/drdo/offerings/vacancies', parse_drdo, allow_missing_deadline=True, missing_deadline_max_age_days=60),
)
