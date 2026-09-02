import hashlib
import hmac
import os
from datetime import datetime, timezone

import requests
from flask import Blueprint, jsonify, request

from ..models.notification import Notification
from ..models.order import Order
from ..models.payment import Payment
from ..utils.database import db
from ..utils.jwt_handler import get_request_user

bp = Blueprint('payments', __name__)
RAZORPAY_API = 'https://api.razorpay.com/v1'


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _credentials():
    key_id = (os.getenv('RAZORPAY_KEY_ID') or '').strip()
    key_secret = (os.getenv('RAZORPAY_KEY_SECRET') or '').strip()
    if not key_id or not key_secret:
        return None
    return key_id, key_secret


def _client_order(order_id):
    user = get_request_user()
    if not user or user.is_admin:
        return None, (jsonify({'error': 'Please log in as a client.'}), 401)
    order = Order.query.filter_by(id=order_id).first()
    if not order or order.user_id != user.id:
        return None, (jsonify({'error': 'Request not found.'}), 404)
    return order, None


def _captured(payment):
    return payment and payment.status in {'captured', 'paid'}


@bp.get('/config')
def payment_config():
    credentials = _credentials()
    return jsonify({
        'provider': 'razorpay',
        'enabled': bool(credentials),
        'key_id': credentials[0] if credentials else None,
        'currency': 'INR',
        'purpose': 'assistance_fee',
    })


@bp.post('/orders/<int:order_id>/checkout')
def create_checkout(order_id):
    order, error = _client_order(order_id)
    if error:
        return error
    credentials = _credentials()
    if not credentials:
        return jsonify({'error': 'Online payment is not configured yet.'}), 503

    amount_paise = int(round(float(order.fee_inr or 0) * 100))
    if amount_paise <= 0:
        return jsonify({'error': 'No assistance fee is due for this request.'}), 409

    existing = Payment.query.filter_by(order_id=order.id, purpose='assistance_fee').order_by(Payment.id.desc()).first()
    if _captured(existing):
        return jsonify({'message': 'The assistance fee is already paid.', 'payment': existing.to_dict()}), 200
    if existing and existing.status == 'created':
        return jsonify({
            'key_id': credentials[0],
            'razorpay_order_id': existing.razorpay_order_id,
            'amount': existing.amount_paise,
            'currency': existing.currency,
            'name': 'Public Online Service Provider',
            'description': f'Applicable Assistance Fee for {order.order_code}',
            'prefill': {'name': order.client_name, 'email': order.email or '', 'contact': order.phone or ''},
            'payment': existing.to_dict(),
        })

    payload = {
        'amount': amount_paise,
        'currency': 'INR',
        'receipt': order.order_code[:40],
        'notes': {
            'platform_order_id': str(order.id),
            'platform_order_code': order.order_code,
            'purpose': 'assistance_fee',
        },
    }
    try:
        response = requests.post(
            f'{RAZORPAY_API}/orders',
            json=payload,
            auth=credentials,
            timeout=15,
        )
        response.raise_for_status()
        provider_order = response.json()
    except requests.RequestException:
        return jsonify({'error': 'Unable to start Razorpay checkout right now. Please try again.'}), 502

    payment = Payment(
        order_id=order.id,
        amount_paise=amount_paise,
        currency='INR',
        status='created',
        razorpay_order_id=provider_order['id'],
    )
    db.session.add(payment)
    db.session.commit()
    return jsonify({
        'key_id': credentials[0],
        'razorpay_order_id': payment.razorpay_order_id,
        'amount': payment.amount_paise,
        'currency': payment.currency,
        'name': 'Public Online Service Provider',
        'description': f'Applicable Assistance Fee for {order.order_code}',
        'prefill': {'name': order.client_name, 'email': order.email or '', 'contact': order.phone or ''},
        'payment': payment.to_dict(),
    }), 201


