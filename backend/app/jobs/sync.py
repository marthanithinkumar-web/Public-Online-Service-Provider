import sys
import threading
from datetime import date, datetime, timedelta, timezone

import requests
from sqlalchemy import text

from ..models.job import JobNotification, JobSource
from ..utils.database import db
from .official_fetch import OfficialSourceUnavailable, fetch_official_page, validate_official_url
from .rules import item_hash, target_status, unique_slug
from .sources import SOURCE_BY_KEY, SOURCE_DEFINITIONS, JobItem


JOB_SYNC_LOCK_ID = 20260831
_background_lock = threading.Lock()


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def ensure_job_sources():
    changed = False
    for definition in SOURCE_DEFINITIONS:
        source = JobSource.query.filter_by(key=definition.key).first()
        if source is None:
            db.session.add(JobSource(key=definition.key, name=definition.name, listing_url=definition.listing_url))
            changed = True
        else:
            if source.name != definition.name or source.listing_url != definition.listing_url:
                source.name = definition.name
                source.listing_url = definition.listing_url
                changed = True
    if changed:
        db.session.commit()
    return changed


def upsert_item(source, item, allow_missing_deadline=False, missing_deadline_max_age_days=45):
    validate_official_url(item.official_notice_url)
    if item.application_url:
        validate_official_url(item.application_url)
    content_hash = item_hash(item)
    external_id = str(item.external_id or content_hash)[:300]
    existing = JobNotification.query.filter_by(source_id=source.id, external_id=external_id).first()
    duplicate = JobNotification.query.filter_by(content_hash=content_hash).first()
    if duplicate and (existing is None or duplicate.id != existing.id):
        duplicate.last_seen_at = utc_now()
        return duplicate, False, True
    is_new = existing is None
    if is_new:
        existing = JobNotification(source_id=source.id, external_id=external_id, slug=unique_slug(item, content_hash), content_hash=content_hash, title=item.title[:500], organization=item.organization[:500], official_notice_url=item.official_notice_url)
        db.session.add(existing)
    previous_status = existing.status
    existing.content_hash = content_hash
    for field in ('title', 'organization', 'job_type', 'appointment_type', 'location', 'qualification', 'age_limit', 'application_fee', 'vacancies', 'salary', 'summary', 'issue_date', 'application_start_date', 'deadline', 'official_notice_url', 'application_url', 'confidence'):
        value = getattr(item, field)
        if isinstance(value, str):
            limits = {'title': 500, 'organization': 500, 'official_notice_url': 1200, 'application_url': 1200}
            value = value[:limits.get(field, 600)]
        setattr(existing, field, value)
    proposed = target_status(item, allow_missing_deadline=allow_missing_deadline, missing_deadline_max_age_days=missing_deadline_max_age_days)
    if previous_status == 'hidden': existing.status = 'hidden'
    elif proposed == 'expired': existing.status = 'expired'
    elif previous_status == 'published' and not is_new: existing.status = 'published'
    else: existing.status = proposed
    if existing.status == 'published' and not existing.published_at: existing.published_at = utc_now()
    existing.verification_status = 'official_source_checked'
    existing.last_seen_at = utc_now()
    return existing, is_new, False


def _has_verified_notices(source_id):
    return JobNotification.query.filter(JobNotification.source_id == source_id, JobNotification.status.in_(['published', 'expired', 'hidden'])).count() > 0


def _record_source_failure(source_id, message, detail=''):
    """Preserve verified data and report temporary upstream trouble as degraded."""
    db.session.rollback()
    current = db.session.get(JobSource, source_id)
    current.last_sync_completed_at = utc_now()
    has_verified = _has_verified_notices(source_id)
    current.last_sync_status = 'degraded' if has_verified else 'failed'
    current.last_error = message
    db.session.commit()
    return {'source': current.key, 'fetched': 0, 'published': int(current.published_count or 0), 'duplicates': 0, 'status': current.last_sync_status, 'error': detail}


