import hashlib
import hmac
import os
from datetime import datetime, timezone

import requests
from flask import Blueprint, Response, jsonify, request

from ..models.notification import Notification
from ..models.order import Order
from ..models.payment import Payment
from ..utils.database import db
from ..utils.email import send_email
from ..utils.jwt_handler import get_request_user
from ..utils.payment_receipt import receipt_html, receipt_text

bp = Blueprint('payments', __name__)
RAZORPAY_API = 'https://api.razorpay.com/v1'
PAYMENT_PURPOSES = {'assistance_fee', 'official_fee', 'request_total'}


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _credentials():
    key_id = (os.getenv('RAZORPAY_KEY_ID') or '').strip()
    key_secret = (os.getenv('RAZORPAY_KEY_SECRET') or '').strip()
    return (key_id, key_secret) if key_id and key_secret else None


def _client_order(order_id):
    user = get_request_user()
    if not user or user.is_admin:
        return None, (jsonify({'error': 'Please log in as a client.'}), 401)
    order = Order.query.filter_by(id=order_id).first()
    if not order or order.user_id != user.id:
        return None, (jsonify({'error': 'Request not found.'}), 404)
    return order, None


def _captured(payment):
    return bool(payment and payment.status in {'captured', 'paid'})


def _payments_for(order):
    return Payment.query.filter_by(order_id=order.id).order_by(Payment.id.desc()).all()


def _captured_purposes(order):
    purposes = {payment.purpose for payment in _payments_for(order) if _captured(payment)}
    if 'request_total' in purposes:
        purposes.update({'assistance_fee', 'official_fee'})
    return purposes


def _payable_breakdown(order):
    assistance = round(float(order.fee_inr or 0), 2)
    status = order.official_fee_status or 'unconfirmed'
    official = None
    if status in {'known', 'none'}:
        official = round(float(order.official_fee_inr or 0), 2)
    return {
        'assistance_fee_inr': assistance,
        'official_fee_inr': official,
        'official_fee_status': status,
        'combined_total_inr': round(assistance + (official or 0), 2) if official is not None else None,
    }


def _payment_payload(payment):
    data = payment.to_dict() if payment else None
    if data and _captured(payment):
        data['receipt_available'] = True
    return data


def _purpose_amount(order, purpose):
    breakdown = _payable_breakdown(order)
    paid = _captured_purposes(order)
    if purpose == 'assistance_fee':
        if 'assistance_fee' in paid:
            raise ValueError('The assistance fee has already been paid.')
        return breakdown['assistance_fee_inr'], breakdown
    if purpose == 'official_fee':
        if breakdown['official_fee_status'] == 'unconfirmed':
            raise LookupError('The official fee has not been confirmed yet.')
        if 'official_fee' in paid:
            raise ValueError('The official fee has already been paid.')
        return float(breakdown['official_fee_inr'] or 0), breakdown
    if purpose == 'request_total':
        if breakdown['official_fee_status'] == 'unconfirmed':
            raise LookupError('The official fee has not been confirmed yet.')
        if 'assistance_fee' in paid or 'official_fee' in paid:
            raise ValueError('One part of this request has already been paid. Please pay only the remaining fee.')
        return float(breakdown['combined_total_inr'] or 0), breakdown
    raise ValueError('Invalid payment option.')


def _email_receipt(payment):
    order = payment.order
    if not order or not order.email:
        return False
    return send_email(order.email, f'Payment receipt for request {order.order_code}', receipt_text(order, payment))


@bp.get('/config')
def payment_config():
    credentials = _credentials()
    return jsonify({'provider': 'razorpay', 'enabled': bool(credentials), 'key_id': credentials[0] if credentials else None, 'currency': 'INR', 'purposes': sorted(PAYMENT_PURPOSES)})


