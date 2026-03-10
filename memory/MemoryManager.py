"""
JARVIS Memory Manager

Unified interface for both vector store (ChromaDB) and file-based (MEMORY.md) storage.
Includes filtered memory for importance-based storage.
"""

from typing import Any

from core.config import Config

from memory.chroma_store import VectorStore
from memory.filtered_store import FilteredMemory, MemoryFilter
from memory.importance import MemoryEntryType
from memory.memory_file import MemoryFileController


class MemoryManager:
    """
    Unified memory manager providing access to both vector and file-based storage.
    
    Combines:
    - ChromaDB vector store for semantic search of past conversations
    - MEMORY.md file for persistent human-editable information
    
    Usage:
        manager = MemoryManager(config)
        
        # Save a conversation (goes to vector store)
        manager.save_conversation("What's the weather?", "It's sunny today!")
        
        # Save important facts (goes to MEMORY.md)
        manager.save_fact("User prefers metric units")
        
        # Get combined context for LLM prompts
        context = manager.get_context("weather forecast")
    """
    
    def __init__(self, config: Config):
        """
        Initialize the memory manager.
        
        Args:
            config: JARVIS configuration object
        """
        self.config = config
        self._vector_store = None
        self._memory_file = None
        self._filtered_memory = None
    
    @property
    def vector_store(self) -> VectorStore:
        """Lazy-initialize the vector store."""
        if self._vector_store is None:
            self._vector_store = VectorStore(
                persist_directory=self.config.chroma_persist_directory
            )
        return self._vector_store
    
    @property
    def memory_file(self) -> MemoryFileController:
        """Lazy-initialize the memory file controller."""
        if self._memory_file is None:
            self._memory_file = MemoryFileController(
                file_path=self.config.memory_file
            )
        return self._memory_file
    
    @property
    def filtered_memory(self) -> FilteredMemory:
        """Lazy-initialize the filtered memory."""
        if self._filtered_memory is None:
            self._filtered_memory = FilteredMemory(
                chroma_client=self.vector_store,
                threshold=0.3
            )
        return self._filtered_memory
    
    def save_conversation(
        self,
        user_query: str,
        assistant_response: str,
        session_id: str = "default",
        metadata: dict[str, Any] | None = None
    ) -> str:
        """
        Save a conversation exchange to the vector store.
        
        Args:
            user_query: The user's query/input
            assistant_response: The assistant's response
            session_id: Identifier for the conversation session
            metadata: Optional additional metadata
            
        Returns:
            The ID of the stored conversation entry
        """
        return self.vector_store.save_conversation(
            user_query=user_query,
            assistant_response=assistant_response,
            session_id=session_id,
            metadata=metadata
        )
    
    def get_vector_context(
        self,
        query: str,
        n_results: int = 3,
        session_id: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Get relevant context from past conversations using vector similarity.
        
        Args:
            query: Query to search for relevant context
            n_results: Number of results to return
            session_id: Optional filter for specific session
            
        Returns:
            List of relevant conversation entries
        """
        return self.vector_store.get_context(
            query=query,
            n_results=n_results,
            session_id=session_id
        )
    
    def get_file_context(self) -> str:
        """
        Get content from the MEMORY.md file.
        
        Returns:
            Full content of the memory file
        """
        return self.memory_file.get_full_content()
    
    def get_user_profile(self) -> dict[str, str]:
        """
        Get the user profile from MEMORY.md.
        
        Returns:
            Dictionary of profile key-value pairs
        """
        return self.memory_file.get_user_profile()
    
    def get_preferences(self) -> dict[str, Any]:
        """
        Get user preferences from MEMORY.md.
        
        Returns:
            Dictionary of preference key-value pairs
        """
        preferences = {}
        
        # Common preference keys
        keys = ["Voice Speed", "Model", "Wake Word", "TTS Voice"]
        
        for key in keys:
            value = self.memory_file.get_preference(key)
            if value is not None:
                preferences[key] = value
        
        return preferences
    
    def get_context(
        self,
        query: str,
        n_vector_results: int = 3,
        include_file: bool = True
    ) -> dict[str, Any]:
        """
        Get combined context for LLM prompts.
        
        Retrieves both:
        1. Relevant past conversations from vector store
        2. Full MEMORY.md file content
        
        Args:
            query: Query to search for relevant context
            n_vector_results: Number of vector search results
            include_file: Whether to include MEMORY.md content
            
        Returns:
            Dictionary with 'vector_context' and 'file_context' keys
        """
        context = {
            "vector_context": self.get_vector_context(query, n_vector_results),
            "file_context": self.get_file_context() if include_file else None,
            "user_profile": self.get_user_profile(),
            "preferences": self.get_preferences(),
        }
        
        return context
    
    def format_context_for_prompt(
        self,
        query: str,
        n_vector_results: int = 3
    ) -> str:
        """
        Format context as a string for inclusion in LLM prompts.
        
        Args:
            query: Original user query
            n_vector_results: Number of vector search results
            
        Returns:
            Formatted context string
        """
        context = self.get_context(query, n_vector_results)
        
        parts = []
        
        # Add relevant past conversations
        if context["vector_context"]:
            parts.append("## Relevant Past Conversations\n")
            for entry in context["vector_context"]:
                parts.append(f"- {entry['metadata']['user_query']}")
                parts.append(f"  Assistant: {entry['metadata']['assistant_response']}\n")
        
        # Add user profile
        if context["user_profile"]:
            parts.append("\n## User Profile\n")
            for key, value in context["user_profile"].items():
                parts.append(f"- {key}: {value}")
        
        # Add preferences
        if context["preferences"]:
            parts.append("\n## User Preferences\n")
            for key, value in context["preferences"].items():
                parts.append(f"- {key}: {value}")
        
        # Add important facts from MEMORY.md
        try:
            important_facts = self.memory_file.get_section("Important Facts")
            if important_facts.strip():
                parts.append("\n## Important Facts\n")
                parts.append(important_facts)
        except Exception:
            pass
        
        return "\n".join(parts)
    
    def save_fact(self, fact: str) -> None:
        """
        Save an important fact to MEMORY.md.
        
        Args:
            fact: The fact to save
        """
        self.memory_file.save_fact(fact)
        self.memory_file.update_timestamp()
    
    def save_preference(self, key: str, value: Any) -> None:
        """
        Save or update a user preference in MEMORY.md.
        
        Args:
            key: Preference key
            value: Preference value
        """
        self.memory_file.save_preference(key, value)
        self.memory_file.update_timestamp()
    
    def add_task(self, task: str) -> None:
        """
        Add a task to the ongoing tasks list in MEMORY.md.
        
        Args:
            task: Task description
        """
        self.memory_file.add_task(task)
        self.memory_file.update_timestamp()
    
    def complete_task(self, task: str) -> bool:
        """
        Mark a task as completed in MEMORY.md.
        
        Args:
            task: Task description
            
        Returns:
            True if task was found and marked complete
        """
        result = self.memory_file.complete_task(task)
        if result:
            self.memory_file.update_timestamp()
        return result
    
    def get_session_history(
        self,
        session_id: str = "default",
        limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Get conversation history for a specific session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of entries
            
        Returns:
            List of conversation entries
        """
        return self.vector_store.get_session_history(session_id, limit)
    
    def delete_session(self, session_id: str) -> int:
        """
        Delete all data for a specific session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Number of entries deleted
        """
        return self.vector_store.delete_session(session_id)
    
    def add_filtered(
        self,
        content: str,
        entry_type: str = "conversation",
        project: str | None = None,
        force_store: bool = False
    ) -> str | None:
        """
        Add content to filtered memory with importance scoring.
        
        Args:
            content: Content to store
            entry_type: Type of entry (conversation, fact, code, project, note, decision)
            project: Project name (auto-detected if None)
            force_store: Store regardless of importance threshold
            
        Returns:
            Entry ID if stored, None if rejected
        """
        entry_type_enum = MemoryEntryType(entry_type)
        return self.filtered_memory.add(
            content=content,
            entry_type=entry_type_enum,
            project=project,
            force_store=force_store
        )
    
    def get_important_context(
        self,
        query: str,
        project: str | None = None,
        limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Get high-importance memories for context.
        
        Prioritizes decisions and facts, returns most relevant for current project.
        
        Args:
            query: Search query
            project: Filter by project (uses current project if None)
            limit: Maximum number of results
            
        Returns:
            List of important memory entries
        """
        # Build filter prioritizing important types
        filter = MemoryFilter(
            entry_types=[
                MemoryEntryType.DECISION,
                MemoryEntryType.FACT,
                MemoryEntryType.NOTE,
                MemoryEntryType.PROJECT,
                MemoryEntryType.CODE,
                MemoryEntryType.CONVERSATION
            ],
            projects=[project] if project else None,
            min_importance=0.3,  # Only get important entries
            limit=limit
        )
        
        results = self.filtered_memory.search(query, filter)
        
        return [
            {
                "id": r.id,
                "content": r.content,
                "entry_type": r.entry_type.value,
                "importance": r.importance,
                "project": r.project,
                "created_at": r.created_at.isoformat()
            }
            for r in results
        ]
    
    def get_filtered_stats(self) -> dict[str, Any]:
        """
        Get filtered memory statistics.
        
        Returns:
            Statistics about filtered memory
        """
        return self.filtered_memory.get_stats()
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about the memory system.
        
        Returns:
            Dictionary with memory statistics
        """
        return {
            "vector_store": self.vector_store.get_stats(),
            "memory_file": {
                "path": str(self.memory_file.file_path),
                "exists": self.memory_file.file_path.exists(),
            }
        }


# Export public API
__all__ = ["MemoryManager"]
