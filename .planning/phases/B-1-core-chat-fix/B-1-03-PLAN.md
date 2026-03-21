---
phase: B-1-core-chat-fix
plan: '03'
type: execute
wave: 1
depends_on: []
files_modified:
  - main.py
  - core/config.py
  - brain/router.py
  - backend/main.py
  - backend/api/routes/chat.py
  - backend/api/routes/memory.py
  - backend/api/dependencies.py
  - requirements.txt
autonomous: true
requirements:
  - BL-05
  - HW-04
must_haves:
  truths:
    - "main.py uses imported setup_logging, not local duplicate"
    - "core/config.py load_config is simple and clean"
    - "Router uses enum comparison, not string comparison"
    - "Fuzzy match has length ratio guard to prevent false positives"
    - "Wildcard substitution extracts only the wildcard portion"
    - "Backend shares one agent/memory/router via app.state"
    - "No route-level singletons exist"
    - "requirements.txt has no kokoro conflict, includes duckduckgo-search"
  artifacts:
    - path: main.py
      provides: No duplicate setup_logging, enum router comparison
      min_lines: 340
    - path: backend/api/dependencies.py
      provides: Dependency injectors for agent, memory, router
      min_lines: 90
    - path: requirements.txt
      provides: Fixed dependency list
      min_lines: 50
  key_links:
    - from: main.py
      to: core.logger
      via: uses imported setup_logging (line 20), no local redefinition
      pattern: from core.logger import setup_logging
    - from: backend/main.py
      to: backend/api/routes/chat.py
      via: app.state.agent attached in lifespan
      pattern: app.state.agent.*ReActAgent
    - from: backend/api/routes/chat.py
      to: backend/api/dependencies.py
      via: get_agent(request) dependency
      pattern: Depends\(get_agent\)
---

<objective>
Fix logging/config (B-1.1), backend state sharing (B-1.4), router (B-1.5), and dependencies (B-1.6).
Purpose: Remove duplicate code, fix router enum comparison, implement shared backend state, fix dependency conflicts.
Output: main.py, core/config.py, brain/router.py, backend/main.py, backend/api/routes/chat.py, backend/api/routes/memory.py, backend/api/dependencies.py, requirements.txt
</objective>

<context>
@main.py
@core/config.py
@brain/router.py
@backend/main.py
@backend/api/routes/chat.py
@backend/api/routes/memory.py
@backend/api/dependencies.py
@requirements.txt
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix logging (main.py) + config (core/config.py)</name>
  <files>main.py, core/config.py</files>
  <action>
    B-1.1 Fix A — main.py (BUG-001):
    Delete the local setup_logging() function at lines 56-77 (the entire function definition). Keep the import at line 20: `from core.logger import setup_logging`. Change the call on line 166 from `setup_logging(args.verbose)` to `setup_logging(verbose=args.verbose)` — matching the imported function's signature from core/logger.py.

    B-1.1 Fix B — core/config.py (BUG-031):
    In load_config() (lines 209-240), remove the dead if/else branches. Replace:
    ```python
    env_path = Path(".env")
    if env_path.exists():
        try:
            config = Config()
        except Exception as e:
            raise ConfigValidationError(f"Failed to load configuration: {e}")
    else:
        config = Config()
    ```
    With simply: `config = Config()`
    
    Also move vram_mb setting and profile selection to happen unconditionally after the Config() call. The simplified load_config should be:
    ```python
    def load_config(vram_mb: int | None = None) -> Config:
        try:
            config = Config()
        except Exception as e:
            raise ConfigValidationError(f"Failed to load configuration: {e}")
        if vram_mb is not None:
            config.vram_mb = vram_mb
        config.profile = config.select_profile()
        return config
    ```
  </action>
  <verify>
    <automated>python -c "
# Check main.py: no local setup_logging function
with open('main.py', 'r') as f:
    content = f.read()

# Should import from core.logger
assert 'from core.logger import setup_logging' in content

# Should NOT have local setup_logging function definition
import re
local_def = re.search(r'^def setup_logging\(', content, re.MULTILINE)
assert not local_def, 'Local setup_logging still exists in main.py'
print('BUG-001 FIXED: setup_logging imported, not redefined')

# Check core/config.py: simplified load_config
with open('core/config.py', 'r') as f:
    cfg = f.read()

# Should not have duplicate if/else branches
assert cfg.count('config = Config()') == 1, f'Config() called {cfg.count(\"config = Config()\")} times'
print('BUG-031 FIXED: load_config simplified')
print('PASS: Logging + Config fixes')
"</automated>
  </verify>
  <done>main.py uses imported setup_logging, no local duplicate. core/config.py load_config simplified to single Config() call.</done>
