```markdown
# JARVIS Project Execution Plan

## Project Overview
*   **Project Name:** JARVIS
*   **Wake Word:** "JARVIS"
*   **OS:** Windows
*   **Language:** Python 3.11+
*   **Agent Pattern:** ReAct loop (Reason → Act → Observe → Repeat)
*   **Memory Structure:** Vector Database (ChromaDB) + Human-readable core facts (`MEMORY.md`)

---

## GSD Phase Breakdown

### Phase 1: Project Setup & Environment
**GSD Command:** `/gsd-plan-phase 1` then `/gsd-execute-phase 1`
**Objective:** Create the complete project scaffold, virtual environment, and dependency files.
*   **Deliverables:**
    *   `requirements.txt`: Pin all core Python dependencies (local LLM tools, STT/TTS engines, Langchain, Playwright, API clients, FastAPI, etc.).
    *   `setup.py`: Script to create the virtual environment, install requirements, run playwright install, and create necessary data folders.
    *   `.env.example`: Template for API keys (Google, Microsoft) and configuration variables (Wake word, Base URLs, Log level).
    *   `.gitignore`: Exclude `.env`, cache, and data/model directories.
    *   **Folder Structure:** Empty `__init__.py` files in `core/`, `voice/`, `brain/`, `memory/`, `tools/`, `ui/`, `data/`, `tests/`.

### Phase 2: Core Hardware Detection & Config
**GSD Command:** `/gsd-plan-phase 2` then `/gsd-execute-phase 2`
**Objective:** Build hardware detection to auto-select the correct AI model tier based on available VRAM at startup.
*   **Deliverables:**
    *   `core/hardware.py`: Detect CPU/GPU, measure VRAM, and return a configuration profile (CPU, Low GPU, Mid GPU, High GPU).
    *   `core/config.py`: Load `.env`, run hardware detection, and export constants for the rest of the app.
    *   `core/logger.py`: Centralized logging system (console + file output).

### Phase 3: Voice Pipeline
**GSD Command:** `/gsd-plan-phase 3` then `/gsd-execute-phase 3`
**Objective:** Build the passive wake word detection ("Tita"), speech-to-text (STT), and text-to-speech (TTS) output.
*   **Deliverables:**
    *   `voice/wake_word.py`: Background listener triggering a callback on detection.
    *   `voice/stt.py`: Audio recorder with Voice Activity Detection (VAD) and transcription capabilities.
    *   `voice/tts.py`: Audio synthesizer mapped to the hardware config (blocking and async methods).
    *   `voice/__init__.py`: `VoicePipeline` class unifying wake, listen, and respond logic.

### Phase 4: Brain Layer (Agent Core)
**GSD Command:** `/gsd-plan-phase 4` then `/gsd-execute-phase 4`
**Objective:** Construct the LLM interface, ReAct loop, and dynamic system prompt builder.
*   **Deliverables:**
    *   `brain/llm.py`: Local LLM client wrapper with streaming support and server health checks.
    *   `brain/prompt.py`: Inject core `MEMORY.md` knowledge, vector memories, and available tools into the system prompt.
    *   `brain/agent.py`: `ReactAgent` loop to reason, parse tool actions, execute tools, and handle malformed outputs gracefully.

### Phase 5: Memory System
**GSD Command:** `/gsd-plan-phase 5` then `/gsd-execute-phase 5`
**Objective:** Implement the two-tier memory system.
*   **Deliverables:**
    *   `memory/chroma.py`: Vector store for conversation embeddings and fact storage.
    *   `memory/readme_memory.py`: Read/write controller for permanent facts.
    *   `memory/MEMORY.md`: Template initialized with User Profile, Preferences, Important Facts, and Ongoing Tasks.
    *   `memory/__init__.py`: `MemoryManager` unifying both storage tiers.

### Phase 6: System Tool Integrations
**GSD Command:** `/gsd-plan-phase 6` then `/gsd-execute-phase 6`
**Objective:** Build callable modules for the ReAct agent.
*   **Deliverables:**
    *   `tools/search.py` & `tools/browser.py`: Web search and Playwright web automation.
    *   `tools/filesystem.py` & `tools/code_exec.py`: File manipulation and sandboxed Python subprocess execution.
    *   `tools/calendar_*.py` & `tools/email_*.py`: Google and Microsoft integrations with OAuth2.
    *   `tools/system_monitor.py` & `tools/__init__.py`: Diagnostic tracking and the unified `TOOLS_REGISTRY` dict.

### Phase 7: UI Layer (FastAPI + React)
**GSD Command:** `/gsd-plan-phase 7` then `/gsd-execute-phase 7`
**Objective:** Build the dark-themed HUD backend and frontend visual display.
*   **Deliverables:**
    *   `ui/app.py`: FastAPI server with WebSockets for live token streaming and memory endpoints.
    *   `ui/frontend/`: Single-page React app with a status bar, animated waveform, chat window, and live system stats (CSS-styled, no separate CSS files).

### Phase 8: Boot Sequence & Main Loop
**GSD Command:** `/gsd-plan-phase 8` then `/gsd-execute-phase 8`
**Objective:** Create the central `main.py` entry point.
*   **Deliverables:**
    *   `main.py`: Sequential startup sequence (Logger → Hardware → Config → Memory → LLM → Agent → Voice → UI).
    *   Include a `--text-only` flag for testing, a graceful shutdown handler, and ASCII startup banners.

### Phase 9: Test Suite Validation
**GSD Command:** `/gsd-plan-phase 9` then `/gsd-execute-phase 9`
**Objective:** Guarantee system stability through comprehensive mocked tests.
*   **Deliverables:**
    *   Unit tests for `hardware`, `config`, `stt`, `tts`, `llm`, `agent`, `memory`, and `tools` using Pytest and heavy mocking.
    *   `tests/test_main_integration.py`: End-to-end text input to agent response pipeline.
    *(Note: Use `/gsd-verify-work 9` to automatically validate test coverage against criteria).*

### Phase 10: Final Polish & Documentation
**GSD Command:** `/gsd-plan-phase 10` then `/gsd-execute-phase 10`
**Objective:** Production-ready cleanup and tech debt resolution.
*   **Deliverables:**
    *   Update `README.md`, create `ARCHITECTURE.md` (with ASCII diagrams), and initialize `CHANGELOG.md`.
    *   Implement `validate_config()` in `core/config.py` for startup checks.
    *   Audit and inject error handlers across all modules (e.g., missing microphones, connection refusals, OAuth token expiries).

---

## GSD Workflow Best Practices for this Project
*   **Progress Tracking:** Run `/gsd-progress` regularly to monitor your position across the 10 JARVIS phases.
*   **Context Management:** If you need to stop midway through a complex phase like Phase 6 (Tools), use `/gsd-pause-work` to safely dump the context, and `/gsd-resume-work` when you return.
*   **Idea Capture:** If you discover a bug in the ReAct loop during execution but want to stay focused, use `/gsd-add-todo "Fix malformed output parsing in agent.py"` to push it to your backlog.
*   **Troubleshooting:** If the UI WebSocket fails to connect to FastAPI, spawn a specialized debug session using `/gsd-debug "WebSocket connection refused on port 3000"`.
*   **Milestone Completion:** Once Phase 10 is verified, run `/gsd-complete-milestone 1.0.0` to archive the phase files and prepare the environment for future fine-tuning updates.
```