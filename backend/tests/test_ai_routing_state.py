from concurrent.futures import ProcessPoolExecutor
import os

import pytest

from app.ai import routing_state as state
from app.ai.providers.errors import ProviderError


def _try_reservation(directory):
    os.environ['POSP_AI_STATE_DIR'] = directory
    try:
        state.reserve('groq', 'client', 4)
        return True
    except ProviderError:
        return False


def test_workers_share_one_daily_cap(tmp_path, monkeypatch):
    directory = str(tmp_path / 'quota')
    monkeypatch.setenv('POSP_AI_STATE_DIR', directory)
    with ProcessPoolExecutor(max_workers=4) as pool:
        assert sum(pool.map(_try_reservation, [directory] * 16)) == 4
    assert state.snapshot()['attempts'] == {'groq': 4}


def test_settings_apply_to_benchmarks_and_faqs(monkeypatch):
    from app.ai import free_router as router
    monkeypatch.setattr(router.FreeTransport, 'eligible', lambda self: True)
    state.set_order('client', [])
    assert router.public_faq('what is posp', 'client') == router._LOCAL['help', 'English']
    with pytest.raises(ProviderError):
        router.benchmark_reply('groq', 'client', 'English')
    state.set_order('admin', [])
    with pytest.raises(ProviderError):
        list(router.stream_benchmark('admin', 'English'))
    assert state.snapshot()['attempts'] == {}


def test_corrupt_state_falls_back_without_inference(monkeypatch):
    from app.ai import free_router as router
    monkeypatch.setattr(router.FreeTransport, 'eligible', lambda self: True)
    (state._directory() / 'routing.json').write_text('{')
    assert router.public_faq('what is posp', 'client') == router._LOCAL['help', 'English']
    assert router.routing_status()['shared'] is None


def test_role_controls_require_admin_and_reject_invalid_input(client, monkeypatch):
    from app.routes import ai_operations
    path = '/api/admin/ai/routing/admin'
    assert client.put(path, json={'order': []}).status_code == 401
    monkeypatch.setattr(ai_operations, '_require_admin', lambda: True)
    for order in (['groq', 'groq'], ['paid'], 'groq', [None]):
        assert client.put(path, json={'order': order}).status_code == 400
    assert client.put(path, json={'order': ['gemini', 'groq']}).status_code == 200
    assert state.snapshot()['orders']['admin'] == ['gemini', 'groq']
