# J.A.R.V.I.S

> **Just A Rather Very Intelligent System**  
> A privacy-focused, local AI assistant — voice-controlled, system-aware, and always on call.

---

## What is J.A.R.V.I.S?

J.A.R.V.I.S is a **locally-run AI assistant** that runs entirely on your machine. No cloud subscriptions, no data leaves your PC.

- 🎙️ **Voice commands** — Push-to-talk (spacebar) activates listening
- 🧠 **Local AI** — Uses Ollama for privacy-first reasoning
- 💾 **Memory** — ChromaDB vector store + persistent MEMORY.md
- 🔧 **System automation** — Opens apps, manages files, runs code
- 🌐 **Web tools** — Search, browser automation, research
- ⚡ **Fast** — Hardware-aware model selection (CPU/GPU)

---

## Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|--------------|
| RAM | 8GB | 16GB |
| CPU | Any modern | Ryzen 5 / i5+ |
| GPU | Optional | NVIDIA / AMD for faster AI |
| Storage | 5GB free | 10GB+ for models |

### Model Selection (Automatic)

JARVIS auto-selects models based on your hardware:

| Profile | VRAM | STT Model | LLM Model |
|---------|------|-----------|------------|
| CPU | 0MB | tiny | qwen2.5-coder:7b |
| Low GPU | 2-4GB | base | qwen2.5-coder:7b |
| Mid GPU | 4-8GB | small | mistral:7b |
| High GPU | 8GB+ | medium | llama3.2:latest |

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/JARVIS.git
cd JARVIS
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download from https://ollama.com/download/windows
```

### 4. Pull a model

```bash
ollama pull qwen2.5-coder:7b
```

### 5. Configure

```bash
# Copy example env file
cp .env.example .env

# Edit with your settings (optional)
```

---

## Usage

### Quick Start

```bash
# Text-only mode (no voice)
python main.py --text-only

# With UI (opens web dashboard)
python main.py

# With voice (requires microphone)
python main.py --headless
```

### Command Line Options

| Flag | Description |
|------|-------------|
| `--text-only` | Run without voice (text input only) |
| `--headless` | Run without UI (backend only) |
| `--verbose` / `-v` | Enable debug logging |

### Running JARVIS

```bash
# Default: text-only with UI
python main.py

# Output:
#    JARVIS   AI   Assistant
#    =======================
#    Starting up...
#
# Hardware: 6 cores, 0MB VRAM
# Profile: CPU
# Whisper Model: tiny
# LLM Model: qwen2.5-coder:7b
# Memory initialized
# Agent ready
# UI available at http://localhost:8000
#
# You:
```

---

## Configuration

Configuration is loaded from `.env` file:

```bash
# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b

# Voice
WHISPER_MODEL=base
KOKORO_VOICE=bm_lewis

# Memory
CHROMA_PERSIST=./data/chromadb
MEMORY_FILE=./data/MEMORY.md

# UI
UI_HOST=0.0.0.0
UI_PORT=8000
```

---

## Features

### Voice Pipeline
- **Push-to-talk** — Hold spacebar to speak
- **VAD** — Voice Activity Detection filters silence
- **STT** — Faster-Whisper for transcription
- **TTS** — Kokoro for natural speech output

### Brain (AI Agent)
- **ReAct pattern** — Reasoning + Acting loop
- **Tool execution** — Single tool at a time
- **Streaming** — Real-time response via WebSocket

### Memory System
- **ChromaDB** — Vector store for conversation embeddings
- **MEMORY.md** — Human-editable persistent facts
- **Context retrieval** — Relevant memories injected into prompts

### Tools
- **Web search** — DuckDuckGo integration
- **Browser automation** — Playwright-based
- **Filesystem** — Read/write with safety guards
- **Code execution** — Sandboxed Python runner
- **Calendar/Email** — Google & Microsoft OAuth integrations

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    JARVIS v1.0                        │
├─────────────────────────────────────────────────────────┤
│  Input Layer                                          │
│  ├── Voice (Spacebar PTT)                            │
│  ├── Text (CLI/UI)                                   │
│  └── WebSocket (UI chat)                             │
├─────────────────────────────────────────────────────────┤
│  Processing Layer                                     │
│  ├── STT (faster-whisper)                           │
│  ├── LLM (Ollama)                                   │
│  ├── ReAct Agent                                     │
│  └── Tool System                                     │
├─────────────────────────────────────────────────────────┤
│  Memory Layer                                        │
│  ├── ChromaDB (vector store)                        │
│  └── MEMORY.md (persistent facts)                   │
├─────────────────────────────────────────────────────────┤
│  Output Layer                                        │
│  ├── TTS (Kokoro)                                  │
│  ├── Text response                                  │
│  └── UI (FastAPI + React)                          │
└─────────────────────────────────────────────────────────┘
```

### Module Structure

| Module | Purpose |
|--------|---------|
| `core/` | Config, hardware detection, logging |
| `voice/` | STT, TTS, VAD, audio pipeline |
| `brain/` | Agent, LLM client, tool registry |
| `memory/` | ChromaDB, MEMORY.md, context retrieval |
| `tools/` | Filesystem, browser, code execution |
| `backend/` | FastAPI, WebSocket, REST endpoints |
| `ui/` | React frontend |

---

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Adding Tools

1. Create tool in `tools/` directory
2. Inherit from `BaseTool`
3. Register in `brain/tools.py`

### Custom Models

Edit `.env` to change models:

```bash
# For faster CPU inference
OLLAMA_MODEL=qwen2.5-coder:2b

# For better reasoning (requires GPU)
OLLAMA_MODEL=mistral:7b
```

---

## Troubleshooting

### Voice not working

```bash
# Test with text-only mode
python main.py --text-only
```

### Ollama not connecting

```bash
# Check Ollama is running
ollama list

# Restart Ollama
ollama serve
```

### Memory errors

```bash
# Clear ChromaDB
rm -rf data/chromadb/

# Edit MEMORY.md
notepad data/MEMORY.md
```

---

## Roadmap

| Feature | Status |
|---------|--------|
| Voice commands (PTT) | ✅ Complete |
| Local LLM (Ollama) | ✅ Complete |
| Memory system | ✅ Complete |
| Tool integrations | ✅ Complete |
| UI dashboard | ✅ Complete |
| Test suite | ✅ Complete |
| Wake word detection | 🔲 Future |
| Multi-user support | 🔲 Future |

---

## License

MIT — see [LICENSE](./LICENSE)

---

*"At your service."*
