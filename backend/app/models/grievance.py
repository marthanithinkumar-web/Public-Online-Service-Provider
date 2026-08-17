from ..utils.database import db
from datetime import datetime


class Grievance(db.Model):
    __tablename__ = 'grievances'
    id = db.Column(db.Integer, primary_key=True)
    grievance_code = db.Column(db.String(50), unique=True, nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    client_name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='New')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'grievance_code': self.grievance_code,
            'order_id': self.order_id,
            'client_name': self.client_name,
            'phone': self.phone,
            'email': self.email,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }
