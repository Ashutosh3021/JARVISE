"""
JARVIS HITL - Confirmation & Undo Module

Provides:
- ConfirmationCallback: type for user confirmation prompts
- UndoTracker: tracks reversible state changes for Yellow actions
"""

import time
import json
import uuid
from pathlib import Path
from typing import Callable, Any, Optional
from dataclasses import dataclass, field
from loguru import logger


# Type for confirmation callback: (message, risk_level) -> bool
ConfirmationCallback = Callable[[str, str], bool]


@dataclass
class UndoEntry:
    """A reversible state change record."""
    undo_id: str
    tool_name: str
    action: str
    timestamp: float
    snapshot: dict  # pre-state for undo
    description: str


class UndoTracker:
    """Tracks reversible state changes for Yellow actions.
    
    Stores snapshots before write/delete operations.
    Provides undo() to revert if needed.
    """
    
    UNDO_WINDOW_SECONDS = 300  # 5 minutes
    
    def __init__(self, persist_path: str = "./data/undo_log.jsonl"):
        self._persist_path = Path(persist_path)
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, UndoEntry] = {}
        self._load()
    
    def _load(self) -> None:
        """Load persisted undo entries."""
        if not self._persist_path.exists():
            return
        try:
            with open(self._persist_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    entry = UndoEntry(**data)
                    # Only load entries within window
                    if time.time() - entry.timestamp < self.UNDO_WINDOW_SECONDS:
                        self._entries[entry.undo_id] = entry
        except Exception as e:
            logger.error(f"Failed to load undo log: {e}")
    
    def record(self, tool_name: str, action: str, snapshot: dict,
               description: str = "") -> str:
        """Record a reversible change. Returns undo_id."""
        undo_id = str(uuid.uuid4())[:8]
        entry = UndoEntry(
            undo_id=undo_id,
            tool_name=tool_name,
            action=action,
            timestamp=time.time(),
            snapshot=snapshot,
            description=description,
        )
        self._entries[undo_id] = entry
        self._persist(entry)
        logger.debug(f"Undo recorded: {undo_id} ({tool_name}.{action})")
        return undo_id
    
    def can_undo(self, undo_id: str) -> bool:
        """Check if an undo is still within the grace window."""
        entry = self._entries.get(undo_id)
        if not entry:
            return False
        return (time.time() - entry.timestamp) < self.UNDO_WINDOW_SECONDS
    
    def get_entry(self, undo_id: str) -> UndoEntry | None:
        """Get an undo entry."""
        return self._entries.get(undo_id)
    
    def pop_entry(self, undo_id: str) -> UndoEntry | None:
        """Get and remove an undo entry."""
        return self._entries.pop(undo_id, None)
    
    def cleanup_expired(self) -> int:
        """Remove expired entries. Returns count removed."""
        now = time.time()
        expired = [uid for uid, e in self._entries.items()
                   if now - e.timestamp >= self.UNDO_WINDOW_SECONDS]
        for uid in expired:
            del self._entries[uid]
        return len(expired)
    
    def _persist(self, entry: UndoEntry) -> None:
        """Append an entry to the persist file."""
        try:
            with open(self._persist_path, "a") as f:
                f.write(json.dumps({
                    "undo_id": entry.undo_id,
                    "tool_name": entry.tool_name,
                    "action": entry.action,
                    "timestamp": entry.timestamp,
                    "snapshot": entry.snapshot,
                    "description": entry.description,
                }) + "\n")
        except Exception as e:
            logger.error(f"Failed to persist undo entry: {e}")
    
    @property
    def active_count(self) -> int:
        """Number of active undo entries."""
        return len(self._entries)


# Global instances
_undo_tracker: UndoTracker | None = None
_confirmation_callback: ConfirmationCallback | None = None


def get_undo_tracker() -> UndoTracker:
    """Get or create the global undo tracker."""
    global _undo_tracker
    if _undo_tracker is None:
        _undo_tracker = UndoTracker()
    return _undo_tracker


def set_confirmation_callback(callback: ConfirmationCallback) -> None:
    """Set the global confirmation callback (called by CLI/voice layer)."""
    global _confirmation_callback
    _confirmation_callback = callback


def get_confirmation_callback() -> ConfirmationCallback | None:
    """Get the current confirmation callback."""
    return _confirmation_callback


def ask_confirmation(message: str, risk_level: str = "yellow") -> bool:
    """Ask user for confirmation using the registered callback.
    
    Falls back to console input if no callback is set.
    """
    global _confirmation_callback
    
    if _confirmation_callback:
        return _confirmation_callback(message, risk_level)
    
    # Fallback: console prompt
    print(f"\n⚠️  CONFIRMATION REQUIRED [{risk_level.upper()}]")
    print(f"   {message}")
    response = input("   Confirm? [y/N]: ").strip().lower()
    return response in ("y", "yes")


__all__ = [
    "UndoTracker", "UndoEntry",
    "ConfirmationCallback", "set_confirmation_callback", "ask_confirmation",
    "get_undo_tracker", "get_confirmation_callback",
]
