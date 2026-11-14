from app.routes.ai_operations import _extract_response_text


def test_extract_response_text_reads_responses_api_output():
    payload = {
        'output': [
            {'type': 'message', 'content': [
                {'type': 'output_text', 'text': 'POSP is healthy.'},
            ]},
        ],
    }
    assert _extract_response_text(payload) == 'POSP is healthy.'


def test_extract_response_text_returns_empty_for_missing_text():
    assert _extract_response_text({'output': []}) == ''


def test_parse_client_ai_response_detects_handoff():
    from app.routes.ai_operations import _parse_client_ai_response
    answer, handoff = _parse_client_ai_response('HANDOFF=YES\nANSWER=I will connect you with the service team.')
    assert handoff is True
    assert answer == 'I will connect you with the service team.'


def test_parse_client_ai_response_keeps_safe_answer():
    from app.routes.ai_operations import _parse_client_ai_response
    answer, handoff = _parse_client_ai_response('HANDOFF=NO\nANSWER=You can track your request from your dashboard.')
    assert handoff is False
    assert answer == 'You can track your request from your dashboard.'

def test_ai_job_context_uses_public_freshness_and_cutoff_eligibility(client):
    from datetime import datetime, time, timedelta, timezone

    from app.jobs.sources import JobItem, india_today
    from app.jobs.sync import upsert_item
    from app.models.job import JobSource
    from app.routes.ai_operations import _verified_active_job_context
    from app.utils.database import db

    checked = datetime.now(timezone.utc).replace(tzinfo=None)
    fresh_source = JobSource.query.filter_by(key='employment_news').one()
    fresh_source.last_sync_status = 'success'
    fresh_source.last_sync_completed_at = checked
    fresh_source.last_successful_sync_at = checked
    fresh_source.consecutive_failures = 0

    stale_source = JobSource.query.filter_by(key='ssc').one()
    stale_source.last_sync_status = 'success'
    stale_source.last_sync_completed_at = checked
    stale_source.last_successful_sync_at = checked - timedelta(hours=37)
    stale_source.consecutive_failures = 0

    def add(source, external_id, title, deadline, cutoff=None):
        item = JobItem(
            external_id=external_id,
            title=title,
            organization='Official Recruitment Board',
            official_notice_url=f'https://example.gov/notices/{external_id}',
            application_url=f'https://example.gov/apply/{external_id}',
            deadline=deadline,
            deadline_cutoff_time=cutoff,
            deadline_timezone='Asia/Kolkata',
            qualification='Graduate',
            confidence=0.95,
        )
        return upsert_item(source, item)[0]

    today = india_today()
    add(fresh_source, 'ai-future', 'Verified Future', today + timedelta(days=2))
    add(fresh_source, 'ai-today', 'Deadline Today', today)
    add(fresh_source, 'ai-expired', 'Expired Notice', today - timedelta(days=1))
    add(fresh_source, 'ai-cutoff', 'Cutoff Passed', today, time(0, 0))
    add(stale_source, 'ai-stale', 'Stale Source Notice', today + timedelta(days=3))
    db.session.commit()

    context = _verified_active_job_context(limit=10)
    titles = {item['title'] for item in context}
    assert titles == {'Verified Future', 'Deadline Today'}

    today_item = next(item for item in context if item['title'] == 'Deadline Today')
    assert today_item['application_status'] == 'deadline_today'
    assert today_item['status_label'] == 'Deadline today—check official portal'
    assert today_item['can_apply'] is False

    future_item = next(item for item in context if item['title'] == 'Verified Future')
    assert future_item['application_status'] == 'open'
    assert future_item['status_label'] == 'Verified open'
    assert future_item['can_apply'] is True


def test_ai_scholarship_context_preserves_deadline_and_renewal_scope(monkeypatch):
    from app.routes.ai_operations import _verified_active_scholarship_context

    monkeypatch.setattr('app.routes.ai_operations.load_catalog', lambda: {
        'items': [
            {'title': 'Verified Scholarship', 'application_status': 'open', 'application_scope': None, 'source_checked_at': '2026-11-15T00:00:00+05:30'},
            {'title': 'Deadline Today Scholarship', 'application_status': 'deadline_today', 'application_scope': None, 'source_checked_at': '2026-11-15T00:00:00+05:30'},
            {'title': 'Renewal Scholarship', 'application_status': 'open', 'application_scope': 'renewal_only', 'source_checked_at': '2026-11-15T00:00:00+05:30'},
            {'title': 'Closed Scholarship', 'application_status': 'closed'},
            {'title': 'Unverified Scholarship', 'application_status': 'unverified'},
        ],
    })

    context = _verified_active_scholarship_context(limit=10)
    assert {item['title'] for item in context} == {
        'Verified Scholarship',
        'Deadline Today Scholarship',
        'Renewal Scholarship',
    }

    today_item = next(item for item in context if item['title'] == 'Deadline Today Scholarship')
    assert today_item['status_label'] == 'Deadline today—check official portal'
    assert today_item['can_apply'] is False

    renewal_item = next(item for item in context if item['title'] == 'Renewal Scholarship')
    assert renewal_item['status_label'] == 'Verified open—renewal only'
    assert renewal_item['can_apply'] is False

