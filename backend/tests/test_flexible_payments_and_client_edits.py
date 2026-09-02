from app.models.notification import Notification
from app.models.order import Order
from app.models.service import Category, Service
from app.models.user import User
from app.utils.database import db
from app.utils.jwt_handler import create_token
from app.utils.password import hash_password


def _client_headers(client, suffix='flex'):
    response = client.post('/api/auth/register', json={
        'name': 'Flexible Payment Client',
        'phone': '9888800001',
        'email': f'{suffix}@example.com',
        'password': 'strong-pass1',
    })
    return {'Authorization': f"Bearer {response.get_json()['token']}"}


def _admin(client):
    with client.application.app_context():
        admin = User(name='Edit Admin', email='edit-admin@example.com', phone='9000000999', password_hash=hash_password('adminpass'), is_admin=True)
        db.session.add(admin)
        db.session.commit()
        return admin.id


def _service(client, official_status='unconfirmed', official_fee=None):
    with client.application.app_context():
        category = Category.query.filter_by(name='Flexible Payment Tests').first() or Category(name='Flexible Payment Tests')
        db.session.add(category)
        db.session.flush()
        service = Service(name=f'Flexible Service {official_status} {official_fee}', description='Test service', price_inr=30, official_fee_inr=official_fee, official_fee_status=official_status, category=category, is_active=True)
        db.session.add(service)
        db.session.commit()
        return service.id


def _mock_razorpay(monkeypatch):
    monkeypatch.setenv('RAZORPAY_KEY_ID', 'rzp_test_key')
    monkeypatch.setenv('RAZORPAY_KEY_SECRET', 'secret')
    calls = []
    class Response:
        def raise_for_status(self):
            pass
        def json(self):
            return {'id': f'order_test_{len(calls)}'}
    def fake_post(url, json, auth, timeout):
        calls.append(json)
        return Response()
    monkeypatch.setattr('app.routes.payments.requests.post', fake_post)
    return calls


def test_assistance_fee_can_be_paid_while_official_fee_is_unconfirmed(client, monkeypatch):
    service_id = _service(client)
    headers = _client_headers(client, 'assist-first')
    created = client.post('/api/orders/', headers=headers, json={'service_id': service_id, 'application_data': {'purpose': 'certificate'}})
    order_id = created.get_json()['order']['id']
    calls = _mock_razorpay(monkeypatch)

    assistance = client.post(f'/api/payments/orders/{order_id}/checkout', headers=headers, json={'purpose': 'assistance_fee'})
    assert assistance.status_code == 201
    assert assistance.get_json()['amount'] == 3000
    assert calls[-1]['notes']['purpose'] == 'assistance_fee'

    official = client.post(f'/api/payments/orders/{order_id}/checkout', headers=headers, json={'purpose': 'official_fee'})
    assert official.status_code == 409
    assert 'not been confirmed' in official.get_json()['error']


def test_combined_checkout_is_available_when_both_fees_are_confirmed(client, monkeypatch):
    service_id = _service(client, 'known', 80)
    headers = _client_headers(client, 'combined')
    created = client.post('/api/orders/', headers=headers, json={'service_id': service_id, 'application_data': {'purpose': 'test'}})
    order_id = created.get_json()['order']['id']
    calls = _mock_razorpay(monkeypatch)

    checkout = client.post(f'/api/payments/orders/{order_id}/checkout', headers=headers, json={'purpose': 'request_total'})
    assert checkout.status_code == 201
    assert checkout.get_json()['amount'] == 11000
    assert calls[-1]['amount'] == 11000


def test_client_can_edit_submitted_application_and_admin_is_notified(client):
    admin_id = _admin(client)
    service_id = _service(client)
    headers = _client_headers(client, 'editing')
    created = client.post('/api/orders/', headers=headers, json={'service_id': service_id, 'application_data': {'purpose': 'old value', 'district': 'Old District'}})
    order_id = created.get_json()['order']['id']

    edited = client.put(f'/api/orders/{order_id}', headers=headers, json={'application_data': {'purpose': 'new value', 'district': 'New District'}})
    assert edited.status_code == 200
    assert 'admin has been notified' in edited.get_json()['message'].lower()

    with client.application.app_context():
        order = db.session.get(Order, order_id)
        assert order.application_data['purpose'] == 'new value'
        notice = Notification.query.filter_by(user_id=admin_id, order_id=order_id, title='Application edited by Client').first()
        assert notice is not None
        assert order.order_code in notice.message
