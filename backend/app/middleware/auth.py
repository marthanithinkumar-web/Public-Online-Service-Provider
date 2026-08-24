from functools import wraps
from flask import jsonify
from ..utils.jwt_handler import get_request_user


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_request_user()
        if not user or not user.is_admin:
            return jsonify({'error': 'Unauthorized'}), 401
        # attach user to request context if needed
        return f(*args, **kwargs)
    return decorated
