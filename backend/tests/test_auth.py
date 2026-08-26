import pytest
from app.main import create_app
from app.utils.database import db
from app.models.user import User
from app.utils.password import hash_password


def setup_test_app(monkeypatch, tmp_path):
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{tmp_path / "auth.db"}')
    app = create_app()
    app.config['TESTING'] = True
    return app


def test_register_and_login(monkeypatch, tmp_path):
    app = setup_test_app(monkeypatch, tmp_path)
    with app.app_context():
        db.drop_all()
        db.create_all()
        client = app.test_client()
        # register
        r = client.post('/api/auth/register', json={'name':'Test User','phone':'9990001111','email':'test@example.com','password':'secret'})
        assert r.status_code == 200
        data = r.get_json()
        assert 'token' in data
        # login
        r2 = client.post('/api/auth/login', json={'email':'test@example.com','password':'secret'})
        assert r2.status_code == 200
        data2 = r2.get_json()
        assert 'token' in data2


def test_authenticated_client_can_load_dashboard_profile(client):
    registered = client.post('/api/auth/register', json={
        'name': 'Dashboard Client', 'phone': '9990002222',
        'email': 'client-profile@example.com', 'password': 'secret123',
    })
    token = registered.get_json()['token']
    response = client.get('/api/auth/profile', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert response.get_json()['user']['name'] == 'Dashboard Client'
    assert 'password_hash' not in response.get_json()['user']

    updated = client.put('/api/auth/profile', headers={'Authorization': f'Bearer {token}'}, json={
        'name': 'Updated Client', 'phone': '9990003333',
        'email': 'updated-profile@example.com', 'current_password': 'secret123',
        'new_password': 'newsecret123',
    })
    assert updated.status_code == 200
    assert updated.get_json()['user']['name'] == 'Updated Client'
    assert client.get('/api/auth/profile', headers={'Authorization': f'Bearer {token}'}).status_code == 401
    replacement = updated.get_json()['token']
    assert client.get('/api/auth/profile', headers={'Authorization': f'Bearer {replacement}'}).status_code == 200
    assert client.post('/api/auth/login', json={'email': 'updated-profile@example.com', 'password': 'newsecret123'}).status_code == 200
