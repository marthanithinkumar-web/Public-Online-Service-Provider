from app.utils.password import hash_password
from app.utils.database import db
from app.models.user import User
from app.models.service import Category, Service


def test_order_lifecycle_and_admin_controls(client):
    # create category and service
    with client.application.app_context():
        # Use existing seeded defaults if present, otherwise create them.
        cat = Category.query.filter_by(name='Certificates').first()
        if cat is None:
            cat = Category(name='Certificates')
            db.session.add(cat)
            db.session.commit()
        svc = Service.query.filter_by(name='Residence Certificate').first()
        if svc is None:
            svc = Service(name='Residence Certificate', description='Residence proof', price_inr=30.0, category=cat)
            db.session.add(svc)
            db.session.commit()
        service_id = svc.id

    # register user1
    r = client.post('/api/auth/register', json={'name':'User One','phone':'9990001111','email': 'user1@example.com', 'password': 'pass1'})
    assert r.status_code == 200
    data = r.get_json()
    token1 = data['token']

    # register user2
    r = client.post('/api/auth/register', json={'name':'User Two','phone':'9990002222','email': 'user2@example.com', 'password': 'pass2'})
    assert r.status_code == 200
    token2 = r.get_json()['token']

    headers1 = {'Authorization': f'Bearer {token1}'}
    headers2 = {'Authorization': f'Bearer {token2}'}

    # user1 creates an order
    order_payload = {
        'client_name': 'User One',
        'phone': '9990001111',
        'email': 'user1@example.com',
        'service_id': service_id,
        'description': 'Please help with residence certificate'
    }
    r = client.post('/api/orders/', json=order_payload, headers=headers1)
    assert r.status_code == 200
    order = r.get_json()['order']
    order_id = order['id']
    order_code = order['order_code']

    # user2 should NOT be able to view user1's order with their token
    r = client.get(f'/api/orders/{order_id}', headers=headers2)
    assert r.status_code == 401

    # user1 can view their own order
    r = client.get(f'/api/orders/{order_id}', headers=headers1)
    assert r.status_code == 200
    got = r.get_json()
    assert got['id'] == order_id

    # create admin user directly
    with client.application.app_context():
        admin = User(email='admin@example.com', password_hash=hash_password('adminpass'), is_admin=True)
        db.session.add(admin)
        db.session.commit()

    # login as admin to get token
    r = client.post('/api/auth/login', json={'email': 'admin@example.com', 'password': 'adminpass'})
    assert r.status_code == 200
    admin_token = r.get_json()['token']
    admin_headers = {'Authorization': f'Bearer {admin_token}'}

    # admin can list orders
    r = client.get('/api/admin/orders', headers=admin_headers)
    assert r.status_code == 200
    items = r.get_json()['items']
    assert any(it['id'] == order_id for it in items)

    # admin updates order status
    r = client.post(f'/api/admin/orders/{order_id}/status', json={'status': 'In Progress', 'note': 'Started processing'}, headers=admin_headers)
    assert r.status_code == 200
    data = r.get_json()
    assert data['order']['status'] == 'In Progress'

    # admin can fetch order detail including history
    r = client.get(f'/api/admin/orders/{order_id}', headers=admin_headers)
    assert r.status_code == 200
    detail = r.get_json()
    assert detail['order']['id'] == order_id
    assert len(detail['history']) >= 1
