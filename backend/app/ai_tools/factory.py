from __future__ import annotations

from .posp_operations import register_posp_operations
from .registry import ToolRegistry


def build_posp_ai_registry() -> ToolRegistry:
    registry = ToolRegistry()
    register_posp_operations(registry)
    return registry
