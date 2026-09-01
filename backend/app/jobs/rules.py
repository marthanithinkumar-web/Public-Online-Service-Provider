"""Pure validation and identity rules shared by database and snapshot feeds."""

import hashlib
import re
from datetime import date, timedelta


def slugify(value):
    value = re.sub(r'[^a-z0-9]+', '-', str(value or '').lower()).strip('-')
    return value[:250] or 'job-notice'


def item_hash(item):
    normalized = '|'.join(
        re.sub(r'\s+', ' ', str(value or '')).strip().lower()
        for value in (item.title, item.organization, item.deadline, item.location)
    )
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def target_status(item, today=None, allow_missing_deadline=False, missing_deadline_max_age_days=45):
    today = today or date.today()
    if item.deadline and item.deadline < today:
        return 'expired'
    if (
        not item.deadline
        and item.issue_date
        and missing_deadline_max_age_days
        and item.issue_date < today - timedelta(days=missing_deadline_max_age_days)
    ):
        return 'expired'
    complete = bool(
        item.title and item.organization and item.official_notice_url
        and (item.deadline or allow_missing_deadline)
    )
    return 'published' if complete and item.confidence >= 0.8 else 'needs_review'


def unique_slug(item, content_hash):
    base = slugify(f'{item.organization}-{item.title}')
    return f'{base[:245]}-{content_hash[:8]}'
