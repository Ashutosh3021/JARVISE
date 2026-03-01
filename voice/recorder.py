"""
JARVIS Audio Recorder Module
Provides audio recording with circular buffer for continuous capture
"""

import sounddevice as sd
import numpy as np
from typing import Optional, Callable
from collections import deque
import threading
import time
from loguru import logger


class AudioRecorder:
    """
    Audio recorder with circular buffer for continuous capture.
    Records audio when activated, buffers frames, and returns on stop.
    """
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1, 
                 dtype: str = 'int16', max_duration: float = 30.0):
        """
        Initialize audio recorder.
        
        Args:
            sample_rate: Audio sample rate (default 16000 Hz for VAD/STT)
            channels: Number of audio channels (default 1 for mono)
            dtype: Audio data type
            max_duration: Maximum recording duration in seconds
        """
        self._sample_rate = sample_rate
        self._channels = channels
        self._dtype = dtype
        self._max_duration = max_duration
        self._max_samples = int(max_duration * sample_rate)
        
        self._is_recording = False
        self._audio_buffer: deque = deque(maxlen=self._max_samples)
        self._stream: Optional[sd.InputStream] = None
        self._lock = threading.Lock()
        self._callback: Optional[Callable] = None
        
        logger.info(f"AudioRecorder initialized: {sample_rate}Hz, {channels}ch, max {max_duration}s")
    
    def start(self, device: Optional[int] = None):
        """
        Start audio recording.
        
        Args:
            device: Input device index (None for default)
        """
        if self._is_recording:
            logger.warning("Already recording")
            return
        
        with self._lock:
            self._audio_buffer.clear()
            self._is_recording = True
        
        try:
            self._stream = sd.InputStream(
                device=device,
                channels=self._channels,
                samplerate=self._sample_rate,
                dtype=self._dtype,
                blocksize=1024,  # ~64ms blocks
                callback=self._audio_callback
            )
            self._stream.start()
            logger.info("Audio recording started")
        except Exception as e:
            self._is_recording = False
            logger.error(f"Failed to start recording: {e}")
            raise
    
    def stop(self) -> np.ndarray:
        """
        Stop audio recording and return recorded audio.
        
        Returns:
            Audio data as numpy array
        """
        if not self._is_recording:
            logger.warning("Not recording")
            return np.array([], dtype=self._dtype)
        
        with self._lock:
            self._is_recording = False
            
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
                self._stream = None
        
        # Collect audio from buffer
        audio_data = np.array(list(self._audio_buffer), dtype=self._dtype)
        self._audio_buffer.clear()
        
        logger.info(f"Audio recording stopped, captured {len(audio_data)} samples")
        return audio_data
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Audio stream callback."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        if self._is_recording:
            with self._lock:
                self._audio_buffer.extend(indata[:, 0])  # Take first channel
    
    def get_audio(self) -> np.ndarray:
        """
        Get current audio buffer without stopping.
        
        Returns:
            Current audio data as numpy array
        """
        with self._lock:
            return np.array(list(self._audio_buffer), dtype=self._dtype)
    
    def clear_buffer(self):
        """Clear the audio buffer."""
        with self._lock:
            self._audio_buffer.clear()
        logger.debug("Audio buffer cleared")
    
    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._is_recording
    
    @property
    def sample_rate(self) -> int:
        """Get sample rate."""
        return self._sample_rate
    
    def list_devices(self):
        """List available audio input devices."""
        return sd.query_devices(kind='input')
    
    def set_callback(self, callback: Callable):
        """
        Set callback for audio data processing.
        
        Args:
            callback: Function called with audio chunk
        """
        self._callback = callback


if __name__ == "__main__":
    # Test recording
    recorder = AudioRecorder()
    
    print("Available input devices:")
    print(recorder.list_devices())
    
    print("\nRecording for 3 seconds...")
    recorder.start()
    time.sleep(3)
    audio = recorder.stop()
    
    print(f"Recorded {len(audio)} samples ({len(audio)/16000:.2f}s)")
    print("Recording test complete")
