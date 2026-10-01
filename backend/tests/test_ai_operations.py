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
    answer, handoff = _parse_client_ai_response('HANDOFF=YES\\nANSWER=I will connect you with the service team.')
    assert handoff is True
    assert answer == 'I will connect you with the service team.'


def test_parse_client_ai_response_keeps_safe_answer():
    from app.routes.ai_operations import _parse_client_ai_response
    answer, handoff = _parse_client_ai_response('HANDOFF=NO\\nANSWER=You can track your request from your dashboard.')
    assert handoff is False
    assert answer == 'You can track your request from your dashboard.'
