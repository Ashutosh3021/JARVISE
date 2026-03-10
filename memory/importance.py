"""
Importance Scoring System

Provides importance scoring for memory entries to filter out unimportant
conversations and focus on storing knowledge that matters.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class MemoryEntryType(Enum):
    """Types of memory entries."""
    CONVERSATION = "conversation"
    FACT = "fact"
    CODE = "code"
    PROJECT = "project"
    NOTE = "note"
    DECISION = "decision"


# Importance keywords that indicate high-value content
IMPORTANCE_KEYWORDS = [
    "important", "remember", "don't forget", "key", "critical",
    "significant", "essential", "must remember", "never forget",
    "worth noting", "note that", "keep in mind", "as a reminder"
]

# Decision language patterns
DECISION_KEYWORDS = [
    "decided", "agreed", "will use", "choose", "chose",
    "decision", "resolution", "conclusion", "settled on",
    "going with", "opted for", "selected"
]

# Personal note markers
PERSONAL_NOTE_MARKERS = [
    r"note:", r"remember that", r"personal:", r"my note:",
    r"reminder:", r"to self:", r"@self"
]


@dataclass
class ExtractedMetadata:
    """Metadata extracted from memory content."""
    dates: list[str]
    entities: list[str]
    technologies: list[str]
    project_names: list[str]


class ImportanceScorer:
    """
    Scores the importance of memory content on a 0-1 scale.
    
    Scoring factors:
    - Explicit importance keywords
    - Question marks (indicates learning)
    - Code blocks
    - Decision language
    - Project references
    - Personal notes
    - Content length (prefer medium length)
    """
    
    # Common technology names for entity extraction
    TECHNOLOGIES = {
        "python", "javascript", "typescript", "java", "rust", "go",
        "react", "vue", "angular", "nextjs", "django", "flask",
        "fastapi", "express", "node", "postgresql", "mysql", "mongodb",
        "redis", "docker", "kubernetes", "aws", "azure", "gcp",
        "git", "github", "gitlab", "chromadb", "ollama", "llama"
    }
    
    def __init__(self, default_threshold: float = 0.3):
        """
        Initialize the importance scorer.
        
        Args:
            default_threshold: Minimum score to consider worth storing
        """
        self.default_threshold = default_threshold
        self._importance_keywords_re = re.compile(
            r'\b(' + '|'.join(re.escape(k) for k in IMPORTANCE_KEYWORDS) + r')\b',
            re.IGNORECASE
        )
        self._decision_keywords_re = re.compile(
            r'\b(' + '|'.join(re.escape(k) for k in DECISION_KEYWORDS) + r')\b',
            re.IGNORECASE
        )
        self._personal_note_re = re.compile(
            r'^(' + '|'.join(m.strip('^') for m in PERSONAL_NOTE_MARKERS) + r')',
            re.IGNORECASE | re.MULTILINE
        )
        self._code_block_re = re.compile(r'```[\s\S]*?```|`[^`]+`')
        self._question_re = re.compile(r'\?+')
    
    def score(
        self,
        content: str,
        entry_type: MemoryEntryType,
        metadata: Optional[dict] = None,
        project_name: Optional[str] = None
    ) -> float:
        """
        Calculate importance score for content.
        
        Args:
            content: The text content to score
            entry_type: Type of memory entry
            metadata: Additional metadata (optional)
            project_name: Current project name (optional)
            
        Returns:
            Importance score between 0 and 1
        """
        if not content or not content.strip():
            return 0.0
        
        score = 0.0
        
        # Check for explicit importance keywords (+0.3)
        if self._importance_keywords_re.search(content):
            score += 0.3
        
        # Check for question marks - indicates learning (+0.1)
        if self._question_re.search(content):
            score += 0.1
        
        # Code blocks - important for CODE type (+0.2 for CODE)
        if entry_type == MemoryEntryType.CODE:
            if self._code_block_re.search(content):
                score += 0.2
        
        # Decision language (+0.3 for DECISION type)
        if entry_type == MemoryEntryType.DECISION:
            if self._decision_keywords_re.search(content):
                score += 0.3
        
        # Project references (+0.2)
        if project_name and project_name.lower() in content.lower():
            score += 0.2
        
        # Personal note markers (+0.3)
        if self._personal_note_re.search(content):
            score += 0.3
        
        # Length scoring: prefer medium (50-500 chars)
        length = len(content)
        if 50 <= length <= 500:
            score += 0.2  # Bonus for ideal length
        elif length < 20:
            score -= 0.1  # Penalty for too short
        elif length > 2000:
            score -= 0.1  # Penalty for too long
        
        # Type-based base scores
        type_scores = {
            MemoryEntryType.DECISION: 0.2,
            MemoryEntryType.FACT: 0.2,
            MemoryEntryType.PROJECT: 0.15,
            MemoryEntryType.NOTE: 0.15,
            MemoryEntryType.CODE: 0.1,
            MemoryEntryType.CONVERSATION: 0.0,
        }
        score += type_scores.get(entry_type, 0.0)
        
        # Clamp to 0-1 range
        return max(0.0, min(1.0, score))
    
    def is_worth_storing(
        self,
        content: str,
        entry_type: MemoryEntryType,
        metadata: Optional[dict] = None,
        project_name: Optional[str] = None,
        threshold: Optional[float] = None
    ) -> bool:
        """
        Check if content is worth storing based on importance threshold.
        
        Args:
            content: Content to evaluate
            entry_type: Type of entry
            metadata: Additional metadata
            project_name: Current project name
            threshold: Custom threshold (uses default if None)
            
        Returns:
            True if importance score meets threshold
        """
        threshold = threshold or self.default_threshold
        score = self.score(content, entry_type, metadata, project_name)
        return score >= threshold
    
    def extract_metadata(self, content: str) -> ExtractedMetadata:
        """
        Extract metadata from content.
        
        Args:
            content: Content to analyze
            
        Returns:
            ExtractedMetadata with extracted information
        """
        # Extract dates
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}',
        ]
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, content, re.IGNORECASE))
        
        # Extract technologies
        content_lower = content.lower()
        technologies = [
            tech for tech in self.TECHNOLOGIES
            if tech in content_lower
        ]
        
        # Extract potential entities (capitalized words that aren't at start)
        entity_pattern = r'(?<!^)(?<![.\s])[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*'
        potential_entities = re.findall(entity_pattern, content)
        # Filter out common words
        entities = [e for e in potential_entities if len(e) > 2]
        
        # Extract potential project names (paths like /project-name or project_name)
        project_pattern = r'[/\-]([a-zA-Z][a-zA-Z0-9_-]+)'
        project_names = re.findall(project_pattern, content)
        
        return ExtractedMetadata(
            dates=list(set(dates)),
            entities=entities[:5],  # Limit to 5
            technologies=list(set(technologies)),
            project_names=list(set(project_names))[:3]  # Limit to 3
        )


def calculate_importance(
    content: str,
    entry_type: MemoryEntryType,
    project_name: Optional[str] = None
) -> float:
    """
    Convenience function to calculate importance.
    
    Args:
        content: Content to score
        entry_type: Type of entry
        project_name: Current project name
        
    Returns:
        Importance score (0-1)
    """
    scorer = ImportanceScorer()
    return scorer.score(content, entry_type, project_name=project_name)


__all__ = [
    "MemoryEntryType",
    "ImportanceScorer",
    "ExtractedMetadata",
    "calculate_importance",
]
