"""
JARVIS Brain Layer - Tool Registry Module

Manages tool registration, risk classification, and HITL enforcement.
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from loguru import logger

from tools.base import ConfirmationRequest, RiskLevel
from brain.hitl import ask_confirmation, get_undo_tracker
from brain.audit import get_audit_log


class ToolExecutionError(Exception):
    """Raised when tool execution fails."""
    pass


class RetryEngine:
    """Engine for retrying failed tool calls with alternative approaches."""
    
    MAX_RETRIES = 3
    
    def __init__(self):
        self.cache: dict[str, dict] = {}
        self.cache_file = Path("./data/tool_cache.json")
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load tool cache from JSON file."""
        if self.cache_file.exists():
            try:
                self.cache = json.loads(self.cache_file.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, IOError):
                self.cache = {}
    
    def _save_cache(self) -> None:
        """Save tool cache to JSON file."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(
            json.dumps(self.cache, indent=2),
            encoding='utf-8'
        )
    
    def get_alternatives(self, tool_name: str, error: str) -> list[dict]:
        """
        Generate alternative approaches for a failed tool call.
        
        Args:
            tool_name: Name of the tool that failed
            error: Error message from the failed call
            
        Returns:
            List of alternative approaches to try
        """
        alternatives = []
        
        # Parse error to determine retry strategy
        error_lower = error.lower()
        
        # "File not found" - try variations of the path
        if "not found" in error_lower or "no such file" in error_lower:
            # Extract potential path from args if available
            alternatives.append({"strategy": "search_similar", "description": "Search for similar filename"})
        
        # "Permission denied" - try alternative locations
        if "permission" in error_lower or "access denied" in error_lower:
            alternatives.append({"strategy": "alt_location", "description": "Try alternative location"})
        
        # "Command not found" - try from PATH
        if "command not found" in error_lower or "not recognized" in error_lower:
            alternatives.append({"strategy": "from_path", "description": "Try command from system PATH"})
        
        # Default alternatives
        if not alternatives:
            alternatives.append({"strategy": "retry", "description": "Retry with same args"})
        
        return alternatives[:self.MAX_RETRIES]
    
    def record_success(self, tool_name: str, args: dict, result: str) -> None:
        """Record successful tool execution."""
        cache_key = f"{tool_name}:{hash(str(args))}"
        if cache_key not in self.cache:
            self.cache[cache_key] = {}
        
        self.cache[cache_key].update({
            "tool_name": tool_name,
            "args_hash": hash(str(args)),
            "result": result[:500],  # Truncate long results
            "timestamp": datetime.now().isoformat(),
            "success": True
        })
        self._save_cache()
    
    def record_failure(self, tool_name: str, args: dict, error: str) -> None:
        """Record failed tool execution."""
        cache_key = f"{tool_name}:{hash(str(args))}"
        if cache_key not in self.cache:
            self.cache[cache_key] = {}
        
        self.cache[cache_key].update({
            "tool_name": tool_name,
            "args_hash": hash(str(args)),
            "error": error[:500],
            "timestamp": datetime.now().isoformat(),
            "success": False
        })
        self._save_cache()
    
    def get_last_working(self, tool_name: str) -> dict | None:
        """Get the last successful approach for a tool."""
        for key, entry in self.cache.items():
            if entry.get("tool_name") == tool_name and entry.get("success"):
                return entry
        return None
    
    def get_stats(self) -> dict:
        """Get retry engine statistics."""
        total = len(self.cache)
        successful = sum(1 for e in self.cache.values() if e.get("success"))
        return {
            "total_entries": total,
            "successful": successful,
            "failed": total - successful
        }


class ToolRegistry:
    """Registry for managing and executing tools."""

    def __init__(self, use_cache: bool = True, use_retry: bool = True):
        self.tools: dict[str, dict[str, Any]] = {}
        self._action_pattern = re.compile(
            r"^Action:\s*(\w+)(?:\s*:\s*(\{[\s\S]+?\}|\[[\s\S]+?\]))?",
            re.MULTILINE | re.IGNORECASE
        )
        self._thought_pattern = re.compile(
            r"^Thought:\s*(.+?)(?=\nAction:|\n\n|\Z)",
            re.MULTILINE | re.DOTALL
        )
        
        self._use_retry = use_retry
        self._retry_engine = None
        
        if self._use_retry:
            self._retry_engine = RetryEngine()

    def register(
        self,
        name: str,
        func: Callable[..., Any],
        description: str = "",
        parameter_schema: dict | None = None,
        risk_level: RiskLevel | str = RiskLevel.GREEN,
    ) -> None:
        """Register a tool with the registry."""
        if isinstance(risk_level, str):
            risk_level = RiskLevel(risk_level)
        
        self.tools[name.lower()] = {
            "func": func,
            "desc": description,
            "schema": parameter_schema,
            "risk_level": risk_level,
        }
        logger.debug(f"Registered tool: {name} (risk={risk_level.value})")

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
        """Get formatted string of tool schemas for prompt (includes risk levels)."""
        if not self.tools:
            return "No tools available."
        
        lines = ["Available tools:"]
        for name, info in self.tools.items():
            desc = info.get("desc", "No description")
            risk = info.get("risk_level", RiskLevel.GREEN)
            risk_tag = f" [{risk.value.upper()}]" if risk != RiskLevel.GREEN else ""
            lines.append(f"- {name}{risk_tag}: {desc}")
        return "\n".join(lines)

    def execute(self, name: str, args: dict[str, Any] | str | None = None) -> str:
        """Execute a registered tool with HITL enforcement and audit logging."""
        name_lower = name.lower()
        
        if name_lower not in self.tools:
            return f"Error: Unknown tool '{name}'. Available tools: {', '.join(self.tools.keys())}"
        
        tool = self.tools[name_lower]
        func = tool["func"]
        risk_level = tool.get("risk_level", RiskLevel.GREEN)
        
        # Normalize args to dict
        normalized_args = {}
        if args is None:
            normalized_args = {}
        elif isinstance(args, dict):
            normalized_args = args
        elif isinstance(args, str):
            if args.startswith('{') or args.startswith('['):
                try:
                    normalized_args = json.loads(args)
                except Exception:
                    normalized_args = {}
            else:
                normalized_args = {}
        
        # === HITL ENFORCEMENT ===
        # RED actions: always require confirmation, no auto-execute
        if risk_level == RiskLevel.RED:
            action_desc = f"Execute {name} with args: {normalized_args}"
            granted = ask_confirmation(action_desc, risk_level="red")
            
            get_audit_log().log_confirmation(
                tool_name=name, action=action_desc,
                risk_level="red", granted=granted,
            )
            
            if not granted:
                return f"Action '{name}' denied by user."
        
        # YELLOW actions: require confirmation
        elif risk_level == RiskLevel.YELLOW:
            action_desc = f"Execute {name} with args: {normalized_args}"
            granted = ask_confirmation(action_desc, risk_level="yellow")
            
            get_audit_log().log_confirmation(
                tool_name=name, action=action_desc,
                risk_level="yellow", granted=granted,
            )
            
            if not granted:
                return f"Action '{name}' denied by user."
        
        # GREEN actions: auto-execute, just log
        
        # === EXECUTION ===
        try:
            result = func(normalized_args)
            result_str = str(result) if result is not None else "Done"
            logger.debug(f"Tool '{name}' executed: {result_str}")
            
            # Audit log
            get_audit_log().log_tool_execution(
                tool_name=name, action=f"execute {name}",
                risk_level=risk_level.value, args=normalized_args,
                result=result_str,
            )
            
            # Record success for learning
            if self._retry_engine:
                self._retry_engine.record_success(name, normalized_args, result_str)
            
            return result_str
        except ConfirmationRequest as e:
            # Tool itself raised confirmation (legacy path)
            details = f" {e.details}" if e.details else ""
            return (
                f"Confirmation required for tool '{e.tool_name}' action '{e.action}'.{details} "
                "Ask the user to confirm, then retry with confirmation if supported."
            )
        except Exception as e:
            error_msg = f"Tool '{name}' failed: {str(e)}"
            logger.error(error_msg)
            
            # Audit log failure
            get_audit_log().log_tool_execution(
                tool_name=name, action=f"execute {name}",
                risk_level=risk_level.value, args=normalized_args,
                result=f"ERROR: {e}",
            )
            
            # Record failure for learning
            if self._retry_engine:
                self._retry_engine.record_failure(name, normalized_args, str(e))
            
            # Try alternatives if retry is enabled
            if self._retry_engine and self._use_retry:
                alternatives = self._retry_engine.get_alternatives(name, str(e))
                for attempt in alternatives:
                    logger.info(f"Retrying with alternative: {attempt.get('description')}")
                    try:
                        result = func(normalized_args)
                        result_str = str(result) if result is not None else "Done"
                        logger.info(f"Alternative succeeded: {result_str}")
                        if self._retry_engine:
                            self._retry_engine.record_success(name, normalized_args, result_str)
                        return result_str
                    except Exception:
                        continue
            
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
    
    def get_retry_stats(self) -> dict | None:
        """Get retry engine statistics.
        
        Returns:
            Dict with retry stats or None if retry not enabled
        """
        if self._retry_engine is None:
            return None
        return self._retry_engine.get_stats()


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
            safe_paths = [str(Path.cwd()), str(Path.home())]
            abs_path = Path(filepath).resolve()
            allowed = any(str(abs_path).startswith(sp) for sp in safe_paths)
            if not allowed:
                return f"Error: Access denied to {filepath}"
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
        """Search the web using duckduckgo-search package."""
        query = args.get("query", "")
        if not query:
            return "Error: No search query provided"
        
        try:
            # BUG-018 fix: Use duckduckgo-search package instead of HTML scraping
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
                if results:
                    output = []
                    for r in results[:5]:
                        output.append(f"- {r['title']}: {r['href']}")
                    return "Search Results:\n" + "\n".join(output)
            return "No search results found."
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


# Lazy-initialized heavy tool instances (BUG-011 fix)
_browser = None
_web_search_tool = None
_filesystem = None
_code_exec = None
_google_calendar = None
_google_email = None
_microsoft_outlook = None
_system_monitor = None

# Simple in-memory storage for conversation context (shared across registries)
_memory_store = {}


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
    import os
    
    registry = ToolRegistry()
    
    # === HEAVY TOOLS (lazy-initialized) ===
    
    # Register browser tool
    def execute_browser(args: dict) -> str:
        """Execute browser tool action."""
        global _browser
        if _browser is None:
            from tools.browser import BrowserTool
            _browser = BrowserTool()
        action = args.get("action", "navigate")
        # Pass all kwargs except action
        clean_args = {k: v for k, v in args.items() if k != "action"}
        return _browser.execute(action=action, **clean_args)
    
    registry.register(
        "browser",
        execute_browser,
        "Browser automation: navigate, extract, click, fill, screenshot, tabs",
        risk_level=RiskLevel.GREEN,
    )
    
    # Register research workflow tool
    def execute_research(args: dict) -> str:
        """Execute multi-step research workflow."""
        global _browser
        if _browser is None:
            from tools.browser import BrowserTool
            _browser = BrowserTool()
        
        from brain.research import ResearchWorkflow
        workflow = ResearchWorkflow(browser_tool=_browser)
        
        action = args.get("action", "research")
        
        if action == "research":
            query = args.get("query", "")
            if not query:
                return "Error: 'query' required"
            max_sources = args.get("max_sources", 3)
            engine = args.get("engine", "duckduckgo")
            result = workflow.research(query, max_sources=max_sources, engine=engine)
            return result.format_with_citations()
        
        elif action == "quick":
            query = args.get("query", "")
            if not query:
                return "Error: 'query' required"
            return workflow.quick_research(query)
        
        else:
            return f"Unknown research action: {action}. Use 'research' or 'quick'"
    
    registry.register(
        "research",
        execute_research,
        "Multi-step research: search, extract sources, compile with citations",
        risk_level=RiskLevel.GREEN,
    )
    
    # Register web search tool
    def execute_search(args: dict) -> str:
        """Execute web search using duckduckgo-search directly."""
        query = args.get("query", "")
        if not query:
            return "Error: No search query provided"
        
        try:
            from duckduckgo_search import DDGS
            
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5, backend='bing'))
                if results:
                    output = []
                    for r in results:
                        title = r.get('title', 'No title')
                        url = r.get('href', r.get('url', ''))
                        body = r.get('body', r.get('snippet', ''))
                        output.append(f"- {title}: {url}\n  {body[:100]}...")
                    return "Search Results:\n" + "\n".join(output)
            return "No search results found."
        except ImportError as e:
            return f"Error: duckduckgo-search not installed. Install with: pip install duckduckgo-search"
        except Exception as e:
            return f"Search error: {str(e)}"
    
    registry.register(
        "web_search",
        execute_search,
        "Search the web using duckduckgo-search API",
        risk_level=RiskLevel.GREEN,
    )
    
    # Register filesystem tool
    def execute_filesystem(args: dict) -> str:
        """Execute filesystem operation."""
        global _filesystem
        if _filesystem is None:
            from tools.filesystem import FilesystemTool
            _filesystem = FilesystemTool()
        action = args.get("action", "list")
        path = args.get("path", ".")
        clean_args = {k: v for k, v in args.items() if k not in ("action", "path")}
        return _filesystem.execute(action=action, path=path, **clean_args)
    
    registry.register(
        "filesystem",
        execute_filesystem,
        "Read, write, delete files. Write/delete requires confirmation.",
        risk_level=RiskLevel.YELLOW,
    )
    
    # Register code execution sandbox
    _sandbox = None
    
    def execute_code(args: dict) -> str:
        """Execute code in sandbox."""
        nonlocal _sandbox
        if _sandbox is None:
            from brain.sandbox import CodeSandbox
            _sandbox = CodeSandbox()
        
        action = args.get("action", "python")
        confirm = args.get("confirm", False)
        
        if action == "python":
            code = args.get("code", "")
            if not code:
                return "Error: 'code' required"
            result = _sandbox.run_python(code, confirm=confirm)
        elif action == "shell":
            command = args.get("command", "")
            if not command:
                return "Error: 'command' required"
            result = _sandbox.run_shell(command, confirm=confirm)
        elif action == "install":
            package = args.get("package", "")
            if not package:
                return "Error: 'package' required"
            result = _sandbox.install_package(package, confirm=confirm)
        elif action == "diff":
            file_path = args.get("file_path", "")
            new_content = args.get("new_content", "")
            if not file_path or not new_content:
                return "Error: 'file_path' and 'new_content' required"
            preview = _sandbox.preview_diff(file_path, new_content)
            return json.dumps(preview.to_dict(), indent=2)
        elif action == "apply":
            file_path = args.get("file_path", "")
            new_content = args.get("new_content", "")
            if not file_path or not new_content:
                return "Error: 'file_path' and 'new_content' required"
            preview = _sandbox.preview_diff(file_path, new_content)
            result = _sandbox.apply_diff(preview, confirm=confirm)
        elif action == "history":
            limit = args.get("limit", 10)
            records = _sandbox.get_history(limit)
            return json.dumps(records, indent=2)
        elif action == "replay":
            record_id = args.get("record_id", "")
            if not record_id:
                return "Error: 'record_id' required"
            result = _sandbox.replay(record_id, confirm=confirm)
        elif action == "packages":
            pkgs = _sandbox.get_installed_packages()
            return "Installed: " + ", ".join(pkgs) if pkgs else "No packages installed"
        else:
            return f"Unknown action: {action}. Use: python, shell, install, diff, apply, history, replay, packages"
        
        # Format result
        if result.get("status") == "error":
            return f"Error: {result.get('error', 'Unknown error')}"
        output = result.get("output", "")
        duration = result.get("duration_ms", 0)
        return f"{output}\n({duration:.0f}ms)" if duration else output
    
    registry.register(
        "execute_code",
        execute_code,
        "Sandboxed code execution: python, shell, pip install, diff preview, history",
        risk_level=RiskLevel.RED,
    )
    
    # Register Google Calendar tool
    def execute_calendar(args: dict) -> str:
        """Execute Google Calendar operation."""
        global _google_calendar
        if _google_calendar is None:
            from tools.google_calendar import GoogleCalendarTool
            _google_calendar = GoogleCalendarTool()
        action = args.get("action", "list_events")
        clean_args = {k: v for k, v in args.items() if k != "action"}
        return _google_calendar.execute(action=action, **clean_args)
    
    registry.register(
        "google_calendar",
        execute_calendar,
        "List, create, update Google Calendar events",
        risk_level=RiskLevel.YELLOW,
    )
    
    # Register Google Email tool
    def execute_gmail(args: dict) -> str:
        """Execute Google Email operation."""
        global _google_email
        if _google_email is None:
            from tools.google_email import GoogleEmailTool
            _google_email = GoogleEmailTool()
        action = args.get("action", "list_emails")
        clean_args = {k: v for k, v in args.items() if k != "action"}
        return _google_email.execute(action=action, **clean_args)
    
    registry.register(
        "google_email",
        execute_gmail,
        "Read, send Google Email messages",
        risk_level=RiskLevel.YELLOW,
    )
    
    # Register Microsoft Outlook tool
    def execute_outlook(args: dict) -> str:
        """Execute Microsoft Outlook operation."""
        global _microsoft_outlook
        if _microsoft_outlook is None:
            from tools.microsoft_outlook import MicrosoftOutlookTool
            _microsoft_outlook = MicrosoftOutlookTool()
        action = args.get("action", "list_emails")
        clean_args = {k: v for k, v in args.items() if k != "action"}
        return _microsoft_outlook.execute(action=action, **clean_args)
    
    registry.register(
        "outlook",
        execute_outlook,
        "Read, send Microsoft Outlook emails via Microsoft Graph",
        risk_level=RiskLevel.YELLOW,
    )
    
    # Register system monitor tool
    def execute_monitor(args: dict) -> str:
        """Execute system monitoring."""
        global _system_monitor
        if _system_monitor is None:
            from tools.system_monitor import SystemMonitorTool
            _system_monitor = SystemMonitorTool()
        action = args.get("action", "all")
        clean_args = {k: v for k, v in args.items() if k != "action"}
        return _system_monitor.execute(action=action, **clean_args)
    
    registry.register(
        "system_monitor",
        execute_monitor,
        "Get CPU, memory, disk, network statistics",
        risk_level=RiskLevel.GREEN,
    )
    
    # === BASIC TOOLS (BUG-015 fix: add missing memory tools) ===
    
    def get_time(args: dict) -> str:
        from datetime import datetime
        return datetime.now().strftime("%I:%M %p")
    
    def get_date(args: dict) -> str:
        from datetime import datetime
        return datetime.now().strftime("%A, %B %d, %Y")
    
    def get_working_directory(args: dict) -> str:
        from pathlib import Path
        return str(Path.cwd())
    
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
    
    # Register basic tools
    registry.register("get_time", get_time, "Get the current time")
    registry.register("get_date", get_date, "Get the current date")
    registry.register("pwd", get_working_directory, "Get current working directory")
    registry.register("remember", remember, "Remember something (key, value)")
    registry.register("recall", recall, "Recall a remembered item by key")
    registry.register("list_memories", list_memories, "List all remembered items")
    registry.register("forget", forget, "Forget a specific memory")
    
    # === CALENDAR & EMAIL ORCHESTRATOR ===
    
    _cal_email_orchestrator = None
    
    def execute_calendar_email(args: dict) -> str:
        """Execute calendar/email orchestrator action."""
        nonlocal _cal_email_orchestrator
        if _cal_email_orchestrator is None:
            from brain.calendar_email import CalendarEmailOrchestrator
            _cal_email_orchestrator = CalendarEmailOrchestrator()
        
        action = args.get("action", "status")
        
        if action == "triage_emails":
            messages = args.get("messages", [])
            if not messages:
                return "Error: 'messages' list required for triage"
            result = _cal_email_orchestrator.triage_emails(messages)
            lines = []
            for priority, items in result.items():
                if items:
                    lines.append(f"\n{priority.upper()} ({len(items)}):")
                    for item in items:
                        lines.append(f"  - {item.subject} (from: {item.sender})")
                        lines.append(f"    Reason: {item.reason}")
            return "\n".join(lines) if lines else "No emails to triage"
        
        elif action == "draft_reply":
            to = args.get("to", "")
            subject = args.get("subject", "")
            context = args.get("context", "")
            tone = args.get("tone", "professional")
            if not all([to, subject, context]):
                return "Error: 'to', 'subject', and 'context' required"
            draft = _cal_email_orchestrator.draft_reply(to, subject, context, tone)
            return (
                f"Draft created (pending approval):\n"
                f"To: {draft.to}\n"
                f"Subject: {draft.subject}\n"
                f"Body:\n{draft.body}"
            )
        
        elif action == "check_conflicts":
            events = args.get("events", [])
            new_event = args.get("new_event")
            conflicts = _cal_email_orchestrator.check_calendar_conflicts(events, new_event)
            if not conflicts:
                return "No conflicts found"
            lines = ["Conflicts detected:"]
            for c in conflicts:
                lines.append(f"  - {c.suggestion}")
            return "\n".join(lines)
        
        elif action == "suggest_times":
            events = args.get("events", [])
            duration = args.get("duration_minutes", 60)
            slots = _cal_email_orchestrator.suggest_meeting_times(events, duration)
            if not slots:
                return "No available slots found in the next 3 days"
            lines = ["Suggested meeting times:"]
            for s in slots:
                lines.append(f"  - {s['day']} at {s['time']}")
            return "\n".join(lines)
        
        elif action == "status":
            drafts = _cal_email_orchestrator.get_pending_drafts()
            return (
                f"Calendar/Email Orchestrator Status:\n"
                f"  Pending drafts: {len(drafts)}"
            )
        
        else:
            return f"Unknown action: {action}. Use: triage_emails, draft_reply, check_conflicts, suggest_times, status"
    
    registry.register(
        "calendar_email",
        execute_calendar_email,
        "Calendar & email orchestrator: triage emails, draft replies, check conflicts, suggest meeting times",
        risk_level=RiskLevel.YELLOW,
    )
    
    return registry


__all__ = ["ToolRegistry", "ToolExecutionError", "create_default_registry", "create_tools_registry"]
