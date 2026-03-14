# JARVIS Architecture

> System architecture documentation for J.A.R.V.I.S v1.0

---

## Overview

JARVIS is a **privacy-focused, local AI assistant** that runs entirely on your machine. It uses a modular architecture with distinct layers for input, processing, memory, and output.

### Design Principles

1. **Local-first** — No data leaves your machine
2. **Hardware-aware** — Auto-selects models based on available resources
3. **Modular** — Each component is independent and replaceable
4. **Fault-tolerant** — Graceful fallbacks when components fail

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                           USER                                       │
│  Voice (microphone)  │  Text (CLI/UI)  │  WebSocket (browser)  │
└─────────────────────┬──────────────────────┬────────────────────────────┘
                     │                    │
                     ▼                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      INPUT LAYER                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ voice/pipeline│  │   CLI input  │  │  backend/api/routes/  │  │
│  │  (PTT + VAD) │  │  (main.py)  │  │      chat.py         │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
└─────────┼──────────────────┼──────────────────────┼──────────────┘
          │                  │                      │
          ▼                  ▼                      ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   PROCESSING LAYER                                 │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    voice/stt.py                           │  │
│  │                 (faster-whisper)                          │  │
│  │                   audio → text                            │  │
│  └─────────────────────────┬───────────────────────────────────┘  │
│                            │                                       │
│                            ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    brain/agent.py                        │  │
│  │                    (ReAct Loop)                           │  │
│  │    Thought → Action → Observation → Repeat             │  │
│  └─────────────────────────┬───────────────────────────────────┘  │
│                            │                                       │
│              ┌─────────────┼─────────────┐                        │
│              ▼             ▼             ▼                        │
│  ┌─────────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │ brain/client.py│ │brain/tools │ │brain/prompt│            │
│  │  (Ollama)     │ │  Registry  │ │  Builder   │            │
│  └────────┬────────┘ └──────┬──────┘ └─────────────┘            │
│           │                │                                     │
└───────────┼────────────────┼─────────────────────────────────────┘
            │                │
            ▼                ▼
    ┌──────────────────────────────────────────────────────────────┐
    │                    TOOL EXECUTION LAYER                        │
    │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐     │
    │  │filesystem│ │ browser  │ │code_exec│ │ web_search  │     │
    │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘     │
    └──────────────────────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      MEMORY LAYER                                   │
│                                                                  │
│  ┌─────────────────────┐    ┌───────────────────────────────┐    │
│  │  memory/chroma.py │    │   memory/memory_file.py    │    │
│  │   (Vector Store)   │    │      (MEMORY.md)          │    │
│  └─────────────────────┘    └───────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     OUTPUT LAYER                                     │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  voice/tts  │  │   Text      │  │   backend/main.py     │  │
│  │  (Kokoro)   │  │  Response   │  │   (FastAPI + WS)     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### Core Layer (`core/`)

| Module | Purpose |
|--------|---------|
| `config.py` | Configuration loading, hardware-aware model selection |
| `hardware.py` | CPU/GPU detection, VRAM measurement |
| `logger.py` | Centralized logging (loguru) |

#### Hardware Detection Flow

```
detect_hardware()
    │
    ├─→ psutil.cpu_count() ──→ CPU cores
    │
    ├─→ pynvml ──────────────→ NVIDIA VRAM (if available)
    │
    └─→ gpu-list ────────────→ AMD/Intel VRAM (if available)

load_config(vram_mb)
    │
    └─→ select_profile() ──→ CPU / LOW_GPU / MID_GPU / HIGH_GPU
           │
           └─→ select_models() ──→ stt_model, ollama_model
```

### Voice Layer (`voice/`)

| Module | Purpose |
|--------|---------|
| `pipeline.py` | Unified voice pipeline orchestration |
| `stt.py` | Faster-Whisper transcription |
| `tts.py` | Kokoro TTS synthesis |
| `vad.py` | Voice Activity Detection |
| `recorder.py` | Audio capture |
| `audio_output.py` | Speaker playback |

#### Voice Pipeline Flow

```
1. User holds SPACE ──→ KeyboardHandler triggers
2. AudioRecorder starts ──→ Captures audio
3. VAD filters ──→ Removes silence/noise
4. User releases SPACE ──→ Silence timer starts
5. Silence timeout ──→ STT.transcribe()
6. Text returned ──→ Callback to brain agent
7. Agent processes ──→ Generate response
8. TTS synthesizes ──→ AudioOutput plays
```

### Brain Layer (`brain/`)

| Module | Purpose |
|--------|---------|
| `agent.py` | ReAct agent loop |
| `client.py` | Ollama API client |
| `prompt_builder.py` | Context injection |
| `tools.py` | Tool registry & execution |

#### ReAct Agent Loop

```
Input: "search for Python tutorials"
│
├─→ Thought: I should use the web search tool
├─→ Action: web_search
├─→ Action Input: "Python tutorials"
├─→ Observation: [search results]
│
├─→ Thought: I have results, I should summarize
├─→ Action: None (no tool needed)
└─→ Final Response: "Here are some Python tutorials..."
```

