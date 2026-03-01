"""
JARVIS Audio Output Module
Provides speaker playback with interruption support
"""

import sounddevice as sd
import numpy as np
from typing import Optional, Callable, List
import threading
import time
from loguru import logger


class AudioOutput:
    """
    Audio output handler for speaker playback.
    Supports play, stop, pause, resume, and interruption detection.
    """
    
    def __init__(self, sample_rate: int = 24000):
        """
        Initialize audio output.
        
        Args:
            sample_rate: Audio sample rate (default 24000 for Kokoro)
        """
        self._sample_rate = sample_rate
        self._is_playing = False
        self._is_paused = False
        self._stream: Optional[sd.OutputStream] = None
        self._current_audio: Optional[np.ndarray] = None
        self._playback_position = 0
        self._lock = threading.Lock()
        self._queue: List[np.ndarray] = []
        
        # Interruption callback
        self._on_interruption: Optional[Callable] = None
        
        logger.info(f"AudioOutput initialized: {sample_rate}Hz")
    
    def play(self, audio: np.ndarray, wait: bool = True):
        """
        Play audio through speakers.
        
        Args:
            audio: Audio data as numpy array
            wait: If True, wait for playback to finish
        """
        if audio is None or len(audio) == 0:
            logger.warning("Empty audio provided")
            return
        
        # Convert to correct dtype if needed
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        
        # Normalize if needed
        if audio.max() > 1.0:
            audio = audio / 32768.0
        
        # Clamp to valid range
        audio = np.clip(audio, -1.0, 1.0)
        
        with self._lock:
            if self._is_playing and self._is_paused:
                # Resume from pause
                self._is_paused = False
                self._resume_playback(audio)
                return
            elif self._is_playing:
                # Queue for sequential playback
                self._queue.append(audio)
                logger.debug(f"Audio queued, queue size: {len(self._queue)}")
                return
            
            self._current_audio = audio
            self._playback_position = 0
            self._is_playing = True
        
        # Play audio
        try:
            self._stream = sd.OutputStream(
                samplerate=self._sample_rate,
                channels=1,
                dtype='float32',
                callback=self._playback_callback
            )
            self._stream.start()
            
            if wait:
                while self._is_playing and not self._is_paused:
                    time.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Playback error: {e}")
            self._is_playing = False
            raise
    
    def _playback_callback(self, outdata, frames, time_info, status):
        """Playback stream callback."""
        if status:
            logger.warning(f"Playback status: {status}")
        
        with self._lock:
            if not self._is_playing or self._is_paused:
                outdata.fill(0)
                return
            
            if self._current_audio is None or self._playback_position >= len(self._current_audio):
                # Check queue
                if self._queue:
                    self._current_audio = self._queue.pop(0)
                    self._playback_position = 0
                else:
                    # End of playback
                    outdata.fill(0)
                    self._is_playing = False
                    return
            
            # Get next chunk
            end_pos = min(self._playback_position + frames, len(self._current_audio))
            chunk = self._current_audio[self._playback_position:end_pos]
            
            # Pad if needed
            if len(chunk) < frames:
                chunk = np.pad(chunk, (0, frames - len(chunk)))
            
            outdata[:, 0] = chunk
            self._playback_position = end_pos
    
    def _resume_playback(self, audio: np.ndarray):
        """Resume playback with new audio."""
        self._current_audio = audio
        self._playback_position = 0
        
        try:
            self._stream = sd.OutputStream(
                samplerate=self._sample_rate,
                channels=1,
                dtype='float32',
                callback=self._playback_callback
            )
            self._stream.start()
        except Exception as e:
            logger.error(f"Resume error: {e}")
            raise
    
    def stop(self):
        """Stop playback and clear queue."""
        with self._lock:
            self._is_playing = False
            self._is_paused = False
            self._queue.clear()
            self._playback_position = 0
            
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
                self._stream = None
        
        logger.info("Playback stopped")
    
    def pause(self):
        """Pause playback."""
        with self._lock:
            if self._is_playing and not self._is_paused:
                self._is_paused = True
                logger.info("Playback paused")
    
    def resume(self):
        """Resume paused playback."""
        with self._lock:
            if self._is_playing and self._is_paused:
                self._is_paused = False
                logger.info("Playback resumed")
    
    def queue_audio(self, audio: np.ndarray):
        """
        Queue audio for sequential playback.
        
        Args:
            audio: Audio data to queue
        """
        with self._lock:
            if not self._is_playing:
                # Play immediately
                self.play(audio)
            else:
                self._queue.append(audio)
                logger.debug(f"Audio added to queue")
    
    def clear_queue(self):
        """Clear pending audio queue."""
        with self._lock:
            self._queue.clear()
        logger.debug("Audio queue cleared")
    
    def set_interruption_callback(self, callback: Callable):
        """
        Set callback for interruption detection.
        
        Args:
            callback: Function called when interruption is detected
        """
        self._on_interruption = callback
    
    def trigger_interruption(self):
        """Manually trigger an interruption."""
        logger.info("Interruption triggered")
        if self._on_interruption:
            self._on_interruption()
        self.stop()
    
    @property
    def is_playing(self) -> bool:
        """Check if audio is playing."""
        return self._is_playing
    
    @property
    def is_paused(self) -> bool:
        """Check if playback is paused."""
        return self._is_paused
    
    @property
    def sample_rate(self) -> int:
        """Get sample rate."""
        return self._sample_rate
    
    @property
    def queue_size(self) -> int:
        """Get queued audio count."""
        return len(self._queue)


if __name__ == "__main__":
    # Test audio output
    print("Testing audio output...")
    output = AudioOutput()
    
    # Generate test tone
    duration = 1.0
    frequency = 440
    t = np.linspace(0, duration, int(24000 * duration))
    test_audio = (np.sin(2 * np.pi * frequency * t) * 0.3).astype(np.float32)
    
    print(f"Playing test tone ({frequency}Hz)...")
    output.play(test_audio)
    print("Playback test complete")
