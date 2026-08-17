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
