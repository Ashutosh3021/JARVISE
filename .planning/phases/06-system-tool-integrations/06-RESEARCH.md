# Phase 6: System Tool Integrations - Research

**Researched:** 2026-03-02
**Domain:** System tool integrations (web search, browser automation, filesystem, calendar, email, code execution)
**Confidence:** HIGH

## Summary

This phase implements executable tools for the JARVIS agent to interact with external systems. The core challenge is integrating OAuth2-based calendar/email APIs, browser automation with Playwright, secure filesystem operations, and sandboxed code execution into the existing ToolRegistry architecture. All decisions from discussion phase are locked and must be honored.

**Primary recommendation:** Use google-auth-oauthlib for Google OAuth2, msgraph-sdk for Microsoft Graph, playwright with persistent context for browser automation, and restricted-python or safe-py-runner for sandboxed code execution. Integrate all tools into the existing ToolRegistry in brain/tools.py.

---

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Token Storage:** File-based (encrypted JSON in data/)
- **Token Refresh:** Automatic using refresh_token grant
- **Auth Separation:** Unified per provider (Google = all Google APIs, Microsoft = all MS APIs)
- **First-time Auth:** CLI-based flow (prints URL, user visits, pastes code)

### Browser Automation
- **Operations:** Full automation (any operation a human can do in browser)
- **Sessions:** Persistent (browser stays open, reuses session)
- **Display:** Visible (user sees browser window)
- **Content:** Text extraction with JARVIS highlighting important details

### Filesystem
- **Access:** User decides each time — interactive path selection
- **Write Confirmation:** Confirm every write before executing
- **Delete Confirmation:** Ask user before deleting anything
- **Path Handling:** Expand ~ to user home directory on Windows

### Tool Execution
- **Result Return:** Streaming + Async callbacks
- **Timeout:** Depends on task complexity (configurable per tool)
- **Logging:** Full logging (log to file + console)
- **Error Handling:** Raise exception with exact issue + suggested solution

### Claude's Discretion (Research Options)
- Exact timeout values per tool type
- Encryption algorithm choice for token storage
- Browser pool size for concurrent requests
- File operation retry logic

</user_constraints>

---

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ST-01 | Web search tool | Can use browser automation or httpx for search APIs |
| ST-02 | Browser automation (Playwright) | Playwright with persistent context, visible window |
| ST-03 | Filesystem manipulation tool | pathlib with ~ expansion, user confirmations |
| ST-04 | Code execution tool (sandboxed subprocess) | safe-py-runner or restricted library |
| ST-05 | Google Calendar integration with OAuth2 | google-api-python-client + google-auth-oauthlib |
| ST-06 | Google Email integration with OAuth2 | gmail API with google-auth-oauthlib |
| ST-07 | Microsoft Outlook integration | msgraph-sdk for Graph API |
| ST-08 | System monitor tool (diagnostics) | psutil (already in requirements.txt) |
| ST-09 | Tools registry for agent | Existing ToolRegistry in brain/tools.py |

</phase_requirements>

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| playwright | >=1.40.0 | Browser automation | Already in requirements.txt, cross-browser support |
| google-api-python-client | >=2.100.0 | Google APIs (Calendar, Gmail) | Already in requirements.txt |
| google-auth-oauthlib | latest | OAuth2 flow for Google | Required for refresh tokens |
| msgraph-sdk | >=1.0.0 | Microsoft Graph API | Already in requirements.txt |
| httpx | >=0.26.0 | HTTP client for web search | Already in requirements.txt |
| psutil | >=5.9.0 | System monitoring | Already in requirements.txt |
| cryptography | latest | Token encryption | Standard Python crypto library |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| safe-py-runner | latest | Sandboxed code execution | ST-04 code execution tool |
| restricted | latest | AST-based code restrictions | Alternative to safe-py-runner |
| aiofiles | >=23.2.0 | Async file operations | Tool execution async support |
| loguru | >=0.7.0 | Logging | Already in requirements.txt |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| playwright | selenium | Older, less reliable, slower |
| google-auth-oauthlib | flask + google-auth | More complex, requires web server |
| msgraph-sdk | raw REST + requests | More boilerplate, no type hints |
| safe-py-runner | subprocess.run with whitelist | Less secure, more manual work |

