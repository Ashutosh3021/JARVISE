"""
JARVIS Tools - Filesystem

Filesystem manipulation tool with path expansion and confirmation requests.
Per user decision: user confirms each write/delete, expand ~ to home.
"""

import os
from pathlib import Path
from typing import Any

from loguru import logger

from tools.base import BaseTool, ToolError, ConfirmationRequest, execute_with_error_handling


class FilesystemTool(BaseTool):
    """Filesystem manipulation tool.
    
    Per user decision:
    - User confirms each write/delete
    - Expand ~ to user home directory on Windows
    - Path validation to prevent traversal attacks
    """
    
    # Blocked paths for security
    BLOCKED_PATHS = [
        "C:\\Windows",
        "C:\\Program Files",
        "C:\\Program Files (x86)",
        "/etc",
        "/usr",
        "/bin",
        "/sbin",
    ]
    
    def __init__(self, allowed_dirs: list[str] | None = None):
        """Initialize filesystem tool.
        
        Args:
            allowed_dirs: Optional list of allowed directories (if set, restricts access)
        """
        super().__init__(name="FilesystemTool")
        
        self.home = Path.home()
        self.allowed_dirs = allowed_dirs
        
        # Default to allowing access within user's home
        if allowed_dirs is None:
            self.allowed_dirs = [str(self.home)]
    
    def expand_path(self, path: str) -> Path:
        """Expand ~ to user home directory.
        
        Per user decision: expand ~ to home on Windows.
        
        Args:
            path: Path that may contain ~
            
        Returns:
            Expanded Path object
        """
        if not path:
            raise ToolError("FilesystemTool", "Empty path provided", "Provide a valid path")
        
        # Expand ~ to home directory
        if path.startswith("~"):
            # Handle both ~/ and ~\\ cases first (more specific)
            if path.startswith("~/") or path.startswith("~\\"):
                expanded = str(self.home) + path[1:]
            elif len(path) == 1:
                # Just ~ by itself
                expanded = str(self.home)
            else:
                # ~ followed by something but no separator
                # This could be like ~test which means ~test (a directory named test in root)
                # But for Windows, we want to treat it as home directory
                expanded = str(self.home)
            path = expanded
        
        # Also handle os.path.expanduser for cross-platform
        expanded = Path(os.path.expanduser(path))
        
        # Resolve to absolute path
        resolved = expanded.resolve()
        
        self.logger.debug(f"Expanded path: {path} -> {resolved}")
        return resolved
    
    def _validate_path(self, path: Path) -> None:
        """Validate path for security.
        
        Checks for:
        - Path traversal attempts
        - Blocked system paths
        - Access outside allowed directories
        
        Args:
            path: Path to validate
            
        Raises:
            ToolError: If path is not allowed
        """
        # Check for path traversal patterns
        path_str = str(path)
        if ".." in path.parts:
            raise ToolError(
                "FilesystemTool",
                "Path traversal not allowed",
                "Do not use '..' in paths"
            )
        
        # Check blocked paths
        for blocked in self.BLOCKED_PATHS:
            if path_str.lower().startswith(blocked.lower()):
                raise ToolError(
                    "FilesystemTool",
                    f"Access to system path not allowed: {blocked}",
                    "Choose a different directory"
                )
        
        # Check allowed directories
        if self.allowed_dirs:
            allowed = False
            for allowed_dir in self.allowed_dirs:
                try:
                    path.relative_to(Path(allowed_dir))
                    allowed = True
                    break
                except ValueError:
                    continue
            
            if not allowed:
                raise ToolError(
                    "FilesystemTool",
                    f"Path outside allowed directories: {path}",
                    f"Allowed: {', '.join(self.allowed_dirs)}"
                )
    
    def read_file(self, path: str, ask_confirmation: bool = True) -> str:
        """Read file content.
        
        Args:
            path: File path to read
            ask_confirmation: Whether to ask for confirmation (default True for consistency)
            
        Returns:
            File content as string
            
        Raises:
            ToolError: If file cannot be read
        """
        expanded_path = self.expand_path(path)
        self._validate_path(expanded_path)
        
        def do_read():
            if not expanded_path.exists():
                raise ToolError(
                    "FilesystemTool",
                    f"File does not exist: {expanded_path}",
                    "Verify the file path"
                )
            
            if expanded_path.is_dir():
                raise ToolError(
                    "FilesystemTool",
                    f"Path is a directory, not a file: {expanded_path}",
                    "Provide a file path"
                )
            
            return expanded_path.read_text(encoding="utf-8")
        
        content = execute_with_error_handling(self.name, do_read)
        self.logger.info(f"Read file: {expanded_path}")
        return content
    
    def write_file(self, path: str, content: str, ask_confirmation: bool = True) -> str:
        """Write content to file.
        
        Per user decision: user confirms each write.
        
        Args:
            path: File path to write
            content: Content to write
            ask_confirmation: Whether to ask for confirmation (always True per user decision)
            
        Returns:
            Success message
            
        Raises:
            ConfirmationRequest: If user confirmation is required
            ToolError: If file cannot be written
        """
        expanded_path = self.expand_path(path)
        self._validate_path(expanded_path)
        
        # Per user decision: always request confirmation for write
        if ask_confirmation:
            raise ConfirmationRequest(
                tool_name=self.name,
                action="write",
                details=f"Write to file: {expanded_path}\nSize: {len(content)} bytes"
            )
        
        def do_write():
            # Create parent directories if needed
            expanded_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            expanded_path.write_text(content, encoding="utf-8")
            return f"Written to {expanded_path}"
        
        result = execute_with_error_handling(self.name, do_write)
        self.logger.info(f"Wrote file: {expanded_path}")
        return result
    
    def write_fileConfirmed(self, path: str, content: str) -> str:
        """Write content to file (after user confirmation).
        
        This method should be called after user confirms the write.
        
        Args:
            path: File path to write
            content: Content to write
            
        Returns:
            Success message
        """
        expanded_path = self.expand_path(path)
        self._validate_path(expanded_path)
        
        def do_write():
            # Create parent directories if needed
            expanded_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            expanded_path.write_text(content, encoding="utf-8")
            return f"Written to {expanded_path}"
        
        result = execute_with_error_handling(self.name, do_write)
        self.logger.info(f"Wrote file (confirmed): {expanded_path}")
        return result
    
    def delete_file(self, path: str, ask_confirmation: bool = True) -> str:
        """Delete a file.
        
        Per user decision: user confirms each delete.
        
        Args:
            path: File path to delete
            ask_confirmation: Whether to ask for confirmation (always True per user decision)
            
        Returns:
            Success message
            
        Raises:
            ConfirmationRequest: If user confirmation is required
            ToolError: If file cannot be deleted
        """
        expanded_path = self.expand_path(path)
        self._validate_path(expanded_path)
        
        # Per user decision: always request confirmation for delete
        if ask_confirmation:
            raise ConfirmationRequest(
                tool_name=self.name,
                action="delete",
                details=f"Delete file: {expanded_path}"
            )
        
        def do_delete():
            if not expanded_path.exists():
                raise ToolError(
                    "FilesystemTool",
                    f"File does not exist: {expanded_path}",
                    "Verify the file path"
                )
            
            if expanded_path.is_dir():
                raise ToolError(
                    "FilesystemTool",
                    f"Path is a directory, not a file: {expanded_path}",
                    "Use delete_directory for directories"
                )
            
            expanded_path.unlink()
            return f"Deleted {expanded_path}"
        
        result = execute_with_error_handling(self.name, do_delete)
        self.logger.info(f"Deleted file: {expanded_path}")
        return result
    
    def delete_fileConfirmed(self, path: str) -> str:
        """Delete a file (after user confirmation).
        
        This method should be called after user confirms the delete.
        
        Args:
            path: File path to delete
            
        Returns:
            Success message
        """
        expanded_path = self.expand_path(path)
        self._validate_path(expanded_path)
        
        def do_delete():
            if not expanded_path.exists():
                raise ToolError(
                    "FilesystemTool",
                    f"File does not exist: {expanded_path}",
                    "Verify the file path"
                )
            
            expanded_path.unlink()
            return f"Deleted {expanded_path}"
        
        result = execute_with_error_handling(self.name, do_delete)
        self.logger.info(f"Deleted file (confirmed): {expanded_path}")
        return result
    
    def list_directory(self, path: str = ".") -> list[str]:
        """List contents of a directory.
        
        Args:
            path: Directory path (default: current directory)
            
        Returns:
            List of file/directory names
        """
        expanded_path = self.expand_path(path)
        self._validate_path(expanded_path)
        
        def do_list():
            if not expanded_path.exists():
                raise ToolError(
                    "FilesystemTool",
                    f"Directory does not exist: {expanded_path}",
                    "Verify the directory path"
                )
            
            if not expanded_path.is_dir():
                raise ToolError(
                    "FilesystemTool",
                    f"Path is not a directory: {expanded_path}",
                    "Provide a directory path"
                )
            
            return [item.name for item in expanded_path.iterdir()]
        
        result = execute_with_error_handling(self.name, do_list)
        self.logger.info(f"Listed directory: {expanded_path}")
        return result
    
    def create_directory(self, path: str, ask_confirmation: bool = True) -> str:
        """Create a directory.
        
        Per user decision: user confirms each write (directory creation counts as write).
        
        Args:
            path: Directory path to create
            ask_confirmation: Whether to ask for confirmation
            
        Returns:
            Success message
        """
        expanded_path = self.expand_path(path)
        self._validate_path(expanded_path)
        
        if ask_confirmation:
            raise ConfirmationRequest(
                tool_name=self.name,
                action="create_directory",
                details=f"Create directory: {expanded_path}"
            )
        
        def do_create():
            expanded_path.mkdir(parents=True, exist_ok=True)
            return f"Created directory: {expanded_path}"
        
        result = execute_with_error_handling(self.name, do_create)
        self.logger.info(f"Created directory: {expanded_path}")
        return result
    
    def execute(self, action: str, path: str, **kwargs: Any) -> Any:
        """Execute filesystem operation.
        
        Args:
            action: Action to perform (read, write, delete, list)
            path: File/directory path
            **kwargs: Additional arguments
            
        Returns:
            Result of the action
        """
        actions = {
            "read": lambda: self.read_file(path, kwargs.get("ask_confirmation", True)),
            "write": lambda: self.write_file(path, kwargs.get("content", ""), kwargs.get("ask_confirmation", True)),
            "delete": lambda: self.delete_file(path, kwargs.get("ask_confirmation", True)),
            "list": lambda: self.list_directory(path),
            "create_directory": lambda: self.create_directory(path, kwargs.get("ask_confirmation", True)),
        }
        
        if action not in actions:
            raise ToolError(
                "FilesystemTool",
                f"Unknown action: {action}",
                f"Available actions: {', '.join(actions.keys())}"
            )
        
        return execute_with_error_handling(self.name, actions[action])
    
    def __repr__(self) -> str:
        return f"<FilesystemTool home={self.home}>"


__all__ = ["FilesystemTool"]
