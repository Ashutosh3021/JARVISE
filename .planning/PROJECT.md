# JARVIS

## What This Is

A Windows desktop AI voice assistant powered by local LLMs. Listens for wake word "JARVIS", processes voice input, reasons using a ReAct loop, and responds via text-to-speech. Features persistent memory via ChromaDB vector store and human-readable MEMORY.md.

## Core Value

A privacy-focused, always-available AI assistant that runs entirely locally on Windows, understanding context through vector memory and executing tasks through integrated system tools.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Phase 1: Project Setup & Environment — scaffold, requirements.txt, .env.example
- [ ] Phase 2: Core Hardware Detection & Config — VRAM detection, config loader, logger
- [ ] Phase 3: Voice Pipeline — wake word, STT, TTS
- [ ] Phase 4: Brain Layer — LLM client, prompt builder, ReAct agent
- [ ] Phase 5: Memory System — ChromaDB, MEMORY.md, MemoryManager
- [ ] Phase 6: System Tool Integrations — search, browser, filesystem, calendar, email
- [ ] Phase 7: UI Layer — FastAPI backend, React frontend
- [ ] Phase 8: Boot Sequence & Main Loop — main.py entry point
- [ ] Phase 9: Test Suite Validation — unit tests, integration tests
- [ ] Phase 10: Final Polish & Documentation — README, ARCHITECTURE.md, error handlers

### Out of Scope

- Mobile apps — Windows desktop only for v1
- Cloud LLM APIs — fully local operation
- Real-time collaboration features — single user focus

## Context

- **OS:** Windows
- **Language:** Python 3.11+
- **Wake Word:** "JARVIS"
- **Agent Pattern:** ReAct loop (Reason → Act → Observe → Repeat)
- **Memory:** Vector Database (ChromaDB) + Human-readable core facts (MEMORY.md)

## Constraints

- **Tech Stack:** Python 3.11+, local LLM tools, STT/TTS engines, Langchain, Playwright, FastAPI
- **Privacy:** All data stays local, no cloud services
- **Hardware:** Auto-detect VRAM to select AI model tier (CPU, Low GPU, Mid GPU, High GPU)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Local-only LLM | Privacy-first, no API costs | — Pending |
| ChromaDB + MEMORY.md | Vector search + human-editable facts | — Pending |
| ReAct agent pattern | Proven for tool-calling agents | — Pending |
| FastAPI + React UI | WebSocket streaming, modern UI | — Pending |

---
*Last updated: 2026-02-28 after initialization*
