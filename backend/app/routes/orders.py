from flask import Blueprint, request, jsonify
from ..jobs.fee_rules import assess_official_fee
from ..models.order import Order
from ..models.service import Service, PlatformSetting
from ..models.user import User
from ..models.order_history import OrderStatusHistory
from ..models.attachment import Attachment
from ..models.grievance import Grievance
from ..models.review import Review
from ..models.notification import Notification
from ..models.job import JobNotification
from ..models.payment import Payment
from ..utils.database import db
from datetime import date, datetime, timedelta, timezone
from secrets import token_hex
from ..schemas.order_schema import OrderCreateSchema, OrderSchema
from ..utils.jwt_handler import get_request_user
import json

bp = Blueprint('orders', __name__)
create_schema = OrderCreateSchema()
dump_schema = OrderSchema()
MAX_APPLICATION_BYTES = 64 * 1024
ALLOWED_CONTACT_METHODS = {'email', 'phone', 'whatsapp'}
DUPLICATE_WINDOW_SECONDS = 60
CLIENT_CANCELLABLE_STATUSES = {'New', 'Submitted', 'Pending', 'Documents Required'}
CLIENT_EDITABLE_STATUSES = {'New', 'Submitted', 'Pending', 'Documents Required'}
JOB_ASSISTANCE_CATALOG_NAME = 'Government Job Application Assistance'
JOB_PROTECTED_FIELDS = {
    'job_id', 'job_slug', 'job_title', 'job_organization', 'job_deadline',
    'job_official_notice_url', 'job_application_url', 'job_source', 'job_source_key',
    'job_official_fee', 'job_official_fee_notice_text', 'job_official_fee_assessment',
    'service_name', 'request_mode',
}


def _job_assistance_fee():
    setting = db.session.get(PlatformSetting, 'job_assistance_fee_inr')
    try:
        return max(0.0, float(setting.value)) if setting else 30.0
    except (TypeError, ValueError):
        return 30.0


def _generate_order_code():
    return f"POSP-{datetime.now(timezone.utc).year}-{token_hex(5).upper()}"


def _authenticated_user():
    return get_request_user()


def _client_history_dict(item):
    data = item.to_dict()
    data.pop('changed_by', None)
    return data


def _normalise_application(value, depth=0):
    if depth > 6:
        raise ValueError('Application data is too deeply nested.')
    if isinstance(value, dict):
        if len(value) > 100:
            raise ValueError('Application contains too many fields.')
        return {str(k)[:100]: _normalise_application(v, depth + 1) for k, v in value.items()}
    if isinstance(value, list):
        if len(value) > 100:
            raise ValueError('Application contains too many list items.')
        return [_normalise_application(v, depth + 1) for v in value]
    if isinstance(value, str):
        return value.strip()[:4000]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    raise ValueError('Application contains an unsupported value.')


def _bind_verified_job_context(service, application_data):
    if service.name != JOB_ASSISTANCE_CATALOG_NAME:
        return None
    job_slug = str(application_data.get('job_slug') or '').strip()
    if not job_slug:
        return None
    job = JobNotification.query.filter(
        JobNotification.slug == job_slug,
        JobNotification.status == 'published',
        (JobNotification.deadline.is_(None) | (JobNotification.deadline >= date.today())),
    ).first()
    if not job:
        raise ValueError('The selected official job notice is unavailable or has closed. Choose a current job notice and try again.')
    application_data.update({
        'job_id': job.id,
        'job_slug': job.slug,
        'job_title': job.title,
        'job_organization': job.organization,
        'job_deadline': job.deadline.isoformat() if job.deadline else None,
        'job_official_notice_url': job.official_notice_url,
        'job_application_url': job.application_url,
        'job_source': job.source.name if job.source else None,
        'job_source_key': job.source.key if job.source else None,
        'job_official_fee': job.application_fee,
        'job_official_fee_notice_text': job.application_fee,
    })
    return job


def _official_payment_locked(order):
    return Payment.query.filter(
        Payment.order_id == order.id,
        Payment.purpose.in_(['official_fee', 'request_total']),
        Payment.status.in_(['created', 'authorized', 'captured', 'paid']),
    ).first() is not None


def _notify_admins_application_edited(order, client, changed_fields):
    admins = User.query.filter_by(is_admin=True).all()
    field_text = ', '.join(changed_fields[:12]) if changed_fields else 'application details'
    for admin in admins:
        db.session.add(Notification(
            user_id=admin.id,
            order_id=order.id,
            title='Application edited by Client',
            message=f'{client.name} edited request {order.order_code}. Updated: {field_text}. Open the application to review the latest details.',
        ))


