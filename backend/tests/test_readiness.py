from app.utils.readiness import production_readiness, readiness_status


def _clear_readiness_env(monkeypatch):
    for name in (
        'SMTP_HOST','SMTP_PORT','SMTP_USER','SMTP_PASS','SMTP_FROM_EMAIL',
        'MAIL_DEFAULT_SENDER','ADMIN_EMAIL','ADMIN_2FA_ENABLED','S3_BUCKET',
        'S3_ENDPOINT_URL','AWS_ACCESS_KEY_ID','AWS_SECRET_ACCESS_KEY','AWS_REGION',
        'RATELIMIT_STORAGE_URI','STRICT_PRODUCTION_READINESS',
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


def test_readiness_reports_missing_launch_configuration(monkeypatch):
    _clear_readiness_env(monkeypatch)
    checks = production_readiness()
    assert checks == {
        'persistent_document_storage': False,
        'shared_rate_limit_storage': False,
        'smtp_delivery': False,
        'admin_2fa': False,
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


def test_readiness_endpoint_is_non_blocking_until_strict_mode(client, monkeypatch):
    _clear_readiness_env(monkeypatch)
    response = client.get('/readiness')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'needs_configuration'


def test_readiness_endpoint_can_fail_closed_in_strict_mode(client, monkeypatch):
    _clear_readiness_env(monkeypatch)
    monkeypatch.setenv('STRICT_PRODUCTION_READINESS', '1')
    response = client.get('/readiness')
    assert response.status_code == 503
    assert response.get_json()['status'] == 'needs_configuration'