def sync_source(source, session=None):
    definition = SOURCE_BY_KEY[source.key]
    source.last_sync_started_at = utc_now(); source.last_sync_status = 'running'; source.last_error = None; db.session.commit()
    try:
        html = fetch_official_page(definition.listing_url, session=session)
        items = definition.parser(html, definition.listing_url)
        published = 0; duplicates = 0
        for item in items:
            job, _, duplicate = upsert_item(source, item, allow_missing_deadline=definition.allow_missing_deadline, missing_deadline_max_age_days=definition.missing_deadline_max_age_days)
            duplicates += int(duplicate); published += int(job.status == 'published')
        source.fetched_count = len(items); source.published_count = published; source.last_sync_completed_at = utc_now(); source.last_sync_status = 'success'; source.last_error = f'{duplicates} duplicate notice(s) skipped.' if duplicates else None
        db.session.commit()
        return {'source': source.key, 'fetched': len(items), 'published': published, 'duplicates': duplicates, 'status': 'success'}
    except OfficialSourceUnavailable as exc:
        return _record_source_failure(source.id, 'Official source is temporarily unavailable. Last verified job notices remain available and synchronization will retry automatically.', str(exc))
    except requests.RequestException as exc:
        return _record_source_failure(source.id, 'Official source could not be reached reliably. Last verified job notices remain available and synchronization will retry automatically.', str(exc))
    except Exception as exc:
        db.session.rollback()
        current = db.session.get(JobSource, source.id)
        current.last_sync_completed_at = utc_now()
        detail = str(exc).strip()
        if _has_verified_notices(source.id):
            current.last_sync_status = 'degraded'
            current.last_error = 'The latest official-source check could not be processed. Last verified job notices remain available while the next check retries.'
        else:
            current.last_sync_status = 'failed'
            current.last_error = detail[:350] if detail else 'The official source could not be processed. Review the source configuration.'
        db.session.commit()
        return {'source': source.key, 'fetched': 0, 'published': int(current.published_count or 0), 'duplicates': 0, 'status': current.last_sync_status, 'error': detail}


def expire_old_jobs():
    expired = JobNotification.query.filter(JobNotification.deadline.isnot(None), JobNotification.deadline < date.today(), JobNotification.status.in_(['published', 'needs_review'])).all()
    for job in expired: job.status = 'expired'
    undated_cutoff = utc_now() - timedelta(days=60)
    stale_undated = JobNotification.query.filter(JobNotification.deadline.is_(None), JobNotification.last_seen_at < undated_cutoff, JobNotification.status.in_(['published', 'needs_review'])).all()
    for job in stale_undated: job.status = 'expired'
    if expired or stale_undated: db.session.commit()
    return len(expired) + len(stale_undated)


def sync_all_sources(session=None):
    ensure_job_sources(); results = []
    for source in JobSource.query.filter_by(enabled=True).order_by(JobSource.id).all():
        if source.key in SOURCE_BY_KEY: results.append(sync_source(source, session=session))
    expired = expire_old_jobs()
    return {'results': results, 'expired': expired, 'successful_sources': sum(item['status'] == 'success' for item in results), 'degraded_sources': sum(item['status'] == 'degraded' for item in results)}


def sync_is_due(hours=20):
    running_cutoff = utc_now() - timedelta(hours=1)
    if JobSource.query.filter(JobSource.enabled.is_(True), JobSource.last_sync_status == 'running', JobSource.last_sync_started_at >= running_cutoff).count():
        return False

    # Production deliberately skips the broad database bootstrap at web-process
    # startup. Register any newly configured official source here instead. The
    # first request that notices the registry change immediately schedules a
    # refresh, while preserving the existing lightweight startup behavior.
    if ensure_job_sources():
        return True

    configured_keys = {definition.key for definition in SOURCE_DEFINITIONS}
    stored_sources = {source.key: source for source in JobSource.query.all()}
    enabled_sources = [stored_sources[key] for key in configured_keys if stored_sources[key].enabled]
    completed_sources = [source for source in enabled_sources if source.last_sync_completed_at is not None]
    if not completed_sources:
        return True

    # Sources that have synchronized before must remain fresh. Never-run rows
    # are tolerated during the initial bootstrap, but a newly registered source
    # above always forces a refresh once so it can be populated.
    stale_cutoff = utc_now() - timedelta(hours=hours)
    return any(source.last_sync_completed_at < stale_cutoff for source in completed_sources)


def trigger_background_sync(app):
    if app.config.get('TESTING'): return False
    if not sync_is_due() or not _background_lock.acquire(blocking=False): return False
    def run():
        lock_connection = None; database_lock_acquired = True
        try:
            with app.app_context():
                if db.engine.dialect.name == 'postgresql':
                    lock_connection = db.engine.connect(); database_lock_acquired = bool(lock_connection.execute(text('SELECT pg_try_advisory_lock(:lock_id)'), {'lock_id': JOB_SYNC_LOCK_ID}).scalar())
                if database_lock_acquired and sync_is_due(): app.logger.info('Scheduled job-source refresh completed: %s', sync_all_sources())
        except Exception: app.logger.exception('Scheduled job-source refresh failed')
        finally:
            if lock_connection is not None:
                try:
                    if database_lock_acquired: lock_connection.execute(text('SELECT pg_advisory_unlock(:lock_id)'), {'lock_id': JOB_SYNC_LOCK_ID})
                finally: lock_connection.close()
            with app.app_context(): db.session.remove()
            _background_lock.release()
    threading.Thread(target=run, name='official-job-refresh', daemon=True).start(); return True


def main():
    from ..main import create_app
    app = create_app()
    with app.app_context():
        result = sync_all_sources(); print(result)
        if result['successful_sources'] + result.get('degraded_sources', 0) == 0: return 1
    return 0


if __name__ == '__main__': sys.exit(main())
