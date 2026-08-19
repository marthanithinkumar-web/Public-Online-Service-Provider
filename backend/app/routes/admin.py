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


def _require_admin():
    from flask import request
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    token = auth.split(' ', 1)[1]
    try:
        data = decode_token(token)
    except Exception:
        return None
    user = User.query.get(data.get('user_id'))
    if not user or not user.is_admin:
        return None
    return user


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
        q = q.filter_by(status=status)
    q = q.order_by(Order.created_at.desc())

    # paginate
    from ..utils.pagination import paginate_query
    res = paginate_query(q, page, per_page)
    items = [o.to_dict() for o in res['items']]
    return jsonify({'items': items, 'meta': res['meta']})


@bp.route('/orders/<int:order_id>/status', methods=['POST'])
def update_status(order_id):
    user = _require_admin()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json or {}
    status = data.get('status')
    note = data.get('note')
    if not status:
        return jsonify({'error': 'status required'}), 400

    o = Order.query.get_or_404(order_id)
    previous = o.status
    o.status = status

    # record history
    history = OrderStatusHistory(
        order_id=o.id,
        previous_status=previous,
        new_status=status,
        changed_by=user.email,
        note=note
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
    # load history, attachments, grievances, reviews
    history = OrderStatusHistory.query.filter_by(order_id=o.id).order_by(OrderStatusHistory.created_at.asc()).all()
    attachments = Attachment.query.filter_by(order_id=o.id).all()
    grievances = Grievance.query.filter_by(order_id=o.id).all()
    reviews = Review.query.filter_by(order_id=o.id).all()

    return jsonify({
        'order': o.to_dict(),
        'history': [h.to_dict() for h in history],
        'attachments': [a.to_dict() for a in attachments],
        'grievances': [g.to_dict() for g in grievances],
        'reviews': [r.to_dict() for r in reviews]
    })


# Admin: list users (clients only)
@bp.route('/users', methods=['GET'])
def list_users():
    user = _require_admin()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    # Only return non-admin (client) users to the admin users UI
    users = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).all()
    items = [u.to_dict() for u in users]
    return jsonify({'items': items})


# Admin: list all services (including disabled)
@bp.route('/services', methods=['GET'])
def admin_list_services():
    user = _require_admin()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    from ..models.service import Service
    services = Service.query.order_by(Service.created_at.desc()).all()
    items = [s.to_dict() for s in services]
    return jsonify({'items': items})


# Admin: delete user
@bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = _require_admin()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    target = User.query.get_or_404(user_id)
    if target.is_admin:
        return jsonify({'error': 'Cannot delete admin user via this endpoint'}), 403

    # remove related orders/grievances/reviews/attachments
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