</task>

<task type="auto">
  <name>Task 2: Fix router — enum comparison, fuzzy guard, wildcard substitution</name>
  <files>brain/router.py</files>
  <action>
    B-1.5 Fix A — Enum comparison in main.py (BUG-032):
    In main.py lines 270-280, change string comparisons to enum comparisons:
    ```python
    # Line 270: from
    if route_result.route_type.value == "direct_tool":
    # to:
    if route_result.route_type == RouteType.DIRECT_TOOL:

    # Line 274: from
    elif route_result.route_type.value == "llm_agent":
    # to:
    elif route_result.route_type == RouteType.LLM_AGENT:
    ```
    Make sure RouteType is imported at the top of main.py: `from brain.router import CommandRouter, RouteType`

    Also fix BUG-033: In main.py UNKNOWN route handling (line 278-280), add `self._stats.llm_agent_calls += 1` inside the else block:
    ```python
    else:
        # Unknown - default to LLM (safer)
        logger.info("Unknown command, routing to LLM")
        response = agent.run(user_input)
        router._stats.llm_agent_calls += 1  # Add this line
    ```

    B-1.5 Fix B — Fuzzy match length ratio guard (BUG-016):
    In brain/router.py _match_fuzzy() method, add length ratio check:
    In the loop (around line 467), change:
    ```python
    if distance < best_distance and distance <= 3:
    ```
    To:
    ```python
    if distance < best_distance and distance <= 3 and distance / max(len(normalized), len(pattern)) < 0.4:
    ```

    B-1.5 Fix C — Wildcard substitution extracts only wildcard portion (BUG-017):
    In _substitute_wildcards() method, replace the entire method (lines 499-511):
    ```python
    def _substitute_wildcards(self, args: dict, user_input: str) -> dict:
        """Substitute wildcard placeholders in tool arguments."""
        result = {}
        for key, value in args.items():
            if value == "*":
                # Extract from user input — extract ONLY the wildcard portion
                # Find which pattern this args came from by matching all wildcard patterns
                for pattern in self._direct_commands:
                    if self._direct_commands[pattern][0] == self._direct_commands.get(list(args.keys())[0]) or \
                       (pattern, self._direct_commands[pattern]) in [(k, tuple(self._direct_commands.get(k) or [])) for k in self._direct_commands]:
                        # Simple approach: strip matched prefix from user input
                        prefix = pattern.replace("*", "").strip()
                        wildcard_value = user_input.lower().replace(prefix, "").strip()
                        result[key] = wildcard_value if wildcard_value else user_input
                        break
                else:
                    result[key] = user_input
            elif isinstance(value, str) and "*" in value:
                # Handle patterns like "search *"
                prefix = value.rsplit("*", 1)[0].strip()
                wildcard_value = user_input.lower().replace(prefix, "").strip()
                result[key] = wildcard_value if wildcard_value else user_input
            else:
                result[key] = value
        return result
    ```
    The key insight: `prefix = pattern.replace("*", "").strip()` then `wildcard_value = user_input.lower().replace(prefix, "").strip()` extracts only the part after the matched prefix.
  </action>
  <verify>
    <automated>python -c "
import re

with open('main.py', 'r') as f:
    main_content = f.read()

# Check enum comparison used (not .value string)
assert 'route_result.route_type == RouteType.DIRECT_TOOL' in main_content, 'BUG-032: enum comparison not found'
assert '.value == \"direct_tool\"' not in main_content, 'BUG-032: string comparison still present'
assert 'route_result.route_type == RouteType.LLM_AGENT' in main_content, 'BUG-032: llm_agent enum not found'
print('BUG-032 FIXED: enum comparison in main.py')

# Check llm_agent_calls incremented on UNKNOWN
unknown_block = re.search(r'else:.*?Unknown command.*?agent\.run.*?llm_agent_calls', main_content, re.DOTALL)
assert unknown_block and 'llm_agent_calls' in unknown_block.group(), 'BUG-033: llm_agent_calls not incremented on UNKNOWN'
print('BUG-033 FIXED: llm_agent_calls incremented on UNKNOWN')

with open('brain/router.py', 'r') as f:
    router_content = f.read()

# Check fuzzy match has length ratio guard
fuzzy_match = re.search(r'_match_fuzzy.*?(?=def |class |\Z)', router_content, re.DOTALL)
assert fuzzy_match and '< 0.4' in fuzzy_match.group(), 'BUG-016: length ratio guard not found'
print('BUG-016 FIXED: fuzzy match has length ratio guard')

