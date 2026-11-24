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
