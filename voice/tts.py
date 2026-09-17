"""
JARVIS TTS (Text-to-Speech) Module
Provides speech synthesis using Kokoro
"""

import os
import numpy as np
import librosa
from typing import Optional, List
from loguru import logger

# Try to import kokoro-onnx first, fallback to kokoro
try:
    from kokoro_onnx import Kokoro
    KOKORO_TYPE = "onnx"
except ImportError:
    try:
        from kokoro import KPipeline
        KOKORO_TYPE = "kokoro"
    except ImportError:
        KOKORO_TYPE = None
        logger.warning("Neither kokoro-onnx nor kokoro available")

# Default model paths
DEFAULT_MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "kokoro_models")
DEFAULT_MODEL_PATH = os.path.join(DEFAULT_MODEL_DIR, "kokoro-v1.0.int8.onnx")
DEFAULT_VOICES_PATH = os.path.join(DEFAULT_MODEL_DIR, "voices-v1.0.bin")


class TTSEngine:
    """
    Text-to-speech engine using Kokoro.
    Synthesizes text to audio with British male voice.
    """
    
    # Language codes (short -> espeak)
    LANGUAGE_CODES = {
        'b': 'en-gb',
        'a': 'en-us'
    }
    
    # Available British male voices
    BRITISH_MALE_VOICES = ['bm_daniel', 'bm_fable', 'bm_george', 'bm_lewis']
    
    def __init__(self, voice: str = 'bm_lewis', language_code: str = 'b',
                 speed: float = 1.0, model_path: Optional[str] = None,
                 voices_path: Optional[str] = None):
        """
        Initialize TTS engine.
        
        Args:
            voice: Voice identifier
            language_code: Language code ('b' for British, 'a' for American)
            speed: Speech speed (0.5 - 2.0, 1.0 is normal)
            model_path: Path to kokoro ONNX model file
            voices_path: Path to voices binary file
        """
        self._voice = voice
        self._language_code = language_code
        self._speed = speed
        self._model_path = model_path or DEFAULT_MODEL_PATH
        self._voices_path = voices_path or DEFAULT_VOICES_PATH
        self._kokoro: Optional[Kokoro] = None
        
        if KOKORO_TYPE is None:
            raise RuntimeError("Neither kokoro-onnx nor kokoro is installed")
        
        logger.info(f"TTSEngine initializing: voice={voice}, lang={language_code}, speed={speed}")
        self._load_pipeline()
    
    def _load_pipeline(self):
        """Load the Kokoro engine."""
        try:
            if KOKORO_TYPE == "onnx":
                if not os.path.exists(self._model_path):
                    raise FileNotFoundError(f"Model file not found: {self._model_path}")
                if not os.path.exists(self._voices_path):
                    raise FileNotFoundError(f"Voices file not found: {self._voices_path}")
                
                self._kokoro = Kokoro(self._model_path, self._voices_path)
                logger.info(f"TTS engine loaded from local files")
            else:
                # Fallback to old kokoro library
                self._pipeline = KPipeline(lang_code=self._language_code, repo_id='hexgrad/Kokoro-82M')
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
        if self._kokoro is None and KOKORO_TYPE == "onnx":
            raise RuntimeError("TTS engine not loaded")
        
        if not text or not text.strip():
            logger.warning("Empty text provided")
            return np.array([], dtype=np.float32)
        
        try:
            # Generate audio
            audio_arrays = []
            
            if KOKORO_TYPE == "onnx":
                # New kokoro-onnx API: create() returns (audio_array, sample_rate)
                # Map short language code to espeak code
                espeak_lang = self.LANGUAGE_CODES.get(self._language_code, self._language_code)
                audio, sample_rate = self._kokoro.create(
                    text,
                    voice=self._voice,
                    speed=self._speed,
                    lang=espeak_lang
                )
                if audio is not None and len(audio) > 0:
                    audio_arrays.append(np.asarray(audio, dtype=np.float32))
            else:
                # Old kokoro library API
                for result in self._pipeline(text, voice=self._voice):
                    audio = self._extract_audio_chunk(result)
                    if audio is not None and len(audio) > 0:
                        audio_arrays.append(audio)
            
            if audio_arrays:
                result = np.concatenate(audio_arrays)
                if KOKORO_TYPE != "onnx" and self._speed != 1.0:
                    result = self._adjust_speed(result, self._speed)
                logger.info(f"Generated {len(result)} samples ({len(result)/24000:.2f}s) of audio")
                return result
            else:
                logger.warning("No audio generated")
                return np.array([], dtype=np.float32)
                
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            raise
    
    def _extract_audio_chunk(self, result) -> np.ndarray | None:
        """Extract audio array from a Kokoro pipeline result (supports onnx API variants)."""
        audio = None
        if hasattr(result, "output") and hasattr(result.output, "audio"):
            audio = result.output.audio
        elif hasattr(result, "audio"):
            audio = result.audio

        if audio is None:
            return None

        try:
            import torch
            if isinstance(audio, torch.Tensor):
                audio = audio.cpu().numpy()
        except ImportError:
            pass

        return np.asarray(audio, dtype=np.float32)

    def _adjust_speed(self, audio: np.ndarray, speed: float) -> np.ndarray:
        """
        Adjust audio speed via time stretching.
        
        Args:
            audio: Input audio
            speed: Speed multiplier (>1 = faster, <1 = slower)
            
        Returns:
            Speed-adjusted audio at same sample rate
        """
        if speed == 1.0:
            return audio
        
        return librosa.effects.time_stretch(audio, rate=speed)
    
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
