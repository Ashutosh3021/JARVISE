# Phase 4: Brain Layer - Context

**Gathered:** 2026-03-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Local LLM integration with ReAct reasoning loop. Connects to Ollama for local inference, processes text input through ReAct agent, executes tools, and streams responses via TTS. This phase integrates with Voice (Phase 3) and Memory (Phase 5) systems.

</domain>

<decisions>
## Implementation Decisions

### Model Selection
- **Primary model**: qwen2.5 — excellent problem-solving, strong reasoning, large community support
- **Auto-switching**: Yes — LLM classifies task complexity and selects appropriate model
- **Model tiers**:
  - Simple tasks → smaller/faster model (phi4 or tiny)
  - General conversation → qwen2.5:7b (default)
  - Complex reasoning → larger model (qwen2.5:14b or llama3.2)

### Context Management
- **Conversation history**: Sliding window — keep last 10 exchanges in prompt
- **Cross-session memory**: Summary stored in MEMORY.md file
- **On startup**: Load MEMORY.md to provide context from previous sessions
- **Example**: If user mentioned "add birthday to calendar" in previous session, JARVIS recalls this from MEMORY.md

### Tool Execution
- **Timeout**: 30 seconds per tool execution
- **On timeout**: Kill process, return error to LLM, request alternative approach
- **Sandboxing**: Subprocess execution with limited scope (filesystem, browser, etc.)

### Response Streaming
- **Real-time TTS**: Tokens stream from LLM → immediately to TTS → speakers
- **No buffering**: User hears response as it's generated
- **Synchronization**: Audio queued if user interrupts

### Error Handling
- **Malformed output**: Retry up to 3 times with different prompting
- **Connection failure**: Retry Ollama connection 3 times, then fall back to error message
- **Graceful degradation**: If tool fails, return error to LLM for retry or alternative

### Claude's Discretion
- Exact prompt templates for task classification
- How to weight simplicity vs accuracy in classification
- Tool timeout values (30s is default, can adjust per tool)
- VAD handling during TTS playback

</decisions>

<specifics>
## Specific Ideas

- "LLM classifies task complexity" — Let the model decide which model to use
- "qwen2.5:7b as default" — Main model for general conversation
- "Remember previous sessions via MEMORY.md" — Persistent context across sessions
- "Real-time TTS streaming" — No buffering, immediate audio output

</specifics>

# Existing Code Insights

### Reusable Assets
- `voice/pipeline.py` — Already has VoicePipeline with speak() method for TTS output
- `core/config.py` — Has ollama_host and ollama_model settings
- `core/logger.py` — Can be used for brain layer logging

### Established Patterns
- Phase 2: Configuration via pydantic-settings, logging via loguru
- Phase 3: Voice pipeline with TTS integration ready

### Integration Points
- Input: Voice pipeline (Phase 3) provides transcribed text
- Output: Voice pipeline (Phase 3) receives TTS for playback
- Memory: Will integrate with Memory system (Phase 5) for persistent context

</code_context>

<deferred>
## Deferred Ideas

- Model-specific optimizations — fine-tune prompts per model (future enhancement)
- Custom tool creation — user-defined tools beyond built-in set (Phase 6+)
- Multi-modal input — images, documents as input (out of scope for v1)

</deferred>

---

*Phase: 04-brain-layer*
*Context gathered: 2026-03-01*
