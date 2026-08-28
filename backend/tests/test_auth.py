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
        r = client.post('/api/auth/register', json={'name':'Test User','phone':'9990001111','email':'test@example.com','password':'secret123'})
        assert r.status_code == 200
        data = r.get_json()
        assert 'token' in data
        # login
        r2 = client.post('/api/auth/login', json={'email':'test@example.com','password':'secret123'})
        assert r2.status_code == 200
        data2 = r2.get_json()
    assert 'token' in data2


def test_registration_rejects_weak_password_and_invalid_email(monkeypatch, tmp_path):
    app = setup_test_app(monkeypatch, tmp_path)
    client = app.test_client()
    weak = client.post('/api/auth/register', json={'name':'Weak User','phone':'9990001111','email':'weak@example.com','password':'short'})
    invalid_email = client.post('/api/auth/register', json={'name':'Email User','phone':'9990001111','email':'invalid','password':'strong-pass'})
    assert weak.status_code == 400
    assert '8 characters' in weak.get_json()['error']
    assert invalid_email.status_code == 400


@pytest.mark.parametrize('email', [
    'missing-at.example.com',
    'person@localhost',
    '.person@example.com',
    'person..name@example.com',
    'person@example',
    'person@example..com',
])
def test_registration_rejects_malformed_email_addresses(client, email):
    response = client.post('/api/auth/register', json={
        'name': 'Invalid Email', 'phone': '9990001111',
        'email': email, 'password': 'strong-pass',
    })
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Enter a valid email address.'


@pytest.mark.parametrize('phone', [
    '1234567890',
    '5990001111',
    '999000111',
    '99900011111',
    '+1 999 000 1111',
    '99900abc11',
])
def test_registration_rejects_invalid_indian_mobile_numbers(client, phone):
    response = client.post('/api/auth/register', json={
        'name': 'Invalid Phone', 'phone': phone,
        'email': f'phone-{phone.replace(" ", "").replace("+", "")[:12]}@example.com',
        'password': 'strong-pass',
    })
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Enter a valid Indian mobile number.'


@pytest.mark.parametrize('phone', ['9990001111', '09990001111', '91 99900 01111', '+91-99900-01111'])
def test_registration_normalizes_valid_indian_mobile_numbers(client, phone):
    response = client.post('/api/auth/register', json={
        'name': 'Normalized Phone', 'phone': phone,
        'email': f'normalized-{phone[-4:]}-{len(phone)}@example.com',
        'password': 'strong-pass',
    })
    assert response.status_code == 200
    assert response.get_json()['user']['phone'] == '+919990001111'


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
