"""Pure validation and identity rules shared by database and snapshot feeds."""

import hashlib
import re
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def slugify(value):
    value = re.sub(r'[^a-z0-9]+', '-', str(value or '').lower()).strip('-')
    return value[:250] or 'job-notice'


def item_hash(item):
    normalized = '|'.join(
        re.sub(r'\s+', ' ', str(value or '')).strip().lower()
        for value in (item.title, item.organization, item.deadline, item.location)
    )
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def _field(item, name):
    return item.get(name) if isinstance(item, dict) else getattr(item, name, None)


def _as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _as_datetime(value):
    if isinstance(value, datetime):
        parsed = value
    elif value:
        try:
            parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        except (TypeError, ValueError):
            return None
    else:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def target_status(item, today=None, allow_missing_deadline=False, missing_deadline_max_age_days=45):
    """Require deadlines for government notices; allow configured private roles without one."""
    today = today or datetime.now(ZoneInfo('Asia/Kolkata')).date()
    deadline_value = getattr(item, 'deadline', None)
    deadline = _as_date(deadline_value)
    if deadline_value:
        if deadline is None:
            return 'needs_review'
        if deadline < today:
            return 'expired'
    else:
        issue_date = _as_date(getattr(item, 'issue_date', None))
        if issue_date and missing_deadline_max_age_days and issue_date < today - timedelta(days=missing_deadline_max_age_days):
            return 'expired'
        if not (
            allow_missing_deadline
            and str(getattr(item, 'job_type', '') or '').lower() == 'private'
            and float(getattr(item, 'confidence', 0) or 0) >= 0.8
        ):
            return 'needs_review'
    complete = bool(getattr(item, 'title', None) and getattr(item, 'organization', None) and getattr(item, 'official_notice_url', None))
    return 'published' if complete and float(getattr(item, 'confidence', 0) or 0) >= 0.8 else 'needs_review'


def is_public_active_job(item, source_allows_missing_deadline=False, today=None, now=None):
    """Return whether a stored/snapshot job meets the public active-listing rule."""
    today = today or datetime.now(ZoneInfo('Asia/Kolkata')).date()
    deadline_value = _field(item, 'deadline')
    if deadline_value:
        deadline = _as_date(deadline_value)
        return bool(deadline and deadline >= today)
    if str(_field(item, 'job_type') or '').lower() != 'private':
        return False
    if not source_allows_missing_deadline or float(_field(item, 'confidence') or 0) < 0.8:
        return False
    last_seen = _as_datetime(_field(item, 'last_seen_at'))
    if last_seen is None:
        return False
    current = _as_datetime(now) if now is not None else datetime.now(timezone.utc).replace(tzinfo=None)
    if current is None:
        return False
    return current - timedelta(days=3) <= last_seen <= current + timedelta(minutes=5)


def unique_slug(item, content_hash):
    base = slugify(f'{item.organization}-{item.title}')
    return f'{base[:245]}-{content_hash[:8]}'
