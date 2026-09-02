from flask import Blueprint, jsonify

from ..models.order import Order
from ..models.payment import Payment
from ..utils.jwt_handler import get_request_user

bp = Blueprint('admin_payments', __name__)


def _captured(payment):
    return bool(payment and payment.status in {'captured', 'paid'})


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


@bp.get('/orders/<int:order_id>/payments')
def admin_order_payments(order_id):
    admin = get_request_user()
    if not admin or not admin.is_admin or not admin.is_active:
        return jsonify({'error': 'Unauthorized'}), 401
    order = Order.query.filter_by(id=order_id).first()
    if not order:
        return jsonify({'error': 'Request not found.'}), 404
    payments = Payment.query.filter_by(order_id=order.id).order_by(Payment.id.desc()).all()
    captured_purposes = {payment.purpose for payment in payments if _captured(payment)}
    if 'request_total' in captured_purposes:
        captured_purposes.update({'assistance_fee', 'official_fee'})
    breakdown = _payable_breakdown(order)
    official_due = breakdown['official_fee_status'] != 'unconfirmed' and float(breakdown['official_fee_inr'] or 0) > 0
    return jsonify({
        'payments': [payment.to_dict() for payment in payments],
        'breakdown': breakdown,
        'paid_components': {
            'assistance_fee': 'assistance_fee' in captured_purposes,
            'official_fee': 'official_fee' in captured_purposes,
        },
        'fully_paid': 'assistance_fee' in captured_purposes and (not official_due or 'official_fee' in captured_purposes),
    })
