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


def test_provider_diagnostics_requires_admin(client):
    assert client.post('/api/admin/ai/diagnostics').status_code == 401


def test_provider_diagnostics_returns_safe_result(client, monkeypatch):
    from app.routes import ai_operations

    monkeypatch.setattr(ai_operations, '_require_admin', lambda: object())
    monkeypatch.setattr(ai_operations, '_probe_provider_access', lambda: {
        'provider': 'gemini', 'model': 'gemini-2.5-flash', 'configured': True,
        'ready': False, 'status': 'model_unavailable',
        'message': 'Gemini model was not found or is not accessible to this API key.',
        'supported_methods': [], 'available_models': ['gemini-3.5-flash'],
    })
    response = client.post('/api/admin/ai/diagnostics')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'model_unavailable'
    assert data['available_models'] == ['gemini-3.5-flash']
    assert 'api_key' not in data


def test_admin_ai_chat_returns_safe_provider_failure(client, monkeypatch):
    from app.routes import ai_operations

    monkeypatch.setattr(ai_operations, '_require_admin', lambda: object())
    monkeypatch.setattr(ai_operations, '_build_context', lambda: {'checked_at': '2026-10-12T00:00:00+00:00'})
    monkeypatch.setattr(ai_operations, '_call_model', lambda *args: (
        None, 'Gemini model was not found or is not accessible to this API key (HTTP 404).'
    ))
    monkeypatch.setattr(ai_operations, '_ai_is_configured', lambda: True)
    monkeypatch.setattr(ai_operations, '_configured_provider', lambda: 'gemini')
    response = client.post('/api/admin/ai/chat', json={'message': 'Summarize current status'})
    assert response.status_code == 502
    data = response.get_json()
    assert data['provider'] == 'gemini'
    assert 'HTTP 404' in data['error']
    assert 'secret' not in str(data).lower()


def test_ai_overview_exposes_operation_statuses(client, monkeypatch):
    from app.routes import ai_operations

    monkeypatch.setattr(ai_operations, '_require_admin', lambda: object())
    response = client.get('/api/admin/ai/overview')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data.get('operations'), list)
    assert data['operations']
    assert all(item.get('key') and item.get('status') and item.get('message') for item in data['operations'])
    assert data['ai'].get('provider_status') in {'configured_unverified', 'not_configured'}
