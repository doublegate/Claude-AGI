"""
Integration Tests for Refactored Memory Components
==================================================

Tests the integration between MemoryManager and its refactored components:
- WorkingMemoryStore
- EpisodicMemoryStore
- SemanticIndex
- MemoryCoordinator
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, List

from src.memory.working_memory_store import WorkingMemoryStore
from src.memory.episodic_memory_store import EpisodicMemoryStore
from src.memory.semantic_index import SemanticIndex
from src.memory.memory_coordinator import MemoryCoordinator
from src.memory.manager_refactored import MemoryManager


class TestWorkingMemoryStoreIntegration:
    """Test WorkingMemoryStore integration"""

    @pytest.fixture
    def working_memory(self):
        """Create working memory store (in-memory mode)"""
        return WorkingMemoryStore(db_manager=None, use_database=False)

    @pytest.mark.asyncio
    async def test_store_and_recall_thought(self, working_memory):
        """Test storing and recalling thoughts"""
        thought = {
            'content': 'Test thought content',
            'stream': 'primary',
            'timestamp': datetime.now().isoformat()
        }

        # Store thought
        thought_id = await working_memory.store_thought(thought)
        assert thought_id is not None

        # Recall thought
        recalled = await working_memory.recall_by_id(thought_id)
        assert recalled is not None
        assert recalled['content'] == 'Test thought content'

    @pytest.mark.asyncio
    async def test_recall_recent_thoughts(self, working_memory):
        """Test recalling recent thoughts"""
        # Store multiple thoughts
        for i in range(5):
            await working_memory.store_thought({
                'content': f'Thought {i}',
                'stream': 'primary',
                'timestamp': datetime.now().isoformat()
            })

        # Recall recent
        recent = await working_memory.recall_recent(n=3)
        assert len(recent) == 3
        # Should be in reverse chronological order
        assert recent[0]['content'] == 'Thought 4'

    @pytest.mark.asyncio
    async def test_context_management(self, working_memory):
        """Test active context storage and retrieval"""
        await working_memory.update_context('user_name', 'Alice')
        await working_memory.update_context('topic', 'AI Ethics')

        name = await working_memory.get_context('user_name')
        topic = await working_memory.get_context('topic')

        assert name == 'Alice'
        assert topic == 'AI Ethics'

    @pytest.mark.asyncio
    async def test_clear_working_memory(self, working_memory):
        """Test clearing working memory"""
        # Store thoughts
        await working_memory.store_thought({'content': 'Test', 'timestamp': datetime.now().isoformat()})

        # Clear
        await working_memory.clear()

        # Should be empty
        recent = await working_memory.recall_recent(n=10)
        assert len(recent) == 0


class TestEpisodicMemoryStoreIntegration:
    """Test EpisodicMemoryStore integration"""

    @pytest.fixture
    def episodic_memory(self):
        """Create episodic memory store (in-memory mode)"""
        return EpisodicMemoryStore(db_manager=None, embedder=None, use_database=False)

    @pytest.mark.asyncio
    async def test_store_and_recall_memory(self, episodic_memory):
        """Test storing and recalling long-term memory"""
        memory_data = {
            'id': 'mem_test_1',
            'content': 'Important long-term memory',
            'importance': 0.8,
            'memory_type': 'episodic',
            'context': {'event': 'test'}
        }

        # Store memory
        memory_id = await episodic_memory.store_memory(memory_data)
        assert memory_id == 'mem_test_1'

        # Recall memory
        recalled = await episodic_memory.recall_by_id(memory_id)
        assert recalled is not None
        assert recalled['content'] == 'Important long-term memory'
        assert recalled['importance'] == 0.8

    @pytest.mark.asyncio
    async def test_recall_recent_memories(self, episodic_memory):
        """Test recalling recent long-term memories"""
        # Store multiple memories
        for i in range(5):
            await episodic_memory.store_memory({
                'id': f'mem_{i}',
                'content': f'Memory {i}',
                'importance': 0.5,
                'memory_type': 'episodic'
            })

        # Recall recent
        recent = await episodic_memory.recall_recent(n=3)
        assert len(recent) == 3

    @pytest.mark.asyncio
    async def test_recall_important_memories(self, episodic_memory):
        """Test recalling important memories"""
        # Store memories with varying importance
        await episodic_memory.store_memory({
            'id': 'mem_low',
            'content': 'Low importance',
            'importance': 0.3,
            'memory_type': 'episodic'
        })
        await episodic_memory.store_memory({
            'id': 'mem_high',
            'content': 'High importance',
            'importance': 0.9,
            'memory_type': 'episodic'
        })

        # Recall important (threshold 0.7)
        important = await episodic_memory.recall_important(threshold=0.7, limit=10)
        assert len(important) == 1
        assert important[0]['id'] == 'mem_high'

    @pytest.mark.asyncio
    async def test_memory_type_filtering(self, episodic_memory):
        """Test filtering memories by type"""
        await episodic_memory.store_memory({
            'id': 'mem_episodic',
            'content': 'Episodic memory',
            'memory_type': 'episodic'
        })
        await episodic_memory.store_memory({
            'id': 'mem_semantic',
            'content': 'Semantic memory',
            'memory_type': 'semantic'
        })

        # Recall episodic only
        episodic = await episodic_memory.recall_recent(n=10, memory_type='episodic')
        assert all(m['memory_type'] == 'episodic' for m in episodic)


class TestSemanticIndexIntegration:
    """Test SemanticIndex integration"""

    @pytest.fixture
    def semantic_index(self):
        """Create semantic index (simple vector store mode)"""
        index = SemanticIndex(embedder=None, use_faiss=False)
        return index

    @pytest.mark.asyncio
    async def test_semantic_index_initialization(self, semantic_index):
        """Test semantic index initializes correctly"""
        await semantic_index.initialize()
        assert semantic_index.simple_store is not None

    @pytest.mark.asyncio
    async def test_add_and_search_without_embedder(self, semantic_index):
        """Test adding content without embedder falls back gracefully"""
        await semantic_index.initialize()

        # Without embedder, add should fail gracefully
        result = await semantic_index.add('mem_1', 'Test content', {})
        # Should return False since no embedder
        assert result is False

    @pytest.mark.asyncio
    async def test_similarity_calculation_without_embedder(self, semantic_index):
        """Test similarity calculation without embedder"""
        await semantic_index.initialize()

        # Without embedder, should return 0.0
        similarity = await semantic_index.calculate_similarity('text1', 'text2')
        assert similarity == 0.0

    @pytest.mark.asyncio
    async def test_get_statistics(self, semantic_index):
        """Test getting semantic index statistics"""
        await semantic_index.initialize()

        stats = await semantic_index.get_statistics()
        assert 'has_embedder' in stats
        assert 'using_faiss' in stats
        assert 'simple_store_size' in stats
        assert stats['has_embedder'] is False  # No embedder in test
        assert stats['using_faiss'] is False   # No FAISS in test


class TestMemoryCoordinatorIntegration:
    """Test MemoryCoordinator integration - simplified to test via MemoryManager"""

    @pytest.mark.asyncio
    async def test_coordinator_via_memory_manager(self):
        """Test coordinator functionality through MemoryManager interface"""
        manager = MemoryManager()
        await manager.initialize(use_database=False)

        # Test that coordinator was created
        coordinator = manager.get_coordinator()
        assert coordinator is not None

        # Test storing thought through manager (which uses coordinator)
        thought = {
            'content': 'Coordinator test thought',
            'stream': 'primary',
            'timestamp': datetime.now().isoformat(),
            'importance': 5
        }

        thought_id = await manager.store_thought(thought)
        assert thought_id is not None

        # Test recalling thought
        recalled = await manager.recall_by_id(thought_id)
        assert recalled is not None
        assert recalled['content'] == 'Coordinator test thought'

        await manager.close()

    @pytest.mark.asyncio
    async def test_coordinator_stores_integration(self):
        """Test that coordinator integrates working, episodic, and semantic stores"""
        manager = MemoryManager()
        await manager.initialize(use_database=False)

        # Verify all stores are available through manager
        working = manager.get_working_memory()
        episodic = manager.get_episodic_memory()
        semantic = manager.get_semantic_index()

        assert isinstance(working, WorkingMemoryStore)
        assert isinstance(episodic, EpisodicMemoryStore)
        assert isinstance(semantic, SemanticIndex)

        await manager.close()


class TestRefactoredMemoryManagerIntegration:
    """Test complete MemoryManager integration with all components"""

    @pytest.mark.asyncio
    async def test_memory_manager_initialization(self):
        """Test memory manager initializes all components"""
        manager = MemoryManager()
        await manager.initialize(use_database=False)

        assert manager.working_memory is not None
        assert manager.episodic_memory is not None
        assert manager.semantic_index is not None
        assert manager.coordinator is not None

    @pytest.mark.asyncio
    async def test_memory_manager_store_thought(self):
        """Test storing thought through memory manager"""
        manager = MemoryManager()
        await manager.initialize(use_database=False)

        thought = {
            'content': 'Manager test thought',
            'stream': 'primary',
            'timestamp': datetime.now().isoformat(),
            'importance': 6
        }

        thought_id = await manager.store_thought(thought)
        assert thought_id is not None

    @pytest.mark.asyncio
    async def test_memory_manager_recall_recent(self):
        """Test recalling recent through memory manager"""
        manager = MemoryManager()
        await manager.initialize(use_database=False)

        # Store thoughts
        for i in range(5):
            await manager.store_thought({
                'content': f'Thought {i}',
                'stream': 'primary',
                'timestamp': datetime.now().isoformat()
            })

        # Recall recent
        recent = await manager.recall_recent(n=3)
        assert len(recent) == 3

    @pytest.mark.asyncio
    async def test_memory_manager_recall_by_id(self):
        """Test recalling specific thought by ID"""
        manager = MemoryManager()
        await manager.initialize(use_database=False)

        thought = {
            'content': 'Specific thought',
            'stream': 'primary',
            'timestamp': datetime.now().isoformat()
        }

        thought_id = await manager.store_thought(thought)
        recalled = await manager.recall_by_id(thought_id)

        assert recalled is not None
        assert recalled['content'] == 'Specific thought'

    @pytest.mark.asyncio
    async def test_memory_manager_consolidation(self):
        """Test memory consolidation through manager"""
        manager = MemoryManager()
        await manager.initialize(use_database=False)

        # Store important thought
        await manager.store_thought({
            'content': 'Important memory',
            'stream': 'primary',
            'timestamp': datetime.now().isoformat(),
            'importance': 8
        })

        # Consolidate
        await manager.consolidate_memories()

        # Should complete without error
        stats = await manager.get_statistics()
        assert 'total_thoughts' in stats

    @pytest.mark.asyncio
    async def test_memory_manager_context_operations(self):
        """Test context operations through manager"""
        manager = MemoryManager()
        await manager.initialize(use_database=False)

        await manager.update_context('test_key', 'test_value')
        value = await manager.get_context('test_key')

        assert value == 'test_value'

    @pytest.mark.asyncio
    async def test_memory_manager_clear_working_memory(self):
        """Test clearing working memory through manager"""
        manager = MemoryManager()
        await manager.initialize(use_database=False)

        # Store thought
        await manager.store_thought({
            'content': 'To be cleared',
            'timestamp': datetime.now().isoformat()
        })

        # Clear
        await manager.clear_working_memory()

        # Should be empty
        recent = await manager.recall_recent(n=10)
        assert len(recent) == 0

    @pytest.mark.asyncio
    async def test_memory_manager_statistics(self):
        """Test getting statistics through manager"""
        manager = MemoryManager()
        await manager.initialize(use_database=False)

        stats = await manager.get_statistics()

        assert isinstance(stats, dict)
        assert 'working_memory' in stats
        assert 'episodic_memory' in stats
        assert 'semantic_index' in stats

    @pytest.mark.asyncio
    async def test_memory_manager_backwards_compatibility(self):
        """Test backwards compatibility of public API"""
        manager = MemoryManager()
        await manager.initialize(use_database=False)

        # All original methods should exist and work
        thought = {'content': 'Test', 'timestamp': datetime.now().isoformat()}

        # Original API methods
        thought_id = await manager.store_thought(thought)
        await manager.recall_recent(n=5)
        await manager.recall_by_id(thought_id)
        await manager.consolidate_memories()
        await manager.update_context('key', 'value')
        await manager.get_context('key')
        await manager.get_statistics()

        # Should all work without errors

    @pytest.mark.asyncio
    async def test_memory_manager_component_access(self):
        """Test accessing individual components"""
        manager = MemoryManager()
        await manager.initialize(use_database=False)

        # Should be able to access components directly
        working = manager.get_working_memory()
        episodic = manager.get_episodic_memory()
        semantic = manager.get_semantic_index()
        coordinator = manager.get_coordinator()

        assert isinstance(working, WorkingMemoryStore)
        assert isinstance(episodic, EpisodicMemoryStore)
        assert isinstance(semantic, SemanticIndex)
        assert isinstance(coordinator, MemoryCoordinator)

    @pytest.mark.asyncio
    async def test_memory_manager_cleanup(self):
        """Test memory manager cleanup"""
        manager = MemoryManager()
        await manager.initialize(use_database=False)

        # Store some data
        await manager.store_thought({'content': 'Test', 'timestamp': datetime.now().isoformat()})

        # Close
        await manager.close()

        # Should complete without errors


class TestEndToEndMemoryFlow:
    """Test end-to-end memory flow through all components"""

    @pytest.mark.asyncio
    async def test_complete_memory_lifecycle(self):
        """Test complete memory lifecycle from storage to retrieval"""
        manager = MemoryManager()
        await manager.initialize(use_database=False)

        # 1. Store initial thought
        thought_id = await manager.store_thought({
            'content': 'Initial thought',
            'stream': 'primary',
            'timestamp': datetime.now().isoformat(),
            'importance': 7
        })

        # 2. Recall by ID
        recalled = await manager.recall_by_id(thought_id)
        assert recalled['content'] == 'Initial thought'

        # 3. Store more thoughts
        for i in range(10):
            await manager.store_thought({
                'content': f'Thought {i}',
                'timestamp': datetime.now().isoformat(),
                'importance': 5 + i % 3  # Varying importance
            })

        # 4. Recall recent
        recent = await manager.recall_recent(n=5)
        assert len(recent) == 5

        # 5. Consolidate
        await manager.consolidate_memories()

        # 6. Get statistics
        stats = await manager.get_statistics()
        assert stats['total_thoughts'] >= 11  # At least our 11 thoughts

        # 7. Update context
        await manager.update_context('session', 'test_session')
        session = await manager.get_context('session')
        assert session == 'test_session'

        # 8. Clear working memory
        await manager.clear_working_memory()
        recent_after_clear = await manager.recall_recent(n=10)
        assert len(recent_after_clear) == 0

        # 9. Cleanup
        await manager.close()

    @pytest.mark.asyncio
    async def test_concurrent_memory_operations(self):
        """Test concurrent memory operations"""
        manager = MemoryManager()
        await manager.initialize(use_database=False)

        # Concurrent stores
        tasks = []
        for i in range(10):
            task = manager.store_thought({
                'content': f'Concurrent thought {i}',
                'timestamp': datetime.now().isoformat()
            })
            tasks.append(task)

        thought_ids = await asyncio.gather(*tasks)
        assert len(thought_ids) == 10

        # All should be recallable
        recent = await manager.recall_recent(n=10)
        assert len(recent) == 10

        await manager.close()
