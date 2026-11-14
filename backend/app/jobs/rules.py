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


def target_status(item, today=None, allow_missing_deadline=False, missing_deadline_max_age_days=45, now=None):
    """Publish only complete notices whose official application window is still valid."""
    try:
        tz = ZoneInfo(getattr(item, 'deadline_timezone', None) or 'Asia/Kolkata')
    except Exception:
        return 'needs_review'
    current = now or datetime.now(tz)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    local = current.astimezone(tz)
    today = today or local.date()
    if item.deadline:
        if item.deadline < today:
            return 'expired'
        if item.deadline == today and item.deadline_cutoff_time and local.timetz().replace(tzinfo=None) >= item.deadline_cutoff_time:
            return 'expired'
    elif item.issue_date and missing_deadline_max_age_days and item.issue_date < today - timedelta(days=missing_deadline_max_age_days):
        return 'expired'
    else:
        return 'needs_review'
    complete = bool(item.title and item.organization and item.official_notice_url and item.deadline)
    return 'published' if complete and item.confidence >= 0.8 else 'needs_review'

def unique_slug(item, content_hash):
    base = slugify(f'{item.organization}-{item.title}')
    return f'{base[:245]}-{content_hash[:8]}'
