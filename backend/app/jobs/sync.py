import hashlib
import re
import sys
import threading
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlparse

import requests
from sqlalchemy import func, text

from ..models.job import JobNotification, JobSource
from ..utils.database import db
from .sources import SOURCE_BY_KEY, SOURCE_DEFINITIONS, JobItem


ALLOWED_HOSTS = {
    'employmentnews.gov.in', 'www.employmentnews.gov.in',
    'upsc.gov.in', 'www.upsc.gov.in', 'upsconline.nic.in', 'www.upsconline.nic.in',
    'ncs.gov.in', 'www.ncs.gov.in',
}
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
JOB_SYNC_LOCK_ID = 20260831
_background_lock = threading.Lock()


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def validate_official_url(url):
    parsed = urlparse(str(url or ''))
    if parsed.scheme != 'https' or parsed.hostname not in ALLOWED_HOSTS or parsed.username or parsed.password:
        raise ValueError('Job source URL is not on the approved official HTTPS allowlist.')
    return url


def fetch_official_page(url, session=None):
    validate_official_url(url)
    client = session or requests.Session()
    response = client.get(
        url,
        timeout=(8, 25),
        allow_redirects=True,
        stream=True,
        headers={'User-Agent': 'PublicOnlineServiceProvider/1.0 (+independent job-notice index)'},
    )
    response.raise_for_status()
    validate_official_url(response.url)
    content_type = (response.headers.get('Content-Type') or '').lower()
    if content_type and not any(kind in content_type for kind in ('text/html', 'application/xhtml+xml')):
        raise ValueError('Official source returned an unsupported content type.')
    chunks = []
    size = 0
    for chunk in response.iter_content(chunk_size=65536):
        if not chunk:
            continue
        size += len(chunk)
        if size > MAX_RESPONSE_BYTES:
            raise ValueError('Official source response exceeded the safe size limit.')
        chunks.append(chunk)
    encoding = response.encoding or 'utf-8'
    return b''.join(chunks).decode(encoding, errors='replace')


def slugify(value):
    value = re.sub(r'[^a-z0-9]+', '-', str(value or '').lower()).strip('-')
    return value[:250] or 'job-notice'


def item_hash(item):
    normalized = '|'.join(
        re.sub(r'\s+', ' ', str(value or '')).strip().lower()
        for value in (item.title, item.organization, item.deadline, item.location)
    )
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def target_status(item):
    if item.deadline and item.deadline < date.today():
        return 'expired'
    complete = bool(item.title and item.organization and item.official_notice_url and item.deadline)
    return 'published' if complete and item.confidence >= 0.8 else 'needs_review'


def unique_slug(item, content_hash):
    base = slugify(f'{item.organization}-{item.title}')
    return f'{base[:245]}-{content_hash[:8]}'


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


def upsert_item(source, item):
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
        existing = JobNotification(
            source_id=source.id,
            external_id=external_id,
            slug=unique_slug(item, content_hash),
            content_hash=content_hash,
            title=item.title[:500],
            organization=item.organization[:500],
            official_notice_url=item.official_notice_url,
        )
        db.session.add(existing)

    previous_status = existing.status
    existing.content_hash = content_hash
    for field in (
        'title', 'organization', 'job_type', 'appointment_type', 'location', 'qualification',
        'age_limit', 'application_fee', 'vacancies', 'salary', 'summary', 'issue_date',
        'application_start_date', 'deadline', 'official_notice_url', 'application_url', 'confidence',
    ):
        value = getattr(item, field)
        if isinstance(value, str):
            limits = {'title': 500, 'organization': 500, 'official_notice_url': 1200, 'application_url': 1200}
            value = value[:limits.get(field, 600)]
        setattr(existing, field, value)
    proposed = target_status(item)
    if previous_status == 'hidden':
        existing.status = 'hidden'
    elif proposed == 'expired':
        existing.status = 'expired'
    elif previous_status == 'published' and not is_new:
        existing.status = 'published'
    else:
        existing.status = proposed
    if existing.status == 'published' and not existing.published_at:
        existing.published_at = utc_now()
    existing.verification_status = 'official_source_checked'
    existing.last_seen_at = utc_now()
    return existing, is_new, False


