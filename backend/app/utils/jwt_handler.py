import os
import jwt
from datetime import datetime, timedelta

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key')


def create_token(payload: dict, expires_hours: int = 12) -> str:
    data = payload.copy()
    data.update({
        'exp': datetime.utcnow() + timedelta(hours=expires_hours)
    })
    return jwt.encode(data, SECRET_KEY, algorithm='HS256')


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise
    except Exception:
        raise
