"""Build a public, database-independent snapshot of verified job notices."""
import argparse
import hashlib
import json
from datetime import date, datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .notice_enrichment import enrich_job_item
from .official_fetch import fetch_official_page, validate_official_url
from .rules import item_hash, slugify, target_status, unique_slug
from .sources import SOURCE_DEFINITIONS


def utc_now(): return datetime.now(timezone.utc).replace(microsecond=0)
def _iso(value): return value.isoformat() if value else None


def _is_open(job, today=None, now=None):
    raw = job.get('deadline')
    if not raw:
        return False
    try:
        deadline = date.fromisoformat(str(raw)[:10])
        tz = ZoneInfo(str(job.get('deadline_timezone') or 'Asia/Kolkata'))
        current = now or utc_now()
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        local = current.astimezone(tz)
        if deadline < local.date():
            return False
        if deadline == local.date() and job.get('deadline_cutoff_time'):
            cutoff = time.fromisoformat(str(job['deadline_cutoff_time']))
            if local.timetz().replace(tzinfo=None) >= cutoff:
                return False
        return True
    except (TypeError, ValueError, KeyError):
        return False


def _safe_previous(existing):
    if not isinstance(existing,dict):return {'items':[],'sources':[]}
    return {'items':existing.get('items') if isinstance(existing.get('items'),list) else [],'sources':existing.get('sources') if isinstance(existing.get('sources'),list) else []}


def _serialize_item(item, definition, checked_at, previous=None, now=None):
    validate_official_url(item.official_notice_url)
    if item.application_url:
        validate_official_url(item.application_url)
    content_hash = item_hash(item)
    previous = previous or {}
    current = now or datetime.fromisoformat(checked_at.replace('Z', '+00:00'))
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    timezone_name = item.deadline_timezone or 'Asia/Kolkata'
    local = current.astimezone(ZoneInfo(timezone_name))
    deadline = item.deadline
    cutoff = item.deadline_cutoff_time
    if deadline == local.date():
        application_status = 'deadline_today'
        can_apply = bool(cutoff and local.timetz().replace(tzinfo=None) < cutoff)
        if cutoff:
            status_label = f'Deadline today—closes at {cutoff.isoformat(timespec="minutes")} {timezone_name}'
        else:
            status_label = 'Deadline today—check official portal'
    else:
        application_status = 'open'
        can_apply = True
        status_label = 'Verified open'
    source = {
        'key': definition.key,
        'name': definition.name,
        'listing_url': definition.listing_url,
        'last_sync_completed_at': checked_at,
        'last_successful_sync_at': checked_at,
        'consecutive_failures': 0,
        'last_sync_status': 'success',
    }
    return {
        'id': int(content_hash[:12], 16),
        'slug': unique_slug(item, content_hash),
        'title': item.title[:500],
        'organization': item.organization[:500],
        'job_type': item.job_type if item.job_type in {'government', 'private'} else 'government',
        'appointment_type': item.appointment_type,
        'location': item.location,
        'qualification': item.qualification,
        'age_limit': item.age_limit,
        'application_fee': item.application_fee,
        'vacancies': item.vacancies,
        'salary': item.salary,
        'summary': item.summary,
        'issue_date': _iso(item.issue_date),
        'application_start_date': _iso(item.application_start_date),
        'deadline': _iso(deadline),
        'deadline_cutoff_time': cutoff.isoformat(timespec='minutes') if cutoff else None,
        'deadline_timezone': timezone_name,
        'application_status': application_status,
        'can_apply': can_apply,
        'status_label': status_label,
        'source_checked_at': checked_at,
        'official_notice_url': item.official_notice_url,
        'application_url': item.application_url,
        'status': 'published',
        'verification_status': 'official_source_checked',
        'confidence': float(item.confidence or 0),
        'is_featured': bool(previous.get('is_featured', False)),
        'source': source,
        'first_seen_at': previous.get('first_seen_at') or checked_at,
        'last_seen_at': checked_at,
        'published_at': previous.get('published_at') or checked_at,
        'content_hash': content_hash,
    }


def _fallback_job_hash(job):
    payload={key:job.get(key) for key in ('title','organization','deadline','location','official_notice_url','application_url','id')}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,default=str).encode('utf-8')).hexdigest()


def _deduplicate_job_identities(jobs):
    """Keep one public record per official notice, then fall back to content identity."""
    seen=set();deduplicated=[]
    for job in jobs:
        official_url=str(job.get('official_notice_url') or '').strip().rstrip('/').lower()
        identity=f'url:{official_url}' if official_url else f'hash:{str(job.get("content_hash") or "").strip() or _fallback_job_hash(job)}'
        if identity in seen:continue
        seen.add(identity);deduplicated.append(job)
    return deduplicated


def _ensure_unique_slugs(jobs):
    """Preserve valid public job URLs while deterministically repairing collisions."""
    seen=set()
    for job in jobs:
        current=str(job.get('slug') or '').strip()
        if current and current not in seen:
            seen.add(current);continue
        digest=str(job.get('content_hash') or '').strip() or _fallback_job_hash(job)
        base=slugify(f"{job.get('organization') or 'job'}-{job.get('title') or 'opportunity'}")
        # Keep well below the 250-character slug limit after adding the suffix.
        candidate=f"{base[:235].rstrip('-')}-{digest[:10]}"
        if candidate in seen:
            # Extremely unlikely hash-prefix collision; extend deterministically.
            candidate=f"{base[:225].rstrip('-')}-{digest[:20]}"
        if candidate in seen:
            suffix=1
            root=candidate[:240].rstrip('-')
            while f'{root}-{suffix}' in seen:suffix+=1
            candidate=f'{root}-{suffix}'
        job['slug']=candidate
        seen.add(candidate)
    return jobs


