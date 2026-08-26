from flask import Blueprint, request, jsonify
from ..models.grievance import Grievance, GrievanceHistory
from ..models.order import Order
from ..models.notification import Notification
from ..models.admin_audit import AdminAuditLog
from ..utils.database import db
from ..schemas.grievance_schema import GrievanceCreateSchema, GrievanceSchema
from ..middleware.auth import require_admin
from ..utils.jwt_handler import get_request_user
from datetime import datetime, timezone
from secrets import token_hex

bp = Blueprint('grievances', __name__)

create_schema = GrievanceCreateSchema()
dump_schema = GrievanceSchema()
ALLOWED_STATUSES = {'New', 'Under Review', 'Resolved', 'Closed'}


def _authenticated_user():
    return get_request_user()


def _generate_grievance_code():
    # Random references avoid collisions when two clients submit at once and
    # do not reveal the number of grievances in the system.
    return f"GV-{datetime.now(timezone.utc).year}-{token_hex(5).upper()}"


def _client_history(item):
    data = item.to_dict()
    data.pop('changed_by', None)
    return data


@bp.route('', methods=['POST'])
@bp.route('/', methods=['POST'])
def create_grievance():
    user = _authenticated_user()
    if not user or user.is_admin:
        return jsonify({'error': 'Please log in with a client account.'}), 401
    data = request.json or {}
    errors = create_schema.validate(data)
    if errors:
        return jsonify({'error': errors}), 400

    order_id = data.get('order_id')
    order = db.session.get(Order, order_id) if order_id else None
    if order_id and not order:
        return jsonify({'error': 'The selected request could not be found.'}), 400
    if order and order.user_id != user.id:
        return jsonify({'error': 'You can only raise a grievance for your own request.'}), 403

    code = _generate_grievance_code()
    g = Grievance(
        grievance_code=code,
        user_id=user.id,
        order_id=order.id if order else None,
        client_name=user.name,
        phone=user.phone,
        email=user.email,
        description=data.get('description'),
        status='New'
    )
    db.session.add(g)
    db.session.flush()
    db.session.add(GrievanceHistory(
        grievance_id=g.id, previous_status=None, new_status='New',
        changed_by=user.email, note='Grievance submitted by client.'
    ))
    db.session.commit()
    return jsonify({'message': 'Grievance submitted', 'grievance': dump_schema.dump(g)}), 201


@bp.route('/mine', methods=['GET'])
def my_grievances():
    user = _authenticated_user()
    if not user or user.is_admin:
        return jsonify({'error': 'Please log in with a client account.'}), 401
    items = Grievance.query.filter_by(user_id=user.id).order_by(Grievance.created_at.desc()).limit(100).all()
    payload = []
    for item in items:
        data = dump_schema.dump(item)
        data['history'] = [_client_history(entry) for entry in GrievanceHistory.query.filter_by(grievance_id=item.id).order_by(GrievanceHistory.created_at.asc()).all()]
        data['order_code'] = item.order.order_code if getattr(item, 'order', None) else None
        payload.append(data)
    return jsonify({'items': payload})


@bp.route('/<int:grievance_id>', methods=['GET'])
def grievance_detail(grievance_id):
    user = _authenticated_user()
    if not user or user.is_admin:
        return jsonify({'error': 'Please log in with a client account.'}), 401
    item = Grievance.query.filter_by(id=grievance_id, user_id=user.id).first_or_404()
    data = dump_schema.dump(item)
    data['history'] = [_client_history(entry) for entry in GrievanceHistory.query.filter_by(grievance_id=item.id).order_by(GrievanceHistory.created_at.asc()).all()]
    data['order_code'] = item.order.order_code if getattr(item, 'order', None) else None
    return jsonify({'grievance': data})


@bp.route('/admin', methods=['GET'])
@require_admin
def list_grievances():
    args = request.args
    page = args.get('page', 1)
    per_page = args.get('per_page', 20)
    q = Grievance.query.order_by(Grievance.created_at.desc())
    from ..utils.pagination import paginate_query
    res = paginate_query(q, page, per_page)
    items = dump_schema.dump(res['items'], many=True)
    return jsonify({'items': items, 'meta': res['meta']})


@bp.route('/admin/<int:grievance_id>/status', methods=['POST'])
@require_admin
def update_grievance_status(grievance_id):
    admin = _authenticated_user()
    if not admin or not admin.is_admin:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    status = str(data.get('status') or '').strip()
    response = str(data.get('response') or '').strip()[:4000]
    if status not in ALLOWED_STATUSES:
        return jsonify({'error': 'Choose a valid grievance status.'}), 400
    if status in {'Resolved', 'Closed'} and len(response) < 3:
        return jsonify({'error': 'Add a clear response before resolving or closing the grievance.'}), 400
    g = db.get_or_404(Grievance, grievance_id)
    if g.status == status and (not response or response == (g.admin_response or '')):
        return jsonify({'error': 'No grievance change was provided.'}), 409
    previous = g.status
    g.status = status
    if response:
        g.admin_response = response
    g.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.session.add(GrievanceHistory(
        grievance_id=g.id, previous_status=previous, new_status=status,
        changed_by=admin.email, note=response or f'Status changed to {status}.'
    ))
    db.session.add(Notification(
        user_id=g.user_id, order_id=g.order_id, title='Grievance updated',
        message=(f'Your grievance {g.grievance_code} is now {status}.' + (f' {response}' if response else ''))[:4000]
    ))
    db.session.add(AdminAuditLog(
        admin_id=admin.id, action='grievance_update',
        summary=f'Updated grievance {g.grievance_code} to {status}.',
        details={'grievance_id': g.id, 'previous_status': previous, 'new_status': status, 'response_added': bool(response)},
    ))
    db.session.commit()
    return jsonify({'message': 'Grievance status updated', 'grievance': dump_schema.dump(g)})
