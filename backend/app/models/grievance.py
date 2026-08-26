from ..utils.database import db
from datetime import datetime, timezone
def utc_now(): return datetime.now(timezone.utc).replace(tzinfo=None)


class Grievance(db.Model):
    __tablename__ = 'grievances'
    id = db.Column(db.Integer, primary_key=True)
    grievance_code = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    order = db.relationship('Order')
    client_name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='New')
    admin_response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'grievance_code': self.grievance_code,
            'user_id': self.user_id,
            'order_id': self.order_id,
            'client_name': self.client_name,
            'phone': self.phone,
            'email': self.email,
            'description': self.description,
            'status': self.status,
            'admin_response': self.admin_response,
            'created_at': self.created_at.isoformat(),
            'updated_at': (self.updated_at or self.created_at).isoformat(),
        }


class GrievanceHistory(db.Model):
    __tablename__ = 'grievance_history'
    id = db.Column(db.Integer, primary_key=True)
    grievance_id = db.Column(db.Integer, db.ForeignKey('grievances.id'), nullable=False, index=True)
    previous_status = db.Column(db.String(50), nullable=True)
    new_status = db.Column(db.String(50), nullable=False)
    changed_by = db.Column(db.String(200), nullable=False)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'grievance_id': self.grievance_id,
            'previous_status': self.previous_status,
            'new_status': self.new_status,
            'changed_by': self.changed_by,
            'note': self.note,
            'created_at': self.created_at.isoformat(),
        }
