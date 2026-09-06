"""Extract scheme-specific facts already published on allow-listed scholarship pages."""
import re
from collections import defaultdict

import requests

from .discovery import USER_AGENT, html_lines, is_official_url

_GENERIC = re.compile(r'apply only if|review the current|official provider|current eligibility criteria|detailed scheme conditions', re.I)
_FACT = re.compile(r'eligib|income|family income|class\s|course|degree|diploma|category|sc\b|st\b|obc\b|minority|disabil|domicile|resident|marks|percentage|documents?|certificate|award|amount|₹|rs\.?\s*\d', re.I)
_DEADLINE_ONLY = re.compile(r'^student application\s+(?:open|opened|not yet opened|open till|open until|open till \(for renewal\))', re.I)


def _compact(value):
    return re.sub(r'\s+', ' ', str(value or '')).strip()


def _tokens(value):
    return [token.casefold() for token in re.findall(r'[A-Za-z0-9]+', _compact(value))]


def _source_text(url, session=None):
    if not is_official_url(url):
        return ''
    client = session or requests.Session()
    response = client.get(url, timeout=(10, 30), headers={'User-Agent': USER_AGENT}, allow_redirects=True)
    response.raise_for_status()
    if not is_official_url(response.url):
        return ''
    return '\n'.join(html_lines(response.text))[:1_500_000]


def _looks_like_title(line, title):
    line_tokens = _tokens(line)
    title_tokens = _tokens(title)
    if len(title_tokens) < 2:
        return False
    prefix = title_tokens[: min(7, len(title_tokens))]
    joined = ' '.join(line_tokens)
    return ' '.join(prefix) in joined


def _scheme_context(text, title, other_titles=()):
    """Return only the current scheme's block, stopping before the next scheme.

    Listing pages such as NSP place many scholarship names next to one another.
    A broad character window can therefore attach a neighbouring scheme's
    eligibility to the wrong scholarship. This line-bounded extraction refuses
    to cross a recognised title boundary.
    """
    if not text or not title:
        return ''
    lines = [_compact(line) for line in text.splitlines() if _compact(line)]
    start = next((index for index, line in enumerate(lines) if _looks_like_title(line, title)), None)
    if start is None:
        return ''

    selected = [lines[start]]
    for line in lines[start + 1 : start + 18]:
        if any(_looks_like_title(line, other) for other in other_titles if other and other != title):
            break
        selected.append(line)
        if len(selected) >= 10:
            break
    return '\n'.join(selected)


def _facts(context, title):
    lines = [_compact(x) for x in context.splitlines() if _compact(x)]
    selected = []
    for line in lines:
        if _looks_like_title(line, title):
            continue
        if _DEADLINE_ONLY.search(line):
            continue
        if _FACT.search(line) and 8 <= len(line) <= 420 and line not in selected:
            selected.append(line)
        if len(selected) >= 8:
            break
    return selected


def enrich_scholarships(items, session=None):
    """Add only scheme-specific source-visible facts; never mix adjacent schemes."""
    grouped = defaultdict(list)
    for item in items:
        if isinstance(item, dict) and item.get('source_type') == 'official' and is_official_url(item.get('source_url')):
            grouped[item['source_url']].append(item)

    for url, group in grouped.items():
        try:
            text = _source_text(url, session=session)
        except requests.RequestException:
            continue
        titles = [_compact(item.get('title')) for item in group]
        for item in group:
            title = _compact(item.get('title'))
            existing = _compact(item.get('eligibility'))
            context = _scheme_context(text, title, titles)
            facts = _facts(context, title)
            if facts:
                item['eligibility'] = '; '.join(facts)
                item['eligibility_source'] = 'official_source_page'
            elif not existing or _GENERIC.search(existing) or item.get('source_key') == 'nsp':
                item['eligibility'] = 'Detailed scheme conditions are not exposed in structured text by this official listing. Open the linked official scheme details before applying.'
                item['eligibility_source'] = 'official_source_unstructured'
    return items
