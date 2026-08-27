from app.models.user import User
from app.utils.database import db
from app.utils.password import hash_password


def _register(client, email, name):
    response = client.post('/api/auth/register', json={
        'name': name,
        'phone': '9000000000',
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
