---
phase: "04-brain-layer"
plan: "01"
type: "execute"
wave: 1
depends_on: []
files_modified:
  - brain/__init__.py
  - brain/client.py
  - brain/prompt_builder.py
  - brain/agent.py
  - brain/tools.py
  - brain/errors.py
autonomous: true
requirements:
  - BL-01
  - BL-02
  - BL-03
  - BL-04
  - BL-05
  - BL-06
must_haves:
  truths:
    - Ollama server connection is verified and working at startup
    - User text input is processed through ReAct loop (Reason → Act → Observe → Repeat)
    - Tool actions are parsed from LLM output and executed correctly
    - Streaming response is returned to user in real-time
  artifacts:
    - brain/client.py - Ollama LLM client with streaming support
    - brain/prompt_builder.py - Prompt assembly with memory context
    - brain/agent.py - ReAct agent loop implementation
    - brain/tools.py - Tool registry and action parser
    - brain/errors.py - Error handling utilities
    - brain/__init__.py - Module exports
    - brain/__main__.py - CLI testing entry point
  key_links:
    - "client.py → agent.py: OllamaClient provides chat() and stream_chat() to ReActAgent"
    - "prompt_builder.py → agent.py: PromptBuilder assembles prompts with context for ReActAgent"
    - "tools.py ↔ agent.py: ToolRegistry is used by ReActAgent to execute parsed tool actions"
    - "errors.py → client.py: Error handling with retry logic applied to OllamaClient connections"
---

<?xml version="1.0" encoding="UTF-8"?>
<tasks>
  <task>
    <id>BL-01-01</id>
    <description>Create brain/client.py - Ollama LLM client with streaming support</description>
    <priority>critical</priority>
    <requirements>BL-01,BL-02</requirements>
    <verification>
      <criteria>Ollama client can connect to server, send messages, and stream responses</criteria>
      <test_commands>python -c "from brain.client import OllamaClient; c = OllamaClient(); print(c.health_check())"</test_commands>
    </verification>
    <must_haves>
      <item>OllamaClient class with chat() and stream_chat() methods</item>
      <item>health_check() method that verifies Ollama server is running</item>
      <item>list_models() method to enumerate available models</item>
      <item>Error handling for connection failures</item>
    </must_haves>
  </task>

  <task>
    <id>BL-01-02</id>
    <description>Create brain/prompt_builder.py - Prompt assembly with memory context</description>
    <priority>critical</priority>
    <requirements>BL-03</requirements>
    <verification>
      <criteria>Prompt builder can assemble system prompt with history and context</criteria>
      <test_commands>python -c "from brain.prompt_builder import PromptBuilder; pb = PromptBuilder(); print(pb.build({'role':'user','content':'hello'})[:100])"</test_commands>
    </verification>
    <must_haves>
      <item>PromptBuilder class with build() method</item>
      <item>System prompt with JARVIS personality and capabilities</item>
      <item>add_memory_context() stub for Phase 5 integration</item>
      <item>add_conversation_history() for last 10 exchanges</item>
    </must_haves>
  </task>

  <task>
    <id>BL-01-03</id>
    <description>Create brain/tools.py - Tool registry and action parser</description>
    <priority>critical</priority>
    <requirements>BL-05</requirements>
    <verification>
      <criteria>Tool registry can register tools and execute by name</criteria>
      <test_commands>python -c "from brain.tools import ToolRegistry; r = ToolRegistry(); r.register('test', lambda x: 'ok', 'test'); print(r.execute('test', {}))"</test_commands>
    </verification>
    <must_haves>
      <item>ToolRegistry class with register() and execute() methods</item>
      <item>parse_action() method to extract tool name and args from LLM output</item>
      <item>Regex pattern matching for Action: tool_name: args format</item>
    </must_haves>
  </task>

  <task>
    <id>BL-01-04</id>
    <description>Create brain/agent.py - ReAct agent loop implementation</description>
    <priority>critical</priority>
    <requirements>BL-04</requirements>
    <verification>
      <criteria>ReAct agent can process user input through reasoning loop</criteria>
      <test_commands>python -c "from brain.agent import ReActAgent; print('ReActAgent imported successfully')"</test_commands>
    </verification>
    <must_haves>
      <item>ReActAgent class with run() method</item>
      <item>Thought → Action → Observe → Repeat loop</item>
      <item>Max 10 iterations to prevent infinite loops</item>
      <item>Termination detection for final answer</item>
    </must_haves>
  </task>

  <task>
    <id>BL-01-05</id>
    <description>Create brain/errors.py - Error handling utilities</description>
    <priority>high</priority>
    <requirements>BL-06</requirements>
    <verification>
      <criteria>Error handling module provides retry logic and malformed output handling</criteria>
      <test_commands>python -c "from brain.errors import MalformedOutputError, retry_on_error; print('Error handling imported')"</test_commands>
    </verification>
    <must_haves>
      <item>MalformedOutputError exception class</item>
      <item>retry_on_error decorator for retry logic (3 attempts)</item>
      <item>ConnectionError handling with exponential backoff</item>
    </must_haves>
  </task>

  <task>
    <id>BL-01-06</id>
    <description>Update brain/__init__.py with exports</description>
    <priority>medium</priority>
    <requirements>BL-01,BL-04,BL-05</requirements>
    <verification>
      <criteria>Brain module exports all public classes</criteria>
      <test_commands>python -c "from brain import OllamaClient, ReActAgent, ToolRegistry, PromptBuilder; print('All exports working')"</test_commands>
    </verification>
    <must_haves>
      <item>Export OllamaClient, ReActAgent, ToolRegistry, PromptBuilder</item>
      <item>Module docstring describing brain layer</item>
    </must_haves>
  </task>

  <task>
    <id>BL-01-07</id>
    <description>Create brain/__main__.py for CLI testing</description>
    <priority>low</priority>
    <requirements>BL-01</requirements>
    <verification>
      <criteria>Can run brain module directly for testing</criteria>
      <test_commands>python -m brain --help</test_commands>
    </verification>
    <must_haves>
      <item>CLI entry point with --text input option</item>
      <item>Health check command</item>
    </must_haves>
  </task>
</tasks>
