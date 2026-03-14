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
        # Only match Action: toolname or Action: toolname: {json}
        self._action_pattern = re.compile(
            r"^Action:\s*(\w+)(?:\s*:\s*(\{.+\}|\[.+\]))?$",
            re.MULTILINE | re.IGNORECASE
        )
        self._thought_pattern = re.compile(
            r"^Thought:\s*(.+?)(?=\nAction:|\n\n|\Z)",
            re.MULTILINE | re.DOTALL
        )
        
        # Disable learning components for simplicity
        self._use_cache = False
        self._use_retry = False
        self._cache = None
        self._retry_engine = None

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
        
        # Normalize args to dict - simple approach
        normalized_args = {}
        if args is None:
            normalized_args = {}
        elif isinstance(args, dict):
            normalized_args = args
        elif isinstance(args, str):
            if args.startswith('{') or args.startswith('['):
                try:
                    normalized_args = json.loads(args)
                except:
                    normalized_args = {}
            else:
                normalized_args = {}
        
        # Direct execution
        try:
            result = func(normalized_args)
            result_str = str(result) if result is not None else "Done"
            logger.debug(f"Tool '{name}' executed: {result_str}")
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
    import os
    from pathlib import Path
    
    registry = ToolRegistry()
    
    # Time/Date tools
    def get_time(args: dict) -> str:
        from datetime import datetime
        return datetime.now().strftime("%I:%M %p")
    
    def get_date(args: dict) -> str:
        from datetime import datetime
        return datetime.now().strftime("%A, %B %d, %Y")
    
    # File system tools
    def read_file(args: dict) -> str:
        """Read content of a file."""
        filepath = args.get("path", "")
        if not filepath:
            return "Error: No file path provided"
        
        try:
            # Security: restrict to allowed directories
            safe_paths = [str(Path.cwd()), str(Path.home())]
            abs_path = Path(filepath).resolve()
            
            allowed = any(str(abs_path).startswith(sp) for sp in safe_paths)
            if not allowed:
                return f"Error: Access denied to {filepath}"
            
            if not abs_path.exists():
                return f"Error: File not found: {filepath}"
            
            content = abs_path.read_text(encoding='utf-8', errors='ignore')
            # Limit output size
            if len(content) > 5000:
                content = content[:5000] + "\n... (truncated)"
            return content
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def write_file(args: dict) -> str:
        """Write content to a file."""
        filepath = args.get("path", "")
        content = args.get("content", "")
        
        if not filepath:
            return "Error: No file path provided"
        
        try:
            abs_path = Path(filepath).resolve()
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.write_text(content, encoding='utf-8')
            return f"Success: Written to {filepath}"
        except Exception as e:
            return f"Error writing file: {str(e)}"
    
    def list_directory(args: dict) -> str:
        """List files in a directory."""
        path = args.get("path", ".")
        
        try:
            abs_path = Path(path).resolve()
            if not abs_path.exists():
                return f"Error: Directory not found: {path}"
            
            items = []
            for item in abs_path.iterdir():
                suffix = "/" if item.is_dir() else ""
                items.append(f"{item.name}{suffix}")
            
            return "\n".join(items[:50])  # Limit to 50 items
        except Exception as e:
            return f"Error listing directory: {str(e)}"
    
    def search_web(args: dict) -> str:
        """Search the web using Wikipedia API and fallback searches."""
        query = args.get("query", "")
        if not query:
            return "Error: No search query provided"
        
        try:
            import requests
            from urllib.parse import quote
            
            # Try Wikipedia API first (most reliable)
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(query.replace(' ', '_'))}"
            headers = {'User-Agent': 'JARVIS/1.0'}
            resp = requests.get(wiki_url, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                title = data.get('title', '')
                extract = data.get('extract', '')
                if extract:
                    return f"Wikipedia - {title}:\n{extract[:500]}"
            
            # Try DuckDuckGo as fallback
            url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            resp = requests.get(url, headers=headers, timeout=15)
            
            import re
            pattern = r'<a class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, resp.text)
            
            if matches:
                output = []
                for url, title in matches[:5]:
                    title = re.sub(r'<[^>]+>', '', title).strip()
                    output.append(f"- {title}: {url}")
                return "Search Results:\n" + "\n".join(output)
            
            return "No search results found. Please try a more specific query."
        except Exception as e:
            return f"Search error: {str(e)}"
    
    def get_working_directory(args: dict) -> str:
        """Get current working directory."""
        return str(Path.cwd())
    
    # Simple in-memory storage for conversation context
    _memory_store = {}
    
    def remember(args: dict) -> str:
        """Remember something for future reference."""
        key = args.get("key", "")
        value = args.get("value", "")
        if not key or not value:
            return "Error: Both 'key' and 'value' are required"
        _memory_store[key] = value
        return f"Remembered: {key} = {value}"
    
    def recall(args: dict) -> str:
        """Recall something from memory."""
        key = args.get("key", "")
        if not key:
            return "Error: 'key' is required"
        value = _memory_store.get(key, f"No memory found for: {key}")
        return value
    
    def list_memories(args: dict) -> str:
        """List all remembered items."""
        if not _memory_store:
            return "No memories stored"
        return "\n".join([f"- {k}: {v}" for k, v in _memory_store.items()])
    
    def forget(args: dict) -> str:
        """Forget a specific memory."""
        key = args.get("key", "")
        if not key:
            return "Error: 'key' is required"
        if key in _memory_store:
            del _memory_store[key]
            return f"Forgotten: {key}"
        return f"No memory found for: {key}"
    
    # Register all tools
    registry.register("get_time", get_time, "Get the current time")
    registry.register("get_date", get_date, "Get the current date")
    registry.register("read_file", read_file, "Read content from a file")
    registry.register("write_file", write_file, "Write content to a file")
    registry.register("list_dir", list_directory, "List files in a directory")
    registry.register("search_web", search_web, "Search the web for information")
    registry.register("pwd", get_working_directory, "Get current working directory")
    registry.register("remember", remember, "Remember something (key, value)")
    registry.register("recall", recall, "Recall a remembered item by key")
    registry.register("list_memories", list_memories, "List all remembered items")
    registry.register("forget", forget, "Forget a specific memory")
    
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
