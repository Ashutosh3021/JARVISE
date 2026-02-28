# Research Summary

**Project:** JARVIS — Windows AI Voice Assistant
**Date:** 2026-02-28
**Type:** Greenfield

---

## Key Findings

### Stack

**Core:** Python 3.11+ | Ollama (local LLM) | faster-whisper (STT) | Kokoro (TTS) | ChromaDB (memory)

The project uses a fully local stack with Ollama for LLM runtime, faster-whisper for speech-to-text, and Kokoro for text-to-speech. All processing happens on-device.

### Table Stakes

- Wake word detection ("JARVIS")
- Voice input/output (STT/TTS)
- Local LLM inference
- Basic conversation with session memory
- System info queries

### Differentiators

- Persistent memory via ChromaDB + MEMORY.md
- Tool execution (filesystem, browser, calendar)
- Privacy-first (100% local operation)
- VRAM-aware model selection

### Watch Out For

1. **Blocking audio** — Use async/await, run STT/TTS in executor
2. **Wake word false positives** — Add VAD and confirmation before listening
3. **Context overflow** — Implement sliding window for conversation history
4. **Memory persistence** — Handle Windows paths and file locking
5. **Hardware fallback** — Detect VRAM at startup, select appropriate model
6. **TTS overlap** — Implement audio queue, ignore input during speech

---

## Architecture

Pipeline: Wake Word → VAD → STT → ReAct Agent → LLM → TTS → Output

Components: voice/ (audio I/O), brain/ (LLM + reasoning), memory/ (ChromaDB + MEMORY.md), tools/ (execution), ui/ (FastAPI + React)

---

## Files

- `.planning/research/STACK.md` — Recommended stack with versions
- `.planning/research/FEATURES.md` — Feature categories and priorities
- `.planning/research/ARCHITECTURE.md` — System design and data flow
- `.planning/research/PITFALLS.md` — Common mistakes and prevention

---

*Synthesized: 2026-02-28*
