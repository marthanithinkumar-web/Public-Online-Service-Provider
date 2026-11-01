from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
import re

from flask import Blueprint, current_app, jsonify, request
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
    # Public listings must have a valid, current deadline. Undated records may
    # remain in storage for review, but must not be advertised as open.
    return JobNotification.query.filter(
        JobNotification.status == 'published',
        JobNotification.deadline.isnot(None),
        JobNotification.deadline >= _india_today(),
    )


@bp.get('/')
def list_jobs():
    from ..jobs.sync import trigger_background_sync
    trigger_background_sync(current_app._get_current_object())
    query = _public_query()
    term = (request.args.get('q') or '').strip()
    job_type = (request.args.get('type') or request.args.get('job_type') or '').strip().lower()
    featured = (request.args.get('featured') or '').strip().lower()
    location = (request.args.get('location') or request.args.get('state') or '').strip()[:120]
    qualification = (request.args.get('qualification') or request.args.get('education') or '').strip()[:120]
    deadline_filter = (request.args.get('deadline') or '').strip().lower()
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
    if location:
        query = query.filter(JobNotification.location.ilike(f'%{location}%'))
    if qualification:
        query = query.filter(JobNotification.qualification.ilike(f'%{qualification}%'))
    if featured in {'1', 'true', 'yes'}:
        query = query.filter(JobNotification.is_featured.is_(True))
    if deadline_filter == 'closing_soon':
        query = query.filter(JobNotification.deadline <= _india_today() + timedelta(days=7))
    elif deadline_filter == 'this_month':
        today = _india_today()
        next_month = date(today.year + (today.month == 12), 1 if today.month == 12 else today.month + 1, 1)
        query = query.filter(JobNotification.deadline < next_month)
    total = query.count()
    try:
        limit = min(100, max(1, int(request.args.get('limit', 30))))
    except (TypeError, ValueError):
        limit = 30
    try:
        page = max(1, int(request.args.get('page', 1)))
    except (TypeError, ValueError):
        page = 1
    sort = (request.args.get('sort') or 'deadline_asc').strip().lower()
    if sort == 'deadline_desc':
        ordering = (JobNotification.deadline.desc(), JobNotification.is_featured.desc())
    elif sort == 'newest':
        ordering = (JobNotification.published_at.desc(), JobNotification.deadline.asc())
    else:
        ordering = (JobNotification.is_featured.desc(), JobNotification.deadline.asc(), JobNotification.published_at.desc())
    jobs = query.order_by(*ordering).offset((page - 1) * limit).limit(limit).all()
    response = jsonify({'items': [job.to_dict() for job in jobs], 'count': len(jobs), 'total': total, 'page': page, 'limit': limit})
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
    response = jsonify({'job': job.to_dict()})
    response.headers['Cache-Control'] = 'public, max-age=300, stale-while-revalidate=600'
    return response
