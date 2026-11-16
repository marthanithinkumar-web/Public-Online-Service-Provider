import logging
import time

import pytest
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.utils.limiter import DEFAULT_RATE_LIMITS, limiter


def test_default_hourly_limit_applies_to_unannotated_api_route(client):
    app = client.application

    @app.get('/__rate-limit-hourly-probe')
    def rate_limit_hourly_probe():
        return 'ok'

    statuses = [
        client.get('/__rate-limit-hourly-probe').status_code
        for _ in range(501)
    ]

    assert statuses[:500] == [200] * 500
    assert statuses[500] == 429


def test_default_daily_limit_applies_to_unannotated_route():
    daily_limit = next(limit for limit in DEFAULT_RATE_LIMITS if ' per day' in limit)
    app = Flask(__name__)
    daily_limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[daily_limit],
        storage_uri='memory://',
    )
    daily_limiter.init_app(app)

    @app.get('/ordinary-api')
    def ordinary_api():
        return 'ok'

    with app.test_client() as client:
        statuses = [client.get('/ordinary-api').status_code for _ in range(2001)]

    assert statuses[:2000] == [200] * 2000
    assert statuses[2000] == 429


@pytest.mark.parametrize(
    ('path', 'limit'),
    [
        ('/api/auth/login', 6),
        ('/api/auth/register', 4),
        ('/api/auth/request-password-reset', 3),
        ('/api/auth/reset-password', 6),
    ],
)
def test_authentication_route_limits_are_preserved(client, path, limit):
    statuses = [
        client.post(path, json={}).status_code
        for _ in range(limit + 1)
    ]

    assert all(status != 429 for status in statuses[:limit])
    assert statuses[limit] == 429


@pytest.mark.parametrize('path', ['/health', '/health/rate-limit', '/readiness'])
def test_operational_health_routes_are_exempt_from_default_limits(client, monkeypatch, path):
    monkeypatch.setenv('STRICT_PRODUCTION_READINESS', '0')
    monkeypatch.setattr('app.main.persistent_storage_connectivity', lambda: False)
    monkeypatch.setattr('app.main.shared_rate_limit_connectivity', lambda: False)
    monkeypatch.setattr('app.main.smtp_connectivity', lambda: False)
    monkeypatch.setattr('app.main.razorpay_connectivity', lambda: False)

    statuses = [client.get(path).status_code for _ in range(501)]

    assert statuses == [200] * 501


def test_health_is_liveness_only(client, monkeypatch):
    def fail_if_called():
        raise AssertionError('liveness must not call readiness checks')

    monkeypatch.setattr('app.main.production_readiness', fail_if_called)

    response = client.get('/health')

    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok'}


def test_strict_readiness_reports_redis_failure_without_connection_details(client, monkeypatch):
    monkeypatch.setenv('STRICT_PRODUCTION_READINESS', '1')
    monkeypatch.setattr('app.main.shared_rate_limit_connectivity', lambda: False)
    monkeypatch.setattr('app.main.persistent_storage_connectivity', lambda: True)
    monkeypatch.setattr('app.main.smtp_connectivity', lambda: True)
    monkeypatch.setattr('app.main.razorpay_connectivity', lambda: True)

    response = client.get('/readiness')

    assert response.status_code == 503
    assert response.get_json()['checks']['shared_rate_limit_connectivity'] is False
    assert 'redis://' not in response.get_data(as_text=True)
    assert 'password' not in response.get_data(as_text=True).lower()


def test_limiter_falls_back_to_bounded_local_limits_when_store_fails(client, monkeypatch, caplog):
    app = client.application

    @app.get('/__rate-limit-fallback-probe')
    @limiter.limit('2 per minute')
    def rate_limit_fallback_probe():
        return 'ok'

    storage = limiter.storage

    def fail_incr(*args, **kwargs):
        raise ConnectionError('simulated rate-limit storage outage')

    monkeypatch.setattr(storage, 'incr', fail_incr)
    monkeypatch.setattr(storage, 'check', lambda: False)
    monkeypatch.setattr(limiter, '_storage_dead', False)
    caplog.set_level(logging.WARNING, logger='flask-limiter')

    statuses = [
        client.get('/__rate-limit-fallback-probe').status_code
        for _ in range(3)
    ]

    assert statuses == [200, 200, 429]
    assert 'falling back to in-memory storage' in caplog.text
    assert 'bounded per-process fallback' in caplog.text


def test_authentication_fails_closed_when_shared_storage_is_unavailable(client, monkeypatch):
    app = client.application
    app.config['RATELIMIT_REQUIRE_SHARED_STORAGE'] = True
    storage = limiter.storage

    def fail_incr(*args, **kwargs):
        raise ConnectionError('simulated rate-limit storage outage')

    monkeypatch.setattr(storage, 'incr', fail_incr)
    monkeypatch.setattr(storage, 'check', lambda: False)
    monkeypatch.setattr(limiter, '_storage_dead', False)

    response = client.post('/api/auth/login', json={})

    assert response.status_code == 503
    assert response.get_json() == {'error': 'Service temporarily unavailable.'}
    assert 'redis://' not in response.get_data(as_text=True)


def test_authentication_fails_closed_when_shared_storage_is_not_configured(client):
    app = client.application
    app.config['RATELIMIT_REQUIRE_SHARED_STORAGE'] = True
    app.config['RATELIMIT_SHARED_STORAGE_CONFIGURED'] = False

    response = client.post('/api/auth/login', json={})

    assert response.status_code == 503


def test_local_fallback_fails_closed_after_bounded_window(client, monkeypatch):
    app = client.application
    app.extensions['posp_rate_limit_fallback'] = {
        'started_at': time.monotonic() - 301,
        'expired_logged': False,
    }

    @app.get('/__rate-limit-expired-fallback-probe')
    def expired_fallback_probe():
        return 'ok'

    monkeypatch.setattr(limiter, '_storage_dead', True)
    monkeypatch.setattr(limiter, '_Limiter__should_check_backend', lambda: False)

    response = client.get('/__rate-limit-expired-fallback-probe')

    assert response.status_code == 503


def test_limiter_recovers_after_storage_reconnects(client, monkeypatch):
    app = client.application
    storage = limiter.storage
    original_incr = storage.incr
    available = {'value': False}

    @app.get('/__rate-limit-recovery-probe')
    @limiter.limit('2 per minute')
    def recovery_probe():
        return 'ok'

    def toggle_incr(*args, **kwargs):
        if not available['value']:
            raise ConnectionError('simulated rate-limit storage outage')
        return original_incr(*args, **kwargs)

    monkeypatch.setattr(storage, 'incr', toggle_incr)
    monkeypatch.setattr(storage, 'check', lambda: available['value'])
    monkeypatch.setattr(limiter, '_storage_dead', False)
    monkeypatch.setattr(limiter, '_Limiter__should_check_backend', lambda: True)

    assert client.get('/__rate-limit-recovery-probe').status_code == 200
    assert limiter._storage_dead is True

    available['value'] = True
    response = client.get('/__rate-limit-recovery-probe')

    assert response.status_code == 200
    assert limiter._storage_dead is False
