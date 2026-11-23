import re
from datetime import timedelta
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from .official_fetch import validate_official_url
from .sources import JobItem, SourceDefinition, _first, _looks_like_initial_recruitment, _row_url, _table_records, _visible_text, clean, parse_date, parse_explicit_deadline, parse_explicit_deadline_cutoff_time, parse_html, india_today

_EXCLUDED = (
    'result', 'results', 'admit card', 'call letter', 'answer key', 'interview schedule',
    'shortlisted', 'selected candidates', 'selection list', 'marks', 'score card',
    'information handout', 'scribe declaration', 'corrigendum', 'addendum',
    'cancellation', 'cancelled', 'document verification',
    'exam city', 'response sheet', 'notice regarding exam', 'final result',
)

_RECRUITMENT = re.compile(
    r'\b(recruitment|vacanc(?:y|ies)|current openings?|career opportunities?|'
    r'engagement of|invites? applications?|applications? invited|application for (?:the )?(?:post|position)|'
    r'inviting applications|apply online|advertisement|advt\.?|'
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
        today = india_today()
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
                deadline_cutoff_time=parse_explicit_deadline_cutoff_time(' '.join([title] + [label for _, label in application_candidates] + [label for _, label in notice_candidates])),
                deadline_timezone='Asia/Kolkata',
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
        today = india_today()

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
                deadline_cutoff_time=parse_explicit_deadline_cutoff_time(text),
                deadline_timezone='Asia/Kolkata',
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
        if deadline is not None and deadline < india_today():
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
            deadline_cutoff_time=parse_explicit_deadline_cutoff_time(' '.join(str(value) for value in record.values())),
            deadline_timezone='Asia/Kolkata',
            summary='Official KVS recruitment notice. Confirm post-specific eligibility, closing date and application instructions in the linked official notice.',
            confidence=0.95 if deadline else 0.9,
            warnings=[] if deadline else ['Closing date must be confirmed in the linked official KVS notice.'],
        ))
    return items
def parse_sebi(html, base_url):
    """Parse dated SEBI vacancy rows and discard archived/result-only notices."""
    records = list(_table_records(parse_html(html)))
    has_dated_titles = any(
        _first(record, ('date',)) and _first(record, ('title',))
        for record in records
    )
    if not has_dated_titles:
        raise ValueError('SEBI vacancies page did not contain its dated listing table.')

    today = india_today()
    oldest_issue_date = today - timedelta(days=365)
    items = []
    seen = set()
    for record in records:
        title = _first(record, ('title', 'subject', 'vacancy'))
        issue_date = parse_date(_first(record, ('date', 'published')))
        if not title or not issue_date:
            continue
        if issue_date < oldest_issue_date or not _RECRUITMENT.search(title):
            continue
        if any(term in title.lower() for term in _EXCLUDED):
            continue

        notice_url = _row_url(record, base_url)
        if not notice_url:
            continue
        validate_official_url(notice_url)
        identity = (title.casefold(), notice_url)
        if identity in seen:
            continue
        seen.add(identity)

        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:120]
        deadline = parse_explicit_deadline(title)
        items.append(JobItem(
            external_id=f'sebi-{issue_date.isoformat()}-{slug}',
            title=title[:500],
            organization='Securities and Exchange Board of India (SEBI)',
            official_notice_url=notice_url,
            location='India',
            issue_date=issue_date,
            deadline=deadline,
            deadline_timezone='Asia/Kolkata',
            summary='Official SEBI recruitment notice. Confirm stream, eligibility, vacancies, fee, dates and application instructions in the linked official notice.',
            confidence=0.96,
            warnings=[] if deadline else ['Confirm the application deadline in the official SEBI notice.'],
        ))

    return sorted(items, key=lambda item: (item.issue_date or today, item.title), reverse=True)


parse_ibps = _generic_official_parser(
    'Institute of Banking Personnel Selection (IBPS)',
    'Official IBPS recruitment process notice. Confirm participating organisations, eligibility, vacancies, fee and dates in the official notification.',
)
parse_drdo = _generic_official_parser(
    'Defence Research and Development Organisation (DRDO)',
    'Official DRDO vacancy notice. Confirm discipline, eligibility, vacancies, application deadline and instructions in the linked official notice.',
)


def parse_drdo_rac(html, base_url):
    text = _visible_text(html)
    if not re.search(r'Ongoing Recruitment Opportunities in DRDO', text, re.I):
        return []
    advertisement = re.search(
        r'Lateral Recruitment of Scientists\s+Advertisement\s*#\s*(\d+)',
        text,
        re.I,
    )
    if not advertisement:
        return []
    date_pattern = r'(\d{1,2}[ -]+[A-Za-z]{3,9}[,\s-]+20\d{2})'
    extended = re.search(
        rf'Extended Form Submission date\s*:\s*{date_pattern}',
        text,
        re.I,
    )
    closing = re.search(rf'Closing date\s*:\s*{date_pattern}', text, re.I)
    date_match = extended or closing
    if not date_match:
        return []
    deadline = parse_date(re.sub(r'[-]+', ' ', date_match.group(1)))
    if not deadline:
        return []
    number = advertisement.group(1)
    notice = re.search(
        rf'href\s*=\s*["\']([^"\']*advt_{re.escape(number)}\.pdf(?:\?[^"\']*)?)["\']',
        html,
        re.I,
    )
    notice_url = urljoin(base_url, notice.group(1)) if notice else base_url
    validate_official_url(notice_url)
    return [JobItem(
        external_id=f'drdo-rac-advt-{number}',
        title=f'DRDO-RAC Lateral Recruitment of Scientists (Advertisement {number})',
        organization='Defence Research and Development Organisation — Recruitment and Assessment Centre',
        official_notice_url=notice_url,
        location='India',
        deadline=deadline,
        summary='Official DRDO-RAC scientist recruitment notice. Verify the current application status and eligibility on the official source.',
        confidence=0.98,
    )]


PRIORITY_OFFICIAL_SOURCES = (
    SourceDefinition('rbi', 'Reserve Bank of India', 'https://opportunities.rbi.org.in/Scripts/Vacancies.aspx', parse_rbi, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('sbi', 'State Bank of India — Careers', 'https://sbi.bank.in/web/careers/current-openings1', parse_sbi, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('nvs', 'Navodaya Vidyalaya Samiti', 'https://navodaya.gov.in/nvs/en/Recruitment/', parse_nvs, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('sainik_schools', 'Sainik Schools Society', 'https://sainikschoolsociety.in/', parse_sainik, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('kvs', 'Kendriya Vidyalaya Sangathan', 'https://kvs.gov.in/en/interview-notice/', parse_kvs, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition(
        'sebi',
        'Securities and Exchange Board of India',
        'https://www.sebi.gov.in/sebiweb/about/AboutAction.do?doVacancies=yes',
        parse_sebi,
    ),
    SourceDefinition('ibps', 'Institute of Banking Personnel Selection', 'https://www.ibps.in/', parse_ibps, allow_missing_deadline=True, missing_deadline_max_age_days=45),
    SourceDefinition('drdo_rac', 'Defence Research and Development Organisation — Recruitment and Assessment Centre', 'https://rac.gov.in/index.php?lang=en&id=0', parse_drdo_rac),
)
