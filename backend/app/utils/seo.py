import re
import unicodedata


def slugify(value: str) -> str:
    """Return a stable, URL-safe slug for a public catalog name."""
    normalized = unicodedata.normalize('NFKD', value or '').encode('ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[^a-z0-9]+', '-', normalized.lower()).strip('-')
    return slug or 'service'


def application_service_name(value: str) -> str:
    """Use ``Apply <service>`` without changing stored catalog records.

    Order services intentionally remain commands such as ``Aadhaar PVC Card
    Order``.  The helper is idempotent because administrators receive the
    public display title while editing the catalog.
    """
    name = (value or '').strip()
    if not name:
        return name
    if name.lower().startswith('apply '):
        return f"Apply {name[6:].strip()}"
    if name.lower().endswith(' order apply'):
        return name[:-len(' Apply')]
    if name.lower().endswith(' apply'):
        return f"Apply {name[:-len(' Apply')].strip()}"
    for suffix in (' Application Assistance', ' Service Assistance', ' Assistance', ' Guidance'):
        if name.endswith(suffix):
            base = name[:-len(suffix)].rstrip()
            return base if base.lower().endswith(' order') else f'Apply {base}'
    return name


def legacy_application_service_name(value: str) -> str:
    """Return the former trailing-Apply title for backwards-compatible URLs."""
    name = (value or '').strip()
    if name.lower().startswith('apply '):
        name = name[6:].strip()
    for suffix in (' Application Assistance', ' Service Assistance', ' Assistance', ' Guidance'):
        if name.endswith(suffix):
            base = name[:-len(suffix)].rstrip()
            return base if base.lower().endswith(' order') else f'{base} Apply'
    return name
