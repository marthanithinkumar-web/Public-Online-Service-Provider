import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

from .catalog import CATALOG_PATH, _active
from .discovery import dedupe_items, discover_official_scholarships, is_official_url, source_key_for_url

OFFICIAL_FAILURE_GRACE_DAYS = 7
PRIVATE_LISTING_MAX_AGE_DAYS = 30


def _parse_timestamp(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _age_days(value, now):
    parsed = _parse_timestamp(value)
    if not parsed:
        return None
    return max(0.0, (now - parsed).total_seconds() / 86400)


def _normalise_nsp_provider(item):
    """Prevent a neighbouring NSP scheme title from being published as provider."""
    value = dict(item)
    if value.get('source_key') != 'nsp':
        return value
    provider = str(value.get('provider') or '').strip()
    title = str(value.get('title') or '').strip()
    lower = provider.lower()
    trustworthy_prefixes = (
        'ministry of ',
        'department of ',
        'all india council for technical education',
        'north eastern council',
        'university grants commission',
    )
    scheme_like = any(marker in lower for marker in (' scholarship', ' scholarship scheme', ' fellowship', ' financial assistance', ' welfare based scheme', ' merit based scheme'))
    if provider and (lower.startswith(trustworthy_prefixes) or not scheme_like):
        return value
    if title.lower().startswith('aicte'):
        value['provider'] = 'All India Council for Technical Education (AICTE)'
    else:
        value['provider'] = 'Government of India (via National Scholarship Portal)'
    value['provider_normalized'] = True
    return value


def _normalise_existing(item, generated_at=None):
    value = dict(item)
    official = is_official_url(value.get('source_url'))
    value['source_type'] = 'official' if official else 'private'
    value['is_official'] = official
    if not value.get('source_key'):
        value['source_key'] = source_key_for_url(value.get('source_url')) or ('private_manual' if not official else 'official_manual')
    if not value.get('record_type'):
        value['record_type'] = 'scholarship'
    if not value.get('last_seen_at'):
        value['last_seen_at'] = value.get('verified_at') or generated_at
    if not value.get('discovery_method'):
        value['discovery_method'] = 'existing_snapshot' if official else 'manual_or_partner_listing'
    return _normalise_nsp_provider(value)


def _preserve_previous(item, health, now, check_date):
    if not _active(item, check_date):
        return False
    age = _age_days(item.get('last_seen_at'), now)
    if item.get('source_type') == 'private':
        return age is not None and age <= PRIVATE_LISTING_MAX_AGE_DAYS
    source_key = item.get('source_key')
    source_health = health.get(source_key)
    if source_health and source_health.get('ok'):
        return False
    return age is not None and age <= OFFICIAL_FAILURE_GRACE_DAYS


def refresh_snapshot(path=CATALOG_PATH, today=None, *, discover=True, strict=False, now=None, discovery_func=None):
    path = Path(path)
    try:
        previous = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError, TypeError):
        previous = {'items': []}

    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    check_date = today or now.date()
    generated_at = previous.get('generated_at')
    previous_items = [
        _normalise_existing(item, generated_at)
        for item in previous.get('items', [])
        if isinstance(item, dict)
    ]

    health = {}
    discovered = []
    if discover:
        discoverer = discovery_func or discover_official_scholarships
        discovered, health = discoverer(now=now)
        discovered = [_normalise_nsp_provider(item) for item in discovered]
        if strict:
            nsp = health.get('nsp') or {}
            if not nsp.get('ok'):
                raise RuntimeError('National Scholarship Portal discovery failed; refusing to publish an unverified daily snapshot.')
            if sum(1 for item in discovered if item.get('source_type') == 'official') < 5:
                raise RuntimeError('Official scholarship discovery returned too few current listings; refusing to publish.')

    preserved = []
    for item in previous_items:
        if not discover or _preserve_previous(item, health, now, check_date):
            if discover and item.get('source_type') == 'official':
                item['stale_source'] = True
            preserved.append(item)

    items = dedupe_items([*discovered, *preserved])
    items = [item for item in items if _active(item, check_date)]
    items.sort(key=lambda item: (
        0 if item.get('source_type') == 'official' else 1,
        item.get('deadline') or '9999-12-31',
        item.get('title') or '',
    ))

    official_count = sum(1 for item in items if item.get('source_type') == 'official')
    private_count = sum(1 for item in items if item.get('source_type') == 'private')
    stale_source_count = sum(1 for item in items if item.get('stale_source'))
    refreshed = {
        'generated_at': now.isoformat(),
        'count': len(items),
        'official_count': official_count,
        'private_count': private_count,
        'stale_source_count': stale_source_count,
        'discovery': {
            'mode': 'official_daily_discovery' if discover else 'expiry_only',
            'checked_at': now.isoformat(),
            'source_health': health,
        },
        'items': items,
    }
    path.write_text(json.dumps(refreshed, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return refreshed


def main():
    parser = argparse.ArgumentParser(description='Discover current scholarships from official sources and refresh the public snapshot.')
    parser.add_argument('--output', default=str(CATALOG_PATH))
    parser.add_argument('--no-discover', action='store_true', help='Only remove closed/stale entries; do not contact official sources.')
    parser.add_argument('--strict', action='store_true', help='Fail rather than publish when the primary official discovery source is unhealthy.')
    args = parser.parse_args()
    payload = refresh_snapshot(args.output, discover=not args.no_discover, strict=args.strict)
    healthy = sum(1 for source in payload.get('discovery', {}).get('source_health', {}).values() if source.get('ok'))
    print(
        f"Published {payload['count']} active scholarships "
        f"({payload['official_count']} official, {payload['private_count']} private/partner); "
        f"{healthy} official sources healthy."
    )


if __name__ == '__main__':
    main()
