"""
JARVIS API Client
"""

import asyncio
import json
from typing import AsyncGenerator, Optional

import aiohttp
import websockets


class JarvisClient:
    """Client for interacting with JARVIS backend API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.ws_url = f"ws://localhost:8000/ws/chat"
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        """Close the client session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def chat(self, message: str, stream: bool = False) -> str:
        """
        Send a chat message and get response
        
        Args:
            message: Message to send
            stream: Whether to stream the response
            
        Returns:
            Response from JARVIS
        """
        session = await self._get_session()
        
        # Use WebSocket for streaming
        try:
            async with websockets.connect(self.ws_url) as ws:
                # Send message
                await ws.send(json.dumps({
                    "type": "message",
                    "content": message
                }))
                
                # Collect response
                response = ""
                async for msg in ws:
                    data = json.loads(msg)
                    
                    if data.get("type") == "chunk":
                        content = data.get("content", "")
                        print(content, end="", flush=True)
                        response += content
                    elif data.get("type") == "done":
                        break
                    elif data.get("type") == "error":
                        raise Exception(data.get("content", "Unknown error"))
                
                return response
                
        except websockets.exceptions.ConnectionClosed:
            # Fallback to HTTP if WebSocket fails
            return await self._chat_http(message)
        except Exception as e:
            return await self._chat_http(message)
    
    async def _chat_http(self, message: str) -> str:
        """Fallback HTTP chat"""
        session = await self._get_session()
        
        async with session.post(
            f"{self.base_url}/ws/chat",
            json={"message": message}
        ) as resp:
            if resp.status != 200:
                return f"Error: HTTP {resp.status}"
            data = await resp.json()
            return data.get("response", "")
    
    async def chat_stream(self, message: str) -> AsyncGenerator[str, None]:
        """
        Stream chat response
        
        Yields:
            Response chunks
        """
        session = await self._get_session()
        
        async with websockets.connect(self.ws_url) as ws:
            await ws.send(json.dumps({
                "type": "message",
                "content": message
            }))
            
            async for msg in ws:
                data = json.loads(msg)
                
                if data.get("type") == "chunk":
                    yield data.get("content", "")
                elif data.get("type") == "done":
                    break
                elif data.get("type") == "error":
                    raise Exception(data.get("content", "Unknown error"))
    
    async def get_memories(self, session_id: str = "default", limit: int = 50) -> dict:
        """Get list of memories"""
        session = await self._get_session()
        
        async with session.get(
            f"{self.base_url}/api/memory",
            params={"session_id": session_id, "limit": limit}
        ) as resp:
            return await resp.json()
    
    async def search_memory(self, query: str, limit: int = 10) -> dict:
        """Search memories"""
        session = await self._get_session()
        
        async with session.get(
            f"{self.base_url}/api/memory/search",
            params={"q": query, "limit": limit}
        ) as resp:
            return await resp.json()
    
    async def get_memory_stats(self) -> dict:
        """Get memory statistics"""
        session = await self._get_session()
        
        async with session.get(
            f"{self.base_url}/api/memory/filtered-stats"
        ) as resp:
            return await resp.json()
    
    async def clear_memories(self, project: Optional[str] = None) -> dict:
        """Clear memories"""
        session = await self._get_session()
        
        async with session.post(
            f"{self.base_url}/api/memory/clear",
            json={"project": project}
        ) as resp:
            return await resp.json()
    
    async def get_stats(self) -> dict:
        """Get system statistics"""
        session = await self._get_session()
        
        async with session.get(
            f"{self.base_url}/api/stats/current"
        ) as resp:
            return await resp.json()
    
    async def get_router_stats(self) -> dict:
        """Get router statistics"""
        session = await self._get_session()
        
        async with session.get(
            f"{self.base_url}/api/stats/router"
        ) as resp:
            return await resp.json()
    
    async def get_settings(self) -> dict:
        """Get settings"""
        # This would need a settings endpoint
        # For now, return placeholder
        return {
            "message": "Settings endpoint not implemented yet"
        }
    
    async def health_check(self) -> bool:
        """Check if server is healthy"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/health") as resp:
                return resp.status == 200
        except:
            return False


async def main():
    """Test the client"""
    client = JarvisClient()
    
    # Check health
    if await client.health_check():
        print("✓ Connected to JARVIS server")
    else:
        print("✗ Cannot connect to JARVIS server")
        print("  Start server with: python main.py")
        return
    
    # Test chat
    print("\nTesting chat...")
    response = await client.chat("Hello!")
    print(f"\nResponse: {response}")
    
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
