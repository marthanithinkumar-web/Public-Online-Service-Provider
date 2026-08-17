from ..utils.database import db
from datetime import datetime


class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    client_name = db.Column(db.String(200))
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'rating': self.rating,
            'comment': self.comment,
            'client_name': (self.client_name if self.is_public else None),
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat()
        }
