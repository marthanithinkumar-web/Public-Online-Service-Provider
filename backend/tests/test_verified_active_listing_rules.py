from datetime import date

from app.scholarships.catalog import _active


def test_scholarship_requires_official_active_status_and_current_deadline():
    today = date(2026, 10, 24)
    base = {"status": "active", "source_type": "official", "deadline": "2026-10-24"}
    assert _active(base, today) is True
    assert _active({**base, "deadline": "2026-10-25"}, today) is True
    assert _active({**base, "deadline": "2026-10-23"}, today) is False
    assert _active({**base, "deadline": None}, today) is False
    assert _active({**base, "deadline": "not-a-date"}, today) is False
    assert _active({**base, "stale_source": True}, today) is False
    assert _active({**base, "source_type": "private"}, today) is False
    assert _active({**base, "status": "expired"}, today) is False
