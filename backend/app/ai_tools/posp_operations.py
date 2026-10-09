from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from ..jobs.sync import sync_all_sources
from ..models.job import JobNotification, JobSource
from ..scholarships.snapshot import refresh_snapshot
from ..utils.readiness import production_readiness
from .registry import PermissionLevel, ToolDefinition, ToolRegistry


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def jobs_status(_: Mapping[str, Any]) -> Mapping[str, Any]:
    query = JobNotification.query
    sources = []
    for source in JobSource.query.order_by(JobSource.name).all():
        sources.append({'key': source.key, 'name': source.name, 'enabled': bool(source.enabled), 'status': source.last_sync_status,
                        'last_sync_completed_at': source.last_sync_completed_at.isoformat() if source.last_sync_completed_at else None,
                        'last_error': source.last_error, 'published_count': int(source.published_count or 0)})
    return {'checked_at': _utc(), 'counts': {'published': query.filter_by(status='published').count(), 'needs_review': query.filter_by(status='needs_review').count(),
                                              'expired': query.filter_by(status='expired').count(), 'hidden': query.filter_by(status='hidden').count()}, 'sources': sources}


def sync_jobs(_: Mapping[str, Any]) -> Mapping[str, Any]:
    before = jobs_status({})
    sync = sync_all_sources()
    after = jobs_status({})
    return {'checked_at': _utc(), 'sync': sync, 'before': before['counts'], 'after': after['counts'],
            'delta': {key: after['counts'][key] - before['counts'][key] for key in before['counts']}}


def scholarship_status(_: Mapping[str, Any]) -> Mapping[str, Any]:
    path = Path(__file__).resolve().parents[1] / 'scholarships' / 'data' / 'scholarships.json'
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError, TypeError) as exc:
        return {'available': False, 'checked_at': _utc(), 'error': f'{type(exc).__name__}: {str(exc)[:180]}'}
    return {'available': True, 'checked_at': _utc(), 'generated_at': payload.get('generated_at'), 'count': int(payload.get('count') or 0),
            'official_count': int(payload.get('official_count') or 0), 'private_count': int(payload.get('private_count') or 0),
            'stale_source_count': int(payload.get('stale_source_count') or 0), 'source_health': (payload.get('discovery') or {}).get('source_health') or {}}


def refresh_scholarships(_: Mapping[str, Any]) -> Mapping[str, Any]:
    path = Path(__file__).resolve().parents[1] / 'scholarships' / 'data' / 'scholarships.json'
    before = scholarship_status({})
    payload = refresh_snapshot(path=path, discover=True, strict=True)
    after = scholarship_status({})
    return {'checked_at': _utc(), 'generated_at': payload.get('generated_at'), 'count': payload.get('count'), 'official_count': payload.get('official_count'),
            'private_count': payload.get('private_count'), 'stale_source_count': payload.get('stale_source_count'),
            'before_count': before.get('count'), 'after_count': after.get('count'), 'source_health': payload.get('discovery', {}).get('source_health', {})}


def notification_status(_: Mapping[str, Any]) -> Mapping[str, Any]:
    return {'checked_at': _utc(), 'jobs': jobs_status({}), 'scholarships': scholarship_status({}), 'runtime': production_readiness(),
            'publication_policy': 'automatic publication is limited to validated approved official sources'}


def seo_health(_: Mapping[str, Any]) -> Mapping[str, Any]:
    public_dir = Path(__file__).resolve().parents[3] / 'frontend' / 'public'
    robots = public_dir / 'robots.txt'
    sitemap = public_dir / 'sitemap.xml'
    robots_text = robots.read_text(encoding='utf-8') if robots.exists() else ''
    sitemap_text = sitemap.read_text(encoding='utf-8') if sitemap.exists() else ''
    return {'checked_at': _utc(), 'robots_exists': robots.exists(), 'sitemap_exists': sitemap.exists(),
            'robots_allows_root': 'Allow: /' in robots_text, 'robots_has_sitemap': 'Sitemap: https://pospindia.onrender.com/sitemap.xml' in robots_text,
            'sitemap_is_xml': sitemap_text.lstrip().startswith('<?xml') and '<urlset' in sitemap_text,
            'sitemap_url_count': sitemap_text.count('<url><loc>'),
            'site_url': 'https://pospindia.onrender.com',
            'issues': [name for name, ok in {
                'robots_missing': robots.exists(), 'sitemap_missing': sitemap.exists(), 'robots_root_blocked': 'Allow: /' in robots_text,
                'robots_sitemap_missing': 'Sitemap: https://pospindia.onrender.com/sitemap.xml' in robots_text,
                'sitemap_invalid': sitemap_text.lstrip().startswith('<?xml') and '<urlset' in sitemap_text}.items() if not ok]}


