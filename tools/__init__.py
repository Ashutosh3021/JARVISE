# JARVIS Tools Module

from tools.base import BaseTool, ToolError, execute_with_error_handling

__all__ = [
    "BaseTool",
    "ToolError",
    "execute_with_error_handling",
]


def create_tools_registry():
    """Create and return a tools registry with all tools registered."""
    from brain.tools import create_tools_registry as _create
    return _create()
