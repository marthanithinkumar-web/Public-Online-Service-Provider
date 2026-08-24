import os
import jwt
from datetime import datetime, timedelta, timezone
from secrets import token_hex
from flask import current_app, has_app_context


def _secret_key():
    return current_app.config['SECRET_KEY'] if has_app_context() else os.getenv('SECRET_KEY', 'dev-key')


def create_token(payload: dict, expires_hours: int = 12) -> str:
    data = payload.copy()
    data.update({
        'exp': datetime.now(timezone.utc) + timedelta(hours=expires_hours),
        'jti': token_hex(16),
    })
    return jwt.encode(data, _secret_key(), algorithm='HS256')


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, _secret_key(), algorithms=['HS256'])
        if has_app_context() and payload.get('jti'):
            from ..models.security import RevokedToken
            if RevokedToken.query.filter_by(jti=payload['jti']).first():
                raise jwt.InvalidTokenError('Token has been revoked')
        return payload
    except jwt.ExpiredSignatureError:
        raise
    except Exception:
        raise


def get_request_user():
    """Return the active user for the current bearer token."""
    from flask import request
    from ..models.user import User
    from .database import db
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    try:
        payload = decode_token(auth.split(' ', 1)[1])
    except Exception:
        return None
    user = db.session.get(User, payload.get('user_id'))
    if not user or not user.is_active:
        return None
    if payload.get('token_version', 0) != (user.token_version or 0):
        return None
    return user
