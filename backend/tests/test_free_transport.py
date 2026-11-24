import pytest
from app.ai.free_transport import FreeTransport, KEYS, MODELS
from app.ai.providers.errors import ProviderError


@pytest.mark.parametrize('name', list(KEYS))
def test_key_alone_never_enables_external_requests(monkeypatch, name):
    monkeypatch.setenv(KEYS[name], 'fixture')
    monkeypatch.delenv(f'POSP_{name.upper()}_FREE_ONLY_VERIFIED', raising=False)
    with pytest.raises(ProviderError):
        FreeTransport(name).synthetic_reply('client', 'test')


@pytest.mark.parametrize('name', ['groq', 'cloudflare', 'openrouter'])
def test_free_text_payload_and_output(monkeypatch, name):
    monkeypatch.setattr('app.ai.free_transport.verified_free_listing', lambda model: True)
    adapter = FreeTransport(name)
    monkeypatch.setenv(KEYS[name], 'fixture')
    monkeypatch.setenv(f'POSP_{name.upper()}_FREE_ONLY_VERIFIED', 'true')
    monkeypatch.setenv('CLOUDFLARE_ACCOUNT_ID', 'a' * 32)
    def post(**kwargs):
        if name == 'cloudflare':
            assert MODELS[name]['admin'] in kwargs['endpoint']
            return {'success': True, 'result': {'response': '73 INR', 'usage': {'total_tokens': 17}}}
        assert kwargs['payload']['model'] == MODELS[name]['admin']
        if name == 'openrouter':
            assert kwargs['payload']['provider']['max_price']['completion'] == 0
        return {'usage': {'total_tokens': 17}, 'choices': [{'finish_reason': 'stop', 'message': {'content': '73 INR'}}]}
    monkeypatch.setattr(adapter, 'post_json', post)
    assert adapter.synthetic_reply('admin', 'fixture') == '73 INR'
    assert adapter.reported_tokens == 17


@pytest.mark.parametrize('price,expected', [('0', True), ('0.001', False), (None, False)])
def test_verify_live_catalog_pricing(monkeypatch, price, expected):
    from unittest.mock import Mock
    from app.ai.free_transport import verified_free_listing
    model = MODELS['openrouter']['client']
    response = Mock()
    response.json.return_value = {'data': [{'id': model, 'pricing': {'prompt': '0', 'completion': price}}]}
    monkeypatch.setattr('app.ai.free_transport.requests.get', lambda *a, **kw: response)
    assert verified_free_listing(model) is expected
