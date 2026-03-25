"""
B-5 UAT Test Suite - Final Strict Version
Covers: BUG-029, BUG-030, BUG-034, BUG-035, BUG-036, BUG-039
"""

import sys
import os
import re
import ast

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
    full = os.path.join(PROJECT_ROOT, filepath)
    with open(full, "r", encoding="utf-8") as f:
        return f.read()

print("\n" + "="*75)
print("  B-5 UAT — Polish + Routing  (Final Strict Checks)")
print("="*75 + "\n")

# ─────────────────────────────────────────────
# BUG-029: Hardcoded localhost:8000
# ─────────────────────────────────────────────
print("── BUG-029: URL Configuration ──")

try:
    src = read_source("cli/client.py")
    uses_config = bool(re.search(r'(Config\(\)|config\.(ui_host|ui_port|base_url|server_url))', src))
    no_hardcode = "localhost:8000" not in src and "http://localhost:8000" not in src

    report("BUG-029 CLI uses Config (no hard-coded URL)",
           uses_config and no_hardcode)
except Exception as e:
    report("BUG-029 CLI check", False, f"Error: {e}")

try:
    src = read_source("ui/src/App.tsx")
    uses_dynamic = "window.location" in src and ("host" in src or "origin" in src)
    no_hardcode = "localhost:8000" not in src and "http://localhost:8000" not in src

    report("BUG-029 UI uses dynamic window.location (no hardcode)",
           uses_dynamic and no_hardcode)
except Exception as e:
    report("BUG-029 UI check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# BUG-030: HTTP fallback wrong endpoint
# ─────────────────────────────────────────────
print("\n── BUG-030: HTTP Fallback Endpoint ──")

try:
    src = read_source("cli/client.py")
    correct = bool(re.search(r'["\']?/api/chat["\']?', src))
    wrong_in_http = False
    if "_chat_http" in src:
        http_section = src.split("async def _chat_http")[1].split("async def")[0]
        wrong_in_http = "/ws/chat" in http_section

    report("BUG-030 HTTP fallback uses /api/chat (not /ws/chat)",
           correct and not wrong_in_http)
except Exception as e:
    report("BUG-030 fallback check", False, f"Error: {e}")

try:
    src = read_source("backend/api/routes/chat.py")
    proper_route = bool(re.search(r'@router\.post\s*\(\s*["\']?/api/chat["\']?', src))
    report("BUG-030 /api/chat POST route correctly defined with @router.post",
           proper_route)
except Exception as e:
    report("BUG-030 endpoint check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# BUG-034: Dead code
# ─────────────────────────────────────────────
print("\n── BUG-034: Dead Code Removal ──")
try:
    src = read_source("tools/web_search.py")
    report("BUG-034 _highlight_important fully removed",
           "_highlight_important" not in src)
except Exception as e:
    report("BUG-034 check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# BUG-035: Async patterns
# ─────────────────────────────────────────────
print("\n── BUG-035: Async Pattern Fixes ──")

try:
    files = ["tools/microsoft_outlook.py", "tools/auth/microsoft.py", "brain/chains.py"]
    forbidden_run = False
    has_bridge = False

    for f in files:
        src = read_source(f)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name != "execute":
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        func = child.func
                        if (isinstance(func, ast.Name) and func.id == "asyncio_run") or \
                           (isinstance(func, ast.Attribute) and func.attr == "run" and 
                            isinstance(func.value, ast.Name) and func.value.id == "asyncio"):
                            forbidden_run = True

            if isinstance(node, ast.FunctionDef) and node.name == "execute":
                has_bridge = True

    report("BUG-035 No asyncio.run() inside async methods + execute bridge present",
           not forbidden_run and has_bridge)
except Exception as e:
    report("BUG-035 asyncio.run check", False, f"Error: {e}")

try:
    files = ["backend/api/routes/chat.py", "tools/web_search.py", "tools/code_exec.py", "tools/system_monitor.py"]
    still_has_old = any("asyncio.get_event_loop()" in read_source(f) for f in files)
    report("BUG-035 asyncio.get_event_loop() completely replaced",
           not still_has_old)
except Exception as e:
    report("BUG-035 get_event_loop check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# BUG-036: __del__ cleanup
# ─────────────────────────────────────────────
print("\n── BUG-036: Browser Cleanup Fix ──")
try:
    src = read_source("tools/browser.py")
    has_del = "def __del__" in src
    has_context = "__enter__" in src and "__exit__" in src
    report("BUG-036 __del__ removed + context manager used",
           not has_del and has_context)
except Exception as e:
    report("BUG-036 check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# BUG-039: Route order
# ─────────────────────────────────────────────
print("\n── BUG-039: StaticFiles Route Order ──")
try:
    src = read_source("backend/main.py")
    root_pos = src.find("async def root(")
    health_pos = src.find("async def health(")
    mount_pos = src.find('app.mount("/"')

    root_ok = root_pos != -1 and (mount_pos == -1 or root_pos < mount_pos)
    health_ok = health_pos != -1 and (mount_pos == -1 or health_pos < mount_pos)

    report("BUG-039 Root & Health endpoints BEFORE StaticFiles mount",
           root_ok and health_ok)
except Exception as e:
    report("BUG-039 check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
print("\n" + "="*75)
passed = sum(1 for _, p in results if p)
total = len(results)
print(f"  Final Results: {passed}/{total} checks passed")
print("="*75 + "\n")

sys.exit(0 if passed == total else 1)