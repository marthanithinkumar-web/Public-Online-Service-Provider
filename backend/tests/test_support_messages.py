from app.models.user import User
from app.utils.database import db
from app.utils.password import hash_password


def _register(client, email, name):
    response = client.post('/api/auth/register', json={
        'name': name,
        'phone': '9000000002' if 'two' in email else '9000000001',
        'email': email,
        'password': 'strong-pass',
    })
    return response.get_json()['token']


def _admin_token(client):
    with client.application.app_context():
        db.session.add(User(
            name='Support Admin',
            email='support-admin@example.com',
            password_hash=hash_password('admin-pass'),
            is_admin=True,
        ))
        db.session.commit()
    response = client.post('/api/auth/login', json={'email': 'support-admin@example.com', 'password': 'admin-pass'})
    return response.get_json()['token']


def test_support_chat_requires_registered_client(client):
    assert client.get('/api/messages/mine').status_code == 401
    assert client.post('/api/messages/mine', json={'message': 'Hello'}).status_code == 401


def test_private_client_admin_messaging_and_notifications(client):
    first_token = _register(client, 'chat-one@example.com', 'Chat One')
    second_token = _register(client, 'chat-two@example.com', 'Chat Two')
    admin_token = _admin_token(client)
    first_headers = {'Authorization': f'Bearer {first_token}'}
    second_headers = {'Authorization': f'Bearer {second_token}'}
    admin_headers = {'Authorization': f'Bearer {admin_token}'}

    sent = client.post('/api/messages/mine', json={'message': 'Please help me choose a certificate service.'}, headers=first_headers)
    assert sent.status_code == 201
    first_user_id = sent.get_json()['item']['user_id']

    assert client.get('/api/messages/mine', headers=second_headers).get_json()['items'] == []
    threads = client.get('/api/messages/admin', headers=admin_headers)
    assert threads.status_code == 200
    assert threads.get_json()['items'][0]['unread'] == 1

    assert client.get(f'/api/messages/admin/{first_user_id}', headers=second_headers).status_code == 401
    replied = client.post(
        f'/api/messages/admin/{first_user_id}',
        json={'message': 'We can help. Please select the relevant certificate service.'},
        headers=admin_headers,
    )
    assert replied.status_code == 201
    assert 'sender_user_id' not in replied.get_json()['item']

    own_thread = client.get('/api/messages/mine', headers=first_headers).get_json()
    assert len(own_thread['items']) == 2
    assert own_thread['unread'] == 1
    notices = client.get('/api/notifications', headers=first_headers).get_json()
    assert any(item['title'] == 'New message from support' for item in notices['items'])
    assert client.post('/api/messages/mine/read', headers=first_headers).status_code == 200
    assert client.get('/api/messages/mine', headers=first_headers).get_json()['unread'] == 0


def test_express_request_accepts_optional_application_details(client):
    token = _register(client, 'express@example.com', 'Express Client')
    with client.application.app_context():
        from app.models.service import Service
        service_id = Service.query.filter_by(is_active=True).first().id
    response = client.post(
        '/api/orders/',
        json={'service_id': service_id},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 201
    assert response.get_json()['order']['application_data']['request_mode'] == 'express'


def test_client_ai_error_logs_do_not_include_client_identifier(client, monkeypatch, caplog):
    from app.routes import ai_operations

    token = _register(client, 'privacy-log@example.com', 'Privacy Log Client')

    def fail_provider(*args, **kwargs):
        raise RuntimeError('provider unavailable')

    monkeypatch.setattr(ai_operations, 'generate_client_reply', fail_provider)
    caplog.set_level('ERROR', logger='app.routes.messages')
    response = client.post(
        '/api/messages/mine',
        json={'message': 'Please help with my application.', 'use_ai': True},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 201
    assert 'client_id=' not in caplog.text
    assert 'error_type=RuntimeError' in caplog.text



def test_support_sends_to_ai_only_with_explicit_boolean_opt_in(client, monkeypatch):
    from app.routes import ai_operations

    monkeypatch.setenv('POSP_CLIENT_AI_ENABLED', 'true')
    token = _register(client, 'opt-in@example.com', 'Consent Test')
    headers = {'Authorization': f'Bearer {token}'}
    calls = []

    def provider(user, message):
        calls.append(message)
        return None, True, None

    monkeypatch.setattr(ai_operations, 'generate_client_reply', provider)
    for options in ({}, {'use_ai': False}, {'use_ai': 'true'}, {'use_ai': True}):
        response = client.post('/api/messages/mine', headers=headers,
                               json={'message': 'Support question', **options})
        assert response.status_code == 201
    assert calls == ['Support question']

def test_opt_in_faq_stream_replaces_failed_partial_and_persists_only_final(client, monkeypatch):
    import json
    from app.ai import free_router as router
    token = _register(client, 'stream-one@example.com', 'Client')
    _admin_token(client)
    monkeypatch.setenv('POSP_CLIENT_AI_ENABLED', 'true')
    monkeypatch.setenv('POSP_AI_PROVIDER', 'builtin')
    monkeypatch.setenv('POSP_CLIENT_AI_PRIORITY', 'groq')
    monkeypatch.setattr(router, '_cache', {})
    monkeypatch.setattr(router, '_cooldown', {})
    monkeypatch.setattr(router.FreeTransport, 'eligible', lambda self: self.name == 'groq')
    def interrupted(self, role, prompt):
        assert role == 'client'
        assert 'stream-one' not in prompt and prompt.startswith('Explain that POSP')
        yield 'unfinished'
        raise TimeoutError()
    monkeypatch.setattr(router.FreeTransport, 'stream_prompt', interrupted)
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/x-ndjson'}
    sent = client.post('/api/messages/mine', headers=headers, buffered=True,
                       json={'message':'What is POSP?', 'use_ai':True})
    assert sent.status_code == 201 and sent.mimetype == 'application/x-ndjson'
    events = [json.loads(line) for line in sent.data.splitlines()]
    assert events[:2] == [{'text':'unfinished'}, {'reset':True}]
    final = events[-1]['done']
    assert final['ai_item']['message'] == router._LOCAL['help', 'English']
    history = client.get('/api/messages/mine', headers=headers).get_json()['items']
    assert [row['id'] for row in history] == [final['item']['id'], final['ai_item']['id']]


def test_stream_requires_exact_public_topic_and_explicit_consent(client, monkeypatch):
    token = _register(client, 'privacy-one@example.com', 'Client')
    headers = {'Authorization': f'Bearer {token}', 'Accept':'application/x-ndjson'}
    monkeypatch.setenv('POSP_CLIENT_AI_ENABLED', 'true')
    monkeypatch.setenv('POSP_AI_PROVIDER', 'builtin')
    def forbidden(*args):
        raise AssertionError('Unexpected external stream')
    monkeypatch.setattr('app.ai.free_router.stream_client_faq', forbidden)
    for message, consent in [('What is POSP?', False), ('What is POSP? My password is private.', True)]:
        sent = client.post('/api/messages/mine', headers=headers, json={'message':message,'use_ai':consent})
        assert sent.is_json and sent.get_json()['ai_handoff']
