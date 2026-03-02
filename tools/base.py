"""
JARVIS Tools - Base Classes

Provides base classes and error handling utilities for all tools.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, TypeVar, ParamSpec

from loguru import logger

P = ParamSpec("P")
R = TypeVar("R")


class ToolError(Exception):
    """Exception raised when a tool execution fails.
    
    Attributes:
        tool_name: Name of the tool that failed
        message: Error message describing what went wrong
        suggestion: Optional suggestion for how to fix the issue
    """
    
    def __init__(self, tool_name: str, message: str, suggestion: str | None = None):
        self.tool_name = tool_name
        self.message = message
        self.suggestion = suggestion
        
        # Build the full error message
        full_message = f"Tool '{tool_name}' failed: {message}"
        if suggestion:
            full_message += f"\nSuggestion: {suggestion}"
        
        super().__init__(full_message)


class ConfirmationRequest(Exception):
    """Exception raised when a tool requires user confirmation.
    
    Attributes:
        tool_name: Name of the tool requesting confirmation
        action: The action that needs confirmation
        details: Additional details about the action
    """
    
    def __init__(self, tool_name: str, action: str, details: str | None = None):
        self.tool_name = tool_name
        self.action = action
        self.details = details
        
        message = f"Tool '{tool_name}' requires confirmation for: {action}"
        if details:
            message += f"\nDetails: {details}"
        
        super().__init__(message)


class BaseTool(ABC):
    """Abstract base class for all JARVIS tools.
    
    All tools should inherit from this class and implement the execute method.
    """
    
    def __init__(self, name: str | None = None):
        self.name = name or self.__class__.__name__
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Setup logging for this tool."""
        # Each tool gets its own logger
        self.logger = logger.bind(tool=self.name)
    
    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the tool with the given arguments.
        
        Returns:
            The result of the tool execution
            
        Raises:
            ToolError: If the tool execution fails
            ConfirmationRequest: If user confirmation is needed
        """
        pass
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"


def execute_with_error_handling(
    tool_name: str,
    tool_func: Callable[P, R],
    *args: P.args,
    **kwargs: P.kwargs
) -> R:
    """Execute a tool function with consistent error handling.
    
    This wrapper catches common exceptions and converts them to ToolError
    with detailed suggestions.
    
    Args:
        tool_name: Name of the tool (for error messages)
        tool_func: The function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        The result of the function execution
        
    Raises:
        ToolError: If the function raises a known exception
    """
    try:
        return tool_func(*args, **kwargs)
    
    except PermissionError as e:
        raise ToolError(
            tool_name,
            str(e),
            "Check file permissions or run as administrator"
        ) from e
    
    except FileNotFoundError as e:
        raise ToolError(
            tool_name,
            str(e),
            "Verify the file path exists"
        ) from e
    
    except IsADirectoryError as e:
        raise ToolError(
            tool_name,
            str(e),
            "Expected a file but got a directory"
        ) from e
    
    except TimeoutError as e:
        raise ToolError(
            tool_name,
            str(e),
            "Increase timeout or check network connectivity"
        ) from e
    
    except ConnectionError as e:
        raise ToolError(
            tool_name,
            str(e),
            "Check your internet connection"
        ) from e
    
    except OSError as e:
        raise ToolError(
            tool_name,
            str(e),
            "Operating system error - check system resources"
        ) from e
    
    except ValueError as e:
        raise ToolError(
            tool_name,
            str(e),
            "Invalid input value - check the arguments"
        ) from e
    
    except ToolError:
        # Re-raise ToolError without wrapping
        raise
    
    except Exception as e:
        # Catch-all for unexpected errors
        raise ToolError(
            tool_name,
            str(e),
            "An unexpected error occurred"
        ) from e


__all__ = [
    "BaseTool",
    "ToolError",
    "ConfirmationRequest",
    "execute_with_error_handling",
]
