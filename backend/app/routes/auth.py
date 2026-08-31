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
from ..utils.validation import normalize_email, normalize_indian_mobile
from ..utils.s3 import delete_stored_file
import os
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from secrets import randbelow
from ..models.security import AdminLoginChallenge, RevokedToken

bp = Blueprint('auth', __name__)


def _optional_text(data, key, limit):
    value = str(data.get(key) or '').strip()
    return value[:limit] or None


def _update_optional_service_profile(user, data):
    raw_dob = str(data.get('date_of_birth') or '').strip()
    if raw_dob:
        try:
            parsed_dob = date.fromisoformat(raw_dob)
        except ValueError:
            raise ValueError('Date of birth must use YYYY-MM-DD format.')
        if parsed_dob > date.today() or parsed_dob.year < 1900:
            raise ValueError('Enter a valid date of birth.')
        user.date_of_birth = parsed_dob
    else:
        user.date_of_birth = None

    raw_postal_code = str(data.get('postal_code') or '').strip()
    if raw_postal_code and (len(raw_postal_code) != 6 or not raw_postal_code.isdigit()):
        raise ValueError('PIN code must contain exactly 6 digits.')

    raw_alternate_phone = str(data.get('alternate_phone') or '').strip()
    alternate_phone = normalize_indian_mobile(raw_alternate_phone) if raw_alternate_phone else None
    if raw_alternate_phone and not alternate_phone:
        raise ValueError('Enter a valid alternate Indian mobile number.')

    raw_alternate_email = str(data.get('alternate_email') or '').strip()
    alternate_email = normalize_email(raw_alternate_email) if raw_alternate_email else None
    if raw_alternate_email and not alternate_email:
        raise ValueError('Enter a valid alternate email address.')

    user.gender = _optional_text(data, 'gender', 50)
    user.guardian_name = _optional_text(data, 'guardian_name', 200)
    user.preferred_language = _optional_text(data, 'preferred_language', 50)
    user.occupation = _optional_text(data, 'occupation', 120)
    user.education_qualification = _optional_text(data, 'education_qualification', 150)
    user.address_line = _optional_text(data, 'address_line', 300)
    user.city = _optional_text(data, 'city', 120)
    user.district = _optional_text(data, 'district', 120)
    user.state = _optional_text(data, 'state', 120)
    user.postal_code = raw_postal_code or None
    user.alternate_phone = alternate_phone
    user.alternate_email = alternate_email
    user.accessibility_needs = _optional_text(data, 'accessibility_needs', 500)
    user.service_notes = _optional_text(data, 'service_notes', 1000)
    user.profile_updated_at = datetime.now(timezone.utc).replace(tzinfo=None)


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
        return jsonify({'user': user.to_dict(include_service_profile=True)})
    data = request.json or {}
    name = (data.get('name') or '').strip()[:200]
    phone = normalize_indian_mobile(data.get('phone'))
    email = normalize_email(data.get('email'))
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    if len(name) < 2:
        return jsonify({'error': 'Enter a valid name.'}), 400
    if not phone:
        return jsonify({'error': 'Enter a valid Indian mobile number.'}), 400
    if not email:
        return jsonify({'error': 'Enter a valid email address.'}), 400
    sensitive_change = email != user.email or bool(new_password)
    if sensitive_change and (not current_password or not verify_password(current_password, user.password_hash)):
        return jsonify({'error': 'Your current password is required to change email or password.'}), 400
    existing = User.query.filter(User.email == email, User.id != user.id).first()
    if existing:
        return jsonify({'error': 'That email address is already in use.'}), 409
    existing_phone = User.query.filter(User.phone == phone, User.id != user.id).first()
    if existing_phone:
        return jsonify({'error': 'That mobile number is already in use.'}), 409
    if new_password and len(new_password) < 8:
        return jsonify({'error': 'New password must be at least 8 characters.'}), 400
    if 'service_profile' in data:
        try:
            _update_optional_service_profile(user, data.get('service_profile') or {})
        except ValueError as exc:
            db.session.rollback()
            return jsonify({'error': str(exc)}), 400
    email_changed = email != user.email
    user.name = name;user.phone = phone;user.email = email
    if new_password:
        user.password_hash = hash_password(new_password)
    if email_changed or new_password:
        user.token_version = (user.token_version or 0) + 1
    # Client email activation has been removed. Keep the legacy column true so
    # the deployed schema remains backwards compatible without a data migration.
    user.email_verified = True
    db.session.commit()
    token = create_token({'user_id': user.id, 'is_admin': False, 'token_version': user.token_version})
    return jsonify({'message': 'Profile updated successfully.', 'user': user.to_dict(include_service_profile=True), 'token': token})


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
    phone = normalize_indian_mobile(data.get('phone'))
    email = normalize_email(data.get('email'))
    password = data.get('password')
    if not name or not data.get('phone') or not data.get('email') or not password:
        return jsonify({'error': 'Name, phone, email and password are required'}), 400
    if len(name) < 2 or len(name) > 200:
        return jsonify({'error': 'Name must be between 2 and 200 characters.'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters.'}), 400
    if not email:
        return jsonify({'error': 'Enter a valid email address.'}), 400
    if not phone:
        return jsonify({'error': 'Enter a valid Indian mobile number.'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'An account already exists for this email address.'}), 409
    if User.query.filter_by(phone=phone).first():
        return jsonify({'error': 'An account already exists for this mobile number.'}), 409

    u = User(name=name, phone=phone, email=email, password_hash=hash_password(password), is_admin=False, email_verified=True)
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

    # Remove stored objects first. If private storage is unavailable, retain all
    # database records so cleanup can be retried instead of orphaning documents.
    attachments = Attachment.query.filter(
        (Attachment.uploaded_by == user.id) |
        (Attachment.order_id.in_(order_ids) if order_ids else False)
    ).all()
    try:
        for attachment in attachments:
            delete_stored_file(attachment.stored_path)
    except Exception:
        db.session.rollback()
        current_app.logger.exception('Unable to remove attachment during account deletion: %s', attachment.stored_path)
        return jsonify({'error': 'Document storage is temporarily unavailable. Your account and records were not deleted; please try again.'}), 503
    for attachment in attachments:
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


# Password reset and account verification
@bp.route('/request-password-reset', methods=['POST'])
@limiter.limit("3 per minute")
def request_password_reset():
    data = request.json or {}
    email = normalize_email(data.get('email'))
    account_type = 'admin' if data.get('account_type') == 'admin' else 'client'
    generic_message = 'If that account exists, a reset link will be sent.'
    if not email:
        return jsonify({'message': generic_message}), 200

    user = User.query.filter_by(email=email, is_admin=(account_type == 'admin')).first()
    # Always return success to avoid user enumeration
    if not user:
        return jsonify({'message': generic_message}), 200

    # create a short-lived token for password reset
    token = create_token({
        'action': 'password_reset',
        'user_id': user.id,
        'token_version': user.token_version,
        'account_type': account_type,
    }, expires_hours=1)

    # build reset link using FRONTEND_URL or localhost
    frontend = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    reset_link = f"{frontend.rstrip('/')}/reset-password?token={token}&account={account_type}"
    subject = 'Public Online Service Provider - Password reset'
    body = f"Hello,\n\nA request to reset your password was received. If you made this request, click the link below to reset your password:\n\n{reset_link}\n\nIf you did not request a reset, simply ignore this message.\n\n-- Public Online Service Provider"

    # send email (function handles console fallback if SMTP not configured)
    delivered = False
    try:
        delivered = send_email(user.email, subject, body)
    except Exception as e:
        current_app.logger.exception('Error sending reset email: %s', e)
    if not delivered:
        current_app.logger.error('Password-reset email delivery failed for account type %s', account_type)

    return jsonify({'message': generic_message}), 200


@bp.route('/reset-password', methods=['POST'])
@limiter.limit('6 per hour')
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
    if not user or payload.get('token_version') != user.token_version:
        return jsonify({'error': 'Invalid token'}), 400
    account_type = 'admin' if user.is_admin else 'client'
    if payload.get('account_type') != account_type:
        return jsonify({'error': 'Invalid token'}), 400
    user.password_hash = hash_password(new_password)
    user.token_version = (user.token_version or 0) + 1
    db.session.commit()
    return jsonify({
        'message': 'Password reset successful',
        'login_path': '/admin/login' if user.is_admin else '/login',
    }), 200
