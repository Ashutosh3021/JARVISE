"""
B-5 UAT Test Suite
Run from project root: PYTHONIOENCODING=utf-8 python tests/Bugs_Testing/B5Test.py
Covers: BUG-029, BUG-030, BUG-034, BUG-035, BUG-036, BUG-039
Total: ~13 checks across 6 bugs
"""

import sys
import os
import re
import ast

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []

def report(name, passed, detail=""):
    status = PASS if passed else FAIL
    results.append((name, passed))
    print(f"{status} | {name}")
    if detail:
        print(f"       {detail}")

def read_source(filepath):
    """Read source file from project root."""
    full = os.path.join(PROJECT_ROOT, filepath)
    with open(full, "r", encoding="utf-8") as f:
        return f.read()

print("\n" + "="*60)
print("  B-5 UAT — Polish + Routing")
print("="*60 + "\n")

# ─────────────────────────────────────────────
# BUG-029: Hardcoded localhost:8000
# ─────────────────────────────────────────────
print("── BUG-029: URL Configuration ──")

try:
    # Check CLI client uses config
    src = read_source("cli/client.py")
    uses_config = "Config()" in src or "config.ui_host" in src or "config.ui_port" in src
    no_hardcode = "localhost:8000" not in src
    report("BUG-029 CLI client uses config", uses_config and no_hardcode,
           f"Config used: {uses_config}, No hardcode: {no_hardcode}")
except Exception as e:
    report("BUG-029 CLI check", False, f"Error: {e}")

try:
    # Check UI client uses dynamic URL
    src = read_source("ui/src/App.tsx")
    uses_dynamic = "window.location.host" in src
    no_hardcode_ui = "localhost:8000" not in src
    report("BUG-029 UI client uses dynamic URL", uses_dynamic and no_hardcode_ui,
           f"Dynamic: {uses_dynamic}, No hardcode: {no_hardcode_ui}")
except Exception as e:
    report("BUG-029 UI check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# BUG-030: HTTP fallback wrong endpoint
# ─────────────────────────────────────────────
print("\n── BUG-030: HTTP Fallback Endpoint ──")

try:
    # Check HTTP fallback uses /api/chat
    src = read_source("cli/client.py")
    correct_endpoint = "/api/chat" in src
    # Check if wrong endpoint /ws/chat is still in _chat_http method
    http_method = src.split("async def _chat_http")[1].split("async def")[0] if "_chat_http" in src else ""
    wrong_endpoint = "/ws/chat" in http_method
    report("BUG-030 HTTP fallback uses /api/chat", correct_endpoint and not wrong_endpoint,
           f"Correct endpoint: {correct_endpoint}, Wrong: {wrong_endpoint}")
except Exception as e:
    report("BUG-030 fallback check", False, f"Error: {e}")

try:
    # Check /api/chat endpoint exists
    src = read_source("backend/api/routes/chat.py")
    has_api_chat = '"/api/chat"' in src or "api/chat" in src
    is_post = "def post" in src or "@router.post" in src
    report("BUG-030 /api/chat endpoint exists", has_api_chat and is_post,
           f"Endpoint exists: {has_api_chat}, POST method: {is_post}")
except Exception as e:
    report("BUG-030 endpoint check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# BUG-034: Dead code _highlight_important
# ─────────────────────────────────────────────
print("\n── BUG-034: Dead Code Removal ──")

try:
    # Check _highlight_important is removed
    src = read_source("tools/web_search.py")
    has_dead_code = "_highlight_important" in src
    report("BUG-034 _highlight_important removed", not has_dead_code,
           f"Dead code removed: {not has_dead_code}")
except Exception as e:
    report("BUG-034 check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# BUG-035: Deprecated async patterns
# ─────────────────────────────────────────────
print("\n── BUG-035: Async Pattern Fixes ──")

try:
    # Check asyncio.run() removed from async contexts
    # Note: asyncio.run() in execute() method is OK - it's a sync-to-async bridge
    files_to_check = [
        "tools/microsoft_outlook.py",
        "tools/auth/microsoft.py", 
        "brain/chains.py"
    ]
    has_asyncio_run_in_async = False
    for f in files_to_check:
        src = read_source(f)
        # Parse to check if asyncio.run is inside an async method (not in sync execute bridge)
        lines = src.split('\n')
        in_async_method = False
        for line in lines:
            if 'async def' in line and 'execute' not in line:
                in_async_method = True
            elif 'def ' in line and in_async_method:
                in_async_method = False
            if in_async_method and 'asyncio.run(' in line:
                has_asyncio_run_in_async = True
    
    # Also check that execute() method exists (the sync-to-async bridge)
    has_bridge = False
    for f in files_to_check:
        src = read_source(f)
        if "def execute" in src and "async" not in src.split("def execute")[0].split("\n")[-1]:
            has_bridge = True
    
    report("BUG-035 asyncio.run in async methods", not has_asyncio_run_in_async and has_bridge,
           f"No asyncio.run in async methods: {not has_asyncio_run_in_async}, Bridge exists: {has_bridge}")
except Exception as e:
    report("BUG-035 asyncio.run check", False, f"Error: {e}")

try:
    # Check asyncio.get_event_loop() replaced
    files_with_get_event_loop = [
        "backend/api/routes/chat.py",
        "tools/web_search.py",
        "tools/code_exec.py",
        "tools/system_monitor.py"
    ]
    has_old_pattern = False
    for f in files_with_get_event_loop:
        try:
            src = read_source(f)
            if "asyncio.get_event_loop()" in src:
                has_old_pattern = True
        except:
            pass
    report("BUG-035 get_event_loop replaced", not has_old_pattern,
           f"All replaced: {not has_old_pattern}")
except Exception as e:
    report("BUG-035 get_event_loop check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# BUG-036: Dangerous __del__ cleanup
# ─────────────────────────────────────────────
print("\n── BUG-036: Browser Cleanup Fix ──")

try:
    # Check __del__ is removed from BrowserTool
    src = read_source("tools/browser.py")
    has_del = "def __del__" in src
    has_enter_exit = "__enter__" in src and "__exit__" in src
    report("BUG-036 __del__ removed, context manager exists", not has_del and has_enter_exit,
           f"__del__ removed: {not has_del}, Context manager: {has_enter_exit}")
except Exception as e:
    report("BUG-036 check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# BUG-039: StaticFiles routing
# ─────────────────────────────────────────────
print("\n── BUG-039: StaticFiles Route Order ──")

try:
    # Check root endpoint defined before StaticFiles
    src = read_source("backend/main.py")
    
    # Find positions
    root_def = src.find('async def root(')
    health_def = src.find('async def health(')
    static_mount = src.find('app.mount("/"')
    
    # Both should be before static mount
    root_before_static = root_def > 0 and (static_mount < 0 or root_def < static_mount)
    health_before_static = health_def > 0 and (static_mount < 0 or health_def < static_mount)
    
    report("BUG-039 Root endpoint before StaticFiles", root_before_static and health_before_static,
           f"Root before mount: {root_before_static}, Health before mount: {health_before_static}")
except Exception as e:
    report("BUG-039 check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
print("\n" + "="*60)
passed = sum(1 for _, p in results if p)
total = len(results)
print(f"  Results: {passed}/{total} checks passed")
print("="*60 + "\n")

# Exit with appropriate code
sys.exit(0 if passed == total else 1)
