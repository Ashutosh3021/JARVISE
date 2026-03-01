"""
JARVIS STT (Speech-to-Text) Module
Provides transcription using faster-whisper
"""

from faster_whisper import WhisperModel
import numpy as np
from typing import Optional, Tuple
from pathlib import Path
import tempfile
import os
from loguru import logger


class STTEngine:
    """
    Speech-to-text engine using faster-whisper.
    Loads medium model with CUDA support for efficient transcription.
    """
    
    def __init__(self, model_size: str = "medium", device: str = "cuda",
                 compute_type: str = "float16", language: str = "en"):
        """
        Initialize STT engine.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to use (cuda or cpu)
            compute_type: Computation type (float16, int8, float32)
            language: Language code for transcription
        """
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._language = language
        self._model: Optional[WhisperModel] = None
        
        logger.info(f"STTEngine initializing with model={model_size}, device={device}")
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model."""
        try:
            self._model = WhisperModel(
                self._model_size,
                device=self._device,
                compute_type=self._compute_type
            )
            logger.info(f"STT model loaded: {self._model_size}")
        except Exception as e:
            logger.error(f"Failed to load STT model: {e}")
            # Fallback to CPU if CUDA fails
            if self._device == "cuda":
                logger.info("Falling back to CPU")
                self._model = WhisperModel(
                    self._model_size,
                    device="cpu",
                    compute_type="float32"
                )
            else:
                raise
    
    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Tuple[str, float]:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Audio as numpy array (float32 or int16)
            sample_rate: Audio sample rate
            
        Returns:
            Tuple of (transcribed_text, confidence_score)
        """
        if self._model is None:
            raise RuntimeError("STT model not loaded")
        
        # Convert to float32 if needed
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32) / 32768.0
        
        # Normalize if needed
        if audio_data.max() > 1.0:
            audio_data = audio_data / 32768.0
        
        # Save to temp file (faster-whisper requires file input)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
            temp_path = f.name
        
        try:
            # Write WAV file
            import soundfile as sf
            sf.write(temp_path, audio_data, sample_rate)
            
            # Transcribe
            segments, info = self._model.transcribe(
                temp_path,
                language=self._language,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Combine all segments
            text_parts = []
            total_confidence = 0.0
            segment_count = 0
            
            for segment in segments:
                text_parts.append(segment.text.strip())
                total_confidence += segment.avg_logprob
                segment_count += 1
            
            full_text = " ".join(text_parts)
            avg_confidence = total_confidence / segment_count if segment_count > 0 else 0.0
            
            logger.info(f"Transcribed: '{full_text}' (confidence: {avg_confidence:.2f})")
            return full_text, avg_confidence
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def transcribe_file(self, audio_path: str) -> Tuple[str, float]:
        """
        Transcribe an audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Tuple of (transcribed_text, confidence_score)
        """
        if self._model is None:
            raise RuntimeError("STT model not loaded")
        
        segments, info = self._model.transcribe(
            audio_path,
            language=self._language,
            beam_size=5,
            vad_filter=True
        )
        
        text_parts = []
        total_logprob = 0.0
        segment_count = 0
        
        for segment in segments:
            text_parts.append(segment.text.strip())
            total_logprob += segment.avg_logprob
            segment_count += 1
        
        full_text = " ".join(text_parts)
        avg_confidence = total_logprob / segment_count if segment_count > 0 else 0.0
        
        return full_text, avg_confidence
    
    @property
    def language(self) -> str:
        """Get the language code."""
        return self._language
    
    @property
    def model_size(self) -> str:
        """Get the model size."""
        return self._model_size
    
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model is not None


if __name__ == "__main__":
    # Test transcription
    print("Loading STT engine...")
    stt = STTEngine(model_size="medium", device="cpu")
    
    print("STT engine ready (CPU mode)")
    print("Transcription test would require audio input")
