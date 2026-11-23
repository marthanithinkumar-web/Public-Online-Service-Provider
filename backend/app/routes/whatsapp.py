import hashlib
import hmac
import logging
import os
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from ..models.order import Order
from ..models.order_history import OrderStatusHistory
from ..models.support_message import SupportMessage
from ..models.user import User
from ..models.whatsapp_message import WhatsAppMessage
from ..services import whatsapp as wa_service
from ..services.whatsapp import cloud_api_configured, verify_webhook_signature
from ..utils.database import db
from ..utils.jwt_handler import get_request_user

bp = Blueprint('whatsapp', __name__)
logger = logging.getLogger(__name__)
TERMINAL_STATUSES = {'Completed', 'Cancelled', 'Rejected'}
DELIVERY_STATUS_RANK = {'queued': 0, 'sent': 1, 'delivered': 2, 'read': 3}


def _env(name):
    return (os.getenv(name) or '').strip()


@bp.get('/config')
def whatsapp_config():
    ready = cloud_api_configured() and bool(_env('WHATSAPP_STATUS_TEMPLATE_NAME'))
    return jsonify({
        'cloud_api_enabled': cloud_api_configured(),
        'status_notifications_available': ready,
    }), 200


@bp.get('/webhook')
def verify_webhook():
    mode = request.args.get('hub.mode', '')
    token = request.args.get('hub.verify_token', '')
    challenge = request.args.get('hub.challenge', '')
    expected = _env('WHATSAPP_VERIFY_TOKEN')
    if not expected:
        return jsonify({'error': 'WhatsApp webhook is not configured'}), 503
    if mode != 'subscribe' or not hmac.compare_digest(token, expected):
        return jsonify({'error': 'Webhook verification failed'}), 403
    return challenge, 200, {'Content-Type': 'text/plain; charset=utf-8'}


def _require_admin():
    user = get_request_user()
    return user if user and user.is_admin else None


def _match_user_by_phone(phone):
    if not phone:
        return None
    target = wa_service.normalize_recipient(phone)
    if not target:
        return None
    matches = [
        user for user in User.query.filter(User.phone.isnot(None), User.is_active.is_(True)).all()
        if wa_service.normalize_recipient(user.phone) == target
    ]
    if len(matches) > 1:
        logger.warning('WhatsApp sender matched multiple active accounts; handoff withheld')
        return None
    return matches[0] if matches else None


def _inbound_event_key(message):
    message_id = str(message.get('wa_message_id') or '').strip()
    if message_id:
        return f'wa:{message_id}'
    # Meta normally supplies an ID. A bounded fingerprint protects against a
    # replay of an ID-less payload without collapsing later messages with the
    # same body when their timestamps differ.
    raw = '|'.join(str(message.get(key) or '') for key in ('from_number', 'timestamp', 'type', 'text'))
    digest = hashlib.sha256(raw.encode('utf-8')).hexdigest()
    return f'inbound:{digest}'


def _apply_delivery_status(row, incoming):
    if not row or row.direction != 'outbound' or incoming not in DELIVERY_STATUS_RANK:
        return False
    current = row.status or 'queued'
    if current == 'failed':
        return False
    if incoming == 'failed':
        if current == 'read':
            return False
        row.status = incoming
        return True
    if DELIVERY_STATUS_RANK.get(incoming, -1) > DELIVERY_STATUS_RANK.get(current, -1):
        row.status = incoming
        return True
    return False


