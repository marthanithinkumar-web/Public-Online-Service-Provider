from app.utils.readiness import (
    production_readiness,
    readiness_status,
    persistent_storage_connectivity,
    shared_rate_limit_configured,
    smtp_configured,
    smtp_connectivity,
    razorpay_live_credentials_configured,
    razorpay_webhook_configured,
    razorpay_connectivity,
)


def _clear_readiness_env(monkeypatch):
    for name in (
        'SMTP_HOST','SMTP_PORT','SMTP_USER','SMTP_PASS','SMTP_FROM_EMAIL',
        'SMTP_USE_TLS','SMTP_USE_SSL','MAIL_DEFAULT_SENDER','ADMIN_EMAIL',
        'ADMIN_2FA_ENABLED','S3_BUCKET','S3_ENDPOINT_URL','AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY','AWS_REGION','RATELIMIT_STORAGE_URI',
        'RAZORPAY_KEY_ID','RAZORPAY_KEY_SECRET','RAZORPAY_WEBHOOK_SECRET',
        'STRICT_PRODUCTION_READINESS',
    ):
        monkeypatch.delenv(name, raising=False)


def _set_complete_readiness_env(monkeypatch):
    monkeypatch.setenv('SMTP_HOST', 'smtp.example.test')
    monkeypatch.setenv('SMTP_PORT', '587')
    monkeypatch.setenv('SMTP_USER', 'smtp-user')
    monkeypatch.setenv('SMTP_PASS', 'smtp-password')
    monkeypatch.setenv('SMTP_FROM_EMAIL', 'sender@example.test')
    monkeypatch.setenv('ADMIN_2FA_ENABLED', '1')
    monkeypatch.setenv('S3_BUCKET', 'private-documents')
    monkeypatch.setenv('S3_ENDPOINT_URL', 'https://s3.example.test')
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'access-key')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'secret-key')
    monkeypatch.setenv('AWS_REGION', 'region-1')
    monkeypatch.setenv('RATELIMIT_STORAGE_URI', 'rediss://default:password@redis.example.test:6379/0')
    monkeypatch.setenv('RAZORPAY_KEY_ID', 'rzp_live_example')
    monkeypatch.setenv('RAZORPAY_KEY_SECRET', 'razorpay-secret')
    monkeypatch.setenv('RAZORPAY_WEBHOOK_SECRET', 'webhook-secret')


def test_readiness_reports_missing_launch_configuration(monkeypatch):
    _clear_readiness_env(monkeypatch)
    checks = production_readiness()
    assert checks == {
        'persistent_document_storage': False,
        'shared_rate_limit_storage': False,
        'smtp_delivery': False,
        'admin_2fa': False,
        'razorpay_live_credentials': False,
        'razorpay_webhook': False,
    }
    assert readiness_status(checks) == 'needs_configuration'


def test_readiness_accepts_complete_launch_configuration(monkeypatch):
    _clear_readiness_env(monkeypatch)
    _set_complete_readiness_env(monkeypatch)

    checks = production_readiness()
    assert all(checks.values())
    assert readiness_status(checks) == 'ready'


def test_readiness_rejects_insecure_storage_endpoint(monkeypatch):
    _clear_readiness_env(monkeypatch)
    _set_complete_readiness_env(monkeypatch)
    monkeypatch.setenv('S3_ENDPOINT_URL', 'http://s3.example.test')

    checks = production_readiness()
    assert checks['persistent_document_storage'] is False
    assert readiness_status(checks) == 'needs_configuration'


def test_persistent_storage_connectivity_uses_read_only_bucket_probe(monkeypatch):
    _clear_readiness_env(monkeypatch)
    _set_complete_readiness_env(monkeypatch)
    captured = {}

    class FakeClient:
        def list_objects_v2(self, Bucket, MaxKeys):
            captured.update(bucket=Bucket, max_keys=MaxKeys)
            return {'ResponseMetadata': {'HTTPStatusCode': 200}, 'KeyCount': 0}

    monkeypatch.setattr('app.utils.s3.s3_client', lambda: FakeClient())
    assert persistent_storage_connectivity() is True
    assert captured == {'bucket': 'private-documents', 'max_keys': 1}


def test_rate_limit_readiness_rejects_invalid_redis_uri(monkeypatch):
    _clear_readiness_env(monkeypatch)
    monkeypatch.setenv('RATELIMIT_STORAGE_URI', 'redis://')
    assert shared_rate_limit_configured() is False

    monkeypatch.setenv('RATELIMIT_STORAGE_URI', 'https://redis.example.test')
    assert shared_rate_limit_configured() is False

    monkeypatch.setenv('RATELIMIT_STORAGE_URI', 'rediss://default:password@redis.example.test:6379/0')
    assert shared_rate_limit_configured() is True


