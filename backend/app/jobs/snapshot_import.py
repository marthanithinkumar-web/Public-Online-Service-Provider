"""Import the verified public job snapshot into the database.

The GitHub refresh workflow already validates the snapshot against the strict
official-source registry. Render runs this importer during startup so the
DB-backed API cannot lag behind the verified static feed just because an
upstream career site is temporarily unreachable from Render.
"""

import argparse
import json
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import or_, text

from ..models.job import JobNotification, JobSource
from ..utils.database import db
from .official_fetch import validate_official_url
from .sources import SOURCE_BY_KEY, SOURCE_DEFINITIONS


# Render can start more than one instance during a deploy. Those instances
# share the same production database, so importing the same snapshot in
# parallel can deadlock while both transactions update job_notifications.
# A transaction-scoped PostgreSQL advisory lock makes snapshot imports
# mutually exclusive without affecting SQLite/local test environments.
_SNAPSHOT_IMPORT_LOCK_ID = 728_173_401


def _acquire_snapshot_import_lock():
    bind = db.session.get_bind()
    if bind.dialect.name == 'postgresql':
        db.session.execute(
            text('SELECT pg_advisory_xact_lock(:lock_id)'),
            {'lock_id': _SNAPSHOT_IMPORT_LOCK_ID},
        )


def _parse_date(value):
    if not value:
        return None
    return date.fromisoformat(str(value)[:10])


def _parse_datetime(value):
    if not value:
        return None
    return datetime.fromisoformat(str(value).replace('Z', '+00:00')).replace(tzinfo=None)


