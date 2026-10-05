from app.ai_tools import PermissionLevel, ToolDefinition, ToolRegistry


def test_read_tool_executes():
    registry = ToolRegistry()
    registry.register(ToolDefinition('health_check', 'Read operational health.', PermissionLevel.READ,
                                     handler=lambda args: {'status': 'healthy'}))
    result = registry.execute('health_check')
    assert result.ok is True
    assert result.status == 'completed'
    assert result.data == {'status': 'healthy'}


def test_safe_fix_requires_independent_verifier():
    registry = ToolRegistry()
    registry.register(ToolDefinition('retry_sync', 'Retry an approved deterministic sync.', PermissionLevel.SAFE_FIX,
                                     handler=lambda args: {'retried': True}, reversible=True))
    result = registry.execute('retry_sync', {'source': 'approved'})
    assert result.ok is False
    assert result.status == 'verification_required'


def test_safe_fix_executes_only_after_verification():
    registry = ToolRegistry()
    registry.register(ToolDefinition('retry_sync', 'Retry and verify an approved deterministic sync.', PermissionLevel.SAFE_FIX,
                                     handler=lambda args: {'retried': True},
                                     verifier=lambda args, data: {'verified': data.get('retried') is True}, reversible=True))
    result = registry.execute('retry_sync', {'source': 'approved'})
    assert result.ok is True
    assert result.status == 'verified'


def test_safe_fix_verification_failure_never_reports_success():
    registry = ToolRegistry()
    registry.register(ToolDefinition('retry_sync', 'Retry and verify an approved deterministic sync.', PermissionLevel.SAFE_FIX,
                                     handler=lambda args: {'retried': True},
                                     verifier=lambda args, data: {'verified': False}, reversible=True))
    result = registry.execute('retry_sync')
    assert result.ok is False
    assert result.status == 'verification_failed'


def test_approval_tool_only_proposes_without_approval():
    registry = ToolRegistry()
    registry.register(ToolDefinition('publish_notice', 'Publish a new notice.', PermissionLevel.APPROVAL,
                                     handler=lambda args: {'published': True}))
    result = registry.execute('publish_notice', {'id': '123'})
    assert result.ok is False
    assert result.status == 'approval_required'
    assert result.data['proposal']['tool'] == 'publish_notice'


def test_blocked_tool_cannot_execute_even_when_approved():
    registry = ToolRegistry()
    registry.register(ToolDefinition('delete_client_records', 'Delete client records.', PermissionLevel.BLOCKED,
                                     handler=lambda args: {'deleted': True}))
    result = registry.execute('delete_client_records', approved=True)
    assert result.ok is False
    assert result.status == 'blocked'


def test_unknown_tool_is_rejected():
    result = ToolRegistry().execute('shell')
    assert result.ok is False
    assert result.status == 'rejected'
