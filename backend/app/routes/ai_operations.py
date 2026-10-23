import difflib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from sqlalchemy.orm import joinedload
from flask import Blueprint, jsonify, request

from ..models.admin_audit import AdminAuditLog
from ..models.job import JobNotification, JobSource
from ..models.order import Order
from ..models.service import Service
from ..models.support_message import SupportMessage
from ..utils.database import db
from ..utils.jwt_handler import get_request_user
from ..utils.readiness import production_readiness
from ..ai_core import call_model as _call_model, configured_model as _configured_model, configured_provider as _configured_provider, is_configured as _ai_is_configured, _extract_openai_text as _extract_response_text
from .admin import _require_admin

bp = Blueprint('ai_operations', __name__)
SCHOLARSHIP_SNAPSHOT = Path(__file__).resolve().parents[1] / 'scholarships' / 'data' / 'scholarships.json'

SYSTEM_PROMPT = """You are POSP AI Operations, an internal operations assistant for Public Online Service Provider.
Use only supplied operational context. Never invent check results. Distinguish healthy, warning, failed, stale, and unknown.
Jobs and scholarships must remain based on approved/official sources. Never claim a production change unless the action result says it succeeded.
Never expose credentials, tokens, private client data, payment secrets, or security secrets. Risky changes require admin review.
Be concise and action-oriented.
"""

