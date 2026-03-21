---
phase: B-1-core-chat-fix
plan: '02'
type: execute
wave: 1
depends_on: []
files_modified:
  - brain/tools.py
autonomous: true
requirements:
  - BL-05
  - ST-09
must_haves:
  truths:
    - "Both basic tools AND heavy tools exist in same registry"
    - "Heavy tools lazy-initialized — not instantiated at import time"
    - "Web search works via duckduckgo-search package"
    - "Multi-line JSON args parse correctly"
    - "invalidate_cache doesn't crash when cache is None"
  artifacts:
    - path: brain/tools.py
      provides: Merged tool registry with lazy init
      min_lines: 400
  key_links:
    - from: create_tools_registry()
      to: BrowserTool, GoogleCalendarTool, etc.
      via: module-level None globals + lazy init wrappers
      pattern: global _browser.*if _browser is None
    - from: ToolRegistry.execute_search
      to: web_search.execute
      via: num_results parameter (not max_results)
      pattern: num_results=max_results
---

<objective>
Fix tool registry: merge both registries, lazy init heavy tools, fix 6 bugs.
Purpose: In-session memory tools missing from main.py's registry. Heavy tools crash startup. Arg mismatches silently fail. Regex breaks on multi-line JSON.
Output: brain/tools.py (comprehensively fixed)
</objective>

<context>
@brain/tools.py

<interfaces>
<!-- Key bugs to fix. Extracted from current codebase. -->

BUG-015 — Two separate registries:
create_default_registry() has: remember, recall, forget, pwd, get_time, get_date, read_file, write_file, list_dir, search_web, list_memories
create_tools_registry() has: browser, web_search, filesystem, execute_code, google_calendar, google_email, outlook, system_monitor, get_time, get_date
main.py calls create_tools_registry() → missing remember/recall/forget/list_memories/pwd

FIX: In create_tools_registry(), FIRST call create_default_registry() to get basics, THEN register heavy tools on top of it. Or manually add basics.

---

BUG-011 — Heavy tools instantiated at import time:
Lines 386-393: BrowserTool(), WebSearchTool(), etc. all instantiated immediately.
FIX: Use lazy init pattern. Module-level globals set to None, instantiate on first call:
```python
_browser = None
def execute_browser(args: dict) -> str:
    global _browser
    if _browser is None:
        _browser = BrowserTool()
    action = args.get("action", "navigate")
    url = args.get("url", "")
    return _browser.execute(action=action, url=url)
```

---

BUG-012 — Arg name mismatch in execute_search:
Line 413: web_search.execute(query=query, max_results=max_results)
WebSearchTool.execute() expects: num_results (not max_results)
FIX: web_search.execute(query=query, num_results=max_results)

---

BUG-013 — invalidate_cache crashes when _cache is None:
Line 176: return len(self._cache) after self._cache.clear_all() → None
FIX: Already has early return at line 172 (if self._cache is None: return 0). But line 176 runs after clear_all() which sets _cache to None. Change line 176 to: return 0

---

BUG-014 — Regex fails on multi-line JSON:
Line 25-28: _action_pattern has `$` anchor with re.MULTILINE. The `$` anchors to first newline in MULTILINE mode.
FIX: Remove `$` anchor, use non-greedy `[\s\S]+?`:
```python
self._action_pattern = re.compile(
    r"^Action:\s*(\w+)(?:\s*:\s*(\{[\s\S]+?\}|\[[\s\S]+?\]))?",
    re.MULTILINE | re.IGNORECASE
)
```

---

