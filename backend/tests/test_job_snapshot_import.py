import json
from datetime import datetime, timezone

from app.jobs.snapshot_import import import_verified_snapshot
from app.jobs.sources import SOURCE_DEFINITIONS
from app.models.job import JobNotification, JobSource
from app.utils.database import db


def _snapshot(source, items):
    checked = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    return {
        'schema_version': 1,
        'generated_at': checked,
        'count': len(items),
        'items': items,
        'sources': [{
            'key': source.key,
            'name': source.name,
            'listing_url': source.listing_url,
            'enabled': True,
            'last_sync_completed_at': checked,
            'last_sync_status': 'success',
            'fetched_count': len(items),
            'published_count': len(items),
        }],
    }


def _item(source, digest, slug, title):
    checked = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    return {
        'slug': slug,
        'content_hash': digest,
        'title': title,
        'organization': source.name,
        'job_type': 'government',
        'appointment_type': None,
        'location': 'India',
        'qualification': None,
        'age_limit': None,
        'application_fee': None,
        'vacancies': None,
        'salary': None,
        'summary': None,
        'issue_date': None,
        'application_start_date': None,
        'deadline': None,
        'official_notice_url': source.listing_url,
        'application_url': None,
        'status': 'published',
        'verification_status': 'official_source_checked',
        'confidence': 0.95,
        'is_featured': False,
        'first_seen_at': checked,
        'last_seen_at': checked,
        'published_at': checked,
        'source': {'key': source.key},
    }


def test_verified_snapshot_import_exactly_replaces_active_public_set(client, tmp_path):
    source = SOURCE_DEFINITIONS[0]
    first = _item(source, 'a' * 64, 'verified-one', 'Verified One')
    second = _item(source, 'b' * 64, 'verified-two', 'Verified Two')
    path = tmp_path / 'jobs.json'
    path.write_text(json.dumps(_snapshot(source, [first, second])), encoding='utf-8')

    with client.application.app_context():
        legacy_source = JobSource(key='retired_source', name='Retired', listing_url=source.listing_url, enabled=True)
        db.session.add(legacy_source)
        db.session.flush()
        db.session.add(JobNotification(
            source_id=legacy_source.id,
            external_id='legacy',
            slug='legacy-job',
            content_hash='c' * 64,
            title='Legacy job',
            organization='Legacy',
            official_notice_url=source.listing_url,
            status='published',
            confidence=0.9,
        ))
        db.session.commit()

        result = import_verified_snapshot(path)

        assert result['active_total'] == 2
        assert JobNotification.query.filter_by(status='published').count() == 2
        assert JobNotification.query.filter_by(slug='legacy-job').one().status == 'expired'
        assert JobSource.query.filter_by(key='retired_source').one().enabled is False
        assert JobSource.query.filter_by(key=source.key).one().enabled is True


def test_verified_snapshot_import_is_idempotent(client, tmp_path):
    source = SOURCE_DEFINITIONS[0]
    item = _item(source, 'd' * 64, 'verified-repeat', 'Verified Repeat')
    path = tmp_path / 'jobs.json'
    path.write_text(json.dumps(_snapshot(source, [item])), encoding='utf-8')

    with client.application.app_context():
        first = import_verified_snapshot(path)
        second = import_verified_snapshot(path)
        assert first['active_total'] == second['active_total'] == 1
        assert JobNotification.query.filter_by(content_hash='d' * 64).count() == 1
