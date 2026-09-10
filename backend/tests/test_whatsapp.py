import hashlib
import hmac

from app.models.order import Order
from app.models.order_history import OrderStatusHistory
from app.models.service import Service
from app.models.user import User
from app.services.whatsapp import normalize_recipient
from app.utils.database import db
from app.utils.jwt_handler import create_token


def _signature(secret, body):
    digest = hmac.new(secret.encode('utf-8'), body, hashlib.sha256).hexdigest()
    return f'sha256={digest}'


def _make_client_order(client, *, status='Submitted'):
    with client.application.app_context():
        user = User(
            email='whatsapp-client@example.com',
            password_hash='test-hash',
            name='WhatsApp Client',
            phone='9063403352',
            email_verified=True,
        )
        db.session.add(user)
        db.session.flush()
        service = Service.query.filter_by(is_active=True).first()
        assert service is not None
        order = Order(
            order_code=f'POSP-WA-{status.upper().replace(" ", "-")}',
            client_name=user.name,
            phone=user.phone,
            email=user.email,
            service=service,
            user_id=user.id,
            description='{"application_data":{}}',
            fee_inr=0,
            official_fee_status='none',
            status=status,
        )
        db.session.add(order)
        db.session.commit()
        token = create_token({'user_id': user.id, 'token_version': user.token_version or 0, 'is_admin': False})
        return order.id, token


def test_normalize_indian_whatsapp_number():
    assert normalize_recipient('+91 90634 03352') == '919063403352'
    assert normalize_recipient('9063403352') == '919063403352'


def test_whatsapp_config_stays_hidden_until_cloud_api_is_ready(client, monkeypatch):
    monkeypatch.setenv('WHATSAPP_CLOUD_API_ENABLED', '0')
    monkeypatch.setenv('WHATSAPP_STATUS_TEMPLATE_NAME', '')
    response = client.get('/api/whatsapp/config')
    assert response.status_code == 200
    assert response.get_json() == {
        'cloud_api_enabled': False,
        'status_notifications_available': False,
    }


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


def test_client_can_enable_and_disable_whatsapp_updates_for_own_request(client):
    order_id, token = _make_client_order(client)
    headers = {'Authorization': f'Bearer {token}'}

    enabled = client.post(
        f'/api/whatsapp/orders/{order_id}/preference',
        json={'enabled': True},
        headers=headers,
    )
    assert enabled.status_code == 200
    assert enabled.get_json()['enabled'] is True

    with client.application.app_context():
        order = db.session.get(Order, order_id)
        assert order.contact_method == 'whatsapp'
        notes = [item.note for item in OrderStatusHistory.query.filter_by(order_id=order_id).all()]
        assert 'Client opted in to WhatsApp status notifications for this request.' in notes

    disabled = client.post(
        f'/api/whatsapp/orders/{order_id}/preference',
        json={'enabled': False},
        headers=headers,
    )
    assert disabled.status_code == 200
    assert disabled.get_json()['enabled'] is False

    with client.application.app_context():
        order = db.session.get(Order, order_id)
        assert order.contact_method is None


def test_closed_request_cannot_enable_whatsapp_updates(client):
    order_id, token = _make_client_order(client, status='Completed')
    response = client.post(
        f'/api/whatsapp/orders/{order_id}/preference',
        json={'enabled': True},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 409
