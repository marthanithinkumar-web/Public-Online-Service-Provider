from flask import Blueprint, request, jsonify
from ..models.grievance import Grievance
from ..models.order import Order
from ..utils.database import db
from ..schemas.grievance_schema import GrievanceCreateSchema, GrievanceSchema
from ..middleware.auth import require_admin
from datetime import datetime

bp = Blueprint('grievances', __name__)

create_schema = GrievanceCreateSchema()
dump_schema = GrievanceSchema()


def _generate_grievance_code(db_session):
    # db_session is the SQLAlchemy object; use its session to query
    count = db_session.session.query(Grievance).count() or 0
    return f"GV-{datetime.utcnow().year}-{count+1:04d}"


@bp.route('/', methods=['POST'])
def create_grievance():
    data = request.json or {}
    errors = create_schema.validate(data)
    if errors:
        return jsonify({'error': errors}), 400

    order_id = data.get('order_id')
    if order_id:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Invalid order_id'}), 400

    code = _generate_grievance_code(db)
    g = Grievance(
        grievance_code=code,
        order_id=order_id,
        client_name=data['client_name'],
        phone=data['phone'],
        email=data.get('email'),
        description=data.get('description'),
        status='New'
    )
    db.session.add(g)
    db.session.commit()
    return jsonify({'message': 'Grievance submitted', 'grievance': dump_schema.dump(g)})


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
    g = Grievance.query.get_or_404(grievance_id)
    g.status = status
    db.session.commit()
    return jsonify({'message': 'Grievance status updated', 'grievance': dump_schema.dump(g)})
