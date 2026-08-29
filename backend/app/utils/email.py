import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, parseaddr


logger = logging.getLogger(__name__)

# Simple email helper: in development prints token; in production uses SMTP settings

def send_email(to_address: str, subject: str, body: str):
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT') or 0)
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')
    from_email = (
        os.getenv('SMTP_FROM_EMAIL')
        or os.getenv('MAIL_DEFAULT_SENDER')
        or os.getenv('ADMIN_EMAIL')
        or smtp_user
    )
    from_name = (os.getenv('SMTP_FROM_NAME') or 'Public Online Service Provider').strip()

    if not smtp_host or not smtp_port:
        # Never write password-reset or verification tokens into production
        # logs. Console delivery is restricted to local development.
        if os.getenv('FLASK_ENV') == 'production' or os.getenv('FORCE_HTTPS') == '1':
            return False
        print(f"[EMAIL-DEV] To: {to_address}\nSubject: {subject}\n\n{body}\n")
        return True

    # Brevo's SMTP login is an authentication identity, not necessarily an
    # approved From address. Use a separately verified sender (or ADMIN_EMAIL
    # as the backwards-compatible fallback) so Brevo can accept delivery.
    parsed_from = parseaddr(from_email or '')[1]
    if not parsed_from or '\n' in parsed_from or '\r' in parsed_from:
        logger.error('Email delivery configuration is missing a valid sender address')
        return False
    if bool(smtp_user) != bool(smtp_pass):
        logger.error('Email delivery configuration has incomplete SMTP credentials')
        return False

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = formataddr((from_name, parsed_from))
    msg['To'] = to_address
    msg.set_content(body)

    try:
        use_ssl = os.getenv('SMTP_USE_SSL', '0') == '1' or smtp_port == 465
        use_tls = os.getenv('SMTP_USE_TLS', '1') != '0' and not use_ssl
        smtp_class = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
        smtp_kwargs = {'host': smtp_host, 'port': smtp_port, 'timeout': 20}
        if use_ssl:
            smtp_kwargs['context'] = ssl.create_default_context()
        with smtp_class(**smtp_kwargs) as s:
            s.ehlo()
            if use_tls:
                s.starttls(context=ssl.create_default_context())
                s.ehlo()
            if smtp_user and smtp_pass:
                s.login(smtp_user, smtp_pass)
            s.send_message(msg)
        return True
    except Exception as exc:
        # Do not log the message body, reset token, recipient, or credentials.
        logger.error('SMTP delivery failed (%s)', type(exc).__name__)
        return False
