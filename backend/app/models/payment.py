from datetime import datetime, timezone

from ..utils.database import db


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    provider = db.Column(db.String(30), nullable=False, default='razorpay')
    purpose = db.Column(db.String(40), nullable=False, default='assistance_fee')
    amount_paise = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='INR')
    status = db.Column(db.String(30), nullable=False, default='created', index=True)
    razorpay_order_id = db.Column(db.String(100), nullable=False, unique=True, index=True)
    razorpay_payment_id = db.Column(db.String(100), nullable=True, unique=True, index=True)
    failure_code = db.Column(db.String(120), nullable=True)
    failure_description = db.Column(db.String(1000), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=utc_now, onupdate=utc_now)
    captured_at = db.Column(db.DateTime, nullable=True)

    order = db.relationship('Order', backref=db.backref('payments', lazy=True, cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'provider': self.provider,
            'purpose': self.purpose,
            'amount_inr': round(self.amount_paise / 100, 2),
            'currency': self.currency,
            'status': self.status,
            'razorpay_order_id': self.razorpay_order_id,
            'razorpay_payment_id': self.razorpay_payment_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'captured_at': self.captured_at.isoformat() if self.captured_at else None,
        }
