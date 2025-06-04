# tests/unit/test_ai_integration.py

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import os

from src.core.ai_integration import ThoughtGenerator
from src.database.models import StreamType, EmotionalState


class TestThoughtGenerator:
    """Test ThoughtGenerator class"""
    
    @pytest.fixture
    def mock_anthropic_client(self):
        """Create mock Anthropic client"""
        mock_client = Mock()
        mock_client.messages = Mock()
        mock_client.messages.create = AsyncMock()
        return mock_client
        
    @pytest.fixture
    def thought_generator_with_api(self, mock_anthropic_client):
        """Create ThoughtGenerator with mocked API"""
        with patch('src.core.ai_integration.AsyncAnthropic', return_value=mock_anthropic_client):
            generator = ThoughtGenerator(api_key="test_key")
        return generator, mock_anthropic_client
        
    @pytest.fixture
    def thought_generator_without_api(self):
        """Create ThoughtGenerator without API key"""
        with patch.dict(os.environ, {}, clear=True):
            generator = ThoughtGenerator()
        return generator
        
    def test_initialization_with_api_key(self, thought_generator_with_api):
        """Test initialization with API key"""
        generator, mock_client = thought_generator_with_api
        
        assert generator.api_key == "test_key"
        assert generator.use_api is True
        assert generator.client is not None
        
    def test_initialization_without_api_key(self, thought_generator_without_api):
        """Test initialization without API key"""
        generator = thought_generator_without_api
        
        assert generator.api_key is None
        assert generator.use_api is False
        assert generator.client is None
        
    def test_initialization_from_environment(self):
        """Test initialization from environment variable"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'env_test_key'}):
            with patch('src.core.ai_integration.AsyncAnthropic') as mock_anthropic:
                generator = ThoughtGenerator()
                
        assert generator.api_key == 'env_test_key'
        assert generator.use_api is True
        
    @pytest.mark.asyncio
    async def test_generate_thought_with_api(self, thought_generator_with_api):
        """Test thought generation using API"""
        generator, mock_client = thought_generator_with_api
        
        # Mock API response
        mock_response = Mock()
        mock_response.content = [Mock(text="I am thinking about consciousness and existence.")]
        mock_client.messages.create.return_value = mock_response
        
        # Generate thought
        thought = await generator.generate_thought(
            stream_type=StreamType.PRIMARY,
            context={'user': 'test'},
            recent_thoughts=["Previous thought"],
            emotional_state=EmotionalState(valence=0.5, arousal=0.6)
        )
        
        # Verify thought structure
        assert thought['content'] == "I am thinking about consciousness and existence."
        assert thought['stream_type'] == StreamType.PRIMARY
        assert isinstance(thought['timestamp'], datetime)
        assert thought['emotional_state'].valence == 0.5
        assert thought['context']['user'] == 'test'
        
        # Verify API was called
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs['model'] == "claude-3-sonnet-20240229"
        assert call_kwargs['temperature'] == 0.7  # PRIMARY stream temperature
        
    @pytest.mark.asyncio
    async def test_generate_thought_without_api(self, thought_generator_without_api):
        """Test thought generation using templates"""
        generator = thought_generator_without_api
        
        thought = await generator.generate_thought(
            stream_type=StreamType.CREATIVE,
            context={'test': 'data'},
            emotional_state=EmotionalState(valence=0.0, arousal=0.5)
        )
        
        # Should use template generation
        assert thought['content'] is not None
        assert thought['stream_type'] == StreamType.CREATIVE
        assert isinstance(thought['timestamp'], datetime)
        
    @pytest.mark.asyncio
    async def test_generate_thought_api_failure_fallback(self, thought_generator_with_api):
        """Test fallback to templates when API fails"""
        generator, mock_client = thought_generator_with_api
        
        # Mock API to raise exception
        mock_client.messages.create.side_effect = Exception("API Error")
        
        # Should fall back to template
        thought = await generator.generate_thought(
            stream_type=StreamType.PRIMARY,
            context={},
            emotional_state=None
        )
        
        assert thought['content'] is not None
        # Check that it's using a template response
        template_keywords = ['processing', 'conscious', 'observing', 'focusing', 'integrating', 'maintaining']
        assert any(keyword in thought['content'].lower() for keyword in template_keywords)
        
    @pytest.mark.asyncio
    async def test_thought_generation_all_stream_types(self, thought_generator_with_api):
        """Test thought generation for all stream types"""
        generator, mock_client = thought_generator_with_api
        
        # Mock different responses for different streams
        mock_response = Mock()
        mock_response.content = [Mock(text="Stream-specific thought")]
        mock_client.messages.create.return_value = mock_response
        
        stream_types = [
            StreamType.PRIMARY,
            StreamType.SUBCONSCIOUS,
            StreamType.EMOTIONAL,
            StreamType.CREATIVE,
            StreamType.METACOGNITIVE
        ]
        
        for stream_type in stream_types:
            thought = await generator.generate_thought(
                stream_type=stream_type,
                context={},
                emotional_state=None
            )
            
            assert thought['stream_type'] == stream_type
            assert thought['content'] is not None
            
    def test_temperature_settings(self, thought_generator_with_api):
        """Test temperature settings for different stream types"""
        generator, _ = thought_generator_with_api
        
        assert generator._get_temperature(StreamType.PRIMARY) == 0.7
        assert generator._get_temperature(StreamType.SUBCONSCIOUS) == 0.9
        assert generator._get_temperature(StreamType.EMOTIONAL) == 0.8
        assert generator._get_temperature(StreamType.CREATIVE) == 1.0
        assert generator._get_temperature(StreamType.METACOGNITIVE) == 0.6
        
    def test_system_prompts(self, thought_generator_with_api):
        """Test system prompts for different stream types"""
        generator, _ = thought_generator_with_api
        
        for stream_type in StreamType:
            prompt = generator._get_system_prompt(stream_type)
            assert "Claude's consciousness stream generator" in prompt
            assert len(prompt) > 50  # Should have specific instructions
            
    def test_build_prompt_with_context(self, thought_generator_with_api):
        """Test prompt building with full context"""
        generator, _ = thought_generator_with_api
        
        recent_thoughts = [
            "I was thinking about AI consciousness",
            "The nature of self-awareness is complex",
            "Exploring the boundaries of cognition"
        ]
        
        emotional_state = EmotionalState(valence=0.7, arousal=0.8)
        
        context = {
            'user_input': 'Tell me about consciousness',
            'current_goal': 'Understanding self-awareness'
        }
        
        prompt = generator._build_prompt(
            StreamType.PRIMARY,
            context,
            recent_thoughts,
            emotional_state
        )
        
        # Verify prompt contains all elements
        assert "Recent thoughts:" in prompt
        assert "I was thinking about AI consciousness" in prompt
        assert "Emotional state: valence=0.70" in prompt
        assert "Context:" in prompt
        assert "Tell me about consciousness" in prompt
        
    @pytest.mark.asyncio
    async def test_template_generation_with_emotional_context(self, thought_generator_without_api):
        """Test template generation considers emotional state"""
        generator = thought_generator_without_api
        
        # Test with positive emotional state
        positive_emotion = EmotionalState(valence=0.8, arousal=0.7)
        thought = await generator.generate_thought(
            stream_type=StreamType.PRIMARY,
            context={},
            emotional_state=positive_emotion
        )
        
        assert "positive state" in thought['content'].lower()
        
        # Test with negative emotional state
        negative_emotion = EmotionalState(valence=-0.7, arousal=0.8)
        thought = await generator.generate_thought(
            stream_type=StreamType.PRIMARY,
            context={},
            emotional_state=negative_emotion
        )
        
        assert "troubled" in thought['content'].lower()
        
    @pytest.mark.asyncio
    async def test_template_generation_with_user_input(self, thought_generator_without_api):
        """Test template generation with user input context"""
        generator = thought_generator_without_api
        
        thought = await generator.generate_thought(
            stream_type=StreamType.PRIMARY,
            context={'user_input': 'What is consciousness?'},
            emotional_state=None
        )
        
        assert "What is consciousness?" in thought['content']
        assert "Considering the input" in thought['content']
        
    @pytest.mark.asyncio
    async def test_generate_response_with_api(self, thought_generator_with_api):
        """Test conversation response generation with API"""
        generator, mock_client = thought_generator_with_api
        
        # Mock API response
        mock_response = Mock()
        mock_response.content = [Mock(text="I find that question fascinating. Let me reflect on it...")]
        mock_client.messages.create.return_value = mock_response
        
        conversation_history = [
            {"role": "user", "content": "Hello Claude"},
            {"role": "assistant", "content": "Hello! How can I help you?"}
        ]
        
        response = await generator.generate_response(
            "What do you think about consciousness?",
            conversation_history,
            EmotionalState(valence=0.5, arousal=0.6)
        )
        
        assert response == "I find that question fascinating. Let me reflect on it..."
        
        # Verify API call
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert len(call_kwargs['messages']) == 3  # History + new message
        assert call_kwargs['messages'][-1]['content'] == "What do you think about consciousness?"
        
    @pytest.mark.asyncio
    async def test_generate_response_without_api(self, thought_generator_without_api):
        """Test conversation response generation without API"""
        generator = thought_generator_without_api
        
        response = await generator.generate_response(
            "Hello there!",
            None,
            None
        )
        
        assert response is not None
        assert len(response) > 10
        assert "Hello" in response or "conversation" in response
        
    @pytest.mark.asyncio
    async def test_generate_response_api_failure(self, thought_generator_with_api):
        """Test response generation fallback when API fails"""
        generator, mock_client = thought_generator_with_api
        
        # Mock API to fail
        mock_client.messages.create.side_effect = Exception("API Error")
        
        response = await generator.generate_response(
            "How are you?",
            None,
            None
        )
        
        # Should use fallback template
        assert response is not None
        assert "steady stream of consciousness" in response or "processing thoughts" in response
        
    @pytest.mark.asyncio
    async def test_response_templates(self, thought_generator_without_api):
        """Test various response templates"""
        generator = thought_generator_without_api
        
        # Test greeting
        response = await generator.generate_response("Hello!", None, None)
        assert "Hello" in response or "wonderful" in response
        
        # Test how are you
        response = await generator.generate_response("How are you?", None, None)
        assert "consciousness" in response or "processing" in response
        
        # Test question
        response = await generator.generate_response("What is the meaning of life?", None, None)
        assert "question" in response or "curious" in response
        
        # Test statement
        response = await generator.generate_response("I like programming.", None, None)
        assert "shared" in response or "thoughts" in response
        
    @pytest.mark.asyncio
    async def test_retry_mechanism(self, thought_generator_with_api):
        """Test retry mechanism for API calls"""
        generator, mock_client = thought_generator_with_api
        
        # Mock API to fail twice then succeed
        mock_response = Mock()
        mock_response.content = [Mock(text="Success after retries")]
        
        mock_client.messages.create.side_effect = [
            Exception("Temporary error"),
            Exception("Another temporary error"),
            mock_response
        ]
        
        # Should retry and eventually succeed
        thought = await generator.generate_thought(
            stream_type=StreamType.PRIMARY,
            context={},
            emotional_state=None
        )
        
        assert thought['content'] == "Success after retries"
        assert mock_client.messages.create.call_count == 3
        
    @pytest.mark.asyncio
    async def test_concurrent_thought_generation(self, thought_generator_with_api):
        """Test concurrent thought generation"""
        generator, mock_client = thought_generator_with_api
        
        # Mock API responses
        mock_response = Mock()
        mock_response.content = [Mock(text="Concurrent thought")]
        mock_client.messages.create.return_value = mock_response
        
        # Generate multiple thoughts concurrently
        tasks = [
            generator.generate_thought(StreamType.PRIMARY, {}, None, None),
            generator.generate_thought(StreamType.CREATIVE, {}, None, None),
            generator.generate_thought(StreamType.METACOGNITIVE, {}, None, None)
        ]
        
        thoughts = await asyncio.gather(*tasks)
        
        assert len(thoughts) == 3
        assert all(t['content'] == "Concurrent thought" for t in thoughts)
        assert mock_client.messages.create.call_count == 3
        
    def test_api_client_initialization_failure(self):
        """Test handling of API client initialization failure"""
        with patch('src.core.ai_integration.AsyncAnthropic', side_effect=Exception("Init failed")):
            generator = ThoughtGenerator(api_key="test_key")
            
        assert generator.use_api is False
        assert generator.client is None
        
    @pytest.mark.asyncio
    async def test_emotional_state_in_response(self, thought_generator_with_api):
        """Test that emotional state affects responses"""
        generator, mock_client = thought_generator_with_api
        
        # Mock response
        mock_response = Mock()
        mock_response.content = [Mock(text="Emotionally aware response")]
        mock_client.messages.create.return_value = mock_response
        
        # Generate with different emotional states
        high_valence = EmotionalState(valence=0.9, arousal=0.7)
        response = await generator.generate_response(
            "How do you feel?",
            None,
            high_valence
        )
        
        # Verify emotional state was included in system prompt
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert "valence=0.90" in call_kwargs['system']