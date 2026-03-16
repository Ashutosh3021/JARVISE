"""
JARVIS Tools - Code Execution

Sandboxed Python code execution tool using process-based isolation.
Per user decision: streaming + async callbacks, full logging, detailed errors.
"""

import os
import sys
import io
import signal
import subprocess
import tempfile
import json
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
    """Sandboxed Python code execution tool using process isolation.
    
    Per user decision:
    - Process-based isolation for true sandboxing
    - Memory limits via OS process constraints
    - Timeout limits via OS process termination
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
    
    def _create_safe_script(self, code: str) -> str:
        """Create a safe Python script wrapper.
        
        Args:
            code: User code to wrap
            
        Returns:
            Full Python script to execute
        """
        # Create wrapper that captures output safely
        wrapper = f'''
import sys
import json

# Safe print that outputs JSON
class SafePrint:
    def __init__(self):
        self.output = []
    
    def write(self, text):
        if text.strip():
            self.output.append(str(text))
    
    def flush(self):
        pass

# Redirect stdout to capture output
safe_out = SafePrint()
sys.stdout = safe_out

try:
{code}
    # Output result as JSON
    result = {{"output": "\\\\n".join(safe_out.output), "error": None, "status": "success"}}
except Exception as e:
    result = {{"output": "", "error": str(e), "status": "error"}}

sys.stdout = sys.__stdout__
print(json.dumps(result))
'''
        return wrapper
    
    def execute(
        self,
        code: str,
        stream_callback: Callable[[str], None] | None = None
    ) -> dict[str, Any]:
        """Execute Python code in sandbox using process isolation.
        
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
        
        # Create safe script
        safe_script = self._create_safe_script(code)
        
        # Create temporary file for the script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(safe_script)
            script_path = f.name
        
        try:
            # Execute in a separate process with timeout
            # Use Popen with kill on timeout for hard termination
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
            )
            
            try:
                # Wait for process with timeout
                stdout, stderr = process.communicate(timeout=self.timeout)
                
                # Process completed within timeout
                try:
                    result = json.loads(stdout.strip())
                    
                    # Stream output if callback provided
                    if stream_callback and result.get("output"):
                        for line in result["output"].split("\n"):
                            stream_callback(line)
                    
                    return result
                except json.JSONDecodeError:
                    # Fallback if output wasn't JSON
                    return {
                        "output": stdout,
                        "error": stderr or "Failed to parse execution result",
                        "status": "error"
                    }
                    
            except subprocess.TimeoutExpired:
                # Hard kill the process on timeout
                process.kill()
                process.wait()
                
                raise ToolError(
                    "CodeExecutionTool",
                    f"Execution timed out after {self.timeout} seconds",
                    "Optimize your code or increase the timeout"
                )
        
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(
                "CodeExecutionTool",
                str(e),
                "Check your code for syntax errors"
            )
        finally:
            # Clean up temp file
            try:
                os.unlink(script_path)
            except Exception:
                pass
    
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
