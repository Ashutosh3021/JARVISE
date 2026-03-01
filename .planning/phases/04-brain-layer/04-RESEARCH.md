# Phase 4: Brain Layer - Research

## Overview

Phase 4 implements the "brain" of JARVIS - a local LLM integration using Ollama with a ReAct (Reasoning + Acting) agent loop. This phase connects voice input (Phase 3) to tool execution and TTS output.

## Key Technologies

### Ollama Python Library

```python
from ollama import chat, list as list_models

# Non-streaming chat
response = chat(model='qwen2.5:7b', messages=[
    {'role': 'system', 'content': 'You are JARVIS...'},
    {'role': 'user', 'content': 'What time is it?'}
])
print(response['message']['content'])

# Streaming chat (for real-time TTS)
stream = chat(model='qwen2.5:7b', messages=messages, stream=True)
for chunk in stream:
    print(chunk['message']['content'], end='', flush=True)

# List available models
models = list_models()
for m in models.models:
    print(f"{m.name}: {m.size} bytes")
```

**API Details:**
- Base URL: `http://localhost:11434`
- Python package: `pip install ollama`
- Supports message roles: system, user, assistant
- Streaming via `stream=True` parameter

### ReAct Agent Pattern

The ReAct loop alternates between reasoning and tool use:

```
Input → Thought → Action → Observation → ... → Final Answer
```

**Implementation structure:**

```python
import re

class ReActAgent:
    def __init__(self, llm_client, tools):
        self.llm = llm_client
        self.tools = tools
        self.max_iterations = 10
    
    def run(self, user_input):
        messages = [self._build_system_prompt(), 
                    {'role': 'user', 'content': user_input}]
        
        for _ in range(self.max_iterations):
            response = self.llm.chat(messages)
            content = response['message']['content']
            
            # Parse thought/action from response
            thought, action = self._parse_response(content)
            
            if action is None:  # Final answer
                return content
            
            # Execute tool
            observation = self._execute_tool(action)
            
            # Add to context
            messages.append({'role': 'assistant', 'content': content})
            messages.append({'role': 'user', 'content': f"Observation: {observation}"})
        
        return "Max iterations reached"
    
    def _parse_response(self, response):
        # Extract Thought and Action using regex
        # Format: "Thought: ...\nAction: tool_name: args"
        pass
```

## Implementation Plan

### BL-01: Local LLM Client (Ollama)

**What to implement:**
- `brain/client.py` - Ollama wrapper class
- Methods: `chat()`, `stream_chat()`, `list_models()`, `health_check()`
- Handle connection errors, model loading

**Key considerations:**
- Default model: `qwen2.5:7b`
- Support model switching based on complexity
- Handle Ollama server not running

### BL-02: Server Health Check

**Implementation:**
```python
import requests

def health_check(host="http://localhost:11434") -> bool:
    try:
        response = requests.get(f"{host}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False
```

**When to check:**
- At startup (Phase 8)
- Before each chat request
- Retry 3 times with exponential backoff

### BL-03: Prompt Builder

**Components:**
- System prompt (JARVIS personality, capabilities)
- MEMORY.md content (cross-session facts)
- Conversation history (last 10 exchanges)
- Vector context (from Phase 5)

**Structure:**
```
System: [JARVIS instructions]
Memory: [MEMORY.md content]
Context: [Relevant vector memories]
History: [Last 10 exchanges]
User: [Current input]
```

### BL-04: ReAct Agent Loop

**Components:**
1. **Thought parsing** - Extract reasoning from LLM response
2. **Action detection** - Identify tool name and arguments
3. **Tool execution** - Run the identified tool
4. **Observation feedback** - Return result to LLM
5. **Termination detection** - Recognize final answer

**Action format:**
```
Thought: I need to check the time.
Action: get_time
Observation: 3:45 PM
```

**Iteration limit:** 10 max to prevent infinite loops

### BL-05: Tool Action Parsing

**Regex pattern:**
```python
import re

action_pattern = re.compile(
    r'^Action:\s*(\w+)(?::\s*(.+))?$', 
    re.MULTILINE
)
```

**Tool registry:**
```python
class ToolRegistry:
    def __init__(self):
        self.tools = {}
    
    def register(self, name, func, description):
        self.tools[name] = {'func': func, 'desc': description}
    
    def execute(self, name, args):
        if name not in self.tools:
            return f"Error: Unknown tool '{name}'"
        return self.tools[name]['func'](args)
```

**Tool definitions in prompt:**
```
Available tools:
- search: Search the web for information
- get_time: Get current time
- run_command: Execute a system command
```

### BL-06: Error Handling

**Malformed output handling:**
- Retry up to 3 times with different prompts
- If still failing, return error message to user
- Log failures for debugging

**Connection failures:**
- Retry 3 times with exponential backoff (1s, 2s, 4s)
- Fall back to error TTS: "Sorry, I'm having trouble connecting to the language model"

**Tool execution failures:**
- Return error to LLM as observation
- LLM decides whether to retry or use alternative

## Model Switching Strategy

**Complexity classification:**
```python
def classify_complexity(user_input, client) -> str:
    prompt = """Classify this task as SIMPLE, GENERAL, or COMPLEX.
Task: {input}
Respond with only one word.""".format(input=user_input)
    
    result = client.chat(model='qwen2.5:7b', messages=[
        {'role': 'user', 'content': prompt}
    ])
    
    complexity = result['message']['content'].strip().upper()
    
    # Map to model
    model_map = {
        'SIMPLE': 'phi4',      # or tiny
        'GENERAL': 'qwen2.5:7b',
        'COMPLEX': 'qwen2.5:14b'  # or llama3.2
    }
    return model_map.get(complexity, 'qwen2.5:7b')
```

**Decision factors:**
- SIMPLE: Factual questions, basic commands
- GENERAL: Conversation, summaries
- COMPLEX: Code, multi-step reasoning, analysis

## File Structure

```
brain/
├── __init__.py
├── client.py         # Ollama wrapper (BL-01, BL-02)
├── prompt_builder.py # Context assembly (BL-03)
├── agent.py          # ReAct loop (BL-04)
├── tools.py          # Tool registry (BL-05)
└── errors.py         # Error handling (BL-06)
```

## Integration Points

**Input:**
- Voice pipeline (Phase 3): receives transcribed text
- Memory system (Phase 5): reads MEMORY.md, vector context

**Output:**
- Voice pipeline (Phase 3): streams TTS for playback

## Dependencies

- `ollama` - Python library for Ollama
- `requests` - For REST API fallback
- `loguru` - For logging (already in project)
- `pydantic` - For data validation

## Testing Approach

1. **Unit tests** for each component (client, prompt_builder, tools)
2. **Integration test** with real Ollama instance
3. **Mock tests** for tool execution

## Open Questions

1. **Prompt complexity**: How much system prompt is needed for reliable ReAct behavior?
2. **Model switching latency**: Does classification add noticeable delay?
3. **Tool timeout**: Is 30s sufficient for all tools?
4. **VAD during TTS**: How to handle user interruption while JARVIS is speaking?

---

*Research completed: 2026-03-01*
