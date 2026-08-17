from functools import wraps
from flask import request, jsonify
from ..utils.jwt_handler import decode_token
from ..models.user import User


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'error': 'Unauthorized'}), 401
        token = auth.split(' ', 1)[1]
        try:
            data = decode_token(token)
        except Exception:
            return jsonify({'error': 'Unauthorized'}), 401
        user = User.query.get(data.get('user_id'))
        if not user or not user.is_admin:
            return jsonify({'error': 'Unauthorized'}), 401
        # attach user to request context if needed
        return f(*args, **kwargs)
    return decorated
