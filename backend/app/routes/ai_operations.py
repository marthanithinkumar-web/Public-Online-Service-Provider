import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from flask import Blueprint, jsonify, request

from ..models.job import JobNotification, JobSource
from ..utils.database import db
from ..utils.readiness import production_readiness
from .admin import _require_admin

bp = Blueprint('ai_operations', __name__)

SCHOLARSHIP_SNAPSHOT = Path(__file__).resolve().parents[1] / 'scholarships' / 'data' / 'scholarships.json'

SYSTEM_PROMPT = """You are POSP AI Operations, an internal operations assistant for Public Online Service Provider.
You help an authorized administrator monitor the website, jobs, scholarships, source health, deployment/runtime readiness,
SEO-related operational checks, and safe maintenance tasks.

Rules:
- Use only the supplied POSP operational context. Never invent a check result.
- Clearly distinguish healthy, warning, failed, stale, and unknown.
- Jobs and scholarships must remain based on approved/official sources already configured by POSP.
- Never claim to have changed production unless the context says an action succeeded.
- Do not expose credentials, tokens, private client data, payment secrets, or internal security secrets.
- For risky changes (security settings, payments, database migrations, deleting content, publishing uncertain notices),
  recommend admin review instead of pretending to execute them.
- Be concise and action-oriented. When something is wrong, explain the concrete next step.
"""


def _load_scholarship_snapshot():
    try:
        data = json.loads(SCHOLARSHIP_SNAPSHOT.read_text(encoding='utf-8'))
        health = (data.get('discovery') or {}).get('source_health') or {}
        return {
            'available': True,
            'generated_at': data.get('generated_at'),
            'count': int(data.get('count') or 0),
            'official_count': int(data.get('official_count') or 0),
            'private_count': int(data.get('private_count') or 0),
            'stale_source_count': int(data.get('stale_source_count') or 0),
            'discovery_mode': (data.get('discovery') or {}).get('mode'),
            'source_health': [
                {
                    'key': key,
                    'source_name': value.get('source_name'),
                    'ok': bool(value.get('ok')),
                    'count': int(value.get('count') or 0),
                    'error': value.get('error'),
                    'checked_at': value.get('checked_at'),
                }
                for key, value in sorted(health.items())
            ],
        }
    except (OSError, ValueError, TypeError) as exc:
        return {'available': False, 'error': f'{type(exc).__name__}: {str(exc)[:160]}'}


def _build_context():
    jobs = JobNotification.query
    job_sources = JobSource.query.order_by(JobSource.name).all()
    scholarship = _load_scholarship_snapshot()
    readiness = production_readiness()
    return {
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'runtime': {
            'database': True,
            'production_readiness': readiness,
        },
        'jobs': {
            'published': jobs.filter_by(status='published').count(),
            'needs_review': jobs.filter_by(status='needs_review').count(),
            'expired': jobs.filter_by(status='expired').count(),
            'hidden': jobs.filter_by(status='hidden').count(),
            'sources': [source.to_dict() for source in job_sources],
        },
        'scholarships': scholarship,
    }


def _extract_response_text(payload):
    for item in payload.get('output', []):
        for content in item.get('content', []) or []:
            if content.get('type') in {'output_text', 'text'} and content.get('text'):
                return content['text']
    return ''


@bp.get('/overview')
def overview():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(_build_context())


@bp.post('/chat')
def chat():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json(silent=True) or {}
    message = str(data.get('message') or '').strip()
    if not message:
        return jsonify({'error': 'Message is required.'}), 400
    if len(message) > 4000:
        return jsonify({'error': 'Message is too long.'}), 400

    api_key = (os.getenv('OPENAI_API_KEY') or '').strip()
    if not api_key:
        return jsonify({
            'configured': False,
            'message': 'POSP AI is installed, but OPENAI_API_KEY is not configured on the backend yet.',
        }), 503

    context = _build_context()
    prompt = f"""Operational context (JSON):
{json.dumps(context, ensure_ascii=False, separators=(',', ':'))}

Administrator request:
{message}
"""
    model = (os.getenv('POSP_AI_MODEL') or 'gpt-5.6-luna').strip()
    try:
        response = requests.post(
            'https://api.openai.com/v1/responses',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={
                'model': model,
                'instructions': SYSTEM_PROMPT,
                'input': prompt,
                'max_output_tokens': 900,
            },
            timeout=45,
        )
        if response.status_code >= 400:
            return jsonify({
                'configured': True,
                'error': 'AI provider request failed.',
                'provider_status': response.status_code,
            }), 502
        answer = _extract_response_text(response.json())
        if not answer:
            return jsonify({'configured': True, 'error': 'AI returned no text response.'}), 502
        return jsonify({'configured': True, 'answer': answer, 'checked_at': context['checked_at'], 'model': model})
    except requests.RequestException:
        return jsonify({'configured': True, 'error': 'AI provider could not be reached.'}), 502


@bp.post('/run-job-sync')
def run_job_sync():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    from ..jobs.sync import sync_all_sources
    result = sync_all_sources()
    return jsonify({
        'message': 'Approved job-source synchronization completed.' if result.get('successful_sources') else 'Job synchronization did not complete successfully.',
        'result': result,
    }), 200 if result.get('successful_sources') else 502
