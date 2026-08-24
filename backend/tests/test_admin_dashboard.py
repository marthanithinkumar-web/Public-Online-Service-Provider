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


def test_admin_status_update_reaches_client_notifications(client):
    client_token, admin_token, order = _setup_flow(client)
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    client_headers = {'Authorization': f'Bearer {client_token}'}

    overview = client.get('/api/admin/overview', headers=admin_headers)
    assert overview.status_code == 200
    assert overview.get_json()['total_requests'] == 1
    assert overview.get_json()['counts']['New'] == 1

    search = client.get('/api/admin/orders?q=Dashboard+Client', headers=admin_headers)
    assert search.status_code == 200
    assert search.get_json()['items'][0]['id'] == order['id']

    update = client.post(f"/api/admin/orders/{order['id']}/status", json={'status': 'Under Review', 'note': 'We are checking your application.'}, headers=admin_headers)
    assert update.status_code == 200

    mine = client.get('/api/orders/mine', headers=client_headers)
    assert mine.status_code == 200
    assert mine.get_json()[0]['status'] == 'Under Review'

    notifications = client.get('/api/notifications', headers=client_headers)
    assert notifications.status_code == 200
    body = notifications.get_json()
    assert body['unread'] == 1
    assert order['order_code'] in body['items'][0]['message']

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
