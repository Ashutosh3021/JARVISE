---
phase: B-1-core-chat-fix
plan: '01'
type: execute
wave: 1
depends_on: []
files_modified:
  - brain/prompt_builder.py
  - brain/agent.py
autonomous: true
requirements:
  - BL-05
  - BL-06
must_haves:
  truths:
    - "Exactly ONE system message sent to Ollama"
    - "stream_run yields clean text without Thought:/Action: artifacts"
    - "History saves cleaned response, not raw LLM output"
  artifacts:
    - path: brain/prompt_builder.py
      provides: Single merged system message
      min_lines: 80
    - path: brain/agent.py
      provides: Cleaned response in stream_run
      min_lines: 180
  key_links:
    - from: brain/prompt_builder.py
      to: Ollama API
      via: build() returns list with exactly one system message
      pattern: role.*system.*content
    - from: brain/agent.py
      to: brain/prompt_builder.py
      via: add_message called with self._clean_response(full_response)
      pattern: _clean_response.*full_response
---

<objective>
Fix LLM response correctness: single system message, clean streaming output, clean history.
Purpose: Ollama/Llama3 returns empty with multiple system messages. Raw Thought:/Action: lines leak to users and pollute history.
Output: brain/prompt_builder.py (fixed), brain/agent.py (fixed)
</objective>

<context>
@brain/prompt_builder.py
@brain/agent.py

<interfaces>
<!-- Key code that must change. Extracted from current codebase. -->

From brain/prompt_builder.py (lines 94-132):
Current BUGGY behavior — build() appends 4 separate system messages:
```python
messages.append({"role": "system", "content": self.system_prompt})
if self._context_injector is not None:
    messages.append({"role": "system", "content": f"## Environment Context\n{context_summary}"})
if memory_context:
    messages.append({"role": "system", "content": f"## Memory Context\n{memory_context}"})
if vector_context:
    messages.append({"role": "system", "content": f"## Relevant Context\n{context_str}"})
```

MUST BECOME — single system message:
```python
system_parts = [self.system_prompt]
if self._context_injector:
    system_parts.append(f"## Environment Context\n{self._context_injector.get_context_summary()}")
if memory_context:
    system_parts.append(f"## Memory Context\n{memory_context}")
if vector_context:
    system_parts.append("## Relevant Context\n" + "\n".join(f"- {c}" for c in vector_context))
messages = [{"role": "system", "content": "\n\n".join(system_parts)}]
```

From brain/agent.py stream_run() (lines 160-193):
Current BUGGY behavior — yields raw content and saves raw to history:
```python
# Line 162: yields raw content
yield content, True

# Line 193: saves raw full_response to history
self.prompt_builder.add_message("assistant", full_response)
```

MUST BECOME:
```python
# Line 162: yield cleaned content
yield self._clean_response(content), True

# Line 193: save cleaned response to history
self.prompt_builder.add_message("assistant", self._clean_response(full_response))
```

Note: full_response IS correctly set to content on line 156 BEFORE the if action_name is None check. The bug is ONLY that the clean version isn't used.
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Merge system messages in prompt_builder</name>
  <files>brain/prompt_builder.py</files>
  <action>
    In the `build()` method, replace all 4 separate `messages.append({"role": "system", ...})` calls with a SINGLE system message.

    Implementation:
    1. Create a list `system_parts = [self.system_prompt]`
    2. If `self._context_injector` is not None, append `f"## Environment Context\n{self._context_injector.get_context_summary()}"`
    3. If `memory_context` is non-empty, append `f"## Memory Context\n{memory_context}"`
    4. If `vector_context` is non-empty, append `"## Relevant Context\n" + "\n".join(f"- {c}" for c in vector_context)`
    5. Join with `"\n\n".join(system_parts)` — filter out empty parts first with `filter(None, system_parts)`
    6. Append exactly ONE `{"role": "system", "content": joined}` to messages list

    Keep the history and user_input appending logic unchanged after the system message.
  </action>
  <verify>
    <automated>python -c "
from brain.prompt_builder import PromptBuilder
pb = PromptBuilder()
msgs = pb.build(user_input={'role': 'user', 'content': 'hello'})
system_msgs = [m for m in msgs if m['role'] == 'system']
print(f'System messages count: {len(system_msgs)}')
assert len(system_msgs) == 1, f'Expected 1 system message, got {len(system_msgs)}'
print('PASS: Exactly one system message')
"</automated>
  </verify>
  <done>prompt_builder.build() returns exactly one {"role": "system"} message in the messages list</done>
</task>

<task type="auto">
  <name>Task 2: Fix stream_run to yield and save cleaned response</name>
  <files>brain/agent.py</files>
  <action>
    In `stream_run()`, make two specific changes:

    1. Line ~162 (in the `if action_name is None:` block): Change `yield content, True` to `yield self._clean_response(content), True`

    2. Line ~193 (after the loop, when saving to history): Change `self.prompt_builder.add_message("assistant", full_response)` to `self.prompt_builder.add_message("assistant", self._clean_response(full_response))`

    The `_clean_response()` method already exists at the bottom of the class. Do NOT modify it.
    The `run()` method is NOT part of this fix — only `stream_run()` needs changes.
  </action>
  <verify>
    <automated>python -c "
import re
with open('brain/agent.py', 'r') as f:
    content = f.read()
# Check that stream_run yields self._clean_response(content)
match = re.search(r'if action_name is None:.*?yield self\._clean_response\(content\)', content, re.DOTALL)
print('stream_run yield fix:', 'FOUND' if match else 'MISSING')
# Check that history saves self._clean_response(full_response)
hist_match = re.search(r'add_message\([\"'\'']assistant[\"'\''],\s*self\._clean_response\(full_response\)\)', content)
print('history save fix:', 'FOUND' if hist_match else 'MISSING')
assert match, 'stream_run yield fix not applied'
assert hist_match, 'history save fix not applied'
print('PASS: Both stream_run fixes applied')
"</automated>
  </verify>
  <done>stream_run yields cleaned response to user, and saves cleaned response to prompt history</done>
</task>

</tasks>

<verification>
- prompt_builder.build() returns list with exactly one system message
- agent.stream_run() yields self._clean_response(content) not raw content
- agent.stream_run() saves self._clean_response(full_response) to history
</verification>

<success_criteria>
- Exactly ONE {"role": "system"} in messages list from prompt_builder.build()
- No raw Thought:/Action: lines visible to users in stream_run output
- prompt history contains clean responses, not raw LLM output
</success_criteria>

<output>
After completion, create `.planning/phases/B-1-core-chat-fix/B-1-01-SUMMARY.md`
</output>
