import os
import pytest
from app.main import create_app, ensure_admin_user
from app.utils.database import db

@pytest.fixture
def client(tmp_path, monkeypatch):
    # ensure app uses sqlite in temp
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{tmp_path / "test.db"}')
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as c:
        with app.app_context():
            db.create_all()
        yield c


def test_request_password_reset_console_fallback(client, monkeypatch):
    # ensure no SMTP configured
    monkeypatch.delenv('SMTP_HOST', raising=False)
    # create a user
    from app.models.user import User
    from app.utils.password import hash_password
    with client.application.app_context():
        u = User(email='test@example.com', password_hash=hash_password('password'), is_admin=False)
        db.session.add(u)
        db.session.commit()

    resp = client.post('/api/auth/request-password-reset', json={'email': 'test@example.com'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'reset_token' not in data
    assert 'message' in data


def test_password_reset_email_contains_correct_one_time_client_link(client, monkeypatch):
    from app.models.user import User
    from app.utils.password import hash_password
    captured = {}

    def capture_email(address, subject, body):
        captured.update(address=address, subject=subject, body=body)
        return True

    monkeypatch.setenv('FRONTEND_URL', 'https://public-online-service-provider-ui.onrender.com')
    monkeypatch.setattr('app.routes.auth.send_email', capture_email)
    with client.application.app_context():
        db.session.add(User(email='client-reset@example.com', password_hash=hash_password('old-password'), is_admin=False))
        db.session.commit()

    response = client.post('/api/auth/request-password-reset', json={
        'email': ' Client-Reset@Example.com ', 'account_type': 'client',
    })
    assert response.status_code == 200
    assert captured['address'] == 'client-reset@example.com'
    assert '/reset-password?token=' in captured['body']
    assert '&account=client' in captured['body']


def test_admin_password_reset_is_role_scoped_and_returns_to_admin_login(client, monkeypatch):
    from app.models.user import User
    from app.utils.password import hash_password
    captured = {}

    def capture_email(address, subject, body):
        captured.update(address=address, subject=subject, body=body)
        return True

    monkeypatch.setattr('app.routes.auth.send_email', capture_email)
    with client.application.app_context():
        db.session.add(User(email='admin-reset@example.com', password_hash=hash_password('old-password'), is_admin=True))
        db.session.commit()

    wrong_portal = client.post('/api/auth/request-password-reset', json={
        'email': 'admin-reset@example.com', 'account_type': 'client',
    })
    assert wrong_portal.status_code == 200
    assert captured == {}

    requested = client.post('/api/auth/request-password-reset', json={
        'email': 'admin-reset@example.com', 'account_type': 'admin',
    })
    assert requested.status_code == 200
    token = captured['body'].split('/reset-password?token=', 1)[1].split('&account=', 1)[0]
    assert '&account=admin' in captured['body']

    reset = client.post('/api/auth/reset-password', json={
        'token': token, 'new_password': 'new-admin-password',
    })
    assert reset.status_code == 200
    assert reset.get_json()['login_path'] == '/admin/login'
    assert client.post('/api/auth/login', json={
        'email': 'admin-reset@example.com', 'password': 'new-admin-password',
    }).status_code == 200
    assert client.post('/api/auth/reset-password', json={
        'token': token, 'new_password': 'reused-password',
    }).status_code == 400


def test_admin_bootstrap_does_not_overwrite_a_recovered_password(client, monkeypatch):
    from app.models.user import User
    from app.utils.password import hash_password, verify_password
    monkeypatch.setenv('ADMIN_EMAIL', 'persistent-admin@example.com')
    monkeypatch.setenv('ADMIN_PASSWORD', 'deployment-bootstrap-password')
    with client.application.app_context():
        admin = User(
            email='persistent-admin@example.com',
            password_hash=hash_password('recovered-password'),
            is_admin=True,
        )
        db.session.add(admin)
        db.session.commit()
        ensure_admin_user()
        db.session.refresh(admin)
        assert verify_password('recovered-password', admin.password_hash)
        assert not verify_password('deployment-bootstrap-password', admin.password_hash)


def test_password_reset_reports_email_delivery_failure(client, monkeypatch):
    from app.models.user import User
    from app.utils.password import hash_password
    monkeypatch.setattr('app.routes.auth.send_email', lambda *_: False)
    with client.application.app_context():
        db.session.add(User(email='delivery-failure@example.com', password_hash=hash_password('old-password'), is_admin=False))
        db.session.commit()
    response = client.post('/api/auth/request-password-reset', json={
        'email': 'delivery-failure@example.com', 'account_type': 'client',
    })
    # The outward response remains indistinguishable from an unknown account,
    # preventing SMTP outages from becoming an account-enumeration oracle.
    assert response.status_code == 200
    assert response.get_json()['message'] == 'If that account exists, a reset link will be sent.'


def test_client_registration_requires_one_time_email_verification(client, monkeypatch):
    captured = {}

    def capture_email(address, subject, body):
        captured.update(address=address, subject=subject, body=body)
        return True

    monkeypatch.setenv('REQUIRE_EMAIL_VERIFICATION', '1')
    monkeypatch.setattr('app.routes.auth.send_email', capture_email)
    registered = client.post('/api/auth/register', json={
        'name': 'Verified Client', 'phone': '9876543210',
        'email': 'verified-client@example.com', 'password': 'secure-password',
    })
    assert registered.status_code == 201
    assert registered.get_json()['verification_required'] is True
    assert 'token' not in registered.get_json()
    assert client.post('/api/auth/login', json={
        'email': 'verified-client@example.com', 'password': 'secure-password',
    }).status_code == 403

    token = captured['body'].split('/verify?token=', 1)[1].splitlines()[0]
    verified = client.post('/api/auth/verify', json={'token': token})
    assert verified.status_code == 200
    assert client.post('/api/auth/verify', json={'token': token}).status_code == 400
    assert client.post('/api/auth/login', json={
        'email': 'verified-client@example.com', 'password': 'secure-password',
    }).status_code == 200


def test_registration_rolls_back_when_verification_email_cannot_be_sent(client, monkeypatch):
    from app.models.user import User
    monkeypatch.setenv('REQUIRE_EMAIL_VERIFICATION', '1')
    monkeypatch.setattr('app.routes.auth.send_email', lambda *_: False)
    response = client.post('/api/auth/register', json={
        'name': 'Delivery Failure', 'phone': '9765432109',
        'email': 'not-created@example.com', 'password': 'secure-password',
    })
    assert response.status_code == 503
    with client.application.app_context():
        assert User.query.filter_by(email='not-created@example.com').first() is None


def test_request_verify_console_fallback(client, monkeypatch):
    monkeypatch.delenv('SMTP_HOST', raising=False)
    from app.models.user import User
    from app.utils.password import hash_password
    with client.application.app_context():
        u = User(email='verify@example.com', password_hash=hash_password('password'), is_admin=False)
        db.session.add(u)
        db.session.commit()

    resp = client.post('/api/auth/request-verify', json={'email': 'verify@example.com'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'verify_token' not in data
    assert 'message' in data


def test_password_reset_rejects_short_password_before_token_processing(client):
    response = client.post('/api/auth/reset-password', json={
        'token': 'not-a-real-token',
        'new_password': 'short',
    })
    assert response.status_code == 400
    assert response.get_json()['error'] == 'New password must be at least 8 characters.'


def test_production_email_does_not_print_security_tokens(monkeypatch, capsys):
    from app.utils.email import send_email
    monkeypatch.delenv('SMTP_HOST', raising=False)
    monkeypatch.setenv('FLASK_ENV', 'production')
    delivered = send_email('client@example.com', 'Password reset', 'sensitive-reset-token')
    assert delivered is False
    assert 'sensitive-reset-token' not in capsys.readouterr().out


def test_brevo_uses_port_2525_tls_and_separate_verified_sender(monkeypatch):
    from app.utils.email import send_email
    captured = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            captured.update(host=host, port=port, timeout=timeout)
        def __enter__(self):
            return self
        def __exit__(self, *_):
            return False
        def ehlo(self):
            captured['ehlo_count'] = captured.get('ehlo_count', 0) + 1
        def starttls(self, context):
            captured['tls'] = context is not None
        def login(self, username, password):
            captured.update(username=username, password=password)
        def send_message(self, message):
            captured['message'] = message

    monkeypatch.setenv('SMTP_HOST', 'smtp-relay.brevo.com')
    monkeypatch.setenv('SMTP_PORT', '2525')
    monkeypatch.setenv('SMTP_USER', 'brevo-login@example.com')
    monkeypatch.setenv('SMTP_PASS', 'smtp-key')
    monkeypatch.setenv('SMTP_FROM_EMAIL', 'verified-sender@example.com')
    monkeypatch.setenv('SMTP_FROM_NAME', 'Public Online Service Provider')
    monkeypatch.setattr('app.utils.email.smtplib.SMTP', FakeSMTP)

    assert send_email('client@example.com', 'Account email', 'one-time-link') is True
    assert captured['host'] == 'smtp-relay.brevo.com'
    assert captured['port'] == 2525
    assert captured['tls'] is True
    assert captured['ehlo_count'] == 2
    assert captured['username'] == 'brevo-login@example.com'
    assert captured['message']['From'] == 'Public Online Service Provider <verified-sender@example.com>'
    assert captured['message']['To'] == 'client@example.com'
