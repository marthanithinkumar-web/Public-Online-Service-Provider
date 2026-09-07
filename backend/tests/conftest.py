import pytest

from app.jobs import snapshot as job_snapshot
from app.jobs import sources as job_sources
from app.jobs.sources import SourceDefinition, parse_employment_news
from app.main import create_app
from app.models.job import JobSource
from app.utils.database import db


# Keep the removed Employment News source available only inside pytest because
# older generic sync/snapshot regression tests use it as a deterministic fixture.
# Production SOURCE_DEFINITIONS remains free of this source.
LEGACY_TEST_SOURCE = SourceDefinition(
    'employment_news',
    'Legacy test source',
    'https://employmentnews.gov.in/NewEmp/AllJobs.aspx?k=All',
    parse_employment_news,
)
job_sources.SOURCE_BY_KEY.setdefault('employment_news', LEGACY_TEST_SOURCE)
if not any(source.key == 'employment_news' for source in job_snapshot.SOURCE_DEFINITIONS):
    job_snapshot.SOURCE_DEFINITIONS = (LEGACY_TEST_SOURCE, *job_snapshot.SOURCE_DEFINITIONS)


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
