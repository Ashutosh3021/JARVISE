"""
JARVIS Backend Server

FastAPI server with WebSocket support for live token streaming
and REST endpoints for memory management.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context for startup and shutdown events."""
    # Startup
    logger.info("Starting JARVIS backend server...")
    yield
    # Shutdown
    logger.info("Shutting down JARVIS backend server...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="JARVIS Backend",
        description="FastAPI backend with WebSocket support for JARVIS AI Assistant",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # Configure CORS - allow specific origins for local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",  # Vite dev server
            "http://localhost:3000",  # React dev server
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Import and include routers
    from backend.api.routes import chat, memory, stats, learn
    
    app.include_router(chat.router, tags=["chat"])
    app.include_router(memory.router, prefix="/api", tags=["memory"])
    app.include_router(stats.router, prefix="/api", tags=["stats"])
    app.include_router(learn.router, prefix="/api", tags=["learn"])
    
    @app.get("/")
    async def root():
        """Root endpoint returning server status."""
        return {
            "status": "online",
            "service": "JARVIS Backend",
            "version": "1.0.0",
        }
    
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy"}
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
