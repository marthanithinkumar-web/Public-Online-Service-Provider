import os
import pytest
from app.main import create_app
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
