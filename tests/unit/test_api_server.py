"""
Unit tests for Claude-AGI API Server
====================================

Tests the FastAPI server for external interaction with consciousness system.
"""

import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import pytest
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.testclient import TestClient
from httpx import AsyncClient as HttpxAsyncClient

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
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestAPIServer:
    """Test API server endpoints"""
    
    @pytest.mark.asyncio
    async def test_lifespan_manager(self, mock_orchestrator):
        """Test application lifespan management"""
        mock_memory_manager = AsyncMock()
        mock_memory_manager.initialize = AsyncMock()
        mock_memory_manager.close = AsyncMock()
        
        with patch('src.api.server.AGIOrchestrator', return_value=mock_orchestrator):
            with patch('src.api.server.MemoryManager.create', return_value=mock_memory_manager):
                with patch('src.api.server.ThoughtGenerator'):
                    with patch('asyncio.create_task'):
                        # Test startup and shutdown
                        async with app.router.lifespan_context(app):
                            pass
                        
                        # Verify initialization
                        mock_memory_manager.initialize.assert_called_once_with(use_database=True)
                        mock_orchestrator.run.assert_called_once()
                        
                        # Verify cleanup
                        mock_memory_manager.close.assert_called_once()
    
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
        # Mock consciousness service
        mock_consciousness = Mock()
        mock_consciousness.total_thoughts = 42
        mock_consciousness.streams = {
            "primary": Mock(stream_name="primary"),
            "subconscious": Mock(stream_name="subconscious")
        }
        
        # Set up orchestrator with services
        mock_orchestrator.services = {'consciousness': mock_consciousness}
        mock_orchestrator.state = SystemState.IDLE
        
        # Mock memory manager
        mock_memory = AsyncMock()
        mock_memory.recall_recent = AsyncMock(return_value=[
            {"id": "1", "content": "test memory"}
        ])
        
        with patch('src.api.server.orchestrator', mock_orchestrator):
            with patch('src.api.server.memory_manager', mock_memory):
                response = await async_client.get("/status")
            assert response.status_code == 200
            
            data = response.json()
            assert data["state"] == "idle"
            assert data["memory_count"] == 1  # We're returning 1 memory item
            assert data["total_thoughts"] == 42
            assert len(data["active_streams"]) == 2
            assert "uptime_seconds" in data
    
    @pytest.mark.asyncio
    async def test_generate_thought(self, async_client, mock_orchestrator):
        """Test thought generation endpoint"""
        # Mock thought generator response
        mock_thought_generator = AsyncMock()
        mock_thought_generator.generate_thought = AsyncMock(
            return_value={
                'content': "Contemplating the nature of existence",
                'timestamp': datetime.now(timezone.utc),
                'emotional_state': None,
                'importance': 0.7
            }
        )
        
        # Mock memory manager
        mock_memory = AsyncMock()
        mock_memory.store_thought = AsyncMock(return_value="thought-123")
        
        with patch('src.api.server.thought_generator', mock_thought_generator):
            with patch('src.api.server.memory_manager', mock_memory):
                request_data = {
                    "stream_type": "primary",
                    "context": {"topic": "philosophy"},
                    "emotional_state": {
                        "valence": 0.7,  # positive valence as float
                        "arousal": 0.5,  # medium arousal as float
                        "dominance": 0.7,
                        "primary_emotion": "curious",
                        "intensity": 0.8
                    }
                }
                
                response = await async_client.post("/thoughts/generate", json=request_data)
                if response.status_code != 200:
                    print(f"Response status: {response.status_code}")
                    print(f"Response body: {response.json()}")
                assert response.status_code == 200
                
                data = response.json()
                assert data["thought_id"] == "thought-123"
                assert data["content"] == "Contemplating the nature of existence"
                assert data["stream_type"] == "primary"
                assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_generate_thought_minimal(self, async_client, mock_orchestrator):
        """Test thought generation with minimal parameters"""
        # Mock thought generator
        mock_thought_generator = AsyncMock()
        mock_thought_generator.generate_thought = AsyncMock(
            return_value={
                'content': "A simple thought",
                'timestamp': datetime.now(timezone.utc),
                'emotional_state': None,
                'importance': 0.5
            }
        )
        
        # Mock memory manager
        mock_memory = AsyncMock()
        mock_memory.store_thought = AsyncMock(return_value="thought-456")
        
        with patch('src.api.server.thought_generator', mock_thought_generator):
            with patch('src.api.server.memory_manager', mock_memory):
                response = await async_client.post("/thoughts/generate", json={})
                assert response.status_code == 200
                
                data = response.json()
                assert data["stream_type"] == "primary"
                assert data["content"] == "A simple thought"
    
    @pytest.mark.asyncio
    async def test_query_memory(self, async_client, mock_orchestrator):
        """Test memory query endpoint"""
        # Mock memory manager
        mock_memory = AsyncMock()
        mock_memory.recall_similar = AsyncMock(
            return_value=[
                {
                    "id": "mem1",
                    "content": "First memory",
                    "importance": 0.8,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "stream_type": "primary",
                    "metadata": {}
                },
                {
                    "id": "mem2",
                    "content": "Second memory",
                    "importance": 0.6,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "stream_type": "primary",
                    "metadata": {}
                }
            ]
        )
        
        with patch('src.api.server.memory_manager', mock_memory):
            request_data = {
                "query": "consciousness",
                "memory_type": "episodic",
                "limit": 5
            }
            
            response = await async_client.post("/memory/query", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert len(data["results"]) == 2
            assert data["results"][0]["content"] == "First memory"
            assert data["count"] == 2
    
    @pytest.mark.asyncio
    async def test_get_recent_thoughts(self, async_client, mock_orchestrator):
        """Test getting recent thoughts"""
        # Mock memory manager
        mock_memory = AsyncMock()
        mock_memory.recall_recent = AsyncMock(
            return_value=[
                {"content": "Thought 1", "timestamp": datetime.now(timezone.utc).isoformat(), "stream": "primary"},
                {"content": "Thought 2", "timestamp": datetime.now(timezone.utc).isoformat(), "stream": "primary"}
            ]
        )
        
        with patch('src.api.server.memory_manager', mock_memory):
            response = await async_client.get("/thoughts/recent?limit=5&stream=primary")
            assert response.status_code == 200
            
            data = response.json()
            assert len(data["thoughts"]) == 2
            assert data["count"] == 2
    
    @pytest.mark.asyncio
    async def test_get_recent_thoughts_invalid_stream(self, async_client, mock_orchestrator):
        """Test getting thoughts from invalid stream"""
        # Mock memory manager - returns thoughts but none match 'invalid' stream
        mock_memory = AsyncMock()
        mock_memory.recall_recent = AsyncMock(
            return_value=[
                {"content": "Thought 1", "timestamp": datetime.now(timezone.utc).isoformat(), "stream": "primary"},
                {"content": "Thought 2", "timestamp": datetime.now(timezone.utc).isoformat(), "stream": "subconscious"}
            ]
        )
        
        with patch('src.api.server.memory_manager', mock_memory):
            response = await async_client.get("/thoughts/recent?stream=invalid")
            assert response.status_code == 200
            data = response.json()
            assert len(data["thoughts"]) == 0  # No thoughts match 'invalid' stream
            assert data["count"] == 0
    
    @pytest.mark.asyncio
    async def test_conversation_endpoint(self, async_client, mock_orchestrator):
        """Test conversation endpoint"""
        # Mock thought generator
        mock_thought_generator = AsyncMock()
        mock_thought_generator.generate_response = AsyncMock(
            return_value="I understand your question about consciousness"
        )
        
        # Mock consciousness service
        mock_consciousness = AsyncMock()
        mock_consciousness.handle_user_input = AsyncMock()
        mock_consciousness.streams = {}
        mock_consciousness.total_thoughts = 0
        
        # Set up orchestrator with services
        mock_orchestrator.services = {'consciousness': mock_consciousness}
        mock_orchestrator.state = SystemState.IDLE
        
        with patch('src.api.server.orchestrator', mock_orchestrator):
            with patch('src.api.server.thought_generator', mock_thought_generator):
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
        # Mock thought generator
        mock_thought_generator = AsyncMock()
        mock_thought_generator.generate_response = AsyncMock(return_value="Hello!")
        
        # Mock consciousness service
        mock_consciousness = AsyncMock()
        mock_consciousness.handle_user_input = AsyncMock()
        mock_consciousness.total_thoughts = 5
        
        # Set up orchestrator with services
        mock_orchestrator.services = {'consciousness': mock_consciousness}
        
        with patch('src.api.server.orchestrator', mock_orchestrator):
            with patch('src.api.server.thought_generator', mock_thought_generator):
                request_data = {"message": "Hello"}
                
                response = await async_client.post("/conversation", json=request_data)
                assert response.status_code == 200
                
                data = response.json()
                assert "conversation_id" in data
                assert data["conversation_id"] != ""
                assert data["response"] == "Hello!"
    
    # REMOVED - /reflection/trigger endpoint doesn't exist in server.py
    
    @pytest.mark.asyncio
    async def test_websocket_thoughts_stream(self, mock_orchestrator):
        """Test WebSocket thoughts streaming"""
        # Mock consciousness service with proper stream structure
        mock_stream = Mock()
        mock_stream.stream_id = 'primary'  # Add stream_id attribute
        mock_stream.get_recent = Mock(return_value=[{
            'content': 'Test thought',
            'timestamp': 123456,
            'emotional_tone': 'curious'
        }])
        
        mock_consciousness = Mock()
        mock_consciousness.streams = {'primary': mock_stream}
        
        mock_orchestrator.services = {'consciousness': mock_consciousness}
        
        with patch('src.api.server.orchestrator', mock_orchestrator):
            # Create mock websocket
            websocket = AsyncMock(spec=WebSocket)
            websocket.accept = AsyncMock()
            websocket.send_json = AsyncMock()
            websocket.close = AsyncMock()
            
            # Make send_json raise WebSocketDisconnect on second call to simulate client disconnect
            websocket.send_json.side_effect = [None, WebSocketDisconnect()]
            
            # Import the websocket handler
            from src.api.server import websocket_consciousness
            
            # Test the websocket - it should handle the disconnect gracefully
            await websocket_consciousness(websocket)
            
            websocket.accept.assert_called_once()
            # Should be called at least once before disconnect
            assert websocket.send_json.call_count >= 1
            
            # Verify the correct data was sent in the first call
            sent_data = websocket.send_json.call_args_list[0][0][0]
            assert sent_data['type'] == 'thought'
            assert sent_data['stream'] == 'primary'
            assert sent_data['content'] == 'Test thought'
            assert sent_data['timestamp'] == 123456
            assert sent_data['emotional_tone'] == 'curious'
    
    def test_custom_404_handler(self, test_client):
        """Test custom 404 error handler"""
        response = test_client.get("/nonexistent/endpoint")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Not Found"  # FastAPI default message
    
    @pytest.mark.asyncio
    async def test_error_handling(self, async_client, mock_orchestrator):
        """Test error handling in endpoints"""
        # Mock thought generator
        mock_thought_generator = AsyncMock()
        mock_thought_generator.generate_thought = AsyncMock(
            side_effect=Exception("Generation failed")
        )
        
        with patch('src.api.server.thought_generator', mock_thought_generator):
            response = await async_client.post("/thoughts/generate", json={})
            assert response.status_code == 500
            assert "Generation failed" in response.json()["detail"]
    
    # REMOVED - /emotional/state PUT endpoint doesn't exist in server.py
    
    # REMOVED - /memory GET endpoint doesn't exist in server.py (only /memory/query POST)
    
    # REMOVED - /memory/store endpoint doesn't exist in server.py
    
    @pytest.mark.asyncio
    async def test_cors_middleware(self, async_client):
        """Test CORS middleware configuration"""
        # CORS headers are only added for actual CORS requests with Origin header
        headers = {"Origin": "http://localhost:3000"}
        response = await async_client.get("/health", headers=headers)
        assert response.status_code == 200
        # Check CORS headers are present
        assert "access-control-allow-origin" in response.headers or response.headers.get("access-control-allow-origin", "") == "*"
    
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
    
    @pytest.mark.asyncio
    async def test_memory_consolidate(self, async_client):
        """Test memory consolidation endpoint"""
        mock_memory = AsyncMock()
        mock_memory.consolidate_memories = AsyncMock()
        
        with patch('src.api.server.memory_manager', mock_memory):
            response = await async_client.post("/memory/consolidate")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "Memory consolidation completed" in data["message"]
    
    @pytest.mark.asyncio
    async def test_system_pause(self, async_client, mock_orchestrator):
        """Test system pause endpoint"""
        with patch('src.api.server.orchestrator', mock_orchestrator):
            response = await async_client.post("/system/pause")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "paused"
            assert mock_orchestrator.state == SystemState.IDLE
    
    @pytest.mark.asyncio
    async def test_system_resume(self, async_client, mock_orchestrator):
        """Test system resume endpoint"""
        with patch('src.api.server.orchestrator', mock_orchestrator):
            response = await async_client.post("/system/resume")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "resumed"
            assert mock_orchestrator.state == SystemState.THINKING
    
    @pytest.mark.asyncio
    async def test_system_sleep(self, async_client, mock_orchestrator):
        """Test system sleep endpoint"""
        mock_memory = AsyncMock()
        mock_memory.consolidate_memories = AsyncMock()
        
        with patch('src.api.server.orchestrator', mock_orchestrator):
            with patch('src.api.server.memory_manager', mock_memory):
                with patch('asyncio.create_task'):
                    response = await async_client.post("/system/sleep")
                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] == "sleeping"
                    assert mock_orchestrator.state == SystemState.SLEEPING