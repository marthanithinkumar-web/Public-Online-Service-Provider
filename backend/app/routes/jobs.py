from datetime import date, datetime, time as datetime_time, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from flask import Blueprint, abort, jsonify, request


bp = Blueprint('jobs', __name__)
_REPO_ROOT = Path(__file__).resolve().parents[3]
_SNAPSHOT_PATH = _REPO_ROOT / 'frontend' / 'public' / 'data' / 'jobs.json'
_SNAPSHOT_MARKER = Path(__file__).resolve().parents[1] / 'jobs' / 'verified_snapshot.sha256'
_SHA256_RE = re.compile(r'^[0-9a-f]{64}$')
_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
_MAX_SOURCE_AGE = timedelta(hours=36)
_MAX_FUTURE_CLOCK_SKEW = timedelta(minutes=5)


def _read_snapshot():
    try:
        data = json.loads(_SNAPSHOT_PATH.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {'items': [], 'sources': []}
    if not isinstance(data, dict):
        return {'items': [], 'sources': []}
    return {
        'items': data.get('items') if isinstance(data.get('items'), list) else [],
        'sources': data.get('sources') if isinstance(data.get('sources'), list) else [],
    }


def _deployed_snapshot_sha256():
    try:
        marker = _SNAPSHOT_MARKER.read_text(encoding='utf-8').strip().lower()
        actual = hashlib.sha256(_SNAPSHOT_PATH.read_bytes()).hexdigest()
    except OSError:
        return None
    if not _SHA256_RE.fullmatch(marker) or marker != actual:
        return None
    return marker


def _parse_timestamp(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).strip().replace('Z', '+00:00'))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _is_fresh_timestamp(value, now_utc):
    parsed = _parse_timestamp(value)
    if parsed is None:
        return False
    age = now_utc - parsed
    return -_MAX_FUTURE_CLOCK_SKEW <= age <= _MAX_SOURCE_AGE


def _deadline_state(item, now_utc):
    raw_deadline = str(item.get('deadline') or '').strip()
    if not _DATE_RE.fullmatch(raw_deadline):
        return 'unverified', None, None, None
    try:
        deadline = date.fromisoformat(raw_deadline)
        if deadline.isoformat() != raw_deadline:
            return 'unverified', None, None, None
        timezone_name = str(item.get('deadline_timezone') or 'Asia/Kolkata').strip()
        local = now_utc.astimezone(ZoneInfo(timezone_name))
        raw_cutoff = str(item.get('deadline_cutoff_time') or '').strip()
        cutoff = datetime_time.fromisoformat(raw_cutoff) if raw_cutoff else None
    except (TypeError, ValueError, KeyError):
        return 'unverified', None, None, None

    local_time = local.timetz().replace(tzinfo=None)
    if deadline < local.date():
        return 'closed', timezone_name, cutoff, local_time
    if deadline > local.date():
        return 'open', timezone_name, cutoff, local_time
    if cutoff and local_time >= cutoff:
        return 'closed', timezone_name, cutoff, local_time
    return 'deadline_today', timezone_name, cutoff, local_time