@bp.post('/webhook')
def receive_webhook():
    raw_body = request.get_data(cache=True)
    signature = request.headers.get('X-Hub-Signature-256', '')
    if not verify_webhook_signature(raw_body, signature):
        return jsonify({'error': 'Invalid webhook signature'}), 403

    payload = request.get_json(silent=True) or {}
    inbound, delivery_statuses = wa_service.parse_webhook_payload(payload)

    # Delivery statuses first: update the outbound row that Meta reports.
    for st in delivery_statuses:
        if not st.get('wa_message_id'):
            continue
        row = WhatsAppMessage.query.filter_by(wa_message_id=st['wa_message_id']).first()
        _apply_delivery_status(row, st.get('status'))
    # Inbound messages: dedup on Meta message id, store, and hand off
    # to the existing in-site support thread when the sender matches a
    # POSP user by phone. No message content goes into admin alerts.
    for msg in inbound:
        event_key = _inbound_event_key(msg)
        if WhatsAppMessage.query.filter_by(event_key=event_key).first():
            continue
        matched = _match_user_by_phone(msg.get('from_number'))
        body = (msg.get('text') or '').strip()[:4000] if msg.get('text') else None
        row = WhatsAppMessage(
            direction='inbound',
            wa_message_id=msg.get('wa_message_id'),
            user_id=matched.id if matched else None,
            from_number=wa_service.normalize_recipient(msg.get('from_number')),
            message_type=msg.get('type'),
            body=body,
            status='received',
            event_key=event_key,
        )
        db.session.add(row)
        if matched and body:
            # Reuse the existing support architecture; do not invent a
            # separate WhatsApp-only chat. The admin reads it in the
            # existing Client Messages section.
            db.session.add(SupportMessage(
                user_id=matched.id,
                sender_user_id=matched.id,
                sender_role='client',
                message=body,
            ))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # A concurrent delivery may have inserted the same event. Replaying is
        # safe because event_key is database-enforced; other integrity errors
        # remain retryable by Meta rather than being acknowledged as processed.
        if any(WhatsAppMessage.query.filter_by(event_key=_inbound_event_key(msg)).first() for msg in inbound):
            logger.info('WhatsApp webhook duplicate delivery ignored')
        else:
            logger.exception('WhatsApp webhook integrity failure; requesting retry')
            return jsonify({'error': 'Webhook persistence failed'}), 500
    except Exception:
        db.session.rollback()
        logger.exception('WhatsApp webhook persistence failed; requesting retry')
        return jsonify({'error': 'Webhook persistence failed'}), 500
    logger.info('WhatsApp webhook accepted (messages=%s, statuses=%s)', len(inbound), len(delivery_statuses))
    return jsonify({'status': 'accepted'}), 200


@bp.get('/admin/status')
def whatsapp_admin_status():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    total = WhatsAppMessage.query.count()
    failed = WhatsAppMessage.query.filter_by(direction='outbound', status='failed').count()
    sent = WhatsAppMessage.query.filter(
        WhatsAppMessage.direction == 'outbound',
        WhatsAppMessage.status.in_(['sent', 'delivered', 'read']),
    ).count()
    inbound_count = WhatsAppMessage.query.filter_by(direction='inbound').count()
    return jsonify({
        'cloud_api_enabled': cloud_api_configured(),
        'status_notifications_available': cloud_api_configured() and bool(_env('WHATSAPP_STATUS_TEMPLATE_NAME')),
        'webhook_configured': bool(_env('WHATSAPP_VERIFY_TOKEN')) and bool(_env('WHATSAPP_APP_SECRET')),
        'webhook_url': 'https://public-online-service-provider-api.onrender.com/api/whatsapp/webhook',
        'phone_number_configured': bool(_env('WHATSAPP_PHONE_NUMBER_ID')),
        'stats': {'total': total, 'sent': sent, 'failed': failed, 'inbound': inbound_count},
    }), 200


