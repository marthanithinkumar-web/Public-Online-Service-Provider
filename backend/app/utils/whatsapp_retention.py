"""Explicit retention maintenance for WhatsApp message records.

Inbound and outbound WhatsApp rows contain personal data and delivery metadata.
The policy is a 90-day default, configurable with
``WHATSAPP_MESSAGE_RETENTION_DAYS``. Cleanup is dry-run by default and must be
explicitly invoked with ``apply=True`` by an authorized maintenance process.
"""

import os
from collections import Counter
from datetime import datetime, timedelta, timezone

from ..models.whatsapp_message import WhatsAppMessage
from ..utils.database import db

DEFAULT_RETENTION_DAYS = 90
MIN_RETENTION_DAYS = 30
MAX_RETENTION_DAYS = 3650


def retention_days():
    raw = (os.getenv('WHATSAPP_MESSAGE_RETENTION_DAYS') or str(DEFAULT_RETENTION_DAYS)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError('WHATSAPP_MESSAGE_RETENTION_DAYS must be an integer') from exc
    if not MIN_RETENTION_DAYS <= value <= MAX_RETENTION_DAYS:
        raise ValueError(
            f'WHATSAPP_MESSAGE_RETENTION_DAYS must be between {MIN_RETENTION_DAYS} and {MAX_RETENTION_DAYS}'
        )
    return value


def purge_whatsapp_messages(*, apply=False, limit=None):
    """Preview or delete WhatsApp rows older than the configured retention.

    The default is a read-only preview. Applying deletion removes complete rows
    so message bodies, phone numbers, delivery IDs, and error details are not
    retained beyond the policy window. Work is committed one row at a time so
    an interrupted run can be safely repeated.
    """
    days = retention_days()
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    query = WhatsAppMessage.query.filter(WhatsAppMessage.created_at < cutoff).order_by(WhatsAppMessage.id.asc())
    if limit is not None:
        limit = max(1, int(limit))
        query = query.limit(limit)
    rows = query.all()
    direction_counts = Counter(row.direction for row in rows)
    deleted = 0
    failures = []

    if apply:
        for row in rows:
            try:
                db.session.delete(row)
                db.session.commit()
                deleted += 1
            except Exception as exc:
                db.session.rollback()
                failures.append({'message_id': row.id, 'error': type(exc).__name__})

    return {
        'mode': 'apply' if apply else 'dry-run',
        'retention_days': days,
        'cutoff': cutoff.isoformat(),
        'matched_messages': len(rows),
        'deleted_messages': deleted,
        'failed_messages': len(failures),
        'failures': failures,
        'direction_counts': dict(sorted(direction_counts.items())),
    }
