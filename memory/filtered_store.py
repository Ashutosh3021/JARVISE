"""
Filtered Vector Memory

Provides importance-based filtering for vector memory storage.
Only stores important conversations, facts, and knowledge.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from memory.chroma_store import VectorStore
from memory.importance import ImportanceScorer, MemoryEntryType


# Patterns for auto-type detection
CODE_PATTERNS = [
    r'```[\s\S]*?```',  # Code blocks
    r'`[^`]+`',  # Inline code
    r'def\s+\w+\(',  # Python function
    r'function\s+\w+\(',  # JS function
    r'class\s+\w+',  # Class definition
    r'import\s+',  # Import statement
    r'from\s+\w+\s+import',  # Python import
]

DECISION_PATTERNS = [
    r'\bwe decided\b',
    r'\bagreed\b',
    r'\bwill use\b',
    r'\bchose\b',
    r'\bchoosing\b',
    r'\bgoing with\b',
    r'\bopted for\b',
    r'\bdecided to\b',
    r'\bsettled on\b',
]

NOTE_PATTERNS = [
    r'^note:',
    r'^remember that',
    r'^personal:',
    r'^reminder:',
    r'^@self',
    r'\bkeep in mind\b',
]

PROJECT_PATTERNS = [
    r'^project:',  # Explicit project marker
    r'/(?:src|lib|app|packages)/',  # Code path
    r'\.git',  # Git repository
]


@dataclass
class MemoryFilter:
    """
    Filter criteria for memory retrieval.
    """
    entry_types: Optional[list[MemoryEntryType]] = None
    projects: Optional[list[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_importance: float = 0.0
    limit: int = 10


@dataclass
class MemoryEntry:
    """
    A memory entry with importance scoring.
    """
    id: str
    content: str
    entry_type: MemoryEntryType
    importance: float
    project: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)


class FilteredMemory:
    """
    Memory store that filters by importance.
    
    Wraps ChromaDB to add importance scoring and filtering.
    Only stores entries that meet the importance threshold.
    """
    
    def __init__(
        self,
        chroma_client: Optional[VectorStore],
        importance_scorer: Optional[ImportanceScorer] = None,
        threshold: float = 0.3,
        collection_name: str = "filtered_memories"
    ):
        """
        Initialize filtered memory.
        
        Args:
            chroma_client: Existing VectorStore instance (or None for no-op)
            importance_scorer: ImportanceScorer instance (created if None)
            threshold: Minimum importance to store (0-1)
            collection_name: ChromaDB collection name
        """
        self._chroma_client = chroma_client
        self._importance_scorer = importance_scorer or ImportanceScorer()
        self.threshold = threshold
        self.collection_name = collection_name
        
        # In-memory index for filtering (ChromaDB doesn't support importance filtering)
        self._memory_index: dict[str, MemoryEntry] = {}
        self._stats = {
            "total_stored": 0,
            "total_rejected": 0,
            "by_type": {},
            "by_project": {},
            "importance_sum": 0.0
        }
    
    def _get_project_name(self) -> Optional[str]:
        """Get current project name from context if available."""
        try:
            from context.project_detector import get_project_root
            root = get_project_root()
            return root.name
        except Exception:
            return None
    
    def add(
        self,
        content: str,
        entry_type: MemoryEntryType = MemoryEntryType.CONVERSATION,
        metadata: Optional[dict] = None,
        project: Optional[str] = None,
        force_store: bool = False
    ) -> Optional[str]:
        """
        Add content to memory if it meets importance threshold.
        
        Args:
            content: Content to store
            entry_type: Type of memory entry
            metadata: Additional metadata
            project: Project name (auto-detected if None)
            force_store: Store regardless of importance
            
        Returns:
            Entry ID if stored, None if rejected
        """
        if metadata is None:
            metadata = {}
        
        # Auto-detect project if not provided
        if project is None:
            project = self._get_project_name()
        
        # Extract metadata
        extracted = self._importance_scorer.extract_metadata(content)
        metadata["extracted_entities"] = extracted.entities
        metadata["extracted_dates"] = extracted.dates
        metadata["extracted_technologies"] = extracted.technologies
        
        # Calculate importance
        importance = self._importance_scorer.score(
            content, entry_type, metadata, project
        )
        
        # Check threshold
        if not force_store and importance < self.threshold:
            self._stats["total_rejected"] += 1
            return None
        
        # Generate entry ID
        entry_id = f"mem_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Create memory entry
        entry = MemoryEntry(
            id=entry_id,
            content=content,
            entry_type=entry_type,
            importance=importance,
            project=project,
            created_at=datetime.now(timezone.utc),
            metadata=metadata
        )
        
        # Store in index
        self._memory_index[entry_id] = entry
        
        # Update stats
        self._stats["total_stored"] += 1
        type_key = entry_type.value
        self._stats["by_type"][type_key] = self._stats["by_type"].get(type_key, 0) + 1
        if project:
            self._stats["by_project"][project] = self._stats["by_project"].get(project, 0) + 1
        self._stats["importance_sum"] += importance
        
        # Also store in ChromaDB if available
        if self._chroma_client:
            try:
                self._chroma_client.save_conversation(
                    user_query=content,
                    assistant_response="",
                    session_id=project or "default",
                    metadata={
                        "entry_id": entry_id,
                        "entry_type": entry_type.value,
                        "importance": importance,
                        **metadata
                    }
                )
            except Exception:
                pass  # ChromaDB storage is best-effort
        
        return entry_id
    
    def search(
        self,
        query: str,
        filter: Optional[MemoryFilter] = None,
        include_rejected: bool = False
    ) -> list[MemoryEntry]:
        """
        Search memory with filters.
        
        Args:
            query: Search query
            filter: Optional filter criteria
            include_rejected: Include entries below threshold
            
        Returns:
            List of matching memory entries, sorted by relevance + importance
        """
        if filter is None:
            filter = MemoryFilter()
        
        results = []
        
        for entry in self._memory_index.values():
            # Apply filters
            if filter.entry_types and entry.entry_type not in filter.entry_types:
                continue
            
            if filter.projects and entry.project not in filter.projects:
                continue
            
            if filter.min_importance > 0 and entry.importance < filter.min_importance:
                continue
            
            if filter.date_from and entry.created_at < filter.date_from:
                continue
            
            if filter.date_to and entry.created_at > filter.date_to:
                continue
            
            results.append(entry)
        
        # Sort by importance (higher first)
        results.sort(key=lambda e: e.importance, reverse=True)
        
        # Apply limit
        return results[:filter.limit]
    
    def get_by_project(self, project: str) -> list[MemoryEntry]:
        """
        Get all memories for a specific project.
        
        Args:
            project: Project name
            
        Returns:
            List of memory entries for the project
        """
        return [
            entry for entry in self._memory_index.values()
            if entry.project == project
        ]
    
    def get_recent(self, limit: int = 10) -> list[MemoryEntry]:
        """
        Get most recent memories.
        
        Args:
            limit: Maximum number of entries
            
        Returns:
            List of recent memories
        """
        sorted_entries = sorted(
            self._memory_index.values(),
            key=lambda e: e.created_at,
            reverse=True
        )
        return sorted_entries[:limit]
    
    def delete(self, entry_id: str) -> bool:
        """
        Delete a memory entry.
        
        Args:
            entry_id: ID of entry to delete
            
        Returns:
            True if deleted, False if not found
        """
        if entry_id in self._memory_index:
            entry = self._memory_index.pop(entry_id)
            
            # Update stats
            self._stats["total_stored"] -= 1
            type_key = entry.entry_type.value
            if self._stats["by_type"].get(type_key, 0) > 0:
                self._stats["by_type"][type_key] -= 1
            if entry.project and self._stats["by_project"].get(entry.project, 0) > 0:
                self._stats["by_project"][entry.project] -= 1
            self._stats["importance_sum"] -= entry.importance
            
            return True
        return False
    
    def _detect_entry_type(self, content: str) -> MemoryEntryType:
        """
        Auto-detect entry type from content.
        
        Args:
            content: Content to analyze
            
        Returns:
            Detected MemoryEntryType
        """
        content_lower = content.lower()
        
        # Check for code
        for pattern in CODE_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return MemoryEntryType.CODE
        
        # Check for decisions
        for pattern in DECISION_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return MemoryEntryType.DECISION
        
        # Check for notes
        for pattern in NOTE_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                return MemoryEntryType.NOTE
        
        # Check for project references
        for pattern in PROJECT_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return MemoryEntryType.PROJECT
        
        # Default to conversation
        return MemoryEntryType.CONVERSATION
    
    def _detect_project(self, content: str) -> Optional[str]:
        """
        Auto-detect project from content.
        
        Args:
            content: Content to analyze
            
        Returns:
            Detected project name or None
        """
        # Try to get current project from context
        project = self._get_project_name()
        if project:
            return project
        
        # Try to extract from content
        # Look for paths like /project-name or project_name
        path_match = re.search(r'[/\-]([a-zA-Z][a-zA-Z0-9_-]+)/', content)
        if path_match:
            return path_match.group(1)
        
        return None
    
    def add_with_auto_tagging(
        self,
        content: str,
        entry_type: Optional[MemoryEntryType] = None,
        metadata: Optional[dict] = None,
        project: Optional[str] = None,
        force_store: bool = False
    ) -> Optional[str]:
        """
        Add content with automatic type and project detection.
        
        Args:
            content: Content to store
            entry_type: Type (auto-detected if None)
            metadata: Additional metadata
            project: Project (auto-detected if None)
            force_store: Store regardless of importance
            
        Returns:
            Entry ID if stored, None if rejected
        """
        # Auto-detect entry type
        if entry_type is None:
            entry_type = self._detect_entry_type(content)
        
        # Auto-detect project
        if project is None:
            project = self._detect_project(content)
        
        # Ensure metadata exists
        if metadata is None:
            metadata = {}
        
        # Add detected type to metadata
        metadata["detected_type"] = entry_type.value
        metadata["auto_detected"] = True
        
        # Add word count
        metadata["word_count"] = len(content.split())
        
        # Check for code
        has_code = any(
            re.search(pattern, content, re.IGNORECASE)
            for pattern in CODE_PATTERNS
        )
        metadata["has_code"] = has_code
        
        return self.add(
            content=content,
            entry_type=entry_type,
            metadata=metadata,
            project=project,
            force_store=force_store
        )
    
    def bulk_import(
        self,
        entries: list[dict[str, Any]],
        auto_tag: bool = True
    ) -> dict[str, Any]:
        """
        Import multiple entries with automatic type detection.
        
        Args:
            entries: List of entries with 'content' and optional 'entry_type', 'project', 'metadata'
            auto_tag: Whether to auto-detect entry types
            
        Returns:
            Summary of import results
        """
        stored = 0
        rejected = 0
        entry_ids = []
        
        for entry in entries:
            content = entry.get("content")
            if not content:
                rejected += 1
                continue
            
            entry_type = entry.get("entry_type")
            if auto_tag and entry_type is None:
                entry_type = self._detect_entry_type(content)
            elif entry_type and isinstance(entry_type, str):
                entry_type = MemoryEntryType(entry_type)
            
            project = entry.get("project")
            metadata = entry.get("metadata", {})
            
            result = self.add_with_auto_tagging(
                content=content,
                entry_type=entry_type,
                metadata=metadata,
                project=project
            )
            
            if result:
                stored += 1
                entry_ids.append(result)
            else:
                rejected += 1
        
        return {
            "stored": stored,
            "rejected": rejected,
            "total": len(entries),
            "entry_ids": entry_ids
        }
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get memory statistics.
        
        Returns:
            Dictionary with memory stats
        """
        total = self._stats["total_stored"]
        avg_importance = (
            self._stats["importance_sum"] / total
            if total > 0 else 0.0
        )
        
        return {
            "total": total,
            "total_rejected": self._stats["total_rejected"],
            "rejection_rate": (
                self._stats["total_rejected"] / 
                (self._stats["total_stored"] + self._stats["total_rejected"])
                if (self._stats["total_stored"] + self._stats["total_rejected"]) > 0 
                else 0.0
            ),
            "by_type": self._stats["by_type"],
            "by_project": self._stats["by_project"],
            "average_importance": round(avg_importance, 3),
            "threshold": self.threshold
        }


__all__ = [
    "MemoryFilter",
    "MemoryEntry",
    "FilteredMemory",
]
