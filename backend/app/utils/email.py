import os
import smtplib
from email.message import EmailMessage

# Simple email helper: in development prints token; in production uses SMTP settings

def send_email(to_address: str, subject: str, body: str):
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT') or 0)
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')

    if not smtp_host or not smtp_port:
        # Never write password-reset or verification tokens into production
        # logs. Console delivery is restricted to local development.
        if os.getenv('FLASK_ENV') == 'production' or os.getenv('FORCE_HTTPS') == '1':
            return False
        print(f"[EMAIL-DEV] To: {to_address}\nSubject: {subject}\n\n{body}\n")
        return True

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = smtp_user or f'no-reply@{smtp_host}'
    msg['To'] = to_address
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as s:
            s.starttls()
            if smtp_user and smtp_pass:
                s.login(smtp_user, smtp_pass)
            s.send_message(msg)
        return True
    except Exception as e:
        print('Failed to send email:', e)
        return False
