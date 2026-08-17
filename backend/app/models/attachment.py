from ..utils.database import db
from datetime import datetime


class Attachment(db.Model):
    __tablename__ = 'attachments'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    filename = db.Column(db.String(300), nullable=False)
    stored_path = db.Column(db.String(1000), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'filename': self.filename,
            'stored_path': self.stored_path,
            'uploaded_by': self.uploaded_by,
            'created_at': self.created_at.isoformat()
        }
