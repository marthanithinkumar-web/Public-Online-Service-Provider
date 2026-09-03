import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parents[3] / 'frontend' / 'public' / 'data' / 'scholarships.json'


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
    haystack = ' '.join(str(item.get(key) or '') for key in ('title', 'provider', 'source_name', 'region', 'education_level', 'category', 'eligibility')).lower()
    return all(token in haystack for token in tokens)


def load_catalog(query='', today=None):
    try:
        payload = json.loads(CATALOG_PATH.read_text(encoding='utf-8'))
    except (OSError, ValueError, TypeError):
        payload = {'items': []}
    items = [item for item in payload.get('items', []) if isinstance(item, dict) and _active(item, today) and _matches(item, query)]
    items.sort(key=lambda item: (item.get('deadline') or '9999-12-31', item.get('title') or ''))
    return {'items': items, 'count': len(items), 'generated_at': datetime.now(timezone.utc).isoformat()}
