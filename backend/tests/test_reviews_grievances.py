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
    r = client.post('/api/auth/register', json={'name':'G User','phone':'7777777777','email': 'guser@example.com', 'password': 'strong-pass'})
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
    r = client.post('/api/auth/register', json={'name':'Help User','phone':'7666666666','email':'help@example.com','password':'strong-pass'})
    token = r.get_json()['token']
    r = client.post('/api/grievances/', json={'description': 'I need general account support.'}, headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 201
    grievance = r.get_json()['grievance']
    assert grievance['order_id'] is None
    assert grievance['grievance_code'].startswith('GV-')


def test_client_can_track_only_their_own_grievances_and_admin_response(client):
    first = client.post('/api/auth/register', json={'name':'First Client','phone':'7555555555','email':'first-grievance@example.com','password':'strong-pass'})
    second = client.post('/api/auth/register', json={'name':'Second Client','phone':'7444444444','email':'second-grievance@example.com','password':'strong-pass'})
    first_headers = {'Authorization': f"Bearer {first.get_json()['token']}"}
    second_headers = {'Authorization': f"Bearer {second.get_json()['token']}"}
    created = client.post('/api/grievances/', json={'description':'Please help with my private account issue.'}, headers=first_headers)
    assert created.status_code == 201
    grievance = created.get_json()['grievance']

    first_list = client.get('/api/grievances/mine', headers=first_headers)
    second_list = client.get('/api/grievances/mine', headers=second_headers)
    assert [item['id'] for item in first_list.get_json()['items']] == [grievance['id']]
    assert second_list.get_json()['items'] == []
    assert client.get(f"/api/grievances/{grievance['id']}", headers=second_headers).status_code == 404

    admin_headers = {'Authorization': f'Bearer {_create_admin(client)}'}
    missing_response = client.post(
        f"/api/grievances/admin/{grievance['id']}/status",
        json={'status':'Resolved'}, headers=admin_headers,
    )
    assert missing_response.status_code == 400
    updated = client.post(
        f"/api/grievances/admin/{grievance['id']}/status",
        json={'status':'Resolved','response':'We reviewed and resolved your account issue.'},
        headers=admin_headers,
    )
    assert updated.status_code == 200
    tracked = client.get(f"/api/grievances/{grievance['id']}", headers=first_headers).get_json()['grievance']
    assert tracked['status'] == 'Resolved'
    assert tracked['admin_response'] == 'We reviewed and resolved your account issue.'
    assert [entry['new_status'] for entry in tracked['history']] == ['New', 'Resolved']
    assert all('changed_by' not in entry for entry in tracked['history'])
    notifications = client.get('/api/notifications', headers=first_headers).get_json()['items']
    assert any(grievance['grievance_code'] in item['message'] for item in notifications)


def test_review_flow_and_publish(client):
    service_id = _create_service(client)
    r = client.post('/api/auth/register', json={'name':'R User','phone':'8888888888','email':'ruser@example.com','password':'strong-pass'})
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
    published = next(p for p in pubs if p['id'] == rid)
    assert published['reviewer'] == 'Verified client'
    assert 'client_name' not in published
    assert 'order_id' not in published
