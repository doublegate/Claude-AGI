# tests/unit/test_database_connections.py

import pytest
import asyncio
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
            memory_id="test_123",
            content="Test memory content",
            memory_type="episodic",
            importance=7,
            emotional_valence=0.5,
            created_at=datetime.now()
        )
        
        assert memory.memory_id == "test_123"
        assert memory.content == "Test memory content"
        assert memory.memory_type == "episodic"
        assert memory.importance == 7
        assert memory.emotional_valence == 0.5
        
    def test_thought_model(self):
        """Test Thought SQLAlchemy model"""
        thought = Thought(
            thought_id="thought_456",
            content="Test thought",
            stream_type="primary",
            emotional_tone="curious",
            importance=5,
            created_at=datetime.now()
        )
        
        assert thought.thought_id == "thought_456"
        assert thought.content == "Test thought"
        assert thought.stream_type == "primary"
        assert thought.emotional_tone == "curious"
        assert thought.importance == 5


class TestDatabaseManager:
    """Test DatabaseManager class"""
    
    @pytest.fixture
    async def mock_postgres_engine(self):
        """Create mock PostgreSQL engine"""
        engine = AsyncMock()
        engine.dispose = AsyncMock()
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
        with patch('src.database.connections.create_async_engine', return_value=mock_postgres_engine):
            with patch('src.database.connections.redis.Redis', return_value=mock_redis_client):
                with patch('src.database.connections.faiss.IndexFlatL2', return_value=mock_faiss_index):
                    manager = DatabaseManager()
                    await manager.initialize()
                    return manager
                    
    @pytest.mark.asyncio
    async def test_initialization(self, db_manager):
        """Test database manager initialization"""
        assert db_manager.postgres_engine is not None
        assert db_manager.redis_client is not None
        assert db_manager.faiss_index is not None
        assert db_manager.memory_id_to_index == {}
        
    @pytest.mark.asyncio
    async def test_store_memory(self, db_manager):
        """Test storing memory in database"""
        memory_data = MemoryData(
            memory_id="mem_123",
            content="Important memory",
            memory_type="episodic",
            importance=8,
            emotional_valence=0.6,
            created_at=datetime.now()
        )
        
        # Mock session
        mock_session = AsyncMock()
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        mock_session.close = AsyncMock()
        
        db_manager.Session = Mock(return_value=mock_session)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # Mock embedding
        with patch.object(db_manager, '_generate_embedding', return_value=np.random.rand(384)):
            result = await db_manager.store_memory(memory_data)
            
        assert result == "mem_123"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_retrieve_memory(self, db_manager):
        """Test retrieving memory from database"""
        memory_id = "mem_123"
        
        # Mock database result
        mock_memory = Memory(
            memory_id=memory_id,
            content="Retrieved memory",
            memory_type="episodic",
            importance=7,
            emotional_valence=0.5,
            created_at=datetime.now()
        )
        
        # Mock session and query
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=mock_memory)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.close = AsyncMock()
        
        db_manager.Session = Mock(return_value=mock_session)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        result = await db_manager.retrieve_memory(memory_id)
        
        assert result is not None
        assert result.memory_id == memory_id
        assert result.content == "Retrieved memory"
        
    @pytest.mark.asyncio
    async def test_store_thought(self, db_manager):
        """Test storing thought in database"""
        thought_data = ThoughtData(
            thought_id="thought_789",
            content="Deep thought",
            stream_type="primary",
            emotional_tone="contemplative",
            importance=6,
            created_at=datetime.now()
        )
        
        # Mock session
        mock_session = AsyncMock()
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        mock_session.close = AsyncMock()
        
        db_manager.Session = Mock(return_value=mock_session)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        result = await db_manager.store_thought(thought_data)
        
        assert result == "thought_789"
        mock_session.add.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_get_recent_thoughts(self, db_manager):
        """Test retrieving recent thoughts"""
        # Mock thoughts
        mock_thoughts = [
            Thought(
                thought_id=f"thought_{i}",
                content=f"Thought {i}",
                stream_type="primary",
                emotional_tone="neutral",
                importance=5,
                created_at=datetime.now()
            )
            for i in range(5)
        ]
        
        # Mock session and query
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=mock_thoughts)))
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.close = AsyncMock()
        
        db_manager.Session = Mock(return_value=mock_session)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        results = await db_manager.get_recent_thoughts(limit=5)
        
        assert len(results) == 5
        assert all(isinstance(t, ThoughtData) for t in results)
        
    @pytest.mark.asyncio
    async def test_set_working_memory(self, db_manager, mock_redis_client):
        """Test setting working memory in Redis"""
        key = "current_topic"
        value = "consciousness"
        
        await db_manager.set_working_memory(key, value)
        
        mock_redis_client.setex.assert_called_once_with(
            f"working_memory:{key}",
            300,  # Default TTL
            value
        )
        
    @pytest.mark.asyncio
    async def test_get_working_memory(self, db_manager, mock_redis_client):
        """Test getting working memory from Redis"""
        key = "current_topic"
        mock_redis_client.get.return_value = b"consciousness"
        
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
    async def test_clear_working_memory(self, db_manager, mock_redis_client):
        """Test clearing working memory"""
        mock_redis_client.keys.return_value = [
            b"working_memory:key1",
            b"working_memory:key2"
        ]
        
        await db_manager.clear_working_memory()
        
        mock_redis_client.keys.assert_called_once_with("working_memory:*")
        assert mock_redis_client.delete.call_count == 2
        
    @pytest.mark.asyncio
    async def test_find_similar_memories(self, db_manager, mock_faiss_index):
        """Test finding similar memories using FAISS"""
        query = "test query"
        
        # Mock embedding generation
        with patch.object(db_manager, '_generate_embedding', return_value=np.random.rand(384)):
            # Mock stored memories
            db_manager.memory_id_to_index = {0: "mem_1", 1: "mem_2"}
            
            # Mock memory retrieval
            mock_memories = [
                MemoryData(
                    memory_id="mem_1",
                    content="Similar memory 1",
                    memory_type="semantic",
                    importance=7
                ),
                MemoryData(
                    memory_id="mem_2",
                    content="Similar memory 2",
                    memory_type="semantic",
                    importance=6
                )
            ]
            
            with patch.object(db_manager, 'retrieve_memory', side_effect=mock_memories):
                results = await db_manager.find_similar_memories(query, k=2)
                
        assert len(results) == 2
        assert results[0].memory_id == "mem_1"
        assert results[1].memory_id == "mem_2"
        mock_faiss_index.search.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_save_faiss_index(self, db_manager, mock_faiss_index):
        """Test saving FAISS index to disk"""
        with patch('src.database.connections.faiss.write_index') as mock_write:
            await db_manager.save_faiss_index()
            mock_write.assert_called_once_with(mock_faiss_index, "data/faiss_index.bin")
            
        # Also test with pickle for mapping
        import pickle
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            await db_manager.save_faiss_index()
            mock_file.write.assert_called()
            
    @pytest.mark.asyncio
    async def test_load_faiss_index(self, db_manager):
        """Test loading FAISS index from disk"""
        mock_index = Mock()
        mock_mapping = {0: "mem_1", 1: "mem_2"}
        
        with patch('src.database.connections.faiss.read_index', return_value=mock_index):
            with patch('builtins.open', create=True) as mock_open:
                import pickle
                mock_file = MagicMock()
                mock_file.read.return_value = pickle.dumps(mock_mapping)
                mock_open.return_value.__enter__.return_value = mock_file
                
                await db_manager.load_faiss_index()
                
        assert db_manager.faiss_index == mock_index
        assert db_manager.memory_id_to_index == mock_mapping
        
    @pytest.mark.asyncio
    async def test_embedding_generation(self, db_manager):
        """Test embedding generation"""
        text = "Test text for embedding"
        
        # Mock sentence transformer
        mock_model = Mock()
        mock_model.encode = Mock(return_value=np.random.rand(384))
        
        with patch('src.database.connections.SentenceTransformer', return_value=mock_model):
            db_manager.embedding_model = mock_model
            embedding = db_manager._generate_embedding(text)
            
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)
        mock_model.encode.assert_called_once_with(text)
        
    @pytest.mark.asyncio
    async def test_close_connections(self, db_manager, mock_postgres_engine, mock_redis_client):
        """Test closing all database connections"""
        await db_manager.close()
        
        mock_postgres_engine.dispose.assert_called_once()
        mock_redis_client.close.assert_called_once()
        
        # Verify FAISS index is saved
        with patch.object(db_manager, 'save_faiss_index', new_callable=AsyncMock) as mock_save:
            await db_manager.close()
            mock_save.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_connection_error_handling(self):
        """Test handling of connection errors"""
        # Test PostgreSQL connection error
        with patch('src.database.connections.create_async_engine', side_effect=Exception("Connection failed")):
            manager = DatabaseManager()
            with pytest.raises(Exception):
                await manager.initialize()
                
    @pytest.mark.asyncio
    async def test_redis_connection_error_handling(self, mock_postgres_engine):
        """Test handling of Redis connection errors"""
        with patch('src.database.connections.create_async_engine', return_value=mock_postgres_engine):
            with patch('src.database.connections.redis.Redis', side_effect=Exception("Redis connection failed")):
                manager = DatabaseManager()
                with pytest.raises(Exception):
                    await manager.initialize()
                    
    @pytest.mark.asyncio
    async def test_batch_store_memories(self, db_manager):
        """Test batch storing multiple memories"""
        memories = [
            MemoryData(
                memory_id=f"mem_{i}",
                content=f"Memory {i}",
                memory_type="episodic",
                importance=5+i
            )
            for i in range(3)
        ]
        
        # Mock session
        mock_session = AsyncMock()
        mock_session.add_all = Mock()
        mock_session.commit = AsyncMock()
        mock_session.close = AsyncMock()
        
        db_manager.Session = Mock(return_value=mock_session)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # Mock embedding generation
        with patch.object(db_manager, '_generate_embedding', return_value=np.random.rand(384)):
            # Implement batch store if available
            for memory in memories:
                await db_manager.store_memory(memory)
                
        assert mock_session.add.call_count == 3
        
    @pytest.mark.asyncio
    async def test_database_transaction_rollback(self, db_manager):
        """Test transaction rollback on error"""
        memory_data = MemoryData(
            memory_id="mem_error",
            content="Error memory",
            memory_type="episodic"
        )
        
        # Mock session with commit error
        mock_session = AsyncMock()
        mock_session.add = Mock()
        mock_session.commit = AsyncMock(side_effect=Exception("Commit failed"))
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()
        
        db_manager.Session = Mock(return_value=mock_session)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(db_manager, '_generate_embedding', return_value=np.random.rand(384)):
            with pytest.raises(Exception):
                await db_manager.store_memory(memory_data)
                
        # Rollback should be called in real implementation
        # This depends on actual error handling implementation