import os


def _present(name):
    return bool((os.getenv(name) or '').strip())


def smtp_configured():
    if not _present('SMTP_HOST') or not _present('SMTP_PORT'):
        return False
    sender = (
        os.getenv('SMTP_FROM_EMAIL')
        or os.getenv('MAIL_DEFAULT_SENDER')
        or os.getenv('ADMIN_EMAIL')
        or os.getenv('SMTP_USER')
        or ''
    ).strip()
    if not sender:
        return False
    user = _present('SMTP_USER')
    password = _present('SMTP_PASS')
    return user == password


def persistent_storage_configured():
    return all(_present(name) for name in (
        'S3_BUCKET',
        'S3_ENDPOINT_URL',
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_REGION',
    ))


def shared_rate_limit_configured():
    uri = (os.getenv('RATELIMIT_STORAGE_URI') or '').strip().lower()
    return uri.startswith(('redis://', 'rediss://'))


def production_readiness():
    smtp_ready = smtp_configured()
    admin_2fa_enabled = os.getenv('ADMIN_2FA_ENABLED', '0') == '1'
    checks = {
        'persistent_document_storage': persistent_storage_configured(),
        'shared_rate_limit_storage': shared_rate_limit_configured(),
        'smtp_delivery': smtp_ready,
        'admin_2fa': admin_2fa_enabled and smtp_ready,
    }
    return checks


def readiness_status(checks):
    return 'ready' if all(checks.values()) else 'needs_configuration'
