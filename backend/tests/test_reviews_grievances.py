from app.utils.password import hash_password
from app.utils.database import db
from app.models.user import User
from app.models.service import Category, Service


def _create_service(client):
    with client.application.app_context():
        cat = Category(name='General')
        db.session.add(cat)
        db.session.commit()
        svc = Service(name='Sample Service', description='Test', price_inr=50.0, category=cat)
        db.session.add(svc)
        db.session.commit()
        return svc.id


def _create_admin(client):
    with client.application.app_context():
        admin = User(email='admin2@example.com', password_hash=hash_password('adminpass2'), is_admin=True)
        db.session.add(admin)
        db.session.commit()
    r = client.post('/api/auth/login', json={'email': 'admin2@example.com', 'password': 'adminpass2'})
    assert r.status_code == 200
    return r.get_json()['token']


def test_grievance_flow(client):
    service_id = _create_service(client)

    # register user and create order
    r = client.post('/api/auth/register', json={'name':'G User','phone':'7777777777','email': 'guser@example.com', 'password': 'pass'})
    token = r.get_json()['token']
    headers = {'Authorization': f'Bearer {token}'}

    r = client.post('/api/orders/', json={'client_name': 'G User', 'phone': '777', 'service_id': service_id}, headers=headers)
    assert r.status_code == 200
    order = r.get_json()['order']
    order_id = order['id']

    # submit grievance
    gpay = {'client_name': 'G User', 'phone': '777', 'order_id': order_id, 'description': 'Problem with service'}
    r = client.post('/api/grievances/', json=gpay)
    assert r.status_code == 200
    grievance = r.get_json()['grievance']
    gid = grievance['id']

    # admin list and update status
    admin_token = _create_admin(client)
    admin_headers = {'Authorization': f'Bearer {admin_token}'}

    r = client.get('/api/grievances/admin', headers=admin_headers)
    assert r.status_code == 200
    items = r.get_json()['items']
    assert any(it['id'] == gid for it in items)

    r = client.post(f'/api/grievances/admin/{gid}/status', json={'status': 'Under Review'}, headers=admin_headers)
    assert r.status_code == 200
    assert r.get_json()['grievance']['status'] == 'Under Review'


def test_review_flow_and_publish(client):
    service_id = _create_service(client)
    # create order anonymously
    r = client.post('/api/orders/', json={'client_name': 'R User', 'phone': '888', 'service_id': service_id})
    assert r.status_code == 200
    order = r.get_json()['order']
    order_id = order['id']

    # submit review
    r = client.post('/api/reviews/', json={'order_id': order_id, 'rating': 5, 'comment': 'Great', 'client_name': 'R User'})
    assert r.status_code == 200
    review = r.get_json()['review']
    rid = review['id']

    # admin publishes review
    admin_token = _create_admin(client)
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    r = client.post(f'/api/reviews/admin/{rid}/publish', json={'public': True}, headers=admin_headers)
    assert r.status_code == 200

    # public reviews should include it now
    r = client.get('/api/reviews/public')
    assert r.status_code == 200
    pubs = r.get_json()
    assert any(p['id'] == rid for p in pubs)
