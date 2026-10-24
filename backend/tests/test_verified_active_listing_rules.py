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


from datetime import datetime, timezone
from types import SimpleNamespace

from app.jobs.rules import is_public_active_job, target_status


def test_private_undated_role_requires_explicit_source_permission_and_recent_verification():
    today = date(2026, 10, 24)
    current = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
    private = SimpleNamespace(title='Consultant', organization='Wipro', official_notice_url='https://careers.wipro.com/job/example', deadline=None, issue_date=None, job_type='private', confidence=0.88)
    government = SimpleNamespace(title='Recruitment', organization='Board', official_notice_url='https://ssc.gov.in/notice', deadline=None, issue_date=None, job_type='government', confidence=0.95)
    assert target_status(private, today=today, allow_missing_deadline=True) == 'published'
    assert target_status(government, today=today, allow_missing_deadline=True) == 'needs_review'
    record = {'job_type':'private','deadline':None,'confidence':0.88,'last_seen_at':current.isoformat()}
    assert is_public_active_job(record, source_allows_missing_deadline=True, today=today, now=current) is True
    stale = {**record, 'last_seen_at':datetime(2026, 10, 20, tzinfo=timezone.utc).isoformat()}
    assert is_public_active_job(stale, source_allows_missing_deadline=True, today=today, now=current) is False
    assert is_public_active_job(record, source_allows_missing_deadline=False, today=today, now=current) is False
