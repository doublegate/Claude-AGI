"""
Unit Tests for Theory of Mind
==============================

Tests for user mental state modeling and perspective-taking.
"""

import pytest
from src.social.theory_of_mind import (
    TheoryOfMind,
    UserBelief,
    UserIntention,
    EmotionalStateInference,
    PerspectiveModel,
    BeliefType
)


class TestTheoryOfMind:
    """Test the TheoryOfMind class"""

    @pytest.fixture
    def tom(self):
        """Create a Theory of Mind instance"""
        return TheoryOfMind()

    @pytest.mark.asyncio
    async def test_initialize_user_model(self, tom):
        """Test initializing a user model"""
        model = await tom.initialize_user_model("user_123")

        assert isinstance(model, PerspectiveModel)
        assert model.user_id == "user_123"
        assert len(model.beliefs) == 0
        assert len(model.intentions) == 0

    @pytest.mark.asyncio
    async def test_infer_belief_factual(self, tom):
        """Test inferring factual beliefs"""
        belief = await tom.infer_belief(
            user_id="user_1",
            statement="The Earth is round",
            context="Science discussion"
        )

        assert belief is not None
        assert belief.belief_type == BeliefType.FACTUAL
        assert belief.confidence > 0.0
        assert "Earth is round" in belief.content

    @pytest.mark.asyncio
    async def test_infer_belief_preferential(self, tom):
        """Test inferring preferential beliefs"""
        belief = await tom.infer_belief(
            user_id="user_1",
            statement="I love Python programming",
            context="Tech discussion"
        )

        assert belief.belief_type == BeliefType.PREFERENTIAL
        assert "love" in belief.content.lower()

    @pytest.mark.asyncio
    async def test_infer_belief_normative(self, tom):
        """Test inferring normative beliefs"""
        belief = await tom.infer_belief(
            user_id="user_1",
            statement="Code should be well-documented",
            context="Best practices"
        )

        assert belief.belief_type == BeliefType.NORMATIVE
        assert belief.confidence > 0.0

    @pytest.mark.asyncio
    async def test_infer_belief_self(self, tom):
        """Test inferring self-beliefs"""
        belief = await tom.infer_belief(
            user_id="user_1",
            statement="I am a software developer",
            context="Introduction"
        )

        assert belief.belief_type == BeliefType.SELF
        assert "I am" in belief.content

    @pytest.mark.asyncio
    async def test_calculate_belief_confidence_high(self, tom):
        """Test high confidence belief inference"""
        confidence = tom._calculate_belief_confidence(
            statement="I strongly believe that AI will change everything",
            context="Tech discussion"
        )

        # Should have high confidence due to explicit markers
        assert confidence > 0.5

    @pytest.mark.asyncio
    async def test_calculate_belief_confidence_low(self, tom):
        """Test low confidence for questions"""
        confidence = tom._calculate_belief_confidence(
            statement="Is AI dangerous?",
            context="Question"
        )

        # Questions should have lower confidence
        assert confidence < 0.6

    @pytest.mark.asyncio
    async def test_calculate_belief_confidence_hedging(self, tom):
        """Test low confidence for hedging language"""
        confidence = tom._calculate_belief_confidence(
            statement="Maybe AI might possibly be useful",
            context="Uncertain"
        )

        # Hedging language should reduce confidence
        assert confidence < 0.5

    @pytest.mark.asyncio
    async def test_infer_intention_question(self, tom):
        """Test inferring intention from question"""
        intention = await tom.infer_intention(
            user_id="user_1",
            utterance="How does machine learning work?",
            conversation_context=[]
        )

        assert intention is not None
        assert "Seek information" in intention.goal
        assert intention.confidence > 0.5

    @pytest.mark.asyncio
    async def test_infer_intention_request(self, tom):
        """Test inferring intention from request"""
        intention = await tom.infer_intention(
            user_id="user_1",
            utterance="Can you help me debug this code?",
            conversation_context=[]
        )

        assert intention is not None
        assert intention.intention_type == "immediate"
        assert intention.confidence > 0.6

    @pytest.mark.asyncio
    async def test_infer_intention_want(self, tom):
        """Test inferring intention from want statement"""
        intention = await tom.infer_intention(
            user_id="user_1",
            utterance="I want to learn Python",
            conversation_context=[]
        )

        assert intention is not None
        assert "Python" in intention.goal

    @pytest.mark.asyncio
    async def test_infer_emotional_state_positive(self, tom):
        """Test inferring positive emotional state"""
        emotion = await tom.infer_emotional_state(
            user_id="user_1",
            message="This is amazing! I'm so happy!"
        )

        assert emotion.valence > 0.0  # Positive
        assert emotion.arousal > 0.5  # Exclamation marks indicate high arousal
        assert emotion.confidence > 0.5

    @pytest.mark.asyncio
    async def test_infer_emotional_state_negative(self, tom):
        """Test inferring negative emotional state"""
        emotion = await tom.infer_emotional_state(
            user_id="user_1",
            message="This is terrible and frustrating"
        )

        assert emotion.valence < 0.0  # Negative
        assert emotion.confidence > 0.5

    @pytest.mark.asyncio
    async def test_infer_emotional_state_explicit_emotion(self, tom):
        """Test inferring emotion with explicit emotion word"""
        emotion = await tom.infer_emotional_state(
            user_id="user_1",
            message="I feel sad about this"
        )

        assert emotion.emotion == "sad"
        assert emotion.valence < 0.0
        assert emotion.confidence > 0.6  # Explicit emotion increases confidence

    @pytest.mark.asyncio
    async def test_analyze_valence_positive(self, tom):
        """Test valence analysis for positive text"""
        valence = tom._analyze_valence("This is great and wonderful and excellent")

        assert valence > 0.0

    @pytest.mark.asyncio
    async def test_analyze_valence_negative(self, tom):
        """Test valence analysis for negative text"""
        valence = tom._analyze_valence("This is terrible and awful and bad")

        assert valence < 0.0

    @pytest.mark.asyncio
    async def test_analyze_arousal_high(self, tom):
        """Test arousal analysis for high-arousal text"""
        arousal = tom._analyze_arousal("I'm so excited and thrilled!")

        assert arousal > 0.5

    @pytest.mark.asyncio
    async def test_analyze_arousal_low(self, tom):
        """Test arousal analysis for low-arousal text"""
        arousal = tom._analyze_arousal("I feel calm and peaceful")

        assert arousal < 0.5

    @pytest.mark.asyncio
    async def test_map_to_emotion(self, tom):
        """Test mapping valence-arousal to emotion labels"""
        # High valence, high arousal = excited
        emotion = tom._map_to_emotion(0.8, 0.9)
        assert emotion == "excited"

        # High valence, low arousal = calm
        emotion = tom._map_to_emotion(0.8, 0.2)
        assert emotion == "calm"

        # Low valence, high arousal = angry
        emotion = tom._map_to_emotion(-0.8, 0.9)
        assert emotion == "angry"

        # Low valence, low arousal = sad
        emotion = tom._map_to_emotion(-0.8, 0.2)
        assert emotion == "sad"

    @pytest.mark.asyncio
    async def test_update_knowledge_state(self, tom):
        """Test updating user knowledge state"""
        await tom.update_knowledge_state(
            user_id="user_1",
            new_knowledge="Python basics",
            confidence=0.9
        )

        model = tom.user_models["user_1"]
        assert "Python basics" in model.knowledge_state

    @pytest.mark.asyncio
    async def test_update_knowledge_state_low_confidence(self, tom):
        """Test that low confidence knowledge is not added"""
        await tom.initialize_user_model("user_1")
        initial_count = len(tom.user_models["user_1"].knowledge_state)

        await tom.update_knowledge_state(
            user_id="user_1",
            new_knowledge="Uncertain knowledge",
            confidence=0.2  # Below threshold
        )

        # Should not add low-confidence knowledge
        assert len(tom.user_models["user_1"].knowledge_state) == initial_count

    @pytest.mark.asyncio
    async def test_check_false_belief(self, tom):
        """Test checking for false beliefs"""
        # Add a belief
        await tom.infer_belief(
            user_id="user_1",
            statement="The moon is made of cheese"
        )

        # Check if user has this belief
        has_belief = await tom.check_false_belief(
            user_id="user_1",
            belief_content="moon is made of cheese"
        )

        assert has_belief is True

    @pytest.mark.asyncio
    async def test_perspective_take(self, tom):
        """Test taking user's perspective"""
        # Set up user model with beliefs and preferences
        await tom.infer_belief(
            user_id="user_1",
            statement="I think AI is fascinating"
        )

        perspective = await tom.perspective_take(
            user_id="user_1",
            situation="Discussion about AI development"
        )

        assert 'likely_beliefs' in perspective
        assert 'likely_emotions' in perspective
        assert 'situation' in perspective

    @pytest.mark.asyncio
    async def test_generate_empathetic_response_upset(self, tom):
        """Test generating empathetic response for upset user"""
        response = await tom.generate_empathetic_response(
            user_id="user_1",
            user_message="This is so frustrating and difficult"
        )

        assert isinstance(response, str)
        assert len(response) > 0
        # Should acknowledge difficulty
        assert any(word in response.lower() for word in ['understand', 'help', 'support', 'challenging'])

    @pytest.mark.asyncio
    async def test_generate_empathetic_response_excited(self, tom):
        """Test generating empathetic response for excited user"""
        response = await tom.generate_empathetic_response(
            user_id="user_1",
            user_message="This is amazing! I'm so excited!"
        )

        assert isinstance(response, str)
        # Should match enthusiasm
        assert any(word in response.lower() for word in ['great', 'wonderful', 'exciting', 'enthusiasm'])

    @pytest.mark.asyncio
    async def test_get_user_model_summary(self, tom):
        """Test getting user model summary"""
        # Create some data
        await tom.infer_belief("user_1", "I believe in AI")
        await tom.infer_intention("user_1", "I want to learn ML")
        await tom.update_knowledge_state("user_1", "Python", 0.9)

        summary = await tom.get_user_model_summary("user_1")

        assert 'user_id' in summary
        assert 'beliefs_count' in summary
        assert 'intentions_count' in summary
        assert 'knowledge_items' in summary
        assert summary['beliefs_count'] > 0
        assert summary['intentions_count'] > 0

    @pytest.mark.asyncio
    async def test_multiple_users(self, tom):
        """Test managing multiple user models"""
        await tom.initialize_user_model("user_1")
        await tom.initialize_user_model("user_2")

        assert "user_1" in tom.user_models
        assert "user_2" in tom.user_models
        assert tom.user_models["user_1"].user_id != tom.user_models["user_2"].user_id

    @pytest.mark.asyncio
    async def test_emotional_history_tracking(self, tom):
        """Test that emotional history is tracked"""
        await tom.infer_emotional_state("user_1", "I'm happy")
        await tom.infer_emotional_state("user_1", "Now I'm sad")

        model = tom.user_models["user_1"]
        assert len(model.emotional_history) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
