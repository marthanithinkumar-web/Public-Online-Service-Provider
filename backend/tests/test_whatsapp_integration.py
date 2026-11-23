"""WhatsApp integration tests, using mocked Meta responses.

No real Meta, Render, or customer message is sent. The tests cover:
- webhook verification challenge and signature rejection
- inbound dedup, delivery-status updates, and support handoff by phone
- confirmation/status notification dedup (same event sent once)
- admin-only access to the WhatsApp panel endpoints and retry
- opt-in preference enforcement (no send without whatsapp opt-in)
"""

import hashlib
import hmac
import os
import sys
from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import create_app  # noqa: E402
from app.models.order import Order  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.whatsapp_message import WhatsAppMessage  # noqa: E402
from app.services import whatsapp as wa  # noqa: E402
from app.utils.database import db  # noqa: E402
from app.utils.jwt_handler import create_token  # noqa: E402
from app.utils.password import hash_password  # noqa: E402


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{tmp_path / "whatsapp-tests.db"}')
    monkeypatch.setenv('SECRET_KEY', 'test-secret-key-for-whatsapp-tests')
    monkeypatch.setenv('FLASK_ENV', 'development')
    monkeypatch.setenv('WHATSAPP_CLOUD_API_ENABLED', '1')
    monkeypatch.setenv('WHATSAPP_GRAPH_API_VERSION', 'v21.0')
    monkeypatch.setenv('WHATSAPP_PHONE_NUMBER_ID', 'test-phone-id')
    monkeypatch.setenv('WHATSAPP_ACCESS_TOKEN', 'test-token-not-real')
    monkeypatch.setenv('WHATSAPP_APP_SECRET', 'test-app-secret')
    monkeypatch.setenv('WHATSAPP_VERIFY_TOKEN', 'test-verify-token')
    monkeypatch.setenv('WHATSAPP_STATUS_TEMPLATE_NAME', 'posp_status_update')
    monkeypatch.setenv('WHATSAPP_TEMPLATE_LANGUAGE', 'en')
    application = create_app()
    application.config['TESTING'] = True
    with application.app_context():
        db.create_all()
        admin = User(email='admin@test.example', password_hash=hash_password('AdminPass123!'),
                     name='Admin', phone='9999999999', is_admin=True, is_active=True)
        client = User(email='client@test.example', password_hash=hash_password('ClientPass123!'),
                      name='Test Client', phone='9876543210', is_admin=False, is_active=True)
        db.session.add_all([admin, client])
        db.session.commit()
        order = Order(order_code='POSP-2026-TEST1', client_name='Test Client',
                      phone='9876543210', email='client@test.example',
                      contact_method='whatsapp', user_id=client.id, status='Submitted')
        db.session.add(order)
        db.session.commit()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _auth(app, email):
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        return {'Authorization': f'Bearer {create_token({"user_id": user.id, "token_version": user.token_version or 0})}'}


def _signed(body: bytes):
    digest = hmac.new(b'test-app-secret', body, hashlib.sha256).hexdigest()
    return f'sha256={digest}'


def test_webhook_verification_and_signature(client):
    resp = client.get('/api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=test-verify-token&hub.challenge=abc123')
    assert resp.status_code == 200
    assert resp.data == b'abc123'
    resp = client.get('/api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=abc123')
    assert resp.status_code == 403
    resp = client.post('/api/whatsapp/webhook', data=b'{}', headers={'X-Hub-Signature-256': 'sha256=bad'})
    assert resp.status_code == 403


def test_inbound_dedup_and_support_handoff(client, app):
    import json
    payload = {
        'entry': [{'changes': [{'value': {
            'messages': [{'id': 'wamid.test1', 'from': '919876543210', 'type': 'text',
                          'text': {'body': 'Hello, what is my application status?'}}],
            'statuses': [],
        }}]}]
    }
    body = json.dumps(payload).encode()
    headers = {'X-Hub-Signature-256': _signed(body), 'Content-Type': 'application/json'}
    assert client.post('/api/whatsapp/webhook', data=body, headers=headers).status_code == 200
    # Same Meta message id again must not duplicate.
    assert client.post('/api/whatsapp/webhook', data=body, headers=headers).status_code == 200
    with app.app_context():
        assert WhatsAppMessage.query.filter_by(wa_message_id='wamid.test1').count() == 1
        from app.models.support_message import SupportMessage
        assert SupportMessage.query.filter_by(message='Hello, what is my application status?').count() == 1


