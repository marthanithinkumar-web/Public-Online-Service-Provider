from datetime import datetime, timezone

from sqlalchemy import UniqueConstraint

from ..utils.database import db


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class WhatsAppMessage(db.Model):
    """Delivery-tracked WhatsApp Cloud API message.

    This table is the single source for the admin WhatsApp panel and for
    duplicate prevention. It never stores access tokens, app secrets, or
    document files. Inbound text is stored only so an admin can hand a
    conversation to the existing in-site support thread; it is visible
    only to admins and to the matched order owner, and it must never be
    copied into email/SMS alerts.
    """

    __tablename__ = 'whatsapp_messages'

    id = db.Column(db.Integer, primary_key=True)
    # 'inbound' or 'outbound'
    direction = db.Column(db.String(20), nullable=False, index=True)
    # Meta waba message id (wamid). Unique when present: webhook retries
    # with the same id must not create a second row.
    wa_message_id = db.Column(db.String(200), nullable=True, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    from_number = db.Column(db.String(50), nullable=True)
    to_number = db.Column(db.String(50), nullable=True)
    message_type = db.Column(db.String(50), nullable=True)
    template_name = db.Column(db.String(200), nullable=True)
    # Short, non-confidential body for inbound text, or a template
    # summary for outbound messages. Never store OTPs, banking details,
    # or document contents here.
    body = db.Column(db.Text, nullable=True)
    # For outbound messages: 'queued', 'sent', 'delivered', 'read', 'failed'.
    # For inbound messages: 'received'.
    status = db.Column(db.String(50), nullable=False, default='queued', index=True)
    # Dedup key for business events, e.g. 'order:123:status:Under Review'
    # or 'order:123:confirmation'. Unique when present.
    event_key = db.Column(db.String(300), nullable=True, index=True)
    retry_count = db.Column(db.Integer, nullable=False, default=0)
    last_error = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        UniqueConstraint('event_key', name='uq_whatsapp_message_event_key'),
        UniqueConstraint('wa_message_id', name='uq_whatsapp_message_wa_id'),
    )

    def to_dict(self, include_body=False):
        data = {
            'id': self.id,
            'direction': self.direction,
            'wa_message_id': self.wa_message_id,
            'order_id': self.order_id,
            'user_id': self.user_id,
            'from_number': self.from_number,
            'to_number': self.to_number,
            'message_type': self.message_type,
            'template_name': self.template_name,
            'status': self.status,
            'event_key': self.event_key,
            'retry_count': self.retry_count,
            'last_error': self.last_error,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_body:
            data['body'] = self.body
        return data
