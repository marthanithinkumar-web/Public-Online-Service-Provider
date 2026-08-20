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

    name = (user.name or data.get('client_name') or '').strip()
    phone = (user.phone or data.get('phone') or '').strip()
    email = (user.email or data.get('email') or '').strip() or None
    if len(name) < 2 or len(phone) < 7:
        return jsonify({'error': 'Please complete your name and phone number in Account Settings before requesting a service.'}), 400

    application_data = data.get('application_data') or {}
    if not isinstance(application_data, dict) or not application_data:
        return jsonify({'error': 'Please complete the service application before submitting.'}), 400

    # Keep structured application answers in the existing database field so this upgrade is backward compatible.
    description = json.dumps({'application_data': application_data}, ensure_ascii=False)
    order = Order(
        order_code=_generate_order_code(), client_name=name, phone=phone, email=email,
        contact_method=data.get('contact_method'), service=service, user_id=user.id,
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
