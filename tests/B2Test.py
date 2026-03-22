"""
B-2 UAT Test Suite
Run from project root: python test_b2_uat.py
"""

import sys
import os
import numpy as np

# Add project root to path so 'voice', 'brain', etc. imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []

def report(name, passed, detail=""):
    status = PASS if passed else FAIL
    results.append((name, passed))
    print(f"{status} | {name}")
    if detail:
        print(f"       {detail}")

print("\n" + "="*55)
print("  B-2 UAT — Voice Pipeline")
print("="*55 + "\n")

# ─────────────────────────────────────────────
# BUG-008 — KPipeline constructor
# ─────────────────────────────────────────────
print("── BUG-008: TTS Constructor ──")
try:
    from voice.tts import TTSEngine
    t = TTSEngine()
    audio = t.speak("hello jarvis")
    passed = len(audio) > 0
    report("BUG-008 KPipeline no repo_id", passed,
           f"Generated {len(audio)} samples")
except TypeError as e:
    report("BUG-008 KPipeline no repo_id", False, f"TypeError: {e}")
except Exception as e:
    report("BUG-008 KPipeline no repo_id", False, f"Error: {e}")

# ─────────────────────────────────────────────
# BUG-037 — librosa speed adjustment
# ─────────────────────────────────────────────
print("\n── BUG-037: TTS Speed ──")
try:
    from voice.tts import TTSEngine
    t1 = TTSEngine(speed=1.0)
    t2 = TTSEngine(speed=1.5)
    a1 = t1.speak("test speed adjustment")
    a2 = t2.speak("test speed adjustment")
    ratio = len(a2) / len(a1) if len(a1) > 0 else 1.0
    # 1.5x speed = ~0.67x samples (within 10% tolerance)
    passed = 0.57 <= ratio <= 0.77
    report("BUG-037 librosa speed ratio", passed,
           f"1.0x={len(a1)} samples | 1.5x={len(a2)} samples | ratio={ratio:.2f} (expect ~0.67)")
except Exception as e:
    report("BUG-037 librosa speed ratio", False, f"Error: {e}")

# ─────────────────────────────────────────────
# BUG-007 — VAD framing
# ─────────────────────────────────────────────
print("\n── BUG-007: VAD Framing ──")
try:
    from voice.pipeline import VoicePipeline
    vp = VoicePipeline()

    # Check method exists
    has_method = hasattr(vp, '_has_speech')
    report("BUG-007 _has_speech method exists", has_method)

    if has_method:
        # Silence → should be False
        silence = np.zeros(16000, dtype=np.float32)
        silence_result = vp._has_speech(silence)
        report("BUG-007 silence = no speech", not silence_result,
               f"_has_speech(silence) = {silence_result} (expect False)")

        # Tone → should be True
        tone = (np.sin(2 * np.pi * 440 * np.linspace(0, 1, 16000))).astype(np.float32)
        tone_result = vp._has_speech(tone)
        report("BUG-007 tone = speech detected", tone_result,
               f"_has_speech(tone) = {tone_result} (expect True)")

except Exception as e:
    report("BUG-007 VAD framing", False, f"Error: {e}")

# ─────────────────────────────────────────────
# BUG-009 — STT single normalization
# ─────────────────────────────────────────────
print("\n── BUG-009: STT Normalization ──")
try:
    # Simulate normalization logic without loading full model
    # int16 at 50% amplitude → should become 0.5 float, never > 1.0
    audio_int16 = np.full(16000, 16384, dtype=np.int16)

    if audio_int16.dtype == np.int16:
        audio_f = audio_int16.astype(np.float32) / 32768.0
    elif audio_int16.dtype != np.float32:
        audio_f = audio_int16.astype(np.float32)
    else:
        audio_f = audio_int16

    audio_clipped = np.clip(audio_f, -1.0, 1.0)
    max_val = float(audio_clipped.max())
    expected = 16384 / 32768.0  # 0.5

    passed = abs(max_val - expected) < 0.001 and max_val <= 1.0
    report("BUG-009 normalization single-pass", passed,
           f"max={max_val:.4f} (expect {expected:.4f}, must be ≤ 1.0)")

    # Now verify actual stt.py doesn't double-divide
    import inspect
    from voice import stt
    src = inspect.getsource(stt.STTEngine.transcribe)
    divide_count = src.count("/ 32768")
    passed2 = divide_count <= 1
    report("BUG-009 no double division in source", passed2,
           f"Found '/ 32768' {divide_count} time(s) in transcribe() (expect ≤ 1)")

