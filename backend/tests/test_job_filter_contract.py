import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.routes import jobs as jobs_route
from app.utils.database import db


def _now():
    return datetime.now(timezone.utc).replace(microsecond=0)


def _timestamp(value=None):
    value = value or _now()
    return value.isoformat().replace('+00:00', 'Z')


def _job(
    slug,
    title='Graduate Assistant',
    *,
    job_type='government',
    featured=False,
    location='Hyderabad, Telangana',
    qualification='Engineering degree',
    deadline='auto',
    cutoff=None,
    checked_at=None,
    source_status='success',
):
    checked_at = checked_at or _timestamp()
    today = datetime.now(ZoneInfo('Asia/Kolkata')).date()
    return {
        'id': abs(hash(slug)) % 1000000,
        'slug': slug,
        'title': title,
        'organization': 'Example Recruitment Board',
        'job_type': job_type,
        'location': location,
        'qualification': qualification,
        'deadline': (today + timedelta(days=20)).isoformat() if deadline == 'auto' else (deadline.isoformat() if isinstance(deadline, date) else deadline),
        'deadline_cutoff_time': cutoff,
        'deadline_timezone': 'Asia/Kolkata',
        'application_status': 'open',
        'can_apply': True,
        'status_label': 'Verified open',
        'source_checked_at': checked_at,
        'official_notice_url': f'https://example.gov.in/notices/{slug}.pdf',
        'application_url': f'https://example.gov.in/apply/{slug}',
        'status': 'published',
        'verification_status': 'official_source_checked',
        'is_featured': featured,
        'source': {
            'key': 'upsc',
            'name': 'Union Public Service Commission',
            'listing_url': 'https://www.upsc.gov.in/recruitment',
            'last_sync_status': source_status,
            'last_successful_sync_at': checked_at,
            'consecutive_failures': 0,
        },
        'last_seen_at': checked_at,
        'published_at': checked_at,
    }


def _write_snapshot(monkeypatch, tmp_path, items, sources=None):
    snapshot_path = tmp_path / 'jobs.json'
    snapshot_path.write_text(json.dumps({
        'schema_version': 1,
        'generated_at': _timestamp(),
        'items': items,
        'sources': sources or [{
            'key': 'upsc',
            'name': 'Union Public Service Commission',
            'listing_url': 'https://www.upsc.gov.in/recruitment',
            'enabled': True,
            'last_sync_status': 'success',
            'last_successful_sync_at': _timestamp(),
            'consecutive_failures': 0,
        }],
        'count': len(items),
    }), encoding='utf-8')
    monkeypatch.setattr(jobs_route, '_SNAPSHOT_PATH', snapshot_path)
    return snapshot_path


def test_public_job_filters_match_source_type_featured_and_limit(client, monkeypatch, tmp_path):
    featured = _job('upsc-featured', featured=True)
    private = _job('private-role', title='Private Graduate Assistant', job_type='private', featured=False)
    _write_snapshot(monkeypatch, tmp_path, [featured, private])

    response = client.get('/api/jobs/?q=UPSC&type=government&featured=true&location=Hyderabad&qualification=Engineering&limit=1')
    assert response.status_code == 200
    assert response.get_json()['total'] == 1
    assert [item['slug'] for item in response.get_json()['items']] == ['upsc-featured']

    no_match = client.get('/api/jobs/?q=upsc&type=private&featured=true')
    assert no_match.status_code == 200
    assert no_match.get_json()['items'] == []

    wrong_location = client.get('/api/jobs/?q=upsc&type=government&featured=true&location=Delhi')
    assert wrong_location.status_code == 200
    assert wrong_location.get_json()['items'] == []


def test_expired_and_undated_jobs_are_excluded_from_public_list_and_detail(client, monkeypatch, tmp_path):
    today = datetime.now(ZoneInfo('Asia/Kolkata')).date()
    expired = _job('expired', deadline=today - timedelta(days=1))
    undated = _job('undated', deadline=None)
    future = _job('future', deadline=today + timedelta(days=2))
    _write_snapshot(monkeypatch, tmp_path, [expired, undated, future])

    response = client.get('/api/jobs/')
    assert response.status_code == 200
    assert [item['slug'] for item in response.get_json()['items']] == ['future']
    assert client.get('/api/jobs/expired').status_code == 404
    assert client.get('/api/jobs/undated').status_code == 404
    assert client.get('/api/jobs/future').status_code == 200


