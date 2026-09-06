from datetime import datetime, timezone

from sqlalchemy import event, inspect, text

from ..utils.database import db


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    provider = db.Column(db.String(30), nullable=False, default='razorpay')
    purpose = db.Column(db.String(40), nullable=False, default='request_total')
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


def _send_payment_alert(connection, target):
    try:
        row = connection.execute(text('''
            SELECT o.order_code, o.client_name, s.name AS service_name
            FROM orders o LEFT JOIN services s ON s.id = o.service_id
            WHERE o.id = :order_id
        '''), {'order_id': target.order_id}).mappings().first()
        if not row:
            return
        status = (target.status or 'updated').lower()
        labels = {
            'created': 'Payment initiated',
            'authorized': 'Payment authorized',
            'captured': 'Payment completed',
            'paid': 'Payment completed',
            'failed': 'Payment failed',
            'refunded': 'Payment refunded',
        }
        title = labels.get(status, 'Payment updated')
        client = (row.get('client_name') or 'A client').strip()[:120]
        service = (row.get('service_name') or 'service').strip()[:160]
        code = (row.get('order_code') or f'#{target.order_id}').strip()[:80]
        amount = round((target.amount_paise or 0) / 100, 2)
        from ..utils.admin_alerts import send_admin_activity_alert
        send_admin_activity_alert(title, f'{client}: {title.lower()} for {service}. Amount: INR {amount:.2f}. Reference: {code}.', target.order_id)
    except Exception:
        pass


@event.listens_for(Payment, 'after_insert')
def _alert_admin_payment_created(mapper, connection, target):
    _send_payment_alert(connection, target)


@event.listens_for(Payment, 'after_update')
def _alert_admin_payment_updated(mapper, connection, target):
    if inspect(target).attrs.status.history.has_changes():
        _send_payment_alert(connection, target)
