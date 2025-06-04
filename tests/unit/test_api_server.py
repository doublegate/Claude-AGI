"""
Unit tests for Claude-AGI API Server
====================================

Tests the FastAPI server for external interaction with consciousness system.
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import pytest
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.api.server import app
from src.core.orchestrator import AGIOrchestrator, SystemState
from src.memory.manager import MemoryManager
from src.core.ai_integration import ThoughtGenerator
from src.database.models import EmotionalState, MemoryType, StreamType


@pytest.fixture
async def mock_orchestrator():
    """Create mock orchestrator"""
    orchestrator = AsyncMock(spec=AGIOrchestrator)
    orchestrator.state = SystemState.IDLE
    orchestrator.start_time = datetime.now()
    orchestrator._state = SystemState.THINKING
    orchestrator.running = True
    orchestrator.initialize = AsyncMock()
    orchestrator.shutdown = AsyncMock()
    orchestrator.memory_manager = AsyncMock(spec=MemoryManager)
    orchestrator.memory_manager.get_memory_count = AsyncMock(return_value=100)
    orchestrator.thought_generator = AsyncMock(spec=ThoughtGenerator)
    return orchestrator


@pytest.fixture
def test_client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


class TestAPIServer:
    """Test API server endpoints"""
    
    @pytest.mark.asyncio
    async def test_lifespan_manager(self, mock_orchestrator):
        """Test application lifespan management"""
        # Mock the global orchestrator
        with patch('src.api.server.orchestrator', mock_orchestrator):
            # Test startup
            async with app.router.lifespan_context(app):
                mock_orchestrator.initialize.assert_called_once()
            
            # Test shutdown
            mock_orchestrator.shutdown.assert_called_once()
    
    def test_health_check(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_get_status(self, async_client, mock_orchestrator):
        """Test status endpoint"""
        with patch('src.api.server.orchestrator', mock_orchestrator):
            mock_orchestrator.consciousness_streams = {
                "primary": Mock(stream_name="primary"),
                "subconscious": Mock(stream_name="subconscious")
            }
            
            response = await async_client.get("/status")
            assert response.status_code == 200
            
            data = response.json()
            assert data["state"] == "IDLE"
            assert data["memory_count"] == 100
            assert len(data["active_streams"]) == 2
            assert "uptime_seconds" in data
    
    @pytest.mark.asyncio
    async def test_generate_thought(self, async_client, mock_orchestrator):
        """Test thought generation endpoint"""
        with patch('src.api.server.orchestrator', mock_orchestrator):
            # Mock thought generator response
            mock_orchestrator.thought_generator.generate_thought = AsyncMock(
                return_value="Contemplating the nature of existence"
            )
            
            request_data = {
                "stream_type": "primary",
                "context": {"topic": "philosophy"},
                "emotional_state": {
                    "valence": "positive",
                    "arousal": "medium",
                    "dominance": 0.7,
                    "emotions": {"curious": 0.8}
                }
            }
            
            response = await async_client.post("/thoughts/generate", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert "thought_id" in data
            assert data["content"] == "Contemplating the nature of existence"
            assert data["stream_type"] == "primary"
            assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_generate_thought_minimal(self, async_client, mock_orchestrator):
        """Test thought generation with minimal parameters"""
        with patch('src.api.server.orchestrator', mock_orchestrator):
            mock_orchestrator.thought_generator.generate_thought = AsyncMock(
                return_value="A simple thought"
            )
            
            response = await async_client.post("/thoughts/generate", json={})
            assert response.status_code == 200
            
            data = response.json()
            assert data["stream_type"] == "primary"
            assert data["content"] == "A simple thought"
    
    @pytest.mark.asyncio
    async def test_query_memory(self, async_client, mock_orchestrator):
        """Test memory query endpoint"""
        with patch('src.api.server.orchestrator', mock_orchestrator):
            # Mock memory search
            mock_memories = [
                Mock(id="mem1", content="First memory", importance=0.8, 
                     timestamp=datetime.now(), metadata={}),
                Mock(id="mem2", content="Second memory", importance=0.6,
                     timestamp=datetime.now(), metadata={})
            ]
            mock_orchestrator.memory_manager.search_memories = AsyncMock(
                return_value=mock_memories
            )
            
            request_data = {
                "query": "consciousness",
                "memory_type": "episodic",
                "limit": 5
            }
            
            response = await async_client.post("/memory/query", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert len(data["memories"]) == 2
            assert data["memories"][0]["content"] == "First memory"
            assert data["total"] == 2
    
    @pytest.mark.asyncio
    async def test_get_recent_thoughts(self, async_client, mock_orchestrator):
        """Test getting recent thoughts"""
        with patch('src.api.server.orchestrator', mock_orchestrator):
            # Mock consciousness stream
            mock_stream = Mock()
            mock_stream.recent_thoughts = [
                {"content": "Thought 1", "timestamp": datetime.now()},
                {"content": "Thought 2", "timestamp": datetime.now()}
            ]
            mock_orchestrator.consciousness_streams = {"primary": mock_stream}
            
            response = await async_client.get("/thoughts/recent?limit=5&stream=primary")
            assert response.status_code == 200
            
            data = response.json()
            assert len(data["thoughts"]) == 2
            assert data["stream"] == "primary"
    
    @pytest.mark.asyncio
    async def test_get_recent_thoughts_invalid_stream(self, async_client, mock_orchestrator):
        """Test getting thoughts from invalid stream"""
        with patch('src.api.server.orchestrator', mock_orchestrator):
            mock_orchestrator.consciousness_streams = {}
            
            response = await async_client.get("/thoughts/recent?stream=invalid")
            assert response.status_code == 404
            assert "Stream 'invalid' not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_conversation_endpoint(self, async_client, mock_orchestrator):
        """Test conversation endpoint"""
        with patch('src.api.server.orchestrator', mock_orchestrator):
            # Mock conversation response
            mock_orchestrator.thought_generator.generate_conversation_response = AsyncMock(
                return_value="I understand your question about consciousness"
            )
            
            # Mock emotional state
            mock_emotional = Mock(spec=EmotionalState)
            mock_emotional.model_dump = Mock(return_value={
                "valence": "positive",
                "arousal": "medium",
                "dominance": 0.6,
                "emotions": {"engaged": 0.8}
            })
            mock_orchestrator.emotional_state = mock_emotional
            
            request_data = {
                "message": "What is consciousness?",
                "conversation_id": "conv123"
            }
            
            response = await async_client.post("/conversation", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["response"] == "I understand your question about consciousness"
            assert data["conversation_id"] == "conv123"
            assert "emotional_state" in data
    
    @pytest.mark.asyncio
    async def test_conversation_new_session(self, async_client, mock_orchestrator):
        """Test conversation with new session"""
        with patch('src.api.server.orchestrator', mock_orchestrator):
            mock_orchestrator.thought_generator.generate_conversation_response = AsyncMock(
                return_value="Hello!"
            )
            
            mock_emotional = Mock()
            mock_emotional.model_dump = Mock(return_value={
                "valence": "positive",
                "arousal": "medium",
                "dominance": 0.5,
                "emotions": {}
            })
            mock_orchestrator.emotional_state = mock_emotional
            
            request_data = {"message": "Hello"}
            
            response = await async_client.post("/conversation", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert "conversation_id" in data
            assert data["conversation_id"] != ""
    
    @pytest.mark.asyncio
    async def test_trigger_reflection(self, async_client, mock_orchestrator):
        """Test reflection trigger endpoint"""
        with patch('src.api.server.orchestrator', mock_orchestrator):
            # Mock publish method
            mock_orchestrator.publish = AsyncMock()
            
            response = await async_client.post(
                "/reflection/trigger",
                json={"topic": "self-awareness"}
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "triggered"
            assert data["topic"] == "self-awareness"
            
            # Verify reflection was triggered
            mock_orchestrator.publish.assert_called_once()
            call_args = mock_orchestrator.publish.call_args[0]
            assert call_args[0] == "reflection_requested"
    
    @pytest.mark.asyncio
    async def test_websocket_thoughts_stream(self, mock_orchestrator):
        """Test WebSocket thoughts streaming"""
        with patch('src.api.server.orchestrator', mock_orchestrator):
            # Create mock websocket
            websocket = AsyncMock(spec=WebSocket)
            websocket.accept = AsyncMock()
            websocket.receive_json = AsyncMock()
            websocket.send_json = AsyncMock()
            websocket.close = AsyncMock()
            
            # Mock subscription and thoughts
            websocket.receive_json.side_effect = [
                {"action": "subscribe", "stream": "primary"},
                WebSocketDisconnect()
            ]
            
            # Import the websocket handler
            from src.api.server import websocket_endpoint
            
            # Test the websocket
            with pytest.raises(WebSocketDisconnect):
                await websocket_endpoint(websocket)
            
            websocket.accept.assert_called_once()
            websocket.send_json.assert_called()
    
    def test_custom_404_handler(self, test_client):
        """Test custom 404 error handler"""
        response = test_client.get("/nonexistent/endpoint")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Endpoint not found"
    
    @pytest.mark.asyncio
    async def test_error_handling(self, async_client, mock_orchestrator):
        """Test error handling in endpoints"""
        with patch('src.api.server.orchestrator', mock_orchestrator):
            # Test error in thought generation
            mock_orchestrator.thought_generator.generate_thought = AsyncMock(
                side_effect=Exception("Generation failed")
            )
            
            response = await async_client.post("/thoughts/generate", json={})
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_update_emotional_state(self, async_client, mock_orchestrator):
        """Test emotional state update endpoint"""
        with patch('src.api.server.orchestrator', mock_orchestrator):
            # Mock update
            mock_orchestrator.update_emotional_state = AsyncMock()
            
            emotional_data = {
                "valence": "negative",
                "arousal": "high",
                "dominance": 0.3,
                "emotions": {"anxious": 0.7, "worried": 0.5}
            }
            
            response = await async_client.put("/emotional/state", json=emotional_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "updated"
            
            # Verify update was called
            mock_orchestrator.update_emotional_state.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_memories_paginated(self, async_client, mock_orchestrator):
        """Test paginated memory retrieval"""
        with patch('src.api.server.orchestrator', mock_orchestrator):
            # Mock memory retrieval
            mock_memories = [
                Mock(id=f"mem{i}", content=f"Memory {i}", 
                     memory_type=MemoryType.EPISODIC,
                     timestamp=datetime.now(), importance=0.5,
                     metadata={})
                for i in range(5)
            ]
            mock_orchestrator.memory_manager.get_memories = AsyncMock(
                return_value=(mock_memories, 15)  # memories, total_count
            )
            
            response = await async_client.get(
                "/memory?memory_type=episodic&page=2&page_size=5"
            )
            assert response.status_code == 200
            
            data = response.json()
            assert len(data["memories"]) == 5
            assert data["page"] == 2
            assert data["page_size"] == 5
            assert data["total_count"] == 15
            assert data["total_pages"] == 3
    
    @pytest.mark.asyncio
    async def test_store_memory(self, async_client, mock_orchestrator):
        """Test memory storage endpoint"""
        with patch('src.api.server.orchestrator', mock_orchestrator):
            # Mock memory storage
            mock_orchestrator.memory_manager.add_memory = AsyncMock(
                return_value="mem123"
            )
            
            memory_data = {
                "content": "Important insight about consciousness",
                "memory_type": "episodic",
                "importance": 0.9,
                "metadata": {"topic": "consciousness", "source": "reflection"}
            }
            
            response = await async_client.post("/memory/store", json=memory_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["memory_id"] == "mem123"
            assert data["status"] == "stored"
    
    @pytest.mark.asyncio
    async def test_cors_middleware(self, async_client):
        """Test CORS middleware configuration"""
        response = await async_client.options("/health")
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
    
    def test_api_documentation(self, test_client):
        """Test API documentation endpoints"""
        # Test OpenAPI schema
        response = test_client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert schema["info"]["title"] == "Claude-AGI API"
        
        # Test docs endpoint
        response = test_client.get("/docs")
        assert response.status_code == 200
        
        # Test redoc endpoint
        response = test_client.get("/redoc")
        assert response.status_code == 200