"""
JARVIS Learning Module - Retry Engine

Automatically retries failed tools with alternative strategies.
"""

import time
from dataclasses import dataclass, field
from typing import Any

from loguru import logger


@dataclass
class RetryResult:
    """Result of a retry attempt."""
    success: bool
    tool_name: str
    attempts: list[dict] = field(default_factory=list)
    final_output: str = ""


class AlternativeStrategy:
    """Defines alternative tools to try when a tool fails."""
    
    # Common tool alternatives mapping
    TOOL_ALTERNATIVES = {
        "editor": ["vscode", "code", "notepad++", "notepad"],
        "browser": ["chrome", "firefox", "edge", "browser"],
        "terminal": ["cmd", "powershell", "wt", "terminal"],
        "open file": [],  # Special handling for file paths
    }
    
    @classmethod
    def get_alternatives(cls, tool_name: str) -> list[str]:
        """Get alternative tool names for a failed tool.
        
        Args:
            tool_name: The tool that failed
            
        Returns:
            List of alternative tool names to try
        """
        tool_lower = tool_name.lower()
        
        # Check exact match
        if tool_lower in cls.TOOL_ALTERNATIVES:
            return cls.TOOL_ALTERNATIVES[tool_lower]
        
        # Check partial match
        for key, alternatives in cls.TOOL_ALTERNATIVES.items():
            if key in tool_lower or tool_lower in key:
                return alternatives
        
        return []
    
    @classmethod
    def add_alternative(cls, tool_name: str, alternative: str) -> None:
        """Add an alternative for a tool.
        
        Args:
            tool_name: Original tool name
            alternative: Alternative tool name
        """
        tool_lower = tool_name.lower()
        if tool_lower not in cls.TOOL_ALTERNATIVES:
            cls.TOOL_ALTERNATIVES[tool_lower] = []
        
        if alternative not in cls.TOOL_ALTERNATIVES[tool_lower]:
            cls.TOOL_ALTERNATIVES[tool_lower].append(alternative)
            logger.info(f"Added alternative: {tool_name} -> {alternative}")


class RetryEngine:
    """Engine that retries failed tool executions with alternatives."""
    
    def __init__(self, tool_registry, max_retries: int = 3):
        """Initialize the retry engine.
        
        Args:
            tool_registry: ToolRegistry instance for executing tools
            max_retries: Maximum number of retry attempts (default: 3)
        """
        self.tool_registry = tool_registry
        self.max_retries = max_retries
        self._failure_cache: dict[str, str] = {}  # tool_name -> error reason
        
    def execute_with_retry(
        self, 
        tool_name: str, 
        args: dict[str, Any] | str | None = None
    ) -> RetryResult:
        """Execute a tool with automatic retry on failure.
        
        Args:
            tool_name: Name of the tool to execute
            args: Arguments to pass to the tool
            
        Returns:
            RetryResult with success status and all attempts
        """
        attempts = []
        all_already_failed = []
        
        # Convert args to dict if needed
        if args is None:
            args = {}
        elif isinstance(args, str):
            import json
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}
        
        # Check if we know this tool fails consistently
        tool_key = f"{tool_name}:{str(args)}"
        if tool_key in self._failure_cache:
            logger.debug(f"Skipping known failing tool: {tool_name}")
            return RetryResult(
                success=False,
                tool_name=tool_name,
                attempts=[{"error": self._failure_cache[tool_key], "skipped": True}],
                final_output=f"Error: Known failing tool '{tool_name}'"
            )
        
        # Try original tool first
        result = self._execute_single(tool_name, args)
        attempts.append(result)
        
        if result.get("success", False):
            logger.info(f"Tool '{tool_name}' succeeded on first try")
            return RetryResult(
                success=True,
                tool_name=tool_name,
                attempts=attempts,
                final_output=result.get("output", "Success")
            )
        
        # Get alternatives
        alternatives = AlternativeStrategy.get_alternatives(tool_name)
        
        if not alternatives:
            logger.debug(f"No alternatives available for '{tool_name}'")
            return RetryResult(
                success=False,
                tool_name=tool_name,
                attempts=attempts,
                final_output=result.get("error", "Tool failed")
            )
        
        # Try alternatives
        for alt_tool in alternatives[:self.max_retries - 1]:
            logger.info(f"Retrying with alternative: {alt_tool}")
            alt_result = self._execute_single(alt_tool, args)
            attempts.append(alt_result)
            
            if alt_result.get("success", False):
                logger.info(f"Alternative '{alt_tool}' succeeded")
                return RetryResult(
                    success=True,
                    tool_name=alt_tool,
                    attempts=attempts,
                    final_output=alt_result.get("output", "Success")
                )
        
        # All attempts failed - cache the failure
        last_error = attempts[-1].get("error", "Unknown error")
        self._failure_cache[tool_key] = last_error
        logger.warning(f"Tool '{tool_name}' failed after {len(attempts)} attempts")
        
        return RetryResult(
            success=False,
            tool_name=tool_name,
            attempts=attempts,
            final_output=last_error
        )
    
    def _execute_single(self, tool_name: str, args: dict) -> dict:
        """Execute a single tool and return result dict.
        
        Args:
            tool_name: Name of tool to execute
            args: Arguments for the tool
            
        Returns:
            Dict with success, output, error, and tool info
        """
        try:
            start_time = time.time()
            output = self.tool_registry.execute(tool_name, args)
            duration = time.time() - start_time
            
            success = not output.startswith("Error:")
            
            return {
                "tool": tool_name,
                "args": args,
                "success": success,
                "output": output if success else None,
                "error": output if not success else None,
                "duration_ms": round(duration * 1000, 2)
            }
        except Exception as e:
            return {
                "tool": tool_name,
                "args": args,
                "success": False,
                "output": None,
                "error": str(e),
                "duration_ms": 0
            }
    
    def clear_failure_cache(self) -> None:
        """Clear the failure cache to allow retries."""
        self._failure_cache.clear()
        logger.info("Failure cache cleared")
    
    def get_stats(self) -> dict:
        """Get retry engine statistics.
        
        Returns:
            Dict with stats about retries and failures
        """
        return {
            "cached_failures": len(self._failure_cache),
            "max_retries": self.max_retries,
        }


__all__ = ["RetryEngine", "RetryResult", "AlternativeStrategy"]