def test_status_notification_dedup_and_opt_in(client, app):
    from app.services.whatsapp_notify import notify_status_change, notify_confirmation

    class FakeResponse:
        status_code = 200
        content = b'{"messages": [{"id": "wamid.out1"}]}'

        def json(self):
            return {'messages': [{'id': 'wamid.out1'}]}

        def raise_for_status(self):
            return None

    with mock.patch('app.services.whatsapp.requests.post', return_value=FakeResponse()) as post:
        with app.app_context():
            order = Order.query.filter_by(order_code='POSP-2026-TEST1').first()
            assert notify_status_change(order, 'Under Review') is True
            assert notify_status_change(order, 'Under Review') is True
            # One send only, despite two calls for the same transition.
            assert post.call_count == 1
            assert WhatsAppMessage.query.filter_by(event_key='order:1:status:Under Review').count() == 1
            # Opt-out stops future sends.
            order.contact_method = None
            db.session.commit()
            assert notify_confirmation(order) is False


def test_admin_endpoints_require_admin(client, app):
    # No token -> 401, client token -> 401, admin token -> 200.
    assert client.get('/api/whatsapp/admin/status').status_code == 401
    assert client.get('/api/whatsapp/admin/status', headers=_auth(app, 'client@test.example')).status_code == 401
    resp = client.get('/api/whatsapp/admin/status', headers=_auth(app, 'admin@test.example'))
    assert resp.status_code == 200
    assert 'cloud_api_enabled' in resp.get_json()
    assert 'WHATSAPP_ACCESS_TOKEN' not in resp.get_data(as_text=True)
    assert 'test-token-not-real' not in resp.get_data(as_text=True)


def test_failed_retry_endpoint(client, app):
    with app.app_context():
        order = Order.query.filter_by(order_code='POSP-2026-TEST1').first()
        row = WhatsAppMessage(direction='outbound', order_id=order.id, user_id=order.user_id,
                              to_number='919876543210', message_type='template',
                              template_name='posp_status_update', status='failed',
                              event_key='order:1:status:Under Review')
        db.session.add(row)
        db.session.commit()
        message_id = row.id

    class FakeResponse:
        status_code = 200
        content = b'{"messages": [{"id": "wamid.out2"}]}'

        def json(self):
            return {'messages': [{'id': 'wamid.out2'}]}

        def raise_for_status(self):
            return None

    with mock.patch('app.services.whatsapp.requests.post', return_value=FakeResponse()):
        resp = client.post(f'/api/whatsapp/admin/messages/{message_id}/retry',
                           headers=_auth(app, 'admin@test.example'))
        assert resp.status_code == 200
    with app.app_context():
        assert WhatsAppMessage.query.filter_by(event_key='order:1:status:Under Review', status='sent').count() == 1


def test_admin_reply_requires_24h_window(client, app):
    # No recent inbound -> 409, not a silent template send.
    resp = client.post('/api/whatsapp/admin/reply', json={'user_id': 2, 'message': 'Hello'},
                       headers=_auth(app, 'admin@test.example'))
    assert resp.status_code == 409
    # Recent inbound -> text send succeeds (mocked).
    with app.app_context():
        db.session.add(WhatsAppMessage(direction='inbound', wa_message_id='wamid.recent',
                                       user_id=2, from_number='919876543210',
                                       message_type='text', body='Hi', status='received'))
        db.session.commit()

    class FakeResponse:
        status_code = 200
        content = b'{"messages": [{"id": "wamid.reply1"}]}'

        def json(self):
            return {'messages': [{'id': 'wamid.reply1'}]}

        def raise_for_status(self):
            return None

    with mock.patch('app.services.whatsapp.requests.post', return_value=FakeResponse()):
        resp = client.post('/api/whatsapp/admin/reply', json={'user_id': 2, 'message': 'Hello, we are on it.'},
                           headers=_auth(app, 'admin@test.example'))
        assert resp.status_code == 200


