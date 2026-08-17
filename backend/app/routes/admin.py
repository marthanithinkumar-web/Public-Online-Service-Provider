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
