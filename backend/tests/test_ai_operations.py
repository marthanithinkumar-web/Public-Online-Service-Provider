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



def test_client_ai_searches_for_current_jobs_and_scholarships():
    from app.routes.ai_operations import _should_use_google_search
    assert _should_use_google_search("latest scholarship deadline", [])
    assert _should_use_google_search("official job notification", [])


def test_client_ai_does_not_search_for_simple_greeting():
    from app.routes.ai_operations import _should_use_google_search
    assert _should_use_google_search("hello", []) is False


def test_client_ai_searches_unknown_factual_question():
    from app.routes.ai_operations import _should_use_google_search
    assert _should_use_google_search("what is the process for this new scheme?", []) is True



def test_client_ai_quick_replies_to_simple_greetings_without_model_call():
    from app.routes.ai_operations import _quick_client_reply
    assert _quick_client_reply("Hiii!!!") == "Hi! How can I help you with your application or request today?"
    assert _quick_client_reply("good morning") == "Good morning! How can I help you with a service or request today?"


def test_client_ai_quick_reply_does_not_swallow_real_questions():
    from app.routes.ai_operations import _quick_client_reply
    assert _quick_client_reply("hi i need scholarship") is None
    assert _quick_client_reply("how to apply for pan") is None



def test_client_ai_avoids_search_for_local_service_question():
    from app.routes.ai_operations import _should_use_google_search
    assert _should_use_google_search("how can I track my request", [{"name": "Track My Request"}]) is False


def test_client_ai_still_searches_explicit_official_lookup():
    from app.routes.ai_operations import _should_use_google_search
    assert _should_use_google_search("find latest official scholarship deadline", [{"name": "Scholarship service"}]) is True



def test_client_ai_does_not_search_for_ordinary_application_faq():
    from app.routes.ai_operations import _should_use_google_search
    assert _should_use_google_search("how to apply for pan", [{"name": "PAN application"}]) is False
    assert _should_use_google_search("what documents do I need for this POSP request", [{"name": "Track My Request"}]) is False


def test_client_ai_searches_for_current_public_openings():
    from app.routes.ai_operations import _should_use_google_search
    assert _should_use_google_search("current government job openings", []) is True
