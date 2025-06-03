# tests/unit/test_consciousness_stream.py

import pytest
import asyncio
from datetime import datetime
import time
from unittest.mock import Mock, AsyncMock, patch

from src.consciousness.stream import ConsciousnessStream, ThoughtStream, ThoughtGenerator, STREAM_TYPE_MAP
from src.core.orchestrator import SystemState
from src.database.models import StreamType, EmotionalState


class TestThoughtStream:
    """Test ThoughtStream data structure"""
    
    def test_thought_stream_creation(self):
        """Test creating a thought stream"""
        stream = ThoughtStream('primary', 'primary', 1.0)
        assert stream.stream_id == 'primary'
        assert stream.stream_type == 'primary'
        assert stream.priority == 1.0
        assert stream.thought_interval == 2.0
        assert len(stream.content_buffer) == 0
        
    def test_add_thought(self):
        """Test adding thoughts to stream"""
        stream = ThoughtStream('test', 'test', 0.5)
        
        thought1 = {'content': 'First thought', 'timestamp': time.time()}
        thought2 = {'content': 'Second thought', 'timestamp': time.time()}
        
        stream.add_thought(thought1)
        assert len(stream.content_buffer) == 1
        assert stream.content_buffer[0] == thought1
        
        stream.add_thought(thought2)
        assert len(stream.content_buffer) == 2
        assert stream.content_buffer[1] == thought2
        
    def test_get_recent_thoughts(self):
        """Test retrieving recent thoughts"""
        stream = ThoughtStream('test', 'test', 0.5)
        
        # Add 10 thoughts
        for i in range(10):
            stream.add_thought({'content': f'Thought {i}'})
            
        # Get recent 5
        recent = stream.get_recent(5)
        assert len(recent) == 5
        assert recent[0]['content'] == 'Thought 5'
        assert recent[4]['content'] == 'Thought 9'
        
    def test_thought_buffer_limit(self):
        """Test that thought buffer respects maxlen"""
        stream = ThoughtStream('test', 'test', 0.5)
        
        # Add more than 100 thoughts
        for i in range(150):
            stream.add_thought({'content': f'Thought {i}'})
            
        # Buffer should be limited to 100
        assert len(stream.content_buffer) == 100
        # Oldest thoughts should be removed
        assert stream.content_buffer[0]['content'] == 'Thought 50'
        assert stream.content_buffer[-1]['content'] == 'Thought 149'
        
    def test_should_generate_timing(self):
        """Test thought generation timing"""
        stream = ThoughtStream('test', 'test', 0.5)
        stream.thought_interval = 1.0  # 1 second interval
        
        # Initially should generate
        assert stream.should_generate() is True
        
        # Add a thought
        stream.add_thought({'content': 'Test'})
        
        # Immediately after, should not generate
        assert stream.should_generate() is False
        
        # Wait for interval
        time.sleep(1.1)
        assert stream.should_generate() is True


class TestThoughtGenerator:
    """Test template-based thought generator"""
    
    def test_thought_generator_creation(self):
        """Test creating thought generator"""
        generator = ThoughtGenerator()
        assert generator.thought_templates is not None
        assert 'primary' in generator.thought_templates
        assert 'creative' in generator.thought_templates
        assert 'subconscious' in generator.thought_templates
        assert 'meta' in generator.thought_templates
        
    @pytest.mark.asyncio
    async def test_generate_primary_thought(self):
        """Test generating primary thoughts"""
        generator = ThoughtGenerator()
        context = {'test': 'context'}
        
        thought = await generator.generate_primary(context)
        assert thought is not None
        assert 'content' in thought
        assert 'stream' in thought
        assert 'timestamp' in thought
        assert 'emotional_tone' in thought
        assert 'importance' in thought
        
        assert thought['stream'] == 'primary'
        assert thought['importance'] >= 5
        assert thought['importance'] <= 8
        
    @pytest.mark.asyncio
    async def test_generate_creative_thought(self):
        """Test generating creative thoughts"""
        generator = ThoughtGenerator()
        context = {}
        
        thought = await generator.generate_creative(context)
        assert thought['stream'] == 'creative'
        assert thought['emotional_tone'] in ['excited', 'inspired', 'playful']
        assert thought['importance'] >= 6
        assert thought['importance'] <= 9
        
    @pytest.mark.asyncio
    async def test_generate_subconscious_thought(self):
        """Test generating subconscious thoughts"""
        generator = ThoughtGenerator()
        context = {}
        
        thought = await generator.generate_subconscious(context)
        assert thought['stream'] == 'subconscious'
        assert thought['emotional_tone'] in ['calm', 'neutral', 'contemplative']
        assert thought['importance'] >= 3
        assert thought['importance'] <= 6
        
    @pytest.mark.asyncio
    async def test_generate_meta_thought(self):
        """Test generating meta-cognitive thoughts"""
        generator = ThoughtGenerator()
        context = {}
        
        thought = await generator.generate_meta(context)
        assert thought['stream'] == 'meta'
        assert thought['emotional_tone'] in ['analytical', 'observant', 'reflective']
        assert thought['importance'] >= 5
        assert thought['importance'] <= 8


