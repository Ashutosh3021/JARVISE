"""
Chat WebSocket Route

Provides WebSocket endpoint for live token streaming from the agent.
"""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from loguru import logger

from backend.api.websocket.manager import manager

# Import the ReActAgent from brain
from brain.agent import ReActAgent


router = APIRouter()


# Global agent instance
agent = ReActAgent()


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
                
                # Process message through agent with streaming
                for token, is_final in agent.stream_run(user_message):
                    await manager.send_token(websocket, token, is_final)
                    
                    if is_final:
                        break
                
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
