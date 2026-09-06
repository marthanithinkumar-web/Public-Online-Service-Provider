import base64
import json
import logging
import os
from urllib import parse, request

from .email import send_email

logger = logging.getLogger(__name__)


def _clean(value, limit=500):
    return ' '.join(str(value or '').replace('\r', ' ').replace('\n', ' ').split())[:limit]


def _admin_link(order_id=None):
    base = (os.getenv('PUBLIC_APP_URL') or os.getenv('FRONTEND_URL') or '').rstrip('/')
    if not base:
        return ''
    return f"{base}/admin/applications/{order_id}" if order_id else f"{base}/admin"


def _twilio_message(to_number, from_number, body):
    sid = (os.getenv('TWILIO_ACCOUNT_SID') or '').strip()
    token = (os.getenv('TWILIO_AUTH_TOKEN') or '').strip()
    if not sid or not token or not to_number or not from_number:
        return False
    endpoint = f'https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json'
    payload = parse.urlencode({'To': to_number, 'From': from_number, 'Body': body}).encode()
    req = request.Request(endpoint, data=payload, method='POST')
    req.add_header('Authorization', 'Basic ' + base64.b64encode(f'{sid}:{token}'.encode()).decode())
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    try:
        with request.urlopen(req, timeout=8) as response:
            return 200 <= response.status < 300
    except Exception as exc:
        logger.warning('Admin mobile alert delivery failed (%s)', type(exc).__name__)
        return False


def _web_push(title, message, link):
    private_key = (os.getenv('WEB_PUSH_VAPID_PRIVATE_KEY') or '').strip()
    subject = (os.getenv('WEB_PUSH_VAPID_SUBJECT') or 'mailto:' + (os.getenv('ADMIN_EMAIL') or 'admin@example.com')).strip()
    if not private_key:
        return False
    try:
        from pywebpush import WebPushException, webpush
        from ..models.push_subscription import PushSubscription
        stale = []
        sent = False
        payload = json.dumps({'title': title, 'body': message, 'url': link or '/admin'})
        for sub in PushSubscription.query.all():
            try:
                webpush(subscription_info={'endpoint': sub.endpoint, 'keys': {'p256dh': sub.p256dh, 'auth': sub.auth}}, data=payload, vapid_private_key=private_key, vapid_claims={'sub': subject}, timeout=8)
                sent = True
            except WebPushException as exc:
                if getattr(exc.response, 'status_code', None) in (404, 410):
                    stale.append(sub)
                else:
                    logger.warning('Admin web push delivery failed (%s)', type(exc).__name__)
        if stale:
            from .database import db
            for sub in stale:
                db.session.delete(sub)
            db.session.commit()
        return sent
    except Exception as exc:
        logger.warning('Admin web push unavailable (%s)', type(exc).__name__)
        return False


def send_admin_activity_alert(title, message, order_id=None):
    """Best-effort admin alert. Never raises into a client request."""
    safe_title = _clean(title, 160)
    safe_message = _clean(message, 700)
    link = _admin_link(order_id)
    body = f'{safe_title}\n\n{safe_message}' + (f'\n\nOpen admin: {link}' if link else '')
    results = {'email': False, 'web_push': False, 'sms': False, 'whatsapp': False}

    email = (os.getenv('ADMIN_ALERT_EMAIL') or os.getenv('ADMIN_EMAIL') or '').strip()
    if email:
        try:
            results['email'] = bool(send_email(email, f'[Admin alert] {safe_title}', body))
        except Exception as exc:
            logger.warning('Admin email alert delivery failed (%s)', type(exc).__name__)

    results['web_push'] = _web_push(safe_title, safe_message, link)

    # Paid provider channels remain optional and disabled when no credentials exist.
    phone = (os.getenv('ADMIN_ALERT_PHONE') or '').strip()
    sms_from = (os.getenv('TWILIO_SMS_FROM') or '').strip()
    if phone and sms_from:
        results['sms'] = _twilio_message(phone, sms_from, body[:1500])

    whatsapp_to = (os.getenv('ADMIN_WHATSAPP_TO') or phone).strip()
    whatsapp_from = (os.getenv('TWILIO_WHATSAPP_FROM') or '').strip()
    if whatsapp_to and whatsapp_from:
        to_value = whatsapp_to if whatsapp_to.startswith('whatsapp:') else f'whatsapp:{whatsapp_to}'
        from_value = whatsapp_from if whatsapp_from.startswith('whatsapp:') else f'whatsapp:{whatsapp_from}'
        results['whatsapp'] = _twilio_message(to_value, from_value, body[:1500])

    return results
