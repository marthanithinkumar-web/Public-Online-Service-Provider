import hashlib
import hmac
import logging
import os

import requests

logger = logging.getLogger(__name__)


def _env(name):
    return (os.getenv(name) or '').strip()


def normalize_recipient(value):
    digits = ''.join(ch for ch in str(value or '') if ch.isdigit())
    if len(digits) == 10:
        return f'91{digits}'
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


def send_template(to, template_name, parameters=None, language_code=None):
    """Send an approved WhatsApp template when Cloud API is explicitly enabled.

    This stays inert until the Meta credentials, Graph API version and approved
    template name are configured in the production environment.
    """
    if not cloud_api_configured() or not template_name:
        return False
    recipient = normalize_recipient(to)
    if not recipient:
        return False
    version = _env('WHATSAPP_GRAPH_API_VERSION')
    phone_number_id = _env('WHATSAPP_PHONE_NUMBER_ID')
    url = f'https://graph.facebook.com/{version}/{phone_number_id}/messages'
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
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.warning('WhatsApp Cloud API delivery failed (%s)', type(exc).__name__)
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
