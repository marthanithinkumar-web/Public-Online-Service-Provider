from datetime import date

from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from ..models.job import JobNotification, JobSource


bp = Blueprint('jobs', __name__)


def _public_query():
    return JobNotification.query.filter(
        JobNotification.status == 'published',
        or_(JobNotification.deadline.is_(None), JobNotification.deadline >= date.today()),
    )


@bp.get('/')
def list_jobs():
    query = _public_query()
    term = (request.args.get('q') or '').strip()
    job_type = (request.args.get('type') or '').strip().lower()
    featured = (request.args.get('featured') or '').strip().lower()
    if term:
        pattern = f'%{term[:120]}%'
        query = query.filter(or_(
            JobNotification.title.ilike(pattern),
            JobNotification.organization.ilike(pattern),
            JobNotification.qualification.ilike(pattern),
            JobNotification.location.ilike(pattern),
        ))
    if job_type in {'government', 'private'}:
        query = query.filter(JobNotification.job_type == job_type)
    if featured in {'1', 'true', 'yes'}:
        query = query.filter(JobNotification.is_featured.is_(True))
    try:
        limit = min(100, max(1, int(request.args.get('limit', 30))))
    except (TypeError, ValueError):
        limit = 30
    jobs = query.order_by(
        JobNotification.is_featured.desc(),
        JobNotification.deadline.asc(),
        JobNotification.published_at.desc(),
    ).limit(limit).all()
    response = jsonify({'items': [job.to_dict() for job in jobs], 'count': len(jobs)})
    response.headers['Cache-Control'] = 'public, max-age=300, stale-while-revalidate=600'
    return response


@bp.get('/sources')
def list_sources():
    items = []
    for source in JobSource.query.filter_by(enabled=True).order_by(JobSource.name).all():
        data = source.to_dict()
        data.pop('last_error', None)
        items.append(data)
    response = jsonify({'items': items})
    response.headers['Cache-Control'] = 'public, max-age=900, stale-while-revalidate=1800'
    return response


@bp.get('/<slug>')
def job_detail(slug):
    job = _public_query().filter_by(slug=slug).first_or_404()
    response = jsonify({'job': job.to_dict()})
    response.headers['Cache-Control'] = 'public, max-age=300, stale-while-revalidate=600'
    return response
