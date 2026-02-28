# Phase 3: Voice Pipeline - Research

**Phase:** 03-voice-pipeline  
**Purpose:** Plan implementation of complete audio input/output pipeline with push-to-talk activation

---

## Research Question

**What do I need to know to PLAN this phase well?**

---

## Technology Options

### 1. Push-to-Talk (Space Bar Activation)

| Library | Pros | Cons |
|---------|------|------|
| **keyboard** | Pure Python, zero deps, works globally, supports press/release detection | Requires admin on Linux |
| **pyHook3** | Windows-specific, mature | Python 2/3.5 only, unmaintained |

**Recommendation:** Use `keyboard` library (`pip install keyboard`)

```python
import keyboard

def on_press(key):
    if key == 'space':
        start_listening()

def on_release(key):
    if key == 'space':
        stop_listening()

keyboard.on_press(on_press)
keyboard.on_release(on_release)
```

---

### 2. Voice Activity Detection (VAD)

| Library | Quality | Speed | Windows Support |
|---------|---------|-------|-----------------|
| **WebRTC VAD** | Good | Very Fast | ✅ Binary wheels |
| **Silero VAD** | Excellent | Fast | ✅ ONNX runtime |
| **TEN VAD** | Excellent | Low latency | ✅ |

**User Decision:** Aggressive filtering (less false triggers)  
**Recommendation:** WebRTC VAD with mode 3 (most aggressive)

```python
import webrtcvad

vad = webrtcvad.Vad(3)  # Mode 3 = most aggressive
# Accepts 16-bit mono PCM at 8000, 16000, 32000, or 48000 Hz
is_speech = vad.is_speech(audio_frame, sample_rate)
```

---

### 3. Speech-to-Text (STT)

| Model | Size | Accuracy | Speed |
|-------|------|----------|-------|
| tiny | 39 MB | Basic | Fastest |
| base | 74 MB | Practical | Fast |
| **small** | 244 MB | Good | Moderate |
| **medium** | 1.5 GB | Very Good | Slower |
| large-v3 | 3.1 GB | Excellent | Slow |

**User Decision:** Medium model (balance of speed and accuracy)  
**Recommendation:** faster-whisper with "medium" model

```python
from faster_whisper import WhisperModel

model = WhisperModel("medium", device="cuda", compute_type="float16")
segments, info = model.transcribe(audio_path, language="en")
for segment in segments:
    print(segment.text)
```

**Installation:** `pip install faster-whisper`  
**Note:** Does NOT require FFmpeg (uses Python audio decoding)

---

### 4. Text-to-Speech (TTS)

**Library:** Kokoro-82M (82M parameters, Apache licensed)

#### Available British Male Voices

| Voice ID | Description |
|----------|-------------|
| **bm_daniel** | Polished and professional |
| **bm_fable** | Storytelling and engaging |
| **bm_george** | Classic British accent |
| **bm_lewis** | Modern British accent |

**User Decision:** Male voice with natural British accent  
**Recommendation:** `bm_lewis` or `bm_george`

#### Installation Options

```bash
# Option 1: kokoro-onnx (recommended for Windows)
pip install kokoro-onnx soundfile

# Option 2: kokoro package
pip install kokoro soundfile
```

**Language Code:** `'b'` (British English)

```python
from kokoro import KPipeline

pipeline = KPipeline(lang_code='b')
text = "Hello, I am JARVIS."
audios = [audio for _, _, audio in pipeline(text, voice='bm_lewis')]
# audios contains numpy arrays at 24kHz
```

---

### 5. Audio Recording

| Library | Pros | Cons |
|---------|------|------|
| **sounddevice** | NumPy integration, well-maintained | Requires PortAudio |
| **pyaudio** | Widely used, many examples | Windows wheels sometimes problematic |

**Recommendation:** sounddevice (`pip install sounddevice soundfile numpy`)

```python
import sounddevice as sd
import numpy as np

# Query devices
devices = sd.query_devices()
print(devices)

# Record audio
recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1)
sd.wait()
```

