from ..utils.database import db
from datetime import datetime, timezone
from sqlalchemy import event, text

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


@event.listens_for(Attachment, 'after_insert')
def _alert_admin_client_document(mapper, connection, target):
    if not target.order_id or not target.uploaded_by:
        return
    try:
        row = connection.execute(text('''
            SELECT u.is_admin, o.order_code, o.client_name, s.name AS service_name
            FROM users u
            JOIN orders o ON o.id = :order_id
            LEFT JOIN services s ON s.id = o.service_id
            WHERE u.id = :user_id
        '''), {'order_id': target.order_id, 'user_id': target.uploaded_by}).mappings().first()
        if not row or row.get('is_admin'):
            return
        client = (row.get('client_name') or 'A client').strip()[:120]
        service = (row.get('service_name') or 'service').strip()[:160]
        code = (row.get('order_code') or f'#{target.order_id}').strip()[:80]
        from ..utils.admin_alerts import send_admin_activity_alert
        send_admin_activity_alert('Client uploaded a document', f'{client} uploaded a document for {service}. Reference: {code}. Open the application to review it securely.', target.order_id)
    except Exception:
        pass
