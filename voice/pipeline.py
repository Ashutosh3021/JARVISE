"""
JARVIS Voice Pipeline Module
Unified voice pipeline class orchestrating all voice components
"""

import numpy as np
from typing import Optional, Callable, Tuple
import threading
import time
from loguru import logger

from .keyboard_handler import KeyboardHandler
from .recorder import AudioRecorder
from .vad import VADWrapper
from .stt import STTEngine
from .tts import TTSEngine
from .audio_output import AudioOutput


class VoicePipeline:
    """
    Unified voice pipeline orchestrating all voice components.
    
    Flow:
    1. User presses space bar → start recording
    2. Audio is captured and filtered by VAD
    3. User releases space → stop recording
    4. Silence timeout (2-3s) → trigger transcription
    5. Audio sent to STT → text returned
    6. Text sent to brain via callback
    7. Brain response → TTS → AudioOutput → speakers
    """
    
    def __init__(self,
                 stt_model: str = "medium",
                 stt_device: str = "cuda",
                 tts_voice: str = "bm_lewis",
                 tts_language: str = "b",
                 silence_timeout: float = 2.5,
                 max_recording_duration: float = 30.0,
                 vad_mode: int = 3):
        """
        Initialize voice pipeline.
        
        Args:
            stt_model: Whisper model size
            stt_device: STT device (cuda or cpu)
            tts_voice: TTS voice ID
            tts_language: TTS language code
            silence_timeout: Seconds of silence before triggering transcription
            max_recording_duration: Maximum recording duration in seconds
            vad_mode: VAD aggressiveness mode (0-3)
        """
        self._silence_timeout = silence_timeout
        self._max_recording_duration = max_recording_duration
        
        # Callbacks
        self._on_transcription: Optional[Callable[[str, float], None]] = None
        self._on_recording_start: Optional[Callable] = None
        self._on_recording_stop: Optional[Callable] = None
        self._on_speech_start: Optional[Callable] = None
        self._on_speech_end: Optional[Callable] = None
        self._on_listening_start: Optional[Callable] = None
        self._on_listening_stop: Optional[Callable] = None
        
        # State
        self._is_active = False
        self._last_speech_time = 0
        self._silence_timer: Optional[threading.Timer] = None
        
        # Initialize components
        logger.info("Initializing voice pipeline components...")
        
        # Keyboard handler
        self._keyboard = KeyboardHandler(
            on_press_callback=self._on_space_press,
            on_release_callback=self._on_space_release
        )
        
        # Audio recorder
        self._recorder = AudioRecorder(max_duration=max_recording_duration)
        
        # VAD
        self._vad = VADWrapper(mode=vad_mode)
        
        # STT
        try:
            self._stt = STTEngine(model_size=stt_model, device=stt_device)
        except Exception as e:
            logger.warning(f"Failed to load STT with {stt_device}, falling back to CPU: {e}")
            self._stt = STTEngine(model_size=stt_model, device="cpu", compute_type="float32")
        
        # TTS
        try:
            self._tts = TTSEngine(voice=tts_voice, language_code=tts_language)
        except Exception as e:
            logger.warning(f"Failed to load TTS: {e}")
            self._tts = None
        
        # Audio output
        self._audio_output = AudioOutput(sample_rate=24000)
        
        logger.info("Voice pipeline initialized")
    
    def start(self):
        """Start the voice pipeline."""
        if self._is_active:
            logger.warning("Voice pipeline already active")
            return
        
        self._keyboard.start()
        self._is_active = True
        
        if self._on_listening_start:
            self._on_listening_start()
        
        logger.info("Voice pipeline started - press space to speak")
    
    def stop(self):
        """Stop the voice pipeline."""
        if not self._is_active:
            return
        
        self._keyboard.stop()
        self._recorder.stop()
        
        if self._silence_timer:
            self._silence_timer.cancel()
        
        self._is_active = False
        
        if self._on_listening_stop:
            self._on_listening_stop()
        
        logger.info("Voice pipeline stopped")
    
    def _on_space_press(self):
        """Handle space bar press."""
        logger.info("Recording started (space pressed)")
        
        if self._silence_timer:
            self._silence_timer.cancel()
        
        self._recorder.start()
        self._recorder.clear_buffer()
        
        if self._on_recording_start:
            self._on_recording_start()
    
    def _on_space_release(self):
        """Handle space bar release."""
        logger.info("Recording stopped (space released)")
        
        if self._on_recording_stop:
            self._on_recording_stop()
        
        # Start silence timeout
        self._start_silence_timer()
    
    def _start_silence_timer(self):
        """Start the silence timeout timer."""
        if self._silence_timer:
            self._silence_timer.cancel()
        
        self._silence_timer = threading.Timer(
            self._silence_timeout,
            self._process_transcription
        )
        self._silence_timer.start()
        logger.debug(f"Silence timeout started ({self._silence_timeout}s)")
    
    def _process_transcription(self):
        """Process recorded audio through STT."""
        logger.info("Processing transcription...")
        
        # Stop recording and get audio
        audio = self._recorder.stop()
        
        if len(audio) == 0:
            logger.info("No audio recorded")
            return
        
        # Check for speech using VAD
        audio_bytes = audio.tobytes()
        if not self._vad.is_speech(audio_bytes):
            logger.info("No speech detected by VAD")
            return
        
        # Transcribe
        try:
            text, confidence = self._stt.transcribe(audio, sample_rate=16000)
            
            if text and text.strip():
                logger.info(f"Transcribed: '{text}' (confidence: {confidence:.2f})")
                
                if self._on_transcription:
                    self._on_transcription(text, confidence)
            else:
                logger.info("Empty transcription")
                
        except Exception as e:
            logger.error(f"Transcription error: {e}")
    
    def speak(self, text: str, wait: bool = True):
        """
        Speak text through TTS.
        
        Args:
            text: Text to speak
            wait: If True, wait for speech to finish
        """
        if not self._tts:
            logger.warning("TTS not available")
            return
        
        try:
            audio = self._tts.speak(text)
            if len(audio) > 0:
                self._audio_output.play(audio, wait=wait)
        except Exception as e:
            logger.error(f"TTS error: {e}")
    
    def speak_async(self, text: str):
        """
        Speak text asynchronously (non-blocking).
        
        Args:
            text: Text to speak
        """
        thread = threading.Thread(target=self.speak, args=(text, False))
        thread.daemon = True
        thread.start()
    
    def stop_speaking(self):
        """Stop current TTS playback."""
        self._audio_output.stop()
    
    # Callback setters
    def on_transcription(self, callback: Callable[[str, float], None]):
        """Set callback for transcription results."""
        self._on_transcription = callback
    
    def on_recording_start(self, callback: Callable):
        """Set callback for recording start."""
        self._on_recording_start = callback
    
    def on_recording_stop(self, callback: Callable):
        """Set callback for recording stop."""
        self._on_recording_stop = callback
    
    def on_speech_start(self, callback: Callable):
        """Set callback for speech start detection."""
        self._on_speech_start = callback
    
    def on_speech_end(self, callback: Callable):
        """Set callback for speech end detection."""
        self._on_speech_end = callback
    
    def on_listening_start(self, callback: Callable):
        """Set callback for pipeline start."""
        self._on_listening_start = callback
    
    def on_listening_stop(self, callback: Callable):
        """Set callback for pipeline stop."""
        self._on_listening_stop = callback
    
    @property
    def is_active(self) -> bool:
        """Check if pipeline is active."""
        return self._is_active
    
    @property
    def stt(self) -> STTEngine:
        """Get STT engine."""
        return self._stt
    
    @property
    def tts(self) -> Optional[TTSEngine]:
        """Get TTS engine."""
        return self._tts
    
    @property
    def audio_output(self) -> AudioOutput:
        """Get audio output handler."""
        return self._audio_output


if __name__ == "__main__":
    # Test pipeline
    print("Initializing voice pipeline...")
    
    # Create pipeline with CPU fallback
    pipeline = VoicePipeline(
        stt_model="medium",
        stt_device="cpu",
        tts_voice="bm_lewis",
        tts_language="b"
    )
    
    print("Pipeline ready!")
    print("Press space to speak, release to transcribe")
    print("Press ESC to exit")
    
    # Set transcription callback
    pipeline.on_transcription(lambda text, conf: print(f"You said: {text}"))
    
    # Start pipeline
    pipeline.start()
    
    # Wait for exit
    import keyboard
    keyboard.wait('esc')
    
    pipeline.stop()
    print("Pipeline test complete")
