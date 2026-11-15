import os
import uuid

import pytest
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


REDIS_URL = os.getenv('RATELIMIT_TEST_REDIS_URL')
pytestmark = pytest.mark.skipif(
    not REDIS_URL,
    reason='RATELIMIT_TEST_REDIS_URL is required for the Redis integration test',
)


def _worker_app(storage_uri, key_prefix):
    app = Flask(__name__)
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=['1 per minute'],
        storage_uri=storage_uri,
        key_prefix=key_prefix,
    )
    limiter.init_app(app)

    @app.get('/shared-counter-probe')
    def shared_counter_probe():
        return 'ok'

    return app, limiter


def test_independent_workers_share_redis_counters():
    key_prefix = f'posp-rate-limit-test-{uuid.uuid4().hex}'
    first_worker, first_limiter = _worker_app(REDIS_URL, key_prefix)
    second_worker, second_limiter = _worker_app(REDIS_URL, key_prefix)

    assert first_limiter.storage.check() is True
    assert second_limiter.storage.check() is True
    assert first_worker.test_client().get('/shared-counter-probe').status_code == 200
    assert second_worker.test_client().get('/shared-counter-probe').status_code == 429
    assert second_worker.test_client().get(
        '/shared-counter-probe',
        environ_base={'REMOTE_ADDR': '198.51.100.7'},
    ).status_code == 200
