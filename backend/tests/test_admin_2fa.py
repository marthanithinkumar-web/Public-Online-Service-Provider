import re

from app.models.security import AdminLoginChallenge
from app.models.user import User
from app.utils.database import db
from app.utils.password import hash_password


def _create_admin(client, email='two-factor-admin@example.com', password='admin-password'):
    with client.application.app_context():
        admin = User(
            name='Two Factor Admin',
            email=email,
            password_hash=hash_password(password),
            is_admin=True,
            is_active=True,
        )
        db.session.add(admin)
        db.session.commit()
        return admin.id


def test_admin_2fa_requires_email_code_before_issuing_admin_token(client, monkeypatch):
    _create_admin(client)
    monkeypatch.setenv('ADMIN_2FA_ENABLED', '1')
    captured = {}

    def capture_email(address, subject, body):
        captured.update(address=address, subject=subject, body=body)
        return True

    monkeypatch.setattr('app.routes.auth.send_email', capture_email)
    login = client.post('/api/auth/login', json={
        'email': 'two-factor-admin@example.com',
        'password': 'admin-password',
    })
    assert login.status_code == 202
    payload = login.get_json()
    assert payload['requires_2fa'] is True
    assert payload['challenge_token']
    assert 'token' not in payload
    assert captured['address'] == 'two-factor-admin@example.com'

    match = re.search(r'\b(\d{6})\b', captured['body'])
    assert match is not None
    verified = client.post('/api/auth/verify-admin-2fa', json={
        'challenge_token': payload['challenge_token'],
        'code': match.group(1),
    })
    assert verified.status_code == 200
    verified_payload = verified.get_json()
    assert verified_payload['token']
    assert verified_payload['user']['is_admin'] is True

    reused = client.post('/api/auth/verify-admin-2fa', json={
        'challenge_token': payload['challenge_token'],
        'code': match.group(1),
    })
    assert reused.status_code == 401


def test_admin_2fa_fails_closed_when_email_delivery_fails(client, monkeypatch):
    admin_id = _create_admin(
        client,
        email='delivery-failure-admin@example.com',
        password='admin-password',
    )
    monkeypatch.setenv('ADMIN_2FA_ENABLED', '1')
    monkeypatch.setattr('app.routes.auth.send_email', lambda *_: False)

    login = client.post('/api/auth/login', json={
        'email': 'delivery-failure-admin@example.com',
        'password': 'admin-password',
    })
    assert login.status_code == 503
    assert 'verification code' in login.get_json()['error'].lower()
    with client.application.app_context():
        assert AdminLoginChallenge.query.filter_by(user_id=admin_id).count() == 0


def test_admin_login_remains_direct_when_two_factor_is_disabled(client, monkeypatch):
    _create_admin(
        client,
        email='two-factor-disabled@example.com',
        password='admin-password',
    )
    monkeypatch.setenv('ADMIN_2FA_ENABLED', '0')

    login = client.post('/api/auth/login', json={
        'email': 'two-factor-disabled@example.com',
        'password': 'admin-password',
    })
    assert login.status_code == 200
    payload = login.get_json()
    assert payload['token']
    assert payload['user']['is_admin'] is True
    assert 'challenge_token' not in payload
