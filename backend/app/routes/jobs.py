from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
import re

from flask import Blueprint, abort, current_app, jsonify, request
from sqlalchemy import and_, or_

from ..models.job import JobNotification, JobSource


bp = Blueprint('jobs', __name__)
_SNAPSHOT_MARKER = Path(__file__).resolve().parents[1] / 'jobs' / 'verified_snapshot.sha256'
_SHA256_RE = re.compile(r'^[0-9a-f]{64}$')


def _deployed_snapshot_sha256():
    try:
        value = _SNAPSHOT_MARKER.read_text(encoding='utf-8').strip().lower()
    except OSError:
        return None
    return value if _SHA256_RE.fullmatch(value) else None


def _india_today():
    return datetime.now(ZoneInfo('Asia/Kolkata')).date()


def _public_query():
    # A published row is public only while its own notice and its source check
    # are fresh. A failed/degraded source must not keep stale records visible.
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    freshness_cutoff = now - timedelta(hours=36)
    return JobNotification.query.filter(
        JobNotification.status == 'published',
        JobNotification.deadline.isnot(None),
        JobNotification.deadline >= (_india_today() - timedelta(days=1)),
        JobNotification.last_seen_at >= freshness_cutoff,
        JobNotification.source.has(and_(
            JobSource.last_sync_status.in_(['success', 'running']),
            JobSource.last_successful_sync_at.isnot(None),
            JobSource.last_successful_sync_at >= freshness_cutoff,
        )),
    )

@bp.get('/')
def list_jobs():
    from ..jobs.sync import trigger_background_sync
    trigger_background_sync(current_app._get_current_object())
    query = _public_query()
    term = (request.args.get('q') or '').strip()
    job_type = (request.args.get('type') or '').strip().lower()
    featured = (request.args.get('featured') or '').strip().lower()
    if term:
        aliases = {'govt': 'government', 'railways': 'railway'}
        tokens = list(dict.fromkeys(
            aliases.get(token, token) for token in re.sub(r'[^a-z0-9]+', ' ', term[:120].lower()).split() if token
        ))
        query = query.filter(and_(*[
            or_(
                JobNotification.title.ilike(f'%{token}%'),
                JobNotification.organization.ilike(f'%{token}%'),
                JobNotification.qualification.ilike(f'%{token}%'),
                JobNotification.location.ilike(f'%{token}%'),
                JobNotification.source.has(or_(
                    JobSource.name.ilike(f'%{token}%'),
                    JobSource.key.ilike(f'%{token}%'),
                )),
            )
            for token in tokens
        ]))
    if job_type in {'government', 'private'}:
        query = query.filter(JobNotification.job_type == job_type)
    if featured in {'1', 'true', 'yes'}:
        query = query.filter(JobNotification.is_featured.is_(True))
    candidates = query.order_by(
        JobNotification.is_featured.desc(),
        JobNotification.deadline.asc(),
        JobNotification.published_at.desc(),
    ).all()
    eligible = [job for job in candidates if job.is_open]
    total = len(eligible)
    try:
        limit = min(100, max(1, int(request.args.get('limit', 30))))
    except (TypeError, ValueError):
        limit = 30
    jobs = eligible[:limit]
    response = jsonify({
        'items': [job.to_dict() for job in jobs],
        'count': len(jobs),
        'total': total,
        'verified_open_count': sum(1 for job in eligible if job.deadline_status() == 'open'),
        'deadline_today_count': sum(1 for job in eligible if job.deadline_status() == 'deadline_today'),
    })
    response.headers['Cache-Control'] = 'public, max-age=300, stale-while-revalidate=600'
    return response


@bp.get('/sources')
def list_sources():
    from ..jobs.sync import trigger_background_sync
    trigger_background_sync(current_app._get_current_object())
    items = []
    for source in JobSource.query.filter_by(enabled=True).order_by(JobSource.name).all():
        data = source.to_dict()
        data.pop('last_error', None)
        items.append(data)
    response = jsonify({'items': items})
    response.headers['Cache-Control'] = 'public, max-age=900, stale-while-revalidate=1800'
    return response


@bp.get('/snapshot-status')
def snapshot_status():
    """Expose only the deployed verified snapshot fingerprint for rollout checks."""
    sha256 = _deployed_snapshot_sha256()
    response = jsonify({'ready': bool(sha256), 'sha256': sha256})
    response.headers['Cache-Control'] = 'no-store'
    return response


@bp.get('/<slug>')
def job_detail(slug):
    job = _public_query().filter_by(slug=slug).first_or_404()
    if not job.is_open:
        abort(404)
    response = jsonify({'job': job.to_dict()})
    response.headers['Cache-Control'] = 'public, max-age=300, stale-while-revalidate=600'
    return response
