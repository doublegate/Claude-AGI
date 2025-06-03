# tests/unit/test_memory_manager.py

import pytest
import asyncio
from datetime import datetime
import random
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.memory.manager import MemoryManager

class TestMemoryManager:
    @pytest.mark.asyncio
    async def test_memory_creation(self):
        """Test memory manager initialization"""
        memory = await MemoryManager.create()
        assert memory is not None
        assert memory.working_memory is not None
        assert memory.vector_store is not None
        
    @pytest.mark.asyncio
    async def test_thought_storage(self):
        """Test basic thought storage and retrieval"""
        memory = await MemoryManager.create()
        
        thought = {
            'content': 'I wonder about the nature of testing',
            'emotional_tone': 'curious',
            'importance': 7
        }
        
        thought_id = await memory.store_thought(thought)
        assert thought_id is not None
        
        # Retrieve by ID
        retrieved = await memory.recall_by_id(thought_id)
        assert retrieved is not None
        assert retrieved['content'] == thought['content']
        assert retrieved['emotional_tone'] == thought['emotional_tone']
        
    @pytest.mark.asyncio
    async def test_recent_thoughts_retrieval(self):
        """Test retrieving recent thoughts"""
        memory = await MemoryManager.create()
        
        # Store multiple thoughts
        thoughts = []
        for i in range(5):
            thought = {
                'content': f'Test thought number {i}',
                'emotional_tone': 'neutral',
                'importance': 5
            }
            thought_id = await memory.store_thought(thought)
            thoughts.append(thought)
            
        # Retrieve recent thoughts
        recent = await memory.recall_recent(n=3)
        assert len(recent) == 3
        
        # Should be in reverse chronological order
        assert recent[0]['content'] == 'Test thought number 4'
        assert recent[2]['content'] == 'Test thought number 2'
        
    @pytest.mark.asyncio
    async def test_semantic_search(self):
        """Test semantic memory search"""
        memory = await MemoryManager.create()
        
        # Store related thoughts
        thoughts = [
            {'content': 'The sky is blue today', 'importance': 5},
            {'content': 'Ocean waves are blue', 'importance': 6},
            {'content': 'I enjoy the color blue', 'importance': 7},
            {'content': 'Red roses in the garden', 'importance': 5}
        ]
        
        for thought in thoughts:
            await memory.store_thought(thought)
            
        # Search for blue-related memories
        results = await memory.recall_similar('blue color', k=3)
        
        # Should find memories containing 'blue'
        assert len(results) <= 3
        blue_count = sum(1 for r in results if 'blue' in r['content'].lower())
        assert blue_count >= 2  # At least 2 of the 3 should contain 'blue'
        
    @pytest.mark.asyncio
    async def test_memory_consolidation(self):
        """Test memory consolidation process"""
        memory = await MemoryManager.create()
        
        # Simulate many thoughts with varying importance
        high_importance_count = 0
        for i in range(20):
            importance = random.randint(3, 9)
            if importance >= 7:
                high_importance_count += 1
                
            await memory.store_thought({
                'content': f'Thought number {i}',
                'importance': importance,
                'emotional_tone': random.choice(['neutral', 'curious', 'happy'])
            })
            
        # Run consolidation
        await memory.consolidate_memories()
        
        # Verify long-term memory contains high-importance thoughts
        long_term_count = len(memory.long_term_memory)
        assert long_term_count > 0
        
        # All long-term memories should have high importance
        for memory_item in memory.long_term_memory:
            assert memory_item.get('importance', 0) >= 7
            
    @pytest.mark.asyncio
    async def test_context_management(self):
        """Test active context storage and retrieval"""
        memory = await MemoryManager.create()
        
        # Set context values
        await memory.update_context('current_topic', 'consciousness')
        await memory.update_context('emotional_state', 'curious')
        await memory.update_context('user_name', 'TestUser')
        
        # Retrieve context values
        topic = await memory.get_context('current_topic')
        emotion = await memory.get_context('emotional_state')
        name = await memory.get_context('user_name')
        
        assert topic == 'consciousness'
        assert emotion == 'curious'
        assert name == 'TestUser'
        
        # Test non-existent key
        missing = await memory.get_context('non_existent')
        assert missing is None
        
    @pytest.mark.asyncio
    async def test_emotional_intensity_calculation(self):
        """Test emotional intensity calculation"""
        memory = await MemoryManager.create()
        
        test_cases = [
            ({'emotional_tone': 'joy'}, 0.8),
            ({'emotional_tone': 'excitement'}, 0.9),
            ({'emotional_tone': 'neutral'}, 0.3),
            ({'emotional_tone': 'calm'}, 0.2),
            ({'emotional_tone': 'unknown'}, 0.5),  # Default
        ]
        
        for thought, expected in test_cases:
            intensity = memory._get_emotional_intensity(thought)
            assert intensity == expected
            
    @pytest.mark.asyncio
    async def test_working_memory_limits(self):
        """Test working memory size limits"""
        memory = await MemoryManager.create()
        
        # Store many thoughts to exceed limit
        for i in range(1100):
            await memory.store_thought({
                'content': f'Thought {i}',
                'importance': 5
            })
            
        # Working memory should be limited
        assert len(memory.working_memory['recent_thoughts']) <= 1000
        
        # Most recent thoughts should be preserved
        last_thought = memory.working_memory['recent_thoughts'][-1]
        assert 'Thought 1099' in last_thought['content']
        
    @pytest.mark.asyncio
    async def test_clear_working_memory(self):
        """Test clearing working memory"""
        memory = await MemoryManager.create()
        
        # Store some thoughts
        for i in range(5):
            await memory.store_thought({
                'content': f'Thought {i}',
                'importance': 5
            })
            
        # Verify thoughts exist
        assert len(memory.working_memory['recent_thoughts']) == 5
        assert len(memory.working_memory['short_term']) == 5
        
        # Clear working memory
        await memory.clear_working_memory()
        
        # Verify cleared
        assert len(memory.working_memory['recent_thoughts']) == 0
        assert len(memory.working_memory['short_term']) == 0