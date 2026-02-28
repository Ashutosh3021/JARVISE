# ROADMAP: JARVIS

**Project:** JARVIS - Windows AI Voice Assistant
**Created:** 2026-02-28
**Core Value:** A privacy-focused, always-available AI assistant that runs entirely locally on Windows, understanding context through vector memory and executing tasks through integrated system tools.

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
- [ ] 02-core-hardware-02-PLAN.md — Configuration system with profile selection
- [x] 02-core-hardware-03-PLAN.md — Centralized logging system
- [ ] **Phase 3: Voice Pipeline** - Wake word, STT, TTS
- [ ] **Phase 4: Brain Layer** - LLM client, prompt builder, ReAct agent
- [ ] **Phase 5: Memory System** - ChromaDB, MEMORY.md, MemoryManager
- [ ] **Phase 6: System Tool Integrations** - search, browser, filesystem, calendar, email
- [ ] **Phase 7: UI Layer** - FastAPI backend, React frontend
- [ ] **Phase 8: Boot Sequence & Main Loop** - main.py entry point
- [ ] **Phase 9: Test Suite Validation** - unit tests, integration tests
- [ ] **Phase 10: Final Polish & Documentation** - README, ARCHITECTURE.md, error handlers

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
  1. Wake word "JARVIS" triggers voice listening when spoken
  2. Voice Activity Detection filters out silence and noise
  3. Voice input is transcribed to text using faster-whisper
  4. Text response is spoken aloud using Kokoro TTS through speakers
**Plans:** TBD

### Phase 4: Brain Layer
**Goal:** Local LLM integration with ReAct reasoning loop
**Depends on:** Phase 2, Phase 5
**Requirements:** BL-01, BL-02, BL-03, BL-04, BL-05, BL-06
**Success Criteria** (what must be TRUE):
  1. Ollama server connection is verified and working at startup
  2. User text input is processed through ReAct loop (Reason → Act → Observe → Repeat)
  3. Tool actions are parsed from LLM output and executed correctly
  4. Streaming response is returned to user in real-time
**Plans:** TBD

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
**Plans:** TBD

### Phase 7: UI Layer
**Goal:** Web interface for monitoring and control
**Depends on:** Phase 6
**Requirements:** UI-01, UI-02, UI-03, UI-04, UI-05, UI-06, UI-07, UI-08
**Success Criteria** (what must be TRUE):
  1. FastAPI server starts with WebSocket support for streaming
  2. React SPA loads in browser with dark theme
  3. Live token streaming displays in chat window
  4. System stats (CPU, memory, VRAM) display in status bar
**Plans:** TBD

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
**Plans:** TBD

### Phase 9: Test Suite Validation
**Goal:** Automated testing to verify component functionality
**Depends on:** Phase 8
**Requirements:** TS-01, TS-02, TS-03, TS-04, TS-05, TS-06, TS-07, TS-08, TS-09
**Success Criteria** (what must be TRUE):
  1. Unit tests pass for hardware detection module
  2. Unit tests pass for LLM client module
  3. Unit tests pass for memory system
  4. Integration test passes: text input → agent → response
**Plans:** TBD

### Phase 10: Final Polish & Documentation
**Goal:** Complete documentation and error handling
**Depends on:** Phase 9
**Requirements:** DOC-01, DOC-02, DOC-03, DOC-04, DOC-05
**Success Criteria** (what must be TRUE):
  1. README.md contains complete setup and usage instructions
  2. ARCHITECTURE.md contains system diagrams and component descriptions
  3. Error handlers catch and log exceptions across all modules
**Plans:** TBD

---

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Project Setup & Environment | 1/1 | Complete    | 2026-02-28 |
| 2. Core Hardware Detection & Config | 2/3 | Complete    | 2026-02-28 |
| 3. Voice Pipeline | 0/1 | Not started | - |
| 4. Brain Layer | 0/1 | Not started | - |
| 5. Memory System | 0/1 | Not started | - |
| 6. System Tool Integrations | 0/1 | Not started | - |
| 7. UI Layer | 0/1 | Not started | - |
| 8. Boot Sequence & Main Loop | 0/1 | Not started | - |
| 9. Test Suite Validation | 0/1 | Not started | - |
| 10. Final Polish & Documentation | 0/1 | Not started | - |

---

*Last updated: 2026-02-28*
