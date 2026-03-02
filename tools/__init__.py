# JARVIS Tools Module
# System tool integrations

from tools.base import BaseTool, ToolError, execute_with_error_handling
from tools.browser import BrowserTool, BrowserManager
from tools.web_search import WebSearchTool
from tools.filesystem import FilesystemTool
from tools.code_exec import CodeExecutionTool
from tools.google_calendar import GoogleCalendarTool
from tools.google_email import GoogleEmailTool
from tools.microsoft_outlook import MicrosoftOutlookTool, EmailMessage, CalendarEvent
from tools.system_monitor import SystemMonitorTool, CPUStats, MemoryStats, DiskStats, NetworkStats
from tools.auth import TokenManager, GoogleOAuth
from tools.auth.microsoft import MicrosoftAuth

__all__ = [
    # Base classes
    "BaseTool",
    "ToolError",
    "execute_with_error_handling",
    # Core tools
    "BrowserTool",
    "BrowserManager",
    "WebSearchTool",
    "FilesystemTool",
    "CodeExecutionTool",
    # Google tools
    "GoogleCalendarTool",
    "GoogleEmailTool",
    # Microsoft tools
    "MicrosoftOutlookTool",
    "MicrosoftAuth",
    # Data classes
    "EmailMessage",
    "CalendarEvent",
    # System monitor
    "SystemMonitorTool",
    "CPUStats",
    "MemoryStats",
    "DiskStats",
    "NetworkStats",
    # Auth
    "TokenManager",
    "GoogleOAuth",
]


def create_tools_registry():
    """Create and return a tools registry with all tools registered.
    
    Returns:
        ToolRegistry with all JARVIS tools
    """
    from brain.tools import create_tools_registry as _create
    return _create()
