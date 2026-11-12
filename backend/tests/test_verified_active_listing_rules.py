from datetime import date, datetime, timedelta, timezone

from app.scholarships.catalog import _active


def _item(now, *, deadline='2026-10-24', application_status='deadline_today', evidence='Student Application Open till : 24-10-2026', **changes):
    value = {
        'status': 'active',
        'source_type': 'official',
        'is_official': True,
        'deadline': deadline,
        'deadline_type': 'student_application',
        'application_status': application_status,
        'status_evidence': evidence,
        'source_checked_at': now.isoformat(),
        'deadline_timezone': 'Asia/Kolkata',
        'deadline_cutoff_time': None,
    }
    value.update(changes)
    return value


def test_scholarship_requires_fresh_official_status_and_current_application_deadline():
    today = date(2026, 10, 24)
    now = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
    base = _item(now)
    assert _active(base, today, now=now) is True
    assert _active(_item(now, deadline='2026-10-25', application_status='open'), today, now=now) is True
    assert _active(_item(now, deadline='2026-10-23', application_status='closed'), today, now=now) is False
    assert _active(_item(now, deadline=None, application_status='unverified'), today, now=now) is False
    assert _active(_item(now, deadline='not-a-date'), today, now=now) is False
    assert _active({**base, 'stale_source': True}, today, now=now) is False
    assert _active({**base, 'source_type': 'private'}, today, now=now) is False
    assert _active({**base, 'status': 'expired'}, today, now=now) is False
    assert _active({**base, 'application_status': 'closed'}, today, now=now) is False
    assert _active({**base, 'status_evidence': ''}, today, now=now) is False
    assert _active({**base, 'deadline_type': 'institute_verification'}, today, now=now) is False


def test_deadline_today_is_visible_only_with_explicit_warning_state():
    today = date(2026, 10, 24)
    now = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
    assert _active(_item(now, deadline='2026-10-24', application_status='deadline_today'), today, now=now)
    assert not _active(_item(now, deadline='2026-10-24', application_status='open'), today, now=now)


def test_rolling_scholarship_requires_explicit_current_acceptance_evidence():
    today = date(2026, 10, 24)
    now = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
    rolling = _item(
        now,
        deadline=None,
        application_status='open',
        evidence='Registration is currently open for eligible SC students.',
    )
    assert _active(rolling, today, now=now)
    assert not _active({**rolling, 'status_evidence': 'Fresh registration link for academic year 2026-27'}, today, now=now)
    assert not _active({**rolling, 'application_status': 'unverified'}, today, now=now)


def test_stale_official_verification_is_not_public():
    today = date(2026, 10, 24)
    now = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
    stale = now - timedelta(hours=37)
    assert not _active(_item(now, source_checked_at=stale.isoformat()), today, now=now)


def test_india_timezone_boundary_closes_yesterday_deadline_after_local_midnight():
    before_midnight_utc = datetime(2026, 11, 7, 18, 29, tzinfo=timezone.utc)  # 23:59 IST
    after_midnight_utc = datetime(2026, 11, 7, 18, 31, tzinfo=timezone.utc)   # 00:01 IST next day
    item = _item(
        before_midnight_utc,
        deadline='2026-11-07',
        application_status='deadline_today',
        evidence='Student Application Open till : 07-11-2026',
    )
    assert _active(item, now=before_midnight_utc)
    assert not _active(item, now=after_midnight_utc)


def test_scholarship_explicitly_closed_or_cancelled_status_is_never_public():
    today = date(2026, 11, 7)
    now = datetime(2026, 11, 7, 10, 0, tzinfo=timezone.utc)
    base = _item(now, deadline='2026-11-30', application_status='open', evidence='Student Application Open till : 30-11-2026')
    assert _active({**base, 'status': 'closed'}, today, now=now) is False
    assert _active({**base, 'status': 'cancelled'}, today, now=now) is False
    assert _active({**base, 'application_status': 'cancelled'}, today, now=now) is False


def test_public_catalog_does_not_expose_internal_audit_or_source_health(tmp_path, monkeypatch):
    from app.scholarships import catalog

    now = datetime(2026, 11, 7, 10, 0, tzinfo=timezone.utc)
    item = _item(now, deadline='2026-11-30', application_status='open', evidence='Student Application Open till : 30-11-2026')
    item.update({'id': 'nsp-open', 'slug': 'nsp-open', 'title': 'Verified NSP Scholarship', 'deadline_type': 'student_application'})
    path = tmp_path / 'scholarships.json'
    path.write_text(json.dumps({
        'generated_at': now.isoformat(),
        'items': [item],
        'closed_items': [{'slug': 'closed-record', 'status': 'closed'}],
        'unverified_items': [{'slug': 'review-record', 'application_status': 'unverified'}],
        'stale_items': [{'slug': 'stale-record', 'stale_source': True}],
        'closed_count': 1,
        'discovery': {'source_health': {'nsp': {'ok': False, 'error': 'internal timeout'}}},
    }), encoding='utf-8')
    monkeypatch.setattr(catalog, 'CATALOG_PATH', path)

    payload = catalog.load_catalog(today=date(2026, 11, 7), now=now)

    assert payload['count'] == 1
    assert payload['items'][0]['slug'] == 'nsp-open'
    assert not any(key in payload for key in ('discovery', 'closed_items', 'unverified_items', 'stale_items', 'source_failures', 'last_successful_sync_at'))
