import pytest

from app.ai import free_router as router
from app.ai.providers.errors import ProviderError


@pytest.fixture
def provider(monkeypatch):
    calls = []
    for key, value in (('_counts', router.Counter()), ('_cache', {}), ('_cooldown', {}),
                       ('_events', router.deque(maxlen=32)), ('_inflight', set())):
        monkeypatch.setattr(router, key, value)
    monkeypatch.setenv('POSP_CLIENT_AI_PRIORITY', 'groq')
    monkeypatch.setattr(router.FreeTransport, 'eligible', lambda self: True)

    def reply(self, role, prompt):
        self.reported_tokens = 12
        calls.append(prompt)
        return 'Fixture answer'

    monkeypatch.setattr(router.FreeTransport, 'synthetic_reply', reply)
    return calls


def test_benchmark_and_faq_share_daily_budget(provider, monkeypatch):
    monkeypatch.setattr(router, '_DAILY_LIMIT', 2)
    assert router.public_faq('what is posp', 'client') == 'Fixture answer'
    assert router.public_faq('what is posp', 'client') == 'Fixture answer'
    assert router.benchmark_reply('groq', 'admin', 'Hindi') == 'Fixture answer'
    with pytest.raises(ProviderError):
        router.benchmark_reply('groq', 'admin', 'Telugu')
    assert router.public_faq('what should i avoid sharing', 'client') == router._LOCAL['privacy', 'English']
    status = router.routing_status()
    assert status['providers']['groq']['reported_tokens'] == 24
    assert status['providers']['groq']['attempts_without_usage'] == 0
    assert len(provider) == 2
    assert status['counts']['cache_hits'] == 1
    assert status['providers']['groq']['remaining_requests'] == 0


def test_benchmark_failure_opens_faq_cooldown(provider, monkeypatch):
    def fail(self, role, prompt):
        raise ValueError('sensitive fixture')

    monkeypatch.setattr(router.FreeTransport, 'synthetic_reply', fail)
    with pytest.raises(ProviderError) as error:
        router.benchmark_reply('groq', 'admin', 'English')
    assert 'sensitive fixture' not in str(error.value)
    assert router.public_faq('what is posp', 'client') == router._LOCAL['help', 'English']
    status = router.routing_status()
    assert status['providers']['groq']['failures'] == 1
    assert status['providers']['groq']['attempts_without_usage'] == 1
    assert status['counts']['groq'] == 1
    assert status['events'] == [{'provider': 'groq', 'result': 'fallback'}]


@pytest.mark.parametrize('question,word', [('What is POSP?', 'POSP'),
                                          ('मुझे चैट में क्या साझा नहीं करना चाहिए?', 'ओटीपी'),
                                          ('చాట్‌లో ఏమి పంచుకోకూడదు?', 'ఓటీపీ')])
def test_local_faq_needs_no_user_or_catalog_lookup(monkeypatch, question, word):
    from app.routes.ai_operations import generate_client_reply

    monkeypatch.setenv('POSP_CLIENT_AI_ENABLED', 'true')
    monkeypatch.setenv('POSP_AI_PROVIDER', 'builtin')
    monkeypatch.setenv('POSP_CLIENT_AI_PRIORITY', '')
    monkeypatch.setattr(router, '_cache', {})
    answer, handoff, error = generate_client_reply(None, question)
    assert word in answer
    assert not handoff and error is None


def test_stream_uses_only_visible_tokens_and_shares_budget(provider, monkeypatch):
    from unittest.mock import MagicMock
    monkeypatch.setattr(router, '_DAILY_LIMIT', 1)
    response = MagicMock()
    response.__enter__.return_value = response
    response.status_code = 200
    response.iter_content.return_value = [
        b'data: {"choices":[{"delta":{"reasoning":"hidden"}}]}\n\nda',
        b'ta: {"choices":[{"delta":{"content":"73 INR"},"finish_reason":"stop"}],"usage":{"total_tokens":9}}\n\ndata: [DONE]\n\n']
    def post(url, **kwargs):
        assert kwargs['json']['model'] == 'openai/gpt-oss-120b'
        assert kwargs['stream'] and not kwargs['allow_redirects']
        return response
    monkeypatch.setattr('app.ai.free_transport.requests.post', post)
    assert list(router.stream_benchmark('admin', 'Telugu')) == ['73 INR']
    assert router.public_faq('what is posp', 'client') == router._LOCAL['help', 'English']
    assert router.routing_status()['providers']['groq']['reported_tokens'] == 9


def test_stream_rejects_untrusted_input_and_reports_disabled(client, monkeypatch):
    from app.routes import ai_operations
    path = '/api/admin/ai/support-check/stream'
    assert client.post(path, json={}).status_code == 401
    monkeypatch.setattr(ai_operations, '_require_admin', lambda: True)
    assert client.post(path, json={'message':'fixture'}).status_code == 400
    monkeypatch.setattr(router.FreeTransport, 'eligible', lambda self: False)
    response = client.post(path, json={}, buffered=True)
    assert response.mimetype == 'application/x-ndjson'
    assert b'Free-tier account is unverified.' in response.data
    assert b'"done":true' not in response.data


def test_global_disable_prevents_benchmark_traffic(monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY', 'fixture')
    monkeypatch.setenv('POSP_GROQ_FREE_ONLY_VERIFIED', 'true')
    monkeypatch.setenv('POSP_AI_ENABLED', 'false')
    assert not router.FreeTransport('groq').eligible()
