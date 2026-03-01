"""
JARVIS Brain Layer - Tool Registry Module

Manages tool registration and parses action calls from LLM output.
"""

import re
import json
from typing import Any, Callable

from loguru import logger


class ToolExecutionError(Exception):
    """Raised when tool execution fails."""
    pass


class ToolRegistry:
    """Registry for managing and executing tools."""

    def __init__(self):
        self.tools: dict[str, dict[str, Any]] = {}
        self._action_pattern = re.compile(
            r"^Action:\s*(\w+)(?::\s*(.+))?$",
            re.MULTILINE | re.IGNORECASE
        )
        self._thought_pattern = re.compile(
            r"^Thought:\s*(.+)$",
            re.MULTILINE | re.DOTALL
        )

    def register(
        self,
        name: str,
        func: Callable[..., Any],
        description: str = "",
        parameter_schema: dict | None = None,
    ) -> None:
        """Register a tool with the registry."""
        self.tools[name.lower()] = {
            "func": func,
            "desc": description,
            "schema": parameter_schema,
        }
        logger.debug(f"Registered tool: {name}")

    def unregister(self, name: str) -> bool:
        """Unregister a tool."""
        name_lower = name.lower()
        if name_lower in self.tools:
            del self.tools[name_lower]
            logger.debug(f"Unregistered tool: {name}")
            return True
        return False

    def list_tools(self) -> dict[str, str]:
        """List all registered tools with descriptions."""
        return {name: info["desc"] for name, info in self.tools.items()}

    def get_tool_schema(self) -> str:
        """Get formatted string of tool schemas for prompt."""
        if not self.tools:
            return "No tools available."
        
        lines = ["Available tools:"]
        for name, info in self.tools.items():
            desc = info.get("desc", "No description")
            lines.append(f"- {name}: {desc}")
        return "\n".join(lines)

    def execute(self, name: str, args: dict[str, Any] | str | None = None) -> str:
        """Execute a registered tool."""
        name_lower = name.lower()
        
        if name_lower not in self.tools:
            return f"Error: Unknown tool '{name}'. Available tools: {', '.join(self.tools.keys())}"
        
        tool = self.tools[name_lower]
        func = tool["func"]
        
        try:
            if args is None:
                args = {}
            elif isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    return f"Error: Invalid JSON arguments for tool '{name}': {args}"
            
            if not isinstance(args, dict):
                return f"Error: Tool '{name}' requires a dict of arguments, got {type(args)}"
            
            result = func(args)
            logger.debug(f"Tool '{name}' executed successfully")
            return str(result) if result is not None else "Tool executed successfully"
            
        except Exception as e:
            error_msg = f"Tool '{name}' failed: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"

    def parse_action(self, response: str) -> tuple[str | None, str | None, str | None]:
        """
        Parse Thought and Action from LLM response.
        
        Returns:
            Tuple of (thought, action_name, action_args) or (None, None, None) if no action found
        """
        thought_match = self._thought_pattern.search(response)
        thought = thought_match.group(1).strip() if thought_match else None
        
        action_match = self._action_pattern.search(response)
        if not action_match:
            return thought, None, None
        
        action_name = action_match.group(1).strip()
        action_args = action_match.group(2)
        
        if action_args:
            action_args = action_args.strip()
        
        return thought, action_name, action_args

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name.lower() in self.tools


def create_default_registry() -> ToolRegistry:
    """Create a registry with built-in basic tools."""
    registry = ToolRegistry()
    
    def get_time(args: dict) -> str:
        from datetime import datetime
        return datetime.now().strftime("%I:%M %p")
    
    def get_date(args: dict) -> str:
        from datetime import datetime
        return datetime.now().strftime("%A, %B %d, %Y")
    
    registry.register("get_time", get_time, "Get the current time")
    registry.register("get_date", get_date, "Get the current date")
    
    return registry


__all__ = ["ToolRegistry", "ToolExecutionError", "create_default_registry"]
