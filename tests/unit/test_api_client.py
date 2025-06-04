"""
Unit tests for Claude-AGI API Client
====================================

Tests the Python client for interacting with Claude-AGI API.
"""

import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import pytest
import httpx
import websockets
from datetime import datetime

from src.api.client import ClaudeAGIClient
from src.database.models import StreamType, EmotionalState, MemoryType


@pytest.fixture
def client():
    """Create test client"""
    return ClaudeAGIClient(base_url="http://localhost:8000", timeout=30.0)


@pytest.fixture
def mock_response():
    """Create mock HTTP response"""
    response = Mock(spec=httpx.Response)
    response.raise_for_status = Mock()
    response.json = Mock(return_value={"status": "ok"})
    return response


class TestClaudeAGIClient:
    """Test ClaudeAGI API client"""
    
    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initialization"""
        client = ClaudeAGIClient()
        assert client.base_url == "http://localhost:8000"
        assert client.timeout == 30.0
        assert isinstance(client.client, httpx.AsyncClient)
        await client.close()
        
    @pytest.mark.asyncio
    async def test_client_custom_initialization(self):
        """Test client with custom URL and timeout"""
        client = ClaudeAGIClient(base_url="http://api.test:9000/", timeout=60.0)
        assert client.base_url == "http://api.test:9000"  # Trailing slash removed
        assert client.timeout == 60.0
        await client.close()
    
    @pytest.mark.asyncio
    async def test_client_context_manager(self):
        """Test client as async context manager"""
        async with ClaudeAGIClient() as client:
            assert isinstance(client, ClaudeAGIClient)
            assert hasattr(client, 'client')
    
    @pytest.mark.asyncio
    async def test_health_check(self, client, mock_response):
        """Test health check endpoint"""
        mock_response.json.return_value = {
            "status": "healthy",
            "timestamp": "2025-06-04T12:00:00Z"
        }
        
        with patch.object(client.client, 'get', return_value=mock_response) as mock_get:
            result = await client.health_check()
            
            mock_get.assert_called_once_with("http://localhost:8000/health")
            mock_response.raise_for_status.assert_called_once()
            assert result == {"status": "healthy", "timestamp": "2025-06-04T12:00:00Z"}
    
    @pytest.mark.asyncio
    async def test_get_status(self, client, mock_response):
        """Test status endpoint"""
        mock_response.json.return_value = {
            "state": "THINKING",
            "consciousness_active": True,
            "memory_count": 150
        }
        
        with patch.object(client.client, 'get', return_value=mock_response) as mock_get:
            result = await client.get_status()
            
            mock_get.assert_called_once_with("http://localhost:8000/status")
            assert result["state"] == "THINKING"
            assert result["consciousness_active"] is True
    
    @pytest.mark.asyncio
    async def test_generate_thought(self, client, mock_response):
        """Test thought generation"""
        mock_response.json.return_value = {
            "thought": "Contemplating the nature of consciousness",
            "stream": "primary",
            "timestamp": "2025-06-04T12:00:00Z"
        }
        
        emotional_state = EmotionalState(
            valence=0.7,
            arousal=0.5,
            dominance=0.6,
            primary_emotion="curious",
            secondary_emotions=["excited"]
        )
        
        with patch.object(client.client, 'post', return_value=mock_response) as mock_post:
            result = await client.generate_thought(
                stream_type=StreamType.PRIMARY,
                context={"topic": "consciousness"},
                emotional_state=emotional_state
            )
            
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == "http://localhost:8000/thoughts/generate"
            
            payload = call_args[1]['json']
            assert payload['stream_type'] == 'primary'
            assert payload['context'] == {"topic": "consciousness"}
            assert 'emotional_state' in payload
            assert result["thought"] == "Contemplating the nature of consciousness"
    
    @pytest.mark.asyncio
    async def test_generate_thought_minimal(self, client, mock_response):
        """Test thought generation with minimal parameters"""
        mock_response.json.return_value = {"thought": "A simple thought"}
        
        with patch.object(client.client, 'post', return_value=mock_response) as mock_post:
            result = await client.generate_thought()
            
            payload = mock_post.call_args[1]['json']
            assert payload['stream_type'] == 'primary'
            assert payload['context'] == {}
            assert 'emotional_state' not in payload
    
    @pytest.mark.asyncio
    async def test_query_memory(self, client, mock_response):
        """Test memory query"""
        mock_response.json.return_value = {
            "memories": [
                {"id": "mem1", "content": "First memory"},
                {"id": "mem2", "content": "Second memory"}
            ],
            "total": 2
        }
        
        with patch.object(client.client, 'post', return_value=mock_response) as mock_post:
            result = await client.query_memory(
                query="consciousness",
                memory_type=MemoryType.EPISODIC,
                limit=5
            )
            
            mock_post.assert_called_once()
            payload = mock_post.call_args[1]['json']
            assert payload['query'] == "consciousness"
            assert payload['memory_type'] == 'episodic'
            assert payload['limit'] == 5
            assert len(result['memories']) == 2
    
    @pytest.mark.asyncio
    async def test_get_recent_thoughts(self, client, mock_response):
        """Test getting recent thoughts"""
        mock_response.json.return_value = {
            "thoughts": [
                {"content": "Thought 1", "timestamp": "2025-06-04T12:00:00Z"},
                {"content": "Thought 2", "timestamp": "2025-06-04T12:01:00Z"}
            ]
        }
        
        with patch.object(client.client, 'get', return_value=mock_response) as mock_get:
            result = await client.get_recent_thoughts(limit=20, stream="primary")
            
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "thoughts/recent" in call_args[0][0]
            assert call_args[1]['params'] == {"limit": 20, "stream": "primary"}
    
    @pytest.mark.asyncio
    async def test_have_conversation(self, client, mock_response):
        """Test conversation endpoint"""
        mock_response.json.return_value = {
            "response": "I understand your question",
            "conversation_id": "conv123"
        }
        
        emotional_context = EmotionalState(
            valence=0.5,
            arousal=0.2,
            dominance=0.5,
            primary_emotion="calm"
        )
        
        with patch.object(client.client, 'post', return_value=mock_response) as mock_post:
            result = await client.have_conversation(
                message="What is consciousness?",
                conversation_id="conv123",
                emotional_context=emotional_context
            )
            
            mock_post.assert_called_once()
            payload = mock_post.call_args[1]['json']
            assert payload['message'] == "What is consciousness?"
            assert payload['conversation_id'] == "conv123"
            assert 'emotional_context' in payload
    
    @pytest.mark.asyncio
    async def test_consolidate_memory(self, client, mock_response):
        """Test memory consolidation"""
        mock_response.json.return_value = {
            "consolidated": 15,
            "status": "success"
        }
        
        with patch.object(client.client, 'post', return_value=mock_response) as mock_post:
            result = await client.consolidate_memory()
            
            mock_post.assert_called_once_with("http://localhost:8000/memory/consolidate")
            assert result['consolidated'] == 15
    
    @pytest.mark.asyncio
    async def test_pause_system(self, client, mock_response):
        """Test system pause"""
        mock_response.json.return_value = {"status": "paused"}
        
        with patch.object(client.client, 'post', return_value=mock_response) as mock_post:
            result = await client.pause_system()
            
            mock_post.assert_called_once_with("http://localhost:8000/system/pause")
            assert result['status'] == "paused"
    
    @pytest.mark.asyncio
    async def test_resume_system(self, client, mock_response):
        """Test system resume"""
        mock_response.json.return_value = {"status": "resumed"}
        
        with patch.object(client.client, 'post', return_value=mock_response) as mock_post:
            result = await client.resume_system()
            
            mock_post.assert_called_once_with("http://localhost:8000/system/resume")
            assert result['status'] == "resumed"
    
    @pytest.mark.asyncio
    async def test_sleep_system(self, client, mock_response):
        """Test system sleep"""
        mock_response.json.return_value = {"status": "sleeping"}
        
        with patch.object(client.client, 'post', return_value=mock_response) as mock_post:
            result = await client.sleep_system()
            
            mock_post.assert_called_once_with("http://localhost:8000/system/sleep")
            assert result['status'] == "sleeping"
    
    @pytest.mark.asyncio
    async def test_stream_consciousness(self, client):
        """Test consciousness streaming"""
        thoughts_received = []
        
        async def capture_thought(thought_data):
            thoughts_received.append(thought_data)
        
        # Mock websocket
        mock_ws = AsyncMock()
        mock_ws.__aiter__.return_value = [
            '{"thought": "First thought", "timestamp": "2025-06-04T12:00:00Z"}',
            '{"thought": "Second thought", "timestamp": "2025-06-04T12:00:01Z"}'
        ]
        
        with patch('websockets.connect') as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws
            await client.stream_consciousness(capture_thought)
        
        assert len(thoughts_received) == 2
        assert thoughts_received[0]['thought'] == "First thought"
        assert thoughts_received[1]['thought'] == "Second thought"
    
    @pytest.mark.asyncio
    async def test_error_handling(self, client):
        """Test error handling"""
        # Test HTTP error
        mock_response = Mock(spec=httpx.Response)
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=None, response=mock_response
        )
        
        with patch.object(client.client, 'get', return_value=mock_response):
            with pytest.raises(httpx.HTTPStatusError):
                await client.health_check()
    
    @pytest.mark.asyncio
    async def test_close_client(self, client):
        """Test closing client"""
        mock_aclose = AsyncMock()
        client.client.aclose = mock_aclose
        
        await client.close()
        mock_aclose.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_recent_thoughts_minimal(self, client, mock_response):
        """Test getting recent thoughts with minimal params"""
        mock_response.json.return_value = {"thoughts": []}
        
        with patch.object(client.client, 'get', return_value=mock_response) as mock_get:
            result = await client.get_recent_thoughts()
            
            call_args = mock_get.call_args
            assert call_args[1]['params'] == {"limit": 10}
    
    @pytest.mark.asyncio
    async def test_have_conversation_minimal(self, client, mock_response):
        """Test conversation with minimal params"""
        mock_response.json.return_value = {
            "response": "Hello!",
            "conversation_id": "new_conv"
        }
        
        with patch.object(client.client, 'post', return_value=mock_response) as mock_post:
            result = await client.have_conversation("Hello")
            
            payload = mock_post.call_args[1]['json']
            assert payload == {"message": "Hello"}
            assert 'conversation_id' not in payload
            assert 'emotional_context' not in payload