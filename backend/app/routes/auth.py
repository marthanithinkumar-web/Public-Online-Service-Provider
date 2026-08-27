from flask import Blueprint, request, jsonify, current_app
from ..models.user import User
from ..models.order import Order
from ..models.order_history import OrderStatusHistory
from ..models.attachment import Attachment
from ..models.grievance import Grievance, GrievanceHistory
from ..models.review import Review
from ..models.notification import Notification
from ..models.support_message import SupportMessage
from ..utils.database import db
from ..utils.password import hash_password, verify_password
from ..utils.jwt_handler import create_token, decode_token
from ..utils.limiter import limiter
from ..utils.email import send_email
import os
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import randbelow
from ..models.security import AdminLoginChallenge, RevokedToken

bp = Blueprint('auth', __name__)


def _current_user_from_request():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    token = auth.split(' ', 1)[1]
    try:
        payload = decode_token(token)
    except Exception:
        return None
    user = db.session.get(User, payload.get('user_id'))
    if not user or not user.is_active or payload.get('token_version', 0) != user.token_version:
        return None
    return user


@bp.route('/profile', methods=['GET', 'PUT'])
def client_profile():
    user = _current_user_from_request()
    if not user or user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'GET':
        return jsonify({'user': user.to_dict()})
    data = request.json or {}
    name = (data.get('name') or '').strip()[:200]
    phone = (data.get('phone') or '').strip()[:50]
    email = (data.get('email') or '').strip().lower()[:200]
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    if len(name) < 2 or len(''.join(c for c in phone if c.isdigit())) < 10 or '@' not in email:
        return jsonify({'error': 'Enter a valid name, email and phone number.'}), 400
    sensitive_change = email != user.email or bool(new_password)
    if sensitive_change and (not current_password or not verify_password(current_password, user.password_hash)):
        return jsonify({'error': 'Your current password is required to change email or password.'}), 400
    existing = User.query.filter(User.email == email, User.id != user.id).first()
    if existing:
        return jsonify({'error': 'That email address is already in use.'}), 409
    if new_password and len(new_password) < 8:
        return jsonify({'error': 'New password must be at least 8 characters.'}), 400
    user.name = name;user.phone = phone;user.email = email
    if new_password:
        user.password_hash = hash_password(new_password)
        user.token_version = (user.token_version or 0) + 1
    db.session.commit()
    token = create_token({'user_id': user.id, 'is_admin': False, 'token_version': user.token_version})
    return jsonify({'message': 'Profile updated successfully.', 'user': user.to_dict(), 'token': token})


@bp.route('/login', methods=['POST'])
@limiter.limit("6 per minute")
def login():
    data = request.json or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    if not user.is_active:
        return jsonify({'error': 'This account is suspended. Contact the service administrator.'}), 403

    if not verify_password(password, user.password_hash):
        return jsonify({'error': 'Invalid credentials'}), 401

    if user.is_admin and os.getenv('ADMIN_2FA_ENABLED', '0') == '1':
        code = f'{randbelow(1000000):06d}'
        challenge = AdminLoginChallenge(
            user_id=user.id, code_hash=sha256(code.encode()).hexdigest(),
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=10),
        )
        db.session.add(challenge)
        db.session.commit()
        delivered = send_email(user.email, 'Public Online Service Provider — admin verification code', f'Your administrator verification code is {code}. It expires in 10 minutes.')
        if not delivered:
            db.session.delete(challenge);db.session.commit()
            return jsonify({'error': 'Unable to deliver the administrator verification code.'}), 503
        challenge_token = create_token({'action': 'admin_2fa', 'challenge_id': challenge.id, 'user_id': user.id}, expires_hours=1)
        return jsonify({'requires_2fa': True, 'challenge_token': challenge_token}), 202

    token = create_token({'user_id': user.id, 'is_admin': user.is_admin, 'token_version': user.token_version})
    return jsonify({'token': token, 'user': user.to_dict()})


@bp.route('/verify-admin-2fa', methods=['POST'])
@limiter.limit('6 per minute')
def verify_admin_2fa():
    data = request.json or {}
    try:
        payload = decode_token(data.get('challenge_token') or '')
    except Exception:
        return jsonify({'error': 'Verification session expired. Sign in again.'}), 401
    if payload.get('action') != 'admin_2fa':
        return jsonify({'error': 'Invalid verification session.'}), 401
    challenge = db.session.get(AdminLoginChallenge, payload.get('challenge_id'))
    user = db.session.get(User, payload.get('user_id'))
    if not challenge or not user or not user.is_admin or challenge.used_at or challenge.expires_at < datetime.now(timezone.utc).replace(tzinfo=None) or challenge.attempts >= 5:
        return jsonify({'error': 'Verification session expired. Sign in again.'}), 401
    challenge.attempts += 1
    if sha256(str(data.get('code') or '').encode()).hexdigest() != challenge.code_hash:
        db.session.commit()
        return jsonify({'error': 'Incorrect verification code.'}), 401
    challenge.used_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.session.commit()
    token = create_token({'user_id': user.id, 'is_admin': True, 'token_version': user.token_version})
    return jsonify({'token': token, 'user': user.to_dict()})


@bp.route('/logout', methods=['POST'])
def revoke_logout_token():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return jsonify({'message': 'Signed out.'}), 200
    try:
        payload = decode_token(auth.split(' ', 1)[1])
        expires_at = datetime.fromtimestamp(payload['exp'], timezone.utc).replace(tzinfo=None)
        if payload.get('jti') and not RevokedToken.query.filter_by(jti=payload['jti']).first():
            db.session.add(RevokedToken(jti=payload['jti'], expires_at=expires_at))
            db.session.commit()
    except Exception:
        pass
    return jsonify({'message': 'Signed out.'}), 200


