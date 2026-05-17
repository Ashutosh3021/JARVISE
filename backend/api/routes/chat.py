"""
Chat WebSocket Route

Provides WebSocket endpoint for live token streaming from the agent
and REST endpoint for synchronous chat.
"""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel

from loguru import logger

from backend.api.websocket.manager import manager
from backend.api.dependencies import get_agent

# Import the ReActAgent type only
from brain.agent import ReActAgent


class ChatRequest(BaseModel):
    """Request model for REST chat endpoint."""
    message: str


class ChatResponse(BaseModel):
    """Response model for REST chat endpoint."""
    response: str


router = APIRouter()


@router.post("/api/chat", response_model=ChatResponse)
async def rest_chat(
    request: ChatRequest,
    agent: ReActAgent = Depends(get_agent)
):
    """
    REST endpoint for chat (non-streaming).
    
    Accepts a JSON body with a "message" field and returns the agent's response.
    
    Used as HTTP fallback when WebSocket is unavailable.
    """
    if not request.message:
        return ChatResponse(response="No message provided")
    
    # Run agent in thread pool to avoid blocking the event loop
    response = await asyncio.to_thread(agent.run, request.message)
    return ChatResponse(response=response)


@router.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    api_key: str | None = None,
    agent: ReActAgent = Depends(get_agent)
):
    """
    WebSocket endpoint for chat with live token streaming.
    
    Expects JSON messages with a "message" field containing user input.
    Streams tokens back to the client as they're generated.
    
    Message format:
        {"message": "user input text"}
    
    Response format:
        {"type": "token", "content": "token text", "is_final": false}
        {"type": "done"}  # When complete
    
    Authentication:
        - If API_KEY not set in config → only localhost connections allowed
        - If API_KEY set → require valid ?api_key=... query param or reject
    """
    # Auth check - import here to avoid circular deps
    from core.config import Config
    config = Config()
    
    # Check if request is from localhost
    client_host = websocket.client.host if websocket.client else ""
    localhost_ips = {"127.0.0.1", "::1", "localhost"}
    is_localhost = client_host in localhost_ips or client_host.startswith("127.")
    
    if not config.api_key:
        # No API key configured → local-only mode
        if not is_localhost:
            await websocket.close(code=4003, reason="Local only - no API key configured. Set API_KEY in .env for remote access.")
            return
    else:
        # API key configured → require valid key
        if not is_localhost and api_key != config.api_key:
            await websocket.close(code=4003, reason="Invalid API key")
            return
    
    await manager.connect(websocket)
    
    try:
        # Send connection confirmation
        await manager.send_message(websocket, {
            "type": "chat.stream",
            "status": "connected",
            "message": "Ready for chat"
        })
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                user_message = message_data.get("message", "")
                
                if not user_message:
                    await manager.send_message(websocket, {
                        "type": "error",
                        "message": "No message provided"
                    })
                    continue
                
                # Send thinking indicator
                await manager.send_message(websocket, {
                    "type": "chat.stream",
                    "status": "processing"
                })

                memory_context = None
                memory_manager = getattr(websocket.app.state, "memory", None)
                if memory_manager is not None:
                    memory_context = memory_manager.format_context_for_prompt(user_message)
                
                # Process message through agent with TRUE streaming
                # Use asyncio.Queue to hand off tokens from thread to async context
                token_queue = asyncio.Queue()
                stop_event = asyncio.Event()
                
                def run_generator():
                    """Run the generator in a thread and put tokens in queue."""
                    try:
                        for token, is_final in agent.stream_run(
                            user_message, memory_context=memory_context
                        ):
                            if stop_event.is_set():
                                break
                            loop.call_soon_threadsafe(
                                token_queue.put_nowait, (token, is_final, None)
                            )
                            if is_final:
                                break
                    except Exception as e:
                        logger.error(f"Error in agent stream: {e}")
                        loop.call_soon_threadsafe(
                            token_queue.put_nowait, (None, True, str(e))
                        )
                    finally:
                        loop.call_soon_threadsafe(
                            token_queue.put_nowait, (None, None, None)
                        )
                
                # Start generator in thread pool
                loop = asyncio.get_running_loop()
                stream_task = loop.run_in_executor(None, run_generator)
                
                try:
                    # Receive tokens from queue and send to WebSocket progressively
                    while True:
                        token, is_final, error = await token_queue.get()
                        
                        if error:
                            await manager.send_message(websocket, {
                                "type": "error",
                                "message": f"Processing error: {error}"
                            })
                            break
                        
                        if token is None and is_final is None:
                            # Sentinel - generator finished
                            break
                        
                        if token is not None:
                            await manager.send_token(websocket, token, is_final)
                        
                        if is_final:
                            break
                except Exception as e:
                    logger.error(f"Error in token handling: {e}")
                    await manager.send_message(websocket, {
                        "type": "error",
                        "message": f"Processing error: {str(e)}"
                    })
                finally:
                    # Ensure generator thread is cleaned up
                    stop_event.set()
                    # Wait for the stream task to complete
                    try:
                        await stream_task
                    except Exception:
                        pass
                
                # Send done message
                await manager.send_message(websocket, {
                    "type": "done"
                })
                
            except json.JSONDecodeError:
                await manager.send_message(websocket, {
                    "type": "error",
                    "message": "Invalid JSON"
                })
            except Exception as e:
                logger.error(f"Error processing chat: {e}")
                await manager.send_message(websocket, {
                    "type": "error",
                    "message": f"Error: {str(e)}"
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    finally:
        manager.disconnect(websocket)


@router.post("/chat/reset")
async def reset_chat(agent: ReActAgent = Depends(get_agent)):
    """Reset the chat conversation history."""
    agent.reset()
    return {"status": "success", "message": "Chat history reset"}


__all__ = ["router"]
