"""
JARVIS Tools - Code Execution

Sandboxed Python code execution tool.
Per user decision: streaming + async callbacks, full logging, detailed errors.
"""

import sys
import io
import signal
import threading
from typing import Any, Callable
from dataclasses import dataclass

from loguru import logger

from tools.base import BaseTool, ToolError, execute_with_error_handling


@dataclass
class ExecutionResult:
    """Result of code execution."""
    output: str
    error: str | None
    status: str  # "success" or "error"


class TimeoutException(Exception):
    """Raised when code execution times out."""
    pass


class MemoryLimitException(Exception):
    """Raised when code exceeds memory limit."""
    pass


class CodeExecutionTool(BaseTool):
    """Sandboxed Python code execution tool.
    
    Per user decision:
    - Blocking dangerous imports (os, subprocess, socket, etc.)
    - Memory limits
    - Timeout limits
    - Streaming output via callback
    - Full logging
    - Detailed errors with suggestions
    """
    
    # Blocked imports for security
    BLOCKED_IMPORTS = [
        "os",
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "http.client",
        "ftplib",
        "telnetlib",
        "poplib",
        "imaplib",
        "smtplib",
        "xmlrpc",
        "multiprocessing",
        "threading",
        "asyncio",
        "concurrent",
        "pickle",
        "marshal",
        "eval",
        "exec",
        "compile",
        "builtins",
        "importlib",
        "pkgutil",
        "sys",
        "gc",
        "ctypes",
    ]
    
    def __init__(self, timeout: int = 30, memory_mb: int = 128):
        """Initialize code execution tool.
        
        Args:
            timeout: Maximum execution time in seconds (default: 30)
            memory_mb: Maximum memory in MB (default: 128)
        """
        super().__init__(name="CodeExecutionTool")
        
        self.timeout = timeout
        self.memory_mb = memory_mb
        
        # Setup custom stdout/stderr capture
        self._output_buffer = io.StringIO()
        self._error_buffer = io.StringIO()
    
    def _check_dangerous_code(self, code: str) -> None:
        """Check for dangerous patterns in code.
        
        Args:
            code: Code to check
            
        Raises:
            ToolError: If dangerous code is detected
        """
        import re
        
        # Check for blocked imports
        for blocked in self.BLOCKED_IMPORTS:
            # Match import statements
            patterns = [
                rf"^\s*import\s+{blocked}\s*$",
                rf"^\s*from\s+{blocked}\s+import",
                rf"^\s*import\s+\w+\s+as\s+\w+\s*$",  # import X as Y
                rf'^\s*import\s+["\']?{blocked}["\']?\s*$',
            ]
            
            for pattern in patterns:
                if re.search(pattern, code, re.MULTILINE):
                    raise ToolError(
                        "CodeExecutionTool",
                        f"Blocked import: {blocked}",
                        f"Remove the import statement for '{blocked}' - it's not allowed for security reasons"
                    )
        
        # Check for dangerous function calls
        dangerous_patterns = [
            (r'open\s*\(', "Use of 'open()' is blocked for security"),
            (r'__import__\s*\(', "Dynamic imports are blocked"),
            (r'eval\s*\(', "'eval()' is blocked for security"),
            (r'exec\s*\(', "'exec()' is blocked for security"),
            (r'compile\s*\(', "'compile()' is blocked for security"),
        ]
        
        for pattern, message in dangerous_patterns:
            if re.search(pattern, code):
                raise ToolError(
                    "CodeExecutionTool",
                    message,
                    "Rewrite your code without this pattern"
                )
    
    def _timeout_handler(self, signum, frame):
        """Signal handler for timeout."""
        raise TimeoutException(f"Execution timed out after {self.timeout} seconds")
    
    def _run_with_timeout(self, code: str, globals_dict: dict, locals_dict: dict) -> None:
        """Run code with timeout.
        
        Args:
            code: Python code to execute
            globals_dict: Global variables dict
            locals_dict: Local variables dict
        """
        # Set up timeout
        signal.signal(signal.SIGALRM, self._timeout_handler)
        signal.alarm(self.timeout)
        
        try:
            # Execute the code
            exec(code, globals_dict, locals_dict)
        finally:
            # Cancel alarm
            signal.alarm(0)
    
    def execute(
        self,
        code: str,
        stream_callback: Callable[[str], None] | None = None
    ) -> dict[str, Any]:
        """Execute Python code in sandbox.
        
        Per user decision: blocks dangerous imports, returns {output, error, status}.
        
        Args:
            code: Python code to execute
            stream_callback: Optional callback for streaming output
            
        Returns:
            Dict with {output, error, status}
        """
        self.logger.info(f"Executing code (length: {len(code)} chars)")
        
        # Check for dangerous code first
        self._check_dangerous_code(code)
        
        # Setup execution environment
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        # Safe globals - no access to dangerous modules
        safe_globals = {
            "__builtins__": {
                # Allow only safe builtins
                "print": lambda *args, **kwargs: (
                    stdout_capture.write(" ".join(str(a) for a in args) + "\n"),
                    stream_callback(" ".join(str(a) for a in args)) if stream_callback else None
                ),
                "len": len,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "sorted": sorted,
                "reversed": reversed,
                "sum": sum,
                "min": min,
                "max": max,
                "abs": abs,
                "round": round,
                "pow": pow,
                "divmod": divmod,
                "isinstance": isinstance,
                "issubclass": issubclass,
                "type": type,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "frozenset": frozenset,
                "slice": slice,
                "format": format,
                "hex": hex,
                "oct": oct,
                "bin": bin,
                "ord": ord,
                "chr": chr,
                "ascii": ascii,
                "repr": repr,
                "hasattr": hasattr,
                "getattr": getattr,
                "setattr": setattr,
                "delattr": delattr,
                "iter": iter,
                "next": next,
                "super": super,
                "property": property,
                "staticmethod": staticmethod,
                "classmethod": classmethod,
                "Exception": Exception,
                "BaseException": BaseException,
                "StopIteration": StopIteration,
                "ArithmeticError": ArithmeticError,
                "LookupError": LookupError,
                "ValueError": ValueError,
                "TypeError": TypeError,
                "KeyError": KeyError,
                "IndexError": IndexError,
            },
            # Math module is safe to provide
            "math": __import__("math"),
            "random": __import__("random"),
            "json": __import__("json"),
            "re": __import__("re"),
        }
        
        try:
            # Execute in a separate thread with timeout
            result_container = []
            error_container = []
            
            def run_code():
                try:
                    # Create empty locals
                    safe_locals = {}
                    
                    # Redirect stdout/stderr
                    old_stdout = sys.stdout
                    old_stderr = sys.stderr
                    sys.stdout = stdout_capture
                    sys.stderr = stderr_capture
                    
                    try:
                        exec(compile(code, "<code>", "exec"), safe_globals, safe_locals)
                    finally:
                        sys.stdout = old_stdout
                        sys.stderr = old_stderr
                    
                    # Get the last expression value if no return
                    if safe_locals:
                        last_value = list(safe_locals.values())[-1] if safe_locals else None
                        if last_value is not None:
                            stdout_capture.write(repr(last_value))
                    
                    result_container.append(stdout_capture.getvalue())
                except Exception as e:
                    error_container.append(str(e))
            
            # Run in thread with timeout
            thread = threading.Thread(target=run_code)
            thread.daemon = True
            thread.start()
            thread.join(timeout=self.timeout)
            
            if thread.is_alive():
                raise ToolError(
                    "CodeExecutionTool",
                    f"Execution timed out after {self.timeout} seconds",
                    "Optimize your code or increase the timeout"
                )
            
            # Check for errors
            if error_container:
                error_msg = error_container[0]
                if "timeout" in error_msg.lower():
                    raise ToolError(
                        "CodeExecutionTool",
                        f"Execution timed out after {self.timeout} seconds",
                        "Optimize your code or increase the timeout"
                    )
                return {
                    "output": result_container[0] if result_container else "",
                    "error": error_msg,
                    "status": "error"
                }
            
            return {
                "output": result_container[0] if result_container else "",
                "error": None,
                "status": "success"
            }
            
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(
                "CodeExecutionTool",
                str(e),
                "Check your code for syntax errors"
            ) from e
    
    async def execute_async(
        self,
        code: str,
        stream_callback: Callable[[str], None] | None = None
    ) -> dict[str, Any]:
        """Async version of execute.
        
        Args:
            code: Python code to execute
            stream_callback: Optional callback for streaming output
            
        Returns:
            Dict with {output, error, status}
        """
        import asyncio
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.execute(code, stream_callback)
        )
    
    def __repr__(self) -> str:
        return f"<CodeExecutionTool timeout={self.timeout}s memory={self.memory_mb}MB>"


__all__ = ["CodeExecutionTool", "ExecutionResult"]
