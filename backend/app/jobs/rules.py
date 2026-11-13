"""Pure validation and identity rules shared by database and snapshot feeds."""

import hashlib
import re
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

DEFAULT_DEADLINE_TIMEZONE = 'Asia/Kolkata'
SOURCE_VERIFICATION_MAX_AGE = timedelta(hours=36)
CLOCK_SKEW_ALLOWANCE = timedelta(minutes=5)


def _zone(name=DEFAULT_DEADLINE_TIMEZONE):
    try:
        return ZoneInfo(str(name or DEFAULT_DEADLINE_TIMEZONE))
    except Exception:
        return ZoneInfo(DEFAULT_DEADLINE_TIMEZONE)


def _as_date(value):
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _as_utc(value, now=None):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return None
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def is_fresh_timestamp(value, now=None, max_age=SOURCE_VERIFICATION_MAX_AGE):
    """Require a recent, successful observation; future timestamps allow 5m clock skew."""
    checked = _as_utc(value)
    current = _as_utc(now) if now is not None else datetime.now(timezone.utc)
    if checked is None or current is None:
        return False
    age = current - checked
    return -CLOCK_SKEW_ALLOWANCE <= age <= max_age


def _cutoff(value):
    if isinstance(value, time):
        return value.replace(tzinfo=None)
    raw = str(value or '').strip()
    if not raw:
        return None
    try:
        return time.fromisoformat(raw)
    except ValueError:
        return None


def deadline_status(deadline, cutoff_time=None, timezone_name=DEFAULT_DEADLINE_TIMEZONE, now=None, verified=True):
    """Return an explicit user-facing deadline state using the notice's timezone."""
    due = _as_date(deadline)
    if due is None:
        return 'Unverified—check official source'
    zone = _zone(timezone_name)
    if now is None:
        local_now = datetime.now(zone)
    else:
        current = now if isinstance(now, datetime) else None
        if current is None:
            local_now = datetime.now(zone)
        elif current.tzinfo is None:
            local_now = current.replace(tzinfo=timezone.utc).astimezone(zone)
        else:
            local_now = current.astimezone(zone)
    if due < local_now.date():
        return 'Closed—deadline passed'
    if not verified:
        return 'Unverified—check official source'
    if due == local_now.date():
        closing_time = _cutoff(cutoff_time)
        if closing_time is None:
            return 'Deadline today—check official portal'
        if local_now.timetz().replace(tzinfo=None) >= closing_time:
            return 'Closed—deadline passed'
    return 'Verified open'


def snapshot_item_is_verified(item, now=None):
    source = item.get('source') or {}
    if source.get('last_sync_status') != 'success':
        return False
    return (
        is_fresh_timestamp(source.get('last_sync_completed_at'), now=now)
        and is_fresh_timestamp(item.get('last_seen_at'), now=now)
    )


def is_publicly_active_snapshot_item(item, now=None):
    """Fail closed for missing deadlines, stale items, and failed source checks."""
    if not isinstance(item, dict) or item.get('status') != 'published':
        return False
    verified = snapshot_item_is_verified(item, now=now)
    state = deadline_status(
        item.get('deadline'),
        item.get('deadline_cutoff_time'),
        item.get('deadline_timezone') or DEFAULT_DEADLINE_TIMEZONE,
        now=now,
        verified=verified,
    )
    return state in {'Verified open', 'Deadline today—check official portal'}


def slugify(value):
    value = re.sub(r'[^a-z0-9]+', '-', str(value or '').lower()).strip('-')
    return value[:250] or 'job-notice'


def item_hash(item):
    normalized = '|'.join(
        re.sub(r'\\s+', ' ', str(value or '')).strip().lower()
        for value in (item.title, item.organization, item.deadline, item.location)
    )
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def target_status(item, today=None, allow_missing_deadline=False, missing_deadline_max_age_days=45, now=None):
    """Only publish records with a current, explicit application deadline."""
    if now is None:
        if today is not None:
            now = datetime.combine(today, time.min, tzinfo=_zone())
        else:
            now = datetime.now(_zone())
    local_now = now.astimezone(_zone()) if now.tzinfo else now.replace(tzinfo=timezone.utc).astimezone(_zone())
    local_today = local_now.date()
    if item.deadline:
        state = deadline_status(
            item.deadline,
            getattr(item, 'deadline_cutoff_time', None),
            getattr(item, 'deadline_timezone', DEFAULT_DEADLINE_TIMEZONE),
            now=local_now,
            verified=True,
        )
        if state == 'Closed—deadline passed':
            return 'expired'
    elif item.issue_date and missing_deadline_max_age_days and item.issue_date < local_today - timedelta(days=missing_deadline_max_age_days):
        return 'expired'
    else:
        return 'needs_review'
    complete = bool(item.title and item.organization and item.official_notice_url and item.deadline)
    return 'published' if complete and item.confidence >= 0.8 else 'needs_review'


def unique_slug(item, content_hash):
    base = slugify(f'{item.organization}-{item.title}')
    return f'{base[:245]}-{content_hash[:8]}'
