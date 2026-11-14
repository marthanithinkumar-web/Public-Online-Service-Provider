import json
import re
from datetime import date, datetime, time, timedelta, timezone
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


def _local_deadline_now(item, now=None):
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    tz = ZoneInfo(str(item.get('deadline_timezone') or 'Asia/Kolkata'))
    return current.astimezone(tz)


def _normalise_deadline_today(item, today=None, now=None):
    value = dict(item)
    try:
        local = _local_deadline_now(value, now=now)
    except Exception:
        return value
    local_today = today or local.date()
    if (
        value.get('deadline')
        and str(value.get('deadline'))[:10] == local_today.isoformat()
        and str(value.get('application_status') or '').lower() == 'open'
    ):
        value['application_status'] = 'deadline_today'
    return value


def _active(item, today=None, now=None):
    """Return only fresh, evidence-backed official student-application opportunities.

    Fail closed: publish only verified student-application dates, never downstream
    verification dates or undated records without explicit current-open evidence.

    A verification deadline is never substituted for a student application
    deadline. Date-only deadlines that fall today are shown with a warning
    state, not counted as verified-open. A published cutoff is enforced in the
    item's own timezone.
    """
    if str(item.get('status') or '').lower() != 'active' or item.get('stale_source'):
        return False
    if item.get('source_type') != 'official' or item.get('is_official') is not True:
        return False
    evidence = str(item.get('status_evidence') or '').strip()
    if not evidence or not _fresh_source_check(item, now=now):
        return False
    application_status = str(item.get('application_status') or '').lower()
    deadline = item.get('deadline')
    if deadline and item.get('deadline_type') != 'student_application':
        return False
    if not deadline:
        return application_status == 'open' and bool(ROLLING_OPEN_EVIDENCE.search(evidence))
    try:
        end = date.fromisoformat(str(deadline)[:10])
        local = _local_deadline_now(item, now=now)
    except (TypeError, ValueError, KeyError):
        return False
    local_today = today or local.date()
    if end < local_today:
        return False
    if end == local_today:
        if application_status != 'deadline_today':
            return False
        cutoff_value = item.get('deadline_cutoff_time')
        if cutoff_value:
            try:
                cutoff = time.fromisoformat(str(cutoff_value))
            except ValueError:
                return False
            if local.timetz().replace(tzinfo=None) >= cutoff:
                return False
        return True
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
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    items = []
    for raw_item in payload.get('items', []):
        if not isinstance(raw_item, dict):
            continue
        item = _normalise_deadline_today(raw_item, today=today, now=current)
        if _active(item, today=today, now=current) and _matches(item, query):
            items.append(item)
    items.sort(key=lambda item: (
        0 if item.get('source_type') == 'official' else 1,
        item.get('deadline') or '9999-12-31',
        item.get('title') or '',
    ))
    official_count = sum(1 for item in items if item.get('source_type') == 'official' or item.get('is_official') is True)
    private_count = sum(1 for item in items if item.get('source_type') == 'private' or item.get('is_official') is False)
    return {
        'items': items,
        'count': len(items),
        'generated_at': payload.get('generated_at') or datetime.now(timezone.utc).isoformat(),
        'official_count': official_count,
        'private_count': private_count,
        'verified_open_count': sum(1 for item in items if item.get('application_status') == 'open'),
        'deadline_today_count': sum(1 for item in items if item.get('application_status') == 'deadline_today'),
    }
