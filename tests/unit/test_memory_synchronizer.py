"""
Unit tests for the Memory Synchronizer
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import redis.asyncio as redis
import asyncpg
import numpy as np

from src.memory.synchronizer import (
    MemorySynchronizer,
    SyncStatus,
    MemoryVersion,
    SyncTransaction,
    ConflictResolution
)
from src.core.service_registry import ServiceRegistry
from src.core.event_bus import EventBus


class TestMemorySynchronizer:
    """Test suite for MemorySynchronizer"""
    
    @pytest.fixture
    async def mock_redis(self):
        """Create mock Redis client"""
        mock = AsyncMock(spec=redis.Redis)
        mock.hget = AsyncMock(return_value=None)
        mock.hset = AsyncMock(return_value=True)
        mock.sadd = AsyncMock(return_value=1)
        mock.expire = AsyncMock(return_value=True)
        mock.hkeys = AsyncMock(return_value=[])
        mock.smembers = AsyncMock(return_value=set())
        return mock
    
    @pytest.fixture
    async def mock_postgres(self):
        """Create mock PostgreSQL pool"""
        mock_pool = AsyncMock(spec=asyncpg.Pool)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_conn.fetchrow = AsyncMock(return_value=None)
        mock_conn.fetchval = AsyncMock(return_value=1)
        
        mock_pool.acquire = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock()
        
        return mock_pool
    
    @pytest.fixture
    def mock_faiss(self):
        """Create mock FAISS index"""
        mock = MagicMock()
        mock.add = MagicMock()
        return mock
    
    @pytest.fixture
    async def synchronizer(self, mock_redis, mock_postgres, mock_faiss):
        """Create MemorySynchronizer instance"""
        service_registry = ServiceRegistry()
        event_bus = EventBus()
        
        sync = MemorySynchronizer(
            redis_client=mock_redis,
            postgres_pool=mock_postgres,
            faiss_index=mock_faiss,
            service_registry=service_registry,
            event_bus=event_bus
        )
        
        await sync.initialize()
        yield sync
        await sync.shutdown()
    
    @pytest.mark.asyncio
    async def test_initialization(self, synchronizer):
        """Test synchronizer initialization"""
        assert synchronizer._sync_task is not None
        assert synchronizer._consistency_task is not None
        assert synchronizer.batch_size == 100
        assert synchronizer.sync_interval == 5.0
    
    @pytest.mark.asyncio
    async def test_sync_memory_success(self, synchronizer, mock_redis, mock_postgres):
        """Test successful memory synchronization"""
        memory_id = "test_memory_123"
        memory_data = {
            "content": "Test memory content",
            "memory_type": "episodic",
            "importance": 0.8,
            "embedding": [0.1, 0.2, 0.3]
        }
        
        result = await synchronizer.sync_memory(memory_id, memory_data)
        
        assert result is True
        assert mock_redis.hset.called
        assert mock_redis.sadd.called
        assert mock_postgres.acquire.called
        
        # Check version was updated
        version = synchronizer._versions.get(memory_id)
        assert version is not None
        assert version.version == 2  # Incremented from default 1
        assert "redis" in version.store_versions
        assert "postgres" in version.store_versions
        assert "faiss" in version.store_versions
    
    @pytest.mark.asyncio
    async def test_sync_memory_with_ttl(self, synchronizer, mock_redis):
        """Test memory sync with TTL"""
        memory_id = "temp_memory"
        memory_data = {
            "content": "Temporary memory",
            "ttl": 3600  # 1 hour
        }
        
        await synchronizer.sync_memory(memory_id, memory_data)
        
        mock_redis.expire.assert_called_with(f"memory:{memory_id}", 3600)
    
    @pytest.mark.asyncio
    async def test_sync_memory_conflict_detection(self, synchronizer, mock_redis):
        """Test conflict detection during sync"""
        memory_id = "conflict_memory"
        
        # Set up existing memory with different checksum
        existing_data = {"content": "Old content"}
        mock_redis.hget.return_value = json.dumps(existing_data)
        
        new_data = {"content": "New content"}
        
        # Should still succeed with LATEST_WINS strategy
        result = await synchronizer.sync_memory(memory_id, new_data)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_sync_batch(self, synchronizer):
        """Test batch synchronization"""
        memories = [
            {"memory_id": "mem1", "content": "Memory 1"},
            {"memory_id": "mem2", "content": "Memory 2"},
            {"memory_id": "mem3", "content": "Memory 3"}
        ]
        
        results = await synchronizer.sync_batch(memories)
        
        assert len(results) == 3
        assert all(results.values())  # All should succeed
    
    @pytest.mark.asyncio
    async def test_check_consistency(self, synchronizer, mock_redis, mock_postgres):
        """Test consistency checking"""
        # Set up inconsistent state
        mock_redis.hkeys.return_value = ["mem1", "mem2"]
        mock_postgres.acquire.return_value.__aenter__.return_value.fetch.return_value = [
            {"memory_id": "mem2"},
            {"memory_id": "mem3"}
        ]
        
        inconsistencies = await synchronizer.check_consistency()
        
        # mem1 is only in Redis, mem3 is only in Postgres
        assert len(inconsistencies) >= 2
    
    @pytest.mark.asyncio
    async def test_repair_inconsistencies(self, synchronizer, mock_postgres):
        """Test inconsistency repair"""
        inconsistencies = {
            "mem1": ["postgres", "faiss"],
            "mem2": ["redis"]
        }
        
        # Mock getting latest version
        mock_postgres.acquire.return_value.__aenter__.return_value.fetchrow.return_value = {
            "memory_id": "mem1",
            "content": "Memory content"
        }
        
        results = await synchronizer.repair_inconsistencies(inconsistencies)
        
        assert "mem1" in results
        # Results depend on mock behavior
    
    @pytest.mark.asyncio
    async def test_sync_to_redis(self, synchronizer, mock_redis):
        """Test Redis synchronization"""
        memory_id = "redis_test"
        memory_data = {
            "content": "Test content",
            "memory_type": "working"
        }
        
        result = await synchronizer._sync_to_redis(memory_id, memory_data)
        
        assert result is True
        mock_redis.hset.assert_called_with(
            "working_memory",
            memory_id,
            json.dumps(memory_data)
        )
        mock_redis.sadd.assert_called_with("memory_type:working", memory_id)
    
    @pytest.mark.asyncio
    async def test_sync_to_postgres(self, synchronizer, mock_postgres):
        """Test PostgreSQL synchronization"""
        memory_id = "postgres_test"
        memory_data = {
            "content": "Test content",
            "memory_type": "episodic",
            "importance": 0.7,
            "emotional_valence": 0.2,
            "metadata": {"source": "test"},
            "timestamp": datetime.now(timezone.utc)
        }
        
        result = await synchronizer._sync_to_postgres(memory_id, memory_data)
        
        assert result is True
        assert mock_postgres.acquire.called
    
    @pytest.mark.asyncio
    async def test_sync_to_faiss(self, synchronizer, mock_faiss):
        """Test FAISS synchronization"""
        memory_id = "faiss_test"
        memory_data = {
            "content": "Test content",
            "embedding": [0.1, 0.2, 0.3, 0.4]
        }
        
        result = await synchronizer._sync_to_faiss(memory_id, memory_data)
        
        assert result is True
        mock_faiss.add.assert_called_once()
        
        # Check the embedding was properly formatted
        call_args = mock_faiss.add.call_args[0][0]
        assert isinstance(call_args, np.ndarray)
        assert call_args.shape == (1, 4)
    
    @pytest.mark.asyncio
    async def test_calculate_checksum(self, synchronizer):
        """Test checksum calculation"""
        data1 = {"content": "Test", "value": 123}
        data2 = {"value": 123, "content": "Test"}  # Different order
        data3 = {"content": "Different", "value": 123}
        
        checksum1 = synchronizer._calculate_checksum(data1)
        checksum2 = synchronizer._calculate_checksum(data2)
        checksum3 = synchronizer._calculate_checksum(data3)
        
        # Same data different order should have same checksum
        assert checksum1 == checksum2
        # Different data should have different checksum
        assert checksum1 != checksum3
    
    @pytest.mark.asyncio
    async def test_transaction_tracking(self, synchronizer):
        """Test transaction tracking"""
        memory_id = "transaction_test"
        memory_data = {"content": "Test"}
        
        # Start sync
        task = asyncio.create_task(
            synchronizer.sync_memory(memory_id, memory_data)
        )
        
        # Give it a moment to start
        await asyncio.sleep(0.1)
        
        # Should have active transaction
        assert len(synchronizer._active_transactions) > 0
        
        # Wait for completion
        await task
        
        # Should be cleared
        assert len(synchronizer._active_transactions) == 0
    
    @pytest.mark.asyncio
    async def test_rollback_on_failure(self, synchronizer, mock_redis, mock_postgres):
        """Test rollback on sync failure"""
        memory_id = "rollback_test"
        memory_data = {"content": "Test"}
        
        # Set up existing data for rollback
        existing_data = {"content": "Original"}
        mock_redis.hget.return_value = json.dumps(existing_data)
        
        # Make postgres fail
        mock_postgres.acquire.side_effect = Exception("Database error")
        
        result = await synchronizer.sync_memory(memory_id, memory_data)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_conflict_resolution_strategies(self, synchronizer):
        """Test different conflict resolution strategies"""
        # Test LATEST_WINS (default)
        assert synchronizer._conflict_resolution == ConflictResolution.LATEST_WINS
        
        memory_id = "conflict_test"
        memory_data = {"content": "Latest"}
        conflicts = ["redis", "postgres"]
        
        resolved = await synchronizer._resolve_conflicts(
            memory_id, memory_data, conflicts
        )
        
        assert resolved == memory_data
        
        # Test MERGE strategy
        synchronizer._conflict_resolution = ConflictResolution.MERGE
        resolved = await synchronizer._resolve_conflicts(
            memory_id, memory_data, conflicts
        )
        
        # For now, returns the original data
        assert resolved == memory_data
    
    @pytest.mark.asyncio
    async def test_version_management(self, synchronizer):
        """Test version tracking"""
        memory_id = "version_test"
        
        # Initial version
        version = MemoryVersion(memory_id=memory_id, checksum="abc123")
        synchronizer._versions[memory_id] = version
        
        assert version.version == 1
        
        # Sync should increment version
        memory_data = {"content": "Updated"}
        await synchronizer.sync_memory(memory_id, memory_data)
        
        updated_version = synchronizer._versions[memory_id]
        assert updated_version.version == 2
        assert updated_version.checksum != "abc123"
    
    @pytest.mark.asyncio
    async def test_event_publishing(self, synchronizer):
        """Test event publishing on successful sync"""
        memory_id = "event_test"
        memory_data = {"content": "Test"}
        
        # Spy on event bus
        publish_calls = []
        synchronizer.event_bus.publish = AsyncMock(
            side_effect=lambda event, data: publish_calls.append((event, data))
        )
        
        await synchronizer.sync_memory(memory_id, memory_data)
        
        # Should publish sync event
        assert len(publish_calls) == 1
        assert publish_calls[0][0] == "memory.synchronized"
        assert publish_calls[0][1]["memory_id"] == memory_id
    
    @pytest.mark.asyncio
    async def test_get_pending_syncs(self, synchronizer, mock_redis):
        """Test getting pending synchronizations"""
        # Set up pending sync queue
        mock_redis.smembers.return_value = {"mem1", "mem2"}
        mock_redis.hget.side_effect = [
            json.dumps({"content": "Memory 1"}),
            json.dumps({"content": "Memory 2"})
        ]
        
        pending = await synchronizer._get_pending_syncs()
        
        assert len(pending) == 2
        assert pending[0]["memory_id"] == "mem1"
        assert pending[1]["memory_id"] == "mem2"
    
    @pytest.mark.asyncio
    async def test_sync_with_no_embedding(self, synchronizer, mock_faiss):
        """Test sync when memory has no embedding"""
        memory_id = "no_embedding"
        memory_data = {"content": "Test without embedding"}
        
        result = await synchronizer.sync_memory(memory_id, memory_data)
        
        assert result is True
        # FAISS should not be called
        mock_faiss.add.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_concurrent_syncs(self, synchronizer):
        """Test handling concurrent synchronizations"""
        memories = [
            {"memory_id": f"concurrent_{i}", "content": f"Memory {i}"}
            for i in range(10)
        ]
        
        # Sync all concurrently
        tasks = [
            synchronizer.sync_memory(m["memory_id"], m)
            for m in memories
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert all(results)
        assert len(synchronizer._versions) == 10