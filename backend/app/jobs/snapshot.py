"""Build a public, database-independent snapshot of verified job notices.

The snapshot keeps public job search useful during a free Render cold start or
backend deployment. It applies the same allowlist and publishing threshold as
the database-backed feed and never promotes an uncertain notice.
"""

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

from .official_fetch import fetch_official_page, validate_official_url
from .rules import item_hash, target_status, unique_slug
from .sources import SOURCE_DEFINITIONS


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0)


def _iso(value):
    return value.isoformat() if value else None


def _is_open(job, today, now=None):
    raw = job.get('deadline')
    if not raw:
        last_seen = job.get('last_seen_at')
        if not last_seen:
            return False
        try:
            seen = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
            current = now or datetime.now(timezone.utc)
            if seen.tzinfo is None:
                seen = seen.replace(tzinfo=timezone.utc)
            return (current - seen).days <= 3
        except (TypeError, ValueError):
            return False
    try:
        return date.fromisoformat(raw) >= today
    except (TypeError, ValueError):
        return False


def _safe_previous(existing):
    if not isinstance(existing, dict):
        return {'items': [], 'sources': []}
    items = existing.get('items') if isinstance(existing.get('items'), list) else []
    sources = existing.get('sources') if isinstance(existing.get('sources'), list) else []
    return {'items': items, 'sources': sources}


def _serialize_item(item, definition, checked_at, previous=None):
    validate_official_url(item.official_notice_url)
    if item.application_url:
        validate_official_url(item.application_url)
    content_hash = item_hash(item)
    previous = previous or {}
    source = {
        'key': definition.key,
        'name': definition.name,
        'listing_url': definition.listing_url,
        'last_sync_completed_at': checked_at,
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
        'deadline': _iso(item.deadline),
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


def build_snapshot(existing=None, session=None, now=None):
    now = now or utc_now()
    checked_at = now.isoformat().replace('+00:00', 'Z')
    today = now.date()
    previous = _safe_previous(existing)
    previous_jobs = previous['items']
    previous_by_hash = {
        job.get('content_hash'): job for job in previous_jobs
        if isinstance(job, dict) and job.get('content_hash')
    }
    previous_by_source = {}
    for job in previous_jobs:
        if not isinstance(job, dict):
            continue
        source_key = (job.get('source') or {}).get('key')
        if source_key:
            previous_by_source.setdefault(source_key, []).append(job)

    jobs = []
    sources = []
    seen_hashes = set()
    successful_sources = 0
    review_count = 0

    for definition in SOURCE_DEFINITIONS:
        source_jobs = []
        try:
            html = fetch_official_page(definition.listing_url, session=session)
            parsed = definition.parser(html, definition.listing_url)
            published_count = 0
            for item in parsed:
                status = target_status(
                    item,
                    today=today,
                    allow_missing_deadline=definition.allow_missing_deadline,
                    missing_deadline_max_age_days=definition.missing_deadline_max_age_days,
                )
                if status != 'published':
                    review_count += int(status == 'needs_review')
                    continue
                digest = item_hash(item)
                if digest in seen_hashes:
                    continue
                serialized = _serialize_item(item, definition, checked_at, previous_by_hash.get(digest))
                seen_hashes.add(digest)
                source_jobs.append(serialized)
                published_count += 1

            # Official listings can rotate older open notices off their first
            # page. Keep a previously verified notice until its stated closing
            # date instead of making it disappear early.
            for old_job in previous_by_source.get(definition.key, []):
                digest = old_job.get('content_hash')
                if digest and digest not in seen_hashes and _is_open(old_job, today, now=now):
                    carried = dict(old_job)
                    carried['last_seen_at'] = checked_at
                    source_data = dict(carried.get('source') or {})
                    source_data.update({
                        'key': definition.key,
                        'name': definition.name,
                        'listing_url': definition.listing_url,
                        'last_sync_completed_at': checked_at,
                        'last_sync_status': 'success',
                    })
                    carried['source'] = source_data
                    source_jobs.append(carried)
                    seen_hashes.add(digest)
            sources.append({
                'key': definition.key,
                'name': definition.name,
                'listing_url': definition.listing_url,
                'enabled': True,
                'last_sync_completed_at': checked_at,
                'last_sync_status': 'success',
                'fetched_count': len(parsed),
                'published_count': published_count,
            })
            successful_sources += 1
        except Exception as exc:
            # A temporary failure at one official portal must not erase other
            # verified, still-open notices from the public feed.
            for old_job in previous_by_source.get(definition.key, []):
                digest = old_job.get('content_hash')
                if digest and digest not in seen_hashes and _is_open(old_job, today, now=now):
                    jobs.append(old_job)
                    seen_hashes.add(digest)
            sources.append({
                'key': definition.key,
                'name': definition.name,
                'listing_url': definition.listing_url,
                'enabled': True,
                'last_sync_completed_at': checked_at,
                'last_sync_status': 'failed',
                'fetched_count': 0,
                'published_count': 0,
                'last_error': str(exc)[:300],
            })
        jobs.extend(source_jobs)

    jobs.sort(key=lambda job: (
        not bool(job.get('is_featured')),
        job.get('deadline') or '9999-12-31',
        job.get('title') or '',
    ))
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
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def write_snapshot(path, snapshot):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Refresh the verified public job snapshot.')
    parser.add_argument('--output', default='frontend/public/data/jobs.json')
    args = parser.parse_args(argv)
    output = Path(args.output)
    snapshot = build_snapshot(load_snapshot(output))
    write_snapshot(output, snapshot)
    print(
        f"Job snapshot ready: {snapshot['count']} published, "
        f"{snapshot['review_count']} held for review, "
        f"{snapshot['successful_sources']} official source(s) checked."
    )
    return 0 if snapshot['successful_sources'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
