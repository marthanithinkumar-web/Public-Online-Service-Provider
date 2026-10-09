from app.ai_tools.registry import PermissionLevel, ToolDefinition, ToolRegistry


def test_safe_fix_requires_verification_for_success(monkeypatch):
    registry = ToolRegistry()
    registry.register(ToolDefinition('refresh', 'safe refresh', PermissionLevel.SAFE_FIX, lambda _: {'changed': True}, verifier=lambda _args, _data: {'verified': True}, reversible=True))

    result = registry.execute('refresh', autonomous=True)

    assert result.ok is True
    assert result.status == 'verified'
    assert result.verification['verified'] is True


def test_safe_fix_verification_failure_never_reports_success():
    registry = ToolRegistry()
    registry.register(ToolDefinition('refresh', 'safe refresh', PermissionLevel.SAFE_FIX, lambda _: {'changed': True}, verifier=lambda _args, _data: {'verified': False}, reversible=True))

    result = registry.execute('refresh', autonomous=True)

    assert result.ok is False
    assert result.status == 'verification_failed'


def test_approval_tool_cannot_run_autonomously():
    registry = ToolRegistry()
    registry.register(ToolDefinition('publish', 'publish notification', PermissionLevel.APPROVAL, lambda _: {'published': True}))

    result = registry.execute('publish', autonomous=True)

    assert result.ok is False
    assert result.status == 'approval_required'


def test_blocked_tool_remains_blocked():
    registry = ToolRegistry()
    registry.register(ToolDefinition('delete_client_data', 'delete private client data', PermissionLevel.BLOCKED, lambda _: {}))

    result = registry.execute('delete_client_data', autonomous=True)

    assert result.ok is False
    assert result.status == 'blocked'
