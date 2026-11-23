from unittest.mock import Mock

import pytest
import requests

from app import ai_core
from app.ai.providers import GeminiProvider, OpenAIProvider, ProviderError


@pytest.mark.parametrize(
    ('provider', 'key_name', 'model_name'),
    [
        (OpenAIProvider(), 'OPENAI_API_KEY', 'gpt-5'),
        (GeminiProvider(), 'GEMINI_API_KEY', 'gemini-3.5-flash-lite'),
    ],
)
def test_provider_adapters_send_expected_payloads_without_logging_secrets(monkeypatch, provider, key_name, model_name):
    monkeypatch.setenv(key_name, 'test-secret')
    response = Mock(status_code=200)
    response.json.return_value = (
        {'output': [{'content': [{'type': 'output_text', 'text': 'OpenAI reply'}]}]}
        if provider.name == 'openai'
        else {'candidates': [{'content': {'parts': [{'text': 'Gemini reply'}]}}]}
    )
    session = Mock()
    session.post.return_value = response
    monkeypatch.setattr('app.ai.providers.base._http_session', lambda: session)

    answer = provider.generate(
        instructions='Be accurate.', prompt='Hello', model=model_name, max_output_tokens=40,
    )

    assert answer in {'OpenAI reply', 'Gemini reply'}
    kwargs = session.post.call_args.kwargs
    url = session.post.call_args.args[0]
    assert kwargs['timeout'] == (3.05, 15)
    assert kwargs['allow_redirects'] is False
    assert kwargs['headers'].get('Authorization', kwargs['headers'].get('x-goog-api-key')) == (
        'Bearer test-secret' if provider.name == 'openai' else 'test-secret'
    )
    if provider.name == 'gemini':
        assert model_name in url
    else:
        assert kwargs['json']['model'] == model_name


def test_provider_selection_requires_explicit_provider_and_key(monkeypatch):
    monkeypatch.delenv('POSP_AI_PROVIDER', raising=False)
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.setenv('GEMINI_API_KEY', 'present-but-not-selected')
    config = ai_core.settings()
    assert config.provider is None
    assert config.error == 'POSP_AI_PROVIDER must explicitly select openai or gemini.'
    assert ai_core.is_configured() is False

    monkeypatch.setenv('POSP_AI_PROVIDER', 'gemini')
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    assert ai_core.is_configured() is False
    answer, error = ai_core.call_model('instructions', 'prompt')
    assert answer is None
    assert 'not configured' in error
    assert 'secret' not in error.lower()


def test_invalid_provider_and_model_configuration_fail_closed(monkeypatch):
    monkeypatch.setenv('POSP_AI_PROVIDER', 'unknown')
    assert ai_core.settings().provider is None
    assert ai_core.call_model('instructions', 'prompt')[0] is None

    monkeypatch.setenv('POSP_AI_PROVIDER', 'gemini')
    monkeypatch.setenv('POSP_AI_MODEL', 'gpt-5')
    assert ai_core.settings().model is None
    assert ai_core.call_model('instructions', 'prompt')[0] is None


def test_ai_disabled_mode_does_not_call_provider(monkeypatch):
    monkeypatch.setenv('POSP_AI_ENABLED', 'false')
    monkeypatch.setenv('POSP_AI_PROVIDER', 'gemini')
    monkeypatch.setenv('GEMINI_API_KEY', 'test-secret')
    provider = Mock()
    monkeypatch.setitem(ai_core._PROVIDERS, 'gemini', provider)
    answer, error = ai_core.call_model('instructions', 'prompt')
    assert answer is None
    assert error == 'AI is disabled.'
    provider.generate.assert_not_called()


def test_rate_limit_retries_once_then_returns_normalized_error(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'test-secret')
    response = Mock(status_code=429, headers={'Retry-After': '0'})
    session = Mock()
    session.post.return_value = response
    monkeypatch.setattr('app.ai.providers.base._http_session', lambda: session)
    monkeypatch.setattr('app.ai.providers.base.time.sleep', lambda _delay: None)

    with pytest.raises(ProviderError) as caught:
        GeminiProvider().generate(
            instructions='Be accurate.', prompt='Hello', model='gemini-3.5-flash-lite', max_output_tokens=40,
        )
    assert caught.value.code == 'rate_limited'
    assert session.post.call_count == 2
    assert 'test-secret' not in caught.value.safe_message


def test_timeout_is_normalized_and_not_retried_after_read_timeout(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'test-secret')
    session = Mock()
    session.post.side_effect = requests.ReadTimeout('sensitive transport detail')
    monkeypatch.setattr('app.ai.providers.base._http_session', lambda: session)
    with pytest.raises(ProviderError) as caught:
        OpenAIProvider().generate(
            instructions='Be accurate.', prompt='Hello', model='gpt-5', max_output_tokens=40,
        )
    assert caught.value.code == 'timeout'
    assert session.post.call_count == 1
    assert 'sensitive' not in caught.value.safe_message


def test_provider_health_distinguishes_disabled_unconfigured_and_available(monkeypatch):
    monkeypatch.setenv('POSP_AI_ENABLED', 'true')
    monkeypatch.setenv('POSP_AI_PROVIDER', 'gemini')
    monkeypatch.setenv('GEMINI_API_KEY', 'test-secret')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    ai_core._last_provider_state.clear()
    health = ai_core.provider_health()
    assert health['providers']['gemini']['state'] == 'configured'
    assert health['providers']['openai']['state'] == 'disabled'
    ai_core._last_provider_state['gemini'] = 'available'
    assert ai_core.provider_health()['providers']['gemini']['state'] == 'available'
