import json
import logging
import os

from sqlalchemy import event, select

from ..models.notification import Notification
from ..models.push_subscription import PushSubscription
from ..models.user import User
from .email import send_email

logger = logging.getLogger(__name__)


def _base_url():
    return (os.getenv('PUBLIC_APP_URL') or os.getenv('FRONTEND_URL') or '').rstrip('/')


def _client_link(order_id=None):
    base = _base_url()
    if not base:
        return '/my-orders'
    return f'{base}/my-orders/{order_id}' if order_id else f'{base}/my-orders'


def _deliver_push(connection, notification):
    private_key = (os.getenv('WEB_PUSH_VAPID_PRIVATE_KEY') or '').strip()
    subject = (os.getenv('WEB_PUSH_VAPID_SUBJECT') or 'mailto:' + (os.getenv('ADMIN_EMAIL') or 'admin@example.com')).strip()
    if not private_key:
        return False
    rows = connection.execute(
        select(PushSubscription.endpoint, PushSubscription.p256dh, PushSubscription.auth)
        .where(PushSubscription.user_id == notification.user_id)
    ).all()
    if not rows:
        return False
    try:
        from pywebpush import WebPushException, webpush
    except Exception:
        return False
    payload = json.dumps({
        'title': str(notification.title or 'Application update')[:160],
        'body': str(notification.message or '')[:700],
        'url': _client_link(notification.order_id),
    })
    sent = False
    for endpoint, p256dh, auth in rows:
        try:
            webpush(
                subscription_info={'endpoint': endpoint, 'keys': {'p256dh': p256dh, 'auth': auth}},
                data=payload,
                vapid_private_key=private_key,
                vapid_claims={'sub': subject},
                timeout=8,
            )
            sent = True
        except WebPushException as exc:
            logger.warning('Client web push delivery failed (%s)', type(exc).__name__)
        except Exception as exc:
            logger.warning('Client web push unavailable (%s)', type(exc).__name__)
    return sent


def _deliver_status_email(connection, notification):
    # Manual admin notifications already send email in the admin route. Automatic
    # request status notifications previously only appeared inside the website, so
    # add email delivery here without creating duplicate manual-notification emails.
    if notification.title != 'Request status updated':
        return False
    email = connection.execute(
        select(User.email).where(User.id == notification.user_id, User.is_active.is_(True))
    ).scalar_one_or_none()
    if not email:
        return False
    try:
        return bool(send_email(
            email,
            'Public Online Service Provider — Request status updated',
            str(notification.message or ''),
        ))
    except Exception as exc:
        logger.warning('Client status email delivery failed (%s)', type(exc).__name__)
        return False


@event.listens_for(Notification, 'after_insert')
def deliver_client_notification(mapper, connection, notification):
    """Best-effort client delivery for each persisted in-site notification.

    Delivery failures never roll back the client/application transaction.
    """
    try:
        user = connection.execute(
            select(User.is_admin, User.is_active).where(User.id == notification.user_id)
        ).first()
        if not user or user.is_admin or not user.is_active:
            return
        _deliver_push(connection, notification)
        _deliver_status_email(connection, notification)
    except Exception as exc:
        logger.warning('Client notification delivery failed (%s)', type(exc).__name__)
