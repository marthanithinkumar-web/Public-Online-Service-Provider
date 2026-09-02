import math

from flask import Blueprint, jsonify, request

from ..middleware.auth import require_admin
from ..models.admin_audit import AdminAuditLog
from ..models.order import Order
from ..models.payment import Payment
from ..models.service import PlatformSetting
from ..utils.database import db
from ..utils.jwt_handler import get_request_user

bp = Blueprint('fees', __name__)
JOB_FEE_KEY = 'job_assistance_fee_inr'


def job_assistance_fee():
    setting = db.session.get(PlatformSetting, JOB_FEE_KEY)
    try:
        return max(0.0, float(setting.value)) if setting else 30.0
    except (TypeError, ValueError):
        return 30.0


def _money(value, label):
    try:
        amount = round(float(value), 2)
    except (TypeError, ValueError):
        raise ValueError(f'Enter a valid {label}.')
    if not math.isfinite(amount) or amount < 0 or amount > 100000:
        raise ValueError(f'{label.capitalize()} must be between ₹0 and ₹1,00,000.')
    return amount


@bp.get('/job-assistance')
def public_job_assistance_fee():
    response = jsonify({'price_inr': job_assistance_fee()})
    response.headers['Cache-Control'] = 'public, max-age=60, stale-while-revalidate=300'
    return response


@bp.put('/job-assistance')
@require_admin
def update_job_assistance_fee():
    admin = get_request_user()
    data = request.get_json(silent=True) or {}
    try:
        amount = _money(data.get('price_inr'), 'job assistance fee')
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    setting = db.session.get(PlatformSetting, JOB_FEE_KEY)
    previous = setting.value if setting else None
    if setting:
        setting.value = f'{amount:.2f}'
    else:
        db.session.add(PlatformSetting(key=JOB_FEE_KEY, value=f'{amount:.2f}'))
    db.session.add(AdminAuditLog(
        admin_id=admin.id,
        action='job_assistance_fee_update',
        summary=f'Changed the website-wide job application assistance fee to ₹{amount:.2f}.',
        details={'previous_fee_inr': previous, 'new_fee_inr': amount, 'existing_requests_repriced': False},
    ))
    db.session.commit()
    return jsonify({'message': f'Job application assistance fee updated to ₹{amount:g}.', 'price_inr': amount, 'existing_requests_repriced': False})


@bp.put('/orders/<int:order_id>')
@require_admin
def update_request_fees(order_id):
    admin = get_request_user()
    order = Order.query.filter_by(id=order_id).with_for_update().first_or_404()
    blocking_payment = Payment.query.filter(
        Payment.order_id == order.id,
        Payment.status.in_(['created', 'authorized', 'captured', 'paid']),
    ).first()
    if blocking_payment:
        return jsonify({'error': 'Fees cannot be changed after a payment checkout has been created. Resolve or refund that payment first.'}), 409

    data = request.get_json(silent=True) or {}
    status = str(data.get('official_fee_status') or '').strip().lower()
    if status not in {'known', 'none', 'unconfirmed'}:
        return jsonify({'error': 'Official fee status must be known, none, or unconfirmed.'}), 400
    try:
        assistance = _money(data.get('fee_inr', order.fee_inr or 0), 'assistance fee')
        official = _money(data.get('official_fee_inr'), 'official fee') if status == 'known' else (0.0 if status == 'none' else None)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    previous = {'fee_inr': float(order.fee_inr or 0), 'official_fee_inr': order.official_fee_inr, 'official_fee_status': order.official_fee_status}
    order.fee_inr = assistance
    order.official_fee_inr = official
    order.official_fee_status = status
    db.session.add(AdminAuditLog(
        admin_id=admin.id,
        action='request_fee_update',
        summary=f'Confirmed fees for request {order.order_code}.',
        details={'order_id': order.id, 'previous': previous, 'new': {'fee_inr': assistance, 'official_fee_inr': official, 'official_fee_status': status}},
    ))
    db.session.commit()
    total = assistance + (official or 0)
    return jsonify({'message': 'Request fees updated.', 'order': order.to_dict(include_admin=True), 'total_payable_inr': round(total, 2)})
