"""Official private-employer career sources for the verified jobs feed."""

import html as html_lib
import re
from html.parser import HTMLParser
from urllib.parse import unquote, urljoin, urlparse

from .sources import JobItem, SourceDefinition, clean


class _CareerLinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self._link = None

    def handle_starttag(self, tag, attrs):
        if tag != 'a':
            return
        attributes = dict(attrs)
        self._link = {'href': attributes.get('href', ''), 'text': []}

    def handle_data(self, data):
        if self._link is not None:
            self._link['text'].append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self._link is not None:
            self.links.append((self._link['href'], clean(' '.join(self._link['text']))))
            self._link = None


def _source_profile(base_url):
    host = (urlparse(base_url).hostname or '').lower()
    if host.endswith('careers.wipro.com'):
        return 'Wipro', re.compile(r'/job/', re.I)
    if host.endswith('digitalcareers.infosys.com'):
        return 'Infosys', re.compile(r'jobdetails|/job/', re.I)
    if host.endswith('accenture.com'):
        return 'Accenture', re.compile(r'(?:^|/)jobdetails\?id=|/careers/jobdetails\?id=', re.I)
    return None, None


def _title_from_job_url(job_url):
    path = unquote(urlparse(job_url).path)
    match = re.search(r'/job/([^/]+)/', path, re.I)
    if not match:
        return ''
    parts = [part for part in match.group(1).split('-') if part]
    if len(parts) >= 3 and parts[-1].isdigit():
        parts = parts[:-1]
    if parts and parts[-1].upper() in {'IND', 'USA', 'GBR', 'CAN', 'AUS'}:
        parts = parts[:-1]
    if len(parts) >= 2 and parts[0].lower() in {
        'hyderabad', 'bengaluru', 'bangalore', 'chennai', 'pune', 'gurugram',
        'gurgaon', 'noida', 'kolkata', 'mumbai', 'coimbatore', 'bhubaneswar',
    }:
        parts = parts[1:]
    return clean(' '.join(parts))


def _raw_job_links(document, href_pattern):
    raw = html_lib.unescape(str(document or '')).replace('\\/', '/')
    candidates = re.findall(
        r'https://[^\s"\'<>]+|/(?:[^\s"\'<>]*/)?job/[^\s"\'<>]+',
        raw,
        flags=re.I,
    )
    return [(candidate.rstrip('),.;]'), '') for candidate in candidates if href_pattern.search(candidate)]


def parse_private_careers(document, base_url):
    """Extract individual active-role links from an approved employer page or sitemap."""
    organization, href_pattern = _source_profile(base_url)
    if not organization or href_pattern is None:
        return []

    parser = _CareerLinkParser()
    parser.feed(str(document or ''))
    parser.close()

    items = []
    seen = set()
    generic_labels = {
        'search jobs', 'search job', 'view jobs', 'view job', 'apply', 'apply now',
        'learn more', 'read more', 'careers', 'career opportunities', 'open positions',
    }
    links = list(parser.links)
    if organization == 'Wipro':
        links.extend(_raw_job_links(document, href_pattern))

    for href, label in links:
        href = clean(href)
        title = clean(label)
        if not href or not href_pattern.search(href):
            continue
        job_url = urljoin(base_url, href)
        if not job_url.startswith('https://') or job_url in seen:
            continue
        if not title or title.lower() in generic_labels:
            title = _title_from_job_url(job_url)
        if len(title) < 4:
            continue
        seen.add(job_url)
        identifier_match = re.search(r'(?:id=|/job/)([A-Za-z0-9_-]{4,})', job_url, re.I)
        identifier = identifier_match.group(1) if identifier_match else job_url
        items.append(JobItem(
            external_id=f'{organization.lower()}-{identifier}',
            title=title[:500],
            organization=organization,
            official_notice_url=job_url,
            job_type='private',
            location='India',
            application_url=job_url,
            summary=f'Current role listed on the official {organization} careers website. Confirm location, experience, qualifications and application requirements on the employer page.',
            confidence=0.88,
            warnings=['Private employer listings may close without a separately published deadline.'],
        ))
    return items


PRIVATE_SOURCES = (
    SourceDefinition(
        'wipro_careers',
        'Wipro Careers',
        'https://careers.wipro.com/sitemap.xml',
        parse_private_careers,
        allow_missing_deadline=True,
    ),
    SourceDefinition(
        'infosys_careers',
        'Infosys Careers',
        'https://digitalcareers.infosys.com/infosys/global-careers?location=India',
        parse_private_careers,
        allow_missing_deadline=True,
    ),
    SourceDefinition(
        'accenture_careers',
        'Accenture Careers',
        'https://www.accenture.com/in-en/careers/jobsearch',
        parse_private_careers,
        allow_missing_deadline=True,
    ),
)
