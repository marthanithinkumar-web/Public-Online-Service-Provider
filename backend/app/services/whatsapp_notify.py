"""Best-effort WhatsApp notifications for POSP orders.

Rules, enforced here so every caller gets them for free:
- Only when the order's contact_method is 'whatsapp' (explicit opt-in).
- Never send the same business event twice: each event has a stable
  event_key, stored in whatsapp_messages with a unique constraint.
- Never break the caller: every failure is recorded on the message
  row and in logs, and the function returns False instead of raising.
- Never include document contents, OTPs, banking details, or a
  customer phone number in an admin alert; alerts carry only a
  reference and a status, and the secure tracking link is sent to
  the customer inside the approved template parameters.
- Confirmation and completion use the same approved status template
  when no dedicated template is configured, because the existing
  approved template takes (reference, status, tracking URL). A
  dedicated template name can be set later without changing callers.
"""

import logging
import os

from ..models.whatsapp_message import WhatsAppMessage
from ..utils.database import db
from . import whatsapp as wa

logger = logging.getLogger(__name__)


def _env(name):
    return (os.getenv(name) or '').strip()


def _tracking_url(order):
    base = (_env('PUBLIC_APP_URL') or _env('FRONTEND_URL') or '').rstrip('/')
    if not base:
        return f'/orders/{order.id}'
    return f'{base}/orders/{order.id}'


def _already_sent(event_key):
    if not event_key:
        return False
    row = WhatsAppMessage.query.filter_by(event_key=event_key).first()
    return row is not None and row.status in ('queued', 'sent', 'delivered', 'read')


def _record_outbound(order, event_key, template_name, to_number, ok, message_id, error):
    row = WhatsAppMessage.query.filter_by(event_key=event_key).first() if event_key else None
    if row is None:
        row = WhatsAppMessage(
            direction='outbound',
            wa_message_id=message_id,
            order_id=order.id if order else None,
            user_id=order.user_id if order else None,
            to_number=wa.normalize_recipient(to_number),
            message_type='template',
            template_name=template_name,
            body=f'Template {template_name} for order {order.order_code if order else ""}'.strip(),
            event_key=event_key,
        )
        db.session.add(row)
    row.status = 'sent' if ok else 'failed'
    row.wa_message_id = message_id or row.wa_message_id
    row.last_error = (error or '')[:500] if not ok else None
    if not ok:
        row.retry_count = (row.retry_count or 0) + 1
    db.session.commit()
    return row


def notify_order_event(order, event, status_text, template_name=None, retry_row=None):
    """Send one template notification for an order event, deduped.

    event: 'confirmation', 'status', 'document', or 'completion'.
    Returns True if sent (or already sent), False otherwise.
    """
    if order is None:
        return False
    if str(order.contact_method or '').lower() != 'whatsapp':
        return False
    if not order.phone:
        return False
    event_key = f'order:{order.id}:{event}:{status_text}'
    if retry_row is None and _already_sent(event_key):
        return True
    name = template_name or _env('WHATSAPP_STATUS_TEMPLATE_NAME')
    if not name:
        return False
    # Reserve the event key first so a concurrent duplicate cannot send twice.
    # A retry reuses the existing failed row and never deletes audit history.
    if retry_row is not None:
        row = retry_row
        row.status = 'queued'
        row.last_error = None
        db.session.commit()
    else:
        try:
            row = WhatsAppMessage(
                direction='outbound',
                order_id=order.id,
                user_id=order.user_id,
                to_number=wa.normalize_recipient(order.phone),
                message_type='template',
                template_name=name,
                body=f'Template {name} for order {order.order_code}'.strip(),
                status='queued',
                event_key=event_key,
            )
            db.session.add(row)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return _already_sent(event_key)
    try:
        ok, message_id, error = wa.send_template_with_result(
            order.phone, name, [order.order_code, status_text, _tracking_url(order)]
        )
    except Exception as exc:  # pragma: no cover - transport guard
        ok, message_id, error = False, None, type(exc).__name__
    try:
        _record_outbound(order, event_key, name, order.phone, ok, message_id, error)
    except Exception:
        db.session.rollback()
        logger.warning('WhatsApp notification record failed for order %s', order.id)
    if not ok:
        logger.warning('WhatsApp notification failed for order %s: %s', order.id, error)
        notify_admin_whatsapp_failure(order, error)
    return ok


def notify_confirmation(order):
    return notify_order_event(order, 'confirmation', 'Submitted')


def notify_status_change(order, new_status):
    return notify_order_event(order, 'status', new_status)


def notify_document_event(order, document_status):
    """Document notifications reuse the status template.

    document_status is one of 'Documents Required', 'Documents Received',
    'Documents Rejected', or 'Document Correction Required'. The
    template itself carries only reference/status/link; the reason
    stays in the in-site order history and attachments, never in a
    WhatsApp message body.
    """
    return notify_order_event(order, 'document', document_status)


def notify_completion(order):
    return notify_order_event(order, 'completion', 'Completed')


def notify_admin_whatsapp_failure(order, error):
    """Admin alert for a failed WhatsApp delivery, without phone numbers."""
    try:
        from ..utils.admin_alerts import send_admin_activity_alert
        send_admin_activity_alert(
            'WhatsApp delivery failed',
            f'WhatsApp notification for request {order.order_code} could not be delivered. '
            'Open the admin WhatsApp panel to retry.',
            order.id,
        )
    except Exception:
        pass
