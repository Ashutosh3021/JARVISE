# JARVIS AI Assistant

Your personal AI assistant with voice, web UI, and CLI

---

## Features

- 🤖 **AI Chat** - Conversational AI with context awareness
- 🧠 **Memory** - Persistent conversation history with vector storage
- 🎤 **Voice** - Speech-to-text (Whisper) and text-to-speech (Kokoro)
- 📊 **System Monitoring** - CPU, memory, GPU stats
- 🌐 **Web UI** - Beautiful browser-based interface
- 💻 **CLI** - Terminal interface (pip/npm installable)
- 🔌 **API** - REST API for integrations

---

## Quick Start

### 1. Start the Server

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
# or: source .venv/bin/activate  # Linux/Mac

# Start JARVIS
python main.py
```

Open http://localhost:8000 in your browser

---

## Web UI Usage

The sidebar navigation provides access to:

| Page | Description |
|------|-------------|
| **Chat** | Main conversation interface |
| **Memory** | View conversation history |
| **System** | CPU, memory, GPU monitoring |
| **Voice** | Voice settings |
| **Settings** | Configuration options |

---

## CLI Installation & Usage

### Python (pip)

```bash
# Install
pip install jarvis-ai

# Or install from source
cd cli
pip install -e .
```

### Node.js (npm)

```bash
# Navigate to npm package
cd dist-npm

# Install
npm install

# Or globally
npm install -g
```

---

## CLI Commands

### Interactive Shell

```bash
jarvis shell
# or
python -m cli shell
```

Commands inside shell:
- Type normally to chat
- `:help` - Show help
- `:stats` - System statistics
- `:memory` - View memories
- `:clear` - Clear conversation
- `:quit` - Exit

### One-liner Chat

```bash
jarvis chat "Hello, how are you?"
```

### Memory Management

```bash
jarvis memory list           # List all memories
jarvis memory search "query" # Search memories
jarvis memory stats          # Memory statistics
jarvis memory clear         # Clear all memories
```

### System Stats

```bash
jarvis stats
```

### Web UI

```bash
jarvis web    # Open browser UI
```

### Server Management

```bash
jarvis server start  # Start server
jarvis server stop   # Stop server
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `JARVIS_URL` | Server URL | http://localhost:8000 |
| `JARVIS_API_KEY` | API key (if required) | - |
| `OLLAMA_HOST` | Ollama server | localhost:11434 |
| `OLLAMA_MODEL` | Model to use | llama3.2:latest |

---

## Development

### Project Structure

```
JARVIS/
├── backend/         # FastAPI server
├── brain/           # AI agent logic
├── cli/             # Python CLI package
├── dist-npm/        # npm package
├── memory/          # Vector store & memory
├── ui/              # React frontend
├── voice/           # STT/TTS pipeline
├── main.py          # Entry point
└── .env             # Configuration
```

### Running in Development

```bash
# Backend only (API)
python -m backend.main

# Full app with UI
python main.py

# CLI (development)
python -m cli --help
python -m cli shell
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, Python |
| AI | Ollama (Llama 3.2), LangChain |
| Memory | ChromaDB |
| STT | Faster Whisper |
| TTS | Kokoro |
| Frontend | React, TypeScript |
| CLI | Python (argparse), Node.js |

---

## License

MIT License - See LICENSE file

---

## Support

For issues and questions, please check the Docs folder or open an issue on GitHub.
