from datetime import datetime, timezone

from ..utils.database import db


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Refund(db.Model):
    __tablename__ = 'refunds'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    amount_paise = db.Column(db.Integer, nullable=False)
    method = db.Column(db.String(30), nullable=False)
    reference = db.Column(db.String(160), nullable=False, index=True)
    refunded_at = db.Column(db.DateTime, nullable=False)
    note = db.Column(db.String(2000), nullable=True)
    proof_filename = db.Column(db.String(255), nullable=True)
    proof_stored_path = db.Column(db.Text, nullable=True)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    order = db.relationship('Order', backref=db.backref('refunds', lazy=True, cascade='all, delete-orphan'))

    def to_dict(self, include_private=False):
        data = {
            'id': self.id,
            'order_id': self.order_id,
            'amount_inr': round(self.amount_paise / 100, 2),
            'method': self.method,
            'reference': self.reference,
            'refunded_at': self.refunded_at.isoformat() if self.refunded_at else None,
            'note': self.note,
            'proof_available': bool(self.proof_stored_path),
            'proof_filename': self.proof_filename if self.proof_stored_path else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_private:
            data['recorded_by'] = self.recorded_by
        return data
