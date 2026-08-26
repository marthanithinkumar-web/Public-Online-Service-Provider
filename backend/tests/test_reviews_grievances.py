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

    r = client.post('/api/orders/', json={'service_id': service_id, 'application_data': {'assistance_type': 'Application help'}}, headers=headers)
    assert r.status_code == 201
    order = r.get_json()['order']
    order_id = order['id']

    # submit grievance
    gpay = {'order_id': order_id, 'description': 'Problem with service'}
    r = client.post('/api/grievances/', json=gpay, headers=headers)
    assert r.status_code == 201
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


def test_general_grievance_does_not_require_internal_order_id(client):
    r = client.post('/api/auth/register', json={'name':'Help User','phone':'7666666666','email':'help@example.com','password':'pass'})
    token = r.get_json()['token']
    r = client.post('/api/grievances/', json={'description': 'I need general account support.'}, headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 201
    grievance = r.get_json()['grievance']
    assert grievance['order_id'] is None
    assert grievance['grievance_code'].startswith('GV-')


def test_review_flow_and_publish(client):
    service_id = _create_service(client)
    r = client.post('/api/auth/register', json={'name':'R User','phone':'8888888888','email':'ruser@example.com','password':'pass'})
    token = r.get_json()['token']
    headers = {'Authorization': f'Bearer {token}'}
    r = client.post('/api/orders/', json={'service_id': service_id, 'application_data': {'assistance_type': 'Application help'}}, headers=headers)
    assert r.status_code == 201
    order = r.get_json()['order']
    order_id = order['id']

    admin_token = _create_admin(client)
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    r = client.post(f'/api/admin/orders/{order_id}/status', json={'status': 'Under Review'}, headers=admin_headers)
    assert r.status_code == 200
    r = client.post(f'/api/admin/orders/{order_id}/status', json={'status': 'In Progress'}, headers=admin_headers)
    assert r.status_code == 200
    r = client.post(f'/api/admin/orders/{order_id}/status', json={'status': 'Completed', 'note': 'Completed.'}, headers=admin_headers)
    assert r.status_code == 200

    r = client.post('/api/reviews/', json={'order_id': order_id, 'rating': 5, 'comment': 'Great'}, headers=headers)
    assert r.status_code == 201
    review = r.get_json()['review']
    rid = review['id']

    # admin publishes review
    r = client.post(f'/api/reviews/admin/{rid}/publish', json={'public': True}, headers=admin_headers)
    assert r.status_code == 200

    # public reviews should include it now
    r = client.get('/api/reviews/public')
    assert r.status_code == 200
    pubs = r.get_json()
    assert any(p['id'] == rid for p in pubs)
