from flask import Blueprint, request, jsonify
from ..models.review import Review
from ..models.order import Order
from ..utils.database import db
from ..schemas.review_schema import ReviewCreateSchema, ReviewSchema
from ..middleware.auth import require_admin
from ..models.user import User
from ..utils.jwt_handler import decode_token

bp = Blueprint('reviews', __name__)

create_schema = ReviewCreateSchema()
dump_schema = ReviewSchema()


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
def create_review():
    user = _authenticated_user()
    if not user or user.is_admin:
        return jsonify({'error': 'Please log in with a client account.'}), 401
    data = request.json or {}
    errors = create_schema.validate(data)
    if errors:
        return jsonify({'error': errors}), 400

    order_id = data['order_id']
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Invalid order_id'}), 400
    if order.user_id != user.id:
        return jsonify({'error': 'You can only review your own request.'}), 403
    if order.status != 'Completed':
        return jsonify({'error': 'Reviews can be submitted after the request is completed.'}), 409
    if Review.query.filter_by(order_id=order.id).first():
        return jsonify({'error': 'A review has already been submitted for this request.'}), 409

    r = Review(
        order_id=order_id,
        rating=data['rating'],
        comment=data.get('comment'),
        client_name=user.name,
        is_public=False  # default false; admin can make it public
    )
    db.session.add(r)
    db.session.commit()
    return jsonify({'message': 'Review submitted', 'review': dump_schema.dump(r)}), 201


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