---

## Architecture Patterns

### Recommended Project Structure

```
tools/
├── __init__.py
├── registry.py           # Tool registration + ToolRegistry extension
├── base.py              # Base tool classes
├── web_search.py        # ST-01: Web search
├── browser.py           # ST-02: Playwright automation
├── filesystem.py        # ST-03: File operations
├── code_exec.py         # ST-04: Sandboxed execution
├── google_calendar.py   # ST-05: Google Calendar
├── google_email.py      # ST-06: Google Email (Gmail)
├── microsoft_outlook.py # ST-07: Microsoft Graph
├── system_monitor.py    # ST-08: Diagnostics
└── auth/
    ├── __init__.py
    ├── token_manager.py # Token storage + refresh
    └── oauth.py        # OAuth2 flow helpers
```

### Pattern 1: ToolRegistry Extension

The existing ToolRegistry in brain/tools.py accepts `Callable` functions. Tools should be implemented as classes with an `execute` method and registered as wrappers.

```python
# Source: Based on brain/tools.py patterns
from brain.tools import ToolRegistry

class BrowserTool:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
    
    def execute(self, args: dict) -> str:
        # Implementation
        pass

# Register in registry
browser_tool = BrowserTool(registry)
registry.register("browser", browser_tool.execute, "Navigate and interact with browser")
```

### Pattern 2: OAuth2 Token Storage with Encryption

```python
# Source: google-auth-oauthlib + cryptography
import json
import os
from pathlib import Path
from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials

class TokenManager:
    def __init__(self, token_dir: Path, encryption_key: bytes = None):
        self.token_dir = token_dir
        self.token_dir.mkdir(parents=True, exist_ok=True)
        self.cipher = Fernet(encryption_key or Fernet.generate_key())
    
    def save_credentials(self, provider: str, credentials: Credentials):
        token_data = credentials.to_json()
        encrypted = self.cipher.encrypt(token_data.encode())
        token_file = self.token_dir / f"{provider}_token.enc"
        token_file.write_bytes(encrypted)
    
    def load_credentials(self, provider: str) -> Credentials | None:
        token_file = self.token_dir / f"{provider}_token.enc"
        if not token_file.exists():
            return None
        encrypted = token_file.read_bytes()
        token_data = self.cipher.decrypt(encrypted).decode()
        return Credentials.from_authorized_user_info(json.loads(token_data))
    
    def refresh_if_needed(self, credentials: Credentials) -> Credentials:
        from google.auth.transport.requests import Request
        if credentials.expired and credentials.refresh_token:
            request = Request()
            credentials.refresh(request)
        return credentials
```

### Pattern 3: CLI-based OAuth2 Flow

```python
# Source: google-auth-oauthlib Flow
from google_auth_oauthlib.flow import InstalledAppFlow

def authenticate_google(scopes: list[str], client_secrets_path: str) -> Credentials:
    flow = InstalledAppFlow.from_client_secrets_file(
        client_secrets_path,
        scopes=scopes
    )
    # For CLI - print URL and get code from user
    auth_url, _ = flow.authorization_url(access_type='offline')
    print(f"\nPlease visit this URL:\n{auth_url}\n")
    code = input("Enter the authorization code: ")
    flow.fetch_token(code=code)
    return flow.credentials
```

### Pattern 4: Playwright Persistent Browser

```python
# Source: Playwright Python API
from playwright.sync_api import sync_playwright

class BrowserManager:
    def __init__(self, user_data_dir: str = None):
        self.user_data_dir = user_data_dir
        self.playwright = None
        self.browser = None
        self.context = None
    
    def launch(self):
        self.playwright = sync_playwright().start()
        if self.user_data_dir:
            # Persistent context - maintains login state
            self.context = self.playwright.chromium.launch_persistent_context(
                self.user_data_dir,
                headless=False,  # Visible window per requirement
                viewport={"width": 1280, "720"}
            )
        else:
            self.browser = self.playwright.chromium.launch(headless=False)
            self.context = self.browser.new_context()
        return self.context
    
    def navigate_and_extract(self, url: str, extract_selector: str = None) -> str:
        page = self.context.new_page()
        page.goto(url)
        content = page.content()
        if extract_selector:
            content = page.locator(extract_selector).inner_text()
        return content
```

