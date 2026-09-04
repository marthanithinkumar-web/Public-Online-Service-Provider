import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

LOCAL_CATALOG_PATH = Path(__file__).resolve().parent / 'data' / 'scholarships.json'
LEGACY_CATALOG_PATH = Path(__file__).resolve().parents[3] / 'frontend' / 'public' / 'data' / 'scholarships.json'
CATALOG_PATH = LOCAL_CATALOG_PATH if LOCAL_CATALOG_PATH.exists() else LEGACY_CATALOG_PATH


def _active(item, today=None):
    if str(item.get('status') or 'active').lower() != 'active':
        return False
    deadline = item.get('deadline')
    if not deadline:
        return True
    try:
        end = date.fromisoformat(str(deadline)[:10])
    except ValueError:
        return False
    return end >= (today or date.today())


def _matches(item, query):
    tokens = [token for token in re.sub(r'[^a-z0-9]+', ' ', (query or '').lower()).split() if token]
    if not tokens:
        return True
    haystack = ' '.join(str(item.get(key) or '') for key in (
        'title', 'provider', 'source_name', 'source_type', 'region', 'education_level', 'category', 'eligibility', 'academic_year'
    )).lower()
    return all(token in haystack for token in tokens)


def load_catalog(query='', today=None):
    try:
        payload = json.loads(CATALOG_PATH.read_text(encoding='utf-8'))
    except (OSError, ValueError, TypeError):
        payload = {'items': []}
    items = [item for item in payload.get('items', []) if isinstance(item, dict) and _active(item, today) and _matches(item, query)]
    items.sort(key=lambda item: (
        0 if item.get('source_type') == 'official' else 1,
        item.get('deadline') or '9999-12-31',
        item.get('title') or '',
    ))
    return {
        'items': items,
        'count': len(items),
        'generated_at': payload.get('generated_at') or datetime.now(timezone.utc).isoformat(),
        'official_count': sum(1 for item in items if item.get('source_type') == 'official' or item.get('is_official') is True),
        'private_count': sum(1 for item in items if item.get('source_type') == 'private' or item.get('is_official') is False),
        'stale_source_count': sum(1 for item in items if item.get('stale_source')),
        'discovery': payload.get('discovery') or {},
    }
