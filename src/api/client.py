"""
Python client for Claude-AGI API
================================

Provides a convenient Python interface for interacting with the Claude-AGI API.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
import websockets
from pydantic import BaseModel

from ..database.models import StreamType, EmotionalState, MemoryType


class ClaudeAGIClient:
    """Client for interacting with Claude-AGI API"""
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        response = await self.client.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    async def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        response = await self.client.get(f"{self.base_url}/status")
        response.raise_for_status()
        return response.json()
    
    async def generate_thought(
        self,
        stream_type: StreamType = StreamType.PRIMARY,
        context: Optional[Dict[str, Any]] = None,
        emotional_state: Optional[EmotionalState] = None
    ) -> Dict[str, Any]:
        """Generate a thought"""
        payload = {
            "stream_type": stream_type.value,
            "context": context or {},
        }
        
        if emotional_state:
            payload["emotional_state"] = emotional_state.model_dump()
        
        response = await self.client.post(
            f"{self.base_url}/thoughts/generate",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def query_memory(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Query memories"""
        payload = {
            "query": query,
            "limit": limit
        }
        
        if memory_type:
            payload["memory_type"] = memory_type.value
        
        response = await self.client.post(
            f"{self.base_url}/memory/query",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def get_recent_thoughts(
        self,
        limit: int = 10,
        stream: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get recent thoughts"""
        params = {"limit": limit}
        if stream:
            params["stream"] = stream
        
        response = await self.client.get(
            f"{self.base_url}/thoughts/recent",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def have_conversation(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        emotional_context: Optional[EmotionalState] = None
    ) -> Dict[str, Any]:
        """Have a conversation with Claude"""
        payload = {
            "message": message
        }
        
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        if emotional_context:
            payload["emotional_context"] = emotional_context.model_dump()
        
        response = await self.client.post(
            f"{self.base_url}/conversation",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def consolidate_memory(self) -> Dict[str, Any]:
        """Trigger memory consolidation"""
        response = await self.client.post(f"{self.base_url}/memory/consolidate")
        response.raise_for_status()
        return response.json()
    
    async def pause_system(self) -> Dict[str, Any]:
        """Pause the system"""
        response = await self.client.post(f"{self.base_url}/system/pause")
        response.raise_for_status()
        return response.json()
    
    async def resume_system(self) -> Dict[str, Any]:
        """Resume the system"""
        response = await self.client.post(f"{self.base_url}/system/resume")
        response.raise_for_status()
        return response.json()
    
    async def sleep_system(self) -> Dict[str, Any]:
        """Put system to sleep"""
        response = await self.client.post(f"{self.base_url}/system/sleep")
        response.raise_for_status()
        return response.json()
    
    async def stream_consciousness(self, callback):
        """Stream consciousness via WebSocket
        
        Args:
            callback: Async function called with each thought
        """
        uri = f"{self.base_url.replace('http', 'ws')}/ws/consciousness"
        
        async with websockets.connect(uri) as websocket:
            async for message in websocket:
                data = json.loads(message)
                await callback(data)


# Example usage
async def example_usage():
    """Example of using the Claude-AGI client"""
    async with ClaudeAGIClient() as client:
        # Check health
        health = await client.health_check()
        print(f"Health: {health}")
        
        # Get status
        status = await client.get_status()
        print(f"Status: {status}")
        
        # Generate a thought
        thought = await client.generate_thought(
            stream_type=StreamType.CREATIVE,
            context={"topic": "consciousness"}
        )
        print(f"Generated thought: {thought}")
        
        # Have a conversation
        response = await client.have_conversation(
            "Hello Claude, how are you feeling today?"
        )
        print(f"Claude's response: {response}")
        
        # Query memory
        memories = await client.query_memory(
            "consciousness",
            limit=5
        )
        print(f"Related memories: {memories}")
        
        # Stream consciousness (for 10 seconds)
        async def print_thought(thought_data):
            print(f"[{thought_data['stream']}] {thought_data['content']}")
        
        # This would run indefinitely, so we'd use asyncio.wait_for in practice
        # await asyncio.wait_for(
        #     client.stream_consciousness(print_thought),
        #     timeout=10.0
        # )


if __name__ == "__main__":
    # Run the example
    asyncio.run(example_usage())