### Pattern 5: Sandboxed Code Execution

```python
# Source: safe-py-runner
from safe_py_runner import RunnerPolicy, SafePyRunner

class CodeExecutionTool:
    def __init__(self, timeout: int = 30):
        self.runner = SafePyRunner(
            policy=RunnerPolicy(
                timeout_seconds=timeout,
                memory_limit_mb=128,
                blocked_imports=["os", "subprocess", "socket", "requests"]
            )
        )
    
    def execute(self, code: str) -> dict:
        result = self.runner.execute(code)
        return {
            "output": result.result if result.ok else None,
            "error": result.error if not result.ok else None,
            "status": "success" if result.ok else "error"
        }
```

### Pattern 6: Filesystem Tool with Confirmation

```python
# Source: pathlib + os.path
from pathlib import Path
import os

class FilesystemTool:
    def __init__(self):
        self.home = Path.home()
    
    def expand_path(self, path: str) -> Path:
        if path.startswith("~"):
            return self.home / path[2:].lstrip("/\\")
        return Path(path)
    
    def read_file(self, path: str, ask_confirmation: bool = True) -> str:
        full_path = self.expand_path(path)
        if ask_confirmation:
            # In practice, this would be handled by the agent asking the user
            pass
        return full_path.read_text(encoding="utf-8")
    
    def write_file(self, path: str, content: str, ask_confirmation: bool = True) -> str:
        full_path = self.expand_path(path)
        if ask_confirmation:
            # User confirmation required before write
            pass
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return f"Written to {full_path}"
    
    def delete_file(self, path: str, ask_confirmation: bool = True) -> str:
        full_path = self.expand_path(path)
        if ask_confirmation:
            # User confirmation required before delete
            pass
        full_path.unlink()
        return f"Deleted {full_path}"
```

### Pattern 7: Microsoft Graph Authentication

```python
# Source: msgraph-sdk + DeviceCodeCredential
from azure.identity import DeviceCodeCredential
from msgraph import GraphServiceClient

class MicrosoftAuth:
    def __init__(self, client_id: str, scopes: list[str]):
        self.credential = DeviceCodeCredential(client_id=client_id)
        self.scopes = scopes
        self.client = None
    
    def get_client(self) -> GraphServiceClient:
        if not self.client:
            self.client = GraphServiceClient(credential=self.credential, scopes=self.scopes)
        return self.client
    
    async def get_calendar_events(self):
        client = self.get_client()
        return await client.me.calendar.events.get()
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OAuth2 flow | Custom token handling | google-auth-oauthlib / azure-identity | Handles security, token refresh, edge cases |
| Browser automation | Selenium / requests | Playwright | Auto-waiting, reliable, cross-browser |
| Code sandbox | subprocess with whitelist | safe-py-runner | Memory limits, timeout, import blocking |
| Token encryption | Custom crypto | cryptography.Fernet | Standard, well-audited |
| Microsoft auth | Raw REST | msgraph-sdk | Type hints, pagination, retry logic |

---

## Common Pitfalls

### Pitfall 1: OAuth2 Token Storage Without Encryption
**What goes wrong:** Refresh tokens stored in plain JSON are stolen if data/ directory is compromised.
**Why it happens:** Developers use simple json.dump() for convenience.
**How to avoid:** Use cryptography.Fernet for symmetric encryption. Store key in system keyring or .env (not git).
**Warning signs:** Token files are readable as plain text.

### Pitfall 2: Browser Sessions Not Persistent
**What goes wrong:** User must log in every time, defeats purpose of browser automation.
**Why it happens:** Using browser.new_context() without user_data_dir.
**How to avoid:** Use launch_persistent_context() with a stable directory path.
**Warning signs:** Login prompts every tool execution.

### Pitfall 3: Refresh Token Not Saved After First Auth
**What goes wrong:** App loses access after first access token expires.
**Why it happens:** Not requesting access_type='offline' in OAuth flow.
**How to avoid:** Always set access_type='offline' for Google, offline_access scope for Microsoft.
**Warning signs:** Credentials work for 1 hour then fail.

### Pitfall 4: Blocking Browser Launch in Async Context
**What goes wrong:** Browser operations freeze the event loop.
**Why it happens:** Playwright sync API blocks.
**How to avoid:** Use playwright.async_api or run sync operations in executor.
**Warning signs:** UI freezes during browser operations.

### Pitfall 5: Path Traversal in Filesystem Tool
**What goes wrong:** Users can access files outside intended directories.
**Why it happens:** Not validating resolved paths.
**How to avoid:** Resolve paths and validate they stay within allowed directories.
**Warning signs:** Paths with "../" are accepted without validation.

### Pitfall 6: Code Execution Without Proper Sandboxing
**What goes wrong:** Malicious code deletes files, exfiltrates data, or compromises system.
**Why it happens:** Using exec() or subprocess without restrictions.
**How to avoid:** Use safe-py-runner with blocked_imports and memory limits.
**Warning signs:** Code can import os, subprocess, socket.

### Pitfall 7: Microsoft Token Refresh Different from Google
**What goes wrong:** Google refresh pattern doesn't work for Microsoft Graph.
**Why it happens:** Microsoft uses different token endpoint and refresh flow.
**How to avoid:** Use msgraph-sdk's built-in token refresh or implement MS-specific refresh.
**Warning signs:** Refresh works for Google but not Microsoft.

---

## Code Examples

### Registering Tools in ToolRegistry

```python
# Source: brain/tools.py patterns + this research
from brain.tools import ToolRegistry