### Memory Layer (`memory/`)

| Module | Purpose |
|--------|---------|
| `chroma_store.py` | ChromaDB vector storage |
| `memory_file.py` | MEMORY.md controller |
| `MemoryManager.py` | Unified interface |

#### Memory Architecture

```
┌─────────────────────────────────────────────┐
│              Query Input                    │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│         MemoryManager.get_context()         │
├─────────────────────────────────────────────┤
│  1. Vector search (ChromaDB)               │
│     - Embed query                           │
│     - Search conversations                  │
│     - Top 3 results                         │
│                                             │
│  2. File memory (MEMORY.md)               │
│     - Load sections                        │
│     - Extract preferences                   │
│     - Get user profile                     │
│                                             │
│  3. Combine context                       │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│         Prompt with context                 │
└─────────────────────────────────────────────┘
```

### Tools Layer (`tools/`)

| Tool | Purpose |
|------|---------|
| `filesystem.py` | File read/write with safety |
| `browser.py` | Playwright automation |
| `code_exec.py` | Sandboxed Python execution |
| `web_search.py` | DuckDuckGo search |
| `google_calendar.py` | Google Calendar API |
| `google_email.py` | Gmail API |
| `system_monitor.py` | CPU/RAM/Disk stats |

#### Tool Safety

```
Filesystem Tool:
├── Blocked paths: C:\Windows, /etc, /usr
├── Confirmation for write/delete
└── Restricted to user home directory

Code Execution Tool:
├── Blocked imports: os, subprocess, socket, etc.
├── 30-second timeout
├── 128MB memory limit
└── Regex pattern detection
```

### Backend Layer (`backend/`)

| Module | Purpose |
|--------|---------|
| `main.py` | FastAPI application |
| `api/routes/chat.py` | Chat endpoint |
| `api/routes/memory.py` | Memory management |
| `api/routes/stats.py` | System stats |
| `api/websocket/manager.py` | WebSocket streaming |

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send message, get response |
| `/api/chat/stream` | WebSocket | Streaming response |
| `/api/memory` | GET | Retrieve memories |
| `/api/memory` | POST | Save memory |
| `/api/stats` | GET | System statistics |

---

## Data Flow Examples

### Voice Command

```
User: [hold space] "Open Chrome" [release]
    │
    ▼
voice/pipeline.py: Space press triggers recording
    │
    ▼
voice/recorder.py: Capture audio
    │
    ▼
voice/vad.py: Filter silence
    │
    ▼
voice/stt.py: Whisper transcription
    │
    ▼ "open chrome"
brain/agent.py: ReAct loop
    │
    ├─→ Thought: Need to open application
    ├─→ Action: filesystem.open_app
    ├─→ Action Input: "chrome"
    └─→ Observation: "C:\Program Files\..."
    │
    ▼
voice/tts.py: "Opening Chrome, sir."
    │
    ▼
AudioOutput: Play speakers
```

### Text Command (CLI)

```
User: python main.py --text-only
    │
    ▼
main.py: Text input loop
    │
    ▼ "search Python tutorials"
brain/agent.py: Process text
    │
    ├─→ web_search tool
    └─→ [results]
    │
    ▼
Console output
```

### Web UI

```
User: Opens http://localhost:8000
    │
    ▼
backend/main.py: FastAPI serves React app
    │
    ▼
User: Types "What is Python?"
    │
    ▼
POST /api/chat
    │
    ▼
brain/agent.py: Process
    │
    ▼
Response via WebSocket
    │
    ▼
React UI: Display streaming response
```

---

## Configuration

### Hardware Profiles

| Profile | VRAM | STT | LLM |
|---------|------|-----|-----|
| CPU | 0MB | tiny | qwen2.5-coder:7b |
| LOW_GPU | 2GB | base | qwen2.5-coder:7b |
| MID_GPU | 4GB | small | mistral:7b |
| HIGH_GPU | 8GB+ | medium | llama3.2:latest |

### Environment Variables

```bash
# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b

# Voice
WHISPER_MODEL=base
KOKORO_VOICE=bm_lewis
TTS_SPEED=1.0

# Memory  
CHROMA_PERSIST=./data/chromadb
MEMORY_FILE=./data/MEMORY.md

# UI
UI_HOST=0.0.0.0
UI_PORT=8000

# Logging
LOG_LEVEL=INFO
LOG_FILE=./data/jarvis.log
```

---

## Error Handling

| Component | Error | Handling |
|-----------|-------|----------|
| STT | Microphone not found | Fall back to text input |
| LLM | Ollama not running | Retry 3x, then error message |
| Tools | Execution fails | Retry with alternatives |
| Memory | ChromaDB error | Fall back to MEMORY.md only |
| TTS | Kokoro not installed | Skip voice, text-only |

---

## Future Enhancements

- Wake word detection (Porcupine)
- Multi-user support
- Plugin system
- Scheduled tasks
- Voice cloning
