from flask import Blueprint, request, jsonify
from ..models.service import Service, Category
from ..utils.database import db
from ..middleware.auth import require_admin
from ..schemas.service_schema import ServiceSchema
from ..utils.service_requirements import get_service_requirements
from sqlalchemy import or_

bp = Blueprint('services', __name__)
schema = ServiceSchema()


def _service_dict(service):
    data = service.to_dict()
    data['requirements'] = get_service_requirements(service)
    return data


@bp.route('/', methods=['GET'])
@bp.route('', methods=['GET'])
def list_services():
    category_id = request.args.get('category_id')
    q = Service.query.filter_by(is_active=True)
    if category_id:
        try:
            q = q.filter_by(category_id=int(category_id))
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid category_id'}), 400
    services = q.order_by(Service.created_at.desc(), Service.name.asc()).all()
    return jsonify([_service_dict(s) for s in services])


@bp.route('/<int:service_id>', methods=['GET'])
def service_detail(service_id):
    s = Service.query.filter_by(id=service_id, is_active=True).first_or_404()
    return jsonify(_service_dict(s))


@bp.route('/search', methods=['GET'])
def search():
    raw = (request.args.get('q') or '').strip()
    if not raw:
        services = Service.query.filter_by(is_active=True).order_by(Service.name.asc()).all()
        return jsonify([_service_dict(s) for s in services])

    tokens = [t for t in raw.replace('-', ' ').replace('/', ' ').split() if t]
    search_terms = list(dict.fromkeys([raw, *tokens]))
    conditions = []
    for term in search_terms:
        pattern = f"%{term}%"
        conditions.extend([
            Service.name.ilike(pattern),
            Service.keywords.ilike(pattern),
            Service.description.ilike(pattern),
            Service.category.has(Category.name.ilike(pattern)),
        ])

    services = (
        Service.query.filter(Service.is_active.is_(True), or_(*conditions))
        .order_by(Service.name.asc()).limit(100).all()
    )
    return jsonify([_service_dict(s) for s in services])


@bp.route('/', methods=['POST'])
@require_admin
def create_service():
    data = request.json or {}
    errors = schema.validate(data)
    if errors:
        return jsonify({'error': errors}), 400
    s = Service(name=data['name'], description=data.get('description'), price_inr=data.get('price_inr', 0.0), keywords=data.get('keywords'), category_id=data.get('category_id'))
    db.session.add(s)
    db.session.commit()
    return jsonify({'message': 'Service created', 'service': _service_dict(s)})


@bp.route('/<int:service_id>', methods=['PUT'])
@require_admin
def update_service(service_id):
    s = db.get_or_404(Service, service_id)
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
    return jsonify({'message': 'Service updated', 'service': _service_dict(s)})


@bp.route('/<int:service_id>/active', methods=['POST'])
@require_admin
def set_service_active(service_id):
    s = db.get_or_404(Service, service_id)
    data = request.json or {}
    active = data.get('active')
    if active is None:
        return jsonify({'error': 'active required (true/false)'}), 400
    s.is_active = bool(active)
    db.session.commit()
    return jsonify({'message': 'Service status updated', 'service': _service_dict(s)})
