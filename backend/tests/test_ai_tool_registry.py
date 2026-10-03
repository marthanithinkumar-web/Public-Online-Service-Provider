from app.ai_tools import PermissionLevel, ToolDefinition, ToolRegistry


def test_read_tool_executes():
    registry = ToolRegistry()
    registry.register(ToolDefinition(
        name='health_check',
        description='Read operational health.',
        permission=PermissionLevel.READ,
        handler=lambda args: {'status': 'healthy'},
    ))

    result = registry.execute('health_check')

    assert result.ok is True
    assert result.status == 'verified'
    assert result.data == {'status': 'healthy'}


def test_safe_fix_executes():
    registry = ToolRegistry()
    registry.register(ToolDefinition(
        name='retry_sync',
        description='Retry an approved deterministic sync.',
        permission=PermissionLevel.SAFE_FIX,
        handler=lambda args: {'retried': True},
    ))

    result = registry.execute('retry_sync', {'source': 'approved'})

    assert result.ok is True
    assert result.data['retried'] is True


def test_approval_tool_only_proposes_without_approval():
    registry = ToolRegistry()
    registry.register(ToolDefinition(
        name='publish_notice',
        description='Publish a new notice.',
        permission=PermissionLevel.APPROVAL,
        handler=lambda args: {'published': True},
    ))

    result = registry.execute('publish_notice', {'id': '123'})

    assert result.ok is False
    assert result.status == 'approval_required'
    assert result.data['proposal']['tool'] == 'publish_notice'


def test_blocked_tool_cannot_execute_even_when_approved():
    registry = ToolRegistry()
    registry.register(ToolDefinition(
        name='delete_client_records',
        description='Delete client records.',
        permission=PermissionLevel.BLOCKED,
        handler=lambda args: {'deleted': True},
    ))

    result = registry.execute('delete_client_records', approved=True)

    assert result.ok is False
    assert result.status == 'blocked'


def test_unknown_tool_is_rejected():
    registry = ToolRegistry()

    result = registry.execute('shell')

    assert result.ok is False
    assert result.status == 'rejected'