@bp.post('/orders/<int:order_id>/checkout')
def create_checkout(order_id):
    order, error = _client_order(order_id)
    if error:
        return error
    credentials = _credentials()
    if not credentials:
        return jsonify({'error': 'Online payment is not configured yet.'}), 503
    data = request.get_json(silent=True) or {}
    purpose = str(data.get('purpose') or 'request_total').strip()
    if purpose not in PAYMENT_PURPOSES:
        return jsonify({'error': 'Choose assistance fee, official fee, or both fees.'}), 400
    try:
        amount, breakdown = _purpose_amount(order, purpose)
    except LookupError as exc:
        return jsonify({'error': str(exc), 'breakdown': _payable_breakdown(order)}), 409
    except ValueError as exc:
        return jsonify({'error': str(exc), 'breakdown': _payable_breakdown(order)}), 409
    amount_paise = int(round(amount * 100))
    if amount_paise <= 0:
        return jsonify({'message': 'Nothing is payable for this payment option.', 'payment': None, 'breakdown': breakdown}), 200

    existing = Payment.query.filter_by(order_id=order.id, purpose=purpose).order_by(Payment.id.desc()).first()
    if _captured(existing):
        return jsonify({'message': 'This fee has already been paid.', 'payment': _payment_payload(existing), 'breakdown': breakdown}), 200
    if existing and existing.status in {'created', 'authorized'}:
        if existing.amount_paise != amount_paise:
            return jsonify({'error': 'The fee changed after checkout was created. Contact the administrator before paying.'}), 409
        return jsonify({'key_id': credentials[0], 'razorpay_order_id': existing.razorpay_order_id, 'amount': existing.amount_paise, 'currency': existing.currency, 'name': 'Public Online Service Provider', 'description': f'{purpose.replace("_", " ").title()} for {order.order_code}', 'prefill': {'name': order.client_name, 'email': order.email or '', 'contact': order.phone or ''}, 'payment': _payment_payload(existing), 'breakdown': breakdown, 'purpose': purpose})

    payload = {
        'amount': amount_paise,
        'currency': 'INR',
        'receipt': f'{order.order_code}-{purpose}'[:40],
        'notes': {
            'platform_order_id': str(order.id),
            'platform_order_code': order.order_code,
            'purpose': purpose,
            'assistance_fee_inr': f"{breakdown['assistance_fee_inr']:.2f}",
            'official_fee_inr': '' if breakdown['official_fee_inr'] is None else f"{breakdown['official_fee_inr']:.2f}",
        },
    }
    try:
        response = requests.post(f'{RAZORPAY_API}/orders', json=payload, auth=credentials, timeout=15)
        response.raise_for_status()
        provider_order = response.json()
    except requests.RequestException:
        return jsonify({'error': 'Unable to start Razorpay checkout right now. Please try again.'}), 502

    payment = Payment(order_id=order.id, purpose=purpose, amount_paise=amount_paise, currency='INR', status='created', razorpay_order_id=provider_order['id'])
    db.session.add(payment)
    db.session.commit()
    return jsonify({'key_id': credentials[0], 'razorpay_order_id': payment.razorpay_order_id, 'amount': payment.amount_paise, 'currency': payment.currency, 'name': 'Public Online Service Provider', 'description': f'{purpose.replace("_", " ").title()} for {order.order_code}', 'prefill': {'name': order.client_name, 'email': order.email or '', 'contact': order.phone or ''}, 'payment': _payment_payload(payment), 'breakdown': breakdown, 'purpose': purpose}), 201


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
    expected = hmac.new(credentials[1].encode('utf-8'), f'{payment.razorpay_order_id}|{payment_id}'.encode('utf-8'), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return jsonify({'error': 'Payment signature verification failed.'}), 400
    payment.razorpay_payment_id = payment_id
    if not _captured(payment):
        payment.status = 'authorized'
    db.session.commit()
    return jsonify({'message': 'Payment authorised. Final confirmation will update automatically after capture.', 'payment': _payment_payload(payment)})


@bp.get('/orders/<int:order_id>/status')
def payment_status(order_id):
    order, error = _client_order(order_id)
    if error:
        return error
    payments = _payments_for(order)
    captured = _captured_purposes(order)
    breakdown = _payable_breakdown(order)
    latest = payments[0] if payments else None
    return jsonify({
        'payment': _payment_payload(latest),
        'payments': [_payment_payload(payment) for payment in payments],
        'breakdown': breakdown,
        'paid_components': {'assistance_fee': 'assistance_fee' in captured, 'official_fee': 'official_fee' in captured},
        'fully_paid': 'assistance_fee' in captured and (breakdown['official_fee_status'] == 'unconfirmed' or 'official_fee' in captured or float(breakdown['official_fee_inr'] or 0) == 0),
        'total_payable_inr': breakdown['combined_total_inr'],
    })


@bp.get('/orders/<int:order_id>/receipt')
def payment_receipt(order_id):
    order, error = _client_order(order_id)
    if error:
        return error
    payment_id = request.args.get('payment_id', type=int)
    query = Payment.query.filter_by(order_id=order.id)
    payment = query.filter_by(id=payment_id).first() if payment_id else query.filter(Payment.status.in_(['captured', 'paid'])).order_by(Payment.id.desc()).first()
    if not _captured(payment):
        return jsonify({'error': 'A receipt is available only after payment is confirmed.'}), 409
    return Response(receipt_html(order, payment), mimetype='text/html', headers={'Cache-Control': 'private, no-store'})


@bp.post('/orders/<int:order_id>/receipt/email')
def email_payment_receipt(order_id):
    order, error = _client_order(order_id)
    if error:
        return error
    payment = Payment.query.filter_by(order_id=order.id).filter(Payment.status.in_(['captured', 'paid'])).order_by(Payment.id.desc()).first()
    if not payment:
        return jsonify({'error': 'A receipt is available only after payment is confirmed.'}), 409
    if not order.email:
        return jsonify({'error': 'No email address is saved for this request.'}), 400
    if not _email_receipt(payment):
        return jsonify({'error': 'Receipt email could not be delivered. You can still view or print the receipt here.'}), 503
    return jsonify({'message': 'Receipt emailed successfully.'})


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
    send_receipt = False
    if event_name in {'payment.captured', 'order.paid'}:
        was_captured = _captured(payment)
        payment.status = 'captured'
        payment.captured_at = payment.captured_at or utc_now()
        payment.failure_code = None
        payment.failure_description = None
        if not was_captured:
            send_receipt = True
            label = {'assistance_fee': 'assistance fee', 'official_fee': 'official fee', 'request_total': 'combined request fees'}.get(payment.purpose, 'request payment')
            db.session.add(Notification(user_id=payment.order.user_id, order_id=payment.order_id, title='Request payment received', message=f'Your {label} payment for request {payment.order.order_code} was received successfully. Your payment receipt is now available in the request.'))
    elif event_name == 'payment.failed' and not _captured(payment):
        payment.status = 'failed'
        payment.failure_code = str(payment_entity.get('error_code') or '')[:120] or None
        payment.failure_description = str(payment_entity.get('error_description') or '')[:1000] or None
    elif event_name == 'payment.authorized' and payment.status == 'created':
        payment.status = 'authorized'
    db.session.commit()
    if send_receipt:
        _email_receipt(payment)
    return jsonify({'ok': True}), 200
