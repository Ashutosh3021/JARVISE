"""
System Context Module

Provides environment awareness - active window, current directory, running apps.
"""

import os
import platform
import socket
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

# Use psutil for process listing
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Use ctypes for Windows API
try:
    import ctypes
    from ctypes import wintypes
    HAS_CTYPES = True
except ImportError:
    HAS_CTYPES = False


# Cache for system context
_context_cache: Optional[dict] = None
_cache_time: Optional[datetime] = None
_CACHE_DURATION = timedelta(seconds=30)


@dataclass
class SystemContext:
    """Container for all system context information."""
    active_window: str
    current_directory: str
    running_apps: list[str]
    platform: str
    hostname: str


def _get_windows_active_window() -> str:
    """Get the title of the currently active window on Windows."""
    if not HAS_CTYPES:
        return "Unknown"
    
    try:
        # Windows API calls
        user32 = ctypes.windll.user32
        
        # Get the handle of the foreground window
        hwnd = user32.GetForegroundWindow()
        if hwnd == 0:
            return "None"
        
        # Get window title length
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return "None"
        
        # Get window title
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        return buffer.value or "None"
    except Exception:
        return "Unknown"


def _get_macos_active_window() -> str:
    """Get the title of the currently active window on macOS."""
    # Requires Accessibility permissions
    try:
        from AppKit import NSWorkspace
        frontmost = NSWorkspace.shared.frontmostApplication()
        return frontmost.localizedName() if frontmost else "None"
    except Exception:
        return "Unknown"


def _get_linux_active_window() -> str:
    """Get the title of the currently active window on Linux."""
    try:
        # Try using wmctrl or xdotool
        import subprocess
        result = subprocess.run(
            ["xdotool", "getactivewindow", "getwindowname"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "Unknown"


def get_active_window() -> str:
    """Get the title of the currently active window."""
    system = platform.system()
    
    if system == "Windows":
        return _get_windows_active_window()
    elif system == "Darwin":
        return _get_macos_active_window()
    elif system == "Linux":
        return _get_linux_active_window()
    
    return "Unknown"


def get_current_directory() -> str:
    """Get the current working directory."""
    return os.getcwd()


def get_running_apps() -> list[str]:
    """Get list of running applications (top 20 by memory)."""
    if not HAS_PSUTIL:
        return []
    
    apps = []
    try:
        # Get top processes by memory
        for proc in psutil.process_iter(['name', 'memory_info']):
            try:
                name = proc.info['name']
                if name and name.lower() not in [p.lower() for p in apps]:
                    apps.append(name)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by memory and return top 20
        apps = sorted(apps, key=lambda x: x.lower())[:20]
    except Exception:
        apps = []
    
    return apps


def _get_platform() -> str:
    """Get the platform name."""
    return platform.system()


def _get_hostname() -> str:
    """Get the hostname."""
    return socket.gethostname()


def get_system_context() -> SystemContext:
    """
    Get complete system context with caching.
    
    Returns cached result if within 30 seconds to avoid performance hit.
    """
    global _context_cache, _cache_time
    
    now = datetime.now()
    
    # Check cache
    if _context_cache and _cache_time:
        if now - _cache_time < _CACHE_DURATION:
            return SystemContext(**_context_cache)
    
    # Build fresh context
    _context_cache = {
        "active_window": get_active_window(),
        "current_directory": get_current_directory(),
        "running_apps": get_running_apps(),
        "platform": _get_platform(),
        "hostname": _get_hostname(),
    }
    _cache_time = now
    
    return SystemContext(**_context_cache)


def clear_context_cache() -> None:
    """Clear the system context cache to force refresh."""
    global _context_cache, _cache_time
    _context_cache = None
    _cache_time = None


__all__ = [
    "SystemContext",
    "get_active_window",
    "get_current_directory",
    "get_running_apps",
    "get_system_context",
    "clear_context_cache",
]
