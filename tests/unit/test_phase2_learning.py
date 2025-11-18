"""
Tests for Phase 2 Learning Systems
===================================

Tests goal management, knowledge graphs, skill system, and transfer learning.
"""

import pytest
from datetime import datetime, timedelta

from src.learning.goal_manager import GoalManager, GoalType, GoalPriority, GoalStatus
from src.learning.knowledge_graph import KnowledgeGraph, RelationType
from src.learning.skill_system import SkillSystem, SkillDomain, ProficiencyLevel
from src.learning.transfer_learning import TransferLearningEngine


class TestGoalManager:
    """Test goal management functionality"""

    @pytest.mark.asyncio
    async def test_create_goal(self):
        """Test creating a new goal"""
        manager = GoalManager()

        goal = await manager.create_goal(
            description="Learn Python programming",
            goal_type=GoalType.LONG_TERM,
            priority=GoalPriority.HIGH,
            success_criteria=["Complete tutorial", "Build project"]
        )

        assert goal is not None
        assert goal.description == "Learn Python programming"
        assert goal.status == GoalStatus.PROPOSED
        assert len(goal.success_criteria) == 2

    @pytest.mark.asyncio
    async def test_activate_goal(self):
        """Test activating a goal"""
        manager = GoalManager()

        goal = await manager.create_goal(
            description="Test goal",
            goal_type=GoalType.SESSION,
            priority=GoalPriority.MEDIUM
        )

        success = await manager.activate_goal(goal.id)

        assert success is True
        assert goal.status == GoalStatus.ACTIVE
        assert goal.id in manager.active_goals

    @pytest.mark.asyncio
    async def test_update_progress(self):
        """Test updating goal progress"""
        manager = GoalManager()

        goal = await manager.create_goal(
            description="Test progress",
            goal_type=GoalType.PROJECT,
            priority=GoalPriority.HIGH
        )

        await manager.activate_goal(goal.id)
        await manager.update_progress(goal.id, 0.5, "Halfway milestone")

        assert goal.progress == 0.5
        assert len(goal.milestones) == 1

    @pytest.mark.asyncio
    async def test_goal_completion(self):
        """Test completing a goal"""
        manager = GoalManager()

        goal = await manager.create_goal(
            description="Completable goal",
            goal_type=GoalType.IMMEDIATE,
            priority=GoalPriority.MEDIUM
        )

        await manager.activate_goal(goal.id)
        await manager.update_progress(goal.id, 1.0)

        assert goal.status == GoalStatus.COMPLETED
        assert goal.id in manager.completed_goals


class TestKnowledgeGraph:
    """Test knowledge graph functionality"""

    @pytest.mark.asyncio
    async def test_add_concept(self):
        """Test adding a concept to the graph"""
        kg = KnowledgeGraph()

        concept = await kg.add_concept(
            name="Machine Learning",
            concept_type="field",
            description="AI subfield focused on learning from data"
        )

        assert concept is not None
        assert concept.name == "Machine Learning"
        assert "Machine Learning" in kg.concept_by_name

    @pytest.mark.asyncio
    async def test_add_relationship(self):
        """Test adding relationships between concepts"""
        kg = KnowledgeGraph()

        await kg.add_concept("Python", "programming_language")
        await kg.add_concept("Programming", "skill")

        rel = await kg.add_relationship(
            "Python",
            "Programming",
            RelationType.PART_OF
        )

        assert rel is not None
        assert rel.relation_type == RelationType.PART_OF

    @pytest.mark.asyncio
    async def test_find_path(self):
        """Test finding paths between concepts"""
        kg = KnowledgeGraph()

        await kg.add_concept("A", "test")
        await kg.add_concept("B", "test")
        await kg.add_concept("C", "test")

        await kg.add_relationship("A", "B", RelationType.RELATED_TO)
        await kg.add_relationship("B", "C", RelationType.RELATED_TO)

        path = await kg.find_path("A", "C")

        assert path is not None
        assert len(path) == 3
        assert path == ["A", "B", "C"]


class TestSkillSystem:
    """Test skill acquisition and management"""

    @pytest.mark.asyncio
    async def test_create_skill(self):
        """Test creating a new skill"""
        system = SkillSystem()

        skill = await system.create_skill(
            name="Data Analysis",
            domain=SkillDomain.ANALYTICAL,
            description="Analyzing and interpreting data"
        )

        assert skill is not None
        assert skill.name == "Data Analysis"
        assert skill.domain == SkillDomain.ANALYTICAL

    @pytest.mark.asyncio
    async def test_practice_skill(self):
        """Test skill practice and proficiency gain"""
        system = SkillSystem()

        skill = await system.create_skill(
            name="Test Skill",
            domain=SkillDomain.TECHNICAL,
            description="For testing"
        )

        result = await system.practice_skill(
            skill.skill_id,
            duration=60.0,  # 1 hour
            performance=0.8,
            success=True
        )

        assert result['new_proficiency'] > 0.0
        assert skill.practice_sessions == 1
        assert skill.success_rate > 0.0

    @pytest.mark.asyncio
    async def test_proficiency_levels(self):
        """Test proficiency level calculation"""
        level = ProficiencyLevel.from_proficiency(0.1)
        assert level == ProficiencyLevel.NOVICE

        level = ProficiencyLevel.from_proficiency(0.5)
        assert level == ProficiencyLevel.INTERMEDIATE

        level = ProficiencyLevel.from_proficiency(0.9)
        assert level == ProficiencyLevel.EXPERT


class TestTransferLearning:
    """Test transfer learning capabilities"""

    @pytest.mark.asyncio
    async def test_identify_pattern(self):
        """Test identifying transferable patterns"""
        engine = TransferLearningEngine()

        pattern = await engine.identify_transferable_pattern(
            source_skill="programming",
            source_domain="technical",
            pattern_data={
                'type': 'structural',
                'is_principle': True
            }
        )

        assert pattern is not None
        assert pattern.source_domain == "technical"
        assert pattern.abstraction_level > 0.5

    @pytest.mark.asyncio
    async def test_domain_similarity(self):
        """Test domain similarity calculation"""
        engine = TransferLearningEngine()

        # Same domain should be 1.0
        sim = engine.get_domain_similarity("technical", "technical")
        assert sim == 1.0

        # Related domains should have some similarity
        sim = engine.get_domain_similarity("technical", "analytical")
        assert sim > 0.5

    @pytest.mark.asyncio
    async def test_transfer_recommendations(self):
        """Test getting transfer recommendations"""
        engine = TransferLearningEngine()

        # Add some patterns
        await engine.identify_transferable_pattern(
            "skill1",
            "technical",
            {'type': 'conceptual'}
        )

        recommendations = await engine.get_transfer_recommendations(
            target_skill="new_skill",
            target_domain="analytical",
            available_skills=[("skill1", "technical", 0.8)]
        )

        assert isinstance(recommendations, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