@bp.post('/orders/<int:order_id>/verify')
def verify_checkout(order_id):
    order, error = _client_order(order_id)
    if error:
        return error
    credentials = _credentials()
    if not credentials:
        return jsonify({'error': 'Online payment is not configured yet.'}), 503

    data = request.get_json(silent=True) or {}
    payment_id = str(data.get('razorpay_payment_id') or '').strip()
    checkout_order_id = str(data.get('razorpay_order_id') or '').strip()
    signature = str(data.get('razorpay_signature') or '').strip()
    if not payment_id or not checkout_order_id or not signature:
        return jsonify({'error': 'Incomplete payment confirmation.'}), 400

    payment = Payment.query.filter_by(order_id=order.id, razorpay_order_id=checkout_order_id).first()
    if not payment:
        return jsonify({'error': 'Payment order does not match this request.'}), 400

    expected = hmac.new(
        credentials[1].encode('utf-8'),
        f'{payment.razorpay_order_id}|{payment_id}'.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return jsonify({'error': 'Payment signature verification failed.'}), 400

    # Signature proves authenticity, but fulfilment waits for captured/paid state.
    payment.razorpay_payment_id = payment_id
    payment.status = 'authorized'
    db.session.commit()
    return jsonify({
        'message': 'Payment authorised. Final confirmation will update automatically after capture.',
        'payment': payment.to_dict(),
    })


@bp.get('/orders/<int:order_id>/status')
def payment_status(order_id):
    order, error = _client_order(order_id)
    if error:
        return error
    payment = Payment.query.filter_by(order_id=order.id, purpose='assistance_fee').order_by(Payment.id.desc()).first()
    return jsonify({'payment': payment.to_dict() if payment else None})


@bp.post('/razorpay/webhook')
def razorpay_webhook():
    secret = (os.getenv('RAZORPAY_WEBHOOK_SECRET') or '').strip()
    if not secret:
        return jsonify({'error': 'Webhook is not configured.'}), 503
    signature = (request.headers.get('X-Razorpay-Signature') or '').strip()
    raw = request.get_data(cache=True)
    expected = hmac.new(secret.encode('utf-8'), raw, hashlib.sha256).hexdigest()
    if not signature or not hmac.compare_digest(expected, signature):
        return jsonify({'error': 'Invalid webhook signature.'}), 400

    event = request.get_json(silent=True) or {}
    event_name = event.get('event')
    payment_entity = ((event.get('payload') or {}).get('payment') or {}).get('entity') or {}
    provider_order_id = payment_entity.get('order_id')
    provider_payment_id = payment_entity.get('id')
    if not provider_order_id:
        order_entity = ((event.get('payload') or {}).get('order') or {}).get('entity') or {}
        provider_order_id = order_entity.get('id')
    payment = Payment.query.filter_by(razorpay_order_id=provider_order_id).first() if provider_order_id else None
    if not payment:
        return jsonify({'ok': True}), 200

    if provider_payment_id and not payment.razorpay_payment_id:
        payment.razorpay_payment_id = provider_payment_id

    if event_name in {'payment.captured', 'order.paid'}:
        was_captured = _captured(payment)
        payment.status = 'captured'
        payment.captured_at = payment.captured_at or utc_now()
        payment.failure_code = None
        payment.failure_description = None
        if not was_captured:
            db.session.add(Notification(
                user_id=payment.order.user_id,
                order_id=payment.order_id,
                title='Assistance fee payment received',
                message=f'Payment for request {payment.order.order_code} was received successfully.',
            ))
    elif event_name == 'payment.failed':
        payment.status = 'failed'
        payment.failure_code = str(payment_entity.get('error_code') or '')[:120] or None
        payment.failure_description = str(payment_entity.get('error_description') or '')[:1000] or None
    elif event_name == 'payment.authorized' and payment.status == 'created':
        payment.status = 'authorized'

    db.session.commit()
    return jsonify({'ok': True}), 200
