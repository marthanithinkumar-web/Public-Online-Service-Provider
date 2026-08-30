from flask import Blueprint, request, jsonify
from ..models.review import Review
from ..models.order import Order
from ..utils.database import db
from ..schemas.review_schema import ReviewCreateSchema, ReviewSchema
from ..middleware.auth import require_admin
from ..models.user import User
from ..utils.jwt_handler import get_request_user
from ..utils.seo import application_service_name

bp = Blueprint('reviews', __name__)

create_schema = ReviewCreateSchema()
dump_schema = ReviewSchema()


def _authenticated_user():
    return get_request_user()


@bp.route('', methods=['POST'])
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
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({'error': 'Invalid order_id'}), 400
    if order.user_id != user.id:
        return jsonify({'error': 'You can only review your own request.'}), 403
    first_order = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.asc(), Order.id.asc()).first()
    if not first_order or first_order.id != order.id:
        return jsonify({'error': 'Feedback is available only for your first request.'}), 409
    existing = (Review.query.join(Order, Review.order_id == Order.id)
                .filter(Order.user_id == user.id).first())
    if existing:
        return jsonify({'error': 'Feedback has already been submitted.'}), 409

    r = Review(
        order_id=order_id,
        rating=data['rating'],
        comment=data.get('comment'),
        client_name=user.name,
        is_public=False  # default false; admin can make it public
    )
    db.session.add(r)
    db.session.commit()
    return jsonify({'message': 'Thank you for your feedback.', 'review': dump_schema.dump(r)}), 201


@bp.route('/mine', methods=['GET'])
def my_reviews():
    user = _authenticated_user()
    if not user or user.is_admin:
        return jsonify({'error': 'Please log in with a client account.'}), 401
    reviews = (Review.query.join(Order, Review.order_id == Order.id)
               .filter(Order.user_id == user.id).order_by(Review.created_at.desc()).all())
    return jsonify({'items': dump_schema.dump(reviews, many=True)})


@bp.route('/public', methods=['GET'])
def public_reviews():
    reviews = Review.query.filter_by(is_public=True).order_by(Review.created_at.desc()).limit(20).all()
    # Public review cards deliberately omit client names, contact details,
    # internal order IDs and request references.
    items = []
    for review in reviews:
        order = db.session.get(Order, review.order_id) if review.order_id else None
        items.append({
            'id': review.id,
            'rating': review.rating,
            'comment': review.comment,
            'service': application_service_name(order.service.name) if order and order.service else None,
            'reviewer': 'Verified client',
            'created_at': review.created_at.isoformat(),
        })
    return jsonify(items)


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
    items = []
    for review in res['items']:
        item = dump_schema.dump(review)
        order = db.session.get(Order, review.order_id) if review.order_id else None
        item['order_code'] = order.order_code if order else None
        item['service'] = application_service_name(order.service.name) if order and order.service else None
        items.append(item)
    return jsonify({'items': items, 'meta': res['meta']})


@bp.route('/admin/<int:review_id>/publish', methods=['POST'])
@require_admin
def publish_review(review_id):
    data = request.json or {}
    make_public = data.get('public', True)
    r = db.get_or_404(Review, review_id)
    r.is_public = bool(make_public)
    db.session.commit()
    return jsonify({'message': 'Review updated', 'review': dump_schema.dump(r)})
