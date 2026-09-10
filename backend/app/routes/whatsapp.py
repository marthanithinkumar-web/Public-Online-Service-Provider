import hmac
import logging
import os

from flask import Blueprint, jsonify, request

from ..services.whatsapp import verify_webhook_signature

bp = Blueprint('whatsapp', __name__)
logger = logging.getLogger(__name__)


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
