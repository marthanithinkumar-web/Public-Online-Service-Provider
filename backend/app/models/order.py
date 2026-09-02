from ..utils.database import db
from datetime import datetime, timezone
def utc_now(): return datetime.now(timezone.utc).replace(tzinfo=None)
import json
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

CLIENT_DOCUMENT_PURGE_STATUSES = {'Completed', 'Rejected', 'Cancelled'}


class Order(db.Model):
    __tablename__='orders'
    id=db.Column(db.Integer,primary_key=True);order_code=db.Column(db.String(50),unique=True,nullable=False);client_name=db.Column(db.String(200),nullable=False);phone=db.Column(db.String(50),nullable=False);email=db.Column(db.String(200),nullable=True);contact_method=db.Column(db.String(50),nullable=True);service_id=db.Column(db.Integer,db.ForeignKey('services.id'));service=db.relationship('Service');user_id=db.Column(db.Integer,db.ForeignKey('users.id'),nullable=True);user=db.relationship('User');description=db.Column(db.Text);fee_inr=db.Column(db.Float,default=0.0);official_fee_inr=db.Column(db.Float,nullable=True);official_fee_status=db.Column(db.String(20),nullable=False,default='unconfirmed');status=db.Column(db.String(50),default='Submitted');admin_archived_at=db.Column(db.DateTime,nullable=True,index=True);created_at=db.Column(db.DateTime,default=utc_now);updated_at=db.Column(db.DateTime,default=utc_now,onupdate=utc_now,nullable=False)

    @property
    def total_fee_inr(self):
        if self.official_fee_status not in {'known', 'none'}:
            return None
        return float(self.fee_inr or 0.0) + float(self.official_fee_inr or 0.0)

    @property
    def application_data(self):
        try:
            data=json.loads(self.description or '{}')
            return data.get('application_data',{}) if isinstance(data,dict) else {}
        except (TypeError,ValueError):
            return {'notes':self.description or ''}

    def to_dict(self, include_admin=False):
        from ..utils.seo import application_service_name
        data = {'id':self.id,'order_code':self.order_code,'client_name':self.client_name,'phone':self.phone,'email':self.email,'contact_method':self.contact_method,'service':application_service_name(self.service.name) if self.service else None,'service_id':self.service_id,'user_id':self.user_id,'fee_inr':float(self.fee_inr or 0.0),'official_fee_inr':float(self.official_fee_inr) if self.official_fee_inr is not None else None,'official_fee_status':self.official_fee_status or 'unconfirmed','total_fee_inr':self.total_fee_inr,'status':self.status,'created_at':self.created_at.isoformat(),'updated_at':(self.updated_at or self.created_at).isoformat(),'application_data':self.application_data}
        if include_admin:
            data.update({
                'is_archived': self.admin_archived_at is not None,
                'archived_at': self.admin_archived_at.isoformat() if self.admin_archived_at else None,
            })
        return data


@event.listens_for(Session, 'before_flush')
def _purge_client_documents_when_order_closes(session, flush_context, instances):
    """Remove client-provided documents as soon as an application becomes terminal.

    Admin-delivered result documents are intentionally retained so the client can
    still access the completed result. Client-provided identity/supporting files
    are deleted from private storage and from the attachment table when the
    application is completed, rejected/closed, or cancelled/withdrawn.
    """
    from .attachment import Attachment
    from ..utils.s3 import delete_stored_file

    for order in list(session.dirty):
        if not isinstance(order, Order) or order.id is None or not order.user_id:
            continue
        history = inspect(order).attrs.status.history
        if not history.has_changes():
            continue
        previous_status = history.deleted[0] if history.deleted else None
        if order.status not in CLIENT_DOCUMENT_PURGE_STATUSES or previous_status in CLIENT_DOCUMENT_PURGE_STATUSES:
            continue
        client_attachments = session.query(Attachment).filter(
            Attachment.order_id == order.id,
            Attachment.uploaded_by == order.user_id,
        ).all()
        for attachment in client_attachments:
            delete_stored_file(attachment.stored_path)
            session.delete(attachment)
