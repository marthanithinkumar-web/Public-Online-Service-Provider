import pytest
from app.main import create_app
from app.models.job import JobSource
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
            # Several legacy unit tests use the old Employment News row only as
            # an isolated fixture for generic job-sync behaviour. Keep that row
            # disabled in tests without restoring the source to the production
            # source registry or public feed.
            if not JobSource.query.filter_by(key='employment_news').first():
                db.session.add(JobSource(
                    key='employment_news',
                    name='Legacy test source',
                    listing_url='https://employmentnews.gov.in/jobs',
                    enabled=False,
                ))
                db.session.commit()
        yield c
