from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping


class PermissionLevel(str, Enum):
    READ = 'read'
    SAFE_FIX = 'safe_fix'
    APPROVAL = 'approval'
    BLOCKED = 'blocked'


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    permission: PermissionLevel
    handler: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None
    input_schema: Mapping[str, Any] = field(default_factory=dict)
    reversible: bool = True


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    status: str
    tool: str
    data: Mapping[str, Any] = field(default_factory=dict)
    error: str | None = None


class ToolRegistry:
    """Allowlisted POSP AI capabilities with policy enforcement outside the model."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        if not definition.name or definition.name in self._tools:
            raise ValueError('Tool name must be unique and non-empty.')
        self._tools[definition.name] = definition

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def definitions(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def public_schemas(self) -> list[dict[str, Any]]:
        return [
            {
                'name': tool.name,
                'description': tool.description,
                'permission': tool.permission.value,
                'input_schema': dict(tool.input_schema),
            }
            for tool in self._tools.values()
            if tool.permission != PermissionLevel.BLOCKED
        ]

    def execute(
        self,
        name: str,
        arguments: Mapping[str, Any] | None = None,
        *,
        approved: bool = False,
    ) -> ToolResult:
        tool = self.get(name)
        if tool is None:
            return ToolResult(False, 'rejected', name, error='Tool is not allowlisted.')
        if tool.permission == PermissionLevel.BLOCKED:
            return ToolResult(False, 'blocked', name, error='Tool is blocked by POSP AI policy.')
        if tool.permission == PermissionLevel.APPROVAL and not approved:
            return ToolResult(
                False,
                'approval_required',
                name,
                data={'proposal': {'tool': name, 'arguments': dict(arguments or {})}},
                error='Explicit admin approval is required before execution.',
            )
        if tool.handler is None:
            return ToolResult(False, 'unavailable', name, error='Tool has no executable handler.')
        try:
            data = tool.handler(arguments or {})
            return ToolResult(True, 'verified', name, data=data)
        except Exception as exc:
            return ToolResult(False, 'failed', name, error=f'{type(exc).__name__}: {str(exc)[:200]}')
