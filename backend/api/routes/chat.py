"""
Chat WebSocket Route

Provides WebSocket endpoint for live token streaming from the agent.
"""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from loguru import logger

from backend.api.websocket.manager import manager

# Import the ReActAgent from brain
from brain.agent import ReActAgent
from brain.tools import create_tools_registry


router = APIRouter()


# Global agent instance - with tools!
agent = ReActAgent(tool_registry=create_tools_registry())


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for chat with live token streaming.
    
    Expects JSON messages with a "message" field containing user input.
    Streams tokens back to the client as they're generated.
    
    Message format:
        {"message": "user input text"}
    
    Response format:
        {"type": "token", "content": "token text", "is_final": false}
        {"type": "done"}  # When complete
    """
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
                
                # Process message through agent with TRUE streaming
                # Use asyncio.Queue to hand off tokens from thread to async context
                token_queue = asyncio.Queue()
                stop_event = asyncio.Event()
                
                def run_generator():
                    """Run the generator in a thread and put tokens in queue."""
                    try:
                        for token, is_final in agent.stream_run(user_message):
                            if stop_event.is_set():
                                break
                            # Put token in queue - will block if queue is full
                            # Use 3-tuple to match consumer unpacking
                            token_queue.put_nowait((token, is_final, None))
                            if is_final:
                                break
                    except Exception as e:
                        logger.error(f"Error in agent stream: {e}")
                        token_queue.put_nowait((None, True, str(e)))
                    finally:
                        token_queue.put_nowait((None, None, None))  # Sentinel
                
                # Start generator in thread pool
                loop = asyncio.get_event_loop()
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
async def reset_chat():
    """Reset the chat conversation history."""
    agent.reset()
    return {"status": "success", "message": "Chat history reset"}


__all__ = ["router"]
