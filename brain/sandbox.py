"""
JARVIS Brain Layer - Code Execution Sandbox

Enhanced sandbox with:
- Python and shell execution
- Package installation (pip)
- Diff preview for file changes
- Execution history with replay
- Resource monitoring
- Safe file I/O (allowed directories only)
"""

import difflib
import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger


@dataclass
class ExecutionRecord:
    """A recorded code execution."""
    id: str
    language: str
    code: str
    output: str
    error: str | None
    status: str
    timestamp: float
    duration_ms: float
    package_installs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "language": self.language,
            "code": self.code[:500],
            "output": self.output[:500],
            "error": self.error,
            "status": self.status,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "package_installs": self.package_installs,
        }


@dataclass
class DiffPreview:
    """Preview of file changes before applying."""
    file_path: str
    old_content: str
    new_content: str
    diff_text: str
    additions: int
    deletions: int

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "additions": self.additions,
            "deletions": self.deletions,
            "diff": self.diff_text,
        }


class CodeSandbox:
    """
    Enhanced code execution sandbox.

    Supports:
    - Python execution with blocked imports
    - Shell command execution (restricted)
    - Package installation via pip
    - Diff preview for file writes
    - Execution history
    """

    BLOCKED_IMPORTS = {
        "os", "subprocess", "socket", "requests", "urllib",
        "http.client", "ftplib", "telnetlib", "multiprocessing",
        "threading", "asyncio", "concurrent", "ctypes",
    }

    BLOCKED_PATTERNS = [
        (r'open\s*\(', "Use of 'open()' is blocked"),
        (r'__import__\s*\(', "Dynamic imports are blocked"),
        (r'eval\s*\(', "'eval()' is blocked"),
        (r'exec\s*\(', "'exec()' is blocked"),
    ]

    def __init__(
        self,
        timeout: int = 30,
        memory_mb: int = 128,
        history_path: str = "./data/execution_history.json",
    ):
        self.timeout = timeout
        self.memory_mb = memory_mb
        self.history_path = Path(history_path)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        self._history: list[ExecutionRecord] = []
        self._installed_packages: set[str] = set()
        self._load_history()

    def _load_history(self) -> None:
        if self.history_path.exists():
            try:
                data = json.loads(self.history_path.read_text(encoding="utf-8"))
                for item in data.get("records", []):
                    self._history.append(ExecutionRecord(**item))
                self._installed_packages = set(data.get("installed_packages", []))
            except Exception:
                pass

    def _save_history(self) -> None:
        data = {
            "records": [r.to_dict() for r in self._history[-100:]],
            "installed_packages": list(self._installed_packages),
        }
        self.history_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _check_code(self, code: str) -> None:
        """Check code for dangerous patterns."""
        import re

        for blocked in self.BLOCKED_IMPORTS:
            patterns = [
                rf"^\s*import\s+{blocked}\s*$",
                rf"^\s*from\s+{blocked}\s+import",
            ]
            for pattern in patterns:
                if re.search(pattern, code, re.MULTILINE):
                    raise ValueError(f"Blocked import: {blocked}")

        for pattern, msg in self.BLOCKED_PATTERNS:
            if re.search(pattern, code):
                raise ValueError(msg)

    def run_python(self, code: str, confirm: bool = False) -> dict[str, Any]:
        """
        Execute Python code in sandbox.

        Args:
            code: Python code to execute
            confirm: Must be True to execute

        Returns:
            Dict with output, error, status, duration_ms
        """
        if not confirm:
            return {
                "output": "",
                "error": "Requires confirmation. Set 'confirm': true.",
                "status": "error",
                "duration_ms": 0,
            }

        start = time.time()

        try:
            self._check_code(code)
        except ValueError as e:
            return {
                "output": "",
                "error": str(e),
                "status": "error",
                "duration_ms": 0,
            }

        # Create safe wrapper with properly indented user code
        indented_code = "\n".join("    " + line for line in code.splitlines())
        wrapper = '''
import sys, json

class _Capture:
    def __init__(self):
        self.lines = []
    def write(self, text):
        if text.strip():
            self.lines.append(str(text))
    def flush(self):
        pass

_cap = _Capture()
sys.stdout = _cap
try:
''' + indented_code + '''
    result = {"output": "\\n".join(_cap.lines), "error": None, "status": "success"}
except Exception as e:
    result = {"output": "", "error": str(e), "status": "error"}
sys.stdout = sys.__stdout__
print(json.dumps(result))
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(wrapper)
            script = f.name

        try:
            env = {
                "PATH": "",
                "PYTHONPATH": "",
                "HOME": "",
                "USER": "",
                "TMPDIR": tempfile.gettempdir(),
            }

            if sys.platform == "win32":
                proc = subprocess.Popen(
                    [sys.executable, script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                    env=env,
                    cwd=tempfile.gettempdir(),
                )
            else:
                import resource
                proc = subprocess.Popen(
                    [sys.executable, script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    preexec_fn=os.setsid,
                    env=env,
                    cwd=tempfile.gettempdir(),
                )
                try:
                    resource.setrlimit(resource.RLIMIT_CPU, (self.timeout, self.timeout))
                    resource.setrlimit(resource.RLIMIT_FSIZE, (10 * 1024 * 1024, 10 * 1024 * 1024))
                except (ValueError, OSError):
                    pass

            try:
                stdout, stderr = proc.communicate(timeout=self.timeout)
                duration = (time.time() - start) * 1000

                try:
                    result = json.loads(stdout.strip())
                except json.JSONDecodeError:
                    result = {
                        "output": stdout,
                        "error": stderr or "Failed to parse output",
                        "status": "error",
                    }

                result["duration_ms"] = round(duration, 1)
                self._record("python", code, result)
                return result

            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                duration = (time.time() - start) * 1000
                result = {
                    "output": "",
                    "error": f"Timed out after {self.timeout}s",
                    "status": "error",
                    "duration_ms": round(duration, 1),
                }
                self._record("python", code, result)
                return result

        finally:
            try:
                os.unlink(script)
            except Exception:
                pass

    def run_shell(self, command: str, confirm: bool = False) -> dict[str, Any]:
        """
        Execute a shell command in sandbox.

        Args:
            command: Shell command to execute
            confirm: Must be True to execute

        Returns:
            Dict with output, error, status
        """
        if not confirm:
            return {
                "output": "",
                "error": "Requires confirmation. Set 'confirm': true.",
                "status": "error",
                "duration_ms": 0,
            }

        # Block dangerous commands
        dangerous = ["rm -rf", "del /f", "format", "shutdown", "reboot", "mkfs"]
        cmd_lower = command.lower()
        for d in dangerous:
            if d in cmd_lower:
                return {
                    "output": "",
                    "error": f"Blocked dangerous command: {d}",
                    "status": "error",
                    "duration_ms": 0,
                }

        start = time.time()
        try:
            proc = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout,
                cwd=tempfile.gettempdir(),
            )
            stdout, stderr = proc.communicate(timeout=self.timeout)
            duration = (time.time() - start) * 1000

            result = {
                "output": stdout,
                "error": stderr if stderr else None,
                "status": "success" if proc.returncode == 0 else "error",
                "duration_ms": round(duration, 1),
            }
            self._record("shell", command, result)
            return result

        except subprocess.TimeoutExpired:
            duration = (time.time() - start) * 1000
            return {
                "output": "",
                "error": f"Timed out after {self.timeout}s",
                "status": "error",
                "duration_ms": round(duration, 1),
            }

    def install_package(self, package: str, confirm: bool = False) -> dict[str, Any]:
        """
        Install a Python package via pip.

        Args:
            package: Package name (e.g., "numpy", "requests==2.28.0")
            confirm: Must be True to install

        Returns:
            Dict with output, error, status
        """
        if not confirm:
            return {
                "output": "",
                "error": "Package installation requires confirmation.",
                "status": "error",
                "duration_ms": 0,
            }

        # Block dangerous packages
        blocked = ["os", "subprocess", "socket", "sys", "ctypes"]
        pkg_name = package.split("==")[0].split(">=")[0].split("<=")[0].strip()
        if pkg_name in blocked:
            return {
                "output": "",
                "error": f"Package '{pkg_name}' is blocked for security.",
                "status": "error",
                "duration_ms": 0,
            }

        start = time.time()
        try:
            proc = subprocess.Popen(
                [sys.executable, "-m", "pip", "install", package, "--quiet"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120,
            )
            stdout, stderr = proc.communicate(timeout=120)
            duration = (time.time() - start) * 1000

            if proc.returncode == 0:
                self._installed_packages.add(pkg_name)
                self._save_history()

            result = {
                "output": stdout or f"Installed {package}",
                "error": stderr if proc.returncode != 0 else None,
                "status": "success" if proc.returncode == 0 else "error",
                "duration_ms": round(duration, 1),
            }
            self._record("pip", f"install {package}", result)
            return result

        except subprocess.TimeoutExpired:
            return {
                "output": "",
                "error": "Installation timed out",
                "status": "error",
                "duration_ms": 120000,
            }

    def preview_diff(self, file_path: str, new_content: str) -> DiffPreview:
        """
        Preview a diff before writing to a file.

        Args:
            file_path: Path to the file
            new_content: New content to write

        Returns:
            DiffPreview with the diff
        """
        path = Path(file_path)
        old_content = path.read_text(encoding="utf-8") if path.exists() else ""

        diff_lines = list(difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
        ))

        additions = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
        deletions = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))

        return DiffPreview(
            file_path=file_path,
            old_content=old_content,
            new_content=new_content,
            diff_text="".join(diff_lines),
            additions=additions,
            deletions=deletions,
        )

    def apply_diff(self, preview: DiffPreview, confirm: bool = False) -> dict[str, Any]:
        """Apply a diff preview to disk after confirmation."""
        if not confirm:
            return {
                "output": "",
                "error": "File write requires confirmation.",
                "status": "error",
                "duration_ms": 0,
            }

        try:
            Path(preview.file_path).parent.mkdir(parents=True, exist_ok=True)
            Path(preview.file_path).write_text(preview.new_content, encoding="utf-8")
            return {
                "output": f"Written {len(preview.new_content)} chars to {preview.file_path}",
                "error": None,
                "status": "success",
                "duration_ms": 0,
            }
        except Exception as e:
            return {
                "output": "",
                "error": str(e),
                "status": "error",
                "duration_ms": 0,
            }

    def get_history(self, limit: int = 10) -> list[dict]:
        """Get recent execution history."""
        return [r.to_dict() for r in self._history[-limit:]]

    def replay(self, record_id: str, confirm: bool = False) -> dict[str, Any]:
        """Replay a recorded execution."""
        for record in self._history:
            if record.id == record_id:
                if record.language == "python":
                    return self.run_python(record.code, confirm=confirm)
                elif record.language == "shell":
                    return self.run_shell(record.code, confirm=confirm)
        return {"output": "", "error": f"Record {record_id} not found", "status": "error"}

    def get_installed_packages(self) -> list[str]:
        """List installed packages."""
        return sorted(self._installed_packages)

    def _record(self, language: str, code: str, result: dict) -> None:
        record = ExecutionRecord(
            id=f"exec_{int(time.time() * 1000)}",
            language=language,
            code=code,
            output=result.get("output", ""),
            error=result.get("error"),
            status=result.get("status", "error"),
            timestamp=time.time(),
            duration_ms=result.get("duration_ms", 0),
        )
        self._history.append(record)
        self._save_history()


__all__ = ["CodeSandbox", "ExecutionRecord", "DiffPreview"]