**Windows Requirement:** Requires [PortAudio](http://portaudio.com/download.html) (included in many installations)

---

### 6. Audio Output (Playback)

| Library | Use Case |
|---------|----------|
| **sounddevice** | Play numpy arrays directly |
| **winsound** | Built-in Windows, simple WAV playback |
| **simpleaudio** | Cross-platform WAV playback |

**Recommendation:** sounddevice (consistent with input)

```python
import sounddevice as sd

# Play numpy array
sd.play(audio_array, samplerate=24000)
sd.wait()  # Wait until playback finishes
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     VoicePipeline                           │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐ │
│  │ Keyboard │──▶│  VAD     │──▶│  STT     │──▶│  TTS     │ │
│  │ Handler  │   │ Filter   │   │ (Whisper)│   │ (Kokoro) │ │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘ │
│       │             │              │              │        │
│       ▼             ▼              ▼              ▼        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   Audio I/O                          │  │
│  │  ┌─────────────┐         ┌─────────────────┐        │  │
│  │  │ Microphone  │         │    Speaker      │        │  │
│  │  │ (Input)     │         │    (Output)     │        │  │
│  │  └─────────────┘         └─────────────────┘        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Implementation Decisions

### Audio Format

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Sample Rate | 16000 Hz | WebRTC VAD requirement, efficient |
| Channels | 1 (Mono) | VAD/STT require mono |
| Format | 16-bit PCM | Standard for VAD |
| Chunk Size | 320-480 samples (20-30ms) | VAD frame compatibility |

### Silence Timeout Behavior

1. User presses space → Start recording
2. User releases space → Begin silence detection
3. Monitor audio for 2-3 seconds of silence
4. If silence detected → Process transcription
5. If user speaks again → Cancel timeout, extend recording

### Audio Interruption Strategy

When user speaks while JARVIS is talking:
1. Pause TTS playback immediately
2. Queue the remaining TTS response
3. Capture new user input
4. Analyze relevance (simple keyword matching or defer to brain layer)
5. Either resume original or process new command

---

## Dependencies

```txt
# Core voice dependencies
faster-whisper>=1.0.0
kokoro-onnx>=0.19.0
sounddevice>=0.4.0
soundfile>=0.12.0
numpy>=1.24.0

# VAD (choose one)
webrtcvad>=2.0  # Simple, fast
# OR
silero-vad-lite>=1.0  # Higher quality

# Keyboard handling
keyboard>=0.13.0
```

---

## File Structure

```
voice/
├── __init__.py
├── pipeline.py          # VoicePipeline unified class
├── recorder.py         # Audio recording with buffering
├── stt.py              # faster-whisper wrapper
├── tts.py              # Kokoro TTS wrapper
├── vad.py              # VAD wrapper
├── keyboard_handler.py # Space bar push-to-talk
└── audio_output.py     # Speaker playback
```

---

## Requirement Mapping

| Req ID | Description | Implementation |
|--------|-------------|----------------|
| VP-01 | Wake word detection | Space bar trigger (push-to-talk) |
| VP-02 | VAD for speech filtering | WebRTC VAD mode 3 |
| VP-03 | Audio recorder with buffering | sounddevice with circular buffer |
| VP-04 | STT transcription | faster-whisper "medium" |
| VP-05 | TTS synthesis | Kokoro 'b' language, bm_lewis voice |
| VP-06 | Audio output to speakers | sounddevice playback |
| VP-07 | VoicePipeline unified class | Orchestrates all components |

---

## Edge Cases

1. **Microphone access denied** → Log error, fallback to text-only mode
2. **No audio input device** → Detect at startup, warn user
3. **Very long speech** → Buffer limit with max duration
4. **TTS interruption** → Track playback position for resume
5. **Space bar held too long** → Max recording duration (30s)
6. **Empty transcription** → Skip processing, don't trigger brain

---

## Testing Considerations

1. **Unit tests:** STT module, TTS module (mock audio I/O)
2. **Integration tests:** Full pipeline with real audio
3. **Mocking:** Use ` unittest.mock` for hardware I/O
4. **Hardware:** Test with different microphones

---

## Resources

- faster-whisper: https://github.com/SYSTRAN/faster-whisper
- Kokoro: https://github.com/hexgrad/kokoro-82M
- WebRTC VAD: https://github.com/wiseman/py-webrtcvad
- sounddevice: https://python-sounddevice.readthedocs.io
- keyboard: https://github.com/boppreh/keyboard
