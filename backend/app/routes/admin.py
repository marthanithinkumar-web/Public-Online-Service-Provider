from flask import Blueprint, request, jsonify, Response
from sqlalchemy import func, or_
from datetime import datetime, time, timezone
import math
import os
import csv
import io
from ..models.order import Order
from ..models.user import User
from ..models.order_history import OrderStatusHistory
from ..models.attachment import Attachment
from ..models.grievance import Grievance
from ..models.review import Review
from ..models.notification import Notification
from ..models.service import Service, PlatformSetting
from ..models.admin_audit import AdminAuditLog
from ..utils.database import db
from ..utils.jwt_handler import create_token, decode_token
from ..utils.password import hash_password, verify_password
from ..utils.email import send_email
from ..utils.database_manifest import build_database_manifest

bp = Blueprint('admin', __name__)

ALLOWED_STATUSES = {
    'New', 'Submitted', 'Pending', 'Under Review', 'Documents Required', 'In Progress',
    'Completed', 'Rejected', 'Cancelled'
}
CLOSED_STATUSES = {'Completed', 'Rejected', 'Cancelled'}
TRANSITIONS = {
    'New': {'Pending', 'Under Review', 'Cancelled'},
    'Submitted': {'Pending', 'Under Review', 'Cancelled'},
    'Pending': {'Under Review', 'Cancelled'},
    'Under Review': {'Documents Required', 'In Progress', 'Rejected', 'Cancelled'},
    'Documents Required': {'Under Review', 'In Progress', 'Cancelled'},
    'In Progress': {'Documents Required', 'Completed', 'Rejected', 'Cancelled'},
}


def _require_admin():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    try:
        data = decode_token(auth.split(' ', 1)[1])
    except Exception:
        return None
    user = db.session.get(User, data.get('user_id'))
    return user if user and user.is_admin and user.is_active and data.get('token_version', 0) == user.token_version else None


def _clean_note(value):
    if value is None:
        return None
    return str(value).strip()[:2000] or None


def _parse_date(value, end=False):
    if not value:
        return None
    try:
        day = datetime.strptime(value, '%Y-%m-%d').date()
        return datetime.combine(day, time.max if end else time.min)
    except (TypeError, ValueError):
        raise ValueError('Dates must use YYYY-MM-DD format.')


def _filtered_orders(args):
    query = Order.query
    status = args.get('status')
    if status:
        if status not in ALLOWED_STATUSES:
            raise ValueError('Invalid status filter.')
        query = query.filter(Order.status == status)
    date_from = _parse_date(args.get('date_from'))
    date_to = _parse_date(args.get('date_to'), end=True)
    if date_from:
        query = query.filter(Order.created_at >= date_from)
    if date_to:
        query = query.filter(Order.created_at <= date_to)
    return query


@bp.route('/overview', methods=['GET'])
def overview():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    counts = dict(db.session.query(Order.status, func.count(Order.id)).group_by(Order.status).all())
    fee_total = db.session.query(func.coalesce(func.sum(Order.fee_inr), 0)).filter(Order.status == 'Completed').scalar()
    average_rating = db.session.query(func.avg(Review.rating)).scalar()
    recent_history = OrderStatusHistory.query.order_by(OrderStatusHistory.created_at.desc()).limit(12).all()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(8).all()
    return jsonify({
        'counts': {status: int(counts.get(status, 0)) for status in ALLOWED_STATUSES},
        'total_requests': int(sum(counts.values())),
        'completed_fee_total': float(fee_total or 0),
        'open_grievances': Grievance.query.filter(Grievance.status.notin_(['Resolved', 'Closed'])).count(),
        'average_rating': round(float(average_rating or 0), 1),
        'client_count': User.query.filter_by(is_admin=False).count(),
        'service_count': Service.query.count(),
        'recent_orders': [order.to_dict() for order in recent_orders],
        'activity': [item.to_dict() for item in recent_history],
    })

