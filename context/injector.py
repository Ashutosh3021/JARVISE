"""
Context Injector Module

Injects system context into prompts for smarter AI responses.
"""

from typing import Any, Union

from context.app_tracker import AppTracker, get_app_tracker
from context.project_detector import ProjectInfo, detect_project
from context.system_context import SystemContext, get_system_context


class ContextInjector:
    """
    Injects environment context into prompts.
    
    Provides automatic context about the working directory,
    project type, running apps, and git status.
    """
    
    def __init__(
        self,
        system_context: SystemContext | None = None,
        project_detector: ProjectInfo | None = None,
        app_tracker: AppTracker | None = None,
    ):
        """
        Initialize the context injector.
        
        Args:
            system_context: System context instance (will create if None)
            project_detector: Project info instance (will create if None)
            app_tracker: App tracker instance (will create if None)
        """
        self._system_context = system_context
        self._project_info = project_detector
        self._app_tracker = app_tracker
    
    @property
    def system_context(self) -> SystemContext:
        """Get or create system context."""
        if self._system_context is None:
            self._system_context = get_system_context()
        return self._system_context
    
    @property
    def project_info(self) -> ProjectInfo:
        """Get or create project info."""
        if self._project_info is None:
            self._project_info = detect_project()
        return self._project_info
    
    @property
    def app_tracker(self) -> AppTracker:
        """Get or create app tracker."""
        if self._app_tracker is None:
            self._app_tracker = get_app_tracker()
        return self._app_tracker
    
    def get_context_summary(self) -> str:
        """
        Get formatted context summary string.
        
        Returns:
            Formatted string with all context information
        """
        parts = ["Current Context:"]
        
        # Working directory and project
        project = self.project_info
        parts.append(f"- Working Directory: {project.project_root}")
        
        if project.language != "unknown":
            project_desc = project.language
            if project.framework:
                project_desc += f" ({project.framework})"
            parts.append(f"- Project: {project_desc}")
        
        # Test command
        if project.test_command:
            parts.append(f"- Test Command: {project.test_command}")
        
        # Git status
        if project.has_git:
            git_info = f"- Git Branch: {project.git_branch or 'unknown'}"
            if project.git_modified:
                git_info += f" ({len(project.git_modified)} files modified)"
            parts.append(git_info)
        
        # Active window
        sys_ctx = self.system_context
        if sys_ctx.active_window and sys_ctx.active_window != "None":
            parts.append(f"- Active Window: {sys_ctx.active_window}")
        
        # Running apps (top 5)
        if sys_ctx.running_apps:
            apps = sys_ctx.running_apps[:5]
            apps_str = ", ".join(apps)
            if len(sys_ctx.running_apps) > 5:
                apps_str += f", +{len(sys_ctx.running_apps) - 5} more"
            parts.append(f"- Running Apps: [{apps_str}]")
        
        # Platform
        parts.append(f"- Platform: {sys_ctx.platform}")
        
        return "\n".join(parts)
    
    def get_context_dict(self) -> dict[str, Any]:
        """
        Get raw context dictionary for debugging.
        
        Returns:
            Dictionary with all context data
        """
        project = self.project_info
        sys_ctx = self.system_context
        
        return {
            "working_directory": project.project_root,
            "project": {
                "language": project.language,
                "framework": project.framework,
                "test_command": project.test_command,
                "build_command": project.build_command,
            },
            "git": {
                "has_git": project.has_git,
                "branch": project.git_branch,
                "modified_files": project.git_modified,
            },
            "system": {
                "active_window": sys_ctx.active_window,
                "running_apps": sys_ctx.running_apps,
                "platform": sys_ctx.platform,
                "hostname": sys_ctx.hostname,
            },
        }
    
    def inject_context(
        self,
        prompt_or_messages: Union[str, list[dict[str, str]]],
    ) -> Union[str, list[dict[str, str]]]:
        """
        Inject context into a prompt or messages list.
        
        Args:
            prompt_or_messages: Either a string prompt or list of message dicts
            
        Returns:
            Same type as input, with context injected
        """
        context_block = self.get_context_summary()
        
        if isinstance(prompt_or_messages, str):
            # String prompt - prepend context
            return f"""{context_block}

{prompt_or_messages}"""
        
        # List of messages - inject as system message after existing system
        if not prompt_or_messages:
            return prompt_or_messages
        
        # Find position to insert context (after existing system messages)
        insert_index = 0
        for i, msg in enumerate(prompt_or_messages):
            if msg.get("role") == "system":
                insert_index = i + 1
        
        # Create context message
        context_msg = {
            "role": "system",
            "content": context_block,
        }
        
        # Insert after system messages
        result = prompt_or_messages.copy()
        result.insert(insert_index, context_msg)
        
        return result
    
    def refresh(self) -> None:
        """Refresh all context data."""
        from context.system_context import clear_context_cache
        clear_context_cache()
        self._system_context = get_system_context()
        self._project_info = detect_project()


def inject_context(
    prompt_or_messages: Union[str, list[dict[str, str]]],
) -> Union[str, list[dict[str, str]]]:
    """
    Quick helper to inject context.
    
    Creates a temporary ContextInjector and uses it to inject context.
    
    Args:
        prompt_or_messages: Either a string prompt or list of message dicts
        
    Returns:
        Same type as input, with context injected
    """
    injector = ContextInjector()
    return injector.inject_context(prompt_or_messages)


__all__ = [
    "ContextInjector",
    "inject_context",
]