def create_tools_registry() -> ToolRegistry:
    registry = ToolRegistry()
    
    # Import tool implementations
    from tools.browser import BrowserTool
    from tools.filesystem import FilesystemTool
    from tools.google_calendar import GoogleCalendarTool
    from tools.microsoft_outlook import MicrosoftOutlookTool
    from tools.system_monitor import SystemMonitorTool
    from tools.code_exec import CodeExecutionTool
    
    # Create tool instances
    browser = BrowserTool()
    filesystem = FilesystemTool()
    calendar = GoogleCalendarTool()
    outlook = MicrosoftOutlookTool()
    monitor = SystemMonitorTool()
    code_exec = CodeExecutionTool()
    
    # Register with descriptions
    registry.register("browser", browser.execute, 
        "Navigate to URLs, extract content, fill forms, click elements")
    registry.register("filesystem", filesystem.execute,
        "Read, write, delete files. Requires user confirmation.")
    registry.register("google_calendar", calendar.execute,
        "List, create, update Google Calendar events")
    registry.register("google_email", calendar.execute,  # Reuse for Gmail
        "Read, send Google Email messages")
    registry.register("outlook", outlook.execute,
        "Read, send Microsoft Outlook/Exchange emails")
    registry.register("system_monitor", monitor.execute,
        "Get CPU, memory, disk, network statistics")
    registry.register("execute_code", code_exec.execute,
        "Run Python code in sandboxed environment")
    registry.register("web_search", lambda args: browser.search(args),
        "Search the web using browser automation")
    
    return registry
```

### Error Handling with Detailed Messages

```python
# Source: Error handling best practices
class ToolError(Exception):
    def __init__(self, tool_name: str, message: str, suggestion: str = None):
        self.tool_name = tool_name
        self.suggestion = suggestion
        base_msg = f"Tool '{tool_name}' failed: {message}"
        if suggestion:
            base_msg += f"\nSuggestion: {suggestion}"
        super().__init__(base_msg)

def execute_with_error_handling(tool_func, *args, **kwargs):
    try:
        return tool_func(*args, **kwargs)
    except PermissionError as e:
        raise ToolError(
            tool_func.__name__,
            str(e),
            "Check file permissions or run as administrator"
        ) from e
    except FileNotFoundError as e:
        raise ToolError(
            tool_func.__name__,
            str(e),
            "Verify the file path exists"
        ) from e
    except TimeoutError as e:
        raise ToolError(
            tool_func.__name__,
            str(e),
            "Increase timeout or check network connectivity"
        ) from e
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| Selenium | Playwright | 2020+ | Much faster, auto-waiting, reliable |
| Basic auth (IMAP/SMTP) | OAuth2 for Gmail/Outlook | 2022+ | Microsoft deprecated basic auth |
| json.dump tokens | Encrypted token storage | Now | Security requirement |
| exec() for code | safe-py-runner | 2024+ | Memory limits, import blocking |
| Multiple OAuth libraries | Unified per-provider flow | Now | Simpler maintenance |

