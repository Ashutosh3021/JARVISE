<div align="center">

<img src="https://img.shields.io/badge/JARVIS-v1.0.0-blueviolet?style=for-the-badge&logo=robot&logoColor=white" alt="JARVIS v1.0.0"/>

# JARVIS
### *Just A Rather Very Intelligent System*

**A privacy-first AI assistant — voice, CLI, and 19 tools in one package.**

<br/>

[![Python Version](https://img.shields.io/badge/python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Ollama](https://img.shields.io/badge/Ollama-LLM-FF6600?style=flat-square)](https://ollama.com)
[![Groq](https://img.shields.io/badge/Groq-Cloud_LLM-7C3AED?style=flat-square)](https://groq.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-memory-green?style=flat-square)](https://www.trychroma.com/)
[![License](https://img.shields.io/badge/license-MIT-22c55e?style=flat-square)](LICENSE)

<br/>

> 100% local LLM support. Voice in, voice out. No web UI needed.

[Quick Start](#-quick-start) | [Commands](#-commands) | [Features](#-features) | [Architecture](#-architecture) | [Configuration](#%EF%B8%8F-configuration)

---

</div>

## Quick Start

### Prerequisites

- **Python 3.11+**
- **Ollama** (for local LLM) — [ollama.com](https://ollama.com)
- **Groq API key** (for cloud LLM) — [groq.com](https://groq.com) (free tier available)

### Install

```bash
cd JARVISE
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### First Run

```bash
# Cloud LLM (Groq) + Voice — recommended for first try
python main.py --way

# Select option 1 (groq), enter your API key, enter model: qwen/qwen3.8-27b
```

---

## Commands

### Starting JARVIS

| Command | Description |
|---------|-------------|
| `python main.py --way` | Interactive cloud provider selection (Groq/OpenRouter/Google) |
| `python main.py --way --text-only` | Cloud LLM, text-only (no mic/speaker) |
| `python main.py --model` | Auto-detect best local Ollama model for your hardware |
| `python main.py --ollama3.2 -run` | Pull llama3.2 if needed, then run locally |
| `python main.py --qwen2.5-coder:7b -run` | Pull and run a specific Ollama model |
| `python main.py --verbose` | Show detailed logs (STT, TTS, LLM timing) |
| `python main.py --text-only` | Text input only (no voice pipeline) |
| `python main.py --disable-router` | Skip command router, always use LLM |

### Voice Commands (while running)

| Say | Action |
|-----|--------|
| **Press Space** | Start listening (hold to talk, release to process) |
| "stop" / "cancel" / "shut up" | Interrupt TTS playback |

### CLI Shortcuts (type at the `You:` prompt)

| Input | Action |
|-------|--------|
| `triage` / `check email` | Run email triage |
| `conflicts` / `check conflicts` | Check calendar conflicts |
| `suggest times` / `meeting times` | Get available meeting slots |
| `suggest` / `suggestions` / `what should i do` | Get proactive suggestions |
| `exit` / `quit` | Shutdown JARVIS |

### Example Session

```
(.venv) PS C:\JARVISE> python main.py --way

You: What time is it?
JARVIS: It's 3:45 PM on September 18, 2026.

You: search the web for latest AI news
JARVIS: [searches web, summarizes top 5 articles]

You: remember that I prefer dark mode
JARVIS: Got it. I'll remember you prefer dark mode.

You: what do you know about me?
JARVIS: You prefer dark mode...

You: triage
Email Triage: 3 urgent, 5 normal, 2 promotional

You: exit
```

---

## Features

### 9 Core Features

| # | Feature | Module | What It Does |
|---|---------|--------|--------------|
| 1 | **Voice Pipeline** | `voice/` | Push-to-talk STT (Whisper) + TTS (Kokoro) + VAD + interrupt handling |
| 2 | **HITL Decision Engine** | `brain/hitl.py` | 3-tier risk classification (GREEN/YELLOW/RED), confirmation prompts, undo tracking, audit log |
| 3 | **RAG Memory** | `memory/` | ChromaDB vector store, MEMORY.md facts, learned preferences, forget stale entries |
| 4 | **Proactive Suggestions** | `brain/proactive.py` | Detects interaction patterns, suggests follow-ups, time-of-day awareness |
| 5 | **Calendar + Email** | `brain/calendar_email.py` | Email triage (urgent/important/promo), conflict detection, meeting slot suggestions, draft replies |
| 6 | **Browser Automation** | `tools/browser.py` | Navigate, extract, click, fill, screenshot, tabs, multi-step research with citations |
| 7 | **Code Sandbox** | `brain/sandbox.py` | Sandboxed Python/shell execution, diff preview, blocked imports, execution history |
| 8 | **Multi-Agent** | `brain/multi_agent.py` | Parallel/sequential/pipeline agent execution, role-based prompts, budget tracking |
| 9 | **Task Planner** | `brain/planner.py` | Goal decomposition, dependency graphs, progress tracking, replanning |

### 19 Registered Tools

| Tool | Risk | Description |
|------|------|-------------|
| `browser` | GREEN | Browser automation (navigate, click, fill, screenshot, tabs) |
| `research` | GREEN | Multi-step research with source citations |
| `web_search` | GREEN | DuckDuckGo web search |
| `filesystem` | YELLOW | Read/write/delete files |
| `execute_code` | RED | Sandboxed Python/shell execution |
| `google_calendar` | YELLOW | Google Calendar events |
| `google_email` | YELLOW | Gmail read/send |
| `outlook` | YELLOW | Microsoft Outlook/Exchange |
| `system_monitor` | GREEN | CPU, RAM, GPU stats |
| `get_time` | GREEN | Current time |
| `get_date` | GREEN | Current date |
| `pwd` | GREEN | Current directory |
| `remember` | GREEN | Save to memory |
| `recall` | GREEN | Search memory |
| `list_memories` | GREEN | List all memories |
| `forget` | GREEN | Delete a memory |
| `calendar_email` | YELLOW | Unified calendar + email orchestrator |
| `multi_agent` | YELLOW | Spawn sub-agents for parallel work |
| `planner` | GREEN | Create and manage task plans |

---

## Architecture

```
You (voice or text)
    |
    v
Voice Pipeline (STT)  ──or──  CLI Input
    |
    v
Command Router ──────────────> Direct Tool (fast path)
    |                               |
    v                               v
ReAct Agent + LLM             Tool Execution
    |                               |
    v                               v
Response ───────────────────> TTS (speaks) + Text Output
```

### LLM Providers

| Provider | Command | Speed | Cost |
|----------|---------|-------|------|
| **Groq** (cloud) | `--way` → select groq | Fastest (~200ms) | Free tier |
| **OpenRouter** (cloud) | `--way` → select openrouter | Fast | Free models available |
| **Google Gemini** (cloud) | `--way` → select google | Fast | Free tier |
| **Ollama** (local) | `--model` or `--<name> -run` | Depends on hardware | Free |

---

## Configuration

### `.env` File

```env
# Ollama (local fallback)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest

# Cloud providers (used with --way)
GROQ_API_KEY=gsk_...
GROQ_MODEL=qwen/qwen3.8-27b
OPENROUTER_API_KEY=
OPENROUTER_MODEL=meta-llama/llama-3.2-3b-instruct:free
GOOGLE_AI_API_KEY=
GOOGLE_AI_MODEL=gemini-2.0-flash

# Voice
WHISPER_MODEL=base
KOKORO_VOICE=bm_lewis
TTS_SPEED=1.0

# Memory
CHROMA_PERSIST_DIRECTORY=./data/chromadb
MEMORY_FILE=./data/MEMORY.md

# Logging
LOG_LEVEL=INFO
LOG_FILE=./data/jarvis.log
```

### Hardware Profiles

JARVIS auto-detects your hardware and picks the right STT model:

| Hardware | STT Model | Notes |
|----------|-----------|-------|
| NVIDIA GPU (4GB+) | `tiny` on CUDA | Fastest transcription |
| NVIDIA GPU (2GB+) | `tiny` on CUDA | Good balance |
| CPU only | `tiny` on CPU | Slower but works |

---

## Testing

```bash
# Run all feature tests (72 tests across 9 features)
python tests/test_all_features.py

# Verbose output
python tests/test_all_features.py 2>&1 | Select-String -Pattern "\[PASS\]|\[FAIL\]"
```

---

## Project Structure

```
JARVISE/
├── brain/                  # Core AI
│   ├── agent.py            # ReAct agent loop
│   ├── tools.py            # Tool registry (19 tools)
│   ├── router.py           # Command router (fast path)
│   ├── hitl.py             # Human-in-the-loop + undo
│   ├── audit.py            # JSONL audit log
│   ├── proactive.py        # Proactive suggestions
│   ├── calendar_email.py   # Email triage + calendar
│   ├── research.py         # Multi-step research
│   ├── sandbox.py          # Code execution sandbox
│   ├── multi_agent.py      # Multi-agent orchestration
│   ├── planner.py          # Task planning + goals
│   ├── prompt_builder.py   # Prompt assembly
│   └── providers/          # LLM providers (Ollama, Groq, etc.)
├── voice/                  # Voice pipeline
│   ├── pipeline.py         # Voice orchestrator
│   ├── stt.py              # Speech-to-text (Whisper)
│   ├── tts.py              # Text-to-speech (Kokoro)
│   ├── vad.py              # Voice activity detection
│   ├── recorder.py         # Audio recording
│   ├── audio_output.py     # Speaker output
│   └── keyboard_handler.py # Push-to-talk
├── memory/                 # Memory system
│   ├── MemoryManager.py    # Unified memory facade
│   ├── chroma_store.py     # ChromaDB vector store
│   ├── filtered_store.py   # Filtered memory
│   ├── preference_store.py # User preferences
│   ├── memory_file.py      # MEMORY.md controller
│   └── importance.py       # Importance scoring
├── tools/                  # Tool modules
│   ├── base.py             # RiskLevel, BaseTool
│   ├── browser.py          # Browser automation
│   └── ...
├── learning/               # Learning modules
│   ├── preference_memory.py # Learned preferences
│   ├── tool_cache.py       # Tool result caching
│   └── retry_engine.py     # Smart retries
├── core/                   # Core utilities
│   ├── config.py           # Configuration
│   ├── hardware.py         # Hardware detection
│   └── logger.py           # Logging setup
├── data/                   # Runtime data (auto-created)
│   ├── chromadb/           # Vector store
│   ├── kokoro_models/      # TTS models
│   ├── audit.jsonl         # Audit log
│   └── ...
├── tests/
│   └── test_all_features.py # 72-test feature suite
├── main.py                 # Entry point
├── .env                    # Configuration
└── requirements.txt        # Dependencies
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Voice pipeline failed` | Run with `--text-only` flag |
| `Ollama not responding` | Start Ollama: `ollama serve` |
| `Groq API error` | Check API key in `.env` |
| `Preference memory error` | Delete `data/preferences.json` and restart |
| Slow responses | Use `--way` with Groq (fastest cloud provider) |
| TTS not speaking | Check speaker output, TTS models in `data/kokoro_models/` |
| STT not hearing | Check microphone, try Space bar push-to-talk |

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built for privacy. Designed for speed. Made to be yours.**

*JARVIS — Your Personal AI Assistant*

</div>
