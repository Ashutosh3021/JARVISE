"""
JARVIS Brain Layer - Error Handling Module

Provides error handling utilities for the brain layer.
"""

import functools
import time
from typing import Callable, TypeVar, ParamSpec

from loguru import logger


T = TypeVar("T")
P = ParamSpec("P")


class MalformedOutputError(Exception):
    """Raised when LLM output cannot be parsed."""
    pass


class AgentError(Exception):
    """Base exception for agent errors."""
    pass


class ToolError(AgentError):
    """Raised when a tool fails to execute."""
    pass


class RetryableError(Exception):
    """Error that can be retried."""
    pass


def retry_on_error(
    max_retries: int = 3,
    backoff: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to retry a function on error with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff: Initial backoff time in seconds
        exceptions: Tuple of exception types to catch and retry
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception: Exception | None = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        wait_time = backoff * (2 ** attempt)
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                            f"retrying in {wait_time}s: {e}"
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: {e}"
                        )
            
            raise last_exception  # type: ignore
        
        return wrapper
    return decorator


def handle_malformed_output(func: Callable[P, T]) -> Callable[P, T]:
    """
    Decorator to handle malformed output from LLM.
    
    Retries up to 3 times with modified prompting.
    """
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        last_error: Exception | None = None
        
        for attempt in range(3):
            try:
                return func(*args, **kwargs)
            except MalformedOutputError as e:
                last_error = e
                logger.warning(f"Malformed output (attempt {attempt + 1}/3): {e}")
                
                if "retry_prompt" in kwargs:
                    kwargs = {**kwargs, "retry_prompt": True}
                    
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                break
        
        if last_error:
            raise last_error
        raise MalformedOutputError("Failed to get valid output after 3 attempts")
    
    return wrapper


def validate_action_format(action_str: str) -> tuple[str, str | None]:
    """
    Validate and parse action string format.
    
    Args:
        action_str: String in format "tool_name" or "tool_name: args"
    
    Returns:
        Tuple of (tool_name, args_string or None)
    
    Raises:
        MalformedOutputError: If format is invalid
    """
    if not action_str or not action_str.strip():
        raise MalformedOutputError("Empty action string")
    
    parts = action_str.strip().split(":", 1)
    tool_name = parts[0].strip()
    
    if not tool_name:
        raise MalformedOutputError("Missing tool name in action")
    
    args = parts[1].strip() if len(parts) > 1 else None
    
    return tool_name, args


class ErrorHandler:
    """Centralized error handler for brain layer."""
    
    def __init__(self):
        self.error_count = 0
        self.last_error: Exception | None = None
    
    def record_error(self, error: Exception) -> None:
        """Record an error occurrence."""
        self.error_count += 1
        self.last_error = error
        logger.error(f"Brain layer error #{self.error_count}: {error}")
    
    def should_abort(self) -> bool:
        """Check if too many errors have occurred."""
        return self.error_count >= 5
    
    def reset(self) -> None:
        """Reset error tracking."""
        self.error_count = 0
        self.last_error = None


__all__ = [
    "MalformedOutputError",
    "AgentError",
    "ToolError",
    "RetryableError",
    "retry_on_error",
    "handle_malformed_output",
    "validate_action_format",
    "ErrorHandler",
]