**Deprecated/outdated:**
- IMAP/POP3 with password auth for Gmail/Outlook - OAuth2 required since 2022
- Selenium for browser automation - Playwright is successor
- requests library for Gmail API - google-api-python-client is official

---

## Open Questions

1. **Encryption key storage**
   - What we know: Use cryptography.Fernet for encryption
   - What's unclear: Where to store the encryption key securely on Windows
   - Recommendation: Store in system keyring (keyring package) or prompt user for key on first run

2. **Browser pool size**
   - What we know: Can run multiple browser contexts
   - What's unclear: Optimal pool size for JARVIS use case
   - Recommendation: Start with 1 persistent browser, add pool if concurrent requests needed

3. **Web search implementation**
   - What we know: Can use browser automation or search API
   - What's unclear: Should use browser automation or dedicated search API (DuckDuckGo, SerpAPI)
   - Recommendation: Use browser automation first (more general), add search API if needed

4. **Token refresh on Microsoft**
   - What we know: msgraph-sdk handles refresh internally with DeviceCodeCredential
   - What's unclear: How to persist tokens for offline use with msgraph-sdk
   - Recommendation: Use token cache serialization or re-authenticate on expiry

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already in requirements.txt) |
| Config file | pytest.ini (create if needed) |
| Quick run command | `pytest tests/tools/ -x -v` |
| Full suite command | `pytest tests/tools/ -v --cov=tools` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ST-01 | Web search functionality | unit | `pytest tests/tools/test_web_search.py -x` | ❌ Create |
| ST-02 | Browser navigation + extraction | integration | `pytest tests/tools/test_browser.py -x` | ❌ Create |
| ST-03 | File read/write/delete with path expansion | unit | `pytest tests/tools/test_filesystem.py -x` | ❌ Create |
| ST-04 | Sandboxed code execution | unit | `pytest tests/tools/test_code_exec.py -x` | ❌ Create |
| ST-05 | Google Calendar CRUD | integration | `pytest tests/tools/test_google_calendar.py -x` | ❌ Create |
| ST-06 | Gmail read/send | integration | `pytest tests/tools/test_google_email.py -x` | ❌ Create |
| ST-07 | Outlook read/send | integration | `pytest tests/tools/test_outlook.py -x` | ❌ Create |
| ST-08 | System metrics collection | unit | `pytest tests/tools/test_system_monitor.py -x` | ❌ Create |
| ST-09 | Tools registered in registry | unit | `pytest tests/tools/test_registry.py -x` | ❌ Create |

### Sampling Rate
- **Per task commit:** `pytest tests/tools/ -x -q`
- **Per wave merge:** `pytest tests/tools/ -v --cov=tools`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/tools/` — directory for all tool tests
- [ ] `tests/tools/conftest.py` — shared fixtures (mock tools, temp directories)
- [ ] `tests/tools/__init__.py` — package init

---

## Sources

### Primary (HIGH confidence)
- google-auth-oauthlib documentation - OAuth2 flow, token refresh
- Playwright Python API - Browser automation patterns
- msgraph-sdk documentation - Microsoft Graph authentication
- safe-py-runner documentation - Sandboxed execution

### Secondary (MEDIUM confidence)
- Microsoft identity platform OAuth2 - Token refresh flow
- Stack Overflow - Token storage patterns
- Windows developer blogs - App isolation

### Tertiary (LOW confidence)
- Community tutorials - Specific implementation patterns (verify before use)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in requirements.txt or well-documented
- Architecture: HIGH - Clear patterns from existing ToolRegistry + OAuth flows
- Pitfalls: HIGH - Well-documented OAuth and security pitfalls

**Research date:** 2026-03-02
**Valid until:** 2026-04-02 (30 days - OAuth flows stable, library APIs change slowly)
