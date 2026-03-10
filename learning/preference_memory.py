"""
JARVIS Learning Module - Preference Memory

Stores and retrieves user preferences for tool selection.
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger


@dataclass
class Preference:
    """A learned user preference."""
    trigger: str
    tool_name: str
    tool_args: dict
    confidence: int  # 1-10
    created_at: datetime
    last_used: datetime
    use_count: int
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "trigger": self.trigger,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat(),
            "use_count": self.use_count,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Preference":
        """Create Preference from dictionary."""
        return cls(
            trigger=data["trigger"],
            tool_name=data["tool_name"],
            tool_args=data.get("tool_args", {}),
            confidence=data.get("confidence", 5),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_used=datetime.fromisoformat(data["last_used"]),
            use_count=data.get("use_count", 1),
        )


class PreferenceMemory:
    """Memory system for storing and retrieving user preferences."""
    
    def __init__(self, storage_path: str = "./data/preferences.json"):
        """Initialize preference memory.
        
        Args:
            storage_path: Path to JSON file for persistence
        """
        self.storage_path = Path(storage_path)
        self._preferences: dict[str, Preference] = {}
        
        # Ensure data directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing preferences
        self._load()
    
    def _load(self) -> None:
        """Load preferences from storage file."""
        if not self.storage_path.exists():
            logger.debug("No preferences file found, starting fresh")
            return
        
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
            
            for trigger, pref_data in data.items():
                try:
                    self._preferences[trigger] = Preference.from_dict(pref_data)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Skipping invalid preference: {e}")
            
            logger.info(f"Loaded {len(self._preferences)} preferences")
        except Exception as e:
            logger.error(f"Failed to load preferences: {e}")
    
    def _save(self) -> None:
        """Save preferences to storage file."""
        try:
            data = {
                trigger: pref.to_dict() 
                for trigger, pref in self._preferences.items()
            }
            
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(self._preferences)} preferences")
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
    
    def learn(
        self, 
        trigger: str, 
        tool_name: str, 
        tool_args: dict | None = None,
        confidence: int = 5
    ) -> None:
        """Learn a preference from user action.
        
        Args:
            trigger: The action/command that triggered this
            tool_name: The tool that was used
            tool_args: Arguments used with the tool
            confidence: Confidence level (1-10)
        """
        trigger_lower = trigger.lower().strip()
        tool_args = tool_args or {}
        
        now = datetime.now()
        
        if trigger_lower in self._preferences:
            # Update existing preference
            pref = self._preferences[trigger_lower]
            pref.tool_name = tool_name
            pref.tool_args = tool_args
            pref.last_used = now
            pref.use_count += 1
            
            # Increase confidence over time, up to 10
            pref.confidence = min(10, pref.confidence + 1)
            
            logger.info(f"Updated preference: '{trigger}' -> {tool_name} (count: {pref.use_count})")
        else:
            # Create new preference
            self._preferences[trigger_lower] = Preference(
                trigger=trigger_lower,
                tool_name=tool_name,
                tool_args=tool_args,
                confidence=min(10, confidence),
                created_at=now,
                last_used=now,
                use_count=1
            )
            logger.info(f"Learned new preference: '{trigger}' -> {tool_name}")
        
        self._save()
    
    def get_preferred(self, trigger: str) -> Preference | None:
        """Get the preferred tool for a trigger.
        
        Args:
            trigger: The action/command to look up
            
        Returns:
            Best matching Preference or None
        """
        trigger_lower = trigger.lower().strip()
        
        if trigger_lower not in self._preferences:
            # Try partial match
            for key, pref in self._preferences.items():
                if key in trigger_lower or trigger_lower in key:
                    logger.debug(f"Partial match: '{trigger}' matched '{key}'")
                    return pref
            return None
        
        pref = self._preferences[trigger_lower]
        
        # Update last used
        pref.last_used = datetime.now()
        
        return pref
    
    def forget(self, trigger: str) -> bool:
        """Remove a preference.
        
        Args:
            trigger: The trigger to forget
            
        Returns:
            True if removed, False if not found
        """
        trigger_lower = trigger.lower().strip()
        
        if trigger_lower in self._preferences:
            del self._preferences[trigger_lower]
            self._save()
            logger.info(f"Forgot preference: '{trigger}'")
            return True
        
        return False
    
    def list_preferences(self) -> list[Preference]:
        """List all stored preferences.
        
        Returns:
            List of all preferences
        """
        return list(self._preferences.values())
    
    def export_json(self) -> str:
        """Export preferences as JSON string.
        
        Returns:
            JSON string of all preferences
        """
        data = {
            trigger: pref.to_dict()
            for trigger, pref in self._preferences.items()
        }
        return json.dumps(data, indent=2)
    
    def import_json(self, json_str: str) -> int:
        """Import preferences from JSON string.
        
        Args:
            json_str: JSON string to import
            
        Returns:
            Number of preferences imported
        """
        try:
            data = json.loads(json_str)
            count = 0
            
            for trigger, pref_data in data.items():
                try:
                    self._preferences[trigger] = Preference.from_dict(pref_data)
                    count += 1
                except (KeyError, ValueError) as e:
                    logger.warning(f"Skipping invalid preference during import: {e}")
            
            self._save()
            logger.info(f"Imported {count} preferences")
            return count
        except Exception as e:
            logger.error(f"Failed to import preferences: {e}")
            return 0
    
    def get_stats(self) -> dict:
        """Get statistics about stored preferences.
        
        Returns:
            Dict with preference statistics
        """
        total_uses = sum(p.use_count for p in self._preferences.values())
        avg_confidence = sum(p.confidence for p in self._preferences.values()) / len(self._preferences) if self._preferences else 0
        
        return {
            "total_preferences": len(self._preferences),
            "total_uses": total_uses,
            "average_confidence": round(avg_confidence, 2),
            "most_used": max(
                [(p.trigger, p.use_count) for p in self._preferences.values()],
                default=[("", 0)],
                key=lambda x: x[1]
            )[0],
        }


__all__ = ["PreferenceMemory", "Preference"]