@bp.get('/admin/messages')
def whatsapp_admin_messages():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    query = WhatsAppMessage.query
    direction = (request.args.get('direction') or '').strip()
    if direction in ('inbound', 'outbound'):
        query = query.filter_by(direction=direction)
    status = (request.args.get('status') or '').strip()
    if status:
        query = query.filter_by(status=status)
    order_id = request.args.get('order_id', type=int)
    if order_id:
        query = query.filter_by(order_id=order_id)
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(100, max(1, int(request.args.get('per_page', 50))))
    except ValueError:
        page, per_page = 1, 50
    items = query.order_by(WhatsAppMessage.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return jsonify({
        'items': [item.to_dict(include_body=False) for item in items],
        'total': query.count(),
        'page': page,
        'per_page': per_page,
    }), 200


@bp.post('/admin/messages/<int:message_id>/retry')
def whatsapp_admin_retry(message_id):
    admin = _require_admin()
    if not admin:
        return jsonify({'error': 'Unauthorized'}), 401
    row = db.get_or_404(WhatsAppMessage, message_id)
    if row.direction != 'outbound' or row.status != 'failed' or not row.order_id:
        return jsonify({'error': 'Only a failed outbound order message can be retried.'}), 409
    order = db.get_or_404(Order, row.order_id)
    if str(order.contact_method or '').lower() != 'whatsapp':
        return jsonify({'error': 'WhatsApp updates are no longer enabled for this request.'}), 409
    # Keep the failed row for audit/retry history. The notifier reuses it as a
    # queued attempt and updates it atomically after the transport call.
    from ..services.whatsapp_notify import notify_order_event
    event_key = row.event_key
    sent = False
    if event_key and ':status:' in event_key:
        # Re-send the exact status that failed, not the order's current
        # status, which may have moved on since the failure.
        failed_status = event_key.rsplit(':status:', 1)[1]
        sent = notify_order_event(order, 'status', failed_status, retry_row=row)
    elif event_key and ':confirmation:' in event_key:
        sent = notify_order_event(order, 'confirmation', 'Submitted', retry_row=row)
    elif event_key and ':completion:' in event_key:
        sent = notify_order_event(order, 'completion', 'Completed', retry_row=row)
    elif event_key and ':document:' in event_key:
        sent = notify_order_event(order, 'document', event_key.rsplit(':document:', 1)[1], retry_row=row)
    else:
        sent = notify_order_event(order, 'status', order.status, retry_row=row)
    if not sent:
        return jsonify({'error': 'Retry failed. Check WhatsApp configuration and try again.'}), 502
    return jsonify({'message': 'WhatsApp message retried.'}), 200


@bp.post('/admin/orders/<int:order_id>/document-event')
def whatsapp_admin_document_event(order_id):
    """Admin-recorded document decision sent through the shared notifier."""
    admin = _require_admin()
    if not admin:
        return jsonify({'error': 'Unauthorized'}), 401
    order = db.get_or_404(Order, order_id)
    if str(order.contact_method or '').lower() != 'whatsapp':
        return jsonify({'error': 'WhatsApp updates are not enabled for this request.'}), 409
    body = request.get_json(silent=True) or {}
    event = str(body.get('event') or '').strip()
    allowed = {'Documents Received', 'Documents Rejected', 'Document Correction Required'}
    if event not in allowed:
        return jsonify({'error': 'event must be Documents Received, Documents Rejected, or Document Correction Required.'}), 400
    from ..services.whatsapp_notify import notify_document_event
    ok = notify_document_event(order, event)
    if not ok:
        return jsonify({'error': 'WhatsApp delivery failed.'}), 502
    return jsonify({'message': 'Document notification sent.'}), 200


@bp.post('/admin/reply')
def whatsapp_admin_reply():
    """Admin WhatsApp text reply, only inside the 24-hour window.

    Outside that window Meta requires an approved template, so this
    endpoint refuses instead of silently failing or sending a
    template with free-form text. The reply is also recorded in the
    existing support thread so in-site history stays complete.
    """
    admin = _require_admin()
    if not admin:
        return jsonify({'error': 'Unauthorized'}), 401
    body = request.get_json(silent=True) or {}
    text = str(body.get('message') or '').strip()
    if not text or len(text) > 4000:
        return jsonify({'error': 'A message of 1 to 4000 characters is required.'}), 400
    order = None
    user = None
    if body.get('order_id'):
        order = db.get_or_404(Order, int(body['order_id']))
        user = db.session.get(User, order.user_id) if order.user_id else None
    elif body.get('user_id'):
        user = db.get_or_404(User, int(body['user_id']))
    if not user or not user.phone:
        return jsonify({'error': 'No phone number is available for this recipient.'}), 409
    if not wa_service.last_inbound_within_24h(user.phone):
        return jsonify({'error': 'The customer has not messaged in the last 24 hours, so a free-form WhatsApp reply is not allowed. Use an approved template instead.'}), 409
    ok, message_id, error = wa_service.send_text_message(user.phone, text)
    db.session.add(WhatsAppMessage(
        direction='outbound', wa_message_id=message_id,
        order_id=order.id if order else None, user_id=user.id,
        to_number=wa_service.normalize_recipient(user.phone),
        message_type='text', body=text[:4000],
        status='sent' if ok else 'failed', last_error=(error or '')[:500] if not ok else None,
    ))
    if ok:
        db.session.add(SupportMessage(
            user_id=user.id, sender_user_id=admin.id, sender_role='admin', message=text,
        ))
    db.session.commit()
    if not ok:
        return jsonify({'error': 'WhatsApp delivery failed.'}), 502
    return jsonify({'message': 'WhatsApp reply sent.'}), 200


@bp.get('/orders/<int:order_id>/messages')
def whatsapp_order_messages(order_id):
    user = get_request_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    order = db.get_or_404(Order, order_id)
    if not user.is_admin and order.user_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    items = WhatsAppMessage.query.filter_by(order_id=order_id).order_by(WhatsAppMessage.created_at.asc()).all()
    return jsonify({'items': [item.to_dict(include_body=True) for item in items]}), 200


@bp.post('/orders/<int:order_id>/preference')
def update_order_whatsapp_preference(order_id):
    """Record explicit, reversible WhatsApp status-notification consent per request."""
    user = get_request_user()
    if not user:
        return jsonify({'error': 'Please log in to manage WhatsApp updates.'}), 401
    if user.is_admin:
        return jsonify({'error': 'WhatsApp client preferences can only be changed by the client.'}), 403

    body = request.get_json(silent=True) or {}
    enabled = body.get('enabled')
    if not isinstance(enabled, bool):
        return jsonify({'error': 'enabled must be true or false.'}), 400

    order = Order.query.filter_by(id=order_id).with_for_update().first()
    if not order:
        return jsonify({'error': 'Request not found.'}), 404
    if order.user_id != user.id:
        return jsonify({'error': 'You can manage WhatsApp updates only for your own request.'}), 403
    if enabled and order.status in TERMINAL_STATUSES:
        return jsonify({'error': 'This request is already closed, so there are no future status updates to enable.'}), 409

    currently_enabled = str(order.contact_method or '').lower() == 'whatsapp'
    if currently_enabled == enabled:
        return jsonify({
            'message': 'WhatsApp status-update preference is already up to date.',
            'enabled': enabled,
            'order_id': order.id,
            'order_code': order.order_code,
        }), 200

    order.contact_method = 'whatsapp' if enabled else None
    order.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.session.add(OrderStatusHistory(
        order_id=order.id,
        previous_status=order.status,
        new_status=order.status,
        changed_by=user.email,
        note=(
            'Client opted in to WhatsApp status notifications for this request.'
            if enabled
            else 'Client opted out of WhatsApp status notifications for this request.'
        ),
    ))
    db.session.commit()
    return jsonify({
        'message': (
            'WhatsApp status updates enabled for this request.'
            if enabled
            else 'WhatsApp status updates disabled for this request.'
        ),
        'enabled': enabled,
        'order_id': order.id,
        'order_code': order.order_code,
    }), 200