def test_smtp_readiness_validates_port_sender_and_credentials(monkeypatch):
    _clear_readiness_env(monkeypatch)
    monkeypatch.setenv('SMTP_HOST', 'smtp.example.test')
    monkeypatch.setenv('SMTP_PORT', 'not-a-port')
    monkeypatch.setenv('SMTP_FROM_EMAIL', 'sender@example.test')
    assert smtp_configured() is False

    monkeypatch.setenv('SMTP_PORT', '587')
    monkeypatch.setenv('SMTP_FROM_EMAIL', '')
    assert smtp_configured() is False

    monkeypatch.setenv('SMTP_FROM_EMAIL', 'sender@example.test')
    monkeypatch.setenv('SMTP_USER', 'smtp-user')
    assert smtp_configured() is False

    monkeypatch.setenv('SMTP_PASS', 'smtp-password')
    assert smtp_configured() is True


def test_smtp_connectivity_uses_tls_authentication_without_sending_mail(monkeypatch):
    _clear_readiness_env(monkeypatch)
    _set_complete_readiness_env(monkeypatch)
    captured = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            captured.update(host=host, port=port, timeout=timeout)
        def __enter__(self):
            return self
        def __exit__(self, *_):
            return False
        def ehlo(self):
            captured['ehlo_count'] = captured.get('ehlo_count', 0) + 1
        def starttls(self, context):
            captured['tls'] = context is not None
        def login(self, username, password):
            captured.update(username=username, password=password)
        def noop(self):
            captured['noop'] = True
            return 250, b'OK'

    monkeypatch.setattr('app.utils.readiness.smtplib.SMTP', FakeSMTP)
    assert smtp_connectivity() is True
    assert captured['host'] == 'smtp.example.test'
    assert captured['port'] == 587
    assert captured['timeout'] == 5
    assert captured['tls'] is True
    assert captured['username'] == 'smtp-user'
    assert captured['noop'] is True


def test_razorpay_readiness_requires_live_credentials_and_webhook(monkeypatch):
    _clear_readiness_env(monkeypatch)
    monkeypatch.setenv('RAZORPAY_KEY_ID', 'rzp_test_example')
    monkeypatch.setenv('RAZORPAY_KEY_SECRET', 'secret')
    monkeypatch.setenv('RAZORPAY_WEBHOOK_SECRET', 'webhook-secret')
    assert razorpay_live_credentials_configured() is False
    assert razorpay_webhook_configured() is True

    monkeypatch.setenv('RAZORPAY_KEY_ID', 'rzp_live_example')
    assert razorpay_live_credentials_configured() is True
    monkeypatch.delenv('RAZORPAY_WEBHOOK_SECRET', raising=False)
    assert razorpay_webhook_configured() is False


def test_razorpay_connectivity_uses_read_only_live_api_probe(monkeypatch):
    _clear_readiness_env(monkeypatch)
    _set_complete_readiness_env(monkeypatch)
    captured = {}

    class Response:
        def raise_for_status(self):
            return None
        def json(self):
            return {'items': []}

    def fake_get(url, params, auth, timeout):
        captured.update(url=url, params=params, auth=auth, timeout=timeout)
        return Response()

    monkeypatch.setattr('app.utils.readiness.requests.get', fake_get)
    assert razorpay_connectivity() is True
    assert captured['url'].endswith('/orders')
    assert captured['params'] == {'count': 1}
    assert captured['auth'][0] == 'rzp_live_example'
    assert captured['timeout'] == 5


def test_readiness_endpoint_is_non_blocking_until_strict_mode(client, monkeypatch):
    _clear_readiness_env(monkeypatch)
    response = client.get('/readiness')
    assert response.status_code == 200
    payload = response.get_json()
    assert payload['status'] == 'needs_configuration'
    assert payload['checks']['persistent_storage_connectivity'] is False
    assert payload['checks']['shared_rate_limit_connectivity'] is False
    assert payload['checks']['smtp_connectivity'] is False
    assert payload['checks']['razorpay_connectivity'] is False


def test_readiness_endpoint_can_report_all_external_connectivity(client, monkeypatch):
    _clear_readiness_env(monkeypatch)
    _set_complete_readiness_env(monkeypatch)
    monkeypatch.setattr('app.main.persistent_storage_connectivity', lambda: True)
    monkeypatch.setattr('app.main.shared_rate_limit_connectivity', lambda: True)
    monkeypatch.setattr('app.main.smtp_connectivity', lambda: True)
    monkeypatch.setattr('app.main.razorpay_connectivity', lambda: True)
    response = client.get('/readiness')
    assert response.status_code == 200
    payload = response.get_json()
    assert payload['status'] == 'ready'
    assert payload['checks']['persistent_storage_connectivity'] is True
    assert payload['checks']['shared_rate_limit_connectivity'] is True
    assert payload['checks']['smtp_connectivity'] is True
    assert payload['checks']['razorpay_live_credentials'] is True
    assert payload['checks']['razorpay_webhook'] is True
    assert payload['checks']['razorpay_connectivity'] is True


def test_readiness_endpoint_can_fail_closed_in_strict_mode(client, monkeypatch):
    _clear_readiness_env(monkeypatch)
    monkeypatch.setenv('STRICT_PRODUCTION_READINESS', '1')
    response = client.get('/readiness')
    assert response.status_code == 503
    assert response.get_json()['status'] == 'needs_configuration'