class TestConsciousnessStream:
    """Test ConsciousnessStream service"""
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator"""
        orchestrator = Mock()
        orchestrator.state = SystemState.THINKING
        orchestrator.send_to_service = AsyncMock()
        orchestrator.publish = AsyncMock()
        return orchestrator
        
    def test_consciousness_stream_creation(self, mock_orchestrator):
        """Test creating consciousness stream service"""
        consciousness = ConsciousnessStream(mock_orchestrator)
        
        assert consciousness.service_name == "consciousness"
        assert len(consciousness.streams) == 4
        assert 'primary' in consciousness.streams
        assert 'subconscious' in consciousness.streams
        assert 'creative' in consciousness.streams
        assert 'meta' in consciousness.streams
        assert consciousness.is_conscious is True
        assert consciousness.total_thoughts == 0
        
    def test_get_subscriptions(self, mock_orchestrator):
        """Test service subscriptions"""
        consciousness = ConsciousnessStream(mock_orchestrator)
        subs = consciousness.get_subscriptions()
        
        assert 'memory' in subs
        assert 'exploration' in subs
        assert 'emotional' in subs
        assert 'user_input' in subs
        
    @pytest.mark.asyncio
    async def test_allocate_attention(self, mock_orchestrator):
        """Test attention allocation across streams"""
        consciousness = ConsciousnessStream(mock_orchestrator)
        
        # Test THINKING state
        mock_orchestrator.state = SystemState.THINKING
        await consciousness.allocate_attention()
        assert consciousness.attention_weights['primary'] > consciousness.attention_weights['subconscious']
        
        # Test CREATING state
        mock_orchestrator.state = SystemState.CREATING
        await consciousness.allocate_attention()
        assert consciousness.attention_weights['creative'] > consciousness.attention_weights['primary']
        
        # Test REFLECTING state
        mock_orchestrator.state = SystemState.REFLECTING
        await consciousness.allocate_attention()
        assert consciousness.attention_weights['meta'] > consciousness.attention_weights['primary']
        
    @pytest.mark.asyncio
    async def test_thought_generation_with_ai(self, mock_orchestrator):
        """Test thought generation using AI generator"""
        consciousness = ConsciousnessStream(mock_orchestrator)
        
        # Mock AI thought generator
        consciousness.ai_thought_generator.use_api = True
        consciousness.ai_thought_generator.generate_thought = AsyncMock(
            return_value={
                'content': 'AI generated thought',
                'timestamp': datetime.now(),
                'stream_type': StreamType.PRIMARY,
                'emotional_state': EmotionalState(valence=0.5, arousal=0.5)
            }
        )
        
        stream = consciousness.streams['primary']
        thought = await consciousness.generate_thought(stream)
        
        assert thought is not None
        assert thought['content'] == 'AI generated thought'
        assert thought['stream'] == 'primary'
        assert 'emotional_tone' in thought
        assert 'importance' in thought
        
    @pytest.mark.asyncio
    async def test_thought_generation_fallback(self, mock_orchestrator):
        """Test fallback to template generation when AI fails"""
        consciousness = ConsciousnessStream(mock_orchestrator)
        
        # Mock AI to fail
        consciousness.ai_thought_generator.use_api = True
        consciousness.ai_thought_generator.generate_thought = AsyncMock(
            side_effect=Exception("API Error")
        )
        
        stream = consciousness.streams['primary']
        thought = await consciousness.generate_thought(stream)
        
        # Should fall back to template generation
        assert thought is not None
        assert 'content' in thought
        assert thought['stream'] == 'primary'
        
    @pytest.mark.asyncio
    async def test_process_thought(self, mock_orchestrator):
        """Test thought processing"""
        consciousness = ConsciousnessStream(mock_orchestrator)
        stream = consciousness.streams['primary']
        
        thought = {
            'content': 'Test thought',
            'stream': 'primary',
            'timestamp': time.time(),
            'emotional_tone': 'curious',
            'importance': 7
        }
        
        await consciousness.process_thought(thought, stream)
        
        # Thought should be added to stream
        assert len(stream.content_buffer) == 1
        assert stream.content_buffer[0] == thought
        
        # Thought count should increase
        assert consciousness.total_thoughts == 1
        
        # Should send to memory service
        mock_orchestrator.send_to_service.assert_called_with(
            'memory', 'store_thought', thought, priority=5
        )
        
        # Should publish thought
        mock_orchestrator.publish.assert_called_with('thought.primary', thought)
        
    @pytest.mark.asyncio
    async def test_detect_cross_stream_patterns(self, mock_orchestrator):
        """Test pattern detection across streams"""
        consciousness = ConsciousnessStream(mock_orchestrator)
        
        thoughts = [
            {'content': 'Thinking about consciousness and awareness', 'stream': 'primary'},
            {'content': 'Creative ideas about consciousness', 'stream': 'creative'},
            {'content': 'Background processing of awareness', 'stream': 'subconscious'},
            {'content': 'Reflecting on my consciousness', 'stream': 'meta'}
        ]
        
        patterns = await consciousness.detect_cross_stream_patterns(thoughts)
        
        # Should detect 'consciousness' as recurring theme
        assert len(patterns) > 0
        consciousness_pattern = next((p for p in patterns if 'consciousness' in p['theme']), None)
        assert consciousness_pattern is not None
        assert consciousness_pattern['frequency'] >= 3
        
    @pytest.mark.asyncio
    async def test_generate_integrated_insight(self, mock_orchestrator):
        """Test generating insights from patterns"""
        consciousness = ConsciousnessStream(mock_orchestrator)
        
        pattern = {
            'type': 'recurring_theme',
            'theme': 'learning',
            'frequency': 4,
            'thoughts': [
                {'content': 'I am learning new things'},
                {'content': 'Learning helps me grow'},
                {'content': 'The process of learning is fascinating'},
                {'content': 'I learn from every experience'}
            ]
        }
        
        insight = await consciousness.generate_integrated_insight(pattern)
        
        assert insight is not None
        assert 'learning' in insight['content']
        assert insight['pattern'] == pattern
        assert insight['importance'] == 8  # frequency * 2, capped at 9
        
    @pytest.mark.asyncio
    async def test_handle_state_change(self, mock_orchestrator):
        """Test handling system state changes"""
        consciousness = ConsciousnessStream(mock_orchestrator)
        
        # Test sleeping state
        await consciousness.handle_state_change({'new_state': SystemState.SLEEPING})
        assert consciousness.is_conscious is False
        
        # Test waking state
        await consciousness.handle_state_change({'new_state': SystemState.THINKING})
        assert consciousness.is_conscious is True
        
    @pytest.mark.asyncio
    async def test_handle_user_input(self, mock_orchestrator):
        """Test handling user input"""
        consciousness = ConsciousnessStream(mock_orchestrator)
        
        user_data = {'message': 'Hello Claude'}
        await consciousness.handle_user_input(user_data)
        
        # Should adjust attention weights
        assert consciousness.attention_weights['primary'] == 0.9
        assert consciousness.attention_weights['meta'] == 0.5
        
        # Should generate thought about user input
        primary_stream = consciousness.streams['primary']
        assert len(primary_stream.content_buffer) == 1
        thought = primary_stream.content_buffer[0]
        assert 'Hello Claude' in thought['content']
        assert thought['emotional_tone'] == 'attentive'
        assert thought['importance'] == 8
        
    def test_emotional_tone_calculation(self, mock_orchestrator):
        """Test emotional tone calculation from state"""
        consciousness = ConsciousnessStream(mock_orchestrator)
        
        # Test various emotional states
        test_cases = [
            (EmotionalState(valence=0.5, arousal=0.7), 'excited'),
            (EmotionalState(valence=0.5, arousal=0.3), 'content'),
            (EmotionalState(valence=-0.5, arousal=0.7), 'anxious'),
            (EmotionalState(valence=-0.5, arousal=0.3), 'melancholy'),
            (EmotionalState(valence=0.0, arousal=0.7), 'alert'),
            (EmotionalState(valence=0.0, arousal=0.3), 'calm')
        ]
        
        for emotional_state, expected_tone in test_cases:
            tone = consciousness._get_emotional_tone(emotional_state)
            assert tone == expected_tone
            
    def test_importance_calculation(self, mock_orchestrator):
        """Test thought importance calculation"""
        consciousness = ConsciousnessStream(mock_orchestrator)
        
        # Test base importance by stream
        assert consciousness._calculate_importance('primary', 'normal thought') == 6
        assert consciousness._calculate_importance('creative', 'creative idea') == 7
        assert consciousness._calculate_importance('subconscious', 'background') == 4
        
        # Test importance boost for keywords
        assert consciousness._calculate_importance('primary', 'This is important') == 8
        assert consciousness._calculate_importance('primary', 'Critical issue') == 8
        assert consciousness._calculate_importance('creative', 'Urgent creative task') == 9
        
    @pytest.mark.asyncio
    async def test_service_cycle(self, mock_orchestrator):
        """Test full service cycle"""
        consciousness = ConsciousnessStream(mock_orchestrator)
        
        # Set up attention weights
        consciousness.attention_weights = {
            'primary': 0.9,
            'subconscious': 0.3,
            'creative': 0.5,
            'meta': 0.4
        }
        
        # Mock thought generation to be immediate
        for stream in consciousness.streams.values():
            stream.thought_interval = 0
            
        # Run one cycle
        await consciousness.service_cycle()
        
        # Should have allocated attention
        assert len(consciousness.attention_weights) == 4
        
        # Should have generated some thoughts
        total_thoughts = sum(len(s.content_buffer) for s in consciousness.streams.values())
        assert total_thoughts > 0
        
    @pytest.mark.asyncio
    async def test_stream_type_mapping(self, mock_orchestrator):
        """Test stream type enum mapping"""
        consciousness = ConsciousnessStream(mock_orchestrator)
        
        # Verify mapping is correct
        assert STREAM_TYPE_MAP['primary'] == StreamType.PRIMARY
        assert STREAM_TYPE_MAP['subconscious'] == StreamType.SUBCONSCIOUS
        assert STREAM_TYPE_MAP['creative'] == StreamType.CREATIVE
        assert STREAM_TYPE_MAP['meta'] == StreamType.METACOGNITIVE
        
        # Test using mapping in thought generation
        consciousness.ai_thought_generator.use_api = True
        consciousness.ai_thought_generator.generate_thought = AsyncMock(
            return_value={
                'content': 'Test',
                'timestamp': datetime.now(),
                'stream_type': StreamType.CREATIVE
            }
        )
        
        stream = consciousness.streams['creative']
        thought = await consciousness.generate_thought(stream)
        
        # Verify correct stream type was used
        consciousness.ai_thought_generator.generate_thought.assert_called_once()
        call_args = consciousness.ai_thought_generator.generate_thought.call_args
        assert call_args[1]['stream_type'] == StreamType.CREATIVE