import pytest
from app.main import create_app
from app.utils.database import db
from app.models.user import User
from app.utils.password import hash_password


def setup_test_app():
    app = create_app()
    app.config['TESTING'] = True
    return app


def test_register_and_login():
    app = setup_test_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        client = app.test_client()
        # register
        r = client.post('/api/auth/register', json={'email':'test@example.com','password':'secret'})
        assert r.status_code == 200
        data = r.get_json()
        assert 'token' in data
        # login
        r2 = client.post('/api/auth/login', json={'email':'test@example.com','password':'secret'})
        assert r2.status_code == 200
        data2 = r2.get_json()
        assert 'token' in data2
