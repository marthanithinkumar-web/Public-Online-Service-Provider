from app.ai import free_router as router


def test_only_fixed_questions_leave_the_process(monkeypatch):
    def forbidden(*args):
        raise AssertionError('Unexpected provider call')
    monkeypatch.setattr(router.FreeTransport, 'eligible', forbidden)
    assert router.public_faq('what is posp? my email is private@example.com', 'client') is None


def test_fallback_cooldown_and_cache(monkeypatch):
    monkeypatch.setattr(router, '_cache', {})
    monkeypatch.setattr(router, '_cooldown', {})
    monkeypatch.setenv('POSP_CLIENT_AI_PRIORITY', 'groq,cloudflare')
    monkeypatch.setattr(router.FreeTransport, 'eligible', lambda self: True)
    calls = []
    def generate(self, role, prompt):
        calls.append(self.name)
        if self.name == 'groq':
            raise TimeoutError()
        return 'POSP helps with applications.'
    monkeypatch.setattr(router.FreeTransport, 'synthetic_reply', generate)
    for _ in range(2):
        assert router.public_faq('What is POSP?', 'client') == 'POSP helps with applications.'
    assert calls == ['groq', 'cloudflare']
    assert router.routing_status()['providers']['groq']['cooling_down']


def test_hindi_telugu_fallback_without_providers(monkeypatch):
    monkeypatch.setattr(router.FreeTransport, 'eligible', lambda self: False)
    assert 'आवेदन' in router.public_faq('POSP क्या है?', 'client')
    assert 'దరఖాస్తు' in router.public_faq('POSP అంటే ఏమిటి?', 'client')
