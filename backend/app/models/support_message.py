from datetime import datetime, timezone

from sqlalchemy import event, text

from ..utils.database import db


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SupportMessage(db.Model):
    """A private, account-owned conversation between one client and admins."""

    __tablename__ = 'support_messages'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    sender_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sender_role = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    read_by_client = db.Column(db.Boolean, nullable=False, default=False)
    read_by_admin = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sender_role': self.sender_role,
            'message': self.message,
            'read_by_client': bool(self.read_by_client),
            'read_by_admin': bool(self.read_by_admin),
            'created_at': self.created_at.isoformat(),
        }


@event.listens_for(SupportMessage, 'after_insert')
def _alert_admin_client_message(mapper, connection, target):
    if target.sender_role != 'client':
        return
    try:
        row = connection.execute(text('SELECT name FROM users WHERE id = :user_id'), {'user_id': target.user_id}).mappings().first()
        client = ((row or {}).get('name') or 'A client').strip()[:120]
        from ..utils.admin_alerts import send_admin_activity_alert
        # Do not copy private message contents into SMS/WhatsApp/email alerts.
        send_admin_activity_alert('New client message', f'{client} sent a new private support message. Open the admin Messages section to read it securely.', None)
    except Exception:
        pass
