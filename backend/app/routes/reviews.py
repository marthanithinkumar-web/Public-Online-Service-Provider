from flask import Blueprint, request, jsonify
from ..models.review import Review
from ..models.order import Order
from ..utils.database import db
from ..schemas.review_schema import ReviewCreateSchema, ReviewSchema
from ..middleware.auth import require_admin

bp = Blueprint('reviews', __name__)

create_schema = ReviewCreateSchema()
dump_schema = ReviewSchema()


@bp.route('/', methods=['POST'])
def create_review():
    data = request.json or {}
    errors = create_schema.validate(data)
    if errors:
        return jsonify({'error': errors}), 400

    order_id = data.get('order_id')
    if order_id:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Invalid order_id'}), 400

    r = Review(
        order_id=order_id,
        rating=data['rating'],
        comment=data.get('comment'),
        client_name=data.get('client_name'),
        is_public=False  # default false; admin can make it public
    )
    db.session.add(r)
    db.session.commit()
    return jsonify({'message': 'Review submitted', 'review': dump_schema.dump(r)})


@bp.route('/public', methods=['GET'])
def public_reviews():
    reviews = Review.query.filter_by(is_public=True).order_by(Review.created_at.desc()).limit(20).all()
    return jsonify(dump_schema.dump(reviews, many=True))


# Admin endpoints
@bp.route('/admin', methods=['GET'])
@require_admin
def admin_list_reviews():
    args = request.args
    page = args.get('page', 1)
    per_page = args.get('per_page', 20)
    q = Review.query.order_by(Review.created_at.desc())
    from ..utils.pagination import paginate_query
    res = paginate_query(q, page, per_page)
    items = dump_schema.dump(res['items'], many=True)
    return jsonify({'items': items, 'meta': res['meta']})


@bp.route('/admin/<int:review_id>/publish', methods=['POST'])
@require_admin
def publish_review(review_id):
    data = request.json or {}
    make_public = data.get('public', True)
    r = Review.query.get_or_404(review_id)
    r.is_public = bool(make_public)
    db.session.commit()
    return jsonify({'message': 'Review updated', 'review': dump_schema.dump(r)})
