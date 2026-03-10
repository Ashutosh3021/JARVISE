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

    def __init__(self, use_cache: bool = True, use_retry: bool = True):
        self.tools: dict[str, dict[str, Any]] = {}
        self._action_pattern = re.compile(
            r"^Action:\s*(\w+)(?::\s*(.+))?$",
            re.MULTILINE | re.IGNORECASE
        )
        self._thought_pattern = re.compile(
            r"^Thought:\s*(.+)$",
            re.MULTILINE | re.DOTALL
        )
        
        # Learning components
        self._use_cache = use_cache
        self._use_retry = use_retry
        self._cache = None
        self._retry_engine = None
        
        # Initialize learning components if enabled
        if use_cache:
            try:
                from learning import ToolCache
                self._cache = ToolCache()
                logger.debug("Tool cache enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize tool cache: {e}")
        
        if use_retry:
            try:
                from learning import RetryEngine
                self._retry_engine = RetryEngine(self, max_retries=3)
                logger.debug("Retry engine enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize retry engine: {e}")

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
        
        # Normalize args to dict
        normalized_args = {}
        try:
            if args is None:
                normalized_args = {}
            elif isinstance(args, str):
                try:
                    normalized_args = json.loads(args)
                except json.JSONDecodeError:
                    return f"Error: Invalid JSON arguments for tool '{name}': {args}"
            elif isinstance(args, dict):
                normalized_args = args
            else:
                return f"Error: Tool '{name}' requires a dict of arguments, got {type(args)}"
        except Exception as e:
            return f"Error: Failed to process arguments for tool '{name}': {str(e)}"
        
        # Check cache first
        if self._cache is not None:
            cached_result = self._cache.get(name_lower, normalized_args)
            if cached_result is not None:
                logger.debug(f"Cache hit for tool '{name}'")
                return cached_result
        
        # Execute with retry if enabled
        if self._retry_engine is not None:
            retry_result = self._retry_engine.execute_with_retry(name_lower, normalized_args)
            
            # Cache successful results
            if self._cache is not None and retry_result.success:
                self._cache.set(name_lower, normalized_args, retry_result.final_output, success=True)
            
            return retry_result.final_output
        
        # Direct execution (fallback)
        try:
            result = func(normalized_args)
            result_str = str(result) if result is not None else "Tool executed successfully"
            
            # Cache successful results
            if self._cache is not None and not result_str.startswith("Error:"):
                self._cache.set(name_lower, normalized_args, result_str, success=True)
            
            logger.debug(f"Tool '{name}' executed successfully")
            return result_str
            
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
    
    def get_cache_stats(self) -> dict | None:
        """Get tool cache statistics.
        
        Returns:
            Dict with cache stats or None if cache not enabled
        """
        if self._cache is None:
            return None
        return self._cache.get_stats()
    
    def get_retry_stats(self) -> dict | None:
        """Get retry engine statistics.
        
        Returns:
            Dict with retry stats or None if retry not enabled
        """
        if self._retry_engine is None:
            return None
        return self._retry_engine.get_stats()
    
    def invalidate_cache(self, tool_name: str = None, args: dict = None) -> int:
        """Invalidate cache entries.
        
        Args:
            tool_name: Tool to invalidate (None = all)
            args: Specific args to invalidate
            
        Returns:
            Number of entries invalidated
        """
        if self._cache is None:
            return 0
        
        if tool_name is None:
            self._cache.clear_all()
            return len(self._cache)
        
        return self._cache.invalidate(tool_name, args)


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


