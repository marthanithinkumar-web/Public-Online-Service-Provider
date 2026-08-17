from flask import Blueprint, request, jsonify
from ..models.service import Service, Category
from ..utils.database import db
from ..middleware.auth import require_admin
from ..schemas.service_schema import ServiceSchema

bp = Blueprint('services', __name__)

schema = ServiceSchema()


@bp.route('/', methods=['GET'])
def list_services():
    # Optional filters: category_id
    from flask import request
    category_id = request.args.get('category_id')
    q = Service.query.filter_by(is_active=True)
    if category_id:
        try:
            cid = int(category_id)
            q = q.filter_by(category_id=cid)
        except Exception:
            pass
    services = q.order_by(Service.created_at.desc()).all()
    return jsonify([s.to_dict() for s in services])


@bp.route('/<int:service_id>', methods=['GET'])
def service_detail(service_id):
    s = Service.query.get_or_404(service_id)
    return jsonify(s.to_dict())


@bp.route('/search', methods=['GET'])
def search():
    q = (request.args.get('q') or '').strip()
    if not q:
        services = Service.query.filter_by(is_active=True).limit(20).all()
        return jsonify([s.to_dict() for s in services])

    # simple case-insensitive substring search across name, keywords and category
    term = f"%{q.lower()}%"
    services = Service.query.join(Category, isouter=True).filter(
        (Service.is_active == True) & (
            (Service.name.ilike(term)) | (Service.keywords.ilike(term)) | (Category.name.ilike(term))
        )
    ).limit(50).all()

    return jsonify([s.to_dict() for s in services])


# Admin: create service
@bp.route('/', methods=['POST'])
@require_admin
def create_service():
    data = request.json or {}
    errors = schema.validate(data)
    if errors:
        return jsonify({'error': errors}), 400

    s = Service(
        name=data['name'],
        description=data.get('description'),
        price_inr=data.get('price_inr', 0.0),
        keywords=data.get('keywords'),
        category_id=data.get('category_id')
    )
    db.session.add(s)
    db.session.commit()
    return jsonify({'message': 'Service created', 'service': s.to_dict()})


# Admin: update service
@bp.route('/<int:service_id>', methods=['PUT'])
@require_admin
def update_service(service_id):
    s = Service.query.get_or_404(service_id)
    data = request.json or {}
    errors = schema.validate(data, partial=True)
    if errors:
        return jsonify({'error': errors}), 400

    s.name = data.get('name', s.name)
    s.description = data.get('description', s.description)
    s.price_inr = data.get('price_inr', s.price_inr)
    s.keywords = data.get('keywords', s.keywords)
    s.category_id = data.get('category_id', s.category_id)
    db.session.commit()
    return jsonify({'message': 'Service updated', 'service': s.to_dict()})


# Admin: disable/enable service
@bp.route('/<int:service_id>/active', methods=['POST'])
@require_admin
def set_service_active(service_id):
    s = Service.query.get_or_404(service_id)
    data = request.json or {}
    active = data.get('active')
    if active is None:
        return jsonify({'error': 'active required (true/false)'}), 400
    s.is_active = bool(active)
    db.session.commit()
    return jsonify({'message': 'Service status updated', 'service': s.to_dict()})
