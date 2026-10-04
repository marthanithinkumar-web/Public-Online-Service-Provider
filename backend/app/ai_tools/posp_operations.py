from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from ..jobs.sync import sync_all_sources
from ..models.job import JobNotification, JobSource
from ..scholarships.snapshot import refresh_snapshot
from .registry import PermissionLevel, ToolDefinition, ToolRegistry


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def jobs_status(_: Mapping[str, Any]) -> Mapping[str, Any]:
    query = JobNotification.query
    sources = []
    for source in JobSource.query.order_by(JobSource.name).all():
        sources.append({
            'key': source.key,
            'name': source.name,
            'enabled': bool(source.enabled),
            'status': source.last_sync_status,
            'last_sync_completed_at': source.last_sync_completed_at.isoformat() if source.last_sync_completed_at else None,
            'last_error': source.last_error,
            'published_count': int(source.published_count or 0),
        })
    return {
        'checked_at': _utc(),
        'counts': {
            'published': query.filter_by(status='published').count(),
            'needs_review': query.filter_by(status='needs_review').count(),
            'expired': query.filter_by(status='expired').count(),
            'hidden': query.filter_by(status='hidden').count(),
        },
        'sources': sources,
    }


def sync_jobs(_: Mapping[str, Any]) -> Mapping[str, Any]:
    result = sync_all_sources()
    return {'checked_at': _utc(), 'sync': result}


def scholarship_status(_: Mapping[str, Any]) -> Mapping[str, Any]:
    path = Path(__file__).resolve().parents[1] / 'scholarships' / 'data' / 'scholarships.json'
    try:
        import json
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError, TypeError) as exc:
        return {'available': False, 'checked_at': _utc(), 'error': f'{type(exc).__name__}: {str(exc)[:180]}'}
    discovery = payload.get('discovery') or {}
    return {
        'available': True,
        'checked_at': _utc(),
        'generated_at': payload.get('generated_at'),
        'count': int(payload.get('count') or 0),
        'official_count': int(payload.get('official_count') or 0),
        'private_count': int(payload.get('private_count') or 0),
        'stale_source_count': int(payload.get('stale_source_count') or 0),
        'source_health': discovery.get('source_health') or {},
    }


def refresh_scholarships(_: Mapping[str, Any]) -> Mapping[str, Any]:
    path = Path(__file__).resolve().parents[1] / 'scholarships' / 'data' / 'scholarships.json'
    payload = refresh_snapshot(path=path, discover=True, strict=True)
    return {
        'checked_at': _utc(),
        'generated_at': payload.get('generated_at'),
        'count': payload.get('count'),
        'official_count': payload.get('official_count'),
        'private_count': payload.get('private_count'),
        'stale_source_count': payload.get('stale_source_count'),
        'source_health': payload.get('discovery', {}).get('source_health', {}),
    }


def verify_jobs_after_sync(_: Mapping[str, Any]) -> Mapping[str, Any]:
    result = jobs_status({})
    failures = [source for source in result['sources'] if source['enabled'] and source['status'] not in {'success', 'degraded'}]
    return {'verified': not failures, 'checked_at': result['checked_at'], 'failures': failures, 'counts': result['counts']}


def verify_scholarships_after_refresh(_: Mapping[str, Any]) -> Mapping[str, Any]:
    result = scholarship_status({})
    health = result.get('source_health') or {}
    failed = [key for key, value in health.items() if not value.get('ok')]
    verified = bool(result.get('available')) and not failed and int(result.get('official_count') or 0) > 0
    return {'verified': verified, 'checked_at': result['checked_at'], 'failed_sources': failed, 'official_count': result.get('official_count'), 'count': result.get('count')}


def register_posp_operations(registry: ToolRegistry) -> ToolRegistry:
    registry.register(ToolDefinition('jobs_status', 'Read current job counts and approved source health.', PermissionLevel.READ, jobs_status))
    registry.register(ToolDefinition('scholarship_status', 'Read current scholarship snapshot and official source health.', PermissionLevel.READ, scholarship_status))
    registry.register(ToolDefinition('sync_jobs', 'Refresh approved official job sources and expire outdated notices.', PermissionLevel.SAFE_FIX, sync_jobs))
    registry.register(ToolDefinition('refresh_scholarships', 'Refresh scholarships from approved official discovery sources with strict validation.', PermissionLevel.SAFE_FIX, refresh_scholarships))
    registry.register(ToolDefinition('verify_jobs_after_sync', 'Independently verify job-source state after a sync.', PermissionLevel.READ, verify_jobs_after_sync))
    registry.register(ToolDefinition('verify_scholarships_after_refresh', 'Independently verify scholarship source health and published counts.', PermissionLevel.READ, verify_scholarships_after_refresh))
    return registry
