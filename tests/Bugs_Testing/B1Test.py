"""
B-1 UAT Test Suite
Run from project root: PYTHONIOENCODING=utf-8 python tests/Bugs_Testing/B1Test.py
Covers: BUG-001, 003, 004, 005, 011, 012, 013, 014, 015, 016, 017, 018, 025, 027, 031, 032, 033, 038
Total: 27 checks across 18 bugs (17 core + 1 gap fix)
"""

import sys
import os
import re

# Add project root to path so 'brain', 'voice', etc. imports work
# B1Test.py is at: JARVISE/tests/Bugs_Testing/B1Test.py
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
print("  B-1 UAT — Core Chat Foundation")
print("="*60 + "\n")

# ─────────────────────────────────────────────
# B-1.1 — BUG-001: setup_logging double definition
# ─────────────────────────────────────────────
print("── B-1.1 | BUG-001: setup_logging shadow ──")
try:
    src = read_source("main.py")
    # Count local definitions of setup_logging in main.py
    define_count = len(re.findall(r"^def setup_logging", src, re.MULTILINE))
    passed = define_count == 0
    report("BUG-001 no local setup_logging definition in main.py", passed,
           f"Found {define_count} local definition(s) (expect 0)")
except Exception as e:
    report("BUG-001 setup_logging check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# B-1.1 — BUG-031: redundant load_config branch
# ─────────────────────────────────────────────
print("\n── B-1.1 | BUG-031: load_config redundant branch ──")
try:
    src = read_source("core/config.py")
    # Both branches calling Config() identically
    has_redundant = bool(re.search(
        r"if env_path\.exists\(\).*?Config\(\).*?else.*?Config\(\)",
        src, re.DOTALL
    ))
    passed = not has_redundant
    report("BUG-031 no redundant if/else in load_config", passed,
           "Redundant branch removed ✅" if passed else "Both branches still call Config() identically")
except Exception as e:
    report("BUG-031 load_config check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# B-1.2 — BUG-005: multiple system messages
# ─────────────────────────────────────────────
print("\n── B-1.2 | BUG-005: single system message ──")
try:
    from brain.prompt_builder import PromptBuilder
    pb = PromptBuilder()
    messages = pb.build(
        user_input={"role": "user", "content": "hello"},
        memory_context="test memory",
        vector_context=["ctx1", "ctx2"]
    )
    system_count = sum(1 for m in messages if m["role"] == "system")
    passed = system_count == 1
    report("BUG-005 exactly one system message", passed,
           f"Found {system_count} system message(s) (expect 1)")

    if system_count == 1:
        sys_content = next(m["content"] for m in messages if m["role"] == "system")
        has_memory = "test memory" in sys_content
        has_vector = "ctx1" in sys_content
        report("BUG-005 memory merged into system message", has_memory,
               "memory_context found in system message ✅" if has_memory else "memory_context MISSING")
        report("BUG-005 vector context merged into system message", has_vector,
               "vector_context found in system message ✅" if has_vector else "vector_context MISSING")
except Exception as e:
    report("BUG-005 system message check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# B-1.2 — BUG-003: stream_run saves blank to history
# ─────────────────────────────────────────────
print("\n── B-1.2 | BUG-003: stream_run full_response ──")
try:
    src = read_source("brain/agent.py")
    stream_run_src = src[src.find("def stream_run"):]
    next_def = stream_run_src.find("\n    def ", 1)
    stream_run_body = stream_run_src[:next_def] if next_def != -1 else stream_run_src
    # full_response = content must appear BEFORE if action_name is None
    full_resp_pos = stream_run_body.find("full_response = content")
    action_none_pos = stream_run_body.find("if action_name is None")
    passed = full_resp_pos != -1 and full_resp_pos < action_none_pos
    report("BUG-003 full_response=content before action_name check", passed,
           "full_response updated before branch ✅" if passed else
           "full_response NOT updated before action_name is None check")
except Exception as e:
    report("BUG-003 stream_run check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# B-1.2 — BUG-004: _clean_response called in stream_run
# ─────────────────────────────────────────────
print("\n── B-1.2 | BUG-004: _clean_response in stream_run ──")
try:
    src = read_source("brain/agent.py")
    stream_run_src = src[src.find("def stream_run"):]
    next_def = stream_run_src.find("\n    def ", 1)
    stream_run_body = stream_run_src[:next_def] if next_def != -1 else stream_run_src
    has_clean = "_clean_response" in stream_run_body
    passed = has_clean
    report("BUG-004 _clean_response called in stream_run", passed,
           "_clean_response found in stream_run ✅" if passed else
           "_clean_response NOT called — raw Thought:/Action: lines still yielded")
except Exception as e:
    report("BUG-004 _clean_response check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# B-1.3 — BUG-011: lazy tool instantiation
# ─────────────────────────────────────────────
print("\n── B-1.3 | BUG-011: lazy tool instantiation ──")
try:
    src = read_source("brain/tools.py")
    create_fn = src[src.find("def create_tools_registry"):]
    # Tools should NOT be instantiated eagerly at top level of create_tools_registry
    # Check first 700 chars where eager calls would appear (before lazy guard patterns)
    eager_patterns = [
        "BrowserTool()",
        "GoogleCalendarTool()",
        "MicrosoftOutlookTool()",
        "WebSearchTool()",
        "SystemMonitorTool()",
    ]
    found_eager = [p for p in eager_patterns if p in create_fn[:700]]
    passed = len(found_eager) == 0
    report("BUG-011 no eager tool instantiation at startup", passed,
           f"All tools lazy ✅" if passed else f"Eager init found: {found_eager}")
except Exception as e:
    report("BUG-011 lazy init check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# B-1.3 — BUG-012: web_search arg name
# ─────────────────────────────────────────────
print("\n── B-1.3 | BUG-012: web_search num_results arg ──")
try:
    src = read_source("brain/tools.py")
    # Should use num_results not max_results when calling execute
    has_wrong = "max_results=max_results" in src
    has_right = "num_results=max_results" in src
    passed = not has_wrong and has_right
    report("BUG-012 num_results used (not max_results)", passed,
           "num_results= ✅" if passed else
           "Still using max_results= — WebSearchTool will ignore it")
except Exception as e:
    report("BUG-012 arg name check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# B-1.3 — BUG-013: invalidate_cache None guard
# ─────────────────────────────────────────────
print("\n── B-1.3 | BUG-013: invalidate_cache None guard ──")
try:
    from brain.tools import ToolRegistry
    registry = ToolRegistry()
    # Should return 0 without crashing
    result = registry.invalidate_cache()
    passed = result == 0
    report("BUG-013 invalidate_cache returns 0 when cache=None", passed,
           f"Returned {result} (expect 0, no crash)")
except TypeError as e:
    report("BUG-013 invalidate_cache None guard", False, f"TypeError: {e}")
except Exception as e:
    report("BUG-013 invalidate_cache None guard", False, f"Error: {e}")

# ─────────────────────────────────────────────
# B-1.3 — BUG-014: _action_pattern multi-line JSON
# ─────────────────────────────────────────────
print("\n── B-1.3 | BUG-014: _action_pattern multi-line JSON ──")
try:
    from brain.tools import ToolRegistry
    registry = ToolRegistry()
    # Multi-line JSON in action
    test_response = 'Thought: I need to search for something\nAction: search_web: {"query": "test query",\n"num_results": 5}'
    thought, action_name, action_args = registry.parse_action(test_response)
    passed = action_name is not None and action_name.lower() == "search_web"
    report("BUG-014 parse_action handles multi-line JSON", passed,
           f"action_name='{action_name}', args parsed correctly ✅" if passed else
           f"Failed to parse — action_name={action_name}")
except Exception as e:
    report("BUG-014 multi-line JSON parse", False, f"Error: {e}")

# ─────────────────────────────────────────────
# B-1.3 — BUG-015: merged registries
# ─────────────────────────────────────────────
print("\n── B-1.3 | BUG-015: merged tool registries ──")
try:
    from brain.tools import create_tools_registry
    registry = create_tools_registry()
    tools = list(registry.list_tools().keys())

    basic_tools = ["remember", "recall", "forget", "get_time", "get_date"]
    heavy_tools = ["browser", "web_search", "filesystem"]

    missing_basic = [t for t in basic_tools if t not in tools]
    missing_heavy = [t for t in heavy_tools if t not in tools]

    passed_basic = len(missing_basic) == 0
    passed_heavy = len(missing_heavy) == 0

    report("BUG-015 basic tools present (remember/recall/forget)", passed_basic,
           f"All basic tools ✅" if passed_basic else f"Missing: {missing_basic}")
    report("BUG-015 heavy tools present (browser/calendar etc.)", passed_heavy,
           f"All heavy tools ✅" if passed_heavy else f"Missing: {missing_heavy}")
    report("BUG-015 total tool count reasonable", len(tools) >= 8,
           f"Total tools registered: {len(tools)}")
except Exception as e:
    report("BUG-015 merged registry check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# B-1.3 — BUG-018: search_web not using DDG regex
# ─────────────────────────────────────────────
print("\n── B-1.3 | BUG-018: search_web uses duckduckgo-search ──")
try:
    src = read_source("brain/tools.py")
    has_ddg_import = "duckduckgo_search" in src or "DDGS" in src
    has_old_regex = 'class="result__a"' in src or "result__snippet" in src
    passed1 = has_ddg_import
    passed2 = not has_old_regex
    report("BUG-018 duckduckgo-search package used", passed1,
           "DDGS import found ✅" if passed1 else "duckduckgo_search NOT imported")
    report("BUG-018 old DDG HTML selectors removed", passed2,
           "Old selectors gone ✅" if passed2 else "Old result__a selectors still present")
except Exception as e:
    report("BUG-018 DDG search check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# B-1.4 — BUG-025: shared app.state
# ─────────────────────────────────────────────
print("\n── B-1.4 | BUG-025: shared app.state ──")
try:
    src = read_source("backend/main.py")
    has_app_state = "app.state" in src
    has_lifespan_agent = "app.state.agent" in src

    chat_src = read_source("backend/api/routes/chat.py")
    memory_src = read_source("backend/api/routes/memory.py")

    # Routes should NOT create their own singletons
    chat_singleton = bool(re.search(r"^agent\s*=\s*ReActAgent", chat_src, re.MULTILINE))
    memory_singleton = bool(re.search(r"^_memory_manager\s*=\s*MemoryManager", memory_src, re.MULTILINE))

    report("BUG-025 app.state used in backend/main.py", has_app_state,
           "app.state found ✅" if has_app_state else "app.state NOT found")
    report("BUG-025 agent on app.state in lifespan", has_lifespan_agent,
           "app.state.agent ✅" if has_lifespan_agent else "app.state.agent NOT set")
    report("BUG-025 chat.py no route-level agent singleton", not chat_singleton,
           "No singleton in chat.py ✅" if not chat_singleton else "chat.py still creates own agent")
    report("BUG-025 memory.py no route-level memory singleton", not memory_singleton,
           "No singleton in memory.py ✅" if not memory_singleton else "memory.py still creates own MemoryManager")
except Exception as e:
    report("BUG-025 shared state check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# B-1.5 — BUG-032: enum comparison not string
# ─────────────────────────────────────────────
print("\n── B-1.5 | BUG-032: enum not string comparison ──")
try:
    src = read_source("main.py")
    has_string_compare = '.route_type.value ==' in src or \
                         '== "direct_tool"' in src or \
                         '== "llm_agent"' in src
    passed = not has_string_compare
    report("BUG-032 no .value string comparison in main.py", passed,
           "Enum used directly ✅" if passed else "Still using .value == string comparison")
except Exception as e:
    report("BUG-032 enum check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# B-1.5 — BUG-016: fuzzy match length ratio guard
# ─────────────────────────────────────────────
print("\n── B-1.5 | BUG-016: fuzzy match false positives ──")
try:
    from brain.router import CommandRouter, RouteType
    from brain.tools import create_tools_registry
    router = CommandRouter(tool_registry=create_tools_registry())

    # "hi" should NOT match any direct tool command
    result = router.route("hi")
    not_false_positive = result.route_type != RouteType.DIRECT_TOOL or \
                         (result.confidence is not None and result.confidence < 0.7)
    passed = not_false_positive
    report("BUG-016 'hi' not matched as direct tool", passed,
           f"route_type={result.route_type.value}, confidence={result.confidence:.2f}")
except Exception as e:
    report("BUG-016 fuzzy match check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# B-1.5 — BUG-017: wildcard substitution extracts portion only
# ─────────────────────────────────────────────
print("\n── B-1.5 | BUG-017: wildcard substitution ──")
try:
    from brain.router import CommandRouter, RouteType
    from brain.tools import create_tools_registry
    router = CommandRouter(tool_registry=create_tools_registry())

    test_cases = [
        ("search black holes", "query", "black holes"),
        ("google latest news", "query", "latest news"),
    ]

    for user_input, arg_key, expected in test_cases:
        result = router.route(user_input)
        if result.tool_args and arg_key in result.tool_args:
            query = result.tool_args[arg_key]
            # The command word itself should NOT be in the extracted query
            has_cmd_word = any(
                user_input.lower().startswith(w + " ") and query.lower().startswith(w)
                for w in ["search", "google"]
            )
            passed = not has_cmd_word and query.strip() == expected
            report(f"BUG-017 wildcard extracts '{expected}' not full input", passed,
                   f"query='{query}' ✅" if passed else f"query='{query}' (expect '{expected}')")
        else:
            report(f"BUG-017 wildcard extraction for '{user_input}'", False,
                   f"No {arg_key} in tool_args — route_type={result.route_type.value}")
except Exception as e:
    report("BUG-017 wildcard check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# B-1.5 — BUG-033: UNKNOWN increments llm_agent_calls
# ─────────────────────────────────────────────
print("\n── B-1.5 | BUG-033: UNKNOWN stats tracking ──")
try:
    src = read_source("main.py")
    has_unknown_llm_count = bool(re.search(
        r"UNKNOWN.*?llm_agent_calls|llm_agent_calls.*?UNKNOWN",
        src, re.DOTALL | re.IGNORECASE
    ))
    router_src = read_source("brain/router.py")
    unknown_routes_to_llm = bool(re.search(
        r"UNKNOWN.*?LLM_AGENT|RouteType\.LLM_AGENT.*?unknown",
        router_src, re.DOTALL | re.IGNORECASE
    ))
    passed = has_unknown_llm_count or unknown_routes_to_llm
    report("BUG-033 UNKNOWN routes counted in llm_agent_calls", passed,
           "Stats tracking fixed ✅" if passed else
           "UNKNOWN still not counted as LLM call in stats")
except Exception as e:
    report("BUG-033 stats check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# B-1.6 — BUG-038: requirements.txt clean
# ─────────────────────────────────────────────
print("\n── B-1.6 | BUG-038: requirements.txt ──")
try:
    src = read_source("requirements.txt")

    # Should NOT have both kokoro packages
    has_kokoro = "kokoro>=" in src or "kokoro ==" in src
    has_kokoro_onnx = "kokoro-onnx" in src
    both_kokoro = has_kokoro and has_kokoro_onnx
    passed_kokoro = not both_kokoro
    report("BUG-038 no duplicate kokoro packages", passed_kokoro,
           "Single TTS package ✅" if passed_kokoro else
           "Both kokoro AND kokoro-onnx present — will conflict on install")

    # Should have required packages
    required = ["duckduckgo-search", "requests", "msal", "librosa"]
    missing = [p for p in required if p not in src]
    passed_deps = len(missing) == 0
    report("BUG-038 all required packages present", passed_deps,
           "All deps ✅" if passed_deps else f"Missing: {missing}")

except Exception as e:
    report("BUG-038 requirements check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# GAP FIX — BUG-027: filtered memory uses real ChromaDB
# ─────────────────────────────────────────────
print("\n── GAP FIX | BUG-027: filtered memory persistence ──")
try:
    memory_src = read_source("backend/api/routes/memory.py")
    has_none_client = "FilteredMemory(chroma_client=None)" in memory_src or \
                      "FilteredMemory(None)" in memory_src

    passed1 = not has_none_client
    report("BUG-027 FilteredMemory not constructed with None", passed1,
           "Real ChromaDB client passed ✅" if passed1 else
           "FilteredMemory(chroma_client=None) still present — in-memory only, loses data on restart")

    has_dependency = "get_filtered_memory" in memory_src or \
                     "app.state" in memory_src or \
                     "Depends(" in memory_src
    report("BUG-027 filtered memory uses dependency injection", has_dependency,
           "Dependency injection found ✅" if has_dependency else
           "No DI found — may still be using singleton")

except Exception as e:
    report("BUG-027 filtered memory check", False, f"Error: {e}")

# ─────────────────────────────────────────────
# E2E: Full Chat Round Trip
# ─────────────────────────────────────────────
print("\n── E2E: Full Chat Round Trip ──")
try:
    from brain.agent import ReActAgent
    from brain.tools import create_tools_registry
    from brain.prompt_builder import PromptBuilder

    pb = PromptBuilder()
    agent = ReActAgent(tool_registry=create_tools_registry(), prompt_builder=pb)
    response = agent.run("what time is it")

    passed1 = isinstance(response, str) and len(response) > 0 and "Sorry" not in response
    report("E2E agent returns real response", passed1,
           f"'{response[:80]}'" if len(response) <= 80 else f"'{response[:80]}...'")

    has_raw = response.strip().startswith("Thought:") or "\nThought:" in response
    report("E2E response has no raw Thought:/Action: lines", not has_raw,
           "Clean ✅" if not has_raw else "Raw Thought: lines found")

    report("E2E conversation saved to history", len(pb.conversation_history) >= 2,
           f"{len(pb.conversation_history)} messages in history")
except Exception as e:
    report("E2E chat round trip", False, f"Ollama running? error: {e}")

# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────
print("\n" + "="*60)
print("  RESULTS")
print("="*60)
passed_count = sum(1 for _, p in results if p)
total = len(results)
for name, p in results:
    print(f"  {'✅' if p else '❌'} {name}")
print(f"\n  {passed_count}/{total} passed")
if passed_count == total:
    print("  🔥 B-1 UAT COMPLETE — approved to close")
else:
    failed = [name for name, p in results if not p]
    print(f"  ⚠️  {total - passed_count} test(s) failing:")
    for f in failed:
        print(f"     ❌ {f}")
print("="*60 + "\n")
sys.exit(0 if passed_count == total else 1)
