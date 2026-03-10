# ROADMAP: JARVIS

**Project:** JARVIS - Windows AI Voice Assistant
**Created:** 2026-02-28
**Core Value:** A privacy-focused, always-available AI assistant that runs entirely locally on Windows, understanding context through vector memory and executing tasks through integrated system tools.
**Hardware:** Ryzen 5 5000U, 16GB RAM, AMD Radeon (CPU-only), Target latency <3s

---

## Phases

- [x] **Phase 1: Project Setup & Environment** - Scaffold project with dependencies, requirements.txt, .env.example
  **Plans:** 1 plan

Plans:
- [x] 01-project-setup-01-PLAN.md — Scaffold project with directory structure, dependencies, and configuration templates

- [x] **Phase 2: Core Hardware Detection & Config** - VRAM detection, config loader, logger (completed 2026-02-28)
  **Plans:** 3 plans

Plans:
- [x] 02-core-hardware-01-PLAN.md — Hardware detection module (CPU/GPU, VRAM)
- [x] 02-core-hardware-02-PLAN.md — Configuration system with profile selection
- [x] 02-core-hardware-03-PLAN.md — Centralized logging system

- [x] **Phase 3: Voice Pipeline** - Push-to-talk, STT, TTS, VAD (completed 2026-03-01)
  **Plans:** 1 plan

Plans:
- [x] 03-voice-pipeline-03-PLAN.md — Complete audio input/output pipeline

- [x] **Phase 4: Brain Layer** - LLM client, prompt builder, ReAct agent (completed 2026-03-01)
  **Plans:** 1 plan

Plans:
- [x] 04-BRAIN-LAYER-01-PLAN.md — Ollama client, prompt builder, ReAct agent, tools, errors

- [x] **Phase 5: Memory System** - ChromaDB, MEMORY.md, MemoryManager (completed 2026-03-02)

- [x] **Phase 6: System Tool Integrations** - search, browser, filesystem, calendar, email (completed 2026-03-02)
  **Plans:** 3 plans

Plans:
- [x] 06-01-PLAN.md — Core tools: web search, browser, filesystem, code exec
- [ ] 06-02-PLAN.md — Google Calendar and Email integrations with OAuth2
- [ ] 06-03-PLAN.md — Microsoft Outlook, system monitor, tool registry

- [x] **Phase 7: UI Layer** - FastAPI backend, React frontend (completed 2026-03-04)
  **Plans:** 3 plans

Plans:
- [x] 07-01-PLAN.md — FastAPI backend with WebSocket support
- [x] 07-02-PLAN.md — React SPA with dark theme foundation
- [x] 07-03-PLAN.md — Chat interface and live stats

- [ ] **Phase 0: Performance Fixes** - Hardware-aware models, learning system
  **Plans:** 2 plans

Plans:
- [ ] 00-01-PLAN.md — Hardware-aware STT/LLM model selection
- [ ] 00-02-PLAN.md — Learning system (auto-retry + preference memory)

- [ ] **Phase 8: Boot Sequence & Main Loop** - main.py entry point
  **Plans:** 1 plan

Plans:
- [ ] 08-01-PLAN.md — Unified entry point with graceful shutdown

- [ ] **Phase 9: Test Suite Validation** - unit tests, integration tests
- [x] **Phase 10: Final Polish & Documentation** - README, ARCHITECTURE.md, error handlers (completed 2026-03-09)
  **Plans:** 1 plan

Plans:
- [x] 10-01-PLAN.md — Final polish: README, ARCHITECTURE.md, CHANGELOG.md

- [ ] **Phase 11: Polish & Reliability** - Context awareness, command routing, learning engine, task chains, filtered memory
  **Plans:** 5 plans

Plans:
- [ ] 11-01-PLAN.md — Context Engine (system context, project detection, app tracking)
- [ ] 11-02-PLAN.md — Command Router (simple commands bypass LLM)
- [ ] 11-03-PLAN.md — Learning Engine (retry + preference memory)
- [ ] 11-04-PLAN.md — Task Chains (multi-step workflows)
- [ ] 11-05-PLAN.md — Filtered Vector Memory (importance-based storage)