def build_snapshot(existing=None, session=None, now=None):
    now = now or utc_now()
    checked_at = now.isoformat().replace('+00:00', 'Z')
    previous = _safe_previous(existing)
    previous_jobs = previous['items']
    previous_by_hash = {
        job.get('content_hash'): job
        for job in previous_jobs
        if isinstance(job, dict) and job.get('content_hash')
    }
    previous_by_source = {}
    for job in previous_jobs:
        if isinstance(job, dict) and (job.get('source') or {}).get('key'):
            previous_by_source.setdefault(job['source']['key'], []).append(job)
    previous_sources = {
        source.get('key'): source
        for source in previous['sources']
        if isinstance(source, dict) and source.get('key')
    }

    jobs = []
    sources = []
    seen_hashes = set()
    successful_sources = 0
    review_count = 0
    max_notice_enrichments_per_source = 12

    for definition in SOURCE_DEFINITIONS:
        previous_source = previous_sources.get(definition.key, {})
        previous_success = previous_source.get('last_successful_sync_at')
        if not previous_success and previous_source.get('last_sync_status') == 'success':
            previous_success = previous_source.get('last_sync_completed_at')
        previous_failures = int(previous_source.get('consecutive_failures') or 0)
        previous_items = previous_by_source.get(definition.key, [])

        try:
            html = fetch_official_page(definition.listing_url, session=session)
            parsed = definition.parser(html, definition.listing_url)
            if not parsed:
                review_count += len(previous_items)
                sources.append({
                    'key': definition.key, 'name': definition.name,
                    'listing_url': definition.listing_url, 'enabled': True,
                    'last_sync_completed_at': checked_at,
                    'last_successful_sync_at': previous_success,
                    'consecutive_failures': previous_failures + 1,
                    'last_sync_status': 'degraded', 'fetched_count': 0,
                    'published_count': 0,
                    'last_error': 'Official source returned no parseable listings; previous records were held for review and removed from the verified public feed.',
                })
                continue

            published_count = 0
            notice_enrichments = 0
            source_seen_hashes = set()
            for item in parsed:
                notice_url = str(item.official_notice_url or '').rstrip('/')
                listing_url = str(definition.listing_url or '').rstrip('/')
                if item.confidence >= 0.8 and notice_url and notice_url != listing_url and notice_enrichments < max_notice_enrichments_per_source:
                    item = enrich_job_item(item, session=session)
                    notice_enrichments += 1
                if 'notice_excluded_result_only' in (item.warnings or []):
                    continue

                digest = item_hash(item)
                source_seen_hashes.add(digest)
                status = target_status(
                    item,
                    now=now,
                    allow_missing_deadline=definition.allow_missing_deadline,
                    missing_deadline_max_age_days=definition.missing_deadline_max_age_days,
                )
                if status != 'published':
                    review_count += int(status == 'needs_review')
                    continue
                if digest in seen_hashes:
                    continue
                serialized = _serialize_item(item, definition, checked_at, previous_by_hash.get(digest), now=now)
                seen_hashes.add(digest)
                jobs.append(serialized)
                published_count += 1

            # A previously published notice omitted by the latest official parse
            # is not proof of closure. Preserve it in the database review queue,
            # but never carry it forward as a verified public listing.
            review_count += sum(
                1 for old_job in previous_items
                if old_job.get('content_hash') and old_job.get('content_hash') not in source_seen_hashes
                and _is_open(old_job, now=now)
            )
            sources.append({
                'key': definition.key, 'name': definition.name,
                'listing_url': definition.listing_url, 'enabled': True,
                'last_sync_completed_at': checked_at,
                'last_successful_sync_at': checked_at,
                'consecutive_failures': 0,
                'last_sync_status': 'success',
                'fetched_count': len(parsed),
                'published_count': published_count,
            })
            successful_sources += 1
        except Exception as exc:
            review_count += len(previous_items)
            sources.append({
                'key': definition.key, 'name': definition.name,
                'listing_url': definition.listing_url, 'enabled': True,
                'last_sync_completed_at': checked_at,
                'last_successful_sync_at': previous_success,
                'consecutive_failures': previous_failures + 1,
                'last_sync_status': 'failed', 'fetched_count': 0,
                'published_count': 0, 'last_error': str(exc)[:300],
            })

    jobs.sort(key=lambda job: (
        not bool(job.get('is_featured')),
        job.get('deadline') or '9999-12-31',
        job.get('title') or '',
    ))
    jobs = _deduplicate_job_identities(jobs)
    _ensure_unique_slugs(jobs)
    return {
        'schema_version': 1,
        'generated_at': checked_at,
        'items': jobs,
        'sources': sources,
        'count': len(jobs),
        'review_count': review_count,
        'successful_sources': successful_sources,
    }

def load_snapshot(path):
    try:return json.loads(path.read_text(encoding='utf-8'))
    except (FileNotFoundError,json.JSONDecodeError,OSError):return None
def write_snapshot(path,snapshot):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main(argv=None):
    parser=argparse.ArgumentParser(description='Refresh the verified public job snapshot.');parser.add_argument('--output',default='frontend/public/data/jobs.json');args=parser.parse_args(argv);output=Path(args.output);snapshot=build_snapshot(load_snapshot(output));write_snapshot(output,snapshot);print(f"Job snapshot ready: {snapshot['count']} verified public, {snapshot['review_count']} held for review, {snapshot['successful_sources']} official source(s) checked.");return 0
if __name__=='__main__':raise SystemExit(main())
