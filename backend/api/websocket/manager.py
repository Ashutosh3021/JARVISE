"""
WebSocket Connection Manager

Manages WebSocket connections for live token streaming.
"""

from typing import Any
import json

from fastapi import WebSocket


class ConnectionManager:
    """
    Manages active WebSocket connections and message broadcasting.
    
    Provides methods to connect, disconnect, and send messages
    to individual or all connected clients.
    """
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket) -> None:
        """Accept and track a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection from active connections."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_token(self, websocket: WebSocket, token: str, is_final: bool = False) -> None:
        """
        Send a token to a specific WebSocket client.
        
        Args:
            websocket: The WebSocket connection to send to
            token: The token content
            is_final: Whether this is the final token
        """
        message = {
            "type": "token",
            "content": token,
            "is_final": is_final
        }
        await websocket.send_text(json.dumps(message))
    
    async def send_message(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        """
        Send a JSON message to a specific WebSocket client.
        
        Args:
            websocket: The WebSocket connection to send to
            message: The message dictionary to send
        """
        await websocket.send_text(json.dumps(message))
    
    async def send_to_all(self, message: dict[str, Any]) -> None:
        """
        Broadcast a message to all active connections.
        
        Args:
            message: The message dictionary to broadcast
        """
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                # Remove disconnected clients
                self.disconnect(connection)
    
    async def send_stats(self, stats: dict[str, Any]) -> None:
        """
        Broadcast system stats to all clients.
        
        Args:
            stats: Dictionary containing system statistics
        """
        message = {
            "type": "system.stats",
            "data": stats
        }
        await self.send_to_all(message)
    
    async def send_voice_state(self, state: str, details: dict[str, Any] | None = None) -> None:
        """
        Broadcast voice state changes to all clients.
        
        Args:
            state: The voice state (e.g., "listening", "processing", "idle")
            details: Optional additional details about the state
        """
        message = {
            "type": "voice.state",
            "state": state,
            "details": details or {}
        }
        await self.send_to_all(message)


# Global connection manager instance
manager = ConnectionManager()


__all__ = ["ConnectionManager", "manager"]
