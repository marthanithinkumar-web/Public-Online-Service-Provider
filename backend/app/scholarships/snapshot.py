import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

from .catalog import CATALOG_PATH, _active
from .discovery import dedupe_items, discover_official_scholarships, is_official_url, slugify, source_key_for_url
from .source_enrichment import enrich_scholarships

OFFICIAL_FAILURE_GRACE_DAYS = 7
PRIVATE_LISTING_MAX_AGE_DAYS = 30


def _parse_timestamp(value):
    if not value:return None
    try:parsed=datetime.fromisoformat(str(value).replace('Z','+00:00'))
    except ValueError:return None
    if parsed.tzinfo is None:parsed=parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)

def _age_days(value,now):
    parsed=_parse_timestamp(value);return None if not parsed else max(0.0,(now-parsed).total_seconds()/86400)

def _normalise_nsp_provider(item):
    value=dict(item)
    if value.get('source_key')!='nsp':return value
    provider=str(value.get('provider') or '').strip();title=str(value.get('title') or '').strip();lower=provider.lower();trustworthy_prefixes=('ministry of ','department of ','all india council for technical education','north eastern council','university grants commission');scheme_like=any(marker in lower for marker in (' scholarship',' scholarship scheme',' fellowship',' financial assistance',' welfare based scheme',' merit based scheme'))
    if provider and (lower.startswith(trustworthy_prefixes) or not scheme_like):return value
    value['provider']='All India Council for Technical Education (AICTE)' if title.lower().startswith('aicte') else 'Government of India (via National Scholarship Portal)';value['provider_normalized']=True;return value

def _normalise_existing(item,generated_at=None):
    value=dict(item);official=is_official_url(value.get('source_url'));value['source_type']='official' if official else 'private';value['is_official']=official
    if not value.get('source_key'):value['source_key']=source_key_for_url(value.get('source_url')) or ('private_manual' if not official else 'official_manual')
    if not value.get('record_type'):value['record_type']='scholarship'
    if not value.get('last_seen_at'):value['last_seen_at']=value.get('verified_at') or generated_at
    if not value.get('discovery_method'):value['discovery_method']='existing_snapshot' if official else 'manual_or_partner_listing'
    return _normalise_nsp_provider(value)

def _preserve_previous(item,health,now,check_date):
    if not _active(item,check_date):return False
    age=_age_days(item.get('last_seen_at'),now)
    if item.get('source_type')=='private':return age is not None and age<=PRIVATE_LISTING_MAX_AGE_DAYS
    source_health=health.get(item.get('source_key'))
    if source_health and source_health.get('ok'):return False
    return age is not None and age<=OFFICIAL_FAILURE_GRACE_DAYS

def _closed_record(item, check_date, now):
    value = dict(item)
    status = str(value.get('status') or '').lower()
    deadline = None
    try:
        deadline = date.fromisoformat(str(value.get('deadline') or '')[:10])
    except (TypeError, ValueError):
        pass
    if status in {'closed', 'expired', 'cancelled', 'withdrawn'}:
        reason = value.get('closure_reason') or ('official_status_' + status)
    elif deadline is not None and deadline < check_date:
        reason = 'deadline_passed'
    else:
        return None
    value['status'] = 'closed'
    value['application_status'] = 'closed' if status != 'cancelled' else 'cancelled'
    value['closure_reason'] = reason
    value['closed_at'] = value.get('closed_at') or now.isoformat()
    return value


