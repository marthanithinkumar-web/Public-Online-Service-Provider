"""Extract scheme-specific facts already published on allow-listed scholarship pages."""
import re
from collections import defaultdict

import requests

from .discovery import OFFICIAL_HOSTS, USER_AGENT, html_lines, is_official_url

_GENERIC = re.compile(r'apply only if|review the current|official provider|current eligibility criteria', re.I)
_FACT = re.compile(r'eligib|income|family income|class\s|course|degree|diploma|student|category|sc\b|st\b|obc\b|minority|disabil|domicile|resident|marks|percentage|documents?|certificate|award|amount|₹|rs\.?\s*\d', re.I)


def _compact(value): return re.sub(r'\s+', ' ', str(value or '')).strip()


def _source_text(url, session=None):
    if not is_official_url(url): return ''
    client=session or requests.Session()
    response=client.get(url,timeout=(10,30),headers={'User-Agent':USER_AGENT},allow_redirects=True)
    response.raise_for_status()
    if not is_official_url(response.url): return ''
    return '\n'.join(html_lines(response.text))[:1_500_000]


def _scheme_context(text,title):
    if not text or not title:return ''
    # Match a distinctive normalized prefix so punctuation changes on portals do
    # not prevent enrichment, while keeping a tight window to avoid mixing schemes.
    words=[re.escape(x) for x in re.findall(r'[A-Za-z0-9]+',title)[:8]]
    if len(words)<2:return ''
    match=re.search(r'\s+'.join(words),text,re.I)
    if not match:return ''
    start=max(0,match.start()-500);end=min(len(text),match.end()+2200)
    return text[start:end]


def _facts(context):
    lines=[_compact(x) for x in context.splitlines() if _compact(x)]
    selected=[]
    for line in lines:
        if _FACT.search(line) and 8<=len(line)<=420 and line not in selected:
            selected.append(line)
        if len(selected)>=8:break
    return selected


def enrich_scholarships(items,session=None):
    """Add only source-visible eligibility facts; leave unavailable facts explicit."""
    grouped=defaultdict(list)
    for item in items:
        if isinstance(item,dict) and item.get('source_type')=='official' and is_official_url(item.get('source_url')):
            grouped[item['source_url']].append(item)
    for url,group in grouped.items():
        try:text=_source_text(url,session=session)
        except requests.RequestException:continue
        for item in group:
            existing=_compact(item.get('eligibility'))
            facts=_facts(_scheme_context(text,_compact(item.get('title'))))
            if facts:
                item['eligibility']='; '.join(facts)
                item['eligibility_source']='official_source_page'
            elif not existing or _GENERIC.search(existing):
                item['eligibility']='Detailed scheme conditions are not exposed in structured text by this source listing. Open the linked official scheme details before applying.'
                item['eligibility_source']='official_source_unstructured'
    return items
