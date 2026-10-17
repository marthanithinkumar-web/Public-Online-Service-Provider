from app.jobs.sync import _expire_missing_published_jobs
from app.models.job import JobNotification, JobSource
from app.utils.database import db


def test_successful_source_snapshot_expires_missing_undated_job(client):
    with client.application.app_context():
        source = JobSource.query.filter_by(key='test-expiry-source').first()
        if source is None:
            source = JobSource(key='test-expiry-source', name='Test source', listing_url='https://example.gov/jobs', enabled=True)
            db.session.add(source)
            db.session.flush()
        missing = JobNotification(
            source_id=source.id, slug='missing-undated-job', external_id='old-job',
            content_hash='a' * 64, title='Old listing', organization='Example',
            official_notice_url='https://example.gov/old', deadline=None, status='published',
        )
        current = JobNotification(
            source_id=source.id, slug='current-job', external_id='current-job',
            content_hash='b' * 64, title='Current listing', organization='Example',
            official_notice_url='https://example.gov/current', deadline=None, status='published',
        )
        db.session.add_all([missing, current])
        db.session.commit()

        expired = _expire_missing_published_jobs(source.id, {'current-job'})

        assert expired == 1
        assert db.session.get(JobNotification, missing.id).status == 'expired'
        assert db.session.get(JobNotification, current.id).status == 'published'


def test_empty_source_snapshot_does_not_expire_existing_jobs(client):
    with client.application.app_context():
        source = JobSource.query.filter_by(key='test-empty-source').first()
        if source is None:
            source = JobSource(key='test-empty-source', name='Test source', listing_url='https://example.gov/jobs', enabled=True)
            db.session.add(source)
            db.session.flush()
        job = JobNotification(
            source_id=source.id, slug='preserve-empty-source-job', external_id='preserve-job',
            content_hash='c' * 64, title='Preserved listing', organization='Example',
            official_notice_url='https://example.gov/preserved', deadline=None, status='published',
        )
        db.session.add(job)
        db.session.commit()

        assert _expire_missing_published_jobs(source.id, set()) == 0
        assert db.session.get(JobNotification, job.id).status == 'published'
