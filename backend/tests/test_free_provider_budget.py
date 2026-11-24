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
