"""
JARVIS VAD (Voice Activity Detection) Module
Provides speech detection using WebRTC VAD or fallback energy-based detection
"""

try:
    import webrtcvad
    HAS_WEBRTC = True
except ImportError:
    HAS_WEBRTC = False

import numpy as np
from loguru import logger


class VADWrapper:
    """
    Wrapper around WebRTC VAD for voice activity detection.
    Uses mode 3 (most aggressive) to reduce false positives.
    Falls back to energy-based detection if webrtcvad is not available.
    """
    
    def __init__(self, mode: int = 3, sample_rate: int = 16000, energy_threshold: float = 0.02):
        """
        Initialize VAD wrapper.
        
        Args:
            mode: Aggressiveness mode (0-3), 3 is most aggressive (only for webrtcvad)
            sample_rate: Audio sample rate (8000, 16000, 32000, or 48000)
            energy_threshold: Energy threshold for fallback VAD
        """
        self._sample_rate = sample_rate
        self._mode = mode
        self._energy_threshold = energy_threshold
        self._frame_duration = 30  # ms
        self._vad = None
        
        if HAS_WEBRTC:
            if mode not in [0, 1, 2, 3]:
                raise ValueError("Mode must be 0, 1, 2, or 3")
            if sample_rate not in [8000, 16000, 32000, 48000]:
                raise ValueError("Sample rate must be 8000, 16000, 32000, or 48000")
            self._vad = webrtcvad.Vad(mode)
            logger.info(f"VADWrapper initialized with WebRTC mode={mode}, sample_rate={sample_rate}")
        else:
            logger.warning("WebRTC VAD not available, using energy-based fallback")
            logger.info(f"VADWrapper initialized with energy-based detection, threshold={energy_threshold}")
    
    def is_speech(self, audio_frame) -> bool:
        """
        Check if audio frame contains speech.
        
        Args:
            audio_frame: Raw audio bytes (16-bit PCM mono) or numpy array
            
        Returns:
            True if speech is detected, False otherwise
        """
        if self._vad is not None:
            # Use WebRTC VAD
            try:
                if hasattr(audio_frame, 'tobytes'):
                    audio_frame = audio_frame.tobytes()
                return self._vad.is_speech(audio_frame, self._sample_rate)
            except Exception as e:
                logger.error(f"VAD error: {e}")
                return False
        else:
            # Use energy-based fallback
            return self._is_speech_energy(audio_frame)
    
    def _is_speech_energy(self, audio_frame) -> bool:
        """Energy-based voice activity detection fallback."""
        try:
            if hasattr(audio_frame, 'tobytes'):
                audio = audio_frame
            elif isinstance(audio_frame, bytes):
                audio = np.frombuffer(audio_frame, dtype=np.int16)
            else:
                audio = audio_frame
            
            # Calculate RMS energy
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32) / 32768.0
            
            energy = np.sqrt(np.mean(audio ** 2))
            return energy > self._energy_threshold
        except Exception:
            return False
    
    @property
    def sample_rate(self) -> int:
        """Get the sample rate."""
        return self._sample_rate
    
    @property
    def mode(self) -> int:
        """Get the VAD mode."""
        return self._mode
    
    def set_mode(self, mode: int):
        """
        Change VAD aggressiveness mode.
        
        Args:
            mode: New mode (0-3)
        """
        if mode not in [0, 1, 2, 3]:
            raise ValueError("Mode must be 0, 1, 2, or 3")
        self._mode = mode
        if self._vad is not None:
            self._vad.set_mode(mode)
        logger.info(f"VAD mode changed to {mode}")


if __name__ == "__main__":
    # Simple test
    vad = VADWrapper(mode=3, sample_rate=16000)
    
    # Generate test audio (silence)
    silence = np.zeros(16000 // 10, dtype=np.int16)  # 100ms of silence
    print(f"Silence detected as speech: {vad.is_speech(silence)}")
    
    print("VAD test complete")
