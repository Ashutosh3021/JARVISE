# CHANGELOG

All notable changes to JARVIS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-03-09

### Added

#### Core Infrastructure
- **Hardware Detection** - Automatic CPU/GPU detection with VRAM measurement using psutil and gpu-list
- **Configuration System** - Profile-based config (cpu/low/mid/high) with automatic selection based on hardware
- **Logging System** - Centralized logging with loguru, file rotation, and color-coded console output

#### Voice Pipeline
- **Speech-to-Text (STT)** - faster-whisper integration with model selection based on hardware
- **Text-to-Speech (TTS)** - Kokoro TTS (bm_lewis) with natural British male voice
- **Voice Activity Detection (VAD)** - WebRTC VAD with energy-based fallback for Windows compatibility
- **Push-to-Talk** - Space bar activation for privacy-focused voice input

#### Brain Layer
- **Ollama Client** - Local LLM integration with qwen2.5-coder:7b as default model
- **ReAct Agent** - Reasoning loop (Reason → Act → Observe → Repeat) with tool execution
- **Prompt Builder** - Dynamic prompt construction with context from memory
- **Streaming Response** - Real-time token streaming to user interface

#### Memory System
- **Vector Memory** - ChromaDB integration for semantic search of conversation history
- **File Memory** - MEMORY.md for persistent human-editable facts
- **Context Retrieval** - Automatic relevant context injection into LLM prompts

#### System Tools
- **Web Search** - DuckDuckGo integration for real-time information
- **Browser Automation** - Playwright-based web browsing and interaction
- **Filesystem Operations** - File read/write capabilities
- **Code Execution** - Safe Python code execution in sandboxed environment

#### User Interface
- **FastAPI Backend** - REST API with WebSocket support for streaming
- **React Frontend** - Modern SPA with Vite and Tailwind CSS
- **Dark Theme** - Slate dark theme (#1e1e2e) with teal accent (#14b8a6)
- **Live Stats** - Real-time CPU, memory, and VRAM monitoring
- **Chat Interface** - Message history with streaming token display

#### Boot & Runtime
- **Unified Entry Point** - `python main.py` initializes all components
- **Command-Line Flags** - `--text-only`, `--headless`, `--verbose` for different modes
- **Graceful Shutdown** - Clean termination of all services on Ctrl+C
- **ASCII Banner** - JARVIS branding on startup

#### Testing
- **Unit Tests** - Hardware detection, config loader, memory system tests
- **Integration Tests** - End-to-end text input → agent → response flow
- **30 Test Cases** - Comprehensive coverage of core functionality

### Configuration

- **Hardware-Aware Model Selection** - Automatic STT/LLM model selection based on available VRAM
- **Config Profiles** - cpu, low (2GB), mid (4GB), high (8GB+) configurations
- **Environment Variables** - `.env.example` template for all settings

### Dependencies

- **Python 3.11+** - Language runtime
- **Ollama** - Local LLM server (separate installation)
- **faster-whisper** - Speech recognition
- **Kokoro** - Text-to-speech
- **ChromaDB** - Vector database
- **Playwright** - Browser automation
- **FastAPI** - Web framework
- **React + Vite** - Frontend framework
- **Tailwind CSS** - Styling

---

## [0.1.0] - 2026-02-28

### Added

- Initial project scaffolding
- Directory structure (core/, voice/, brain/, memory/, tools/, ui/, data/, tests/)
- `.env.example` configuration template
- `requirements.txt` with all dependencies

---

## Future Considerations

### Planned Features (Post-v1.0)
- Google Calendar integration with OAuth2
- Microsoft Outlook integration
- Email sending capabilities
- System monitor tool
- Text input fallback (GUI + CLI)
- Memory quality improvements
- Voice interrupt handling
- Learning system for auto-retry and preference memory

---

*For upgrade instructions, see [README.md](./README.md).*
