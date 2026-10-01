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
