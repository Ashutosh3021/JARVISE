# Gap Closure Plans

## BUG-029: UI Client Hardcodes localhost:8000

### Gap Description
The React UI hardcodes the WebSocket URL as `ws://localhost:8000/ws/chat` in `ui/src/App.tsx:36`, making it impossible to connect to a different backend server.

### Current State
```typescript
// ui/src/App.tsx:36
} = useChatWebSocket('ws://localhost:8000/ws/chat')
```

### Required Fix
Replace hardcoded URL with environment variable or configuration:
- Use `import.meta.env.VITE_WS_URL` or similar to read from environment
- Fallback to default `ws://localhost:8000/ws/chat` if not set

### Proposed Solution
```typescript
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/chat'
} = useChatWebSocket(WS_URL)
```

---

## BUG-035: asyncio.get_event_loop() Deprecated

### Gap Description
`asyncio.get_event_loop()` is deprecated in Python 3.10+ and completely removed in Python 3.12+. The codebase uses this deprecated API in 4 files, which will break when running on Python 3.12+.

### Files Affected

1. **backend/api/routes/chat.py:153**
   ```python
   loop = asyncio.get_event_loop()
   stream_task = loop.run_in_executor(None, run_generator)
   ```

2. **tools/web_search.py:140**
   ```python
   loop = asyncio.get_event_loop()
   return await loop.run_in_executor(None, sync_search)
   ```

3. **tools/code_exec.py:336**
   ```python
   loop = asyncio.get_event_loop()
   return await loop.run_in_executor(None, lambda: self.execute(...))
   ```

4. **tools/system_monitor.py:467**
   ```python
   loop = asyncio.get_event_loop()
   return loop.run_in_executor(None, func, *args)
   ```

### Required Fix
Replace `asyncio.get_event_loop()` with modern async patterns:
- Use `asyncio.get_running_loop()` in async context
- Use `asyncio.run()` for top-level coroutines
- Use `asyncio.to_thread()` for simple thread execution (Python 3.9+)
- Use `loop.run_in_executor(None, ...)` only when you have access to an existing loop

### Proposed Solutions

**For async functions (web_search.py, code_exec.py):**
Replace with:
```python
# Instead of asyncio.get_event_loop()
return await asyncio.to_thread(sync_search)
```

**For chat.py:**
```python
# In async function context, use:
loop = asyncio.get_running_loop()
stream_task = loop.run_in_executor(None, run_generator)
```

**For system_monitor.py:**
```python
# Replace the nested function with:
async def run_in_executor(func, *args):
    return await asyncio.to_thread(func, *args)
```

---

## Summary

| Bug ID | File(s) | Issue | Priority |
|--------|---------|-------|----------|
| BUG-029 | ui/src/App.tsx | Hardcoded localhost:8000 | Medium |
| BUG-035 | 4 files | Deprecated asyncio.get_event_loop() | High |
