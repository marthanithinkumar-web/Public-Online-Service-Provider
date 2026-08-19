from app.models.user import User
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
