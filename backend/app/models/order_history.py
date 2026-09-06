from ..utils.database import db
from datetime import datetime, timezone
from sqlalchemy import event, text

def utc_now(): return datetime.now(timezone.utc).replace(tzinfo=None)


class OrderStatusHistory(db.Model):
    __tablename__ = 'order_status_history'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    previous_status = db.Column(db.String(50))
    new_status = db.Column(db.String(50))
    changed_by = db.Column(db.String(200))
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'previous_status': self.previous_status,
            'new_status': self.new_status,
            'changed_by': self.changed_by,
            'note': self.note,
            'created_at': self.created_at.isoformat()
        }


@event.listens_for(OrderStatusHistory, 'after_insert')
def _alert_admin_client_order_activity(mapper, connection, target):
    try:
        row = connection.execute(text('''
            SELECT o.order_code, o.client_name, u.email AS client_email, s.name AS service_name
            FROM orders o
            LEFT JOIN users u ON u.id = o.user_id
            LEFT JOIN services s ON s.id = o.service_id
            WHERE o.id = :order_id
        '''), {'order_id': target.order_id}).mappings().first()
        if not row or not target.changed_by or target.changed_by != row.get('client_email'):
            return
        note = ' '.join(str(target.note or '').split()).lower()
        if target.new_status == 'Submitted' and not target.previous_status:
            title = 'New service request'
            action = 'submitted a new request'
        elif target.new_status == 'Cancelled':
            title = 'Client cancelled service request'
            action = 'cancelled a service request'
        elif 'edited by client' in note:
            title = 'Client edited service request'
            action = 'edited a submitted request'
        else:
            title = 'Client service request updated'
            action = f'updated a request (status: {target.new_status or "unchanged"})'
        client = (row.get('client_name') or 'A client').strip()[:120]
        service = (row.get('service_name') or 'service').strip()[:160]
        code = (row.get('order_code') or f'#{target.order_id}').strip()[:80]
        from ..utils.admin_alerts import send_admin_activity_alert
        send_admin_activity_alert(title, f'{client} {action} for {service}. Reference: {code}.', target.order_id)
    except Exception:
        # External alerts are best-effort and must never break application updates.
        pass
