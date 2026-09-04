import os
import smtplib
import ssl
from email.utils import parseaddr
from urllib.parse import urlparse


def _present(name):
    return bool((os.getenv(name) or '').strip())


def smtp_configured():
    if not _present('SMTP_HOST') or not _present('SMTP_PORT'):
        return False
    try:
        port = int(os.getenv('SMTP_PORT') or 0)
    except (TypeError, ValueError):
        return False
    if port < 1 or port > 65535:
        return False
    sender = (
        os.getenv('SMTP_FROM_EMAIL')
        or os.getenv('MAIL_DEFAULT_SENDER')
        or os.getenv('ADMIN_EMAIL')
        or os.getenv('SMTP_USER')
        or ''
    ).strip()
    parsed_sender = parseaddr(sender)[1]
    if not parsed_sender or '\n' in parsed_sender or '\r' in parsed_sender:
        return False
    user = _present('SMTP_USER')
    password = _present('SMTP_PASS')
    return user == password


def smtp_connectivity():
    """Confirm the configured SMTP server can establish a secured session.

    This verifies connection, STARTTLS/SSL, and authentication where configured,
    but deliberately sends no email and never exposes credentials in the
    readiness response.
    """
    if not smtp_configured():
        return False
    host = (os.getenv('SMTP_HOST') or '').strip()
    port = int(os.getenv('SMTP_PORT') or 0)
    user = os.getenv('SMTP_USER')
    password = os.getenv('SMTP_PASS')
    use_ssl = os.getenv('SMTP_USE_SSL', '0') == '1' or port == 465
    use_tls = os.getenv('SMTP_USE_TLS', '1') != '0' and not use_ssl
    smtp_class = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    smtp_kwargs = {'host': host, 'port': port, 'timeout': 5}
    if use_ssl:
        smtp_kwargs['context'] = ssl.create_default_context()
    try:
        with smtp_class(**smtp_kwargs) as connection:
            connection.ehlo()
            if use_tls:
                connection.starttls(context=ssl.create_default_context())
                connection.ehlo()
            if user and password:
                connection.login(user, password)
            code, _ = connection.noop()
            return 200 <= int(code) < 400
    except Exception:
        return False


def persistent_storage_configured():
    if not all(_present(name) for name in (
        'S3_BUCKET',
        'S3_ENDPOINT_URL',
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_REGION',
    )):
        return False
    endpoint = (os.getenv('S3_ENDPOINT_URL') or '').strip()
    parsed = urlparse(endpoint)
    return parsed.scheme == 'https' and bool(parsed.netloc)


def shared_rate_limit_configured():
    uri = (os.getenv('RATELIMIT_STORAGE_URI') or '').strip()
    if not uri:
        return False
    parsed = urlparse(uri)
    return parsed.scheme in {'redis', 'rediss'} and bool(parsed.hostname)


def shared_rate_limit_connectivity():
    """Confirm that the configured Redis/Valkey rate-limit store answers PING.

    The check uses short timeouts and never exposes credentials or connection
    details. It is intended for the production /readiness endpoint only.
    """
    if not shared_rate_limit_configured():
        return False
    try:
        import redis

        client = redis.Redis.from_url(
            os.environ['RATELIMIT_STORAGE_URI'],
            socket_connect_timeout=2,
            socket_timeout=2,
            retry_on_timeout=False,
        )
        return bool(client.ping())
    except Exception:
        return False


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