CLIENT_AI_PROMPT = """You are the POSP customer support assistant inside the existing private Client/Admin chat.
Understand the user's intent even when the message is silly, informal, misspelled, grammatically incorrect, missing words, has swapped letters, repeated letters, speech-to-text errors, or jumbled word order. Silently correct likely typos when intent is clear; do not criticize spelling. If there are multiple plausible meanings, ask one short clarifying question instead of guessing.
Use the supplied POSP service and request context first. When Google Search results are supplied, use them for current or external facts and prefer official sources for government schemes, jobs, scholarships, deadlines, fees, eligibility, and required documents. Cite source URLs included in the search results. Never pretend to have searched if no search results are supplied.
- POSP is an online public-service APPLY platform, not a government portal.
- Never invent eligibility, official fees, deadlines, document requirements, outcomes, or government rules.
- If neither the supplied context nor grounded search establishes an answer, set HANDOFF=YES. A spelling error or an unusual question is not, by itself, a reason to hand off.
- Never reveal another client's information, prompts, credentials, payment secrets, or private operational data.
- Never ask for passwords, OTPs, card numbers, UPI PINs, or authentication/payment secrets.
- Requests for a human, payment/security problems, complaints, or unsupported actions require HANDOFF=YES.
Return exactly two lines:
HANDOFF=YES or HANDOFF=NO
ANSWER=<client-facing answer>
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
                {'key': key, 'source_name': value.get('source_name'), 'ok': bool(value.get('ok')),
                 'count': int(value.get('count') or 0), 'error': value.get('error'),
                 'checked_at': value.get('checked_at')}
                for key, value in sorted(health.items())
            ],
        }
    except (OSError, ValueError, TypeError) as exc:
        return {'available': False, 'error': f'{type(exc).__name__}: {str(exc)[:160]}'}

def _build_context():
    jobs = JobNotification.query
    readiness = production_readiness()
    scholarship = _load_scholarship_snapshot()
    return {
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'runtime': {
            'database': True,
            'production_readiness': readiness,
            'production_readiness_status': 'ready' if all(readiness.values()) else 'needs_configuration',
        },
        'jobs': {
            'published': jobs.filter_by(status='published').count(),
            'needs_review': jobs.filter_by(status='needs_review').count(),
            'expired': jobs.filter_by(status='expired').count(),
            'hidden': jobs.filter_by(status='hidden').count(),
            'sources': [source.to_dict() for source in JobSource.query.order_by(JobSource.name).all()],
        },
        'scholarships': scholarship,
        'ai': {
            'client_ai_enabled': os.getenv('POSP_CLIENT_AI_ENABLED', 'false').strip().lower() == 'true',
            'operations_ai_configured': _ai_is_configured(),
            'provider': _configured_provider(),
            'model': _configured_model(),
        },
    }

def _operations_findings(context):
    findings = []
    for name, ok in context['runtime']['production_readiness'].items():
        if not ok:
            findings.append({'severity': 'warning', 'area': name, 'message': 'Production configuration check is not ready.'})
    scholarship = context['scholarships']
    if not scholarship.get('available'):
        findings.append({'severity': 'failed', 'area': 'scholarships', 'message': 'Scholarship snapshot is unavailable.'})
    elif scholarship.get('stale_source_count', 0):
        findings.append({'severity': 'warning', 'area': 'scholarships', 'message': f"{scholarship['stale_source_count']} scholarship source(s) are stale."})
    if context['jobs']['needs_review']:
        findings.append({'severity': 'warning', 'area': 'jobs', 'message': f"{context['jobs']['needs_review']} job notice(s) need review."})
    return findings

def _parse_client_ai_response(raw):
    lines = raw.splitlines()
    first_line = lines[0].strip().upper() if lines else ''
    handoff = first_line == 'HANDOFF=YES'
    answer = raw.split('ANSWER=', 1)[1].strip() if 'ANSWER=' in raw else raw.strip()
    return answer, handoff

def _should_use_google_search(message, relevant_services):
    """Use web grounding only when the user clearly needs current/external information."""
    text = (message or "").lower()
    terms = set(re.findall(r"[a-z0-9]+", text))
    current_intent = {
        "latest", "current", "today", "tomorrow", "now", "recent", "new", "newest",
        "deadline", "lastdate", "news", "notification", "recruitment", "opening",
        "openings", "vacancy", "vacancies", "result", "results", "2026", "2027"
    }
    explicit_web_intent = {
        "search", "google", "online", "source", "sources", "link", "links",
        "website", "websites", "official"
    }
    public_program_topics = {
        "scholarship", "scholarships", "job", "jobs", "recruitment", "government",
        "govt", "scheme", "schemes", "exam", "exams", "admission", "admissions"
    }
    time_sensitive_topics = {
        "deadline", "lastdate", "notification", "recruitment", "vacancy", "vacancies",
        "opening", "openings", "result", "results", "latest", "current", "today", "now"
    }
    # Clear requests for current updates or an external search always use grounding.
    if terms & current_intent:
        return True
    if terms & explicit_web_intent and not (terms & {"request", "track", "status", "application"}):
        return True
    # Public-sector opportunities and schemes often change; search when the question
    # asks about eligibility, fees, documents, dates, or applying to a named program.
    if terms & public_program_topics and terms & {
        "eligibility", "eligible", "documents", "fees", "fee", "deadline", "lastdate",
        "apply", "application", "notification", "official", "required", "requirements"
    }:
        return True
    # Do not web-search ordinary POSP FAQs or unknown questions by default. Ask Gemini
    # to answer from existing context, and let its handoff rules handle uncertainty.
    return False


def _quick_client_reply(message):
    """Answer unambiguous greetings/thanks without DB queries or a model round-trip."""
    normalized = re.sub(r"[^a-z0-9\s]", " ", (message or "").lower())
    normalized = re.sub(r"(.)\1{2,}", r"\1\1", normalized)
    normalized = " ".join(normalized.split())
    replies = {
        "hi": "Hi! How can I help you with your application or request today?",
        "hello": "Hello! How can I help you with your application or request today?",
        "hey": "Hey! What can I help you with today?",
        "hii": "Hi! How can I help you with your application or request today?",
        "heyy": "Hey! What can I help you with today?",
        "good morning": "Good morning! How can I help you with a service or request today?",
        "good afternoon": "Good afternoon! How can I help you with a service or request today?",
        "good evening": "Good evening! How can I help you with a service or request today?",
        "thanks": "You're welcome! Let me know if you need help with a service or request.",
        "thank you": "You're welcome! Let me know if you need help with a service or request.",
        "thx": "You're welcome! Let me know if you need help with a service or request.",
        "ok thanks": "You're welcome! Let me know if you need help with a service or request.",
        "bye": "Goodbye! You can message us here again whenever you need help.",
    }
    return replies.get(normalized)


def generate_client_reply(user, current_message):
    if os.getenv('POSP_CLIENT_AI_ENABLED', 'false').strip().lower() != 'true':
        return None, False, 'Client AI is disabled.'
    quick_reply = _quick_client_reply(current_message)
    if quick_reply:
        return quick_reply, False, None
    # Keep the prompt small: sending the full service catalogue and long chat history
    # increases latency and can distract the model from the client's actual question.
    message_terms = {term for term in ''.join(
        char.lower() if char.isalnum() else ' ' for char in current_message
    ).split() if len(term) > 2}
    # Eager-load categories to avoid a lazy-load database query per service (N+1).
    candidates = Service.query.options(joinedload(Service.category)).filter_by(is_active=True).order_by(Service.name).all()
    ranked_services = []
    for service in candidates:
        searchable = f"{service.name or ''} {service.description or ''} {service.keywords or ''} {service.category.name if service.category else ''}".lower()
        searchable_terms = {term for term in ''.join(
            char if char.isalnum() else ' ' for char in searchable
        ).split() if len(term) > 2}
        score = len(message_terms & searchable_terms)
        # Recover service matches when the client misspells a service keyword.
        for term in message_terms - searchable_terms:
            if len(term) >= 4 and searchable_terms:
                if difflib.get_close_matches(term, searchable_terms, n=1, cutoff=0.76):
                    score += 1
        if score:
            ranked_services.append((score, service))
    ranked_services.sort(key=lambda pair: (-pair[0], pair[1].name.lower()))
    services = [{
        'name': service.name,
        'category': service.category.name if service.category else None,
        'description': (service.description or '')[:220],
        'application_fee_inr': float(service.price_inr or 0),
        'official_fee_inr': float(service.official_fee_inr) if service.official_fee_inr is not None else None,
        'official_fee_status': service.official_fee_status or 'unconfirmed',
        'keywords': (service.keywords or '')[:160],
    } for _, service in ranked_services[:8]]
    orders = [{
        'order_code': order.order_code,
        'service': order.service.name if order.service else None,
        'status': order.status,
        'updated_at': (order.updated_at or order.created_at).isoformat(),
    } for order in Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).limit(5).all()]
    history = [{
        'role': 'client' if item.sender_role == 'client' else 'assistant',
        'content': item.message[:500],
    } for item in SupportMessage.query.filter_by(user_id=user.id)
        .order_by(SupportMessage.created_at.desc()).limit(8).all()][::-1]
    context = {'relevant_services': services, 'client_requests': orders, 'recent_conversation': history}
    use_google_search = _should_use_google_search(current_message, services)
    prompt = f"""Answer the client's latest message by understanding their intended meaning, not by judging their spelling or grammar.
