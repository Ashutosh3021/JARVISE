"""
JARVIS Memory File Controller

Provides read/write access to the MEMORY.md human-editable memory file.
"""

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Default MEMORY.md template
DEFAULT_MEMORY_TEMPLATE = """# JARVIS Memory

## User Profile
- **Name:** [Your Name]
- **Location:** [Your Location]
- **Occupation:** [Your Occupation]
- **Interests:** [Your Interests]

## Preferences
- **Voice Speed:** 1.0
- **Model:** llama3.2:latest
- **Wake Word:** jarvis
- **TTS Voice:** af_sarah

## Important Facts
- [Add important facts about the user here]

## Ongoing Tasks
- [ ] [Task 1]
- [ ] [Task 2]

## Notes
- [Add any additional notes here]

---
*Last Updated: {timestamp}*
"""


class MemoryFileController:
    """
    Controller for reading and writing to the MEMORY.md file.
    
    Provides section-based access to different parts of the memory file,
    allowing both reading specific information and updating it.
    """
    
    # Section headers in the MEMORY.md file
    SECTIONS = {
        "User Profile": "## User Profile",
        "Preferences": "## Preferences",
        "Important Facts": "## Important Facts",
        "Ongoing Tasks": "## Ongoing Tasks",
        "Notes": "## Notes",
    }
    
    def __init__(self, file_path: str | Path = "./data/MEMORY.md"):
        """
        Initialize the memory file controller.
        
        Args:
            file_path: Path to the MEMORY.md file
        """
        self.file_path = Path(file_path)
        self._ensure_file_exists()
    
    def _ensure_file_exists(self) -> None:
        """Create the MEMORY.md file with default template if it doesn't exist."""
        if not self.file_path.exists():
            # Create parent directories if needed
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write default template
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            content = DEFAULT_MEMORY_TEMPLATE.format(timestamp=timestamp)
            self.file_path.write_text(content, encoding="utf-8")
    
    def _read_file(self) -> str:
        """Read the entire MEMORY.md file."""
        return self.file_path.read_text(encoding="utf-8")
    
    def _write_file(self, content: str) -> None:
        """Write content to the MEMORY.md file."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text(content, encoding="utf-8")
    
    def get_section(self, section_name: str) -> str:
        """
        Get the content of a specific section.
        
        Args:
            section_name: Name of the section (e.g., "User Profile", "Preferences")
            
        Returns:
            The content of the section, or empty string if not found
        """
        if section_name not in self.SECTIONS:
            raise ValueError(f"Unknown section: {section_name}")
        
        content = self._read_file()
        section_header = self.SECTIONS[section_name]
        
        # Find section start
        start_idx = content.find(section_header)
        if start_idx == -1:
            return ""
        
        # Find next section or end of file
        next_section_idx = len(content)
        for other_header in self.SECTIONS.values():
            if other_header == section_header:
                continue
            idx = content.find(other_header, start_idx + len(section_header))
            if idx != -1 and idx < next_section_idx:
                next_section_idx = idx
        
        # Extract section content (skip header line)
        section_content = content[start_idx + len(section_header):next_section_idx].strip()
        
        return section_content
    
    def update_section(self, section_name: str, new_content: str) -> None:
        """
        Update the content of a specific section.
        
        Args:
            section_name: Name of the section to update
            new_content: New content for the section
        """
        if section_name not in self.SECTIONS:
            raise ValueError(f"Unknown section: {section_name}")
        
        content = self._read_file()
        section_header = self.SECTIONS[section_name]
        
        # Find section start
        start_idx = content.find(section_header)
        if start_idx == -1:
            raise ValueError(f"Section '{section_name}' not found in MEMORY.md")
        
        # Find next section or end of file
        next_section_idx = len(content)
        for other_header in self.SECTIONS.values():
            if other_header == section_header:
                continue
            idx = content.find(other_header, start_idx + len(section_header))
            if idx != -1 and idx < next_section_idx:
                next_section_idx = idx
        
        # Build new content
        before_section = content[:start_idx]
        after_section = content[next_section_idx:]
        
        # Preserve section header and add new content
        new_section = f"{section_header}\n{new_content}\n"
        
        # Reconstruct file
        new_file_content = before_section + new_section + after_section
        
        self._write_file(new_file_content)
    
    def get_full_content(self) -> str:
        """
        Get the entire contents of the MEMORY.md file.
        
        Returns:
            Full content of the memory file
        """
        return self._read_file()
    
    def save_fact(self, fact: str) -> None:
        """
        Add a new fact to the "Important Facts" section.
        
        Facts are added as bullet points. If the section has existing content,
        the new fact is appended.
        
        Args:
            fact: The fact to add
        """
        # Get current section content
        current_content = self.get_section("Important Facts")
        
        # Add timestamp to the fact
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        dated_fact = f"- [{timestamp}] {fact}"
        
        # Append to existing content or create new
        if current_content.strip():
            new_content = f"{current_content}\n{dated_fact}"
        else:
            new_content = dated_fact
        
        self.update_section("Important Facts", new_content)
    
    def save_preference(self, key: str, value: Any) -> None:
        """
        Save or update a preference in the "Preferences" section.
        
        Args:
            key: Preference key (e.g., "Voice Speed")
            value: Preference value
        """
        # Get current preferences
        current_content = self.get_section("Preferences")
        
        # Check if key exists
        pattern = re.compile(rf"^\s*-\s*\*{key}\*:\s*.+$", re.MULTILINE)
        match = pattern.search(current_content)
        
        if match:
            # Update existing preference
            new_preference = f"- **{key}:** {value}"
            new_content = pattern.sub(new_preference, current_content)
        else:
            # Add new preference
            new_preference = f"- **{key}:** {value}"
            new_content = f"{current_content}\n{new_preference}".strip()
        
        self.update_section("Preferences", new_content)
    
    def get_preference(self, key: str) -> Any | None:
        """
        Get a preference value from the "Preferences" section.
        
        Args:
            key: Preference key to retrieve
            
        Returns:
            The preference value, or None if not found
        """
        current_content = self.get_section("Preferences")
        
        # Find the key
        pattern = re.compile(rf"^\s*-\s*\*{re.escape(key)}\*:\s*(.+)$", re.MULTILINE)
        match = pattern.search(current_content)
        
        if match:
            return match.group(1).strip()
        
        return None
    
    def add_task(self, task: str) -> None:
        """
        Add a task to the "Ongoing Tasks" section.
        
        Args:
            task: Task description
        """
        current_content = self.get_section("Ongoing Tasks")
        
        # Add new task as unchecked
        new_task = f"- [ ] {task}"
        
        if current_content.strip():
            new_content = f"{current_content}\n{new_task}"
        else:
            new_content = new_task
        
        self.update_section("Ongoing Tasks", new_content)
    
    def complete_task(self, task_description: str) -> bool:
        """
        Mark a task as completed in the "Ongoing Tasks" section.
        
        Args:
            task_description: Description of the task to mark complete
            
        Returns:
            True if task was found and marked complete, False otherwise
        """
        current_content = self.get_section("Ongoing Tasks")
        
        # Find the task (case insensitive)
        pattern = re.compile(rf"(\- \[ \]) ({re.escape(task_description)})", re.IGNORECASE)
        
        if pattern.search(current_content):
            new_content = pattern.sub(r"- [x] \2", current_content)
            self.update_section("Ongoing Tasks", new_content)
            return True
        
        return False
    
    def update_timestamp(self) -> None:
        """Update the last modified timestamp in the file footer."""
        content = self._read_file()
        
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        new_footer = f"\n---\n*Last Updated: {timestamp}*\n"
        
        # Find and replace the footer
        if "*Last Updated:" in content:
            pattern = re.compile(r"\n---\n\*Last Updated:.*\*\n?", re.IGNORECASE)
            content = pattern.sub(new_footer, content)
        else:
            content = content.rstrip() + new_footer
        
        self._write_file(content)
    
    def get_user_profile(self) -> dict[str, str]:
        """
        Get the user profile as a dictionary.
        
        Returns:
            Dictionary of profile key-value pairs
        """
        profile_content = self.get_section("User Profile")
        profile = {}
        
        # Parse key-value pairs
        pattern = re.compile(r"^\s*-\s*\*\*([^\*]+)\*\*:\s*(.+)$", re.MULTILINE)
        for match in pattern.finditer(profile_content):
            key = match.group(1).strip()
            value = match.group(2).strip()
            profile[key] = value
        
        return profile


# Export public API
__all__ = ["MemoryFileController"]