def test_deadline_today_without_cutoff_is_warning_not_apply_now(client, monkeypatch, tmp_path):
    today = datetime.now(ZoneInfo('Asia/Kolkata')).date()
    _write_snapshot(monkeypatch, tmp_path, [_job('today-no-cutoff', deadline=today, cutoff=None)])

    response = client.get('/api/jobs/')
    assert response.status_code == 200
    item = response.get_json()['items'][0]
    assert item['application_status'] == 'deadline_today'
    assert item['can_apply'] is False
    assert item['status_label'] == 'Deadline today—check official portal'
    assert response.get_json()['verified_open_count'] == 0
    assert response.get_json()['deadline_today_count'] == 1


def test_deadline_today_after_official_cutoff_is_excluded(client, monkeypatch, tmp_path):
    today = datetime.now(ZoneInfo('Asia/Kolkata')).date()
    cutoff = (datetime.now(ZoneInfo('Asia/Kolkata')) - timedelta(minutes=10)).strftime('%H:%M')
    _write_snapshot(monkeypatch, tmp_path, [_job('today-after-cutoff', deadline=today, cutoff=cutoff)])

    response = client.get('/api/jobs/')
    assert response.status_code == 200
    assert response.get_json()['items'] == []


def test_stale_or_degraded_sources_are_excluded(client, monkeypatch, tmp_path):
    stale = _timestamp(_now() - timedelta(hours=37))
    fresh_but_degraded = _job('degraded', source_status='degraded')
    stale_item = _job('stale', checked_at=stale)
    _write_snapshot(monkeypatch, tmp_path, [fresh_but_degraded, stale_item])

    response = client.get('/api/jobs/')
    assert response.status_code == 200
    assert response.get_json()['items'] == []


def test_source_status_endpoint_uses_snapshot_and_hides_internal_errors(client, monkeypatch, tmp_path):
    source = {
        'key': 'upsc',
        'name': 'Union Public Service Commission',
        'listing_url': 'https://www.upsc.gov.in/recruitment',
        'enabled': True,
        'last_sync_status': 'degraded',
        'last_successful_sync_at': _timestamp(),
        'consecutive_failures': 1,
        'last_error': 'Private parser exception detail',
    }
    _write_snapshot(monkeypatch, tmp_path, [], sources=[source])

    response = client.get('/api/jobs/sources')
    assert response.status_code == 200
    item = response.get_json()['items'][0]
    assert item['last_sync_status'] == 'degraded'
    assert 'last_error' not in item


def test_snapshot_status_requires_marker_to_match_snapshot_file(client, monkeypatch, tmp_path):
    snapshot_path = tmp_path / 'jobs.json'
    marker_path = tmp_path / 'verified_snapshot.sha256'
    content = '{"schema_version":1,"items":[],"sources":[],"count":0}'
    snapshot_path.write_text(content, encoding='utf-8')
    marker_path.write_text(hashlib.sha256(content.encode('utf-8')).hexdigest(), encoding='utf-8')
    monkeypatch.setattr(jobs_route, '_SNAPSHOT_PATH', snapshot_path)
    monkeypatch.setattr(jobs_route, '_SNAPSHOT_MARKER', marker_path)

    ready = client.get('/api/jobs/snapshot-status').get_json()
    assert ready == {'ready': True, 'sha256': hashlib.sha256(content.encode('utf-8')).hexdigest()}

    snapshot_path.write_text(content + ' ', encoding='utf-8')
    not_ready = client.get('/api/jobs/snapshot-status').get_json()
    assert not_ready == {'ready': False, 'sha256': None}


def test_public_job_endpoints_do_not_open_database_connections(client, monkeypatch, tmp_path):
    _write_snapshot(monkeypatch, tmp_path, [_job('read-only')])
    with client.application.app_context():
        engine = db.engine

    def fail_database_connection(*args, **kwargs):
        pytest.fail('Public job snapshot endpoint attempted a database connection')

    monkeypatch.setattr(engine, 'connect', fail_database_connection)
    response = client.get('/api/jobs/')
    assert response.status_code == 200
    assert response.get_json()['total'] == 1