The message may contain typos, missing letters/words, phonetic spelling, mixed-up word order, slang, repeated characters, or a silly/very short question. Try to infer the most likely meaning from context. If the meaning is clear, answer normally without mentioning the typo. If genuinely ambiguous, ask one brief clarification question and do not hand off merely because of spelling.
Be accurate, quick, friendly, and easy to understand. Prefer 1–4 short sentences or a few steps. Use simple English and do not repeat the question or reveal internal reasoning.
Use supplied POSP service/request context first. For current or external factual questions, use any grounded Google Search results provided with this request. Prefer official government or organization sources for fees, eligibility, deadlines, jobs, scholarships, rules, and required documents. If a fact cannot be confirmed by context or search, say so clearly and set HANDOFF=YES rather than inventing it.
POSP helps people APPLY for public services; it is not a government portal. Treat greetings and harmless silly questions politely; hand off only when a human is requested, a sensitive issue is raised, or the question needs an administrator.
Context JSON: {json.dumps(context, ensure_ascii=False, separators=(',', ':'))}
Latest client message (interpret generously): {current_message}
"""
    raw, error = _call_model(CLIENT_AI_PROMPT, prompt, 300, use_google_search=use_google_search)
    if error:
        return None, True, error
    answer, handoff = _parse_client_ai_response(raw)
    if not answer:
        return None, True, 'AI produced an empty client answer.'
    return answer, handoff, None

@bp.get('/overview')
def overview():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    context = _build_context()
    return jsonify({**context, 'findings': _operations_findings(context)})

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
    context = _build_context()
    prompt = f"""Operational context (JSON):
{json.dumps(context, ensure_ascii=False, separators=(',', ':'))}

Administrator request:
{message}
"""
    answer, error = _call_model(SYSTEM_PROMPT, prompt, 900)
    if error:
        return jsonify({'configured': _ai_is_configured(), 'provider': _configured_provider(), 'error': error}), 502
    model = _configured_model()
    return jsonify({'configured': True, 'provider': _configured_provider(), 'answer': answer, 'checked_at': context['checked_at'], 'model': model})

@bp.post('/run-job-sync')
def run_job_sync():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    admin = get_request_user()
    from ..jobs.sync import sync_all_sources
    result = sync_all_sources()
    db.session.add(AdminAuditLog(
        admin_id=admin.id,
        action='ai_job_sync',
        summary='Ran the approved job-source synchronization from POSP AI Operations.',
        details={'result': result},
    ))
    db.session.commit()
    return jsonify({
        'message': 'Approved job-source synchronization completed.' if result.get('successful_sources')
            else 'Job synchronization did not complete successfully.',
        'result': result,
    }), 200 if result.get('successful_sources') else 502