@bp.route('/register-admin', methods=['POST'])
@limiter.limit("2 per minute")
def register_admin():
    return jsonify({'error': 'Public administrator registration is disabled.'}), 404




@bp.route('/register', methods=['POST'])
@limiter.limit("4 per minute")
def register():
    # Public client registration (email/password)
    data = request.json or {}
    name = (data.get('name') or '').strip()
    phone = (data.get('phone') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')
    if not name or not phone or not email or not password:
        return jsonify({'error': 'Name, phone, email and password are required'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters.'}), 400
    if len(email) > 200 or '@' not in email or email.startswith('@') or email.endswith('@'):
        return jsonify({'error': 'Enter a valid email address.'}), 400

    # basic phone validation
    cleaned_phone = ''.join([c for c in phone if c.isdigit()])
    if len(cleaned_phone) < 10:
        return jsonify({'error': 'Invalid phone number'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'An account already exists for this email address.'}), 409

    u = User(name=name, phone=phone, email=email, password_hash=hash_password(password), is_admin=False)
    db.session.add(u)
    db.session.commit()
    token = create_token({'user_id': u.id, 'is_admin': u.is_admin, 'token_version': u.token_version})
    return jsonify({'message': 'User registered', 'token': token, 'user': u.to_dict()})


@bp.route('/delete-account', methods=['DELETE'])
@limiter.limit("3 per hour")
def delete_account():
    """Permanently delete a client account and its client-owned data.

    The current password is required as an explicit confirmation. Admin accounts
    cannot be deleted through this client endpoint. Related orders, grievances,
    reviews, status history, and attachments are removed with the account.
    """
    user = _current_user_from_request()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if user.is_admin:
        return jsonify({'error': 'Admin accounts must be managed separately'}), 403

    data = request.json or {}
    current_password = data.get('current_password')
    if not current_password:
        return jsonify({'error': 'Current password is required'}), 400
    if not verify_password(current_password, user.password_hash):
        return jsonify({'error': 'Current password is incorrect'}), 401

    orders = Order.query.filter_by(user_id=user.id).all()
    active_orders = [order for order in orders if order.status not in {'Completed', 'Rejected', 'Cancelled'}]
    if active_orders:
        return jsonify({
            'error': 'Your account has active requests. Cancel eligible requests or contact the provider before deleting your account.',
            'active_requests': [
                {'id': order.id, 'order_code': order.order_code, 'status': order.status}
                for order in active_orders
            ],
        }), 409
    order_ids = [order.id for order in orders]
    Notification.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    SupportMessage.query.filter(
        (SupportMessage.user_id == user.id) | (SupportMessage.sender_user_id == user.id)
    ).delete(synchronize_session=False)

    grievance_ids = [item.id for item in Grievance.query.filter_by(user_id=user.id).all()]
    if grievance_ids:
        GrievanceHistory.query.filter(GrievanceHistory.grievance_id.in_(grievance_ids)).delete(synchronize_session=False)
        Grievance.query.filter(Grievance.id.in_(grievance_ids)).delete(synchronize_session=False)

    # Remove uploaded files before deleting their attachment records.
    attachments = Attachment.query.filter(
        (Attachment.uploaded_by == user.id) |
        (Attachment.order_id.in_(order_ids) if order_ids else False)
    ).all()
    for attachment in attachments:
        stored_path = attachment.stored_path or ''
        try:
            if stored_path.startswith('s3://'):
                from ..utils.s3 import s3_client
                parts = stored_path.replace('s3://', '', 1).split('/', 1)
                if len(parts) == 2:
                    s3_client().delete_object(Bucket=parts[0], Key=parts[1])
            elif stored_path and os.path.exists(stored_path):
                os.remove(stored_path)
        except Exception:
            current_app.logger.exception('Unable to remove attachment during account deletion: %s', stored_path)
        db.session.delete(attachment)

    if order_ids:
        OrderStatusHistory.query.filter(OrderStatusHistory.order_id.in_(order_ids)).delete(synchronize_session=False)
        legacy_grievance_ids = [item.id for item in Grievance.query.filter(Grievance.order_id.in_(order_ids)).all()]
        if legacy_grievance_ids:
            GrievanceHistory.query.filter(GrievanceHistory.grievance_id.in_(legacy_grievance_ids)).delete(synchronize_session=False)
            Grievance.query.filter(Grievance.id.in_(legacy_grievance_ids)).delete(synchronize_session=False)
        Review.query.filter(Review.order_id.in_(order_ids)).delete(synchronize_session=False)
        Order.query.filter(Order.id.in_(order_ids)).delete(synchronize_session=False)

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'Account and associated client data deleted successfully'}), 200


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
    if len(new_password) < 8:
        return jsonify({'error': 'New password must be at least 8 characters.'}), 400
    try:
        payload = decode_token(token)
    except Exception:
        return jsonify({'error': 'Invalid or expired token'}), 400
    if payload.get('action') != 'password_reset':
        return jsonify({'error': 'Invalid token action'}), 400
    user = db.session.get(User, payload.get('user_id'))
    if not user:
        return jsonify({'error': 'Invalid token'}), 400
    user.password_hash = hash_password(new_password)
    user.token_version = (user.token_version or 0) + 1
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
    user = db.session.get(User, payload.get('user_id'))
    if not user:
        return jsonify({'error': 'Invalid token'}), 400
    # placeholder: mark email verified. Add field if needed. For now, return success
    return jsonify({'message': 'Account verified.'}), 200
