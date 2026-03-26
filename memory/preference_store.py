"""
JARVIS Preference Store Module

Provides persistent storage for learned user preferences and corrections.
Used by the learning system to remember user preferences across sessions.
"""

import json
from pathlib import Path
from typing import Any


class PreferenceStore:
    """Store for user preferences learned from corrections."""
    
    def __init__(self, storage_path: str = "./data/preferences.json"):
        """
        Initialize the preference store.
        
        Args:
            storage_path: Path to the preferences JSON file
        """
        self.storage_path = Path(storage_path)
        self._preferences: dict[str, Any] = {}
        self._load()
    
    def _load(self) -> None:
        """Load preferences from JSON file."""
        if self.storage_path.exists():
            try:
                self._preferences = json.loads(self.storage_path.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, IOError) as e:
                self._preferences = {}
    
    def _save(self) -> None:
        """Save preferences to JSON file."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(
            json.dumps(self._preferences, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a preference value.
        
        Args:
            key: Preference key
            default: Default value if key not found
            
        Returns:
            The preference value or default
        """
        return self._preferences.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Store a preference value.
        
        Args:
            key: Preference key
            value: Preference value
        """
        self._preferences[key] = value
        self._save()
    
    def delete(self, key: str) -> bool:
        """
        Remove a preference.
        
        Args:
            key: Preference key to remove
            
        Returns:
            True if key existed, False otherwise
        """
        if key in self._preferences:
            del self._preferences[key]
            self._save()
            return True
        return False
    
    def get_all(self) -> dict[str, Any]:
        """
        Get all preferences.
        
        Returns:
            Dictionary of all preferences
        """
        return dict(self._preferences)
    
    def get_category(self, category: str) -> dict[str, Any]:
        """
        Get all preferences in a category.
        
        Args:
            category: Category name (e.g., "app_aliases", "command_patterns")
            
        Returns:
            Dictionary of preferences in that category
        """
        return self._preferences.get(category, {})
    
    def set_category(self, category: str, values: dict[str, Any]) -> None:
        """
        Set all preferences in a category.
        
        Args:
            category: Category name
            values: Dictionary of preference values
        """
        if category not in self._preferences:
            self._preferences[category] = {}
        self._preferences[category].update(values)
        self._save()
    
    def clear_category(self, category: str) -> bool:
        """
        Clear all preferences in a category.
        
        Args:
            category: Category name
            
        Returns:
            True if category existed, False otherwise
        """
        if category in self._preferences:
            del self._preferences[category]
            self._save()
            return True
        return False


# Example preference categories:
# - "app_aliases": {"editor": "VSCode", "code": "VSCode"}
# - "command_patterns": {"open editor": "open VSCode"}
# - "path_overrides": {"chrome": "C:\\Program Files\\..."}


__all__ = ["PreferenceStore"]