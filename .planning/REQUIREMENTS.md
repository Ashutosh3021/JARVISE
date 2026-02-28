# Requirements: JARVIS

**Defined:** 2026-02-28
**Core Value:** A privacy-focused, always-available AI assistant that runs entirely locally on Windows, understanding context through vector memory and executing tasks through integrated system tools.

## v1 Requirements

### Project Setup

- [x] **PS-01**: Project scaffold with directory structure (core/, voice/, brain/, memory/, tools/, ui/, data/, tests/)
- [x] **PS-02**: requirements.txt with pinned Python dependencies
- [x] **PS-03**: setup.py for virtual environment creation and installation
- [x] **PS-04**: .env.example template for API keys and configuration
- [x] **PS-05**: .gitignore excluding .env, cache, and model directories

### Hardware Detection

- [x] **HW-01**: Hardware detection module (CPU/GPU, VRAM measurement)
- [x] **HW-02**: Configuration profile selection (CPU, Low GPU, Mid GPU, High GPU)
- [x] **HW-03**: .env configuration loader with validation
- [ ] **HW-04**: Centralized logging system (console + file)

### Voice Pipeline

- [ ] **VP-01**: Push-to-talk activation (space bar) - User holds space to activate listening
- [ ] **VP-02**: Voice Activity Detection (VAD) for speech filtering
- [ ] **VP-03**: Audio recorder with proper buffering
- [ ] **VP-04**: Speech-to-text transcription (faster-whisper)
- [ ] **VP-05**: Text-to-speech synthesis (Kokoro)
- [ ] **VP-06**: Audio output to speakers
- [ ] **VP-07**: VoicePipeline unified class

### Brain Layer

- [ ] **BL-01**: Local LLM client (Ollama) with streaming support
- [ ] **BL-02**: Server health check for Ollama
- [ ] **BL-03**: Prompt builder injecting MEMORY.md and vector context
- [ ] **BL-04**: ReAct agent loop (Reason → Act → Observe → Repeat)
- [ ] **BL-05**: Tool action parsing and execution
- [ ] **BL-06**: Malformed output handling

### Memory System

- [ ] **MS-01**: ChromaDB vector store for conversation embeddings
- [ ] **MS-02**: MEMORY.md read/write controller for permanent facts
- [ ] **MS-03**: MemoryManager unifying vector and file storage
- [ ] **MS-04**: Template MEMORY.md with User Profile, Preferences, Important Facts, Ongoing Tasks

### System Tools

- [ ] **ST-01**: Web search tool
- [ ] **ST-02**: Browser automation (Playwright)
- [ ] **ST-03**: Filesystem manipulation tool
- [ ] **ST-04**: Code execution tool (sandboxed subprocess)
- [ ] **ST-05**: Google Calendar integration with OAuth2
- [ ] **ST-06**: Google Email integration with OAuth2
- [ ] **ST-07**: Microsoft Outlook integration
- [ ] **ST-08**: System monitor tool (diagnostics)
- [ ] **ST-09**: Tools registry for agent

### UI Layer

- [ ] **UI-01**: FastAPI server with WebSocket support
- [ ] **UI-02**: Live token streaming endpoint
- [ ] **UI-03**: Memory management endpoints
- [ ] **UI-04**: React single-page application
- [ ] **UI-05**: Dark-themed status bar
- [ ] **UI-06**: Animated waveform display
- [ ] **UI-07**: Chat window interface
- [ ] **UI-08**: Live system stats display

### Boot Sequence

- [ ] **BS-01**: main.py entry point with startup sequence
- [ ] **BS-02**: Logger initialization
- [ ] **BS-03**: Hardware detection at startup
- [ ] **BS-04**: Config loading
- [ ] **BS-05**: Memory initialization
- [ ] **BS-06**: LLM client startup
- [ ] **BS-07**: Agent initialization
- [ ] **BS-08**: Voice pipeline startup
- [ ] **BS-09**: UI server startup
- [ ] **BS-10**: --text-only flag for testing
- [ ] **BS-11**: Graceful shutdown handler
- [ ] **BS-12**: ASCII startup banner

### Testing

- [ ] **TS-01**: Unit tests for hardware detection
- [ ] **TS-02**: Unit tests for configuration loading
- [ ] **TS-03**: Unit tests for STT module
- [ ] **TS-04**: Unit tests for TTS module
- [ ] **TS-05**: Unit tests for LLM client
- [ ] **TS-06**: Unit tests for ReAct agent
- [ ] **TS-07**: Unit tests for memory system
- [ ] **TS-08**: Unit tests for tools
- [ ] **TS-09**: Integration test: text input to agent response

### Documentation

- [ ] **DOC-01**: README.md with setup instructions
- [ ] **DOC-02**: ARCHITECTURE.md with ASCII diagrams
- [ ] **DOC-03**: CHANGELOG.md initialization
- [ ] **DOC-04**: config.validate_config() for startup validation
- [ ] **DOC-05**: Error handlers across all modules

## v2 Requirements

### Enhanced Memory

- **EM-01**: Conversation summarization for long sessions
- **EM-02**: Automatic fact extraction and storage
- **EM-03**: Memory search with relevance scoring

### Advanced Tools

- **AT-01**: Slack integration
- **AT-02**: Discord bot functionality
- **AT-03**: Custom plugin system

### Voice Enhancements

- **VE-01**: Multiple wake word options
- **VE-02**: Voice customization (31 Kokoro voices)
- **VE-03**: Emotional tone adjustment

### Multi-User

- **MU-01**: User profile switching
- **MU-02**: Per-user memory isolation
- **MU-03**: Voice recognition for user identification

## Out of Scope

| Feature | Reason |
|---------|--------|
| Mobile apps | Windows desktop only for v1 |
| Cloud LLM APIs | Fully local operation for privacy |
| Real-time voice streaming | High latency, complex buffering — use push-to-talk |
| Multi-user support | Single user focus for v1 |
| Plugin marketplace | Security risks, maintenance burden |
| Cloud fallback | Violates privacy requirement |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PS-01 to PS-05 | Phase 1 | Complete |
| HW-01 | Phase 2 | Complete |
| HW-02 to HW-04 | Phase 2 | Pending |
| VP-01 to VP-07 | Phase 3 | Pending |
| BL-01 to BL-06 | Phase 4 | Pending |
| MS-01 to MS-04 | Phase 5 | Pending |
| ST-01 to ST-09 | Phase 6 | Pending |
| UI-01 to UI-08 | Phase 7 | Pending |
| BS-01 to BS-12 | Phase 8 | Pending |
| TS-01 to TS-09 | Phase 9 | Pending |
| DOC-01 to DOC-05 | Phase 10 | Pending |

**Coverage:**
- v1 requirements: 59 total
- Mapped to phases: 59
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-28*
*Last updated: 2026-02-28 after initial definition*
