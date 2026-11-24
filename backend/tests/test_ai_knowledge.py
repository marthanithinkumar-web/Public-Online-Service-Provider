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
