import json
import re
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

LOCAL_CATALOG_PATH = Path(__file__).resolve().parent / 'data' / 'scholarships.json'
LEGACY_CATALOG_PATH = Path(__file__).resolve().parents[3] / 'frontend' / 'public' / 'data' / 'scholarships.json'
CATALOG_PATH = LOCAL_CATALOG_PATH if LOCAL_CATALOG_PATH.exists() else LEGACY_CATALOG_PATH
VERIFICATION_MAX_AGE = timedelta(hours=36)
ROLLING_OPEN_EVIDENCE = re.compile(
    r'\b(?:currently accepting applications|applications? (?:are )?(?:currently )?open|'
    r'open for applications|registration\b.{0,80}\b(?:is|are)\s+(?:currently\s+)?open|'
    r'application process is open)\b',
    re.I,
)


def _timestamp(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _fresh_source_check(item, now=None):
    checked = _timestamp(
        item.get('source_checked_at')
        or item.get('verified_at')
        or item.get('last_seen_at')
    )
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    current = current.astimezone(timezone.utc)
    return bool(
        checked
        and current - VERIFICATION_MAX_AGE <= checked <= current + timedelta(minutes=5)
    )


def _active(item, today=None, now=None):
    """Fail closed: publish only fresh, official student-application evidence."""
    """Return only fresh, evidence-backed official student-application opportunities.

    A verification deadline is never substituted for a student application
    deadline. Date-only deadlines that fall today are shown with a warning
    state, not counted as verified-open.
    """
    if str(item.get('status') or '').lower() != 'active' or item.get('stale_source'):
        return False
    if item.get('source_type') != 'official' or item.get('is_official') is not True:
        return False
    evidence = str(item.get('status_evidence') or '').strip()
    if not evidence or not _fresh_source_check(item, now=now):
        return False
    application_status = str(item.get('application_status') or '').lower()
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    india_today = today or current.astimezone(ZoneInfo('Asia/Kolkata')).date()
    deadline = item.get('deadline')
    if not deadline:
        return application_status == 'open' and bool(ROLLING_OPEN_EVIDENCE.search(evidence))
    try:
        end = date.fromisoformat(str(deadline)[:10])
    except (TypeError, ValueError):
        return False
    if end < india_today:
        return False
    if end == india_today:
        return application_status == 'deadline_today'
    return application_status == 'open'


def _matches(item, query):
    tokens = [token for token in re.sub(r'[^a-z0-9]+', ' ', (query or '').lower()).split() if token]
    if not tokens:
        return True
    haystack = ' '.join(str(item.get(key) or '') for key in (
        'title', 'provider', 'source_name', 'source_type', 'region', 'education_level', 'category', 'eligibility', 'academic_year'
    )).lower()
    return all(token in haystack for token in tokens)


def load_catalog(query='', today=None, now=None):
    try:
        payload = json.loads(CATALOG_PATH.read_text(encoding='utf-8'))
    except (OSError, ValueError, TypeError):
        payload = {'items': []}
    items = [
        item for item in payload.get('items', [])
        if isinstance(item, dict) and _active(item, today, now=now) and _matches(item, query)
    ]
    items.sort(key=lambda item: (
        0 if item.get('source_type') == 'official' else 1,
        item.get('deadline') or '9999-12-31',
        item.get('title') or '',
    ))
    official_count = sum(1 for item in items if item.get('source_type') == 'official' or item.get('is_official') is True)
    private_count = sum(1 for item in items if item.get('source_type') == 'private' or item.get('is_official') is False)
    health = (payload.get('discovery') or {}).get('source_health') or {}
    checked_successfully = [
        _timestamp(value.get('checked_at'))
        for value in health.values()
        if isinstance(value, dict) and value.get('ok')
    ]
    checked_successfully = [value for value in checked_successfully if value]
    stale_count = int(payload.get('stale_source_count') or len(payload.get('stale_items') or []))
    closed_count = int(payload.get('closed_count') or len(payload.get('closed_items') or []))
    return {
        'items': items,
        'count': len(items),
        'generated_at': payload.get('generated_at') or datetime.now(timezone.utc).isoformat(),
        'official_count': official_count,
        'private_count': private_count,
        'verified_open_count': sum(1 for item in items if item.get('application_status') == 'open'),
        'deadline_today_count': sum(1 for item in items if item.get('application_status') == 'deadline_today'),
        'closed_count': closed_count,
        'unverified_count': stale_count + len(payload.get('unverified_items') or []),
        'stale_source_count': stale_count,
        'source_failures': sum(1 for value in health.values() if isinstance(value, dict) and not value.get('ok')),
        'last_successful_sync_at': max(checked_successfully).isoformat() if checked_successfully else None,
        'discovery': payload.get('discovery') or {},
    }
