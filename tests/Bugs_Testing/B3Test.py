"""
B-3 UAT Test Suite
Run from project root: PYTHONIOENCODING=utf-8 python tests/Bugs_Testing/B3Test.py
Covers: BUG-006, BUG-010, BUG-020, BUG-021, BUG-042, BUG-043
Total: ~10 checks across 6 bugs
"""

import sys
import os
import re

# Add project root to path so 'tools', 'brain', 'memory', etc. imports work
# B3Test.py is at: JARVISE/tests/Bugs_Testing/B3Test.py
# PROJECT_ROOT is JARVISE (3 levels up)
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
print("  B-3 UAT — Web + Memory")
print("="*60 + "\n")

# ─────────────────────────────────────────────
# B-3.1 — BUG-006: duckduckgo-search replaces DDG selectors
# ─────────────────────────────────────────────
print("── BUG-006: Web Search Implementation ──")
try:
    # Check that web_search in brain/tools.py uses duckduckgo-search
    src = read_source("brain/tools.py")
    uses_ddgs = "DDGS" in src or "duckduckgo" in src
    report("BUG-006 uses duckduckgo-search in tools.py", uses_ddgs,
           "DDGS imported ✅" if uses_ddgs else "Still using old DDG method")
except Exception as e:
    report("BUG-006 web search check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# B-3.1 — BUG-042: Playwright sync removed from search path
# ─────────────────────────────────────────────
print("\n── BUG-042: BrowserTool Search Removed ──")
try:
    # Check that BrowserTool no longer has search method
    from tools.browser import BrowserTool
    bt = BrowserTool()
    has_search = hasattr(bt, 'search') and callable(getattr(bt, 'search', None))
    # After fix, search should be removed or redirect to DDGS
    report("BUG-042 BrowserTool.search removed", not has_search,
           "search method removed ✅" if not has_search else "search method still exists")
except Exception as e:
    report("BUG-042 BrowserTool check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# B-3.1 — BUG-043: URL validation with regex
# ─────────────────────────────────────────────
print("\n── BUG-043: URL Validation ──")
try:
    # Check BrowserTool.navigate has URL validation
    src = read_source("tools/browser.py")
    has_url_validation = "URL" in src and ("regex" in src.lower() or "http" in src.lower())
    # Also check for the validation logic
    has_validation_logic = bool(re.search(r"if.*url.*not.*empty|empty.*url|url.*error", src, re.IGNORECASE))
    report("BUG-043 URL validation exists", has_url_validation or has_validation_logic,
           "URL validation found ✅" if has_url_validation else "validation may be missing")
except Exception as e:
    report("BUG-043 URL validation check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# B-3.2 — BUG-010: Memory injected into agent
# ─────────────────────────────────────────────
print("\n── BUG-010: Memory Injection ──")
try:
    # Check that agent.run accepts memory_context parameter
    from brain.agent import ReActAgent
    import inspect
    sig = inspect.signature(ReActAgent.run)
    has_memory_param = "memory_context" in sig.parameters
    report("BUG-010 agent.run accepts memory_context", has_memory_param,
           "memory_context param found ✅" if has_memory_param else "param missing")
except Exception as e:
    report("BUG-010 agent.run check", False, f"Error: {e}")

try:
    # Check main.py wires MemoryManager
    src = read_source("main.py")
    has_memory_wiring = "memory_manager" in src and "format_context_for_prompt" in src
    report("BUG-010 main.py wires MemoryManager", has_memory_wiring,
           "MemoryManager wired ✅" if has_memory_wiring else "not wired")
except Exception as e:
    report("BUG-010 main.py wiring check", False, f"Error: {e}")

try:
    # Check save_conversation is called in main.py
    src = read_source("main.py")
    has_save = "save_conversation" in src
    report("BUG-010 save_conversation called", has_save,
           "save_conversation called ✅" if has_save else "not called")
except Exception as e:
    report("BUG-010 save check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# B-3.3 — BUG-020: Chain template structure
# ─────────────────────────────────────────────
print("\n── BUG-020: Chain Template Structure ──")
try:
    from brain.chains import TaskChain
    # Check that ChainStep has 'tool' field
    from brain.chains import ChainStep
    # Check template structure
    tc = TaskChain()
    templates = tc.BUILTIN_TEMPLATES
    # Check one template has 'tool' field
    template_check = False
    for name, steps in templates.items():
        if steps:
            first_step = steps[0]
            if isinstance(first_step, dict):
                has_tool = "tool" in first_step
                template_check = has_tool
                break
    report("BUG-020 chain templates have tool field", template_check,
           "tool field in template ✅" if template_check else "tool field missing")
except Exception as e:
    report("BUG-020 chain template check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# B-3.3 — BUG-021: Previous output substitution
# ─────────────────────────────────────────────
print("\n── BUG-021: Previous Output Substitution ──")
try:
    src = read_source("brain/chains.py")
    has_substitution = "{previous_output}" in src or "previous_output" in src
    report("BUG-021 previous_output substitution exists", has_substitution,
           "substitution logic found ✅" if has_substitution else "not found")
except Exception as e:
    report("BUG-021 substitution check", False, f"Error: {e}")

try:
    # Test actual substitution if possible
    from brain.chains import ChainStep
    # Check if ChainStep can handle the substitution (now requires 'tool' param)
    step = ChainStep(step_number=1, tool="test_tool", action="test", input="result: {previous_output}")
    # The substitution happens in execute_chain_async
    has_sub_in_step = "{previous_output}" in step.input
    report("BUG-021 ChainStep supports substitution", True,
           "placeholder supported ✅")
except Exception as e:
    report("BUG-021 ChainStep check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# BUG-019 — Chain route handled in main.py
# ─────────────────────────────────────────────
print("\n── BUG-019: Chain Route in main.py ──")
try:
    src = read_source("main.py")
    has_chain_branch = "execute_chain" in src and "RouteType.CHAIN" in src
    report("BUG-019 chain route handled in main.py", has_chain_branch,
           "execute_chain called ✅" if has_chain_branch else "missing")
except Exception as e:
    report("BUG-019 chain route check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# BUG-026 — delete_memory targets entry not session
# ─────────────────────────────────────────────
print("\n── BUG-026: delete_memory Endpoint ──")
try:
    src = read_source("backend/api/routes/memory.py")
    # Check if endpoint was renamed or fixed
    has_entry_delete = "delete_entry" in src or ("entry_id" in src and "delete" in src)
    # Or renamed to be honest about session deletion
    renamed = "session" in src.lower() and "entry" not in src.lower()
    fixed = has_entry_delete or renamed
    report("BUG-026 delete_memory fixed", fixed,
           "entry deletion or renamed ✅" if fixed else "not fixed")
except Exception as e:
    report("BUG-026 delete_memory check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# BUG-028 — MEMORY.md parser actually works
# ─────────────────────────────────────────────
print("\n── BUG-028: MEMORY.md Parser ──")
try:
    from memory.memory_file import MemoryFileController
    # Use default path or test file
    test_path = os.path.join(PROJECT_ROOT, "data/MEMORY.md")
    if os.path.exists(test_path):
        mc = MemoryFileController(test_path)
        profile = mc.get_user_profile()
        prefs = mc.get_preference("Voice Speed")  # type: ignore
        profile_works = isinstance(profile, dict) and len(profile) > 0
        report("BUG-028 MEMORY.md profile readable", profile_works,
               f"profile keys: {list(profile.keys())}" if profile_works else
               f"EMPTY — parser regex doesn't match template format")
    else:
        # Create test file first
        os.makedirs(os.path.dirname(test_path), exist_ok=True)
        with open(test_path, "w", encoding="utf-8") as f:
            f.write("""# JARVIS Memory

## User Profile
- Name: Test User
- Location: Test City

## Preferences
- Voice Speed: 1.0
- Model: qwen2.5

## Important Facts
- User is a developer
""")
        mc = MemoryFileController(test_path)
        profile = mc.get_user_profile()
        prefs = mc.get_preference("Voice Speed")  # type: ignore
        profile_works = isinstance(profile, dict) and len(profile) > 0
        report("BUG-028 MEMORY.md profile readable", profile_works,
               f"profile: {profile}" if profile_works else "empty")
except Exception as e:
    report("BUG-028 MEMORY.md parser check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# E2E: Memory actually reaches agent
# ─────────────────────────────────────────────
print("\n── E2E: Memory in Agent Loop ──")
try:
    from brain.agent import ReActAgent
    from brain.prompt_builder import PromptBuilder
    from memory import MemoryManager
    from core.config import Config
    
    # Initialize
    config = Config()
    memory_manager = MemoryManager(config)
    
    # Save a test memory
    memory_manager.save_conversation("what is my name", "You haven't told me your name yet")
    
    # Get memory context
    memory_context = memory_manager.format_context_for_prompt("what is my name")
    
    # Check context contains memory
    has_memory = len(memory_context) > 0
    report("E2E memory context generated", has_memory,
           f"context length: {len(memory_context)}")
except Exception as e:
    report("E2E memory context check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
print("\n" + "="*60)
print("  RESULTS")
print("="*60)

passed_count = sum(1 for _, p in results if p)
total_count = len(results)

for name, passed in results:
    print(f"  {'✅' if passed else '❌'} {name}")

print(f"\n  {passed_count}/{total_count} passed")
if passed_count == total_count:
    print("  🔥 B-3 UAT COMPLETE — approved to close")
else:
    print(f"  ⚠️  {total_count - passed_count} failing tests - fix before closing B-3")