---

## Phase Details

### Phase 1: Project Setup & Environment
**Goal:** Scaffold project with directory structure, dependencies, and configuration templates
**Depends on:** Nothing (first phase)
**Requirements:** PS-01, PS-02, PS-03, PS-04, PS-05
**Success Criteria** (what must be TRUE):
  1. Developer can run `pip install -e .` and get all dependencies installed without errors
  2. `.env` file can be created from `.env.example` template and loaded successfully
  3. Project directory structure exists with all required folders (core/, voice/, brain/, memory/, tools/, ui/, data/, tests/)
**Plans:** 1/1 plans complete

Plans:
- [x] 08-01-PLAN.md — Unified entry point with graceful shutdown

### Phase 2: Core Hardware Detection & Config
**Goal:** Detect hardware capabilities, load configuration, setup logging
**Depends on:** Phase 1
**Requirements:** HW-01, HW-02, HW-03, HW-04
**Success Criteria** (what must be TRUE):
  1. Application reports detected hardware (CPU/GPU, VRAM amount) at startup
  2. Configuration profile is automatically selected based on VRAM (CPU/Low GPU/Mid GPU/High GPU)
  3. Logs are written to both console and file with proper formatting
**Plans:** 3/3 plans complete

### Phase 3: Voice Pipeline
**Goal:** Complete audio input/output pipeline with wake word detection
**Depends on:** Phase 2
**Requirements:** VP-01, VP-02, VP-03, VP-04, VP-05, VP-06, VP-07
**Success Criteria** (what must be TRUE):
  1. Push-to-talk (space bar) activates voice listening when pressed
  2. Voice Activity Detection filters out silence and noise
  3. Voice input is transcribed to text using faster-whisper
  4. Text response is spoken aloud using Kokoro TTS through speakers
**Plans:** 1/1 plans complete

### Phase 4: Brain Layer
**Goal:** Local LLM integration with ReAct reasoning loop
**Depends on:** Phase 2, Phase 5
**Requirements:** BL-01, BL-02, BL-03, BL-04, BL-05, BL-06
**Success Criteria** (what must be TRUE):
  1. Ollama server connection is verified and working at startup
  2. User text input is processed through ReAct loop (Reason → Act → Observe → Repeat)
  3. Tool actions are parsed from LLM output and executed correctly
  4. Streaming response is returned to user in real-time
**Plans:** 1/1 plans complete

### Phase 5: Memory System
**Goal:** Persistent vector and file-based memory storage
**Depends on:** Phase 4
**Requirements:** MS-01, MS-02, MS-03, MS-04
**Success Criteria** (what must be TRUE):
  1. Conversations are embedded and stored in ChromaDB vector store
  2. MEMORY.md file can be read and written by the system
  3. Relevant context is retrieved from memory for LLM prompts
**Plans:** TBD

### Phase 6: System Tool Integrations
**Goal:** Executable tools for agent to interact with system
**Depends on:** Phase 4, Phase 5
**Requirements:** ST-01, ST-02, ST-03, ST-04, ST-05, ST-06, ST-07, ST-08, ST-09
**Success Criteria** (what must be TRUE):
  1. Web search tool returns relevant results from search queries
  2. Browser automation can open pages and interact via Playwright
  3. Filesystem tool can read and write files to disk
  4. Calendar and email integrations connect and authenticate successfully
**Plans:** 3/3 plans complete

### Phase 7: UI Layer
**Goal:** Web interface for monitoring and control
**Depends on:** Phase 6
**Requirements:** UI-01, UI-02, UI-03, UI-04, UI-05, UI-06, UI-07, UI-08
**Success Criteria** (what must be TRUE):
  1. FastAPI server starts with WebSocket support for streaming
  2. React SPA loads in browser with dark theme
  3. Live token streaming displays in chat window
  4. System stats (CPU, memory, VRAM) display in status bar
**Plans:** 3/3 plans complete

Plans:
- [x] 07-01-PLAN.md — FastAPI backend with WebSocket support
- [x] 07-02-PLAN.md — React SPA with dark theme foundation
- [x] 07-03-PLAN.md — Chat interface and live stats

