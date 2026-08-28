"""Validation helpers shared by public account endpoints."""

import re


_EMAIL_LOCAL_RE = re.compile(r"^[A-Za-z0-9!#$%&'*+/=?^_`{|}~.-]+$")
_DOMAIN_LABEL_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")


def normalize_email(value: object) -> str | None:
    """Return a normalized, public-looking email address or ``None``.

    Registration intentionally requires a domain with a real top-level suffix;
    local-only addresses such as ``person@localhost`` are not accepted.
    """
    email = str(value or '').strip().lower()
    if not email or len(email) > 254 or email.count('@') != 1:
        return None
    local, domain = email.rsplit('@', 1)
    if not local or len(local) > 64 or local.startswith('.') or local.endswith('.') or '..' in local:
        return None
    if not _EMAIL_LOCAL_RE.fullmatch(local):
        return None
    if not domain or len(domain) > 253 or '..' in domain:
        return None
    labels = domain.split('.')
    if len(labels) < 2 or any(not _DOMAIN_LABEL_RE.fullmatch(label) for label in labels):
        return None
    if len(labels[-1]) < 2 or not labels[-1].isalpha():
        return None
    return email


def normalize_indian_mobile(value: object) -> str | None:
    """Normalize an Indian mobile number to ``+91XXXXXXXXXX``.

    Accepts the common 10-digit, ``0``-prefixed, ``91``-prefixed, and ``+91``
    forms. Indian mobile subscriber numbers must begin with 6, 7, 8, or 9.
    """
    raw = str(value or '').strip()
    if not raw:
        return None
    if re.search(r"[^0-9+()\s.-]", raw) or raw.count('+') > 1 or ('+' in raw and not raw.startswith('+')):
        return None
    digits = re.sub(r'\D', '', raw)
    if len(digits) == 12 and digits.startswith('91'):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith('0'):
        digits = digits[1:]
    if len(digits) != 10 or digits[0] not in '6789':
        return None
    return f'+91{digits}'
