"""
API Authentication Dependencies

Provides FastAPI dependencies for API key authentication.
"""

from typing import TYPE_CHECKING
from fastapi import Depends, HTTPException, Request
from fastapi.security import APIKeyHeader

from core.config import Config

if TYPE_CHECKING:
    from brain.agent import ReActAgent

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_config() -> Config:
    """Get the application config."""
    return Config()


async def verify_api_key(
    request: Request,
    api_key_header: str | None = Depends(_api_key_header),
    config: Config = Depends(get_config),
) -> bool:
    """
    Verify API key for protected endpoints.
    
    Security Model:
    - If API_KEY is not set: Allow all requests (development mode only!)
    - If API_KEY is set: Require valid key in X-API-Key header for remote requests
    - Localhost Bypass: Requests from 127.0.0.1, ::1, or localhost bypass API key check.
      This allows local UI access without credentials while still protecting remote access.
      For production, set API_KEY and ensure UI_HOST=127.0.0.1 (default).
    """
    # If no API key configured, allow all (dev mode)
    if not config.api_key:
        return True
    
    # Check if request is from localhost
    client_host = request.client.host if request.client else ""
    localhost_ips = {"127.0.0.1", "::1", "localhost"}
    if client_host in localhost_ips or client_host.startswith("127."):
        return True
    
    # Check API key header
    if not api_key_header:
        raise HTTPException(
            status_code=401,
            detail="API key required. Add X-API-Key header."
        )
    
    if api_key_header != config.api_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    
    return True


async def require_api_key(
    config: Config = Depends(get_config),
) -> bool:
    """
    Require API key to be configured (for sensitive operations).
    """
    if not config.api_key:
        raise HTTPException(
            status_code=503,
            detail="API key not configured. Set API_KEY in environment."
        )
    return True


async def get_agent(request: Request) -> "ReActAgent":
    """Get the shared agent from app.state."""
    from brain.agent import ReActAgent
    agent = getattr(request.app.state, 'agent', None)
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return agent


async def get_memory_manager(request: Request) -> "MemoryManager":
    """Get the shared memory manager from app.state."""
    from memory.MemoryManager import MemoryManager
    memory: MemoryManager = getattr(request.app.state, 'memory', None)
    if memory is None:
        raise HTTPException(status_code=503, detail="Memory not initialized")
    return memory


async def get_router(request: Request):
    """Get the shared router from app.state."""
    from brain.router import CommandRouter
    router = getattr(request.app.state, 'router', None)
    if router is None:
        raise HTTPException(status_code=503, detail="Router not initialized")
    return router


async def get_filtered_memory(request: Request) -> "FilteredMemory":
    """Get the shared filtered memory from app.state.memory.filtered_memory."""
    from memory.MemoryManager import MemoryManager
    from memory.filtered_store import FilteredMemory
    memory_obj = getattr(request.app.state, 'memory', None)
    if memory_obj is None:
        raise HTTPException(status_code=503, detail="Memory not initialized")
    if not isinstance(memory_obj, MemoryManager):
        raise HTTPException(status_code=503, detail="Memory not properly initialized")
    filtered = getattr(memory_obj, 'filtered_memory', None)
    if filtered is None:
        raise HTTPException(status_code=503, detail="Filtered memory not available")
    return filtered
