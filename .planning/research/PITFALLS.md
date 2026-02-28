# Pitfalls Research

**Domain:** Windows AI Voice Assistant
**Researched:** 2026-02-28
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Blocking Audio Processing

**What goes wrong:** Application freezes during STT/TTS processing

**Why it happens:** Running synchronous audio operations in main thread

**How to avoid:** Use async/await with run_in_executor for all blocking audio operations

**Warning signs:** UI becomes unresponsive during transcription, TTS takes too long

**Phase to address:** Phase 3 (Voice Pipeline) — design for async from start

---

### Pitfall 2: No Wake Word False Positive Handling

**What goes wrong:** Assistant activates on TV, music, or random sounds

**Why it happens:** Default wake word sensitivity too high, no environmental filtering

**How to avoid:** Implement VAD before wake word, add confirmation beep before listening

**Warning signs:** Assistant randomly activates, responds to conversations on TV

**Phase to address:** Phase 3 (Voice Pipeline) — add VAD and confirmation

---

### Pitfall 3: Context Window Overflow

**What goes wrong:** LLM produces garbage when conversation exceeds context limit

**Why it happens:** Sending entire conversation history without truncation

**How to avoid:** Implement sliding window for conversation history, summarize old interactions

**Warning signs:** LLM starts producing incoherent responses after ~30+ messages

**Phase to address:** Phase 4 (Brain Layer) — design context management

---

### Pitfall 4: Memory System Not Working in Production

**What goes wrong:** ChromaDB works in dev but fails or is slow in production

**Why it happens:** Not handling Windows path issues, file locking, or persistence

**How to avoid:** Test persistence path, handle file locks, implement retry logic

**Warning signs:** Works in testing, fails after restart, slow queries

**Phase to address:** Phase 5 (Memory System) — production-harden persistence

---

### Pitfall 5: No Hardware Fallback

**What goes wrong:** Assistant fails completely on systems without expected GPU

**Why it happens:** Hardcoded GPU-only model selection

**How to avoid:** Implement hardware detection at startup, select appropriate models

**Warning signs:** Fails on laptops without dedicated GPU

**Phase to address:** Phase 2 (Core Hardware Detection) — add VRAM detection and fallback models

---

### Pitfall 6: TTS Cuts Off or Overlaps

**What goes wrong:** Audio output is clipped or overlaps with next input

**Why it happens:** Not handling audio queue, no buffering between TTS and input

**How to avoid:** Implement audio queue with proper timing, ignore input during TTS

**Warning signs:** Assistant talks over user, responses get cut off

**Phase to address:** Phase 3 (Voice Pipeline) — implement audio queue management

---

### Pitfall 7: Tool Execution Without Guardrails

**What goes wrong:** LLM executes dangerous commands (delete files, send emails)

**Why it happens:** No sandboxing, unbounded tool permissions

**How to avoid:** Implement permission system, confirm before destructive actions, log all actions

**Warning signs:** Unexpected file operations, strange emails sent

**Phase to address:** Phase 6 (System Tool Integrations) — add safety layers

---

### Pitfall 8: Latency Makes Assistant Unusable

**What goes wrong:** 5+ second response time breaks conversation flow

**Why it happens:** Large models, no streaming, no feedback during processing

**How to avoid:** Stream responses, show "thinking" state, use smaller models for speed

**Warning signs:** Conversations feel robotic, long pauses

**Phase to address:** Phase 4 (Brain Layer) — optimize for latency

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip VRAM detection | Faster to build | Fails on different hardware | Never |
| Hardcode single LLM model | Simple code | Can't adapt to hardware | Only for MVP demo |
| In-memory only ChromaDB | Easier testing | Lose memory on restart | Only during development |
| No error recovery | Move faster | Complete failure on errors | Only for initial prototype |
| Blocking audio calls | Simpler code | Freezes UI | Never |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Ollama | Forgetting to start ollama serve | Check running before queries, auto-start if needed |
| faster-whisper | Loading model every request | Load once at startup, keep in memory |
| Kokoro | No GPU handling | Check CUDA availability, fall back to CPU |
| ChromaDB | Path with spaces on Windows | Use pathlib, quote paths |
| Playwright | Not installing browsers | Run playwright install chromium |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Loading STT model per request | 10s+ latency per request | Load model once at startup | Every request |
| Large context without limits | OOM errors, slow inference | Implement context window management | Long conversations |
| No audio buffering | TTS overlaps with input | Use audio queue | Continuous use |
| Synchronous file I/O in memory ops | System freezes | Async file operations | Memory save/load |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Unbounded file system access | Data loss, malware execution | Restrict to project directory, confirm destructive ops |
| No input sanitization | Prompt injection | Sanitize user input before LLM |
| Logging sensitive data | Privacy leak | Filter passwords, personal info from logs |
| No rate limiting | Resource exhaustion | Implement per-user rate limits |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No feedback during processing | User thinks it froze | Show "listening", "thinking", "speaking" states |
| Wake word too sensitive | Random activations | Adjust threshold, require push-to-talk option |
| No text fallback | Can't use when audio fails | Always allow text input as backup |
| Continuous listening | Privacy concerns | Only listen after wake word |

## "Looks Done But Isn't" Checklist

- [ ] **Wake word:** Often missing — verify it works with background noise
- [ ] **Memory:** Often missing — verify persistence after restart
- [ ] **Error handling:** Often missing — verify graceful degradation on failures
- [ ] **Latency:** Often hidden in demo — measure real-world response times
- [ ] **Audio buffer:** Often missing — verify no overlap between TTS and input

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Model loading failure | LOW | Log error, fall back to smaller model |
| Audio device unavailable | MEDIUM | List available devices, prompt user |
| Ollama not running | LOW | Auto-start ollama serve |
| ChromaDB corruption | MEDIUM | Delete and recreate collection |
| TTS failure | LOW | Fall back to text-only mode |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Blocking audio | Phase 3 (Voice Pipeline) | Test with slow network, verify UI responsive |
| Wake word false positives | Phase 3 (Voice Pipeline) | Test with TV, music playing |
| Context overflow | Phase 4 (Brain Layer) | Test with long conversations |
| Memory not persistent | Phase 5 (Memory System) | Restart app, verify memory persists |
| No hardware fallback | Phase 2 (Hardware Detection) | Test on different machines |
| TTS overlaps | Phase 3 (Voice Pipeline) | Speak while it's talking |
| No tool guardrails | Phase 6 (Tool Integrations) | Try destructive commands |
| Latency | Phase 4 (Brain Layer) | Measure E2E response time |

## Sources

- 10 Lessons Learned Building2025-10-30)
- Common Mistakes in Voice AI Agents ( AI Voice Assistants (2025-07-30)
- Voice AI Project Problems (10Clouds, 2025-12)
- Production Voice AI Failures (Medium, 2025-09)

---
*Pitfalls research for: JARVIS Windows AI Voice Assistant*
*Researched: 2026-02-28*
