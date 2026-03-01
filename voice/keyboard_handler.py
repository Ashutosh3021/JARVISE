"""
JARVIS Keyboard Handler Module
Provides push-to-talk activation via space bar
"""

import keyboard
from typing import Callable, Optional
from loguru import logger


class KeyboardHandler:
    """
    Handles keyboard events for push-to-talk activation.
    Space bar press starts recording, release stops and triggers transcription.
    """
    
    def __init__(self, on_press_callback: Optional[Callable] = None, 
                 on_release_callback: Optional[Callable] = None):
        """
        Initialize the keyboard handler.
        
        Args:
            on_press_callback: Callback function when space is pressed
            on_release_callback: Callback function when space is released
        """
        self._on_press_callback = on_press_callback
        self._on_release_callback = on_release_callback
        self._is_listening = False
        self._hook_id = None
        self._release_hook_id = None
        
        logger.info("KeyboardHandler initialized")
    
    def start(self):
        """Start listening for keyboard events."""
        if self._hook_id is not None:
            logger.warning("Keyboard handler already started")
            return
        
        # Register press handler
        self._hook_id = keyboard.on_press(self._handle_press)
        self._release_hook_id = keyboard.on_release(self._handle_release)
        
        logger.info("Keyboard handler started - press space to activate")
    
    def stop(self):
        """Stop listening for keyboard events."""
        if self._hook_id is not None:
            keyboard.unhook(self._hook_id)
            self._hook_id = None
        if self._release_hook_id is not None:
            keyboard.unhook(self._release_hook_id)
            self._release_hook_id = None
        
        logger.info("Keyboard handler stopped")
    
    def _handle_press(self, event):
        """Handle key press events."""
        if event.name == 'space':
            self._is_listening = True
            logger.debug("Space pressed - starting recording")
            if self._on_press_callback:
                try:
                    self._on_press_callback()
                except Exception as e:
                    logger.error(f"Error in press callback: {e}")
    
    def _handle_release(self, event):
        """Handle key release events."""
        if event.name == 'space':
            self._is_listening = False
            logger.debug("Space released - stopping recording")
            if self._on_release_callback:
                try:
                    self._on_release_callback()
                except Exception as e:
                    logger.error(f"Error in release callback: {e}")
    
    @property
    def is_listening(self) -> bool:
        """Check if currently listening (space bar held)."""
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
    print("Press space to test. Press ESC to exit.")
    keyboard.wait('esc')
    handler.stop()
