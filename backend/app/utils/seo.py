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
    for suffix in (' Application Assistance', ' Service Assistance', ' Assistance', ' Guidance'):
        if name.endswith(suffix):
            base = name[:-len(suffix)].rstrip()
            return base if base.lower().endswith(' order') else base + ' Apply'
    if name.lower().endswith(' order apply'):
        return name[:-len(' Apply')]
    return name
