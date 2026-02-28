---
wave: 1
depends_on: []
files_modified:
  - voice/__init__.py
  - voice/pipeline.py
  - voice/recorder.py
  - voice/stt.py
  - voice/tts.py
  - voice/vad.py
  - voice/keyboard_handler.py
  - voice/audio_output.py
autonomous: true
requirements:
  - VP-01
  - VP-02
  - VP-03
  - VP-04
  - VP-05
  - VP-06
  - VP-07
---

## Plan: 03-voice-pipeline

**Goal:** Implement complete audio input/output pipeline with push-to-talk activation

**must_haves:**
1. Space bar press starts audio capture, release stops and triggers transcription
2. VAD filters silence and noise from audio before STT processing
3. faster-whisper transcribes audio to text with medium model
4. Kokoro TTS synthesizes text to audio with British male voice
5. Audio plays through speakers with interruption handling
6. VoicePipeline class unifies all components with clean API

**Verification:**
- [ ] Space bar activates/deactivates recording
- [ ] VAD rejects non-speech audio frames
- [ ] STT produces text output from audio input
- [ ] TTS produces audio from text input
- [ ] Audio plays through system speakers
- [ ] VoicePipeline orchestrates full input→output cycle

## Tasks

### Task 1: keyboard_handler.py - Space bar push-to-talk
**requirements:** [VP-01]
**description:** Implement keyboard handler for push-to-talk activation using space bar
**actions:**
- Create voice/keyboard_handler.py with keyboard library
- Implement on_press callback to start recording
- Implement on_release callback to stop recording and trigger transcription
- Add key validation (only space activates)
- Add to requirements.txt: keyboard>=0.13.0
**verify:**
<automated>python -c "from voice.keyboard_handler import KeyboardHandler; print('OK')"</automated>

### Task 2: vad.py - Voice Activity Detection
**requirements:** [VP-02]
**description:** Implement VAD wrapper using WebRTC VAD
**actions:**
- Create voice/vad.py with webrtcvad library
- Wrap Vad(3) for aggressive filtering mode
- Implement is_speech(audio_frame, sample_rate) method
- Support 16000 Hz sample rate
- Add to requirements.txt: webrtcvad>=2.0
**verify:**
<automated>python -c "from voice.vad import VADWrapper; print('OK')"</automated>

### Task 3: recorder.py - Audio recording with buffering
**requirements:** [VP-03]
**description:** Implement audio recorder with circular buffer for continuous capture
**actions:**
- Create voice/recorder.py with sounddevice
- Implement AudioRecorder class with start(), stop(), get_audio() methods
- Use 16000 Hz mono 16-bit PCM format
- Implement circular buffer for continuous recording
- Handle microphone device selection
- Add max duration limit (30 seconds)
- Add to requirements.txt: sounddevice>=0.4.0, numpy>=1.24.0
**verify:**
<automated>python -c "from voice.recorder import AudioRecorder; print('OK')"</automated>

### Task 4: stt.py - Speech-to-text transcription
**requirements:** [VP-04]
**description:** Implement STT wrapper using faster-whisper
**actions:**
- Create voice/stt.py with faster-whisper
- Implement STTEngine class with transcribe(audio_path) method
- Load "medium" model with CUDA support (float16)
- Handle language specification (English)
- Return transcribed text with confidence score
- Add to requirements.txt: faster-whisper>=1.0.0
**verify:**
<automated>python -c "from voice.stt import STTEngine; print('OK')"</automated>

### Task 5: tts.py - Text-to-speech synthesis
**requirements:** [VP-05]
**description:** Implement TTS wrapper using Kokoro
**actions:**
- Create voice/tts.py with kokoro-onnx
- Implement TTSEngine class with speak(text) method
- Use British English ('b') language code
- Select bm_lewis voice (modern British male)
- Return numpy audio array at 24kHz
- Add to requirements.txt: kokoro-onnx>=0.19.0, soundfile>=0.12.0
**verify:**
<automated>python -c "from voice.tts import TTSEngine; print('OK')"</automated>

### Task 6: audio_output.py - Speaker playback
**requirements:** [VP-06]
**description:** Implement audio output to speakers with interruption support
**actions:**
- Create voice/audio_output.py with sounddevice
- Implement AudioOutput class with play(), stop(), pause(), resume() methods
- Handle playback at 24kHz sample rate
- Implement interruption detection (user input while speaking)
- Queue multiple responses for sequential playback
**verify:**
<automated>python -c "from voice.audio_output import AudioOutput; print('OK')"</automated>

### Task 7: pipeline.py - VoicePipeline unified class
**requirements:** [VP-07]
**description:** Implement unified VoicePipeline class orchestrating all components
**actions:**
- Create voice/pipeline.py with VoicePipeline class
- Integrate keyboard_handler for activation
- Integrate recorder for audio capture
- Integrate vad for speech filtering
- Integrate stt for transcription
- Integrate tts for synthesis
- Integrate audio_output for playback
- Implement 2-3 second silence timeout after release
- Implement response queue for interruption handling
- Expose process_audio() method returning transcribed text
- Expose speak(text) method for TTS output
- Add on_transcription callback for brain layer integration
**verify:**
<automated>python -c "from voice.pipeline import VoicePipeline; print('OK')"</automated>

### Task 8: voice/__init__.py - Module exports
**requirements:** []
**description:** Export VoicePipeline and components
**actions:**
- Update voice/__init__.py with exports
- Export VoicePipeline, STTEngine, TTSEngine, AudioRecorder, VADWrapper