def refresh_notifications(_: Mapping[str, Any]) -> Mapping[str, Any]:
    before = notification_status({})
    job_result = sync_jobs({})
    scholarship_result = refresh_scholarships({})
    after = notification_status({})
    return {'checked_at': _utc(), 'jobs': job_result, 'scholarships': scholarship_result, 'before': before, 'after': after,
            'summary': {'job_published_delta': job_result['delta'].get('published', 0), 'job_expired_delta': job_result['delta'].get('expired', 0),
                        'scholarship_count_delta': int(after['scholarships'].get('count') or 0) - int(before['scholarships'].get('count') or 0),
                        'official_scholarship_count': after['scholarships'].get('official_count')}}


def verify_jobs_after_sync(_: Mapping[str, Any], __: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
    result = jobs_status({})
    failures = [source for source in result['sources'] if source['enabled'] and source['status'] not in {'success', 'degraded'}]
    return {'verified': not failures and bool(result['sources']), 'checked_at': result['checked_at'], 'failures': failures, 'counts': result['counts']}


def verify_scholarships_after_refresh(_: Mapping[str, Any], __: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
    result = scholarship_status({})
    health = result.get('source_health') or {}
    failed = [key for key, value in health.items() if not value.get('ok')]
    return {'verified': bool(result.get('available')) and not failed and int(result.get('official_count') or 0) > 0,
            'checked_at': result['checked_at'], 'failed_sources': failed, 'official_count': result.get('official_count'), 'count': result.get('count')}


def verify_notifications_after_refresh(_: Mapping[str, Any], data: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
    result = notification_status({})
    job_failures = [s for s in result['jobs']['sources'] if s['enabled'] and s['status'] not in {'success', 'degraded'}]
    scholarship_health = result['scholarships'].get('source_health') or {}
    scholarship_failures = [key for key, value in scholarship_health.items() if not value.get('ok')]
    return {'verified': not job_failures and bool(result['jobs']['sources']) and not scholarship_failures and int(result['scholarships'].get('official_count') or 0) > 0,
            'checked_at': result['checked_at'], 'job_failures': job_failures, 'scholarship_failures': scholarship_failures,
            'official_scholarship_count': result['scholarships'].get('official_count'), 'summary': (data or {}).get('summary', {})}


def register_posp_operations(registry: ToolRegistry) -> ToolRegistry:
    registry.register(ToolDefinition('jobs_status', 'Read current job counts and approved source health.', PermissionLevel.READ, jobs_status))
    registry.register(ToolDefinition('scholarship_status', 'Read current scholarship snapshot and official source health.', PermissionLevel.READ, scholarship_status))
    registry.register(ToolDefinition('notification_status', 'Read combined jobs, scholarships and runtime notification health.', PermissionLevel.READ, notification_status))
    registry.register(ToolDefinition('runtime_health', 'Read production readiness checks used by POSP.', PermissionLevel.READ, lambda _: {'checked_at': _utc(), 'readiness': production_readiness()}))
    registry.register(ToolDefinition('seo_health', 'Read deterministic robots.txt and sitemap.xml health without changing SEO configuration.', PermissionLevel.READ, seo_health))
    registry.register(ToolDefinition('sync_jobs', 'Refresh approved official job sources and expire outdated notices.', PermissionLevel.SAFE_FIX, sync_jobs, verifier=verify_jobs_after_sync, reversible=True))
    registry.register(ToolDefinition('refresh_scholarships', 'Refresh scholarships from approved official discovery sources with strict validation.', PermissionLevel.SAFE_FIX, refresh_scholarships, verifier=verify_scholarships_after_refresh, reversible=True))
    registry.register(ToolDefinition('refresh_notifications', 'Refresh approved official jobs and scholarship notifications, then independently verify both pipelines.', PermissionLevel.SAFE_FIX, refresh_notifications, verifier=verify_notifications_after_refresh, reversible=True))
    registry.register(ToolDefinition('verify_jobs_after_sync', 'Independently verify job-source state after a sync.', PermissionLevel.READ, verify_jobs_after_sync))
    registry.register(ToolDefinition('verify_scholarships_after_refresh', 'Independently verify scholarship source health and published counts.', PermissionLevel.READ, verify_scholarships_after_refresh))
    registry.register(ToolDefinition('verify_notifications_after_refresh', 'Independently verify combined notification health after refresh.', PermissionLevel.READ, verify_notifications_after_refresh))
    return registry