def refresh_snapshot(path=CATALOG_PATH,today=None,*,discover=True,strict=False,now=None,discovery_func=None):
    path=Path(path)
    try:previous=json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError,TypeError):previous={'items':[]}
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:now=now.replace(tzinfo=timezone.utc)
    check_date=today or now.date();generated_at=previous.get('generated_at');previous_items=[_normalise_existing(item,generated_at) for item in previous.get('items',[]) if isinstance(item,dict)];previous_closed=[_normalise_existing(item,generated_at) for item in previous.get('closed_items',[]) if isinstance(item,dict)]
    health={};discovered=[]
    if discover:
        discoverer=discovery_func or discover_official_scholarships;discovered,health=discoverer(now=now);discovered=[_normalise_nsp_provider(item) for item in discovered]
        # One bounded pass per authoritative source adds scheme-specific facts
        # visible on the source page before the public snapshot is published.
        discovered=enrich_scholarships(discovered)
        if strict:
            nsp=health.get('nsp') or {}
            if not nsp.get('ok'):raise RuntimeError('National Scholarship Portal discovery failed; refusing to publish an unverified daily snapshot.')
            if sum(1 for item in discovered if item.get('source_type')=='official')<5:raise RuntimeError('Official scholarship discovery returned too few current listings; refusing to publish.')
    preserved=[];stale_preserved=[]
    previous_stale=[_normalise_existing(item,generated_at) for item in previous.get('stale_items',[]) if isinstance(item,dict)]
    for item in previous_items:
        if not discover:
            preserved.append(item)
        elif _preserve_previous(item,health,now,check_date):
            source_health=health.get(item.get('source_key')) or {}
            if item.get('source_type')=='official' and not source_health.get('ok'):
                item['stale_source']=True;stale_preserved.append(item)
            else:
                preserved.append(item)
    for item in previous_stale:
        source_health=health.get(item.get('source_key')) or {}
        age=_age_days(item.get('last_seen_at'),now)
        still_open=_active({**item,'stale_source':False},check_date)
        if not discover or (not source_health.get('ok') and still_open and age is not None and age<=OFFICIAL_FAILURE_GRACE_DAYS):
            item['stale_source']=True;stale_preserved.append(item)
    items=dedupe_items([*discovered,*preserved]);items=[item for item in items if _active(item,check_date)];items.sort(key=lambda item:(0 if item.get('source_type')=='official' else 1,item.get('deadline') or '9999-12-31',item.get('title') or ''))
    active_keys={(slugify(item.get('title')),slugify(item.get('region') or 'india')) for item in items}
    closed_candidates=[]
    for candidate in [*previous_closed,*previous_items,*previous_stale,*discovered]:
        closed=_closed_record(candidate,check_date,now)
        if not closed:
            continue
        key=(slugify(closed.get('title')),slugify(closed.get('region') or 'india'))
        if key not in active_keys:
            closed_candidates.append(closed)
    closed_items=dedupe_items(closed_candidates)
    stale_items=dedupe_items([item for item in stale_preserved if item.get('source_type')=='official' and item.get('deadline') and item.get('deadline')>=check_date.isoformat()])
    official_count=sum(1 for item in items if item.get('source_type')=='official');private_count=sum(1 for item in items if item.get('source_type')=='private');stale_source_count=len(stale_items)
    refreshed={'generated_at':now.isoformat(),'count':len(items),'official_count':official_count,'private_count':private_count,'stale_source_count':stale_source_count,'closed_count':len(closed_items),'discovery':{'mode':'official_daily_discovery' if discover else 'expiry_only','checked_at':now.isoformat(),'source_health':health},'items':items,'closed_items':closed_items,'stale_items':stale_items};path.write_text(json.dumps(refreshed,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return refreshed

def main():
    parser=argparse.ArgumentParser(description='Discover current scholarships from official sources and refresh the public snapshot.');parser.add_argument('--output',default=str(CATALOG_PATH));parser.add_argument('--no-discover',action='store_true',help='Only remove closed/stale entries; do not contact official sources.');parser.add_argument('--strict',action='store_true',help='Fail rather than publish when the primary official discovery source is unhealthy.');args=parser.parse_args();payload=refresh_snapshot(args.output,discover=not args.no_discover,strict=args.strict);healthy=sum(1 for source in payload.get('discovery',{}).get('source_health',{}).values() if source.get('ok'));print(f"Published {payload['count']} active scholarships ({payload['official_count']} official, {payload['private_count']} private/partner); {healthy} official sources healthy.")
if __name__=='__main__':main()
