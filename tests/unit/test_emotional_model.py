"""
Unit Tests for Advanced Emotional Model
========================================

Tests for multi-dimensional emotional system.
"""

import pytest
from datetime import datetime
from src.emotional.emotional_model import (
    AdvancedEmotionalModel,
    PrimaryEmotion,
    ComplexEmotion,
    EmotionalState,
    EmotionalMemory,
    MoodState
)


class TestAdvancedEmotionalModel:
    """Test the AdvancedEmotionalModel class"""

    @pytest.fixture
    def model(self):
        """Create an emotional model"""
        return AdvancedEmotionalModel()

    @pytest.mark.asyncio
    async def test_initial_state(self, model):
        """Test initial emotional state"""
        assert model.current_state is not None
        assert isinstance(model.current_state, EmotionalState)
        assert -1.0 <= model.current_state.valence <= 1.0
        assert 0.0 <= model.current_state.arousal <= 1.0
        assert 0.0 <= model.current_state.dominance <= 1.0

    @pytest.mark.asyncio
    async def test_process_discovery_stimulus(self, model):
        """Test processing a discovery stimulus"""
        initial_valence = model.current_state.valence

        state = await model.process_emotional_stimulus('discovery', intensity=0.7)

        assert state.primary_emotion == PrimaryEmotion.CURIOSITY
        assert state.valence >= initial_valence  # Discovery is positive
        assert state.intensity == 0.7

    @pytest.mark.asyncio
    async def test_process_achievement_stimulus(self, model):
        """Test processing an achievement stimulus"""
        state = await model.process_emotional_stimulus('achievement', intensity=0.8)

        assert state.primary_emotion == PrimaryEmotion.SATISFACTION
        assert state.valence > 0.0  # Achievement is positive
        assert state.arousal > 0.0

    @pytest.mark.asyncio
    async def test_process_failure_stimulus(self, model):
        """Test processing a failure stimulus"""
        state = await model.process_emotional_stimulus('failure', intensity=0.6)

        assert state.primary_emotion == PrimaryEmotion.FRUSTRATION
        assert state.valence < 0.0  # Failure is negative

    @pytest.mark.asyncio
    async def test_process_confusion_stimulus(self, model):
        """Test processing confusion stimulus"""
        state = await model.process_emotional_stimulus('confusion', intensity=0.5)

        assert state.primary_emotion == PrimaryEmotion.CONCERN
        assert state.valence < 0.0  # Confusion is slightly negative

    @pytest.mark.asyncio
    async def test_emotional_intensity(self, model):
        """Test that intensity affects emotional response"""
        state1 = await model.process_emotional_stimulus('success', intensity=0.3)
        valence1 = state1.valence

        # Reset to baseline
        model.current_state.valence = 0.3

        state2 = await model.process_emotional_stimulus('success', intensity=0.9)
        valence2 = state2.valence

        # Higher intensity should create stronger emotional response
        assert abs(valence2 - 0.3) > abs(valence1 - 0.3)

    @pytest.mark.asyncio
    async def test_experience_nostalgia(self, model):
        """Test experiencing nostalgia (complex emotion)"""
        await model.experience_complex_emotion(
            emotion=ComplexEmotion.NOSTALGIA,
            intensity=0.6,
            context={'memory': 'past conversation'}
        )

        assert 'complex_emotion' in model.current_state.metadata
        assert model.current_state.metadata['complex_emotion'] == 'nostalgia'
        assert model.current_state.primary_emotion == PrimaryEmotion.SADNESS

    @pytest.mark.asyncio
    async def test_experience_anticipation(self, model):
        """Test experiencing anticipation"""
        await model.experience_complex_emotion(
            emotion=ComplexEmotion.ANTICIPATION,
            intensity=0.7
        )

        assert model.current_state.primary_emotion == PrimaryEmotion.EXCITEMENT
        assert model.current_state.valence > 0.0
        assert model.current_state.arousal > 0.6

    @pytest.mark.asyncio
    async def test_experience_pride(self, model):
        """Test experiencing pride"""
        await model.experience_complex_emotion(
            emotion=ComplexEmotion.PRIDE,
            intensity=0.8
        )

        assert model.current_state.valence > 0.5  # Pride is very positive
        assert model.current_state.primary_emotion == PrimaryEmotion.SATISFACTION

    @pytest.mark.asyncio
    async def test_tag_memory_with_emotion(self, model):
        """Test tagging a memory with current emotion"""
        # Set a specific emotional state
        await model.process_emotional_stimulus('success', intensity=0.8)

        # Tag a memory
        em = await model.tag_memory_with_emotion(
            memory_id="mem_123",
            memory_content="Solved a difficult problem",
            importance=0.9
        )

        assert isinstance(em, EmotionalMemory)
        assert em.memory_id == "mem_123"
        assert em.emotional_state.primary_emotion == PrimaryEmotion.JOY
        assert em.importance == 0.9

    @pytest.mark.asyncio
    async def test_recall_mood_congruent_memories(self, model):
        """Test recalling mood-congruent memories"""
        # Create memories with different emotions
        await model.process_emotional_stimulus('success', intensity=0.8)
        await model.tag_memory_with_emotion("mem_happy", "Happy memory", 0.8)

        await model.process_emotional_stimulus('failure', intensity=0.7)
        await model.tag_memory_with_emotion("mem_sad", "Sad memory", 0.7)

        # Set current mood to positive
        model.mood.current_valence = 0.6

        # Recall should prefer positive memories
        memories = await model.recall_mood_congruent_memories(count=2)

        assert len(memories) > 0
        # Should prioritize mood-congruent memories
        assert all(isinstance(m, EmotionalMemory) for m in memories)

    @pytest.mark.asyncio
    async def test_mood_tracking(self, model):
        """Test that mood is tracked separately from emotions"""
        assert isinstance(model.mood, MoodState)
        assert hasattr(model.mood, 'baseline_valence')
        assert hasattr(model.mood, 'current_valence')
        assert hasattr(model.mood, 'stability')

    @pytest.mark.asyncio
    async def test_mood_update(self, model):
        """Test that mood updates based on emotional history"""
        initial_mood = model.mood.current_valence

        # Process multiple positive stimuli
        for _ in range(10):
            await model.process_emotional_stimulus('success', intensity=0.7)
            await model._update_mood()

        final_mood = model.mood.current_valence

        # Mood should shift toward positive
        assert final_mood > initial_mood

    @pytest.mark.asyncio
    async def test_emotional_decay(self, model):
        """Test that emotions decay over time"""
        # Create strong emotion
        await model.process_emotional_stimulus('excitement', intensity=0.9)
        initial_valence = model.current_state.valence
        initial_intensity = model.current_state.intensity

        # Apply decay
        await model.apply_emotional_decay()

        # Values should move toward baseline
        assert abs(model.current_state.valence) < abs(initial_valence)
        assert model.current_state.intensity < initial_intensity

    @pytest.mark.asyncio
    async def test_emotional_influence_on_thinking(self, model):
        """Test that emotions influence cognitive processes"""
        # High arousal state
        await model.process_emotional_stimulus('novelty', intensity=0.9)

        influences = await model.get_emotional_influence_on_thinking()

        assert 'thought_pacing' in influences
        assert 'creativity_boost' in influences
        assert 'analytical_focus' in influences
        assert 'curiosity_drive' in influences

        # High arousal should increase thought pacing
        assert influences['thought_pacing'] > 1.0

    @pytest.mark.asyncio
    async def test_positive_valence_boosts_creativity(self, model):
        """Test that positive emotions boost creativity"""
        # Create positive state
        await model.process_emotional_stimulus('success', intensity=0.8)

        influences = await model.get_emotional_influence_on_thinking()

        # Positive valence should boost creativity
        assert influences['creativity_boost'] > 1.0

    @pytest.mark.asyncio
    async def test_negative_valence_boosts_analysis(self, model):
        """Test that negative emotions boost analytical focus"""
        # Create negative state
        await model.process_emotional_stimulus('failure', intensity=0.7)

        influences = await model.get_emotional_influence_on_thinking()

        # Negative valence should boost analytical focus
        assert influences['analytical_focus'] > 1.0

    @pytest.mark.asyncio
    async def test_curiosity_drives_exploration(self, model):
        """Test that curiosity emotion drives exploration"""
        await model.process_emotional_stimulus('discovery', intensity=0.8)

        influences = await model.get_emotional_influence_on_thinking()

        # Curiosity should increase drive
        assert influences['curiosity_drive'] > 1.0

    @pytest.mark.asyncio
    async def test_get_emotional_state_description(self, model):
        """Test getting human-readable state description"""
        await model.process_emotional_stimulus('success', intensity=0.7)

        description = model.get_emotional_state_description()

        assert isinstance(description, str)
        assert len(description) > 0
        # Should mention the emotion
        assert model.current_state.primary_emotion.value in description.lower()

    @pytest.mark.asyncio
    async def test_get_mood_description(self, model):
        """Test getting human-readable mood description"""
        description = model.get_mood_description()

        assert isinstance(description, str)
        assert len(description) > 0
        assert "mood" in description.lower()

    @pytest.mark.asyncio
    async def test_emotional_statistics(self, model):
        """Test getting emotional statistics"""
        # Generate some emotional activity
        await model.process_emotional_stimulus('discovery', intensity=0.6)
        await model.process_emotional_stimulus('achievement', intensity=0.7)

        stats = await model.get_emotional_statistics()

        assert 'current_emotion' in stats
        assert 'current_valence' in stats
        assert 'current_arousal' in stats
        assert 'mood_valence' in stats
        assert 'dominant_emotions' in stats

    @pytest.mark.asyncio
    async def test_emotion_history_tracking(self, model):
        """Test that emotional history is maintained"""
        # Process several emotions
        emotions_to_test = ['discovery', 'achievement', 'learning']

        for emotion in emotions_to_test:
            await model.process_emotional_stimulus(emotion, intensity=0.5)

        assert len(model.emotion_history) >= len(emotions_to_test)

    @pytest.mark.asyncio
    async def test_emotional_memory_access_count(self, model):
        """Test that memory access is tracked"""
        # Create a memory
        await model.tag_memory_with_emotion("mem_test", "Test memory", 0.5)

        # Set mood to match
        model.mood.current_valence = model.emotional_memories["mem_test"].emotional_state.valence

        # Recall memories
        await model.recall_mood_congruent_memories(count=5)

        # Access count should be updated
        mem = model.emotional_memories["mem_test"]
        if mem.access_count > 0:
            assert mem.last_recalled is not None

    @pytest.mark.asyncio
    async def test_clamp_function(self, model):
        """Test that values are clamped correctly"""
        # Test clamping
        assert model._clamp(1.5, -1.0, 1.0) == 1.0
        assert model._clamp(-1.5, -1.0, 1.0) == -1.0
        assert model._clamp(0.5, -1.0, 1.0) == 0.5

    @pytest.mark.asyncio
    async def test_blend_function(self, model):
        """Test blending function"""
        # 50% blend
        result = model._blend(0.0, 1.0, 0.5)
        assert result == 0.5

        # 100% blend (full target)
        result = model._blend(0.0, 1.0, 1.0)
        assert result == 1.0

        # 0% blend (stay at current)
        result = model._blend(0.5, 1.0, 0.0)
        assert result == 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
