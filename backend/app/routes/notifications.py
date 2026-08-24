from flask import Blueprint, jsonify, request

from ..models.notification import Notification
from ..models.user import User
from ..utils.database import db
from ..utils.jwt_handler import get_request_user

bp = Blueprint('notifications', __name__)


def _client_user():
    user = get_request_user()
    return user if user and not user.is_admin else None


@bp.get('')
@bp.get('/')
def list_notifications():
    user = _client_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    items = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(100).all()
    return jsonify({'items': [item.to_dict() for item in items], 'unread': sum(not item.is_read for item in items)})


@bp.post('/<int:notification_id>/read')
def mark_read(notification_id):
    user = _client_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    item = Notification.query.filter_by(id=notification_id, user_id=user.id).first_or_404()
    item.is_read = True
    db.session.commit()
    return jsonify({'notification': item.to_dict()})


@bp.post('/read-all')
def mark_all_read():
    user = _client_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    Notification.query.filter_by(user_id=user.id, is_read=False).update({'is_read': True}, synchronize_session=False)
    db.session.commit()
    return jsonify({'message': 'Notifications marked as read.'})