@bp.route('/orders', methods=['GET'])
def list_orders():
    user = _require_admin()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    args = request.args
    status = args.get('status')
    page = args.get('page', 1)
    per_page = args.get('per_page', 20)
    q = Order.query
    if status:
        if status not in ALLOWED_STATUSES:
            return jsonify({'error': 'Invalid status filter.'}), 400
        q = q.filter_by(status=status)
    search = (args.get('q') or '').strip()
    if search:
        pattern = f'%{search}%'
        q = q.join(Service, Order.service_id == Service.id, isouter=True).filter(or_(
            Order.order_code.ilike(pattern), Order.client_name.ilike(pattern),
            Order.phone.ilike(pattern), Order.email.ilike(pattern), Service.name.ilike(pattern)
        ))
    try:
        date_from = _parse_date(args.get('date_from'))
        date_to = _parse_date(args.get('date_to'), end=True)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    if date_from:
        q = q.filter(Order.created_at >= date_from)
    if date_to:
        q = q.filter(Order.created_at <= date_to)
    q = q.order_by(Order.created_at.desc())
    from ..utils.pagination import paginate_query
    res = paginate_query(q, page, per_page)
    return jsonify({'items': [o.to_dict() for o in res['items']], 'meta': res['meta']})


@bp.route('/orders/<int:order_id>/status', methods=['POST'])
def update_status(order_id):
    user = _require_admin()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    status = str(data.get('status') or '').strip()
    note = _clean_note(data.get('note'))
    if status not in ALLOWED_STATUSES:
        return jsonify({'error': 'Invalid request status.'}), 400

    o = db.get_or_404(Order, order_id)
    previous = o.status
    if previous == status:
        return jsonify({'error': 'The request is already in this status.'}), 409
    if previous in CLOSED_STATUSES:
        return jsonify({'error': 'Closed requests cannot be moved to another status.'}), 409
    if status not in TRANSITIONS.get(previous, set()):
        return jsonify({'error': f'Invalid workflow transition: {previous} → {status}.'}), 409
    if status in {'Rejected', 'Cancelled', 'Documents Required'} and not note:
        return jsonify({'error': 'A reason or instruction is required for this status.'}), 400
    if status == 'Completed' and not note:
        return jsonify({'error': 'Add a completion note describing the result delivered to the client.'}), 400

    o.status = status
    o.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    history = OrderStatusHistory(
        order_id=o.id, previous_status=previous, new_status=status,
        changed_by=user.email, note=note
    )
    db.session.add(history)
    if o.user_id:
        message = f'Your request {o.order_code} is now {status}.'
        if note:
            message += f' {note}'
        db.session.add(Notification(user_id=o.user_id, order_id=o.id, title='Request status updated', message=message[:4000]))
    db.session.commit()
    return jsonify({'message': 'Status updated', 'order': o.to_dict(), 'history': history.to_dict()})


@bp.route('/orders/<int:order_id>', methods=['GET'])
def order_detail(order_id):
    user = _require_admin()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    o = db.get_or_404(Order, order_id)
    history = OrderStatusHistory.query.filter_by(order_id=o.id).order_by(OrderStatusHistory.created_at.asc()).all()
    attachments = Attachment.query.filter_by(order_id=o.id).order_by(Attachment.id.asc()).all()
    grievances = Grievance.query.filter_by(order_id=o.id).order_by(Grievance.id.desc()).all()
    reviews = Review.query.filter_by(order_id=o.id).order_by(Review.id.desc()).all()
    return jsonify({
        'order': o.to_dict(),
        'history': [h.to_dict() for h in history],
        'attachments': [a.to_dict('client' if a.uploaded_by == o.user_id else 'admin') for a in attachments],
        'grievances': [g.to_dict() for g in grievances],
        'reviews': [r.to_dict() for r in reviews],
        'allowed_next_statuses': sorted(TRANSITIONS.get(o.status, set()))
    })


