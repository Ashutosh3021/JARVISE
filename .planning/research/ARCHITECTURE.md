# Architecture Research

**Domain:** Windows AI Voice Assistant
**Researched:** 2026-02-28
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     VOICE INPUT LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │ Wake Word   │→ │ Voice       │→ │ Speech-to-Text      │   │
│  │ Detector    │  │ Activity    │  │ (faster-whisper)    │   │
│  │ (pvporcupine)│  │ Detection   │  │                     │   │
│  └─────────────┘  └─────────────┘  └──────────┬──────────┘   │
└────────────────────────────────────────────────┼───────────────┘
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BRAIN LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐  │
│  │ Prompt Builder  │→ │ ReAct Agent     │→ │ LLM Client    │  │
│  │                 │  │ (Reason→Act)   │  │ (Ollama)      │  │
│  └────────┬────────┘  └────────┬────────┘  └───────┬───────┘  │
│           │                    │                    │          │
│           ▼                    ▼                    ▼          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Memory System                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐  │   │
│  │  │ ChromaDB    │  │ MEMORY.md   │  │ MemoryManager │  │   │
│  │  │ (vectors)   │  │ (facts)     │  │               │  │   │
│  │  └─────────────┘  └─────────────┘  └───────────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┬───────────────┘
                                                  │
                                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     VOICE OUTPUT LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────┐  ┌─────────────────┐    │
│  │ Response        │→ │ Text-to-    │→ │ Audio Output    │    │
│  │ Processor      │  │ Speech      │  │ (speakers)      │    │
│  │                 │  │ (Kokoro)    │  │                 │    │
│  └─────────────────┘  └─────────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     TOOL LAYER (Optional)                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │Search   │  │Browser   │  │File      │  │Calendar/     │  │
│  │         │  │(Playwright)│ │System    │  │Email         │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Wake Word Detector | Listen for "JARVIS", trigger activation | pvporcupine library |
| Voice Activity Detection | Detect speech vs silence | Energy-based or AI-based |
| Speech-to-Text | Convert audio to text | faster-whisper model |
| Prompt Builder | Construct LLM prompts with context | Custom Python class |
| ReAct Agent | Reasoning loop with tool calling | langchain or custom |
| LLM Client | Interface to local Ollama | ollama Python SDK |
| Memory Manager | Handle long-term storage | ChromaDB + file I/O |
| Text-to-Speech | Convert text to audio | Kokoro model |
| Audio Output | Play audio to speakers | pyaudio/sounddevice |
| Tool Handlers | Execute system actions | Playwright, os, APIs |

## Recommended Project Structure

```
jarvis/
├── src/
│   ├── voice/
│   │   ├── __init__.py
│   │   ├── wake_word.py      # pvporcupine integration
│   │   ├── vad.py            # voice activity detection
│   │   ├── stt.py            # faster-whisper integration
│   │   └── tts.py            # kokoro integration
│   ├── brain/
│   │   ├── __init__.py
│   │   ├── llm_client.py     # ollama wrapper
│   │   ├── prompt_builder.py # context management
│   │   └── react_agent.py    # reasoning loop
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── chroma_store.py   # vector storage
│   │   ├── memory_file.py    # MEMORY.md handling
│   │   └── manager.py        # unified interface
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── search.py         # web search
│   │   ├── browser.py       # playwright automation
│   │   ├── filesystem.py    # file operations
│   │   └── calendar.py      # system calendar
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── api.py           # FastAPI endpoints
│   │   └── web/             # React frontend
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py      # configuration
│   │   └── hardware.py      # VRAM detection
│   ├── utils/
│   │   ├── __init__.py
│   │   └── logger.py        # logging setup
│   └── main.py              # entry point
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

### Structure Rationale

- **voice/:** All audio processing in one place, swapable implementations
- **brain/:** LLM and reasoning logic, separate from I/O
- **memory/:** Storage abstraction, can swap ChromaDB if needed
- **tools/:** Isolated tool implementations, easy to add more
- **ui/:** Web interface separated from core logic
- **config/:** Centralized configuration, hardware detection
- **main.py:** Minimal entry point, orchestrates components

## Architectural Patterns

### Pattern 1: Pipeline Architecture

**What:** Sequential data flow through layers
**When to use:** Voice input → processing → output
**Trade-offs:** Simple, debuggable, but rigid

**Example:**
```python
async def process_voice(audio_data):
    text = await stt.transcribe(audio_data)
    response = await brain.think(text)
    await tts.speak(response)
