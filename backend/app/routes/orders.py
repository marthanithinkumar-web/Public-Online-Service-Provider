from flask import Blueprint, request, jsonify
from ..models.order import Order
from ..models.service import Service
from ..models.user import User
from ..utils.database import db
from datetime import datetime
from ..schemas.order_schema import OrderCreateSchema, OrderSchema
from ..utils.jwt_handler import decode_token

bp = Blueprint('orders', __name__)

create_schema = OrderCreateSchema()
dump_schema = OrderSchema()


def _generate_order_code(db_session):
    # Simple sequential code based on count — replace with robust seq in production
    # db_session is the SQLAlchemy instance; use its session to query
    count = db_session.session.query(Order).count() or 0
    return f"PSP-{datetime.utcnow().year}-{count+1:04d}"


@bp.route('/', methods=['POST'])
def create_order():
    data = request.json or {}
    errors = create_schema.validate(data)
    if errors:
        return jsonify({'error': errors}), 400

    name = data.get('client_name')
    phone = data.get('phone')
    email = data.get('email')
    service_id = data.get('service_id')
    description = data.get('description')

    service = Service.query.get(service_id)
    if not service:
        return jsonify({'error': 'Invalid service'}), 400

    # associate order with authenticated user if token provided
    auth = request.headers.get('Authorization', '')
    user_id = None
    if auth.startswith('Bearer '):
        token = auth.split(' ', 1)[1]
        try:
            payload = decode_token(token)
            user_id = payload.get('user_id')
        except Exception:
            user_id = None

    code = _generate_order_code(db)
    order = Order(
        order_code=code,
        client_name=name,
        phone=phone,
        email=email,
        service=service,
        user_id=user_id,
        description=description,
        fee_inr=service.price_inr or 0.0,
        status='New'
    )
    db.session.add(order)
    db.session.commit()

    return jsonify({'message': 'Request received. We will contact you.', 'order': dump_schema.dump(order)})


@bp.route('/<int:order_id>', methods=['GET'])
def get_order(order_id):
    # Allow admin or client with order_code+phone query to view order
    auth = request.headers.get('Authorization', '')
    is_admin = False
    user_id = None
    if auth.startswith('Bearer '):
        token = auth.split(' ', 1)[1]
        try:
            data = decode_token(token)
            is_admin = data.get('is_admin', False)
            user_id = data.get('user_id')
        except Exception:
            is_admin = False

    o = Order.query.get_or_404(order_id)
    if is_admin:
        return jsonify(dump_schema.dump(o))

    # allow authenticated user to view own orders
    if user_id and o.user_id == user_id:
        return jsonify(dump_schema.dump(o))

    # require order_code and phone to view as client
    order_code = request.args.get('order_code')
    phone = request.args.get('phone')
    if not order_code or not phone:
        return jsonify({'error': 'Unauthorized'}), 401
    if order_code != o.order_code or phone != o.phone:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(dump_schema.dump(o))


@bp.route('/mine', methods=['GET'])
def my_orders():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return jsonify({'error': 'Unauthorized'}), 401
    token = auth.split(' ', 1)[1]
    try:
        data = decode_token(token)
    except Exception:
        return jsonify({'error': 'Unauthorized'}), 401
    user = User.query.get(data.get('user_id'))
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    return jsonify(dump_schema.dump(orders, many=True))
