"""
JARVIS Keyboard Handler Module
Provides push-to-talk activation via space bar
Space = start recording, Enter = stop recording
"""

import keyboard
import threading
from typing import Callable, Optional
from loguru import logger


class KeyboardHandler:
    """
    Handles keyboard events for push-to-talk activation.
    Space bar press starts recording, Enter press stops and triggers transcription.
    """
    
    def __init__(self, on_press_callback: Optional[Callable] = None, 
                 on_release_callback: Optional[Callable] = None,
                 max_recording_duration: float = 30.0):
        """
        Initialize the keyboard handler.
        
        Args:
            on_press_callback: Callback function when space is pressed
            on_release_callback: Callback function when enter is pressed (stop)
            max_recording_duration: Max recording duration in seconds before force-stop
        """
        self._on_press_callback = on_press_callback
        self._on_release_callback = on_release_callback
        self._max_duration = max_recording_duration
        self._is_listening = False
        self._press_hook_id = None
        self._stop_hook_id = None
        self._watchdog: Optional[threading.Timer] = None
        
        logger.info("KeyboardHandler initialized")
    
    def start(self):
        """Start listening for keyboard events."""
        if self._press_hook_id is not None:
            logger.warning("Keyboard handler already started")
            return
        
        # Space = start recording
        self._press_hook_id = keyboard.on_press_key("space", self._handle_space_press)
        # Enter = stop recording
        self._stop_hook_id = keyboard.on_press_key("enter", self._handle_enter_press)
        
        logger.info("Keyboard handler started - press SPACE to start, ENTER to stop")
    
    def stop(self):
        """Stop listening for keyboard events."""
        self._cancel_watchdog()
        if self._press_hook_id is not None:
            keyboard.unhook(self._press_hook_id)
            self._press_hook_id = None
        if self._stop_hook_id is not None:
            keyboard.unhook(self._stop_hook_id)
            self._stop_hook_id = None
        
        logger.info("Keyboard handler stopped")
    
    def _cancel_watchdog(self):
        """Cancel any active watchdog timer."""
        if self._watchdog is not None:
            self._watchdog.cancel()
            self._watchdog = None
    
    def _start_watchdog(self):
        """Start watchdog timer to force-stop if Enter never fires."""
        self._cancel_watchdog()
        self._watchdog = threading.Timer(self._max_duration, self._force_stop)
        self._watchdog.start()
    
    def _force_stop(self):
        """Force stop recording when watchdog timer fires."""
        self._watchdog = None
        if self._is_listening:
            logger.warning(f"Watchdog: force-stopping stuck recorder (max {self._max_duration}s exceeded)")
            self._is_listening = False
            if self._on_release_callback:
                try:
                    self._on_release_callback()
                except Exception as e:
                    logger.error(f"Error in force-stop callback: {e}")
    
    def _handle_space_press(self, event):
        """Handle space bar press — start recording."""
        if self._is_listening:
            logger.debug("Already recording, ignoring space press")
            return
        self._is_listening = True
        self._start_watchdog()
        logger.debug("Space pressed - starting recording")
        if self._on_press_callback:
            try:
                self._on_press_callback()
            except Exception as e:
                logger.error(f"Error in press callback: {e}")
    
    def _handle_enter_press(self, event):
        """Handle Enter press — stop recording."""
        if not self._is_listening:
            logger.debug("Not recording, ignoring enter press")
            return
        self._cancel_watchdog()
        self._is_listening = False
        logger.debug("Enter pressed - stopping recording")
        if self._on_release_callback:
            try:
                self._on_release_callback()
            except Exception as e:
                logger.error(f"Error in release callback: {e}")
    
    @property
    def is_listening(self) -> bool:
        """Check if currently listening."""
        return self._is_listening
    
    def set_press_callback(self, callback: Callable):
        """Set the press callback."""
        self._on_press_callback = callback
    
    def set_release_callback(self, callback: Callable):
        """Set the release callback."""
        self._on_release_callback = callback


if __name__ == "__main__":
    # Simple test
    handler = KeyboardHandler(
        on_press_callback=lambda: print("Recording started"),
        on_release_callback=lambda: print("Recording stopped")
    )
    handler.start()
    print("Press SPACE to start recording, ENTER to stop. Press ESC to exit.")
    keyboard.wait('esc')
    handler.stop()