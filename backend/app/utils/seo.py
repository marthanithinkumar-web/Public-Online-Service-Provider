import re
import unicodedata


def slugify(value: str) -> str:
    """Return a stable, URL-safe slug for a public catalog name."""
    normalized = unicodedata.normalize('NFKD', value or '').encode('ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[^a-z0-9]+', '-', normalized.lower()).strip('-')
    return slug or 'service'


def application_service_name(value: str) -> str:
    """Use a short action title without changing stored catalog records."""
    name = (value or '').strip()
    for suffix in (' Application Assistance', ' Service Assistance', ' Assistance'):
        if name.endswith(suffix):
            return name[:-len(suffix)].rstrip() + ' Apply'
    return name
