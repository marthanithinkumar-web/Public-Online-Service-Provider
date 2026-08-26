from flask import Blueprint, request, jsonify
from ..models.grievance import Grievance
from ..models.order import Order
from ..utils.database import db
from ..schemas.grievance_schema import GrievanceCreateSchema, GrievanceSchema
from ..middleware.auth import require_admin
from ..utils.jwt_handler import get_request_user
from datetime import datetime, timezone
from secrets import token_hex

bp = Blueprint('grievances', __name__)

create_schema = GrievanceCreateSchema()
dump_schema = GrievanceSchema()


def _authenticated_user():
    return get_request_user()


def _generate_grievance_code():
    # Random references avoid collisions when two clients submit at once and
    # do not reveal the number of grievances in the system.
    return f"GV-{datetime.now(timezone.utc).year}-{token_hex(5).upper()}"


@bp.route('/', methods=['POST'])
def create_grievance():
    user = _authenticated_user()
    if not user or user.is_admin:
        return jsonify({'error': 'Please log in with a client account.'}), 401
    data = request.json or {}
    errors = create_schema.validate(data)
    if errors:
        return jsonify({'error': errors}), 400

    order_id = data.get('order_id')
    order = db.session.get(Order, order_id) if order_id else None
    if order_id and not order:
        return jsonify({'error': 'The selected request could not be found.'}), 400
    if order and order.user_id != user.id:
        return jsonify({'error': 'You can only raise a grievance for your own request.'}), 403

    code = _generate_grievance_code()
    g = Grievance(
        grievance_code=code,
        order_id=order.id if order else None,
        client_name=user.name,
        phone=user.phone,
        email=user.email,
        description=data.get('description'),
        status='New'
    )
    db.session.add(g)
    db.session.commit()
    return jsonify({'message': 'Grievance submitted', 'grievance': dump_schema.dump(g)}), 201


@bp.route('/admin', methods=['GET'])
@require_admin
def list_grievances():
    args = request.args
    page = args.get('page', 1)
    per_page = args.get('per_page', 20)
    q = Grievance.query.order_by(Grievance.created_at.desc())
    from ..utils.pagination import paginate_query
    res = paginate_query(q, page, per_page)
    items = dump_schema.dump(res['items'], many=True)
    return jsonify({'items': items, 'meta': res['meta']})


@bp.route('/admin/<int:grievance_id>/status', methods=['POST'])
@require_admin
def update_grievance_status(grievance_id):
    data = request.json or {}
    status = data.get('status')
    if not status:
        return jsonify({'error': 'status required'}), 400
    g = db.get_or_404(Grievance, grievance_id)
    g.status = status
    db.session.commit()
    return jsonify({'message': 'Grievance status updated', 'grievance': dump_schema.dump(g)})