def sync_source(source, session=None):
    definition = SOURCE_BY_KEY[source.key]
    source.last_sync_started_at = utc_now()
    source.last_sync_status = 'running'
    source.last_error = None
    db.session.commit()
    try:
        html = fetch_official_page(definition.listing_url, session=session)
        items = definition.parser(html, definition.listing_url)
        published = 0
        duplicates = 0
        for item in items:
            job, _, duplicate = upsert_item(source, item)
            duplicates += int(duplicate)
            published += int(job.status == 'published')
        source.fetched_count = len(items)
        source.published_count = published
        source.last_sync_completed_at = utc_now()
        source.last_sync_status = 'success'
        source.last_error = f'{duplicates} duplicate notice(s) skipped.' if duplicates else None
        db.session.commit()
        return {'source': source.key, 'fetched': len(items), 'published': published, 'duplicates': duplicates, 'status': 'success'}
    except Exception as exc:
        db.session.rollback()
        current = db.session.get(JobSource, source.id)
        current.last_sync_completed_at = utc_now()
        current.last_sync_status = 'failed'
        current.last_error = str(exc)[:1000]
        db.session.commit()
        return {'source': source.key, 'fetched': 0, 'published': 0, 'duplicates': 0, 'status': 'failed', 'error': str(exc)}


def expire_old_jobs():
    expired = JobNotification.query.filter(
        JobNotification.deadline.isnot(None),
        JobNotification.deadline < date.today(),
        JobNotification.status.in_(['published', 'needs_review']),
    ).all()
    for job in expired:
        job.status = 'expired'
    if expired:
        db.session.commit()
    return len(expired)


def sync_all_sources(session=None):
    ensure_job_sources()
    results = []
    for source in JobSource.query.filter_by(enabled=True).order_by(JobSource.id).all():
        if source.key in SOURCE_BY_KEY:
            results.append(sync_source(source, session=session))
    expired = expire_old_jobs()
    return {'results': results, 'expired': expired, 'successful_sources': sum(item['status'] == 'success' for item in results)}


def sync_is_due(hours=20):
    """Return true when a refresh is due and no recent refresh is running."""
    running_cutoff = utc_now() - timedelta(hours=1)
    if JobSource.query.filter(
        JobSource.enabled.is_(True),
        JobSource.last_sync_status == 'running',
        JobSource.last_sync_started_at >= running_cutoff,
    ).count():
        return False
    last_success = db.session.query(func.max(JobSource.last_sync_completed_at)).filter(
        JobSource.enabled.is_(True), JobSource.last_sync_status == 'success',
    ).scalar()
    return last_success is None or last_success < utc_now() - timedelta(hours=hours)


def trigger_background_sync(app):
    """Refresh in a daemon thread; PostgreSQL advisory locking prevents duplicate workers."""
    # Test requests must stay deterministic and must never contact live sources.
    if app.config.get('TESTING'):
        return False
    if not sync_is_due() or not _background_lock.acquire(blocking=False):
        return False

    def run():
        lock_connection = None
        database_lock_acquired = True
        try:
            with app.app_context():
                if db.engine.dialect.name == 'postgresql':
                    lock_connection = db.engine.connect()
                    database_lock_acquired = bool(lock_connection.execute(
                        text('SELECT pg_try_advisory_lock(:lock_id)'), {'lock_id': JOB_SYNC_LOCK_ID},
                    ).scalar())
                if database_lock_acquired and sync_is_due():
                    result = sync_all_sources()
                    app.logger.info('Scheduled job-source refresh completed: %s', result)
        except Exception:
            app.logger.exception('Scheduled job-source refresh failed')
        finally:
            if lock_connection is not None:
                try:
                    if database_lock_acquired:
                        lock_connection.execute(
                            text('SELECT pg_advisory_unlock(:lock_id)'), {'lock_id': JOB_SYNC_LOCK_ID},
                        )
                finally:
                    lock_connection.close()
            with app.app_context():
                db.session.remove()
            _background_lock.release()

    threading.Thread(target=run, name='official-job-refresh', daemon=True).start()
    return True


def main():
    from ..main import create_app
    app = create_app()
    with app.app_context():
        result = sync_all_sources()
        print(result)
        if result['successful_sources'] == 0:
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
