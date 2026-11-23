import hashlib
import hmac
import logging
import os
import time
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)


def _env(name):
    return (os.getenv(name) or '').strip()


def normalize_recipient(value):
    digits = ''.join(ch for ch in str(value or '') if ch.isdigit())
    if digits.startswith('00'):
        digits = digits[2:]
    if digits.startswith('0') and len(digits) == 11:
        digits = digits[1:]
    if len(digits) == 10:
        return f'91{digits}'
    if len(digits) == 12 and digits.startswith('91'):
        return digits
    return digits


def cloud_api_configured():
    return (
        _env('WHATSAPP_CLOUD_API_ENABLED') == '1'
        and bool(_env('WHATSAPP_GRAPH_API_VERSION'))
        and bool(_env('WHATSAPP_PHONE_NUMBER_ID'))
        and bool(_env('WHATSAPP_ACCESS_TOKEN'))
    )


def verify_webhook_signature(raw_body, signature_header):
    app_secret = _env('WHATSAPP_APP_SECRET')
    if not app_secret or not signature_header or not signature_header.startswith('sha256='):
        return False
    digest = hmac.new(app_secret.encode('utf-8'), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature_header, f'sha256={digest}')


def _post_message(payload, retry_delays=(0, 1, 2)):
    """POST one WhatsApp message with bounded retries.

    Returns (ok, message_id, error). Retries only transient transport
    failures and 5xx/429 responses, never a 4xx auth/template rejection
    (retrying those would spam Meta and leak nothing, but it would not
    fix the underlying template/permission problem).
    """
    version = _env('WHATSAPP_GRAPH_API_VERSION')
    phone_number_id = _env('WHATSAPP_PHONE_NUMBER_ID')
    url = f'https://graph.facebook.com/{version}/{phone_number_id}/messages'
    last_error = None
    for attempt, delay in enumerate(retry_delays):
        if attempt and delay:
            time.sleep(delay)
        try:
            response = requests.post(
                url,
                json=payload,
                headers={
                    'Authorization': f"Bearer {_env('WHATSAPP_ACCESS_TOKEN')}",
                    'Content-Type': 'application/json',
                },
                timeout=8,
            )
            if response.status_code in (429,) or response.status_code >= 500:
                last_error = f'WhatsApp API HTTP {response.status_code}'
                continue
            response.raise_for_status()
            data = response.json() if response.content else {}
            messages = data.get('messages') if isinstance(data, dict) else None
            message_id = messages[0].get('id') if messages else None
            return True, message_id, None
        except requests.RequestException as exc:
            last_error = type(exc).__name__
            logger.warning('WhatsApp Cloud API delivery failed (%s)', last_error)
    return False, None, last_error


def send_template_with_result(to, template_name, parameters=None, language_code=None, retry_delays=(0, 1, 2)):
    """Send a template and return (ok, message_id, error). Inert when disabled."""
    if not cloud_api_configured() or not template_name:
        return False, None, 'WhatsApp Cloud API is not configured'
    recipient = normalize_recipient(to)
    if not recipient:
        return False, None, 'No recipient phone number'
    template = {
        'name': template_name,
        'language': {'code': language_code or _env('WHATSAPP_TEMPLATE_LANGUAGE') or 'en'},
    }
    values = [str(value)[:900] for value in (parameters or []) if value is not None]
    if values:
        template['components'] = [{
            'type': 'body',
            'parameters': [{'type': 'text', 'text': value} for value in values],
        }]
    payload = {
        'messaging_product': 'whatsapp',
        'recipient_type': 'individual',
        'to': recipient,
        'type': 'template',
        'template': template,
    }
    return _post_message(payload, retry_delays=retry_delays)


def send_template(to, template_name, parameters=None, language_code=None):
    """Send an approved WhatsApp template when Cloud API is explicitly enabled.

    This stays inert until the Meta credentials, Graph API version and approved
    template name are configured in the production environment.
    Kept for backward compatibility; new code should use
    send_template_with_result so delivery can be recorded and retried.
    """
    ok, _message_id, _error = send_template_with_result(to, template_name, parameters, language_code)
    return ok


def send_text_message(to, text):
    """Send a free-form text message.

    Callers must enforce the 24-hour customer service window: this
    function alone does not know whether the customer messaged recently.
    The webhook handler records inbound timestamps, and the notify
    helper checks them before using this path. Business-initiated
    messages outside that window must use an approved template instead.
    """
    if not cloud_api_configured():
        return False, None, 'WhatsApp Cloud API is not configured'
    recipient = normalize_recipient(to)
    if not recipient or not text:
        return False, None, 'No recipient or message text'
    payload = {
        'messaging_product': 'whatsapp',
        'recipient_type': 'individual',
        'to': recipient,
        'type': 'text',
        'text': {'preview_url': False, 'body': str(text)[:4000]},
    }
    return _post_message(payload)


def parse_webhook_payload(payload):
    """Extract (inbound_messages, delivery_statuses) from a Meta payload.

    Inbound items: dicts with wa_message_id, from_number, type, text,
    timestamp. Status items: dicts with wa_message_id, status, timestamp.
    Unknown shapes are ignored, never raised, so a malformed Meta event
    cannot break webhook acknowledgement.
    """
    inbound = []
    statuses = []
    if not isinstance(payload, dict):
        return inbound, statuses
    for entry in payload.get('entry', []) or []:
        if not isinstance(entry, dict):
            continue
        for change in entry.get('changes', []) or []:
            if not isinstance(change, dict):
                continue
            value = change.get('value', {}) if isinstance(change.get('value'), dict) else {}
            for msg in value.get('messages', []) or []:
                if not isinstance(msg, dict):
                    continue
                text_body = None
                if msg.get('type') == 'text' and isinstance(msg.get('text'), dict):
                    text_body = msg['text'].get('body')
                inbound.append({
                    'wa_message_id': msg.get('id'),
                    'from_number': msg.get('from'),
                    'type': msg.get('type'),
                    'text': text_body,
                    'timestamp': msg.get('timestamp'),
                })
            for st in value.get('statuses', []) or []:
                if not isinstance(st, dict):
                    continue
                statuses.append({
                    'wa_message_id': st.get('id'),
                    'status': st.get('status'),
                    'timestamp': st.get('timestamp'),
                })
    return inbound, statuses


def last_inbound_within_24h(recipient):
    """True if the recipient messaged in the last 24 hours, from the DB.

    This is a lazy import so the service module can be used without a
    Flask app context in unit tests that only check config/signature.
    """
    try:
        from ..models.whatsapp_message import WhatsAppMessage
        from ..utils.database import db
        from datetime import timedelta
        target = normalize_recipient(recipient)
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
        local = target[2:] if target.startswith('91') and len(target) == 12 else target
        candidates = {target, local, f'0{local}'}
        return WhatsAppMessage.query.filter(
            WhatsAppMessage.direction == 'inbound',
            WhatsAppMessage.created_at >= cutoff,
            WhatsAppMessage.from_number.in_(candidates),
        ).first() is not None
    except Exception:
        return False


def send_status_update(to, request_reference, status, request_url):
    template_name = _env('WHATSAPP_STATUS_TEMPLATE_NAME')
    if not template_name:
        return False
    return send_template(
        to,
        template_name,
        [request_reference, status, request_url],
    )