@bp.route('/users', methods=['GET'])
def list_users():
    user = _require_admin()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    q = User.query.filter_by(is_admin=False)
    search = (request.args.get('q') or '').strip()
    if search:
        pattern = f'%{search}%'
        q = q.filter(or_(User.name.ilike(pattern), User.email.ilike(pattern), User.phone.ilike(pattern)))
    from ..utils.pagination import paginate_query
    res = paginate_query(q.order_by(User.created_at.desc()), request.args.get('page', 1), request.args.get('per_page', 20))
    items = []
    for item in res['items']:
        data = item.to_dict()
        data['request_count'] = Order.query.filter_by(user_id=item.id).count()
        items.append(data)
    return jsonify({'items': items, 'meta': res['meta']})


@bp.route('/users/<int:user_id>', methods=['GET'])
def user_detail(user_id):
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    target = User.query.filter_by(id=user_id, is_admin=False).first_or_404()
    orders = Order.query.filter_by(user_id=target.id).order_by(Order.created_at.desc()).all()
    return jsonify({'user': target.to_dict(include_service_profile=True), 'orders': [order.to_dict() for order in orders]})


@bp.route('/users/<int:user_id>/active', methods=['POST'])
def set_user_active(user_id):
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    target = User.query.filter_by(id=user_id, is_admin=False).first_or_404()
    data = request.json or {}
    if not isinstance(data.get('active'), bool):
        return jsonify({'error': 'active must be true or false.'}), 400
    target.is_active = data['active']
    target.token_version = (target.token_version or 0) + 1
    db.session.commit()
    action = 'reactivated' if target.is_active else 'suspended'
    return jsonify({'message': f'Client account {action}.', 'user': target.to_dict()})


@bp.route('/services', methods=['GET'])
def admin_list_services():
    user = _require_admin()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    services = Service.query.order_by(Service.created_at.desc()).all()
    return jsonify({'items': [s.to_dict() for s in services]})


@bp.route('/services/assistance-fee', methods=['PUT'])
def update_all_assistance_fees():
    admin = _require_admin()
    if not admin:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    if data.get('confirm') is not True:
        return jsonify({'error': 'Confirm the website-wide fee change before continuing.'}), 400
    try:
        new_fee = round(float(data.get('price_inr')), 2)
    except (TypeError, ValueError):
        return jsonify({'error': 'Enter a valid assistance fee.'}), 400
    if not math.isfinite(new_fee) or new_fee < 0 or new_fee > 100000:
        return jsonify({'error': 'Assistance fee must be between ₹0 and ₹1,00,000.'}), 400

    services = Service.query.all()
    if not services:
        return jsonify({'error': 'No services are available to update.'}), 404
    previous_fees = sorted({float(service.price_inr or 0) for service in services})
    for service in services:
        service.price_inr = new_fee
    setting = db.session.get(PlatformSetting, 'assistance_fee_inr')
    if setting:
        setting.value = f'{new_fee:.2f}'
    else:
        db.session.add(PlatformSetting(key='assistance_fee_inr', value=f'{new_fee:.2f}'))
    audit = AdminAuditLog(
        admin_id=admin.id,
        action='assistance_fee_bulk_update',
        summary=f'Changed the current assistance fee for {len(services)} services to ₹{new_fee:.2f}.',
        details={
            'new_fee_inr': new_fee,
            'affected_services': len(services),
            'previous_fee_values_inr': previous_fees,
            'existing_requests_repriced': False,
        },
    )
    db.session.add(audit)
    db.session.commit()
    return jsonify({
        'message': f'Assistance fee updated to ₹{new_fee:g} across {len(services)} services.',
        'price_inr': new_fee,
        'affected_services': len(services),
        'existing_requests_repriced': False,
        'audit': audit.to_dict(),
    })


