from flask import Blueprint, request, jsonify
from ..models.user import User
from ..models.order import Order
from ..models.review import Review
from ..models.grievance import Grievance
from ..utils.database import db
from ..utils.jwt_handler import decode_token
from datetime import datetime
from secrets import token_hex

bp=Blueprint('client_actions',__name__)

def client_user():
    auth=request.headers.get('Authorization','')
    if not auth.startswith('Bearer '):return None
    try:p=decode_token(auth.split(' ',1)[1])
    except Exception:return None
    u=User.query.get(p.get('user_id'));return u if u and not u.is_admin else None

def grievance_code():return f"GV-{datetime.utcnow().year}-{token_hex(4).upper()}"

@bp.route('/reviews',methods=['POST'])
def review():
    user=client_user()
    if not user:return jsonify({'error':'Please log in as a client.'}),401
    data=request.json or {};order_id=data.get('order_id')
    if not order_id:return jsonify({'error':'A completed request is required for a review.'}),400
    order=Order.query.get(order_id)
    if not order or order.user_id!=user.id:return jsonify({'error':'You can review only your own request.'}),403
    if order.status!='Completed':return jsonify({'error':'Reviews are available after the request is completed.'}),409
    if Review.query.filter_by(order_id=order.id).first():return jsonify({'error':'A review has already been submitted for this request.'}),409
    rating=int(data.get('rating',0));comment=(data.get('comment') or '').strip()
    if rating<1 or rating>5 or len(comment)<5:return jsonify({'error':'Please provide a rating from 1 to 5 and a comment of at least 5 characters.'}),400
    r=Review(order_id=order.id,rating=rating,comment=comment,client_name=user.name,is_public=False);db.session.add(r);db.session.commit()
    return jsonify({'message':'Review submitted successfully.','review':r.to_dict()}),201

@bp.route('/grievances',methods=['POST'])
def grievance():
    user=client_user()
    if not user:return jsonify({'error':'Please log in as a client.'}),401
    data=request.json or {};description=(data.get('description') or '').strip();order_id=data.get('order_id')
    if len(description)<10:return jsonify({'error':'Please describe the issue in at least 10 characters.'}),400
    order=None
    if order_id:
        order=Order.query.get(order_id)
        if not order or order.user_id!=user.id:return jsonify({'error':'You can submit a grievance only for your own request.'}),403
    g=Grievance(grievance_code=grievance_code(),order_id=order.id if order else None,client_name=user.name,phone=user.phone,email=user.email,description=description,status='New');db.session.add(g);db.session.commit()
    return jsonify({'message':'Grievance submitted successfully.','grievance':g.to_dict()}),201
