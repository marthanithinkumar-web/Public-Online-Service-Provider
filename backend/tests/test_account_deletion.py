from app.models.user import User
from app.models.service import Service
from app.utils.database import db


def test_client_can_delete_account_with_current_password(client):
    register = client.post(
        '/api/auth/register',
        json={'name': 'Delete Me','phone': '9991112222','email': 'delete-me@example.com', 'password': 'secret'},
    )
    assert register.status_code == 200
    token = register.get_json()['token']

    wrong_password = client.delete(
        '/api/auth/delete-account',
        headers={'Authorization': f'Bearer {token}'},
        json={'current_password': 'wrong'},
    )
    assert wrong_password.status_code == 401

    deleted = client.delete(
        '/api/auth/delete-account',
        headers={'Authorization': f'Bearer {token}'},
        json={'current_password': 'secret'},
    )
    assert deleted.status_code == 200

    with client.application.app_context():
        assert User.query.filter_by(email='delete-me@example.com').first() is None

    login_after_deletion = client.post(
        '/api/auth/login',
        json={'email': 'delete-me@example.com', 'password': 'secret'},
    )
    assert login_after_deletion.status_code == 401


def test_admin_cannot_delete_through_client_endpoint(client):
    with client.application.app_context():
        admin = User(
            email='admin-delete-protected@example.com',
            password_hash='not-used',
            is_admin=True,
        )
        db.session.add(admin)
        db.session.commit()

    # Use the normal password hashing path to obtain a valid admin token.
    from app.utils.password import hash_password
    from app.utils.jwt_handler import create_token

    with client.application.app_context():
        admin = User.query.filter_by(email='admin-delete-protected@example.com').first()
        admin.password_hash = hash_password('admin-secret')
        db.session.commit()
        token = create_token({'user_id': admin.id, 'is_admin': True})

    response = client.delete(
        '/api/auth/delete-account',
        headers={'Authorization': f'Bearer {token}'},
        json={'current_password': 'admin-secret'},
    )
    assert response.status_code == 403

    with client.application.app_context():
        assert User.query.filter_by(email='admin-delete-protected@example.com').first() is not None


def test_active_request_must_be_cancelled_before_account_deletion(client):
    with client.application.app_context():
        service = Service(name='Account Deletion Test Assistance', price_inr=30, is_active=True)
        db.session.add(service)
        db.session.commit()
        service_id = service.id

    registered = client.post('/api/auth/register', json={
        'name':'Active Request Client','phone':'9991113333',
        'email':'active-delete@example.com','password':'secret123',
    })
    owner_headers = {'Authorization': f"Bearer {registered.get_json()['token']}"}
    other = client.post('/api/auth/register', json={
        'name':'Different Client','phone':'9991114444',
        'email':'other-cancel@example.com','password':'secret123',
    })
    other_headers = {'Authorization': f"Bearer {other.get_json()['token']}"}
    submitted = client.post('/api/orders/', json={
        'service_id':service_id,
        'application_data':{'assistance_type':'Please help with this service'},
    }, headers=owner_headers)
    assert submitted.status_code == 201
    order = submitted.get_json()['order']

    blocked = client.delete('/api/auth/delete-account', json={'current_password':'secret123'}, headers=owner_headers)
    assert blocked.status_code == 409
    assert blocked.get_json()['active_requests'][0]['order_code'] == order['order_code']

    forbidden = client.post(f"/api/orders/{order['id']}/cancel", headers=other_headers)
    assert forbidden.status_code == 403
    cancelled = client.post(f"/api/orders/{order['id']}/cancel", headers=owner_headers)
    assert cancelled.status_code == 200
    assert cancelled.get_json()['order']['status'] == 'Cancelled'
    assert client.post(f"/api/orders/{order['id']}/cancel", headers=owner_headers).status_code == 409

    deleted = client.delete('/api/auth/delete-account', json={'current_password':'secret123'}, headers=owner_headers)
    assert deleted.status_code == 200


def test_client_cannot_directly_cancel_request_after_processing_starts(client):
    with client.application.app_context():
        service = Service(name='Started Processing Test Assistance', price_inr=30, is_active=True)
        db.session.add(service)
        db.session.commit()
        service_id = service.id
    registered = client.post('/api/auth/register', json={
        'name':'Processing Client','phone':'9991115555',
        'email':'processing-cancel@example.com','password':'secret123',
    })
    headers = {'Authorization': f"Bearer {registered.get_json()['token']}"}
    submitted = client.post('/api/orders/', json={
        'service_id':service_id,
        'application_data':{'assistance_type':'Please process this request'},
    }, headers=headers)
    order_id = submitted.get_json()['order']['id']
    with client.application.app_context():
        from app.models.order import Order
        order = db.session.get(Order, order_id)
        order.status = 'In Progress'
        db.session.commit()
    response = client.post(f'/api/orders/{order_id}/cancel', headers=headers)
    assert response.status_code == 409
    assert response.get_json()['status'] == 'In Progress'
