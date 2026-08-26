from app.models.notification import Notification
from app.models.service import Category, Service
from app.models.user import User
from app.utils.database import db
from app.utils.password import hash_password


def _setup_flow(client):
    with client.application.app_context():
        category = Category(name='General Admin Test')
        service = Service(name='Admin Test Assistance', description='Test service', price_inr=75, category=category)
        admin = User(name='Dashboard Admin', email='dashboard-admin@example.com', phone='9000000000', password_hash=hash_password('adminpass'), is_admin=True)
        db.session.add_all([category, service, admin])
        db.session.commit()
        service_id = service.id

    register = client.post('/api/auth/register', json={'name': 'Dashboard Client', 'phone': '9111111111', 'email': 'dashboard-client@example.com', 'password': 'clientpass'})
    client_token = register.get_json()['token']
    login = client.post('/api/auth/login', json={'email': 'dashboard-admin@example.com', 'password': 'adminpass'})
    admin_token = login.get_json()['token']
    order = client.post('/api/orders/', json={'service_id': service_id, 'application_data': {'assistance_type': 'Please help with my application'}}, headers={'Authorization': f'Bearer {client_token}'})
    return client_token, admin_token, order.get_json()['order']


def test_admin_dashboard_requires_admin(client):
    assert client.get('/api/admin/overview').status_code == 401
    token, _, _ = _setup_flow(client)
    headers = {'Authorization': f'Bearer {token}'}
    assert client.get('/api/admin/overview', headers=headers).status_code == 401
    assert client.get('/api/admin/documents', headers=headers).status_code == 401
    assert client.get('/api/admin/reports/requests.csv', headers=headers).status_code == 401
    assert client.post('/api/auth/register-admin', json={'email': 'attacker@example.com', 'password': 'pass', 'admin_secret': 'anything'}).status_code == 404


