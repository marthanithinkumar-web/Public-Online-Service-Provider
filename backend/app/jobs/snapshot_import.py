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

from sqlalchemy import or_

from ..models.job import JobNotification, JobSource
from ..utils.database import db
from .official_fetch import validate_official_url
from .sources import SOURCE_BY_KEY, SOURCE_DEFINITIONS


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


def import_verified_snapshot(path):
    data = _load_snapshot(path)
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

    seen_hashes = set()
    for item in data['items']:
        digest = str(item.get('content_hash') or '').strip()
        source_data = item.get('source') or {}
        source_key = source_data.get('key')
        if len(digest) != 64 or source_key not in SOURCE_BY_KEY:
            raise ValueError('Verified snapshot contains an invalid job identity or source.')
        validate_official_url(item.get('official_notice_url'))
        if item.get('application_url'):
            validate_official_url(item.get('application_url'))

        source = stored_sources[source_key]
        job = JobNotification.query.filter_by(content_hash=digest).first()
        if job is None and item.get('slug'):
            job = JobNotification.query.filter_by(slug=item['slug']).first()
        if job is None:
            job = JobNotification(
                source_id=source.id,
                external_id=digest[:300],
                slug=str(item['slug'])[:320],
                content_hash=digest,
                title=str(item['title'])[:500],
                organization=str(item['organization'])[:500],
                official_notice_url=str(item['official_notice_url'])[:1200],
            )
            db.session.add(job)

        job.source_id = source.id
        job.external_id = digest[:300]
        job.slug = str(item['slug'])[:320]
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
        seen_hashes.add(digest)

    # The validated snapshot is the exact active public set. Retire older rows
    # omitted from it instead of leaving stale jobs visible indefinitely.
    stale_query = JobNotification.query.filter(JobNotification.status.in_(['published', 'needs_review']))
    if seen_hashes:
        stale_query = stale_query.filter(~JobNotification.content_hash.in_(seen_hashes))
    for job in stale_query.all():
        job.status = 'expired'

    db.session.commit()

    active_total = JobNotification.query.filter(
        JobNotification.status == 'published',
        or_(JobNotification.deadline.is_(None), JobNotification.deadline >= date.today()),
    ).count()
    expected = len(data['items'])
    if active_total != expected:
        raise RuntimeError(f'Imported production job count mismatch: got {active_total}, expected {expected}.')
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
