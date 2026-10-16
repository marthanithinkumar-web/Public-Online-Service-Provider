from datetime import date

from app.scholarships.catalog import _active


def test_expired_scholarship_is_not_active():
    assert not _active({'status': 'active', 'deadline': '2026-10-15'}, today=date(2026, 10, 16))


def test_deadline_today_remains_active_for_that_date():
    assert _active({'status': 'active', 'deadline': '2026-10-16'}, today=date(2026, 10, 16))


def test_stale_official_source_entry_is_not_active():
    assert not _active({'status': 'active', 'deadline': '2026-10-31', 'stale_source': True}, today=date(2026, 10, 16))


def test_future_deadline_with_fresh_source_remains_active():
    assert _active({'status': 'active', 'deadline': '2026-10-31'}, today=date(2026, 10, 16))
