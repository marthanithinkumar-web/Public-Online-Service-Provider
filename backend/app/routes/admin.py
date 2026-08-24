from flask import Blueprint, request, jsonify
from ..models.order import Order
from ..models.user import User
from ..models.order_history import OrderStatusHistory
from ..models.attachment import Attachment
from ..models.grievance import Grievance
from ..models.review import Review
from ..utils.database import db
from ..utils.jwt_handler import decode_token

bp = Blueprint('admin', __name__)

ALLOWED_STATUSES = {
    'New', 'Under Review', 'Documents Required', 'In Progress',
    'Completed', 'Rejected', 'Cancelled'
}
CLOSED_STATUSES = {'Completed', 'Rejected', 'Cancelled'}
TRANSITIONS = {
    'New': {'Under Review', 'Cancelled'},
    'Under Review': {'Documents Required', 'In Progress', 'Rejected', 'Cancelled'},
    'Documents Required': {'Under Review', 'Cancelled'},
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
    user = User.query.get(data.get('user_id'))
    return user if user and user.is_admin else None


def _clean_note(value):
    if value is None:
        return None
    return str(value).strip()[:2000] or None


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

    o = Order.query.get_or_404(order_id)
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
    history = OrderStatusHistory(
        order_id=o.id, previous_status=previous, new_status=status,
        changed_by=user.email, note=note
    )
    db.session.add(history)
    db.session.commit()
    return jsonify({'message': 'Status updated', 'order': o.to_dict(), 'history': history.to_dict()})


@bp.route('/orders/<int:order_id>', methods=['GET'])
def order_detail(order_id):
    user = _require_admin()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    o = Order.query.get_or_404(order_id)
    history = OrderStatusHistory.query.filter_by(order_id=o.id).order_by(OrderStatusHistory.created_at.asc()).all()
    attachments = Attachment.query.filter_by(order_id=o.id).order_by(Attachment.id.asc()).all()
    grievances = Grievance.query.filter_by(order_id=o.id).order_by(Grievance.id.desc()).all()
    reviews = Review.query.filter_by(order_id=o.id).order_by(Review.id.desc()).all()
    return jsonify({
        'order': o.to_dict(),
        'history': [h.to_dict() for h in history],
        'attachments': [a.to_dict() for a in attachments],
        'grievances': [g.to_dict() for g in grievances],
        'reviews': [r.to_dict() for r in reviews],
        'allowed_next_statuses': sorted(TRANSITIONS.get(o.status, set()))
    })


@bp.route('/users', methods=['GET'])
def list_users():
    user = _require_admin()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    users = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).all()
    return jsonify({'items': [u.to_dict() for u in users]})


@bp.route('/services', methods=['GET'])
def admin_list_services():
    user = _require_admin()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    from ..models.service import Service
    services = Service.query.order_by(Service.created_at.desc()).all()
    return jsonify({'items': [s.to_dict() for s in services]})


@bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = _require_admin()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    target = User.query.get_or_404(user_id)
    if target.is_admin:
        return jsonify({'error': 'Cannot delete admin user via this endpoint'}), 403
    orders = Order.query.filter_by(user_id=target.id).all()
    order_ids = [o.id for o in orders]
    attachments = Attachment.query.filter(
        (Attachment.uploaded_by == target.id) |
        (Attachment.order_id.in_(order_ids) if order_ids else False)
    ).all()
    for attachment in attachments:
        db.session.delete(attachment)
    if order_ids:
        OrderStatusHistory.query.filter(OrderStatusHistory.order_id.in_(order_ids)).delete(synchronize_session=False)
        Grievance.query.filter(Grievance.order_id.in_(order_ids)).delete(synchronize_session=False)
        Review.query.filter(Review.order_id.in_(order_ids)).delete(synchronize_session=False)
        Order.query.filter(Order.id.in_(order_ids)).delete(synchronize_session=False)
    db.session.delete(target)
    db.session.commit()
    return jsonify({'message': 'User and associated data deleted'})
