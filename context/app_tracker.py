"""
App Tracker Module

Track and monitor running applications.
"""

import platform
import threading
import time
from collections import deque
from typing import Callable, Optional

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


class AppTracker:
    """
    Track and monitor running applications.
    
    Provides real-time monitoring of running apps with history
    and callbacks for app changes.
    """
    
    def __init__(self, poll_interval: float = 5.0):
        """
        Initialize the app tracker.
        
        Args:
            poll_interval: How often to poll for app changes (seconds)
        """
        self.poll_interval = poll_interval
        self._tracking = False
        self._thread: Optional[threading.Thread] = None
        self._history: deque[str] = deque(maxlen=50)
        self._previous_apps: set[str] = set()
        self._callbacks: list[Callable[[str, str], None]] = []
        
        # Current focused app
        self._focused_app: Optional[str] = None
    
    def start_tracking(self) -> None:
        """Begin monitoring running apps."""
        if self._tracking:
            return
        
        self._tracking = True
        self._previous_apps = self._get_current_apps()
        self._thread = threading.Thread(target=self._track_loop, daemon=True)
        self._thread.start()
    
    def stop_tracking(self) -> None:
        """Stop monitoring running apps."""
        self._tracking = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
    
    def _track_loop(self) -> None:
        """Background loop to track app changes."""
        while self._tracking:
            try:
                current_apps = self._get_current_apps()
                
                # Check for new apps
                new_apps = current_apps - self._previous_apps
                for app in new_apps:
                    self._history.append(app)
                    self._notify_callbacks("opened", app)
                
                # Check for closed apps
                closed_apps = self._previous_apps - current_apps
                for app in closed_apps:
                    self._notify_callbacks("closed", app)
                
                # Update focused app
                self._focused_app = self._get_focused_app_name()
                
                self._previous_apps = current_apps
                
            except Exception:
                pass
            
            time.sleep(self.poll_interval)
    
    def _get_current_apps(self) -> set[str]:
        """Get current set of running app names."""
        apps = set()
        
        if HAS_PSUTIL:
            try:
                for proc in psutil.process_iter(['name']):
                    try:
                        name = proc.info['name']
                        if name:
                            apps.add(name.lower())
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except Exception:
                pass
        
        return apps
    
    def _get_focused_app_name(self) -> Optional[str]:
        """Get the name of the currently focused app."""
        system = platform.system()
        
        if system == "Windows":
            return self._get_windows_focused_app()
        elif system == "Darwin":
            return self._get_macos_focused_app()
        elif system == "Linux":
            return self._get_linux_focused_app()
        
        return None
    
    def _get_windows_focused_app(self) -> Optional[str]:
        """Get focused app on Windows."""
        if not HAS_CTYPES:
            return None
        
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if hwnd == 0:
                return None
            
            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return None
            
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            return buffer.value or None
        except Exception:
            return None
    
    def _get_macos_focused_app(self) -> Optional[str]:
        """Get focused app on macOS."""
        try:
            from AppKit import NSWorkspace
            frontmost = NSWorkspace.shared.frontmostApplication()
            return frontmost.localizedName() if frontmost else None
        except Exception:
            return None
    
    def _get_linux_focused_app(self) -> Optional[str]:
        """Get focused app on Linux."""
        try:
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
        return None
    
    def _notify_callbacks(self, event: str, app_name: str) -> None:
        """Notify registered callbacks of app changes."""
        for callback in self._callbacks:
            try:
                callback(event, app_name)
            except Exception:
                pass
    
    def get_recent_apps(self, n: int = 10) -> list[str]:
        """
        Get recently opened apps.
        
        Args:
            n: Number of recent apps to return
            
        Returns:
            List of recently opened app names (most recent first)
        """
        return list(self._history)[-n:]
    
    def get_focused_app(self) -> Optional[str]:
        """
        Get the currently focused app.
        
        Returns:
            Name of the focused app or None
        """
        if self._focused_app is None:
            self._focused_app = self._get_focused_app_name()
        return self._focused_app
    
    def is_app_running(self, name: str) -> bool:
        """
        Check if a specific app is running.
        
        Args:
            name: App name to check (case-insensitive)
            
        Returns:
            True if the app is running
        """
        current_apps = self._get_current_apps()
        return name.lower() in current_apps
    
    def on_app_change(self, callback: Callable[[str, str], None]) -> None:
        """
        Register a callback for app changes.
        
        Args:
            callback: Function called with (event, app_name)
                     event is "opened" or "closed"
        """
        self._callbacks.append(callback)
    
    def get_all_running(self) -> list[str]:
        """
        Get list of all currently running apps.
        
        Returns:
            Sorted list of running app names
        """
        apps = list(self._get_current_apps())
        return sorted(apps)


# Global tracker instance
_tracker: Optional[AppTracker] = None


def get_app_tracker() -> AppTracker:
    """
    Get the global AppTracker instance.
    
    Returns:
        Shared AppTracker instance
    """
    global _tracker
    if _tracker is None:
        _tracker = AppTracker()
    return _tracker


__all__ = [
    "AppTracker",
    "get_app_tracker",
]