def test_admin_client_management_does_not_expose_destructive_delete(client):
    _, admin_token, _ = _setup_flow(client)
    with client.application.app_context():
        target_id = User.query.filter_by(email='dashboard-client@example.com').first().id
    response = client.delete(
        f'/api/admin/users/{target_id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )
    assert response.status_code == 405


def test_admin_status_update_reaches_client_notifications(client):
    client_token, admin_token, order = _setup_flow(client)
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    client_headers = {'Authorization': f'Bearer {client_token}'}

    overview = client.get('/api/admin/overview', headers=admin_headers)
    assert overview.status_code == 200
    assert overview.get_json()['total_requests'] == 1
    assert overview.get_json()['counts']['Submitted'] == 1

    search = client.get('/api/admin/orders?q=Dashboard+Client', headers=admin_headers)
    assert search.status_code == 200
    assert search.get_json()['items'][0]['id'] == order['id']

    update = client.post(f"/api/admin/orders/{order['id']}/status", json={'status': 'Under Review', 'note': 'We are checking your application.'}, headers=admin_headers)
    assert update.status_code == 200

    mine = client.get('/api/orders/mine', headers=client_headers)
    assert mine.status_code == 200
    assert mine.get_json()[0]['status'] == 'Under Review'
    assert mine.get_json()[0]['updated_at'] >= mine.get_json()[0]['created_at']

    notifications = client.get('/api/notifications', headers=client_headers)
    assert notifications.status_code == 200
    body = notifications.get_json()
    assert body['unread'] == 1
    assert order['order_code'] in body['items'][0]['message']

    detail = client.get(f"/api/orders/{order['id']}", headers=client_headers)
    assert detail.status_code == 200
    assert detail.get_json()['notifications'][0]['order_id'] == order['id']

    with client.application.app_context():
        assert Notification.query.count() == 1


def test_admin_can_send_notification_and_update_profile(client):
    client_token, admin_token, order = _setup_flow(client)
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    client_headers = {'Authorization': f'Bearer {client_token}'}

    with client.application.app_context():
        target = User.query.filter_by(email='dashboard-client@example.com').first()
        target_id = target.id

    sent = client.post('/api/admin/notifications', json={'user_id': target_id, 'order_id': order['id'], 'title': 'Document reminder', 'message': 'Please review the document requirements.'}, headers=admin_headers)
    assert sent.status_code == 201
    assert client.get('/api/notifications', headers=client_headers).get_json()['unread'] == 1

    profile = client.put('/api/admin/profile', json={'name': 'Updated Dashboard Admin', 'phone': '9222222222'}, headers=admin_headers)
    assert profile.status_code == 200
    assert profile.get_json()['user']['name'] == 'Updated Dashboard Admin'

    report = client.get('/api/admin/reports/requests.csv', headers=admin_headers)
    assert report.status_code == 200
    assert order['order_code'] in report.get_data(as_text=True)

    summary = client.get('/api/admin/reports/summary?status=Submitted', headers=admin_headers)
    assert summary.status_code == 200
    assert summary.get_json()['total'] == 1
    assert summary.get_json()['counts']['Submitted'] == 1
    assert client.get('/api/admin/reports/summary?status=Invalid', headers=admin_headers).status_code == 400
    assert client.get('/api/admin/reports/requests.csv?date_from=not-a-date', headers=admin_headers).status_code == 400


def test_admin_system_readiness_reports_missing_and_configured_controls(client, monkeypatch):
    _, admin_token, _ = _setup_flow(client)
    headers = {'Authorization': f'Bearer {admin_token}'}
    assert client.get('/api/admin/system-readiness').status_code == 401
    missing = client.get('/api/admin/system-readiness', headers=headers)
    assert missing.status_code == 200
    missing_checks = {item['key']:item['ready'] for item in missing.get_json()['checks']}
    assert missing_checks['document_storage'] is False

    monkeypatch.setenv('SECRET_KEY', 'a-production-secret-key-that-is-long-enough')
    monkeypatch.setenv('S3_BUCKET', 'documents')
    monkeypatch.setenv('SMTP_HOST', 'smtp.example.com')
    monkeypatch.setenv('SMTP_PORT', '587')
    monkeypatch.setenv('ADMIN_2FA_ENABLED', '1')
    monkeypatch.setenv('RATELIMIT_STORAGE_URI', 'redis://cache.example.com/0')
    monkeypatch.setenv('FORCE_HTTPS', '1')
    configured = client.get('/api/admin/system-readiness', headers=headers).get_json()
    assert configured['ready'] is True


def test_admin_can_suspend_client_and_invalidate_existing_token(client):
    client_token, admin_token, _ = _setup_flow(client)
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    client_headers = {'Authorization': f'Bearer {client_token}'}
    with client.application.app_context():
        target_id = User.query.filter_by(email='dashboard-client@example.com').first().id

    suspended = client.post(f'/api/admin/users/{target_id}/active', json={'active': False}, headers=admin_headers)
    assert suspended.status_code == 200
    assert suspended.get_json()['user']['is_active'] is False
    assert client.get('/api/orders/mine', headers=client_headers).status_code == 401
    assert client.post('/api/auth/login', json={'email': 'dashboard-client@example.com', 'password': 'clientpass'}).status_code == 403

    reactivated = client.post(f'/api/admin/users/{target_id}/active', json={'active': True}, headers=admin_headers)
    assert reactivated.status_code == 200
    login = client.post('/api/auth/login', json={'email': 'dashboard-client@example.com', 'password': 'clientpass'})
    assert login.status_code == 200
    assert client.get('/api/orders/mine', headers={'Authorization': f"Bearer {login.get_json()['token']}"}).status_code == 200


def test_logout_revokes_token(client):
    client_token, _, _ = _setup_flow(client)
    headers = {'Authorization': f'Bearer {client_token}'}
    assert client.get('/api/orders/mine', headers=headers).status_code == 200
    assert client.post('/api/auth/logout', headers=headers).status_code == 200
    assert client.get('/api/orders/mine', headers=headers).status_code == 401


def test_optional_admin_two_factor_login(client, monkeypatch):
    _, _, _ = _setup_flow(client)
    delivered = {}
    monkeypatch.setenv('ADMIN_2FA_ENABLED', '1')

    def capture_email(address, subject, body):
        delivered['address'] = address
        delivered['code'] = body.split(' is ', 1)[1].split('.', 1)[0]
        return True

    monkeypatch.setattr('app.routes.auth.send_email', capture_email)
    login = client.post('/api/auth/login', json={'email': 'dashboard-admin@example.com', 'password': 'adminpass'})
    assert login.status_code == 202
    assert login.get_json()['requires_2fa'] is True
    assert delivered['address'] == 'dashboard-admin@example.com'

    verified = client.post('/api/auth/verify-admin-2fa', json={
        'challenge_token': login.get_json()['challenge_token'],
        'code': delivered['code'],
    })
    assert verified.status_code == 200
    assert verified.get_json()['user']['is_admin'] is True