```

### Pattern 2: Event-Driven with State Machine

**What:** Components communicate via events, state tracks mode
**When to use:** Handling different states (idle, listening, thinking, speaking)
**Trade-offs:** Flexible, handles edge cases, more complex

**Example:**
```python
class JarvisState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"

async def handle_event(event):
    state = state_machine.transition(current_state, event)
```

### Pattern 3: Agent Tool Calling (ReAct)

**What:** LLM reasons about tools to use
**When to use:** When LLM needs to perform actions
**Trade-offs:** Powerful, but requires good prompt engineering

**Example:**
```python
thought = await llm.think(prompt_with_tools)
if "use_tool" in thought:
    result = await tool.execute(thought.tool_name, thought.args)
    prompt += result  # Feed back for next iteration
```

## Data Flow

### Request Flow (Voice)

```
[Microphone]
    ↓
[Wake Word Detection] → (not detected) → [return to idle]
    ↓ (detected)
[Voice Activity Detection] → (silence) → [continue listening]
    ↓ (speech)
[Audio Buffer]
    ↓
[Speech-to-Text] → "user said this"
    ↓
[Memory System] → retrieve context
    ↓
[Prompt Builder] → construct full prompt
    ↓
[ReAct Agent] → reason about tools/actions
    ↓
[LLM Client (Ollama)] → generate response
    ↓
[Response Processor] → clean output
    ↓
[Memory System] → store interaction
    ↓
[Text-to-Speech] → audio data
    ↓
[Audio Output] → speakers
```

### State Management

```
[Main Loop]
    ↓ (event)
[State Machine] → validates transition
    ↓
[Current State Handler]
    ↓ (action)
[Component] → performs work
    ↓ (result)
[State Machine] → next state
    ↓
[Notify UI] (if web interface)
```

### Key Data Flows

1. **Voice Pipeline:** Continuous audio → wake word → VAD → buffer → STT
2. **Reasoning Pipeline:** Text → context retrieval → prompt → LLM → response
3. **Memory Pipeline:** Interaction → embed → store (vector) + fact → update (file)
4. **Tool Pipeline:** LLM decides → tool executes → result → LLM continues

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Single user | Monolith fine, all in one process |
| 2-5 users | Separate UI server, single brain instance |
| 5+ users | Queue-based, multiple brain workers |

### Scaling Priorities

1. **First bottleneck:** STT/TTS latency → use GPU acceleration
2. **Second bottleneck:** LLM inference → use quantized models or more VRAM
3. **Third bottleneck:** Concurrent requests → add message queue

## Anti-Patterns

### Anti-Pattern 1: Blocking I/O in Main Thread

**What people do:** Running STT/TTS synchronously
**Why it's wrong:** Freezes entire application, poor UX
**Do this instead:** Use async/await, run blocking operations in executor

### Anti-Pattern 2: No Error Recovery

**What people do:** Single failure crashes entire system
**Why it's wrong:** Unusable in production
**Do this instead:** Graceful degradation, fallback to text mode

### Anti-Pattern 3: Hardcoded Model Paths

**What people do:** Assumes specific GPU/model always available
**Why it's wrong:** Fails on different hardware
**Do this instead:** Hardware detection at startup, model selection based on VRAM

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|--------------------|-------|
| Ollama | Local HTTP API | localhost:11434, no auth needed |
| Local models | File system | ~/.ollama/models/ |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Voice ↔ Brain | Async queue | Decouples input rate from processing |
| Brain ↔ Memory | Direct calls | Fast, in-process |
| Brain ↔ Tools | Function calls | Synchronous for simplicity |
| Core ↔ UI | WebSocket | Real-time updates |

## Sources

- InsiderLLM local assistant guide
- SAM v2 architecture documentation
- Towards AI voice assistant architecture guide
- LiveKit voice agent patterns

---
*Architecture research for: JARVIS Windows AI Voice Assistant*
*Researched: 2026-02-28*