@bp.route('/services/homepage-assistance-fee', methods=['GET', 'PUT'])
def homepage_assistance_fee_setting():
    admin = _require_admin()
    if not admin:
        return jsonify({'error': 'Unauthorized'}), 401
    setting = db.session.get(PlatformSetting, 'homepage_assistance_fee_inr')
    if request.method == 'GET':
        try:
            value = float(setting.value) if setting else 30.0
        except (TypeError, ValueError):
            value = 30.0
        return jsonify({'price_inr': max(0.0, value)})

    data = request.json or {}
    try:
        new_fee = round(float(data.get('price_inr')), 2)
    except (TypeError, ValueError):
        return jsonify({'error': 'Enter a valid homepage assistance fee.'}), 400
    if not math.isfinite(new_fee) or new_fee < 0 or new_fee > 100000:
        return jsonify({'error': 'Homepage assistance fee must be between ₹0 and ₹1,00,000.'}), 400
    previous_fee = setting.value if setting else None
    if setting:
        setting.value = f'{new_fee:.2f}'
    else:
        db.session.add(PlatformSetting(key='homepage_assistance_fee_inr', value=f'{new_fee:.2f}'))
    db.session.add(AdminAuditLog(
        admin_id=admin.id,
        action='homepage_assistance_fee_update',
        summary=f'Changed the homepage assistance fee display to ₹{new_fee:.2f}.',
        details={
            'new_fee_inr': new_fee,
            'previous_fee_inr': previous_fee,
            'service_fees_changed': False,
            'existing_requests_repriced': False,
        },
    ))
    db.session.commit()
    return jsonify({
        'message': f'Homepage assistance fee display updated to ₹{new_fee:g}.',
        'price_inr': new_fee,
        'service_fees_changed': False,
        'existing_requests_repriced': False,
    })


@bp.route('/audit', methods=['GET'])
def audit_log():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    from ..utils.pagination import paginate_query
    query = AdminAuditLog.query.order_by(AdminAuditLog.created_at.desc())
    result = paginate_query(query, request.args.get('page', 1), request.args.get('per_page', 20))
    return jsonify({'items': [item.to_dict() for item in result['items']], 'meta': result['meta']})


@bp.route('/documents', methods=['GET'])
def documents():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    q = Attachment.query.order_by(Attachment.created_at.desc())
    from ..utils.pagination import paginate_query
    res = paginate_query(q, request.args.get('page', 1), request.args.get('per_page', 20))
    items = []
    for attachment in res['items']:
        data = attachment.to_dict()
        order = db.session.get(Order, attachment.order_id) if attachment.order_id else None
        data['order_code'] = order.order_code if order else None
        data['client_name'] = order.client_name if order else None
        items.append(data)
    return jsonify({'items': items, 'meta': res['meta']})


@bp.route('/notifications', methods=['POST'])
def send_notification():
    admin = _require_admin()
    if not admin:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    title = (data.get('title') or '').strip()[:200]
    message = (data.get('message') or '').strip()[:4000]
    user_id = data.get('user_id')
    order_id = data.get('order_id')
    if not title or len(message) < 3:
        return jsonify({'error': 'Title and message are required.'}), 400
    target = User.query.filter_by(id=user_id, is_admin=False).first() if user_id else None
    order = db.session.get(Order, order_id) if order_id else None
    if not target and order and order.user_id:
        target = db.session.get(User, order.user_id)
    if not target:
        return jsonify({'error': 'Select a valid client or request.'}), 400
    if order and order.user_id != target.id:
        return jsonify({'error': 'The selected request does not belong to this client.'}), 400
    item = Notification(user_id=target.id, order_id=order.id if order else None, title=title, message=message)
    db.session.add(item)
    db.session.commit()
    if target.email:
        send_email(target.email, f'Public Online Service Provider — {title}', message)
    return jsonify({'message': 'Notification sent.', 'notification': item.to_dict()}), 201


@bp.route('/profile', methods=['GET', 'PUT'])
def profile():
    admin = _require_admin()
    if not admin:
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'GET':
        return jsonify({'user': admin.to_dict()})
    data = request.json or {}
    name = (data.get('name') or '').strip()[:200]
    phone = (data.get('phone') or '').strip()[:50]
    if len(name) < 2:
        return jsonify({'error': 'Admin name is required.'}), 400
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    if new_password:
        if not current_password or not verify_password(current_password, admin.password_hash):
            return jsonify({'error': 'Current password is incorrect.'}), 400
        if len(new_password) < 8:
            return jsonify({'error': 'New password must be at least 8 characters.'}), 400
        admin.password_hash = hash_password(new_password)
        admin.token_version = (admin.token_version or 0) + 1
    admin.name = name
    admin.phone = phone or None
    db.session.commit()
    token = create_token({'user_id': admin.id, 'is_admin': True, 'token_version': admin.token_version})
    return jsonify({'message': 'Admin profile updated.', 'user': admin.to_dict(), 'token': token})


