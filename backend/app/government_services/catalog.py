import json
from pathlib import Path

from ..models.service import Category, PlatformSetting, Service
from ..utils.database import db
from ..utils.service_requirements import SERVICE_REQUIREMENT_PROFILE_BY_NAME

CATALOG_PATH = Path(__file__).with_name('verified_catalog.json')
ALLOWED_FEE_STATUSES = {'known', 'none', 'unconfirmed'}
ALLOWED_STATES = {'active', 'retired'}


def load_verified_catalog(path=CATALOG_PATH):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('schema_version') != 1:
        raise ValueError('Unsupported government-service catalogue schema version.')
    services = data.get('services')
    if not isinstance(services, list):
        raise ValueError('Government-service catalogue requires a services list.')
    seen = set()
    for entry in services:
        name = str(entry.get('name') or '').strip()
        category = str(entry.get('category') or '').strip()
        source_url = str(entry.get('source_url') or '').strip()
        source_name = str(entry.get('source_name') or '').strip()
        verified_at = str(entry.get('verified_at') or '').strip()
        state = str(entry.get('state') or 'active').strip().lower()
        fee_status = str(entry.get('official_fee_status') or 'unconfirmed').strip().lower()
        if not name or name in seen:
            raise ValueError(f'Invalid or duplicate government service name: {name!r}')
        if not category:
            raise ValueError(f'{name}: category is required.')
        if not source_name or not source_url.startswith('https://') or not verified_at:
            raise ValueError(f'{name}: verified first-party source metadata is required.')
        if state not in ALLOWED_STATES:
            raise ValueError(f'{name}: invalid state {state!r}.')
        if fee_status not in ALLOWED_FEE_STATUSES:
            raise ValueError(f'{name}: invalid official fee status {fee_status!r}.')
        if fee_status == 'known' and entry.get('official_fee_inr') is None:
            raise ValueError(f'{name}: a known official fee requires official_fee_inr.')
        seen.add(name)
    return data


def _assistance_fee():
    setting = db.session.get(PlatformSetting, 'assistance_fee_inr')
    if setting:
        try:
            return max(0.0, float(setting.value))
        except (TypeError, ValueError):
            pass
    return 30.0


def sync_verified_catalog(path=CATALOG_PATH):
    """Upsert only reviewed first-party government-service records.

    The checked-in manifest is the controlled handoff between official-source
    monitoring and production. A newly verified service can be added to the
    manifest without writing a database migration; the next deploy/startup
    synchronizes it into the live catalogue. Retired services are deactivated
    rather than deleted so historical requests remain intact.
    """
    data = load_verified_catalog(path)
    default_price = _assistance_fee()
    changed = 0

    for entry in data['services']:
        category = Category.query.filter_by(name=entry['category']).first()
        if category is None:
            category = Category(name=entry['category'])
            db.session.add(category)
            db.session.flush()

        service = Service.query.filter_by(name=entry['name']).first()
        if service is None:
            service = Service(name=entry['name'])
            db.session.add(service)

        fee_status = entry.get('official_fee_status', 'unconfirmed')
        fee_amount = entry.get('official_fee_inr')
        if fee_status == 'none':
            fee_amount = 0.0
        elif fee_status == 'unconfirmed':
            fee_amount = None

        expected = {
            'description': entry.get('description') or '',
            'keywords': entry.get('keywords') or '',
            'category_id': category.id,
            'is_active': entry.get('state', 'active') == 'active',
            'official_fee_status': fee_status,
            'official_fee_inr': fee_amount,
        }
        if service.price_inr is None:
            expected['price_inr'] = default_price

        for field, value in expected.items():
            if getattr(service, field) != value:
                setattr(service, field, value)
                changed += 1

        profile = str(entry.get('requirement_profile') or '').strip()
        if profile:
            SERVICE_REQUIREMENT_PROFILE_BY_NAME[entry['name']] = profile

    if changed:
        db.session.commit()
    return {'services': len(data['services']), 'changes': changed, 'verified_at': data.get('verified_at')}
