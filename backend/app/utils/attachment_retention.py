"""Maintenance helpers for enforcing attachment-retention policy on old orders.

Newly closed orders are handled by the SQLAlchemy hook in ``models.order``.
This module exists for historical rows that were already terminal before that
hook was deployed.
"""

from collections import Counter

from ..models.attachment import Attachment
from ..models.order import CLIENT_DOCUMENT_PURGE_STATUSES, Order
from ..utils.database import db
from ..utils.s3 import delete_stored_file


def historical_client_attachments_query():
    """Return client-owned attachments still present on terminal orders."""
    return (
        Attachment.query
        .join(Order, Attachment.order_id == Order.id)
        .filter(
            Order.status.in_(CLIENT_DOCUMENT_PURGE_STATUSES),
            Order.user_id.isnot(None),
            Attachment.uploaded_by == Order.user_id,
        )
        .order_by(Attachment.id.asc())
    )


def purge_historical_client_attachments(*, apply=False, limit=None):
    """Find or purge legacy client documents from already-closed requests.

    Dry-run is the default. When ``apply`` is true, storage deletion happens
    before each database row is removed. ``delete_stored_file`` is idempotent,
    so rerunning after an interrupted attempt is safe.
    """
    query = historical_client_attachments_query()
    if limit is not None:
        limit = max(1, int(limit))
        query = query.limit(limit)
    attachments = query.all()
    status_counts = Counter()
    order_ids = set()
    failures = []
    deleted = 0

    for attachment in attachments:
        order = db.session.get(Order, attachment.order_id)
        if not order:
            continue
        status_counts[order.status] += 1
        order_ids.add(order.id)
        if not apply:
            continue
        try:
            delete_stored_file(attachment.stored_path)
            db.session.delete(attachment)
            db.session.commit()
            deleted += 1
        except Exception as exc:
            db.session.rollback()
            failures.append({
                'attachment_id': attachment.id,
                'order_id': attachment.order_id,
                'error': type(exc).__name__,
            })

    return {
        'mode': 'apply' if apply else 'dry-run',
        'matched_attachments': len(attachments),
        'matched_orders': len(order_ids),
        'deleted_attachments': deleted,
        'failed_attachments': len(failures),
        'failures': failures,
        'status_counts': dict(sorted(status_counts.items())),
    }