def test_admin_document_event(client, app):
    class FakeResponse:
        status_code = 200
        content = b'{"messages": [{"id": "wamid.doc1"}]}'

        def json(self):
            return {'messages': [{'id': 'wamid.doc1'}]}

        def raise_for_status(self):
            return None

    with mock.patch('app.services.whatsapp.requests.post', return_value=FakeResponse()):
        resp = client.post('/api/whatsapp/admin/orders/1/document-event',
                           json={'event': 'Documents Received'},
                           headers=_auth(app, 'admin@test.example'))
        assert resp.status_code == 200


def test_same_body_with_distinct_meta_ids_is_not_collapsed(client, app):
    import json
    for message_id in ('wamid.same-body-1', 'wamid.same-body-2'):
        payload = {'entry': [{'changes': [{'value': {
            'messages': [{'id': message_id, 'from': '919876543210', 'type': 'text',
                          'text': {'body': 'Hello'}}],
            'statuses': [],
        }}]}]}
        body = json.dumps(payload).encode()
        response = client.post('/api/whatsapp/webhook', data=body, headers={
            'X-Hub-Signature-256': _signed(body), 'Content-Type': 'application/json',
        })
        assert response.status_code == 200
    with app.app_context():
        from app.models.support_message import SupportMessage
        assert WhatsAppMessage.query.filter(WhatsAppMessage.wa_message_id.like('wamid.same-body-%')).count() == 2
        assert SupportMessage.query.filter_by(message='Hello').count() == 2


def test_delivery_status_does_not_regress(client, app):
    import json
    with app.app_context():
        db.session.add(WhatsAppMessage(direction='outbound', wa_message_id='wamid.monotonic',
                                       order_id=1, user_id=2, to_number='919876543210',
                                       message_type='template', status='read'))
        db.session.commit()
    payload = {'entry': [{'changes': [{'value': {
        'messages': [],
        'statuses': [{'id': 'wamid.monotonic', 'status': 'delivered'}],
    }}]}]}
    body = json.dumps(payload).encode()
    assert client.post('/api/whatsapp/webhook', data=body, headers={
        'X-Hub-Signature-256': _signed(body), 'Content-Type': 'application/json',
    }).status_code == 200
    with app.app_context():
        assert WhatsAppMessage.query.filter_by(wa_message_id='wamid.monotonic').one().status == 'read'


def test_24h_window_queries_beyond_first_200_rows(app):
    with app.app_context():
        recent = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=5)
        db.session.add(WhatsAppMessage(direction='inbound', wa_message_id='wamid.target-window',
                                       user_id=2, from_number='919876543210',
                                       message_type='text', body='Hi', status='received',
                                       created_at=recent))
        for index in range(201):
            db.session.add(WhatsAppMessage(direction='inbound', wa_message_id=f'wamid.other-{index}',
                                           from_number=f'91980000{index:04d}', message_type='text',
                                           body='Other', status='received',
                                           created_at=recent + timedelta(seconds=index + 1)))
        db.session.commit()
        assert wa.last_inbound_within_24h('09876543210') is True


def test_whatsapp_retention_is_dry_run_by_default_and_explicitly_deletes_old_rows(app):
    from app.utils.whatsapp_retention import purge_whatsapp_messages

    old = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=91)
    with app.app_context():
        row = WhatsAppMessage(direction='inbound', wa_message_id='wamid.retention-old',
                              from_number='919876543210', message_type='text', body='Old',
                              status='received', created_at=old)
        db.session.add(row)
        db.session.commit()
        preview = purge_whatsapp_messages()
        assert preview['mode'] == 'dry-run'
        assert preview['matched_messages'] == 1
        assert WhatsAppMessage.query.filter_by(wa_message_id='wamid.retention-old').one()
        applied = purge_whatsapp_messages(apply=True)
        assert applied['deleted_messages'] == 1
        assert WhatsAppMessage.query.filter_by(wa_message_id='wamid.retention-old').first() is None
