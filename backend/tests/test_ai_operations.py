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

def test_ai_job_context_uses_public_freshness_and_cutoff_eligibility(monkeypatch, tmp_path):
    import json
    from datetime import datetime, timedelta, timezone
    from zoneinfo import ZoneInfo

    from app.routes import jobs as jobs_route
    from app.routes.ai_operations import _verified_active_job_context

    now = datetime.now(timezone.utc).replace(microsecond=0)
    checked = now.isoformat().replace('+00:00', 'Z')
    stale = (now - timedelta(hours=37)).isoformat().replace('+00:00', 'Z')
    local_now = now.astimezone(ZoneInfo('Asia/Kolkata'))
    today = local_now.date()

    def item(slug, title, deadline, checked_at=checked, cutoff=None):
        return {
            'id': len(slug),
            'slug': slug,
            'title': title,
            'organization': 'Official Recruitment Board',
            'job_type': 'government',
            'deadline': deadline.isoformat() if deadline else None,
            'deadline_cutoff_time': cutoff,
            'deadline_timezone': 'Asia/Kolkata',
            'application_status': 'open',
            'can_apply': True,
            'status_label': 'Verified open',
            'location': 'India',
            'qualification': 'Graduate',
            'official_notice_url': 'https://example.gov.in/notices/' + slug + '.pdf',
            'application_url': 'https://example.gov.in/apply/' + slug,
            'verification_status': 'official_source_checked',
            'status': 'published',
            'source_checked_at': checked_at,
            'last_seen_at': checked_at,
            'published_at': checked,
            'source': {
                'key': 'official_board',
                'name': 'Official Recruitment Board',
                'last_sync_status': 'success',
                'last_successful_sync_at': checked_at,
            },
        }

    cutoff = (local_now - timedelta(minutes=10)).strftime('%H:%M')
    items = [
        item('ai-future', 'Verified Future', today + timedelta(days=2)),
        item('ai-today', 'Deadline Today', today),
        item('ai-expired', 'Expired Notice', today - timedelta(days=1)),
        item('ai-cutoff', 'Cutoff Passed', today, cutoff=cutoff),
        item('ai-stale', 'Stale Source Notice', today + timedelta(days=3), checked_at=stale),
    ]
    snapshot_path = tmp_path / 'jobs.json'
    snapshot_path.write_text(json.dumps({'items': items, 'sources': []}), encoding='utf-8')
    monkeypatch.setattr(jobs_route, '_SNAPSHOT_PATH', snapshot_path)

    context = _verified_active_job_context(limit=10)
    titles = {entry['title'] for entry in context}
    assert titles == {'Verified Future', 'Deadline Today'}

    today_item = next(entry for entry in context if entry['title'] == 'Deadline Today')
    assert today_item['application_status'] == 'deadline_today'
    assert today_item['status_label'] == 'Deadline today—check official portal'
    assert today_item['can_apply'] is False

    future_item = next(entry for entry in context if entry['title'] == 'Verified Future')
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




def test_client_ai_intent_detection_limits_unrelated_context():
    from app.routes.ai_operations import _client_message_intents

    assert _client_message_intents("hello, how are you?") == {
        'jobs': False, 'scholarships': False, 'orders': False,
    }
    assert _client_message_intents("show current government jobs")['jobs'] is True
    assert _client_message_intents("find scholarships for engineering")['scholarships'] is True
    assert _client_message_intents("track my application payment status")['orders'] is True


def test_invalid_support_reply_is_withheld_for_human_review():
    from app.routes.ai_operations import _parse_client_ai_response

    for raw in (None, '', 'Your application is approved.', 'HANDOFF=MAYBE\nANSWER=Approved',
                'HANDOFF=NO\nMissing answer marker', 'HANDOFF=NO\nANSWER='):
        assert _parse_client_ai_response(raw) == ('', True)


def test_support_check_requires_admin(client):
    assert client.post('/api/admin/ai/support-check', json={'case': 'published_fee'}).status_code == 401


def test_support_check_only_accepts_fixed_cases(client, monkeypatch):
    from app.routes import ai_operations
    monkeypatch.setattr(ai_operations, '_require_admin', lambda: True)
    monkeypatch.setattr(ai_operations, '_call_model', lambda *args: ('HANDOFF=NO\nANSWER=73 INR', None))
    assert client.post('/api/admin/ai/support-check', json={'case': 'custom'}).status_code == 400
    result = client.post('/api/admin/ai/support-check', json={'case': 'published_fee'})
    assert result.status_code == 200
    assert result.get_json()['answer'] == '73 INR'


def test_sensitive_message_goes_to_staff_before_customer_data_is_loaded(monkeypatch):
    from app.routes.ai_operations import generate_client_reply
    monkeypatch.setenv('POSP_CLIENT_AI_ENABLED', 'true')
    for message in ('My OTP is 123456', 'Card 4111 1111 1111 1111', 'my password is example'):
        assert generate_client_reply(None, message) == (None, True, None)