def create_tools_registry() -> ToolRegistry:
    """Create a comprehensive registry with all JARVIS tools.
    
    This function imports and registers all available tools:
    - browser: Web browsing and automation
    - web_search: Web search functionality
    - filesystem: File operations
    - code_exec: Sandboxed code execution
    - google_calendar: Google Calendar integration
    - google_email: Google Email (Gmail) integration
    - microsoft_outlook: Microsoft Outlook/Exchange integration
    - system_monitor: System diagnostics (CPU, memory, disk, network)
    
    Returns:
        ToolRegistry with all tools registered
    """
    from tools.browser import BrowserTool
    from tools.web_search import WebSearchTool
    from tools.filesystem import FilesystemTool
    from tools.code_exec import CodeExecutionTool
    from tools.google_calendar import GoogleCalendarTool
    from tools.google_email import GoogleEmailTool
    from tools.microsoft_outlook import MicrosoftOutlookTool
    from tools.system_monitor import SystemMonitorTool
    
    registry = ToolRegistry()
    
    # Create tool instances
    browser = BrowserTool()
    web_search = WebSearchTool()
    filesystem = FilesystemTool()
    code_exec = CodeExecutionTool()
    google_calendar = GoogleCalendarTool()
    google_email = GoogleEmailTool()
    microsoft_outlook = MicrosoftOutlookTool()
    system_monitor = SystemMonitorTool()
    
    # Register browser tool
    def execute_browser(args: dict) -> str:
        """Execute browser tool action."""
        action = args.get("action", "navigate")
        url = args.get("url", "")
        return browser.execute(action=action, url=url)
    
    registry.register(
        "browser",
        execute_browser,
        "Navigate to URLs, extract content, fill forms, click elements"
    )
    
    # Register web search tool
    def execute_search(args: dict) -> str:
        """Execute web search."""
        query = args.get("query", "")
        max_results = args.get("max_results", 10)
        return web_search.execute(query=query, max_results=max_results)
    
    registry.register(
        "web_search",
        execute_search,
        "Search the web using browser automation"
    )
    
    # Register filesystem tool
    def execute_filesystem(args: dict) -> str:
        """Execute filesystem operation."""
        action = args.get("action", "list")
        path = args.get("path", ".")
        return filesystem.execute(action=action, path=path)
    
    registry.register(
        "filesystem",
        execute_filesystem,
        "Read, write, delete files. Requires user confirmation."
    )
    
    # Register code execution tool
    def execute_code(args: dict) -> str:
        """Execute Python code."""
        code = args.get("code", "")
        return code_exec.execute(code=code)
    
    registry.register(
        "execute_code",
        execute_code,
        "Run Python code in sandboxed environment"
    )
    
    # Register Google Calendar tool
    def execute_calendar(args: dict) -> str:
        """Execute Google Calendar operation."""
        action = args.get("action", "list_events")
        return google_calendar.execute(action=action, **args)
    
    registry.register(
        "google_calendar",
        execute_calendar,
        "List, create, update Google Calendar events"
    )
    
    # Register Google Email tool
    def execute_gmail(args: dict) -> str:
        """Execute Google Email operation."""
        action = args.get("action", "list_emails")
        return google_email.execute(action=action, **args)
    
    registry.register(
        "google_email",
        execute_gmail,
        "Read, send Google Email messages"
    )
    
    # Register Microsoft Outlook tool
    def execute_outlook(args: dict) -> str:
        """Execute Microsoft Outlook operation."""
        action = args.get("action", "list_emails")
        return microsoft_outlook.execute(action=action, **args)
    
    registry.register(
        "outlook",
        execute_outlook,
        "Read, send Microsoft Outlook emails via Microsoft Graph"
    )
    
    # Register system monitor tool
    def execute_monitor(args: dict) -> str:
        """Execute system monitoring."""
        action = args.get("action", "all")
        return system_monitor.execute(action=action, **args)
    
    registry.register(
        "system_monitor",
        execute_monitor,
        "Get CPU, memory, disk, network statistics"
    )
    
    # Register get_time and get_date (built-in)
    def get_time(args: dict) -> str:
        from datetime import datetime
        return datetime.now().strftime("%I:%M %p")
    
    def get_date(args: dict) -> str:
        from datetime import datetime
        return datetime.now().strftime("%A, %B %d, %Y")
    
    registry.register("get_time", get_time, "Get the current time")
    registry.register("get_date", get_date, "Get the current date")
    
    return registry


__all__ = ["ToolRegistry", "ToolExecutionError", "create_default_registry", "create_tools_registry"]
