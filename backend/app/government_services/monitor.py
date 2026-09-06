import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from .sources import SERVICE_WORDS, SOURCES

USER_AGENT = 'Public Online Service Provider government-service monitor/1.0'
MAX_LINKS_PER_SOURCE = 120
CATALOG_PATH = Path(__file__).with_name('verified_catalog.json')


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self._href = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'a':
            self._href = dict(attrs).get('href')
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == 'a' and self._href is not None:
            text = ' '.join(''.join(self._text).split())
            self.links.append((text, self._href))
            self._href = None
            self._text = []


def _load_verified_names():
    data = json.loads(CATALOG_PATH.read_text(encoding='utf-8'))
    if data.get('schema_version') != 1 or not isinstance(data.get('services'), list):
        raise ValueError('Invalid verified government-service manifest.')
    return data, {str(item.get('name') or '').strip().lower() for item in data['services']}


def _fetch(url):
    request = Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'text/html,application/xhtml+xml'})
    with urlopen(request, timeout=30) as response:
        body = response.read(2_000_000)
        content_type = response.headers.get('Content-Type', '')
        final_url = response.geturl()
    return body, content_type, final_url


def _service_like(text):
    lowered = text.lower()
    return len(lowered) >= 4 and any(word in lowered for word in SERVICE_WORDS)


def _normalise_text(value):
    return re.sub(r'\s+', ' ', value or '').strip()[:240]


def _same_official_host(source_url, candidate_url):
    source_host = urlparse(source_url).hostname or ''
    candidate_host = urlparse(candidate_url).hostname or ''
    if not candidate_host:
        return True
    source_parts = source_host.lower().split('.')
    candidate_parts = candidate_host.lower().split('.')
    return source_host == candidate_host or candidate_parts[-2:] == source_parts[-2:]


def scan_source(source):
    body, content_type, final_url = _fetch(source['url'])
    digest = hashlib.sha256(body).hexdigest()
    result = {
        'key': source['key'],
        'name': source['name'],
        'url': source['url'],
        'final_url': final_url,
        'sha256': digest,
        'content_type': content_type,
        'candidates': [],
        'ok': True,
    }
    if 'html' not in content_type.lower():
        return result

    parser = LinkParser()
    parser.feed(body.decode('utf-8', errors='ignore'))
    seen = set()
    for text, href in parser.links:
        label = _normalise_text(text)
        if not label or not _service_like(label):
            continue
        absolute = urljoin(final_url, href)
        if not absolute.startswith('https://') or not _same_official_host(final_url, absolute):
            continue
        key = (label.lower(), absolute.split('#', 1)[0])
        if key in seen:
            continue
        seen.add(key)
        result['candidates'].append({'title': label, 'url': key[1]})
        if len(result['candidates']) >= MAX_LINKS_PER_SOURCE:
            break
    return result


def build_snapshot():
    verified, verified_names = _load_verified_names()
    sources = []
    failures = []
    discovered = []

    for source in SOURCES:
        try:
            item = scan_source(source)
        except Exception as exc:
            item = {
                'key': source['key'], 'name': source['name'], 'url': source['url'],
                'ok': False, 'error': type(exc).__name__, 'candidates': [],
            }
            failures.append(source['key'])
        sources.append(item)
        for candidate in item.get('candidates', []):
            title = candidate['title']
            if title.lower() not in verified_names:
                discovered.append({
                    'source_key': source['key'],
                    'source_name': source['name'],
                    'title': title,
                    'url': candidate['url'],
                })

    return {
        'schema_version': 1,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'policy': 'Candidates are discovery signals only. They must be verified from the responsible first-party government source before promotion to the live catalogue.',
        'verified_catalog_count': len(verified['services']),
        'source_count': len(SOURCES),
        'source_failures': failures,
        'sources': sources,
        'discovered_candidates': discovered[:500],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--allow-failures', type=int, default=6)
    args = parser.parse_args()
    snapshot = build_snapshot()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f"Scanned {snapshot['source_count']} official source(s); {len(snapshot['discovered_candidates'])} candidate link(s); failures={len(snapshot['source_failures'])}.")
    if len(snapshot['source_failures']) > args.allow_failures:
        raise SystemExit('Too many official government sources were unavailable during this run.')


if __name__ == '__main__':
    main()
