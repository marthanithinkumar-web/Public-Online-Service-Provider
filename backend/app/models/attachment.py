from ..utils.database import db
from datetime import datetime, timezone
def utc_now(): return datetime.now(timezone.utc).replace(tzinfo=None)


class Attachment(db.Model):
    __tablename__ = 'attachments'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    filename = db.Column(db.String(300), nullable=False)
    stored_path = db.Column(db.String(1000), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self, uploaded_by_role=None):
        # Never expose filesystem paths, S3 bucket names, or storage keys to clients.
        return {
            'id': self.id,
            'order_id': self.order_id,
            'filename': self.filename,
            'uploaded_by_role': uploaded_by_role,
            'created_at': self.created_at.isoformat()
        }
