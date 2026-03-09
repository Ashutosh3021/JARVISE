"""
JARVIS Context Engine

Automatic environment awareness - knows directory, project, apps without asking.
"""

from context.system_context import (
    SystemContext,
    get_active_window,
    get_current_directory,
    get_running_apps,
    get_system_context,
)

from context.project_detector import (
    ProjectInfo,
    detect_project,
    get_test_command,
    get_project_root,
    has_git_repo,
    get_git_status,
)

from context.app_tracker import (
    AppTracker,
    get_app_tracker,
)

from context.injector import (
    ContextInjector,
    inject_context,
)

__all__ = [
    # System context
    "SystemContext",
    "get_active_window",
    "get_current_directory",
    "get_running_apps",
    "get_system_context",
    # Project detector
    "ProjectInfo",
    "detect_project",
    "get_test_command",
    "get_project_root",
    "has_git_repo",
    "get_git_status",
    # App tracker
    "AppTracker",
    "get_app_tracker",
    # Context injector
    "ContextInjector",
    "inject_context",
]