@bp.route('/', methods=['POST'])
def create_order():
    user = _authenticated_user()
    if not user:
        return jsonify({'error': 'Please log in before requesting a service.'}), 401
    if user.is_admin:
        return jsonify({'error': 'Administrator accounts cannot create client service requests.'}), 403
    data = request.get_json(silent=True) or {}
    errors = create_schema.validate(data)
    if errors:
        return jsonify({'error': errors}), 400
    service = Service.query.filter_by(id=data.get('service_id'), is_active=True).first()
    if not service:
        return jsonify({'error': 'This service is currently unavailable.'}), 400
    name = (user.name or '').strip(); phone = (user.phone or '').strip(); email = (user.email or '').strip() or None
    if len(name) < 2 or len(phone) < 7:
        return jsonify({'error': 'Please complete your name and phone number in Account Settings before requesting a service.'}), 400
    contact_method = (data.get('contact_method') or '').strip().lower() or None
    if contact_method and contact_method not in ALLOWED_CONTACT_METHODS:
        return jsonify({'error': 'Invalid contact method.'}), 400
    try:
        application_data = _normalise_application(data.get('application_data') or {})
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    if not isinstance(application_data, dict):
        return jsonify({'error': 'Application information must use named fields.'}), 400
    application_data.setdefault('service_name', service.name)
    application_data.setdefault('request_mode', 'express' if len(application_data) == 1 else 'guided')
    try:
        selected_job = _bind_verified_job_context(service, application_data)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 409
    official_fee_inr = service.official_fee_inr
    official_fee_status = service.official_fee_status or 'unconfirmed'
    if selected_job:
        assessment = assess_official_fee(selected_job, application_data)
        if assessment['status'] == 'missing_factors':
            return jsonify({'error': 'Complete the fee-determining details required by this official notification before submitting.', 'missing_fee_factors': assessment.get('missing') or []}), 400
        if assessment['status'] == 'known':
            official_fee_inr = assessment['amount_inr']; official_fee_status = 'none' if float(official_fee_inr or 0) == 0 else 'known'
            application_data['job_official_fee_assessment'] = {'status': official_fee_status, 'amount_inr': official_fee_inr, 'matched_rule': assessment.get('matched_rule'), 'verified_rules': True}
        else:
            official_fee_inr = None; official_fee_status = 'unconfirmed'
            application_data['job_official_fee_assessment'] = {'status': 'unconfirmed', 'amount_inr': None, 'reason': 'No verified automatic rule matched; admin confirmation is required before payment.', 'verified_rules': bool(selected_job.fee_rules_verified_at)}
    description = json.dumps({'application_data': application_data}, ensure_ascii=False, separators=(',', ':'))
    if len(description.encode('utf-8')) > MAX_APPLICATION_BYTES:
        return jsonify({'error': 'Application information is too large. Please remove unnecessary text and try again.'}), 413
    recent_cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=DUPLICATE_WINDOW_SECONDS)
    duplicate = Order.query.filter(Order.user_id == user.id, Order.service_id == service.id, Order.description == description, Order.created_at >= recent_cutoff).order_by(Order.created_at.desc()).first()
    if duplicate:
        first_order = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.asc(), Order.id.asc()).first()
        order_data = dump_schema.dump(duplicate)
        order_data['can_submit_feedback'] = bool(first_order and first_order.id == duplicate.id and not Review.query.join(Order, Review.order_id == Order.id).filter(Order.user_id == user.id).first())
        return jsonify({'message': 'This request was already submitted recently.', 'duplicate': True, 'order': order_data}), 200
    fee_inr = _job_assistance_fee() if selected_job else (service.price_inr or 0.0)
    order = Order(order_code=_generate_order_code(), client_name=name, phone=phone, email=email, contact_method=contact_method, service=service, user_id=user.id, description=description, fee_inr=fee_inr, official_fee_inr=official_fee_inr, official_fee_status=official_fee_status, status='Submitted')
    db.session.add(order); db.session.flush()
    history_note = 'Official job application assistance requested by client.' if selected_job else 'Application submitted by client.'
    db.session.add(OrderStatusHistory(order_id=order.id, previous_status=None, new_status='Submitted', changed_by=user.email, note=history_note))
    db.session.commit()
    order_data = dump_schema.dump(order); order_data['can_submit_feedback'] = Order.query.filter_by(user_id=user.id).count() == 1
    return jsonify({'message': 'Your service request has been submitted successfully.', 'order': order_data}), 201


@bp.route('/<int:order_id>', methods=['GET'])
def get_order(order_id):
    user = _authenticated_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    order = db.get_or_404(Order, order_id)
    if not user.is_admin and order.user_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    history = OrderStatusHistory.query.filter_by(order_id=order.id).order_by(OrderStatusHistory.created_at.asc()).all()
    attachments = Attachment.query.filter_by(order_id=order.id).order_by(Attachment.id.asc()).all()
    grievances = Grievance.query.filter_by(order_id=order.id).order_by(Grievance.id.desc()).all()
    reviews = Review.query.filter_by(order_id=order.id).order_by(Review.id.desc()).all()
    notifications = Notification.query.filter_by(user_id=order.user_id, order_id=order.id).order_by(Notification.created_at.desc()).all()
    return jsonify({'order': dump_schema.dump(order), 'history': [h.to_dict() if user.is_admin else _client_history_dict(h) for h in history], 'attachments': [a.to_dict('client' if a.uploaded_by == order.user_id else 'admin') for a in attachments], 'grievances': [g.to_dict() for g in grievances], 'reviews': [r.to_dict() for r in reviews], 'notifications': [n.to_dict() for n in notifications]})