def _load_snapshot(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('schema_version') != 1:
        raise ValueError('Unsupported verified job snapshot schema.')
    items = data.get('items')
    sources = data.get('sources')
    if not isinstance(items, list) or not isinstance(sources, list):
        raise ValueError('Verified job snapshot must contain items and sources lists.')
    if int(data.get('count', len(items))) != len(items):
        raise ValueError('Verified job snapshot count does not match item count.')
    return data


def _retired_slug(slug, job_id):
    suffix = f'--retired-{job_id}'
    return f"{str(slug)[:320 - len(suffix)]}{suffix}"


def _retired_external_id(external_id, job_id):
    if not external_id:
        return None
    prefix = f'retired-{job_id}-'
    return f"{prefix}{str(external_id)[:300 - len(prefix)]}"


def import_verified_snapshot(path):
    data = _load_snapshot(path)
    _acquire_snapshot_import_lock()

    # Validate every final identity before mutating the database. The snapshot
    # generator already de-duplicates these, but enforcing uniqueness here
    # prevents an importer bug from silently collapsing two public records.
    normalized_items = []
    seen_hashes = set()
    seen_slugs = set()
    for item in data['items']:
        digest = str(item.get('content_hash') or '').strip()
        slug = str(item.get('slug') or '').strip()[:320]
        source_data = item.get('source') or {}
        source_key = source_data.get('key')
        if len(digest) != 64 or not slug or source_key not in SOURCE_BY_KEY:
            raise ValueError('Verified snapshot contains an invalid job identity or source.')
        if digest in seen_hashes:
            raise ValueError(f'Verified snapshot contains duplicate content hash: {digest}')
        if slug in seen_slugs:
            raise ValueError(f'Verified snapshot contains duplicate slug: {slug}')
        validate_official_url(item.get('official_notice_url'))
        if item.get('application_url'):
            validate_official_url(item.get('application_url'))
        seen_hashes.add(digest)
        seen_slugs.add(slug)
        normalized_items.append((item, digest, slug, source_key))

    snapshot_sources = {item.get('key'): item for item in data['sources'] if item.get('key')}
    configured_keys = {definition.key for definition in SOURCE_DEFINITIONS}
    unknown = set(snapshot_sources) - configured_keys
    if unknown:
        raise ValueError(f'Verified snapshot contains unknown source(s): {sorted(unknown)}')

    stored_sources = {source.key: source for source in JobSource.query.all()}
    for definition in SOURCE_DEFINITIONS:
        source = stored_sources.get(definition.key)
        if source is None:
            source = JobSource(
                key=definition.key,
                name=definition.name,
                listing_url=definition.listing_url,
                enabled=True,
            )
            db.session.add(source)
            db.session.flush()
            stored_sources[definition.key] = source
        else:
            source.name = definition.name
            source.listing_url = definition.listing_url
            source.enabled = True

        metadata = snapshot_sources.get(definition.key) or {}
        source.last_sync_completed_at = _parse_datetime(metadata.get('last_sync_completed_at'))
        source.last_sync_status = metadata.get('last_sync_status') or 'not_run'
        source.fetched_count = int(metadata.get('fetched_count') or 0)
        source.published_count = int(metadata.get('published_count') or 0)
        source.last_error = metadata.get('last_error') or None

    # Retired source rows must not keep appearing as enabled production sources.
    for key, source in stored_sources.items():
        if key not in configured_keys:
            source.enabled = False

    # Freeze the original identity map before changing any JobNotification.
    # Querying by hash/slug inside the mutation loop lets an earlier update be
    # discovered by a later item after SQLAlchemy autoflushes, which can reuse
    # one row for two snapshot items and reduce an N-item snapshot to N-1 rows.
    existing_jobs = JobNotification.query.all()
    by_hash = {job.content_hash: job for job in existing_jobs}
    by_slug = {job.slug: job for job in existing_jobs}
    by_source_external = {
        (job.source_id, job.external_id): job
        for job in existing_jobs
        if job.external_id
    }

    assignments = [None] * len(normalized_items)
    claimed_ids = set()

    # Content hash is the strongest stable identity, so claim all hash matches
    # before considering slug fallback. Each existing row can be used once.
    for index, (_, digest, _, _) in enumerate(normalized_items):
        job = by_hash.get(digest)
        if job is not None and job.id not in claimed_ids:
            assignments[index] = job
            claimed_ids.add(job.id)

    # Slug fallback preserves an existing row only when it was not already
    # claimed by another snapshot item's content hash.
    for index, (_, _, slug, _) in enumerate(normalized_items):
        if assignments[index] is not None:
            continue
        job = by_slug.get(slug)
        if job is not None and job.id not in claimed_ids:
            assignments[index] = job
            claimed_ids.add(job.id)

    # Identify pre-existing unique-key owners that would block the final active
    # identities. Move only those conflicting keys aside before applying final
    # values, which also safely handles slug swaps between two existing rows.
    conflicting_slug_jobs = set()
    conflicting_external_jobs = set()
    for index, (_, digest, slug, source_key) in enumerate(normalized_items):
        assigned = assignments[index]
        slug_owner = by_slug.get(slug)
        if slug_owner is not None and slug_owner is not assigned:
            conflicting_slug_jobs.add(slug_owner)

        source = stored_sources[source_key]
        external_owner = by_source_external.get((source.id, digest[:300]))
        if external_owner is not None and external_owner is not assigned:
            conflicting_external_jobs.add(external_owner)

    for job in conflicting_slug_jobs:
        job.slug = _retired_slug(job.slug, job.id)
        job.status = 'expired'
    for job in conflicting_external_jobs:
        job.external_id = _retired_external_id(job.external_id, job.id)
        job.status = 'expired'

    if conflicting_slug_jobs or conflicting_external_jobs:
        db.session.flush()

    active_jobs = []
    for index, (item, digest, slug, source_key) in enumerate(normalized_items):
        source = stored_sources[source_key]
        job = assignments[index]
        if job is None:
            job = JobNotification(
                source_id=source.id,
                external_id=digest[:300],
                slug=slug,
                content_hash=digest,
                title=str(item['title'])[:500],
                organization=str(item['organization'])[:500],
                official_notice_url=str(item['official_notice_url'])[:1200],
            )
            db.session.add(job)

        job.source_id = source.id
        job.external_id = digest[:300]
        job.slug = slug
        job.content_hash = digest
        job.title = str(item['title'])[:500]
        job.organization = str(item['organization'])[:500]
        job.job_type = item.get('job_type') if item.get('job_type') in {'government', 'private'} else 'government'
        job.appointment_type = item.get('appointment_type')
        job.location = item.get('location')
        job.qualification = item.get('qualification')
        job.age_limit = item.get('age_limit')
        job.application_fee = item.get('application_fee')
        job.vacancies = item.get('vacancies')
        job.salary = item.get('salary')
        job.summary = item.get('summary')
        job.issue_date = _parse_date(item.get('issue_date'))
        job.application_start_date = _parse_date(item.get('application_start_date'))
        job.deadline = _parse_date(item.get('deadline'))
        job.official_notice_url = str(item['official_notice_url'])[:1200]
        job.application_url = str(item['application_url'])[:1200] if item.get('application_url') else None
        job.status = 'published'
        job.verification_status = 'official_source_checked'
        job.confidence = float(item.get('confidence') or 0)
        job.is_featured = bool(item.get('is_featured', False))
        first_seen = _parse_datetime(item.get('first_seen_at'))
        last_seen = _parse_datetime(item.get('last_seen_at'))
        published_at = _parse_datetime(item.get('published_at'))
        if first_seen:
            job.first_seen_at = first_seen
        if last_seen:
            job.last_seen_at = last_seen
        if published_at:
            job.published_at = published_at
        active_jobs.append(job)

    # The validated snapshot is the exact active public set. Expire any older
    # row that was not selected one-to-one for a current snapshot item.
    active_existing_ids = {job.id for job in active_jobs if job.id is not None}
    for job in existing_jobs:
        if job.id not in active_existing_ids and job.status in {'published', 'needs_review'}:
            job.status = 'expired'

    # Flush before commit so uniqueness or identity-count failures roll back the
    # whole import instead of leaving a partially accepted production snapshot.
    db.session.flush()
    published_total = JobNotification.query.filter(JobNotification.status == 'published').count()
    expected = len(data['items'])
    if published_total != expected:
        db.session.rollback()
        raise RuntimeError(f'Imported production job count mismatch: got {published_total}, expected {expected}.')

    active_total = JobNotification.query.filter(
        JobNotification.status == 'published',
        or_(JobNotification.deadline.is_(None), JobNotification.deadline >= date.today()),
    ).count()
    if active_total != expected:
        db.session.rollback()
        raise RuntimeError(f'Imported active production job count mismatch: got {active_total}, expected {expected}.')

    db.session.commit()
    return {'imported': expected, 'active_total': active_total, 'sources': len(configured_keys)}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Import the verified public job snapshot into the database.')
    parser.add_argument('--path', default='../frontend/public/data/jobs.json')
    args = parser.parse_args(argv)

    from ..main import create_app
    app = create_app()
    with app.app_context():
        result = import_verified_snapshot(args.path)
        print(
            f"Verified job snapshot imported: {result['active_total']} active published job(s), "
            f"{result['sources']} configured source(s)."
        )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
