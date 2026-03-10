"""
Memory Management REST Routes

Provides REST endpoints for memory operations:
- GET /api/memory - List memories
- GET /api/memory/{id} - Get specific memory
- POST /api/memory - Create new memory entry
- DELETE /api/memory/{id} - Delete memory
- GET /api/memory.md - Read MEMORY.md file
- PUT /api/memory.md - Write MEMORY.md file
- GET /api/memory/stats - Get memory statistics
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from loguru import logger

from core.config import Config
from memory.MemoryManager import MemoryManager


router = APIRouter()


# Global memory manager instance
_memory_manager: MemoryManager | None = None


def get_memory_manager() -> MemoryManager:
    """Get or create the memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        config = Config()
        _memory_manager = MemoryManager(config)
    return _memory_manager


# Request/Response models
class MemoryEntry(BaseModel):
    """Memory entry model."""
    query: str
    response: str
    session_id: str = "default"
    metadata: dict[str, Any] | None = None


class FactRequest(BaseModel):
    """Request model for saving a fact."""
    fact: str


class MemoryFileUpdate(BaseModel):
    """Request model for updating MEMORY.md."""
    content: str


@router.get("/memory")
async def list_memories(session_id: str = "default", limit: int = 50) -> dict[str, Any]:
    """
    List memories from the vector store.
    
    Args:
        session_id: Filter by session ID
        limit: Maximum number of results
        
    Returns:
        List of memory entries
    """
    try:
        manager = get_memory_manager()
        memories = manager.get_session_history(session_id=session_id, limit=limit)
        return {
            "status": "success",
            "session_id": session_id,
            "count": len(memories),
            "memories": memories
        }
    except Exception as e:
        logger.error(f"Error listing memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/{memory_id}")
async def get_memory(memory_id: str) -> dict[str, Any]:
    """
    Get a specific memory by ID.
    
    Args:
        memory_id: The memory entry ID
        
    Returns:
        Memory entry details
    """
    # Note: VectorStore doesn't have a direct get by ID method
    # This would require adding that method to the store
    try:
        manager = get_memory_manager()
        # Get all and find the matching one
        memories = manager.get_session_history(limit=1000)
        for mem in memories:
            if mem.get("id") == memory_id:
                return {
                    "status": "success",
                    "memory": mem
                }
        raise HTTPException(status_code=404, detail="Memory not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory")
async def create_memory(entry: MemoryEntry) -> dict[str, Any]:
    """
    Create a new memory entry.
    
    Args:
        entry: Memory entry data
        
    Returns:
        Created memory entry with ID
    """
    try:
        manager = get_memory_manager()
        memory_id = manager.save_conversation(
            user_query=entry.query,
            assistant_response=entry.response,
            session_id=entry.session_id,
            metadata=entry.metadata
        )
        return {
            "status": "success",
            "id": memory_id,
            "message": "Memory saved successfully"
        }
    except Exception as e:
        logger.error(f"Error creating memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memory/{memory_id}")
async def delete_memory(memory_id: str) -> dict[str, Any]:
    """
    Delete a memory entry.
    
    Note: ChromaDB doesn't support direct deletion by ID without
    additional implementation. This clears the session instead.
    
    Args:
        memory_id: The memory entry ID or session ID
        
    Returns:
        Deletion status
    """
    try:
        manager = get_memory_manager()
        # Try to delete by session
        deleted = manager.delete_session(memory_id)
        return {
            "status": "success",
            "deleted": deleted,
            "message": f"Deleted {deleted} entries"
        }
    except Exception as e:
        logger.error(f"Error deleting memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory.md")
async def get_memory_file() -> dict[str, Any]:
    """
    Get the content of MEMORY.md file.
    
    Returns:
        MEMORY.md file content
    """
    try:
        manager = get_memory_manager()
        content = manager.get_file_context()
        return {
            "status": "success",
            "content": content
        }
    except Exception as e:
        logger.error(f"Error reading memory file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/memory.md")
async def update_memory_file(update: MemoryFileUpdate) -> dict[str, Any]:
    """
    Update the MEMORY.md file content.
    
    Args:
        update: New content for MEMORY.md
        
    Returns:
        Update status
    """
    try:
        manager = get_memory_manager()
        # Use the internal _write_file method via the controller
        manager.memory_file._write_file(update.content)
        return {
            "status": "success",
            "message": "Memory file updated successfully"
        }
    except Exception as e:
        logger.error(f"Error updating memory file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/fact")
async def save_fact(request: FactRequest) -> dict[str, Any]:
    """
    Save an important fact to MEMORY.md.
    
    Args:
        request: Fact to save
        
    Returns:
        Save status
    """
    try:
        manager = get_memory_manager()
        manager.save_fact(request.fact)
        return {
            "status": "success",
            "message": "Fact saved successfully"
        }
    except Exception as e:
        logger.error(f"Error saving fact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/stats")
async def get_memory_stats() -> dict[str, Any]:
    """
    Get memory system statistics.
    
    Returns:
        Statistics about vector store and memory file
    """
    try:
        manager = get_memory_manager()
        stats = manager.get_stats()
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        # Return basic stats even if full stats fail
        return {
            "status": "success",
            "stats": {
                "error": str(e),
                "vector_store": {"error": "Not initialized"},
                "memory_file": {"error": "Not initialized"}
            }
        }


# Filtered memory endpoints

