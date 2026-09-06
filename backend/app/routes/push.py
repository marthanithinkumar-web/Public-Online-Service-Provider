import os

from flask import Blueprint, jsonify, request

from ..models.push_subscription import PushSubscription
from ..models.user import User
from ..utils.database import db
from ..utils.jwt_handler import decode_token

bp = Blueprint('push', __name__)


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


@bp.get('/public-key')
def public_key():
    key = (os.getenv('WEB_PUSH_VAPID_PUBLIC_KEY') or '').strip()
    return jsonify({'enabled': bool(key), 'public_key': key})


@bp.post('/subscribe')
def subscribe():
    admin = _require_admin()
    if not admin:
        return jsonify({'error': 'Admin access required'}), 403
    payload = request.get_json(silent=True) or {}
    endpoint = str(payload.get('endpoint') or '').strip()
    keys = payload.get('keys') or {}
    p256dh = str(keys.get('p256dh') or '').strip()
    auth_key = str(keys.get('auth') or '').strip()
    if not endpoint.startswith('https://') or not p256dh or not auth_key:
        return jsonify({'error': 'Invalid push subscription'}), 400
    row = PushSubscription.query.filter_by(endpoint=endpoint).first()
    if row is None:
        row = PushSubscription(user_id=admin.id, endpoint=endpoint, p256dh=p256dh, auth=auth_key)
        db.session.add(row)
    else:
        row.user_id = admin.id
        row.p256dh = p256dh
        row.auth = auth_key
    db.session.commit()
    return jsonify({'subscribed': True})


@bp.delete('/subscribe')
def unsubscribe():
    admin = _require_admin()
    if not admin:
        return jsonify({'error': 'Admin access required'}), 403
    endpoint = str((request.get_json(silent=True) or {}).get('endpoint') or '').strip()
    if endpoint:
        PushSubscription.query.filter_by(user_id=admin.id, endpoint=endpoint).delete()
        db.session.commit()
    return jsonify({'subscribed': False})
