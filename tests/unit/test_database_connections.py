# tests/unit/test_database_connections.py

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import numpy as np
import redis
import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connections import DatabaseManager, Memory, Thought
from src.database.models import MemoryData, ThoughtData, EmotionalState


class TestDatabaseModels:
    """Test SQLAlchemy models"""
    
    def test_memory_model(self):
        """Test Memory SQLAlchemy model"""
        memory = Memory(
            content="Test memory content",
            memory_type="episodic",
            importance=0.7,
            emotional_valence=0.5,
            timestamp=datetime.now()
        )
        
        assert memory.content == "Test memory content"
        assert memory.memory_type == "episodic"
        assert memory.importance == 0.7
        assert memory.emotional_valence == 0.5
        
    def test_thought_model(self):
        """Test Thought SQLAlchemy model"""
        thought = Thought(
            content="Test thought",
            stream_type="primary",
            emotional_state={"valence": 0.5, "arousal": 0.3},
            timestamp=datetime.now()
        )
        
        assert thought.content == "Test thought"
        assert thought.stream_type == "primary"
        assert thought.emotional_state is not None


class TestDatabaseManager:
    """Test DatabaseManager class"""
    
    @pytest.fixture
    async def mock_postgres_engine(self):
        """Create mock PostgreSQL engine"""
        engine = AsyncMock()
        engine.dispose = AsyncMock()
        
        # Mock the begin() method to return an async context manager
        mock_conn = AsyncMock()
        mock_conn.run_sync = AsyncMock()
        
        mock_begin_context = AsyncMock()
        mock_begin_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_begin_context.__aexit__ = AsyncMock(return_value=None)
        
        engine.begin = Mock(return_value=mock_begin_context)
        
        return engine
        
    @pytest.fixture
    def mock_redis_client(self):
        """Create mock Redis client"""
        client = Mock()
        client.ping = AsyncMock(return_value=True)
        client.set = AsyncMock(return_value=True)
        client.get = AsyncMock()
        client.setex = AsyncMock(return_value=True)
        client.delete = AsyncMock()
        client.keys = AsyncMock(return_value=[])
        client.mget = AsyncMock(return_value=[])
        client.close = AsyncMock()
        return client
        
    @pytest.fixture
    def mock_faiss_index(self):
        """Create mock FAISS index"""
        index = Mock()
        index.ntotal = 0
        index.d = 384  # Embedding dimension
        index.add = Mock()
        index.search = Mock(return_value=(np.array([[0.9, 0.8]]), np.array([[0, 1]])))
        return index
        
    @pytest.fixture
    async def db_manager(self, mock_postgres_engine, mock_redis_client, mock_faiss_index):
        """Create DatabaseManager with mocked connections"""
        # Mock async_sessionmaker
        mock_session = AsyncMock()
        mock_session_factory = Mock(return_value=mock_session)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('src.database.connections.create_async_engine', return_value=mock_postgres_engine):
            with patch('src.database.connections.redis.from_url', AsyncMock(return_value=mock_redis_client)):
                with patch('src.database.connections.faiss.IndexFlatIP', return_value=mock_faiss_index):
                    with patch('src.database.connections.async_sessionmaker', return_value=mock_session_factory):
                        manager = DatabaseManager()
                        await manager.initialize()
                        return manager
                    
    @pytest.mark.asyncio
    async def test_initialization(self, db_manager):
        """Test database manager initialization"""
        assert db_manager.engine is not None
        assert db_manager.redis_client is not None
        assert db_manager.faiss_index is not None
        assert db_manager._initialized is True
        
    @pytest.mark.asyncio
    async def test_store_memory(self, db_manager):
        """Test storing memory in database"""
        memory_data = {
            'memory_type': 'episodic',
            'content': 'Important memory',
            'importance': 0.8,
            'emotional_valence': 0.6,
            'embedding': [0.1] * 768  # Mock embedding
        }
        
        # Mock the session and memory object
        mock_memory = Mock()
        mock_memory.id = 123
        
        mock_session = AsyncMock()
        mock_session.add = Mock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        
        # Patch the get_session method to return our mock
        with patch.object(db_manager, 'get_session') as mock_get_session:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_get_session.return_value = mock_context
            
            # Patch Memory constructor
            with patch('src.database.connections.Memory', return_value=mock_memory):
                # Mock FAISS operations
                db_manager.faiss_index.add_with_ids = Mock()
                
                result = await db_manager.store_memory(memory_data)
            
        assert result == 123
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_search_similar_memories(self, db_manager):
        """Test searching for similar memories"""
        embedding = [0.1] * 768
        
        # Mock FAISS search results
        db_manager.faiss_index.ntotal = 2
        db_manager.faiss_index.search = Mock(
            return_value=(np.array([[0.9, 0.8]]), np.array([[1, 2]]))
        )
        
        # Mock database query results
        mock_memories = [
            Mock(_mapping={'id': 1, 'content': 'Memory 1', 'memory_type': 'episodic'}),
            Mock(_mapping={'id': 2, 'content': 'Memory 2', 'memory_type': 'semantic'})
        ]
        
        mock_result = Mock()
        mock_result.fetchall = Mock(return_value=mock_memories)
        
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        with patch.object(db_manager, 'get_session') as mock_get_session:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_get_session.return_value = mock_context
            
            results = await db_manager.search_similar_memories(embedding, k=2)
        
        assert len(results) == 2
        assert results[0]['similarity_score'] == 0.9
        assert results[1]['similarity_score'] == 0.8
        
    @pytest.mark.asyncio
    async def test_add_thought(self, db_manager):
        """Test adding thought to database"""
        thought_data = {
            'content': 'Deep thought',
            'emotional_state': {'valence': 0.7, 'arousal': 0.5},
            'context': {'topic': 'consciousness'},
            'memory_references': []
        }
        
        # Mock Redis operations
        db_manager.redis_client.lpush = AsyncMock()
        db_manager.redis_client.ltrim = AsyncMock()
        
        # Mock session
        mock_session = AsyncMock()
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        
        with patch.object(db_manager, 'get_session') as mock_get_session:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_get_session.return_value = mock_context
            
            with patch('src.database.connections.Thought') as mock_thought:
                await db_manager.add_thought('primary', thought_data)
        
        # Verify Redis operations
        db_manager.redis_client.lpush.assert_called_once()
        db_manager.redis_client.ltrim.assert_called_once()
        mock_session.add.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_get_recent_thoughts(self, db_manager):
        """Test retrieving recent thoughts"""
        # Mock Redis response
        mock_thoughts = [
            json.dumps({
                'content': f'Thought {i}',
                'stream_type': 'primary',
                'emotional_state': {'valence': 0.5}
            })
            for i in range(5)
        ]
        
        db_manager.redis_client.lrange = AsyncMock(return_value=mock_thoughts)
        
        results = await db_manager.get_recent_thoughts('primary', limit=5)
        
        assert len(results) == 5
        assert all(isinstance(t, dict) for t in results)
        assert results[0]['content'] == 'Thought 0'
        
    @pytest.mark.asyncio
    async def test_set_working_memory(self, db_manager, mock_redis_client):
        """Test setting working memory in Redis"""
        key = "current_topic"
        value = "consciousness"
        
        await db_manager.set_working_memory(key, value)
        
        mock_redis_client.setex.assert_called_once_with(
            f"working_memory:{key}",
            86400,  # Default TTL is 24 hours
            value
        )
        
    @pytest.mark.asyncio
    async def test_get_working_memory(self, db_manager, mock_redis_client):
        """Test getting working memory from Redis"""
        key = "current_topic"
        mock_redis_client.get = AsyncMock(return_value="consciousness")
        
        result = await db_manager.get_working_memory(key)
        
        assert result == "consciousness"
        mock_redis_client.get.assert_called_once_with(f"working_memory:{key}")
        
    @pytest.mark.asyncio
    async def test_get_working_memory_not_found(self, db_manager, mock_redis_client):
        """Test getting non-existent working memory"""
        mock_redis_client.get.return_value = None
        
        result = await db_manager.get_working_memory("nonexistent")
        
        assert result is None
        
    @pytest.mark.asyncio
    async def test_close_connections(self, db_manager):
        """Test closing database connections"""
        # Set up initial state
        db_manager.faiss_index.ntotal = 10
        
        # Mock the write_index function
        with patch('src.database.connections.faiss.write_index') as mock_write:
            await db_manager.close()
        
        # Verify connections were closed
        db_manager.engine.dispose.assert_called_once()
        db_manager.redis_client.close.assert_called_once()
        mock_write.assert_called_once()
        assert db_manager._initialized is False


class TestDatabaseErrors:
    """Test error handling in database operations"""
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self):
        """Test handling of connection errors"""
        # Test PostgreSQL connection error
        with patch('src.database.connections.create_async_engine', side_effect=Exception("Connection failed")):
            manager = DatabaseManager()
            with pytest.raises(Exception):
                await manager.initialize()
                
    @pytest.mark.asyncio
    async def test_redis_connection_error_handling(self):
        """Test handling of Redis connection errors"""
        mock_engine = AsyncMock()
        mock_engine.dispose = AsyncMock()
        
        # Mock the begin() method
        mock_conn = AsyncMock()
        mock_conn.run_sync = AsyncMock()
        mock_begin_context = AsyncMock()
        mock_begin_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_begin_context.__aexit__ = AsyncMock(return_value=None)
        mock_engine.begin = Mock(return_value=mock_begin_context)
        
        with patch('src.database.connections.create_async_engine', return_value=mock_engine):
            with patch('src.database.connections.async_sessionmaker'):
                with patch('src.database.connections.redis.from_url', side_effect=Exception("Redis connection failed")):
                    manager = DatabaseManager()
                    with pytest.raises(Exception):
                        await manager.initialize()
                    