def _public_snapshot_jobs(now=None):
    now_utc = now or datetime.now(timezone.utc)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    now_utc = now_utc.astimezone(timezone.utc)

    jobs = []
    seen_slugs = set()
    for raw in _read_snapshot()['items']:
        if not isinstance(raw, dict) or raw.get('status') != 'published':
            continue
        slug = str(raw.get('slug') or '').strip()
        if not str(raw.get('title') or '').strip() or not slug or slug in seen_slugs:
            continue
        if raw.get('application_status') not in {'open', 'deadline_today'}:
            continue
        if raw.get('verification_status') != 'official_source_checked':
            continue
        notice_url = str(raw.get('official_notice_url') or '').strip()
        application_url = str(raw.get('application_url') or '').strip()
        if not notice_url.startswith('https://') or not application_url.startswith('https://'):
            continue

        source = raw.get('source')
        if not isinstance(source, dict) or str(source.get('last_sync_status') or '').lower() != 'success':
            continue
        if not _is_fresh_timestamp(source.get('last_successful_sync_at'), now_utc):
            continue
        if not _is_fresh_timestamp(raw.get('source_checked_at') or source.get('last_successful_sync_at'), now_utc):
            continue
        if not _is_fresh_timestamp(raw.get('last_seen_at'), now_utc):
            continue

        state, timezone_name, cutoff, local_time = _deadline_state(raw, now_utc)
        if state not in {'open', 'deadline_today'}:
            continue

        item = dict(raw)
        item['source'] = dict(source)
        item['source'].pop('last_error', None)
        item['application_status'] = state
        if state == 'open':
            item['can_apply'] = True
            item['status_label'] = 'Verified open'
        else:
            item['can_apply'] = bool(cutoff and local_time and local_time < cutoff)
            if cutoff:
                item['status_label'] = (
                    f'Deadline today—closes at {cutoff.isoformat(timespec="minutes")} {timezone_name}'
                )
            else:
                item['status_label'] = 'Deadline today—check official portal'
        jobs.append(item)
        seen_slugs.add(slug)

    jobs.sort(
        key=lambda item: _parse_timestamp(item.get('published_at')) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    jobs.sort(key=lambda item: (
        0 if item.get('is_featured') else 1,
        str(item.get('deadline') or '9999-12-31'),
    ))
    return jobs


def _matches_search(item, tokens):
    if not tokens:
        return True
    source = item.get('source') if isinstance(item.get('source'), dict) else {}
    searchable = ' '.join(str(value or '') for value in (
        item.get('title'),
        item.get('organization'),
        item.get('qualification'),
        item.get('location'),
        source.get('name'),
        source.get('key'),
    )).lower()
    return all(token in searchable for token in tokens)


@bp.get('/')
def list_jobs():
    term = (request.args.get('q') or '').strip()[:120]
    aliases = {'govt': 'government', 'railways': 'railway'}
    tokens = list(dict.fromkeys(
        aliases.get(token, token)
        for token in re.sub(r'[^a-z0-9]+', ' ', term.lower()).split()
        if token
    ))
    job_type = (request.args.get('type') or '').strip().lower()
    featured = (request.args.get('featured') or '').strip().lower()
    location = (request.args.get('location') or '').strip()[:120].lower()
    qualification = (request.args.get('qualification') or '').strip()[:120].lower()

    eligible = _public_snapshot_jobs()
    if job_type in {'government', 'private'}:
        eligible = [item for item in eligible if str(item.get('job_type') or '').lower() == job_type]
    if featured in {'1', 'true', 'yes'}:
        eligible = [item for item in eligible if item.get('is_featured') is True]
    if location:
        eligible = [item for item in eligible if location in str(item.get('location') or '').lower()]
    if qualification:
        eligible = [item for item in eligible if qualification in str(item.get('qualification') or '').lower()]
    eligible = [item for item in eligible if _matches_search(item, tokens)]

    total = len(eligible)
    try:
        limit = min(100, max(1, int(request.args.get('limit', 30))))
    except (TypeError, ValueError):
        limit = 30
    page_items = eligible[:limit]
    response = jsonify({
        'items': page_items,
        'count': len(page_items),
        'total': total,
        'verified_open_count': sum(1 for item in eligible if item.get('application_status') == 'open'),
        'deadline_today_count': sum(1 for item in eligible if item.get('application_status') == 'deadline_today'),
    })
    response.headers['Cache-Control'] = 'public, max-age=300, stale-while-revalidate=600'
    return response


@bp.get('/sources')
def list_sources():
    items = []
    for raw in _read_snapshot()['sources']:
        if not isinstance(raw, dict) or raw.get('enabled') is False:
            continue
        item = dict(raw)
        item.pop('last_error', None)
        items.append(item)
    items.sort(key=lambda item: str(item.get('name') or item.get('key') or '').lower())
    response = jsonify({'items': items})
    response.headers['Cache-Control'] = 'public, max-age=900, stale-while-revalidate=1800'
    return response


@bp.get('/snapshot-status')
def snapshot_status():
    """Expose the deployed snapshot fingerprint only when the file matches its marker."""
    sha256 = _deployed_snapshot_sha256()
    response = jsonify({'ready': bool(sha256), 'sha256': sha256})
    response.headers['Cache-Control'] = 'no-store'
    return response


@bp.get('/<slug>')
def job_detail(slug):
    job = next((item for item in _public_snapshot_jobs() if item.get('slug') == slug), None)
    if job is None:
        abort(404)
    response = jsonify({'job': job})
    response.headers['Cache-Control'] = 'public, max-age=300, stale-while-revalidate=600'
    return response
