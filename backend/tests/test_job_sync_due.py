from datetime import datetime, timedelta, timezone

from app.jobs.sources import SOURCE_DEFINITIONS
from app.jobs import sync as job_sync
from app.jobs.sync import sync_is_due
from app.models.job import JobSource
from app.utils.database import db


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _mark_all_sources_recent():
    now = _now()
    for source in JobSource.query.all():
        source.last_sync_status = 'success'
        source.last_sync_completed_at = now
    db.session.commit()


def test_sync_is_due_when_a_configured_source_has_no_database_row(client):
    with client.application.app_context():
        _mark_all_sources_recent()
        missing_key = SOURCE_DEFINITIONS[-1].key
        source = JobSource.query.filter_by(key=missing_key).one()
        db.session.delete(source)
        db.session.commit()

        assert sync_is_due() is True


def test_sync_is_due_when_enabled_configured_source_never_completed(client):
    with client.application.app_context():
        _mark_all_sources_recent()
        source = JobSource.query.filter_by(key=SOURCE_DEFINITIONS[-1].key).one()
        source.last_sync_status = 'not_run'
        source.last_sync_completed_at = None
        db.session.commit()

        assert sync_is_due() is True


def test_sync_is_due_when_configured_source_url_changed(client):
    with client.application.app_context():
        _mark_all_sources_recent()
        definition = SOURCE_DEFINITIONS[-1]
        source = JobSource.query.filter_by(key=definition.key).one()
        source.listing_url = 'https://example.invalid/old-listing'
        db.session.commit()

        assert sync_is_due() is True


def test_sync_is_due_when_any_enabled_configured_source_is_stale(client):
    with client.application.app_context():
        _mark_all_sources_recent()
        source = JobSource.query.filter_by(key=SOURCE_DEFINITIONS[0].key).one()
        source.last_sync_completed_at = _now() - timedelta(hours=21)
        db.session.commit()

        assert sync_is_due(hours=20) is True


def test_sync_is_not_due_when_all_enabled_configured_sources_are_recent(client):
    with client.application.app_context():
        _mark_all_sources_recent()

        assert sync_is_due(hours=20) is False


def test_background_job_sync_can_be_disabled_for_browser_e2e(client, monkeypatch):
    app = client.application
    app.config['DISABLE_BACKGROUND_JOB_SYNC'] = True
    monkeypatch.setattr(
        job_sync,
        'sync_is_due',
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('sync check must be skipped')),
    )

    assert job_sync.trigger_background_sync(app) is False