except Exception as e:
    report("BUG-009 normalization", False, f"Error: {e}")

# ─────────────────────────────────────────────
# BUG-040 — CUDA detection
# ─────────────────────────────────────────────
print("\n── BUG-040: CUDA Detection ──")
try:
    import torch
    cuda_available = torch.cuda.is_available()
    expected_device = "cuda" if cuda_available else "cpu"

    import inspect
    from voice import pipeline
    src = inspect.getsource(pipeline.VoicePipeline.__init__)
    has_cuda_check = "cuda.is_available" in src or "cuda_available" in src
    report("BUG-040 CUDA check before STT init", has_cuda_check,
           f"torch.cuda.is_available()={cuda_available} → expects device='{expected_device}'")

except Exception as e:
    report("BUG-040 CUDA detection", False, f"Error: {e}")

# ─────────────────────────────────────────────
# BUG-002 — Callback wiring
# ─────────────────────────────────────────────
print("\n── BUG-002: Callback Wiring ──")
try:
    checks = {
        "handle_transcription defined": "handle_transcription",
        "on_transcription called":      "on_transcription",
        "voice_pipeline.start called":  "voice_pipeline.start",
    }
    for label, term in checks.items():
        # Use Python file search (Windows has no grep.exe by default)
        found = False
        detail = "NOT FOUND in main.py"
        try:
            main_path = os.path.join(PROJECT_ROOT, "main.py")
            with open(main_path, "r", encoding="utf-8") as f:
                for lineno, line in enumerate(f, 1):
                    if term in line:
                        found = True
                        detail = f"line {lineno}: {line.strip()}"
                        break
        except Exception:
            pass
        report(f"BUG-002 {label}", found, detail)

except Exception as e:
    report("BUG-002 callback wiring", False, f"Error: {e}")

# ─────────────────────────────────────────────
# END-TO-END SMOKE TEST
# ─────────────────────────────────────────────
print("\n── E2E: Voice Loop Smoke Test ──")
try:
    from brain.agent import ReActAgent
    from brain.tools import create_tools_registry
    from voice.tts import TTSEngine

    agent = ReActAgent(tool_registry=create_tools_registry())
    tts = TTSEngine()

    text = "what time is it"
    response = agent.run(text)
    passed_agent = isinstance(response, str) and len(response) > 0
    report("E2E agent responds to text", passed_agent,
           f"Response: '{response[:80]}...' " if len(response) > 80 else f"Response: '{response}'")

    audio = tts.speak(response)
    passed_tts = len(audio) > 0
    report("E2E TTS speaks agent response", passed_tts,
           f"Audio: {len(audio)} samples ({len(audio)/24000:.2f}s)")

except Exception as e:
    report("E2E voice loop", False, f"Error: {e}")

# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────
print("\n" + "="*55)
print("  RESULTS")
print("="*55)
passed = sum(1 for _, p in results if p)
total = len(results)
for name, p in results:
    print(f"  {'✅' if p else '❌'} {name}")
print(f"\n  {passed}/{total} passed")
if passed == total:
    print("  🔥 B-2 UAT COMPLETE — approved to close")
else:
    print("  ⚠️  Fix failing tests before closing B-2")
print("="*55 + "\n")
sys.exit(0 if passed == total else 1)