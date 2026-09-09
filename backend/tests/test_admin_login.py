from app.models.user import User
from app.utils.database import db
from app.utils.password import hash_password


def _create_admin(client):
    with client.application.app_context():
        db.session.add(User(
            name='Direct Login Admin',
            email='direct-login-admin@example.com',
            password_hash=hash_password('admin-password'),
            is_admin=True,
            is_active=True,
        ))
        db.session.commit()


def test_admin_login_never_requests_email_code(client, monkeypatch):
    _create_admin(client)
    # A stale production variable must not be able to restore the removed flow.
    monkeypatch.setenv('ADMIN_2FA_ENABLED', '1')

    login = client.post('/api/auth/login', json={
        'email': 'direct-login-admin@example.com',
        'password': 'admin-password',
    })

    assert login.status_code == 200
    payload = login.get_json()
    assert payload['token']
    assert payload['user']['is_admin'] is True
    assert 'requires_2fa' not in payload
    assert 'challenge_token' not in payload
    assert client.post('/api/auth/verify-admin-2fa', json={}).status_code == 404