BUG-018 — search_web in default registry uses broken DDG HTML scraping:
Lines 280-296: regex on DDG HTML → always returns empty.
FIX: Use duckduckgo-search package:
```python
from duckduckgo_search import DDGS
def search_web(args: dict) -> str:
    query = args.get("query", "")
    if not query:
        return "Error: No search query provided"
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            if results:
                output = []
                for r in results[:5]:
                    output.append(f"- {r['title']}: {r['href']}")
                return "Search Results:\n" + "\n".join(output)
        return "No search results found."
    except Exception as e:
        return f"Search error: {str(e)}"
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Merge registries and add basic tools to create_tools_registry</name>
  <files>brain/tools.py</files>
  <action>
    In create_tools_registry(), ensure basic tools (remember, recall, forget, pwd, get_time, get_date, list_memories) are included. 
    
    Approach: After creating the base registry, manually register the basics from create_default_registry() — get_time, get_date, pwd, remember, recall, list_memories, forget. This avoids circular import issues.

    Do NOT instantiate heavy tools at module level. Use the lazy init pattern for all of: BrowserTool, WebSearchTool, FilesystemTool, CodeExecutionTool, GoogleCalendarTool, GoogleEmailTool, MicrosoftOutlookTool, SystemMonitorTool.
    
    Each lazy init follows the pattern:
    ```python
    _browser = None
    def execute_browser(args: dict) -> str:
        global _browser
        if _browser is None:
            _browser = BrowserTool()
        # ... use _browser
    ```
  </action>
  <verify>
    <automated>python -c "
from brain.tools import create_tools_registry
reg = create_tools_registry()
basic_tools = ['remember', 'recall', 'forget', 'pwd', 'get_time', 'get_date', 'list_memories']
heavy_tools = ['browser', 'web_search', 'filesystem', 'execute_code', 'google_calendar', 'google_email', 'outlook', 'system_monitor']
missing_basic = [t for t in basic_tools if not reg.has_tool(t)]
missing_heavy = [t for t in heavy_tools if not reg.has_tool(t)]
print(f'Missing basic tools: {missing_basic}')
print(f'Missing heavy tools: {missing_heavy}')
assert not missing_basic, f'Missing basic tools: {missing_basic}'
assert not missing_heavy, f'Missing heavy tools: {missing_heavy}'
print('PASS: All tools present in merged registry')
"</automated>
  </verify>
  <done>create_tools_registry() returns registry with both basic AND heavy tools</done>
</task>

<task type="auto">
  <name>Task 2: Fix 5 remaining tool bugs</name>
  <files>brain/tools.py</files>
  <action>
    Apply all 5 fixes to brain/tools.py:

    1. FIX execute_search arg name (BUG-012): Change `web_search.execute(query=query, max_results=max_results)` to `web_search.execute(query=query, num_results=max_results)` inside the execute_search wrapper function.

    2. FIX invalidate_cache crash (BUG-013): In invalidate_cache(), after `self._cache.clear_all()`, the next line `return len(self._cache)` crashes because _cache is now None. Change to `return 0`.

    3. FIX regex $ anchor (BUG-014): Change _action_pattern to:
    ```python
    self._action_pattern = re.compile(
        r"^Action:\s*(\w+)(?:\s*:\s*(\{[\s\S]+?\}|\[[\s\S]+?\]))?",
        re.MULTILINE | re.IGNORECASE
    )
    ```

    4. FIX search_web in default registry (BUG-018): Replace the Wikipedia+DDG HTML scraping in search_web() with duckduckgo-search:
    ```python
    from duckduckgo_search import DDGS
    def search_web(args: dict) -> str:
        query = args.get("query", "")
        if not query:
            return "Error: No search query provided"
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
                if results:
                    output = []
                    for r in results[:5]:
                        output.append(f"- {r['title']}: {r['href']}")
                    return "Search Results:\n" + "\n".join(output)
            return "No search results found."
        except Exception as e:
            return f"Search error: {str(e)}"
    ```

    5. VERIFY lazy init works: Do NOT call any heavy tool class __init__ at module load time. Only instantiate on first execute_* call.
  </action>
  <verify>
    <automated>python -c "
import re

with open('brain/tools.py', 'r') as f:
    content = f.read()

# Check 1: num_results parameter (not max_results)
assert 'num_results=max_results' in content, 'BUG-012: num_results not found'
print('BUG-012 FIXED: num_results parameter')

# Check 2: invalidate_cache returns 0 after clear_all
m = re.search(r'self._cache.clear_all\(\).*?return\s+(\w+)', content, re.DOTALL)
assert m and m.group(1) == '0', 'BUG-013: invalidate_cache still returns len()'
print('BUG-013 FIXED: invalidate_cache returns 0')

# Check 3: Regex has no $ anchor
assert r'\[\\\\s\\\\S\]' in content or r'[\s\S]' in content, 'BUG-014: multiline pattern not found'
assert '$' not in re.search(r'_action_pattern.*?\)', content, re.DOTALL).group() or r'\[\\\\s\\\\S\]' in content, 'BUG-014: $ anchor still present'
print('BUG-014 FIXED: multiline regex pattern')

# Check 4: duckduckgo-search import (not HTML scraping)
assert 'from duckduckgo_search import DDGS' in content or 'duckduckgo_search' in content, 'BUG-018: duckduckgo-search not found'
assert 're.findall' not in content.split('def search_web')[1].split('def ')[0], 'BUG-018: regex still in search_web'
print('BUG-018 FIXED: duckduckgo-search package used')

print('ALL 5 BUGS FIXED')
"</automated>
  </verify>
  <done>All 6 bugs (015, 011, 012, 013, 014, 018) fixed in brain/tools.py</done>
</task>

</tasks>

<verification>
- create_tools_registry() has both basic (remember/recall/forget/pwd/get_time/get_date/list_memories) AND heavy tools
- Heavy tools are module-level None globals, instantiated lazily in execute_* wrappers
- web_search.execute uses num_results= parameter
- invalidate_cache returns 0 after clear_all()
- _action_pattern uses [\\s\\S]+? and has no $ anchor
- search_web uses duckduckgo-search package, not HTML scraping
</verification>

<success_criteria>
- create_tools_registry() includes all basic and heavy tools in one registry
- No heavy tool class instantiated at module import time
- Multi-line JSON args parse correctly in _action_pattern
- Web search returns actual results
- Cache invalidation doesn't crash
</success_criteria>

<output>
After completion, create `.planning/phases/B-1-core-chat-fix/B-1-02-SUMMARY.md`
</output>
