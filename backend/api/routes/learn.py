"""
Learning REST Routes

Provides REST endpoints for learning features:
- POST /api/learn/correct - Learn from user corrections
- GET /api/learn/preferences - Get stored preferences
- POST /api/learn/forget - Forget a learned preference
- GET /api/learn/stats - Get learning statistics
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

router = APIRouter()


# Request models
class CorrectionRequest(BaseModel):
    """Request to learn from a user correction."""
    trigger: str
    correct_tool: str
    correct_args: dict | None = None
    confidence: int = 7


class ForgetRequest(BaseModel):
    """Request to forget a learned preference."""
    trigger: str


# Global references
_global_tool_registry = None
_global_command_router = None


def set_tool_registry(registry):
    """Set the global tool registry for learning stats."""
    global _global_tool_registry
    _global_tool_registry = registry


def set_command_router(router):
    """Set the global command router for preference learning."""
    global _global_command_router
    _global_command_router = router


@router.post("/learn/correct")
async def learn_correction(request: CorrectionRequest) -> dict[str, Any]:
    """
    Learn from a user correction.
    
    When the user corrects JARVIS's tool choice, this endpoint
    records the preference for future routing.
    """
    try:
        if _global_command_router is None:
            raise HTTPException(status_code=500, detail="Router not initialized")
        
        _global_command_router.learn_correction(
            trigger=request.trigger,
            correct_tool=request.correct_tool,
            correct_args=request.correct_args,
            confidence=request.confidence
        )
        
        return {
            "success": True,
            "message": f"Learned: '{request.trigger}' -> {request.correct_tool}"
        }
        
    except Exception as e:
        logger.error(f"Error learning correction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learn/preferences")
async def get_preferences() -> dict[str, Any]:
    """
    Get all stored preferences.
    
    Returns:
        List of all learned preferences
    """
    try:
        if _global_command_router is None:
            raise HTTPException(status_code=500, detail="Router not initialized")
        
        prefs = _global_command_router._preference_memory
        if prefs is None:
            return {"preferences": [], "message": "Preference memory not enabled"}
        
        preferences = prefs.list_preferences()
        
        return {
            "preferences": [
                {
                    "trigger": p.trigger,
                    "tool_name": p.tool_name,
                    "tool_args": p.tool_args,
                    "confidence": p.confidence,
                    "use_count": p.use_count,
                    "last_used": p.last_used.isoformat(),
                }
                for p in preferences
            ],
            "count": len(preferences)
        }
        
    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learn/forget")
async def forget_preference(request: ForgetRequest) -> dict[str, Any]:
    """
    Forget a learned preference.
    
    Removes a preference from memory.
    """
    try:
        if _global_command_router is None:
            raise HTTPException(status_code=500, detail="Router not initialized")
        
        success = _global_command_router.forget_preference(request.trigger)
        
        return {
            "success": success,
            "message": f"{'Removed' if success else 'Not found'}: {request.trigger}"
        }
        
    except Exception as e:
        logger.error(f"Error forgetting preference: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learn/stats")
async def get_learning_stats() -> dict[str, Any]:
    """
    Get learning system statistics.
    
    Returns:
        Stats from cache, retry engine, and preferences
    """
    try:
        stats = {
            "cache": None,
            "retry": None,
            "preferences": None,
        }
        
        # Get cache stats
        if _global_tool_registry is not None:
            stats["cache"] = _global_tool_registry.get_cache_stats()
            stats["retry"] = _global_tool_registry.get_retry_stats()
        
        # Get preference stats
        if _global_command_router is not None:
            stats["preferences"] = _global_command_router.get_preference_stats()
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting learning stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learn/cache/clear")
async def clear_cache(tool_name: str | None = None) -> dict[str, Any]:
    """
    Clear tool cache.
    
    Args:
        tool_name: Optional specific tool to clear, or all if not provided
    """
    try:
        if _global_tool_registry is None:
            raise HTTPException(status_code=500, detail="Tool registry not initialized")
        
        count = _global_tool_registry.invalidate_cache(tool_name)
        
        return {
            "success": True,
            "cleared": count,
            "message": f"Cleared {count} cache entries"
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = [
    "router",
    "set_tool_registry", 
    "set_command_router"
]
