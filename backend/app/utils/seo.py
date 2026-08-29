import re
import unicodedata


def slugify(value: str) -> str:
    """Return a stable, URL-safe slug for a public catalog name."""
    normalized = unicodedata.normalize('NFKD', value or '').encode('ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[^a-z0-9]+', '-', normalized.lower()).strip('-')
    return slug or 'service'
