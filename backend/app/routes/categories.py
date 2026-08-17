from flask import Blueprint, request, jsonify
from ..models.service import Category
from ..utils.database import db
from ..middleware.auth import require_admin

bp = Blueprint('categories', __name__)


@bp.route('/', methods=['GET'])
def list_categories():
    cats = Category.query.order_by(Category.name).all()
    return jsonify([{'id':c.id, 'name':c.name} for c in cats])


@bp.route('/', methods=['POST'])
@require_admin
def create_category():
    data = request.json or {}
    name = data.get('name')
    if not name:
        return jsonify({'error': 'name required'}), 400
    if Category.query.filter_by(name=name).first():
        return jsonify({'error': 'category exists'}), 400
    c = Category(name=name)
    db.session.add(c)
    db.session.commit()
    return jsonify({'message': 'Category created', 'category': {'id':c.id, 'name':c.name}})


@bp.route('/<int:cat_id>', methods=['PUT'])
@require_admin
def update_category(cat_id):
    c = Category.query.get_or_404(cat_id)
    data = request.json or {}
    name = data.get('name')
    if not name:
        return jsonify({'error': 'name required'}), 400
    c.name = name
    db.session.commit()
    return jsonify({'message': 'Category updated', 'category': {'id':c.id, 'name':c.name}})


@bp.route('/<int:cat_id>', methods=['DELETE'])
@require_admin
def delete_category(cat_id):
    c = Category.query.get_or_404(cat_id)
    # soft-delete: do not remove, but prevent use. For now, just delete if no services
    db.session.delete(c)
    db.session.commit()
    return jsonify({'message': 'Category deleted'})