from memory.filtered_store import FilteredMemory, MemoryFilter, MemoryEntry
from memory.importance import MemoryEntryType

# Global filtered memory instance
_filtered_memory: FilteredMemory | None = None


def get_filtered_memory() -> FilteredMemory:
    """Get or create the filtered memory instance."""
    global _filtered_memory
    if _filtered_memory is None:
        _filtered_memory = FilteredMemory(
            chroma_client=None,
            threshold=0.3
        )
    return _filtered_memory


class AddMemoryRequest(BaseModel):
    """Request model for adding a memory entry."""
    content: str
    entry_type: str = "conversation"
    metadata: dict[str, Any] | None = None
    project: str | None = None
    force_store: bool = False


class SearchMemoryRequest(BaseModel):
    """Request model for searching memory."""
    q: str
    entry_type: str | None = None
    project: str | None = None
    min_importance: float = 0.0
    limit: int = 10


class ClearMemoryRequest(BaseModel):
    """Request model for clearing memory."""
    project: str | None = None


@router.post("/memory/add")
async def add_memory(request: AddMemoryRequest) -> dict[str, Any]:
    """
    Add a memory entry with importance filtering.
    
    Args:
        request: Memory entry data
        
    Returns:
        Entry ID and importance score
    """
    try:
        fm = get_filtered_memory()
        
        # Parse entry type
        entry_type = MemoryEntryType(request.entry_type)
        
        # Add to filtered memory
        entry_id = fm.add(
            content=request.content,
            entry_type=entry_type,
            metadata=request.metadata,
            project=request.project,
            force_store=request.force_store
        )
        
        if entry_id is None:
            return {
                "status": "rejected",
                "message": "Content below importance threshold",
                "entry_id": None,
                "importance_score": None
            }
        
        # Get the entry to return importance
        results = fm.search(request.content, MemoryFilter(limit=1))
        importance = results[0].importance if results else 0.0
        
        return {
            "status": "success",
            "entry_id": entry_id,
            "importance_score": importance,
            "message": "Memory stored successfully"
        }
    except Exception as e:
        logger.error(f"Error adding memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/search")
async def search_memory(
    q: str,
    entry_type: str | None = None,
    project: str | None = None,
    min_importance: float = 0.0,
    limit: int = 10
) -> dict[str, Any]:
    """
    Search memory with filters.
    
    Args:
        q: Search query
        entry_type: Filter by entry type
        project: Filter by project
        min_importance: Minimum importance threshold
        limit: Maximum results
        
    Returns:
        List of matching memory entries
    """
    try:
        fm = get_filtered_memory()
        
        # Build filter
        filter = MemoryFilter(
            entry_types=[MemoryEntryType(entry_type)] if entry_type else None,
            projects=[project] if project else None,
            min_importance=min_importance,
            limit=limit
        )
        
        results = fm.search(q, filter)
        
        return {
            "status": "success",
            "count": len(results),
            "results": [
                {
                    "id": r.id,
                    "content": r.content,
                    "entry_type": r.entry_type.value,
                    "importance": r.importance,
                    "project": r.project,
                    "created_at": r.created_at.isoformat(),
                    "metadata": r.metadata
                }
                for r in results
            ]
        }
    except Exception as e:
        logger.error(f"Error searching memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/recent")
async def get_recent_memory(limit: int = 10) -> dict[str, Any]:
    """
    Get recent memory entries.
    
    Args:
        limit: Maximum number of entries
        
    Returns:
        List of recent memories
    """
    try:
        fm = get_filtered_memory()
        results = fm.get_recent(limit=limit)
        
        return {
            "status": "success",
            "count": len(results),
            "results": [
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
        }
    except Exception as e:
        logger.error(f"Error getting recent memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memory/{entry_id}")
async def delete_memory_entry(entry_id: str) -> dict[str, Any]:
    """
    Delete a specific memory entry.
    
    Args:
        entry_id: ID of entry to delete
        
    Returns:
        Deletion status
    """
    try:
        fm = get_filtered_memory()
        deleted = fm.delete(entry_id)
        
        return {
            "status": "success" if deleted else "not_found",
            "deleted": deleted,
            "message": f"Entry {'deleted' if deleted else 'not found'}"
        }
    except Exception as e:
        logger.error(f"Error deleting memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/clear")
async def clear_memory(request: ClearMemoryRequest) -> dict[str, Any]:
    """
    Clear memory entries.
    
    Args:
        request: Clear request with optional project filter
        
    Returns:
        Clear status
    """
    try:
        fm = get_filtered_memory()
        
        if request.project:
            # Clear specific project
            entries = fm.get_by_project(request.project)
            deleted = 0
            for entry in entries:
                if fm.delete(entry.id):
                    deleted += 1
        else:
            # Clear all - need to get all entries first
            entries = fm.get_recent(limit=1000)
            deleted = 0
            for entry in entries:
                if fm.delete(entry.id):
                    deleted += 1
        
        return {
            "status": "success",
            "deleted": deleted,
            "message": f"Cleared {deleted} entries"
        }
    except Exception as e:
        logger.error(f"Error clearing memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/filtered-stats")
async def get_filtered_stats() -> dict[str, Any]:
    """
    Get filtered memory statistics.
    
    Returns:
        Statistics about filtered memory
    """
    try:
        fm = get_filtered_memory()
        stats = fm.get_stats()
        
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting filtered stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ["router"]
