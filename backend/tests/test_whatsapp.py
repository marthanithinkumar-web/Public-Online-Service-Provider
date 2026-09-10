import hashlib
import hmac

from app.services.whatsapp import build if False else normalize_recipient


def _signature(secret, body):
    digest = hmac.new(secret.encode('utf-8'), body, hashlib.sha256).hexdigest()
    return f'sha256={digest}'


def test_normalize_indian_whatsapp_number():
    assert normalize_recipient('+91 90634 03352') == '919063403352'
    assert normalize_recipient('9063403352') == '919063403352'


def test_whatsapp_webhook_verification(client, monkeypatch):
    monkeypatch.setenv('WHATSAPP_VERIFY_TOKEN', 'verify-me')
    response = client.get('/api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=verify-me&hub.challenge=abc123')
    assert response.status_code == 200
    assert response.get_data(as_text=True) == 'abc123'


def test_whatsapp_webhook_rejects_bad_signature(client, monkeypatch):
    monkeypatch.setenv('WHATSAPP_APP_SECRET', 'app-secret')
    body = b'{"entry":[]}'
    response = client.post(
        '/api/whatsapp/webhook',
        data=body,
        content_type='application/json',
        headers={'X-Hub-Signature-256': 'sha256=bad'},
    )
    assert response.status_code == 403


def test_whatsapp_webhook_accepts_valid_signature(client, monkeypatch):
    monkeypatch.setenv('WHATSAPP_APP_SECRET', 'app-secret')
    body = b'{"entry":[]}'
    response = client.post(
        '/api/whatsapp/webhook',
        data=body,
        content_type='application/json',
        headers={'X-Hub-Signature-256': _signature('app-secret', body)},
    )
    assert response.status_code == 200
    assert response.get_json() == {'status': 'accepted'}
