from flask import Blueprint, jsonify, request
from sqlalchemy import func

from ..middleware.auth import require_admin
from ..models.admin_audit import AdminAuditLog
from ..models.notification import Notification
from ..models.support_message import SupportMessage
from ..models.user import User
from ..utils.database import db
from ..utils.jwt_handler import get_request_user
from ..utils.limiter import limiter


bp = Blueprint('messages', __name__)
MAX_MESSAGE_LENGTH = 2000


def _client_user():
    user = get_request_user()
    return user if user and not user.is_admin else None


def _message_text():
    value = str((request.get_json(silent=True) or {}).get('message') or '').strip()
    if not value:
        return None, 'Please enter a message.'
    if len(value) > MAX_MESSAGE_LENGTH:
        return None, f'Messages must be {MAX_MESSAGE_LENGTH} characters or fewer.'
    return value, None


@bp.get('/mine')
def client_messages():
    user = _client_user()
    if not user:
        return jsonify({'error': 'Please log in as a client.'}), 401
    messages = SupportMessage.query.filter_by(user_id=user.id).order_by(SupportMessage.created_at.asc()).all()
    unread = sum(1 for item in messages if item.sender_role == 'admin' and not item.read_by_client)
    return jsonify({'items': [item.to_dict() for item in messages], 'unread': unread})


@bp.post('/mine')
@limiter.limit('12 per minute')
def send_client_message():
    user = _client_user()
    if not user:
        return jsonify({'error': 'Please log in as a client.'}), 401
    value, error = _message_text()
    if error:
        return jsonify({'error': error}), 400
    item = SupportMessage(
        user_id=user.id,
        sender_user_id=user.id,
        sender_role='client',
        message=value,
        read_by_client=True,
        read_by_admin=False,
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'message': 'Your message was sent to the service team.', 'item': item.to_dict()}), 201


@bp.post('/mine/read')
def mark_client_messages_read():
    user = _client_user()
    if not user:
        return jsonify({'error': 'Please log in as a client.'}), 401
    SupportMessage.query.filter_by(user_id=user.id, sender_role='admin', read_by_client=False).update(
        {'read_by_client': True}, synchronize_session=False
    )
    db.session.commit()
    return jsonify({'message': 'Messages marked as read.'})


@bp.get('/admin')
@require_admin
def admin_threads():
    latest = (
        db.session.query(SupportMessage.user_id, func.max(SupportMessage.id).label('latest_id'))
        .group_by(SupportMessage.user_id)
        .subquery()
    )
    rows = (
        db.session.query(User, SupportMessage)
        .join(latest, latest.c.user_id == User.id)
        .join(SupportMessage, SupportMessage.id == latest.c.latest_id)
        .order_by(SupportMessage.created_at.desc())
        .all()
    )
    unread_counts = dict(
        db.session.query(SupportMessage.user_id, func.count(SupportMessage.id))
        .filter(SupportMessage.sender_role == 'client', SupportMessage.read_by_admin.is_(False))
        .group_by(SupportMessage.user_id)
        .all()
    )
    return jsonify({'items': [{
        'user': user.to_dict(),
        'latest_message': message.to_dict(),
        'unread': int(unread_counts.get(user.id, 0)),
    } for user, message in rows]})


@bp.get('/admin/<int:user_id>')
@require_admin
def admin_thread(user_id):
    user = User.query.filter_by(id=user_id, is_admin=False).first_or_404()
    messages = SupportMessage.query.filter_by(user_id=user.id).order_by(SupportMessage.created_at.asc()).all()
    return jsonify({'user': user.to_dict(), 'items': [item.to_dict() for item in messages]})


@bp.post('/admin/<int:user_id>')
@require_admin
@limiter.limit('30 per minute')
def send_admin_message(user_id):
    admin = get_request_user()
    user = User.query.filter_by(id=user_id, is_admin=False, is_active=True).first_or_404()
    value, error = _message_text()
    if error:
        return jsonify({'error': error}), 400
    item = SupportMessage(
        user_id=user.id,
        sender_user_id=admin.id,
        sender_role='admin',
        message=value,
        read_by_client=False,
        read_by_admin=True,
    )
    db.session.add(item)
    db.session.add(Notification(
        user_id=user.id,
        title='New message from support',
        message='The service team replied to your private dashboard message.',
    ))
    db.session.add(AdminAuditLog(
        admin_id=admin.id,
        action='support_message_sent',
        summary=f'Sent a private support reply to client #{user.id}.',
        details={'client_id': user.id},
    ))
    db.session.commit()
    return jsonify({'message': 'Reply sent to the client.', 'item': item.to_dict()}), 201


@bp.post('/admin/<int:user_id>/read')
@require_admin
def mark_admin_messages_read(user_id):
    User.query.filter_by(id=user_id, is_admin=False).first_or_404()
    SupportMessage.query.filter_by(user_id=user_id, sender_role='client', read_by_admin=False).update(
        {'read_by_admin': True}, synchronize_session=False
    )
    db.session.commit()
    return jsonify({'message': 'Client messages marked as read.'})
