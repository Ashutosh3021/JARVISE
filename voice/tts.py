"""
JARVIS TTS (Text-to-Speech) Module
Provides speech synthesis using Kokoro
"""

import numpy as np
from typing import Optional, List
from loguru import logger

# Try to import kokoro-onnx first, fallback to kokoro
try:
    from kokoro_onnx import KPipeline
    KOKORO_TYPE = "onnx"
except ImportError:
    try:
        from kokoro import KPipeline
        KOKORO_TYPE = "kokoro"
    except ImportError:
        KOKORO_TYPE = None
        logger.warning("Neither kokoro-onnx nor kokoro available")


class TTSEngine:
    """
    Text-to-speech engine using Kokoro.
    Synthesizes text to audio with British male voice.
    """
    
    # Language codes
    LANGUAGE_CODES = {
        'b': 'British English',
        'a': 'American English'
    }
    
    # Available British male voices
    BRITISH_MALE_VOICES = ['bm_daniel', 'bm_fable', 'bm_george', 'bm_lewis']
    
    def __init__(self, voice: str = 'bm_lewis', language_code: str = 'b',
                 speed: float = 1.0):
        """
        Initialize TTS engine.
        
        Args:
            voice: Voice identifier
            language_code: Language code ('b' for British, 'a' for American)
            speed: Speech speed (0.5 - 2.0, 1.0 is normal)
        """
        self._voice = voice
        self._language_code = language_code
        self._speed = speed
        self._pipeline: Optional[KPipeline] = None
        
        if KOKORO_TYPE is None:
            raise RuntimeError("Neither kokoro-onnx nor kokoro is installed")
        
        logger.info(f"TTSEngine initializing: voice={voice}, lang={language_code}, speed={speed}")
        self._load_pipeline()
    
    def _load_pipeline(self):
        """Load the Kokoro pipeline."""
        try:
            self._pipeline = KPipeline(
                lang_code=self._language_code,
                repo_id=None  # Will download default voice
            )
            logger.info(f"TTS pipeline loaded: {KOKORO_TYPE}")
        except Exception as e:
            logger.error(f"Failed to load TTS pipeline: {e}")
            raise
    
    def speak(self, text: str) -> np.ndarray:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            
        Returns:
            Audio data as numpy array (24kHz, float32)
        """
        if self._pipeline is None:
            raise RuntimeError("TTS pipeline not loaded")
        
        if not text or not text.strip():
            logger.warning("Empty text provided")
            return np.array([], dtype=np.float32)
        
        try:
            # Generate audio
            audio_arrays = []
            
            for grapheme, phoneme, audio in self._pipeline(text, voice=self._voice):
                if audio is not None:
                    # Adjust speed by resampling if needed
                    if self._speed != 1.0:
                        audio = self._adjust_speed(audio, self._speed)
                    audio_arrays.append(audio)
            
            if audio_arrays:
                # Concatenate all audio segments
                result = np.concatenate(audio_arrays)
                logger.info(f"Generated {len(result)} samples ({len(result)/24000:.2f}s) of audio")
                return result
            else:
                logger.warning("No audio generated")
                return np.array([], dtype=np.float32)
                
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            raise
    
    def _adjust_speed(self, audio: np.ndarray, speed: float) -> np.ndarray:
        """
        Adjust audio speed by resampling.
        
        Args:
            audio: Input audio
            speed: Speed multiplier (>1 = faster, <1 = slower)
            
        Returns:
            Speed-adjusted audio
        """
        if speed == 1.0:
            return audio
        
        # Simple speed adjustment via resampling
        new_length = int(len(audio) / speed)
        indices = np.linspace(0, len(audio) - 1, new_length)
        return np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)
    
    def speak_to_file(self, text: str, output_path: str):
        """
        Synthesize speech and save to file.
        
        Args:
            text: Text to synthesize
            output_path: Path to save audio file
        """
        import soundfile as sf
        
        audio = self.speak(text)
        if len(audio) > 0:
            sf.write(output_path, audio, 24000)
            logger.info(f"Saved TTS audio to {output_path}")
    
    @property
    def voice(self) -> str:
        """Get the voice identifier."""
        return self._voice
    
    @property
    def language_code(self) -> str:
        """Get the language code."""
        return self._language_code
    
    @property
    def speed(self) -> float:
        """Get the speech speed."""
        return self._speed
    
    @property
    def sample_rate(self) -> int:
        """Get the output sample rate (24kHz for Kokoro)."""
        return 24000
    
    def list_voices(self) -> List[str]:
        """List available voices."""
        return self.BRITISH_MALE_VOICES.copy()


if __name__ == "__main__":
    # Test TTS
    print("Loading TTS engine...")
    try:
        tts = TTSEngine(voice='bm_lewis', language_code='b')
        print(f"TTS engine ready: {tts.voice}, sample_rate={tts.sample_rate}Hz")
        
        # Test synthesis
        audio = tts.speak("Hello, I am JARVIS.")
        print(f"Generated {len(audio)} samples")
    except Exception as e:
        print(f"TTS test skipped: {e}")
