from datetime import datetime, timezone
def utc_now(): return datetime.now(timezone.utc).replace(tzinfo=None)

from ..utils.database import db


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'order_id': self.order_id,
            'title': self.title,
            'message': self.message,
            'is_read': bool(self.is_read),
            'created_at': self.created_at.isoformat(),
        }


# Import after model declaration so the mapper listener can bind without a circular
# dependency while keeping every in-site client notification eligible for web push.
from ..utils import client_notifications as _client_notifications  # noqa: E402,F401
