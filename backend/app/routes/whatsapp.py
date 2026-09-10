import hmac
import logging
import os
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from ..models.order import Order
from ..models.order_history import OrderStatusHistory
from ..services.whatsapp import verify_webhook_signature
from ..utils.database import db
from ..utils.jwt_handler import get_request_user

bp = Blueprint('whatsapp', __name__)
logger = logging.getLogger(__name__)
TERMINAL_STATUSES = {'Completed', 'Cancelled', 'Rejected'}


def _env(name):
    return (os.getenv(name) or '').strip()


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


@bp.post('/webhook')
def receive_webhook():
    raw_body = request.get_data(cache=True)
    signature = request.headers.get('X-Hub-Signature-256', '')
    if not verify_webhook_signature(raw_body, signature):
        return jsonify({'error': 'Invalid webhook signature'}), 403

    payload = request.get_json(silent=True) or {}
    messages = 0
    statuses = 0
    for entry in payload.get('entry', []) if isinstance(payload, dict) else []:
        for change in entry.get('changes', []) if isinstance(entry, dict) else []:
            value = change.get('value', {}) if isinstance(change, dict) else {}
            messages += len(value.get('messages', []) or [])
            statuses += len(value.get('statuses', []) or [])
    logger.info('WhatsApp webhook accepted (messages=%s, statuses=%s)', messages, statuses)
    return jsonify({'status': 'accepted'}), 200


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
