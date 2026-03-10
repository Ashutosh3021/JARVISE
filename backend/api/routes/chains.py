"""
Chain Management REST Routes

Provides REST endpoints for chain execution and management:
- POST /api/chains/execute - Execute a chain
- GET /api/chains/{chain_id}/status - Get chain status
- POST /api/chains/{chain_id}/interrupt - Interrupt a chain
- GET /api/chains/templates - Get available templates
- POST /api/chains/templates - Create custom template
- GET /api/chains/history - Get chain history
"""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from brain.chains import TaskChain, ChainStatus

router = APIRouter()


# Global chain instance
_chain_instance: TaskChain | None = None


def get_chain_instance() -> TaskChain:
    """Get or create the global chain instance."""
    global _chain_instance
    if _chain_instance is None:
        from brain.agent import ReActAgent
        from brain.tools import ToolRegistry
        _chain_instance = TaskChain(
            agent=ReActAgent(),
            tool_registry=ToolRegistry(),
        )
    return _chain_instance


# Request models
class ChainExecuteRequest(BaseModel):
    """Request to execute a chain."""
    user_input: str | None = None  # For LLM-parsed chains
    steps: list[dict[str, Any]] | None = None  # For explicit steps
    template: str | None = None  # For template-based chains


class ChainTemplateRequest(BaseModel):
    """Request to create a custom chain template."""
    name: str
    steps: list[dict[str, Any]]


# Response helpers
def chain_to_dict(chain) -> dict[str, Any]:
    """Convert chain result to dict."""
    if hasattr(chain, 'to_dict'):
        return chain.to_dict()
    return {
        "chain_id": getattr(chain, 'chain_id', 'unknown'),
        "status": getattr(chain, 'status', 'unknown'),
    }


@router.post("/chains/execute")
async def execute_chain(request: ChainExecuteRequest) -> dict[str, Any]:
    """
    Execute a task chain.
    
    Provide one of:
    - user_input: LLM will parse into steps
    - steps: Explicit list of steps
    - template: Use a predefined template
    """
    chain = get_chain_instance()
    
    steps = None
    chain_id = str(uuid.uuid4())[:8]
    
    # Determine what to execute
    if request.steps:
        steps = request.steps
    elif request.template:
        template = chain.get_template(request.template)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{request.template}' not found")
        steps = template
    elif request.user_input:
        # Parse user input into steps
        try:
            steps = chain.parse_chain_request(request.user_input)
            # Convert ChainStep to dict
            steps = [{"action": s.action, "input": s.input} for s in steps]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse chain: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Must provide user_input, steps, or template")
    
    # Validate step count
    if len(steps) > 5:
        raise HTTPException(status_code=400, detail=f"Chain exceeds maximum of 5 steps")
    
    # Execute chain
    try:
        result = await chain.execute_chain_async(steps)
        return {
            "chain_id": result.chain_id,
            "status": result.status.value,
            "result": result.to_dict(),
        }
    except Exception as e:
        logger.error(f"Chain execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chains/{chain_id}/status")
async def get_chain_status(chain_id: str) -> dict[str, Any]:
    """Get the status of a specific chain."""
    chain = get_chain_instance()
    result = chain.get_chain(chain_id)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Chain '{chain_id}' not found")
    
    return result.to_dict()


@router.post("/chains/{chain_id}/interrupt")
async def interrupt_chain(chain_id: str) -> dict[str, Any]:
    """Interrupt a running chain."""
    chain = get_chain_instance()
    
    # Check if chain exists
    result = chain.get_chain(chain_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Chain '{chain_id}' not found")
    
    # Interrupt if still running
    if result.status == ChainStatus.RUNNING:
        chain.interrupt()
        return {"status": "interrupted", "chain_id": chain_id}
    
    return {"status": result.status.value, "chain_id": chain_id}


@router.get("/chains/templates")
async def get_templates() -> dict[str, Any]:
    """Get all available chain templates."""
    chain = get_chain_instance()
    templates = chain.list_templates()
    return {"templates": templates}


@router.post("/chains/templates")
async def create_template(request: ChainTemplateRequest) -> dict[str, Any]:
    """Create a custom chain template."""
    chain = get_chain_instance()
    
    try:
        chain.add_template(request.name, request.steps)
        return {
            "status": "created",
            "name": request.name,
            "steps": request.steps,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/chains/history")
async def get_history() -> dict[str, Any]:
    """Get chain execution history."""
    chain = get_chain_instance()
    history = chain.get_history()
    return {"history": history, "count": len(history)}


__all__ = ["router"]