### Phase 8: Boot Sequence & Main Loop
**Goal:** Unified entry point that initializes all components
**Depends on:** Phase 3, Phase 7
**Requirements:** BS-01, BS-02, BS-03, BS-04, BS-05, BS-06, BS-07, BS-08, BS-09, BS-10, BS-11, BS-12
**Success Criteria** (what must be TRUE):
  1. `python main.py` starts all components in correct sequence without errors
  2. `--text-only` flag runs the agent without voice components for testing
  3. Graceful shutdown handler stops all services cleanly on Ctrl+C
  4. ASCII startup banner displays JARVIS branding at launch
  5. Startup logs show initialization progress for each component
**Plans:** 1/1 plans complete

### Phase 9: Test Suite Validation
**Goal:** Automated testing to verify component functionality
**Depends on:** Phase 8
**Requirements:** TS-01, TS-02, TS-03, TS-04, TS-05, TS-06, TS-07, TS-08, TS-09
**Success Criteria** (what must be TRUE):
  1. Unit tests pass for hardware detection module
  2. Unit tests pass for LLM client module
  3. Unit tests pass for memory system
  4. Integration test passes: text input → agent → response
**Plans:** 1/1 plans complete

Plans:
- [x] 09-01-PLAN.md — Test suite with unit and integration tests

### Phase 10: Final Polish & Documentation
**Goal:** Complete documentation and error handling
**Depends on:** Phase 9
**Requirements:** DOC-01, DOC-02, DOC-03, DOC-04, DOC-05
**Success Criteria** (what must be TRUE):
  1. README.md contains complete setup and usage instructions
  2. ARCHITECTURE.md contains system diagrams and component descriptions
  3. Error handlers catch and log exceptions across all modules
**Plans:** 1/1 plans complete

Plans:
- [x] 10-01-PLAN.md — Final polish: README, ARCHITECTURE.md, CHANGELOG.md

### Phase 11: Polish & Reliability
**Goal:** Make JARVIS proactive, context-aware, and self-improving
**Depends on:** Phase 10
**Requirements:** CTX-01, CTX-02, CTX-03, CTX-04, ROU-01, ROU-02, ROU-03, ROU-04, LRN-01, LRN-02, LRN-03, LRN-04, CHN-01, CHN-02, CHN-03, CHN-04, MEM-01, MEM-02, MEM-03, MEM-04
**Success Criteria** (what must be TRUE):
  1. JARVIS knows environment context (directory, project, apps, git)
  2. Simple commands bypass LLM for speed
  3. Failed tools retry with alternatives automatically
  4. User corrections are remembered across sessions
  5. Multi-step task chains execute correctly
  6. Memory stores only important content
**Plans:** 5 plans

Plans:
- [x] 11-01-PLAN.md — Context Engine (system context, project detection, app tracking)
- [x] 11-02-PLAN.md — Command Router (simple commands bypass LLM)
- [ ] 11-03-PLAN.md — Learning Engine (retry + preference memory)
- [ ] 11-04-PLAN.md — Task Chains (multi-step workflows)
- [ ] 11-05-PLAN.md — Filtered Vector Memory (importance-based storage)

---

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Project Setup & Environment | 1/1 | Complete    | 2026-02-28 |
| 2. Core Hardware Detection & Config | 3/3 | Complete    | 2026-02-28 |
| 3. Voice Pipeline | 1/1 | Complete    | 2026-03-01 |
| 4. Brain Layer | 1/1 | Complete    | 2026-03-01 |
| 5. Memory System | 1/1 | Complete    | 2026-03-02 |
| 6. System Tool Integrations | 1/3 | Complete    | 2026-03-02 |
| 7. UI Layer | 3/3 | Complete    | 2026-03-04 |
| 8. Boot Sequence & Main Loop | 1/1 | Complete    | 2026-03-08 |
| 9. Test Suite Validation | 1/1 | Complete    | 2026-03-08 |
| 10. Final Polish & Documentation | 1/1 | Complete    | 2026-03-09 |
| 11. Polish & Reliability | 2/5 | In Progress | - |

---

*Last updated: 2026-03-10*
