import math
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from ..jobs.fee_rules import assess_official_fee, normalise_fee_configuration
from ..middleware.auth import require_admin
from ..models.admin_audit import AdminAuditLog
from ..models.job import JobNotification
from ..models.order import Order
from ..models.payment import Payment
from ..models.service import PlatformSetting, Service
from ..utils.database import db
from ..utils.jwt_handler import get_request_user

bp = Blueprint('fees', __name__)
JOB_FEE_KEY = 'job_assistance_fee_inr'
JOB_SERVICE_NAME = 'Government Job Application Assistance'


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def job_assistance_fee():
    setting = db.session.get(PlatformSetting, JOB_FEE_KEY)
    try:
        if setting:
            return max(0.0, float(setting.value))
    except (TypeError, ValueError):
        pass
    service = Service.query.filter_by(name=JOB_SERVICE_NAME).first()
    return max(0.0, float(service.price_inr or 0)) if service else 30.0


def _money(value, label):
    try:
        amount = round(float(value), 2)
    except (TypeError, ValueError):
        raise ValueError(f'Enter a valid {label}.')
    if not math.isfinite(amount) or amount < 0 or amount > 100000:
        raise ValueError(f'{label.capitalize()} must be between ₹0 and ₹1,00,000.')
    return amount


def _component_locked(order, component):
    purposes = ['request_total', component]
    return Payment.query.filter(Payment.order_id == order.id, Payment.purpose.in_(purposes), Payment.status.in_(['created', 'authorized', 'captured', 'paid'])).first() is not None


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
    service = Service.query.filter_by(name=JOB_SERVICE_NAME).first()
    if service:
        service.price_inr = amount
    db.session.add(AdminAuditLog(admin_id=admin.id, action='job_assistance_fee_update', summary=f'Changed the website-wide job application assistance fee to ₹{amount:.2f}.', details={'previous_fee_inr': previous, 'new_fee_inr': amount, 'service_catalog_updated': bool(service), 'existing_requests_repriced': False}))
    db.session.commit()
    return jsonify({'message': f'Job application assistance fee updated to ₹{amount:g} across the website.', 'price_inr': amount, 'existing_requests_repriced': False})


@bp.put('/jobs/<int:job_id>/rules')
@require_admin
def update_job_fee_rules(job_id):
    admin = get_request_user()
    job = db.get_or_404(JobNotification, job_id)
    data = request.get_json(silent=True) or {}
    try:
        factors, rules = normalise_fee_configuration(data.get('factors') or [], data.get('rules') or [])
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    if data.get('confirm_from_official_notice') is not True:
        return jsonify({'error': 'Confirm that these fee rules were checked against the official notification.'}), 400
    job.fee_factors = factors
    job.fee_rules = rules
    job.fee_rules_verified_at = utc_now()
    db.session.add(AdminAuditLog(admin_id=admin.id, action='job_official_fee_rules_verified', summary=f'Verified person-specific official fee rules for job {job.id}: {job.title}'[:500], details={'job_id': job.id, 'factor_keys': [item['key'] for item in factors], 'rule_count': len(rules)}))
    db.session.commit()
    return jsonify({'message': 'Official fee rules verified for this job.', 'job': job.to_dict(include_admin=True)})


@bp.delete('/jobs/<int:job_id>/rules')
@require_admin
def clear_job_fee_rules(job_id):
    admin = get_request_user()
    job = db.get_or_404(JobNotification, job_id)
    job.fee_factors = None
    job.fee_rules = None
    job.fee_rules_verified_at = None
    db.session.add(AdminAuditLog(admin_id=admin.id, action='job_official_fee_rules_cleared', summary=f'Cleared person-specific official fee rules for job {job.id}: {job.title}'[:500], details={'job_id': job.id}))
    db.session.commit()
    return jsonify({'message': 'Official fee rules cleared. This job will require manual fee confirmation.', 'job': job.to_dict(include_admin=True)})


@bp.post('/jobs/<string:slug>/assess')
def assess_job_fee(slug):
    user = get_request_user()
    if not user or user.is_admin:
        return jsonify({'error': 'Please log in as a client.'}), 401
    job = JobNotification.query.filter_by(slug=slug, status='published').first_or_404()
    answers = (request.get_json(silent=True) or {}).get('answers') or {}
    if not isinstance(answers, dict):
        return jsonify({'error': 'Fee assessment answers must use named fields.'}), 400
    result = assess_official_fee(job, answers)
    if result['status'] == 'missing_factors':
        return jsonify({'error': 'Complete all fee-determining details.', **result}), 400
    return jsonify({**result, 'job_id': job.id, 'job_slug': job.slug, 'fee_rules_verified': bool(job.fee_rules_verified_at)})


@bp.put('/orders/<int:order_id>')
@require_admin
def update_request_fees(order_id):
    admin = get_request_user()
    order = Order.query.filter_by(id=order_id).with_for_update().first_or_404()
    data = request.get_json(silent=True) or {}
    status = str(data.get('official_fee_status') or '').strip().lower()
    if status not in {'known', 'none', 'unconfirmed'}:
        return jsonify({'error': 'Official fee status must be known, none, or unconfirmed.'}), 400
    try:
        assistance = _money(data.get('fee_inr', order.fee_inr or 0), 'assistance fee')
        official = _money(data.get('official_fee_inr'), 'official fee') if status == 'known' else (0.0 if status == 'none' else None)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    if _component_locked(order, 'assistance_fee') and assistance != round(float(order.fee_inr or 0), 2):
        return jsonify({'error': 'The assistance fee cannot be changed after its checkout has been created or paid.'}), 409
    current_official = None if order.official_fee_inr is None else round(float(order.official_fee_inr), 2)
    if _component_locked(order, 'official_fee') and (official != current_official or status != (order.official_fee_status or 'unconfirmed')):
        return jsonify({'error': 'The official fee cannot be changed after its checkout has been created or paid.'}), 409
    previous = {'fee_inr': float(order.fee_inr or 0), 'official_fee_inr': order.official_fee_inr, 'official_fee_status': order.official_fee_status}
    order.fee_inr = assistance
    order.official_fee_inr = official
    order.official_fee_status = status
    db.session.add(AdminAuditLog(admin_id=admin.id, action='request_fee_update', summary=f'Confirmed fees for request {order.order_code}.', details={'order_id': order.id, 'previous': previous, 'new': {'fee_inr': assistance, 'official_fee_inr': official, 'official_fee_status': status}, 'collection_flow': 'assistance_official_or_combined'}))
    db.session.commit()
    total = assistance + (official or 0)
    return jsonify({'message': 'Request fees updated. The client can pay each fee separately or pay both together when both are due.', 'order': order.to_dict(include_admin=True), 'total_payable_inr': round(total, 2)})
