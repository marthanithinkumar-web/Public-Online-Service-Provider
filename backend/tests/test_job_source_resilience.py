from datetime import date, timedelta

import requests

from app.jobs.official_fetch import OfficialSourceUnavailable, fetch_official_page, validate_official_url
from app.jobs.sync import sync_source, upsert_item
from app.jobs.sources import JobItem
from app.models.job import JobNotification, JobSource
from app.utils.database import db


def test_current_india_post_gds_source_is_allowlisted():
    assert validate_official_url('https://www.indiapost.gov.in/gdsonlineengagement')
    assert validate_official_url('https://indiapostgdsonline.gov.in/')


def test_official_fetch_retries_transient_connection_failures(monkeypatch):
    monkeypatch.setattr('app.jobs.official_fetch.time.sleep', lambda _seconds: None)

    class Response:
        url = 'https://employmentnews.gov.in/jobs'
        status_code = 200
        encoding = 'utf-8'
        headers = {'Content-Type': 'text/html'}
        def raise_for_status(self): pass
        def iter_content(self, chunk_size): yield b'<html>verified</html>'

    class Session:
        def __init__(self): self.calls = 0
        def get(self, *_args, **_kwargs):
            self.calls += 1
            if self.calls < 3:
                raise requests.ConnectionError('temporary refusal')
            return Response()

    session = Session()
    assert 'verified' in fetch_official_page('https://employmentnews.gov.in/jobs', session=session)
    assert session.calls == 3


def test_official_fetch_uses_concise_error_after_retry_exhaustion(monkeypatch):
    monkeypatch.setattr('app.jobs.official_fetch.time.sleep', lambda _seconds: None)

    class Session:
        def __init__(self): self.calls = 0
        def get(self, *_args, **_kwargs):
            self.calls += 1
            raise requests.Timeout('long requests traceback should not leak')

    session = Session()
    try:
        fetch_official_page('https://employmentnews.gov.in/jobs', session=session)
        assert False, 'temporary failure should be raised after retries'
    except OfficialSourceUnavailable as exc:
        assert session.calls == 3
        assert 'temporarily unavailable' in str(exc)
        assert 'traceback' not in str(exc).lower()


def test_sync_keeps_verified_jobs_when_source_temporarily_fails(client, monkeypatch):
    with client.application.app_context():
        source = JobSource.query.filter_by(key='employment_news').one()
        job, *_ = upsert_item(source, JobItem(
            external_id='verified-before-outage',
            title='Verified Assistant Recruitment',
            organization='Official Recruitment Board',
            official_notice_url='https://employmentnews.gov.in/notice/verified',
            application_url='https://employmentnews.gov.in/apply/verified',
            deadline=date.today() + timedelta(days=15),
            confidence=0.95,
        ))
        db.session.commit()
        assert job.status == 'published'
        job_id = job.id

        monkeypatch.setattr(
            'app.jobs.sync.fetch_official_page',
            lambda *_args, **_kwargs: (_ for _ in ()).throw(OfficialSourceUnavailable('temporary outage')),
        )
        result = sync_source(source)
        assert result['status'] == 'degraded'
        assert db.session.get(JobNotification, job_id).status == 'published'
        refreshed_source = db.session.get(JobSource, source.id)
        assert refreshed_source.last_sync_status == 'degraded'
        assert 'Last verified job notices remain available' in refreshed_source.last_error
