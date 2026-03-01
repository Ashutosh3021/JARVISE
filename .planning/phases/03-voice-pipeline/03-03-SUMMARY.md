---
phase: 03-voice-pipeline
plan: 03
subsystem: voice
tags: [stt, tts, vad, faster-whisper, kokoro, push-to-talk]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: Core logging and config
  - phase: 02-core-hardware
    provides: Hardware detection utilities
provides:
  - VoicePipeline unified class for voice input/output
  - Space bar push-to-talk activation
  - VAD speech filtering
  - STT transcription with faster-whisper
  - TTS synthesis with Kokoro
  - Audio playback with interruption handling
affects: [brain-layer, ui-layer, boot-sequence]

# Tech tracking
tech-stack:
  added: [keyboard, webrtcvad, faster-whisper, kokoro-onnx, sounddevice, soundfile]
  patterns: [push-to-talk, VAD filtering, silence timeout, audio queuing]

key-files:
  created: [voice/__init__.py, voice/pipeline.py, voice/keyboard_handler.py, voice/vad.py, voice/recorder.py, voice/stt.py, voice/tts.py, voice/audio_output.py]
  modified: [requirements.txt]

key-decisions:
  - "Push-to-talk via space bar for privacy (not always listening)"
  - "WebRTC VAD with energy-based fallback for compatibility"
  - "Kokoro TTS with British male voice (bm_lewis)"
  - "2.5 second silence timeout before transcription"

patterns-established:
  - "Component-based voice pipeline with lazy loading"
  - "Silent fallback for optional dependencies"

requirements-completed: [VP-01, VP-02, VP-03, VP-04, VP-05, VP-06, VP-07]

# Metrics
duration: 25min
completed: 2026-03-01T13:05:00Z
---

# Phase 3: Voice Pipeline Summary

**Complete audio input/output pipeline with push-to-talk activation using faster-whisper and Kokoro TTS**

## Performance

- **Duration:** 25 min
- **Started:** 2026-03-01T12:40:00Z
- **Completed:** 2026-03-01T13:05:00Z
- **Tasks:** 8
- **Files modified:** 9

## Accomplishments
- Space bar push-to-talk keyboard handler
- Voice Activity Detection with WebRTC + energy fallback
- Audio recorder with circular buffer
- Speech-to-text with faster-whisper medium model
- Text-to-speech with Kokoro British male voice
- Audio output with interruption handling
- Unified VoicePipeline class orchestrating all components

## Task Commits

Each task was committed atomically:

1. **Task 1: keyboard_handler.py** - `3cb1788` (feat)
2. **Task 2: vad.py** - `f6c8bf7` (feat)
3. **Task 3: recorder.py** - `a66e865` (feat)
4. **Task 4: stt.py** - `8ed8b5d` (feat)
5. **Task 5: tts.py** - `4e193ab` (feat)
6. **Task 6: audio_output.py** - `f97bf40` (feat)
7. **Task 7: pipeline.py** - `3d12ea4` (feat)
8. **Task 8: voice/__init__.py** - `519368f` (feat)

**Plan metadata:** `519368f` (docs: complete plan)

## Files Created/Modified
- `voice/__init__.py` - Module exports with lazy loading
- `voice/pipeline.py` - VoicePipeline unified class
- `voice/keyboard_handler.py` - Space bar push-to-talk
- `voice/vad.py` - VAD with WebRTC + fallback
- `voice/recorder.py` - Audio recording with buffering
- `voice/stt.py` - faster-whisper STT wrapper
- `voice/tts.py` - Kokoro TTS wrapper
- `voice/audio_output.py` - Speaker playback
- `requirements.txt` - Added voice dependencies

## Decisions Made
- Push-to-talk via space bar aligns with privacy-focused core value
- WebRTC VAD with energy-based fallback for Windows compatibility
- Kokoro TTS with British male voice (bm_lewis) for natural sound
- 2.5 second silence timeout balances responsiveness vs false triggers

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] VAD library not installable**
- **Found during:** Task 2 (VAD implementation)
- **Issue:** webrtcvad requires C++ build tools not available on system
- **Fix:** Added energy-based VAD fallback that activates when WebRTC unavailable
- **Files modified:** voice/vad.py
- **Verification:** VAD module imports and initializes correctly
- **Committed in:** f6c8bf7 (Task 2 commit)

**2. [Rule 3 - Blocking] Circular import at module load**
- **Found during:** Task 8 (Module exports)
- **Issue:** voice/__init__.py importing pipeline at load time caused circular imports
- **Fix:** Implemented lazy loading with __getattr__ for deferred imports
- **Files modified:** voice/__init__.py
- **Verification:** All voice modules import correctly
- **Committed in:** 519368f (Task 8 commit)

---

**Total deviations:** 2 auto-fixed (both blocking)
**Impact on plan:** Both fixes essential for module to work on Windows without build tools. No scope creep.

## Issues Encountered
- None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Voice pipeline complete and ready for integration with brain layer (Phase 4)
- STT and TTS engines initialized with CPU fallback
- VoicePipeline exposes on_transcription callback for brain integration

---
*Phase: 03-voice-pipeline*
*Completed: 2026-03-01*
