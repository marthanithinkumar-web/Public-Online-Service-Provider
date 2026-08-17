from flask import Blueprint, request, jsonify, current_app
from ..models.user import User
from ..utils.database import db
from ..utils.password import hash_password, verify_password
from ..utils.jwt_handler import create_token, decode_token
from ..utils.limiter import limiter
from ..utils.email import send_email
import os
from datetime import timedelta

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['POST'])
@limiter.limit("6 per minute")
def login():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    if not verify_password(password, user.password_hash):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = create_token({'user_id': user.id, 'is_admin': user.is_admin})
    return jsonify({'token': token, 'user': user.to_dict()})


@bp.route('/register-admin', methods=['POST'])
@limiter.limit("2 per minute")
def register_admin():
    # For initial setup; protected in production
    secret = os.getenv('ADMIN_PASSWORD')
    data = request.json or {}
    if not secret or data.get('admin_secret') != secret:
        return jsonify({'error': 'Forbidden'}), 403

    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'User exists'}), 400

    u = User(email=email, password_hash=hash_password(password), is_admin=True)
    db.session.add(u)
    db.session.commit()
    return jsonify({'message': 'Admin created', 'user': u.to_dict()})


@bp.route('/register', methods=['POST'])
@limiter.limit("4 per minute")
def register():
    # Public client registration (email/password)
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'User exists'}), 400

    u = User(email=email, password_hash=hash_password(password), is_admin=False)
    db.session.add(u)
    db.session.commit()
    token = create_token({'user_id': u.id, 'is_admin': u.is_admin})
    return jsonify({'message': 'User registered', 'token': token, 'user': u.to_dict()})


# Password reset & verification scaffolding
@bp.route('/request-password-reset', methods=['POST'])
@limiter.limit("3 per minute")
def request_password_reset():
    data = request.json or {}
    email = data.get('email')
    if not email:
        return jsonify({'message': 'If that email exists, a reset link will be sent.'}), 200

    user = User.query.filter_by(email=email).first()
    # Always return success to avoid user enumeration
    if not user:
        return jsonify({'message': 'If that email exists, a reset link will be sent.'}), 200

    # create a short-lived token for password reset
    token = create_token({'action': 'password_reset', 'user_id': user.id}, expires_hours=1)

    # build reset link using FRONTEND_URL or localhost
    frontend = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    reset_link = f"{frontend.rstrip('/')}/reset-password?token={token}"
    subject = 'Public Online Service Provider - Password reset'
    body = f"Hello,\n\nA request to reset your password was received. If you made this request, click the link below to reset your password:\n\n{reset_link}\n\nIf you did not request a reset, simply ignore this message.\n\n-- Public Online Service Provider"

    # send email (function handles console fallback if SMTP not configured)
    try:
        send_email(user.email, subject, body)
    except Exception as e:
        current_app.logger.exception('Error sending reset email: %s', e)

    return jsonify({'message': 'If that email exists, a reset link will be sent.'}), 200


@bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json or {}
    token = data.get('token')
    new_password = data.get('new_password')
    if not token or not new_password:
        return jsonify({'error': 'token and new_password required'}), 400
    try:
        payload = decode_token(token)
    except Exception:
        return jsonify({'error': 'Invalid or expired token'}), 400
    if payload.get('action') != 'password_reset':
        return jsonify({'error': 'Invalid token action'}), 400
    user = User.query.get(payload.get('user_id'))
    if not user:
        return jsonify({'error': 'Invalid token'}), 400
    user.password_hash = hash_password(new_password)
    db.session.commit()
    return jsonify({'message': 'Password reset successful'}), 200


@bp.route('/request-verify', methods=['POST'])
def request_verify():
    data = request.json or {}
    email = data.get('email')
    if not email:
        return jsonify({'message': 'If that email exists, a verification link will be sent.'}), 200
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'If that email exists, a verification link will be sent.'}), 200
    token = create_token({'action': 'verify', 'user_id': user.id}, expires_hours=24)

    frontend = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    verify_link = f"{frontend.rstrip('/')}/verify?token={token}"
    subject = 'Public Online Service Provider - Verify your account'
    body = f"Hello,\n\nPlease verify your account by clicking the link below:\n\n{verify_link}\n\nIf you did not create an account, ignore this email.\n\n-- Public Online Service Provider"

    try:
        send_email(user.email, subject, body)
    except Exception as e:
        current_app.logger.exception('Error sending verify email: %s', e)

    return jsonify({'message': 'If that email exists, a verification link will be sent.'}), 200


@bp.route('/verify', methods=['POST'])
def verify_account():
    data = request.json or {}
    token = data.get('token')
    if not token:
        return jsonify({'error': 'token required'}), 400
    try:
        payload = decode_token(token)
    except Exception:
        return jsonify({'error': 'Invalid or expired token'}), 400
    if payload.get('action') != 'verify':
        return jsonify({'error': 'Invalid token action'}), 400
    user = User.query.get(payload.get('user_id'))
    if not user:
        return jsonify({'error': 'Invalid token'}), 400
    # placeholder: mark email verified. Add field if needed. For now, return success
    return jsonify({'message': 'Account verified.'}), 200

