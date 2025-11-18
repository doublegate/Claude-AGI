"""
Unit Tests for Curiosity Engine
================================

Tests for curiosity-driven exploration and question generation.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from src.learning.curiosity_engine import (
    CuriosityEngine,
    ExplorationScheduler,
    CuriosityType,
    CuriosityQuestion,
    KnowledgeGap,
    InterestTopic
)
from src.learning.knowledge_graph import KnowledgeGraph


class TestCuriosityEngine:
    """Test the CuriosityEngine class"""

    @pytest.fixture
    async def knowledge_graph(self):
        """Create a knowledge graph for testing"""
        kg = KnowledgeGraph()
        await kg.add_concept("AI", "field", "Artificial Intelligence")
        await kg.add_concept("Machine Learning", "subfield", "Subset of AI")
        await kg.add_concept("Deep Learning", "technique", "Neural networks")
        return kg

    @pytest.fixture
    def engine(self, knowledge_graph):
        """Create a curiosity engine instance"""
        return CuriosityEngine(knowledge_graph)

    @pytest.mark.asyncio
    async def test_generate_questions_basic(self, engine):
        """Test basic question generation"""
        questions = await engine.generate_questions(context="AI research", max_questions=5)

        assert len(questions) > 0
        assert len(questions) <= 5
        for q in questions:
            assert isinstance(q, CuriosityQuestion)
            assert q.question is not None
            assert q.curiosity_type in CuriosityType

    @pytest.mark.asyncio
    async def test_generate_epistemic_questions(self, engine):
        """Test generation of epistemic (how/why) questions"""
        questions = await engine._generate_epistemic_questions(context="learning", count=3)

        assert len(questions) <= 3
        for q in questions:
            assert q.curiosity_type == CuriosityType.EPISTEMIC
            # Epistemic questions should ask how/why
            assert any(word in q.question.lower() for word in ['how', 'why', 'what'])

    @pytest.mark.asyncio
    async def test_generate_perceptual_questions(self, engine):
        """Test generation of perceptual (what's new) questions"""
        questions = await engine._generate_perceptual_questions(context="technology", count=3)

        assert len(questions) <= 3
        for q in questions:
            assert q.curiosity_type == CuriosityType.PERCEPTUAL

    @pytest.mark.asyncio
    async def test_generate_specific_questions(self, engine):
        """Test generation of specific targeted questions"""
        # Add a knowledge gap first
        await engine.identify_knowledge_gap(
            topic="Quantum Computing",
            gap_type="missing_concept",
            evidence="User mentioned it",
            importance=0.8
        )

        questions = await engine._generate_specific_questions(context="physics", count=3)

        assert len(questions) > 0
        for q in questions:
            assert q.curiosity_type == CuriosityType.SPECIFIC

    @pytest.mark.asyncio
    async def test_generate_diversive_questions(self, engine):
        """Test generation of diversive (broad) questions"""
        questions = await engine._generate_diversive_questions(context="general", count=5)

        assert len(questions) > 0
        for q in questions:
            assert q.curiosity_type == CuriosityType.DIVERSIVE
            # Should have lower priority
            assert q.priority < 0.7

    @pytest.mark.asyncio
    async def test_identify_knowledge_gap(self, engine):
        """Test knowledge gap identification"""
        await engine.identify_knowledge_gap(
            topic="Neural Networks",
            gap_type="weak_understanding",
            evidence="Confusion during conversation",
            importance=0.7,
            related_concepts=["AI", "Deep Learning"]
        )

        assert "Neural Networks" in engine.known_gaps
        gap = engine.known_gaps["Neural Networks"]
        assert gap.gap_type == "weak_understanding"
        assert gap.importance == 0.7
        assert "AI" in gap.related_concepts

    @pytest.mark.asyncio
    async def test_update_interest_new_topic(self, engine):
        """Test updating interest for a new topic"""
        await engine.update_interest(
            topic="Robotics",
            weight_change=0.2,
            exploration_occurred=True,
            satisfaction=0.8
        )

        assert "Robotics" in engine.interests
        interest = engine.interests["Robotics"]
        assert interest.weight > 0.5  # Should be above base
        assert interest.total_explorations == 1

    @pytest.mark.asyncio
    async def test_update_interest_satisfaction_boost(self, engine):
        """Test that high satisfaction boosts interest weight"""
        topic = "Space Exploration"

        # First exploration with high satisfaction
        await engine.update_interest(topic, exploration_occurred=True, satisfaction=0.9)
        initial_weight = engine.interests[topic].weight

        # Second exploration with high satisfaction
        await engine.update_interest(topic, exploration_occurred=True, satisfaction=0.9)
        final_weight = engine.interests[topic].weight

        assert final_weight >= initial_weight  # Should maintain or increase

    @pytest.mark.asyncio
    async def test_update_interest_low_satisfaction(self, engine):
        """Test that low satisfaction reduces interest"""
        topic = "Boring Topic"

        await engine.update_interest(topic, exploration_occurred=True, satisfaction=0.2)

        interest = engine.interests[topic]
        # Low satisfaction should keep weight low
        assert interest.weight < 0.6

    @pytest.mark.asyncio
    async def test_apply_interest_decay(self, engine):
        """Test interest decay over time"""
        # Create an interest with recent exploration
        await engine.update_interest("Old Topic", exploration_occurred=True)

        # Manually set last_explored to past
        engine.interests["Old Topic"].last_explored = datetime.now() - timedelta(days=30)
        initial_weight = engine.interests["Old Topic"].weight

        # Apply decay
        await engine.apply_interest_decay()

        final_weight = engine.interests["Old Topic"].weight
        assert final_weight < initial_weight  # Should decay

    @pytest.mark.asyncio
    async def test_get_next_exploration_target(self, engine):
        """Test getting next exploration target"""
        # Add some interests
        await engine.update_interest("Topic A", weight_change=0.3)
        await engine.update_interest("Topic B", weight_change=0.5)

        target = await engine.get_next_exploration_target()

        assert target is not None
        assert target in engine.interests

    @pytest.mark.asyncio
    async def test_get_next_exploration_target_with_gaps(self, engine):
        """Test that knowledge gaps influence next target"""
        # Add a high-priority gap
        await engine.identify_knowledge_gap(
            topic="Critical Gap",
            gap_type="missing_concept",
            evidence="Important",
            importance=0.9
        )

        target = await engine.get_next_exploration_target()

        # Should likely select the high-priority gap
        assert target is not None

    @pytest.mark.asyncio
    async def test_mark_question_answered(self, engine):
        """Test marking a question as answered"""
        question = CuriosityQuestion(
            question="How does AI work?",
            curiosity_type=CuriosityType.EPISTEMIC,
            priority=0.8,
            context="Learning about AI",
            related_concepts=["AI", "Machine Learning"]
        )

        await engine.mark_question_answered(
            question,
            answer="AI works through algorithms and data",
            satisfaction=0.7
        )

        assert question.answered is True
        assert question.answer is not None
        assert question in engine.answered_questions

    @pytest.mark.asyncio
    async def test_mark_question_answered_low_satisfaction(self, engine):
        """Test that low satisfaction creates follow-up gap"""
        question = CuriosityQuestion(
            question="What is quantum computing?",
            curiosity_type=CuriosityType.SPECIFIC,
            priority=0.7,
            context="Physics",
            related_concepts=["Quantum Computing"]
        )

        await engine.mark_question_answered(
            question,
            answer="Brief answer",
            satisfaction=0.3  # Low satisfaction
        )

        # Should create a knowledge gap for follow-up
        assert len(engine.known_gaps) > 0

    @pytest.mark.asyncio
    async def test_get_curiosity_statistics(self, engine):
        """Test getting curiosity statistics"""
        # Generate some questions
        await engine.generate_questions(max_questions=5)

        stats = await engine.get_curiosity_statistics()

        assert 'pending_questions' in stats
        assert 'answered_questions' in stats
        assert 'total_questions' in stats
        assert 'knowledge_gaps' in stats
        assert 'active_interests' in stats
        assert 'curiosity_types_distribution' in stats

    @pytest.mark.asyncio
    async def test_question_priority_ordering(self, engine):
        """Test that questions are ordered by priority"""
        questions = await engine.generate_questions(max_questions=10)

        if len(questions) > 1:
            # Check that priorities are in descending order
            for i in range(len(questions) - 1):
                assert questions[i].priority >= questions[i + 1].priority


class TestExplorationScheduler:
    """Test the ExplorationScheduler class"""

    @pytest.fixture
    def engine(self):
        """Create a curiosity engine"""
        return CuriosityEngine()

    @pytest.fixture
    def scheduler(self, engine):
        """Create an exploration scheduler"""
        return ExplorationScheduler(engine)

    @pytest.mark.asyncio
    async def test_start_exploration_session(self, scheduler):
        """Test starting an exploration session"""
        session = await scheduler.start_exploration_session(
            mode="active",
            duration_minutes=30,
            focus_topics=["AI", "Robotics"]
        )

        assert session is not None
        assert session['mode'] == "active"
        assert session['duration_minutes'] == 30
        assert "AI" in session['focus_topics']
        assert scheduler.is_session_active()

    @pytest.mark.asyncio
    async def test_end_exploration_session(self, scheduler):
        """Test ending an exploration session"""
        # Start a session
        await scheduler.start_exploration_session("idle", 10)

        # Record some activity
        await scheduler.record_discovery("Learned about neural nets", 0.8)

        # End session
        summary = await scheduler.end_exploration_session()

        assert summary is not None
        assert 'end_time' in summary
        assert 'average_satisfaction' in summary
        assert summary['questions_explored'] == 1
        assert not scheduler.is_session_active()

    @pytest.mark.asyncio
    async def test_record_discovery(self, scheduler):
        """Test recording a discovery"""
        await scheduler.start_exploration_session("active", 20)

        await scheduler.record_discovery("New concept learned", 0.9)

        session = scheduler.active_session
        assert len(session['discoveries']) == 1
        assert session['questions_explored'] == 1
        assert 0.9 in session['satisfaction_scores']

    @pytest.mark.asyncio
    async def test_should_explore_now_user_present(self, scheduler):
        """Test exploration decision when user is present"""
        should_explore, mode = scheduler.should_explore_now(
            system_state='IDLE',
            user_present=True
        )

        if should_explore:
            assert mode == 'idle'  # Background only when user present

    @pytest.mark.asyncio
    async def test_should_explore_now_user_away(self, scheduler):
        """Test exploration decision when user is away"""
        should_explore, mode = scheduler.should_explore_now(
            system_state='IDLE',
            user_present=False
        )

        if should_explore:
            assert mode in ['active', 'idle']

    @pytest.mark.asyncio
    async def test_should_explore_during_sleep(self, scheduler):
        """Test exploration during sleep state"""
        should_explore, mode = scheduler.should_explore_now(
            system_state='SLEEPING',
            user_present=False
        )

        if should_explore:
            assert mode == 'dream'  # Deep exploration during sleep


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