# Check wildcard substitution extracts only wildcard portion
wildcard_method = re.search(r'def _substitute_wildcards.*?(?=\n    def |\n\nclass |\Z)', router_content, re.DOTALL)
assert wildcard_method and 'replace(prefix' in wildcard_method.group(), 'BUG-017: wildcard prefix stripping not found'
print('BUG-017 FIXED: wildcard extracts only portion')

print('ALL ROUTER FIXES PASSED')
"</automated>
  </verify>
  <done>Router uses enum comparison in main.py, fuzzy match has length ratio guard, wildcard extracts only the wildcard portion, UNKNOWN routes increment llm_agent_calls</done>
</task>

<task type="auto">
  <name>Task 3: Fix backend state sharing — app.state pattern</name>
  <files>backend/main.py, backend/api/routes/chat.py, backend/api/routes/memory.py, backend/api/dependencies.py</files>
  <action>
    B-1.4 — Backend State Sharing (BUG-025):

    Step A — backend/api/dependencies.py:
    Add three new dependency functions AFTER the existing verify_api_key function:
    ```python
    async def get_agent(request: Request) -> "ReActAgent":
        """Get the shared agent from app.state."""
        from brain.agent import ReActAgent
        agent = getattr(request.app.state, 'agent', None)
        if agent is None:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        return agent

    async def get_memory(request: Request):
        """Get the shared memory manager from app.state."""
        memory = getattr(request.app.state, 'memory', None)
        if memory is None:
            raise HTTPException(status_code=503, detail="Memory not initialized")
        return memory

    async def get_router(request: Request):
        """Get the shared router from app.state."""
        from brain.router import CommandRouter
        router = getattr(request.app.state, 'router', None)
        if router is None:
            raise HTTPException(status_code=503, detail="Router not initialized")
        return router
    ```
    Add `from typing import TYPE_CHECKING` and use TYPE_CHECKING import for ReActAgent to avoid circular imports.

    Step B — backend/main.py:
    Update the lifespan function to create and attach shared instances:
    ```python
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Lifespan context for startup and shutdown events."""
        from brain.agent import ReActAgent
        from brain.router import CommandRouter
        from memory import MemoryManager
        from core.config import Config
        from brain.tools import create_tools_registry
        
        # Startup: create shared instances
        logger.info("Creating shared agent...")
        try:
            app.state.agent = ReActAgent(tool_registry=create_tools_registry())
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            app.state.agent = ReActAgent()  # Fallback without tools
        
        logger.info("Creating shared memory manager...")
        try:
            config = Config()
            app.state.memory = MemoryManager(config)
        except Exception as e:
            logger.error(f"Failed to create memory manager: {e}")
            app.state.memory = None
        
        logger.info("Creating shared router...")
        tool_registry = getattr(app.state.agent, 'tools', None)
        app.state.router = CommandRouter(tool_registry=tool_registry) if tool_registry else None
        
        logger.info("JARVIS backend server started with shared state")
        yield
        
        # Shutdown
        logger.info("Shutting down JARVIS backend server...")
    ```

    Step C — backend/api/routes/chat.py:
    1. Delete line 25: `agent = ReActAgent(tool_registry=create_tools_registry())`
    2. Delete lines 24 (comment) and 26 (empty line)
    3. Import dependencies: add `from backend.api.dependencies import get_agent`
    4. In websocket_chat, add `agent: ReActAgent = Depends(get_agent)` parameter
    5. In reset_chat, add `agent: ReActAgent = Depends(get_agent)` parameter
    6. Remove `from brain.agent import ReActAgent` (only needed for type annotation)
    7. Remove `from brain.tools import create_tools_registry`

    Step D — backend/api/routes/memory.py:
    1. Delete the global `_memory_manager` variable and `get_memory_manager()` function (lines 29-39)
    2. Add `from backend.api.dependencies import get_memory`
    3. Add `Depends(get_memory)` parameter to ALL route functions: list_memories, get_memory, create_memory, delete_memory, get_memory_file, update_memory_file, save_fact, get_memory_stats, add_memory, search_memory, get_recent_memory, delete_memory_entry, clear_memory, get_filtered_stats
    4. Replace `get_memory_manager()` calls in route handlers with the injected `manager` parameter
    5. For filtered memory: replace `get_filtered_memory()` singleton with `Depends(get_memory)` and access filtered via `manager.filtered_store` or similar

    Note: The filtered memory routes (add_memory, search_memory, etc.) currently use their own `_filtered_memory` singleton with `chroma_client=None`. Replace with: get `manager` from dependency, then use `manager.vector_store` or `manager.filtered_store` as the ChromaDB client.
  </action>
  <verify>
    <automated>python -c "
