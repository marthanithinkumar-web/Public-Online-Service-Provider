from ..utils.database import db
from datetime import datetime, timezone
def utc_now(): return datetime.now(timezone.utc).replace(tzinfo=None)
import json

class Order(db.Model):
    __tablename__='orders'
    id=db.Column(db.Integer,primary_key=True);order_code=db.Column(db.String(50),unique=True,nullable=False);client_name=db.Column(db.String(200),nullable=False);phone=db.Column(db.String(50),nullable=False);email=db.Column(db.String(200),nullable=True);contact_method=db.Column(db.String(50),nullable=True);service_id=db.Column(db.Integer,db.ForeignKey('services.id'));service=db.relationship('Service');user_id=db.Column(db.Integer,db.ForeignKey('users.id'),nullable=True);user=db.relationship('User');description=db.Column(db.Text);fee_inr=db.Column(db.Float,default=0.0);status=db.Column(db.String(50),default='Submitted');created_at=db.Column(db.DateTime,default=utc_now);updated_at=db.Column(db.DateTime,default=utc_now,onupdate=utc_now,nullable=False)

    @property
    def application_data(self):
        try:
            data=json.loads(self.description or '{}')
            return data.get('application_data',{}) if isinstance(data,dict) else {}
        except (TypeError,ValueError):
            return {'notes':self.description or ''}

    def to_dict(self):
        return {'id':self.id,'order_code':self.order_code,'client_name':self.client_name,'phone':self.phone,'email':self.email,'contact_method':self.contact_method,'service':self.service.name if self.service else None,'service_id':self.service_id,'user_id':self.user_id,'fee_inr':float(self.fee_inr or 0.0),'status':self.status,'created_at':self.created_at.isoformat(),'updated_at':(self.updated_at or self.created_at).isoformat(),'application_data':self.application_data}