@bp.route('/system-readiness', methods=['GET'])
def system_readiness():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    secret = os.getenv('SECRET_KEY') or ''
    rate_store = os.getenv('RATELIMIT_STORAGE_URI') or 'memory://'
    email_ready = all(os.getenv(key) for key in ('SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASS')) and bool(
        os.getenv('SMTP_FROM_EMAIL') or os.getenv('ADMIN_EMAIL')
    )
    admin_2fa_enabled = os.getenv('ADMIN_2FA_ENABLED') == '1'
    checks = [
        {'key':'database','label':'Database connection','ready':True,'guidance':'Production database is reachable.'},
        {'key':'secret_key','label':'Secure application secret','ready':len(secret) >= 32 and secret not in {'dev-key','change-me-to-a-secure-random-string'},'guidance':'Set a unique SECRET_KEY of at least 32 characters in Render.'},
        {'key':'document_storage','label':'Persistent document storage','ready':bool(os.getenv('S3_BUCKET')),'guidance':'Configure S3_BUCKET and its credentials so uploads survive deployments.'},
        {'key':'email','label':'Password-reset email delivery','ready':email_ready,'guidance':'Configure SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS and a Brevo-verified SMTP_FROM_EMAIL.'},
        {'key':'admin_2fa','label':'Admin two-factor authentication','ready':admin_2fa_enabled and email_ready,'guidance':'Configure SMTP, then set ADMIN_2FA_ENABLED=1.'},
        {'key':'shared_rate_limits','label':'Shared rate-limit storage','ready':bool(rate_store and rate_store != 'memory://'),'guidance':'Configure RATELIMIT_STORAGE_URI with a shared Redis-compatible store for multiple workers.'},
        {'key':'https','label':'HTTPS enforcement','ready':os.getenv('FORCE_HTTPS') == '1','guidance':'Keep FORCE_HTTPS=1 in production.'},
    ]
    return jsonify({'ready': all(item['ready'] for item in checks), 'checks': checks, 'manual_checks': ['Confirm automated database backups and restore instructions.', 'Complete a real password-reset email test.', 'Complete client/admin production journey tests.']})


@bp.route('/database-manifest', methods=['GET'])
def database_manifest():
    """Return an admin-only, credential-free migration verification manifest."""
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(build_database_manifest())


@bp.route('/reports/requests.csv', methods=['GET'])
def request_report():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        orders = _filtered_orders(request.args).order_by(Order.created_at.desc()).all()
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Request ID', 'Client', 'Phone', 'Email', 'Service', 'Status', 'Assistance Fee INR', 'Official Fee Status', 'Official Fee INR', 'Total Payable INR', 'Created'])
    for order in orders:
        writer.writerow([order.order_code, order.client_name, order.phone, order.email or '', order.service.name if order.service else '', order.status, order.fee_inr or 0, order.official_fee_status or 'unconfirmed', order.official_fee_inr if order.official_fee_inr is not None else '', order.total_fee_inr if order.total_fee_inr is not None else '', order.created_at.isoformat()])
    return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=request-report.csv'})


@bp.route('/reports/summary', methods=['GET'])
def report_summary():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        query = _filtered_orders(request.args)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    counts = dict(query.with_entities(Order.status, func.count(Order.id)).group_by(Order.status).all())
    total = int(sum(counts.values()))
    completed_fees = query.with_entities(func.coalesce(func.sum(Order.fee_inr), 0)).filter(Order.status == 'Completed').scalar()
    return jsonify({
        'total': total,
        'counts': {status: int(counts.get(status, 0)) for status in ALLOWED_STATUSES},
        'completed_fee_total': float(completed_fees or 0),
    })
