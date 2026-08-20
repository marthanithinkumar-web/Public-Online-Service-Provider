from flask import Blueprint, request, jsonify
from ..models.order import Order
from ..models.service import Service
from ..models.user import User
from ..utils.database import db
from datetime import datetime
from secrets import token_hex
from ..schemas.order_schema import OrderCreateSchema, OrderSchema
from ..utils.jwt_handler import decode_token
import json

bp = Blueprint('orders', __name__)
create_schema = OrderCreateSchema()
dump_schema = OrderSchema()
MAX_APPLICATION_BYTES = 64 * 1024
ALLOWED_CONTACT_METHODS = {'email', 'phone', 'whatsapp'}


def _generate_order_code():
    return f"POSP-{datetime.utcnow().year}-{token_hex(5).upper()}"


def _authenticated_user():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    try:
        payload = decode_token(auth.split(' ', 1)[1])
        return User.query.get(payload.get('user_id'))
    except Exception:
        return None


def _normalise_application(value, depth=0):
    """Allow only JSON-safe, bounded application data before persistence."""
    if depth > 6:
        raise ValueError('Application data is too deeply nested.')
    if isinstance(value, dict):
        if len(value) > 100:
            raise ValueError('Application contains too many fields.')
        return {str(k)[:100]: _normalise_application(v, depth + 1) for k, v in value.items()}
    if isinstance(value, list):
        if len(value) > 100:
            raise ValueError('Application contains too many list items.')
        return [_normalise_application(v, depth + 1) for v in value]
    if isinstance(value, str):
        return value.strip()[:4000]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    raise ValueError('Application contains an unsupported value.')


@bp.route('/', methods=['POST'])
def create_order():
    user = _authenticated_user()
    if not user:
        return jsonify({'error': 'Please log in before requesting a service.'}), 401
    if user.is_admin:
        return jsonify({'error': 'Administrator accounts cannot create client service requests.'}), 403

    data = request.json or {}
    errors = create_schema.validate(data)
    if errors:
        return jsonify({'error': errors}), 400

    service = Service.query.filter_by(id=data.get('service_id'), is_active=True).first()
    if not service:
        return jsonify({'error': 'This service is currently unavailable.'}), 400

    name = (user.name or '').strip()
    phone = (user.phone or '').strip()
    email = (user.email or '').strip() or None
    if len(name) < 2 or len(phone) < 7:
        return jsonify({'error': 'Please complete your name and phone number in Account Settings before requesting a service.'}), 400

    contact_method = (data.get('contact_method') or '').strip().lower() or None
    if contact_method and contact_method not in ALLOWED_CONTACT_METHODS:
        return jsonify({'error': 'Invalid contact method.'}), 400

    try:
        application_data = _normalise_application(data.get('application_data'))
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    if not isinstance(application_data, dict) or not application_data:
        return jsonify({'error': 'Please complete the service application before submitting.'}), 400

    description = json.dumps({'application_data': application_data}, ensure_ascii=False, separators=(',', ':'))
    if len(description.encode('utf-8')) > MAX_APPLICATION_BYTES:
        return jsonify({'error': 'Application information is too large. Please remove unnecessary text and try again.'}), 413

    order = Order(
        order_code=_generate_order_code(), client_name=name, phone=phone, email=email,
        contact_method=contact_method, service=service, user_id=user.id,
        description=description, fee_inr=service.price_inr or 0.0, status='New'
    )
    db.session.add(order)
    db.session.commit()
    return jsonify({'message': 'Your service request has been submitted successfully.', 'order': dump_schema.dump(order)}), 201


@bp.route('/<int:order_id>', methods=['GET'])
def get_order(order_id):
    user = _authenticated_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    order = Order.query.get_or_404(order_id)
    if user.is_admin or order.user_id == user.id:
        return jsonify(dump_schema.dump(order))
    return jsonify({'error': 'Unauthorized'}), 403


@bp.route('/mine', methods=['GET'])
def my_orders():
    user = _authenticated_user()
    if not user or user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 401
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    return jsonify(dump_schema.dump(orders, many=True))
