# Phase 3: Voice Pipeline - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete audio input/output pipeline with wake word detection. Users press space bar to activate listening, speech is transcribed, processed by AI, and spoken back via TTS. This phase covers the voice interaction loop only — integration with the brain/agent happens in later phases.

</domain>

<decisions>
## Implementation Decisions

### Wake Activation
- **Push-to-talk via space bar** — User holds space bar to activate listening
- Space bar triggers capture, release stops capture and begins transcription
- This approach aligns with privacy-focused core value (not always listening)

### VAD Sensitivity
- **Less false triggers** — Aggressive filtering to avoid accidental activations
- Prioritize accuracy over catching every whisper
- Reduces background noise false positives

### STT Model Size
- **Medium model** — Balance between speed and accuracy
- Larger than base but still runs locally efficiently

### TTS Voice
- **Male voice with natural British accent**
- From Kokoro's 31 available voices, select a natural-sounding British male voice
- Voice should sound professional and clear

### Audio Interruption
- **Queue response** — When user speaks while JARVIS is talking:
  - JARVIS pauses current response
  - Analyzes new input for relevance to active discussion
  - If relevant, continues/resumes with new context
  - If not relevant, completes original response then processes new command
- This enables natural conversation flow without losing context

### Silence Timeout
- **2-3 seconds** — After user stops speaking:
  - If no new speech detected within timeout
  - Automatically begin transcription processing
  - Prevents hanging indefinitely waiting for more input

### Claude's Discretion
- Exact VAD threshold numbers
- Audio buffer size and chunking
- How to visually indicate "listening" state in UI
- Error handling for microphone access denied

</decisions>

<specifics>
## Specific Ideas

- Space bar activation — familiar keyboard interaction
- "Queue response" behavior should feel like a natural conversation partner
- British male voice — professional, clear, not robotic

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `core/config.py` — Already has voice config fields (wake_word, whisper_model, kokoro_voice, tts_speed)
- `core/logger.py` — Can be used for voice pipeline logging

### Established Patterns
- Phase 2 established: configuration via pydantic-settings, logging via loguru
- No existing voice code yet — this is first voice implementation

### Integration Points
- Voice pipeline will integrate with:
  - Brain layer (Phase 4) — for text input/output
  - UI layer (Phase 7) — for status indicators
  - Main loop (Phase 8) — for startup sequence

</code_context>

<deferred>
## Deferred Ideas

- Always-listening wake word mode — could be added as future option (different phase)
- Custom wake word beyond "JARVIS" — out of scope for v1

</deferred>

---

*Phase: 03-voice-pipeline*
*Context gathered: 2026-02-28*
