# Feature Research

**Domain:** Windows AI Voice Assistant
**Researched:** 2026-02-28
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Wake word detection | Core interaction model | MEDIUM | Must reliably detect "JARVIS" |
| Voice input (STT) | Primary input method | LOW | faster-whisper handles this |
| Voice output (TTS) | Primary output method | MEDIUM | Kokoro provides quality voices |
| Text chat interface | Fallback when voice fails | LOW | Debugging, noisy environments |
| Local LLM inference | Core intelligence | MEDIUM | Ollama handles this |
| Basic conversation | Core value proposition | MEDIUM | Remember context within session |
| System info queries | Immediate utility | LOW | Time, weather, hardware info |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Persistent memory | Remembers user across sessions | HIGH | ChromaDB + MEMORY.md |
| Tool execution | Actually performs tasks | HIGH | Filesystem, browser, calendar |
| Custom wake words | Personalization | LOW | pvporcupine supports custom |
| Multi-voice TTS | Personality options | MEDIUM | 31 Kokoro voices available |
| Local-only operation | Privacy assurance | LOW | No network required after setup |
| VRAM-aware model selection | Performance optimization | MEDIUM | Auto-detect hardware capability |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Real-time voice streaming | Natural conversation | High latency, complex buffering | Push-to-talk with buffering |
| Multi-user support | Family use case | Complexity explosion, privacy mixing | Single user v1 |
| Cloud fallback | Reliability | Violates privacy, defeats purpose | Robust local error handling |
| Continuous listening | Always-on assistant | Privacy concerns, resource drain | Wake |
| Plugin marketplace word activated | Extensibility | Security risks, maintenance burden | Future consideration |

## Feature Dependencies

```
[Wake Word Detection]
    └──requires──> [Voice Activity Detection]
                        └──requires──> [Speech-to-Text]
                                            └──requires──> [LLM Processing]
                                                                └──requires──> [Text-to-Speech]

[Memory System] ──enhances──> [LLM Processing]
[Tool System] ──enhances──> [LLM Processing]
```

### Dependency Notes

- **Wake word requires VAD:** Can't detect wake word reliably without voice activity detection to filter noise
- **STT requires VAD:** Need to know when speech starts/stops
- **LLM processing requires STT:** Input comes from transcription
- **TTS requires LLM:** Output goes to speech synthesis
- **Memory enhances LLM:** Vector store provides context for better responses
- **Tool system enhances LLM:** Enables actionable responses, not just text

## MVP Definition

### Launch With (v1)

- [ ] Wake word detection ("JARVIS") — core interaction model
- [ ] Speech-to-text — voice input capture
- [ ] Local LLM chat — core intelligence
- [ ] Text-to-speech — voice output
- [ ] Basic conversation memory — context within session
- [ ] System info queries — immediate utility

### Add After Validation (v1.x)

- [ ] Persistent memory (ChromaDB + MEMORY.md) — cross-session context
- [ ] Tool execution (files, browser) — actual task completion
- [ ] Custom wake word training — personalization
- [ ] Error recovery improvements — robustness

### Future Consideration (v2+)

- [ ] Multi-language support — broader audience
- [ ] Plugin system — extensibility
- [ ] Voice customization — personality
- [ ] Multi-user support — family use

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Wake word detection | HIGH | MEDIUM | P1 |
| STT (voice input) | HIGH | LOW | P1 |
| TTS (voice output) | HIGH | MEDIUM | P1 |
| Local LLM chat | HIGH | MEDIUM | P1 |
| Basic conversation | HIGH | MEDIUM | P1 |
| System info queries | HIGH | LOW | P1 |
| Persistent memory | MEDIUM | HIGH | P2 |
| Tool execution | MEDIUM | HIGH | P2 |
| Custom wake words | LOW | LOW | P3 |
| Multi-voice TTS | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Jarvis (OpenAI) | Samantha AI | Our Approach |
|---------|-----------------|-------------|---------------|
| Wake word | No (app-based) | Yes | JARVIS wake word |
| Local LLM | No (cloud) | Partial | Fully local with Ollama |
| Memory | Session only | Persistent | ChromaDB + MEMORY.md |
| Tool execution | Limited | Yes | File, browser, calendar |
| Privacy | Cloud-based | Mixed | 100% local |
| Windows focus | Cross-platform | Cross-platform | Windows-first |

## Sources

- InsiderLLM building guide (2026-02-11)
- SAM v2 GitHub repo (2025-10-30)
- Local voice AI stack guides (2026-02)
- OpenClaw comparison (2026-02-06)

---
*Feature research for: JARVIS Windows AI Voice Assistant*
*Researched: 2026-02-28*
