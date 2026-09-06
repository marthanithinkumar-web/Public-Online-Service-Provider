"""Conservative enrichment of recruitment notices from official documents.

Only facts explicitly found in the allow-listed official notice are copied into
public job records.  Missing or ambiguous facts stay empty instead of being
invented.  PDF extraction is bounded so the daily refresh cannot download
arbitrary/oversized documents.
"""
from io import BytesIO
import re
from urllib.parse import urlparse

import requests
from pypdf import PdfReader

from .official_fetch import ALLOWED_HOSTS, BROWSER_HEADERS, validate_official_url

MAX_NOTICE_BYTES = 8 * 1024 * 1024


def _clean(value):
    return re.sub(r'\s+', ' ', str(value or '')).strip()


def _download_pdf(url, session=None):
    validate_official_url(url)
    client = session or requests.Session()
    response = client.get(url, timeout=(10, 35), allow_redirects=True, headers=BROWSER_HEADERS, stream=True)
    response.raise_for_status()
    validate_official_url(response.url)
    content_type = (response.headers.get('Content-Type') or '').lower()
    if 'pdf' not in content_type and not urlparse(response.url).path.lower().endswith('.pdf'):
        return None
    chunks, size = [], 0
    for chunk in response.iter_content(65536):
        if not chunk:
            continue
        size += len(chunk)
        if size > MAX_NOTICE_BYTES:
            return None
        chunks.append(chunk)
    return b''.join(chunks)


def _pdf_text(data):
    if not data:
        return ''
    try:
        reader = PdfReader(BytesIO(data), strict=False)
        # Recruitment facts are normally in the opening/eligibility/fee pages;
        # cap work while still covering long SSC/RRB notices.
        return _clean(' '.join((page.extract_text() or '') for page in reader.pages[:45]))
    except Exception:
        return ''


def _first(text, patterns, max_len=500):
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            value = _clean(match.group(1)).strip(' :-–—.;,')
            if 1 < len(value) <= max_len:
                return value
    return None


def _qualification(text):
    value = _first(text, (
        r'(?:essential educational qualifications?|educational qualifications?|minimum qualification)\s*(?:as on [^:]{0,40})?[:\-]?\s*(.{12,420}?)(?=\s+(?:age limit|age-limit|age as on|nationality|vacanc|pay scale|scheme of examination|note\s*[:\-]|\d+\.\s+[A-Z]))',
        r'(degree in [A-Za-z][^.;]{8,260}(?:recognized|recognised)[^.;]{0,120})',
        r'((?:three[- ]year|3[- ]year) diploma in [A-Za-z][^.;]{8,260})',
    ))
    return value


def _age(text):
    return _first(text, (
        r'(?:age limit|age-limit|age as on[^:]{0,35})\s*[:\-]?\s*((?:between\s+)?\d{2}\s*(?:-|–|to)\s*\d{2}\s*years?[^.;]{0,120})',
        r'(?:age limit|age-limit)\s*[:\-]?\s*(up to\s+\d{2}\s*years?[^.;]{0,120})',
    ), 220)


def _fee(text):
    return _first(text, (
        r'(?:application fee|examination fee|fee payable)\s*[:\-]?\s*(.{3,260}?)(?=\s+(?:women|female|sc\b|st\b|persons? with|pwbd|payment|how to apply|\d+\.\s+[A-Z]))',
        r'(fee payable\s*:?\s*₹?\s*\d+[^.;]{0,180})',
    ), 300)


def _salary(text):
    return _first(text, (
        r'((?:pay level|level)[- ]?\s*\d+\s*\(?\s*(?:₹|rs\.?)[^.;]{3,100})',
        r'((?:₹|rs\.?)\s*[\d,]+\s*(?:-|–|to)\s*(?:₹|rs\.?)?\s*[\d,]+[^.;]{0,80})',
    ), 180)


def _vacancies(text):
    value = _first(text, (
        r'(?:total|approximately|tentative(?:ly)?)\s+(?:number of\s+)?vacanc(?:y|ies)\s*(?:are|is|:)\s*([\d,]+)',
        r'vacanc(?:y|ies)\s*[:\-]\s*([\d,]+)',
    ), 30)
    return f'{value} vacancies' if value and re.fullmatch(r'[\d,]+', value) else value


def enrich_job_item(item, session=None):
    """Fill blank JobItem facts from its official PDF; never overwrite source facts."""
    url = str(getattr(item, 'official_notice_url', '') or '')
    if not url or not urlparse(url).path.lower().endswith('.pdf'):
        return item
    try:
        text = _pdf_text(_download_pdf(url, session=session))
    except (requests.RequestException, ValueError):
        return item
    if len(text) < 100:
        return item
    if not getattr(item, 'qualification', None):
        item.qualification = _qualification(text)
    if not getattr(item, 'age_limit', None):
        item.age_limit = _age(text)
    if not getattr(item, 'application_fee', None):
        item.application_fee = _fee(text)
    if not getattr(item, 'vacancies', None):
        item.vacancies = _vacancies(text)
    if not getattr(item, 'salary', None):
        item.salary = _salary(text)
    extracted = [
        ('Qualification', item.qualification), ('Age', item.age_limit),
        ('Fee', item.application_fee), ('Vacancies', item.vacancies), ('Pay', item.salary),
    ]
    facts = [f'{label}: {value}' for label, value in extracted if value]
    if facts and (not item.summary or item.summary.startswith('Official ')):
        item.summary = 'Verified from the official notification. ' + ' · '.join(facts)
    return item