@bp.route('/mine', methods=['GET'])
def my_orders():
    user = _authenticated_user()
    if not user or user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 401
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    return jsonify(dump_schema.dump(orders, many=True))


@bp.route('/<int:order_id>', methods=['PUT'])
def edit_order(order_id):
    user = _authenticated_user()
    if not user or user.is_admin:
        return jsonify({'error': 'Please log in as a client.'}), 401
    order = Order.query.filter_by(id=order_id).with_for_update().first_or_404()
    if order.user_id != user.id:
        return jsonify({'error': 'You can edit only your own request.'}), 403
    if order.status not in CLIENT_EDITABLE_STATUSES:
        return jsonify({'error': 'This application can no longer be edited directly. Contact the admin for help.', 'status': order.status}), 409
    body = request.get_json(silent=True) or {}
    try:
        incoming = _normalise_application(body.get('application_data') or {})
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    if not isinstance(incoming, dict):
        return jsonify({'error': 'Application information must use named fields.'}), 400
    current = dict(order.application_data or {})
    edited = dict(current)
    changed = []
    for key, value in incoming.items():
        if key in JOB_PROTECTED_FIELDS:
            continue
        if edited.get(key) != value:
            edited[key] = value
            changed.append(key)
    for key in list(edited):
        if key in JOB_PROTECTED_FIELDS:
            continue
        if key not in incoming and key in current:
            edited.pop(key, None)
            changed.append(key)
    if not changed:
        return jsonify({'message': 'No application details changed.', 'order': dump_schema.dump(order)})
    selected_job = None
    if order.service and order.service.name == JOB_ASSISTANCE_CATALOG_NAME and current.get('job_slug'):
        edited['job_slug'] = current['job_slug']
        try:
            selected_job = _bind_verified_job_context(order.service, edited)
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 409
    if selected_job:
        assessment = assess_official_fee(selected_job, edited)
        if assessment['status'] == 'missing_factors':
            return jsonify({'error': 'Complete all fee-determining details before saving this job application edit.', 'missing_fee_factors': assessment.get('missing') or []}), 400
        if assessment['status'] == 'known':
            new_official = round(float(assessment['amount_inr'] or 0), 2)
            new_status = 'none' if new_official == 0 else 'known'
            current_official = None if order.official_fee_inr is None else round(float(order.official_fee_inr), 2)
            if _official_payment_locked(order) and (new_official != current_official or new_status != order.official_fee_status):
                return jsonify({'error': 'This edit would change an official fee whose payment has already started. Contact the admin to update the application safely.'}), 409
            order.official_fee_inr = new_official; order.official_fee_status = new_status
            edited['job_official_fee_assessment'] = {'status': new_status, 'amount_inr': new_official, 'matched_rule': assessment.get('matched_rule'), 'verified_rules': True}
        elif not _official_payment_locked(order):
            order.official_fee_inr = None; order.official_fee_status = 'unconfirmed'
            edited['job_official_fee_assessment'] = {'status': 'unconfirmed', 'amount_inr': None, 'reason': 'Edited application requires admin fee confirmation.', 'verified_rules': bool(selected_job.fee_rules_verified_at)}
    description = json.dumps({'application_data': edited}, ensure_ascii=False, separators=(',', ':'))
    if len(description.encode('utf-8')) > MAX_APPLICATION_BYTES:
        return jsonify({'error': 'Application information is too large. Please remove unnecessary text and try again.'}), 413
    order.description = description
    order.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    readable = [key.replace('_', ' ') for key in sorted(set(changed))]
    db.session.add(OrderStatusHistory(order_id=order.id, previous_status=order.status, new_status=order.status, changed_by=user.email, note='Application details edited by client.'))
    _notify_admins_application_edited(order, user, readable)
    db.session.commit()
    return jsonify({'message': 'Application details updated. The admin has been notified automatically.', 'order': dump_schema.dump(order), 'changed_fields': readable})


@bp.route('/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    user = _authenticated_user()
    if not user or user.is_admin:
        return jsonify({'error': 'Please log in as a client.'}), 401
    order = Order.query.filter_by(id=order_id).with_for_update().first_or_404()
    if order.user_id != user.id:
        return jsonify({'error': 'You can cancel only your own request.'}), 403
    if order.status not in CLIENT_CANCELLABLE_STATUSES:
        return jsonify({'error': 'This request can no longer be cancelled directly. Contact the provider or submit a grievance for help.', 'status': order.status}), 409
    data = request.get_json(silent=True) or {}
    reason = str(data.get('reason') or 'Cancelled by the client before processing.').strip()[:500]
    previous = order.status
    order.status = 'Cancelled'; order.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.session.add(OrderStatusHistory(order_id=order.id, previous_status=previous, new_status='Cancelled', changed_by=user.email, note=reason or 'Cancelled by the client before processing.'))
    db.session.add(Notification(user_id=user.id, order_id=order.id, title='Request cancelled', message=f'Your request {order.order_code} was cancelled. No further processing will take place.'))
    db.session.commit()
    return jsonify({'message': 'Your request has been cancelled.', 'order': dump_schema.dump(order)})
