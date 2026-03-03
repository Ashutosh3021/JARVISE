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
        manager.memory_file.write_full_content(update.content)
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


__all__ = ["router"]
