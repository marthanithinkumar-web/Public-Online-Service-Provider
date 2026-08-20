from flask import Blueprint, request, jsonify
from ..models.order import Order
from ..models.user import User
from ..models.order_history import OrderStatusHistory
from ..models.attachment import Attachment
from ..models.grievance import Grievance
from ..models.review import Review
from ..utils.database import db
from ..utils.jwt_handler import decode_token

bp=Blueprint('admin_workflow',__name__)
ALLOWED={'New','Under Review','Documents Required','In Progress','Completed','Rejected','Cancelled'}
TRANSITIONS={'New':{'Under Review','Cancelled'},'Under Review':{'Documents Required','In Progress','Rejected','Cancelled'},'Documents Required':{'Under Review','In Progress','Cancelled'},'In Progress':{'Documents Required','Completed','Rejected','Cancelled'},'Completed':set(),'Rejected':set(),'Cancelled':set()}

def admin_user():
    auth=request.headers.get('Authorization','')
    if not auth.startswith('Bearer '):return None
    try:p=decode_token(auth.split(' ',1)[1])
    except Exception:return None
    u=User.query.get(p.get('user_id'));return u if u and u.is_admin else None

@bp.route('/orders',methods=['GET'])
def list_orders():
    if not admin_user():return jsonify({'error':'Unauthorized'}),401
    status=request.args.get('status');q=Order.query
    if status:q=q.filter_by(status=status)
    q=q.order_by(Order.created_at.desc())
    from ..utils.pagination import paginate_query
    res=paginate_query(q,request.args.get('page',1),request.args.get('per_page',20))
    return jsonify({'items':[o.to_dict() for o in res['items']],'meta':res['meta'],'statuses':sorted(ALLOWED)})

@bp.route('/orders/<int:order_id>',methods=['GET'])
def detail(order_id):
    if not admin_user():return jsonify({'error':'Unauthorized'}),401
    o=Order.query.get_or_404(order_id)
    history=OrderStatusHistory.query.filter_by(order_id=o.id).order_by(OrderStatusHistory.created_at.asc()).all()
    return jsonify({'order':o.to_dict(),'history':[h.to_dict() for h in history],'attachments':[a.to_dict() for a in Attachment.query.filter_by(order_id=o.id).all()],'grievances':[g.to_dict() for g in Grievance.query.filter_by(order_id=o.id).all()],'reviews':[r.to_dict() for r in Review.query.filter_by(order_id=o.id).all()],'allowed_next_statuses':sorted(TRANSITIONS.get(o.status,set()))})

@bp.route('/orders/<int:order_id>/status',methods=['POST'])
def update_status(order_id):
    user=admin_user()
    if not user:return jsonify({'error':'Unauthorized'}),401
    data=request.json or {};status=(data.get('status') or '').strip();note=(data.get('note') or '').strip();o=Order.query.get_or_404(order_id)
    if status not in ALLOWED:return jsonify({'error':'Invalid request status.'}),400
    if status==o.status:return jsonify({'error':'The request is already in this status.'}),400
    if status not in TRANSITIONS.get(o.status,set()):return jsonify({'error':f'Cannot move a request from {o.status} to {status}.'}),409
    if status in {'Documents Required','Rejected'} and len(note)<5:return jsonify({'error':'A clear note is required for this status.'}),400
    previous=o.status;o.status=status;h=OrderStatusHistory(order_id=o.id,previous_status=previous,new_status=status,changed_by=user.email,note=note or None);db.session.add(h);db.session.commit()
    return jsonify({'message':'Request status updated.','order':o.to_dict(),'history':h.to_dict()})
