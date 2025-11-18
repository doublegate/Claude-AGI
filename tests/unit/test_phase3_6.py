"""
Tests for Phases 3-6 Components
================================

Tests for social intelligence, creative capabilities, meta-cognitive,
and AGI integration components.
"""

import pytest
from datetime import datetime

from src.social.relationship_manager import RelationshipManager, RelationshipType
from src.creative.novelty_detector import NoveltyDetector, CreativeWork
from src.metacognitive.self_model import SelfModel, CapabilityLevel
from src.reasoning.causal_reasoner import CausalReasoner


class TestRelationshipManager:
    """Test relationship management"""

    @pytest.mark.asyncio
    async def test_create_profile(self):
        """Test creating user profile"""
        manager = RelationshipManager()

        profile = await manager.get_or_create_profile("user123", "Test User")

        assert profile is not None
        assert profile.user_id == "user123"
        assert profile.name == "Test User"
        assert profile.relationship_type == RelationshipType.CASUAL

    @pytest.mark.asyncio
    async def test_record_interaction(self):
        """Test recording interactions"""
        manager = RelationshipManager()

        await manager.record_interaction(
            "user123",
            "conversation",
            {"topic": "AI", "topics": ["machine_learning"]},
            sentiment=0.8
        )

        profile = manager.profiles["user123"]
        assert profile.interaction_count == 1
        assert "machine_learning" in profile.topics_of_interest

    @pytest.mark.asyncio
    async def test_relationship_progression(self):
        """Test relationship type progression"""
        manager = RelationshipManager()

        # Simulate many interactions
        for i in range(25):
            await manager.record_interaction(
                "user123",
                "conversation",
                {"topic": f"topic{i}"},
                sentiment=0.7
            )

        profile = manager.profiles["user123"]
        assert profile.relationship_type == RelationshipType.REGULAR


class TestNoveltyDetector:
    """Test novelty detection"""

    @pytest.mark.asyncio
    async def test_evaluate_novelty_first_work(self):
        """Test novelty of first creative work"""
        detector = NoveltyDetector()

        work = CreativeWork(
            work_id="work1",
            content="This is a unique creative piece with original ideas",
            work_type="text"
        )

        result = await detector.evaluate_novelty(work)

        assert result['novelty_score'] > 0.5  # Should be novel
        assert 'uniqueness' in result['factors']

    @pytest.mark.asyncio
    async def test_evaluate_similarity(self):
        """Test similarity detection between works"""
        detector = NoveltyDetector()

        work1 = CreativeWork(
            work_id="work1",
            content="The quick brown fox jumps over the lazy dog",
            work_type="text"
        )

        work2 = CreativeWork(
            work_id="work2",
            content="The quick brown fox runs over the sleepy cat",
            work_type="text"
        )

        await detector.evaluate_novelty(work1)
        result2 = await detector.evaluate_novelty(work2)

        # Second work should be less novel (similar to first)
        assert result2['novelty_score'] < 0.8


class TestSelfModel:
    """Test self-model functionality"""

    @pytest.mark.asyncio
    async def test_assess_capability(self):
        """Test capability assessment"""
        model = SelfModel()

        cap = await model.assess_capability(
            "problem_solving",
            task_outcome=True,
            difficulty=0.7
        )

        assert cap.name == "problem_solving"
        assert cap.confidence > 0.5

    @pytest.mark.asyncio
    async def test_capability_level_progression(self):
        """Test capability level increases with success"""
        model = SelfModel()

        # Multiple successful tasks
        for _ in range(20):
            await model.assess_capability(
                "test_skill",
                task_outcome=True,
                difficulty=0.5
            )

        cap = model.capabilities["test_skill"]
        assert cap.level.value > CapabilityLevel.BASIC.value

    @pytest.mark.asyncio
    async def test_identify_limitation(self):
        """Test limitation identification"""
        model = SelfModel()

        limitation = await model.identify_limitation(
            "Cannot process images",
            severity=0.8
        )

        assert limitation.description == "Cannot process images"
        assert limitation.severity == 0.8
        assert len(model.limitations) == 1

    @pytest.mark.asyncio
    async def test_introspection(self):
        """Test self-introspection"""
        model = SelfModel()

        # Add some capabilities
        await model.assess_capability("skill1", True, 0.5)
        await model.identify_limitation("limitation1", 0.5)

        insights = await model.introspect()

        assert 'capabilities' in insights
        assert 'limitations' in insights
        assert 'personality' in insights


class TestCausalReasoner:
    """Test causal reasoning"""

    @pytest.mark.asyncio
    async def test_observe_data(self):
        """Test observing data"""
        reasoner = CausalReasoner()

        await reasoner.observe({
            'study_time': 5,
            'test_score': 85
        })

        assert len(reasoner.observations) == 1
        assert 'study_time' in reasoner.variables
        assert 'test_score' in reasoner.variables

    @pytest.mark.asyncio
    async def test_propose_causal_relationship(self):
        """Test proposing causal relationships"""
        reasoner = CausalReasoner()

        rel = await reasoner.propose_causal_relationship(
            cause="exercise",
            effect="health",
            strength=0.7,
            confidence=0.8
        )

        assert rel.cause == "exercise"
        assert rel.effect == "health"
        assert rel.strength == 0.7

    @pytest.mark.asyncio
    async def test_predict_outcome(self):
        """Test outcome prediction"""
        reasoner = CausalReasoner()

        # Establish causal relationship
        await reasoner.propose_causal_relationship(
            "temperature",
            "ice_cream_sales",
            strength=0.8,
            confidence=0.9
        )

        predictions = await reasoner.predict_outcome({
            'temperature': 1.0  # Increase temperature
        })

        assert 'ice_cream_sales' in predictions


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