with open('backend/api/dependencies.py', 'r') as f:
    dep = f.read()
assert 'async def get_agent' in dep, 'BUG-025: get_agent not found'
assert 'async def get_memory' in dep, 'BUG-025: get_memory not found'
assert 'async def get_router' in dep, 'BUG-025: get_router not found'
print('BUG-025 FIXED: dependency injectors added')

with open('backend/main.py', 'r') as f:
    main = f.read()
assert 'app.state.agent' in main, 'BUG-025: app.state.agent not set'
assert 'app.state.memory' in main, 'BUG-025: app.state.memory not set'
assert 'app.state.router' in main, 'BUG-025: app.state.router not set'
print('BUG-025 FIXED: shared state attached in lifespan')

with open('backend/api/routes/chat.py', 'r') as f:
    chat = f.read()
assert 'Depends(get_agent)' in chat, 'BUG-025: get_agent dependency not used in chat'
assert 'agent = ReActAgent' not in chat, 'BUG-025: singleton agent still in chat.py'
print('BUG-025 FIXED: chat.py uses dependency injection')

with open('backend/api/routes/memory.py', 'r') as f:
    mem = f.read()
assert 'get_memory_manager' not in mem or 'Depends(get_memory)' in mem, 'BUG-025: singleton memory still in memory.py'
print('BUG-025 FIXED: memory.py uses dependency injection')

print('ALL BACKEND STATE FIXES PASSED')
"</automated>
  </verify>
  <done>Backend shares one agent/memory/router via app.state. No route-level singletons. All routes use dependency injection.</done>
</task>

<task type="auto">
  <name>Task 4: Fix dependencies — requirements.txt</name>
  <files>requirements.txt</files>
  <action>
    B-1.6 — Dependencies Fix (BUG-038):

    1. REMOVE the conflicting kokoro line. Keep `kokoro-onnx>=0.4.0`, remove `kokoro>=0.9.0`.

    2. ADD the missing packages:
       - `duckduckgo-search>=6.0.0`
       - `requests>=2.31.0`
       - `msal>=1.24.0` (for Google/Microsoft auth)

    3. Verify `librosa>=0.10.0` is NOT already present — add it only if missing.

    The resulting requirements.txt should have:
    ```
    kokoro-onnx>=0.4.0    # keep this
    # kokoro>=0.9.0       # REMOVE this (conflict)
    duckduckgo-search>=6.0.0
    requests>=2.31.0
    msal>=1.24.0
    librosa>=0.10.0
    ```
  </action>
  <verify>
    <automated>python -c "
with open('requirements.txt', 'r') as f:
    content = f.read()

# Should NOT have both kokoro lines
has_kokoro_old = 'kokoro>=0.9.0' in content and 'kokoro-onnx' in content
assert not has_kokoro_old, 'BUG-038: Both kokoro packages still present (conflict)'
print('BUG-038 FIXED: kokoro conflict resolved')

# Should have duckduckgo-search
assert 'duckduckgo-search' in content, 'BUG-038: duckduckgo-search missing'
print('BUG-038: duckduckgo-search added')

# Should have requests
assert 'requests>=2.31.0' in content or 'requests>=' in content, 'BUG-038: requests missing'
print('BUG-038: requests added')

# Should have msal
assert 'msal' in content, 'BUG-038: msal missing'
print('BUG-038: msal added')

# Should have librosa
assert 'librosa' in content, 'BUG-038: librosa missing'
print('BUG-038: librosa added')

print('ALL DEPENDENCY FIXES PASSED')
"</automated>
  </verify>
  <done>requirements.txt has no kokoro conflict, includes duckduckgo-search, requests, msal, librosa</done>
</task>

</tasks>

<verification>
- main.py imports setup_logging from core.logger, no local duplicate
- core/config.py load_config is a single Config() call
- Router uses RouteType enum comparison in main.py
- Fuzzy match has length ratio < 0.4 guard
- Wildcard substitution extracts only the wildcard portion
- Backend lifespan creates and attaches agent/memory/router to app.state
- chat.py and memory.py use Depends(get_agent) and Depends(get_memory)
- requirements.txt has no kokoro conflict
</verification>

<success_criteria>
- main.py starts without duplicate setup_logging definition error
- Router enum comparison works (no string .value comparisons)
- Backend starts with one shared agent/memory/router across all routes
- Requirements install without package conflicts
</success_criteria>

<output>
After completion, create `.planning/phases/B-1-core-chat-fix/B-1-03-SUMMARY.md`
</output>
