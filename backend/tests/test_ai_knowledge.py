from app import ai_core
from app.ai.knowledge import support_answer


def test_render_with_external_key_stays_local(monkeypatch):
    monkeypatch.setenv('RENDER', 'true')
    monkeypatch.setenv('POSP_AI_PROVIDER', 'gemini')
    monkeypatch.setenv('GEMINI_API_KEY', 'fixture')
    assert ai_core.provider_health()['provider'] == 'builtin'
    assert ai_core.call_model('test', 'test')[0] is None


def test_local_fees_preserve_zero_and_missing():
    row = {'name': 'Example', 'application_fee_inr': 0}
    for question in ('Example fee?', 'Example शुल्क?', 'Example ఫీజు?'):
        assert '₹0' in support_answer({'relevant_services': [row]}, question)[0]
    row['application_fee_inr'] = None
    assert support_answer({'relevant_services': [row]}, 'Example fee?')[1]


def test_missing_conversation_referent_hands_off():
    context = {'relevant_services': [{'name': 'Example', 'application_fee_inr': 73}]}
    assert support_answer(context, 'What is its fee?')[1]


def test_followup_skips_current_question_and_honors_staff_request():
    context = {'relevant_services': [{'name': 'Example', 'application_fee_inr': 73}],
               'recent_conversation': [{'role': 'client', 'content': 'I need Example'},
                                       {'role': 'client', 'content': 'What is its fee?'}]}
    assert '₹73' in support_answer(context, 'What is its fee?')[0]
    assert support_answer(context, 'What is the Example fee? Connect me to an administrator.')[1]


def test_production_local_preflight_needs_no_db_or_provider(client, monkeypatch):
    import requests
    from sqlalchemy import event
    from app.utils.database import db

    def forbidden(*args, **kwargs):
        raise AssertionError('Readiness accessed an external dependency')

    monkeypatch.setenv('POSP_AI_PROVIDER', 'builtin')
    monkeypatch.setenv('POSP_CLIENT_AI_ENABLED', 'true')
    monkeypatch.setattr(requests.Session, 'request', forbidden)
    with client.application.app_context():
        engine = db.engine
        event.listen(engine, 'before_cursor_execute', forbidden)
        try:
            response = client.get('/api/admin/ai/local-readiness')
        finally:
            event.remove(engine, 'before_cursor_execute', forbidden)
    assert response.status_code == 200
    data = response.get_json()
    assert data['local_mode'] and data['client_opt_in_available'] and all(data['checks'].values())

def test_confirmed_official_fees_are_distinct_from_assistance_fees():
    row = {'name': 'Example', 'application_fee_inr': 73, 'official_fee_status': 'known', 'official_fee_inr': 25}
    context = {'relevant_services': [row]}
    for question in ('Example official fee?', 'Example सरकारी शुल्क?', 'Example ప్రభుత్వ రుసుము?'):
        answer, handoff, _ = support_answer(context, question)
        assert '₹25' in answer and '₹73' not in answer and not handoff
    row.update(official_fee_status='none', official_fee_inr=0)
    assert '₹0' in support_answer(context, 'Example official fee?')[0]
    row['official_fee_status'] = 'unconfirmed'
    assert support_answer(context, 'Example official fee?')[1]
    assert support_answer(context, 'Can an admin confirm the Example fee?')[1]

def test_explicit_region_filters_before_listing_limit(monkeypatch):
    from app.routes.ai_operations import _requested_region, _verified_active_job_context, _verified_active_scholarship_context
    assert _requested_region('Show jobs in New Delhi?') == 'new delhi'
    assert _requested_region('दिल्ली में नौकरी') == 'दिल्ली'
    assert _requested_region('తెలంగాణలో ఉద్యోగాలు') == 'తెలంగాణ'
    rows = [{'title': place, 'location': place, 'region': place, 'application_status': 'open'}
            for place in ('New Delhi', 'Mumbai', 'Bengaluru', 'Hyderabad')]
    monkeypatch.setattr('app.routes.jobs._public_snapshot_jobs', lambda: rows)
    monkeypatch.setattr('app.routes.ai_operations.load_catalog', lambda: {'items': rows})
    for lookup in (_verified_active_job_context, _verified_active_scholarship_context):
        assert [row['title'] for row in lookup(limit=1, region='hyderabad')] == ['Hyderabad']
        assert lookup(limit=1, region='del') == []
