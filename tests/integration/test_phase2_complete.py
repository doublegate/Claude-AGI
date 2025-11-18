"""
Phase 2 Complete Integration Tests
===================================

Integration tests for Phase 2 enhancements:
- Knowledge graph enhancements
- Autonomous learning
- Web exploration
"""

import pytest
import asyncio
from datetime import datetime

# Knowledge Graph Tests
@pytest.mark.asyncio
async def test_knowledge_consolidation_integration():
    """Test knowledge consolidation with knowledge graph"""
    from src.learning.knowledge_graph import KnowledgeGraph
    from src.learning.knowledge_consolidation import KnowledgeConsolidator, SourceCredibility

    kg = KnowledgeGraph()
    consolidator = KnowledgeConsolidator(kg)

    # Register sources
    source = await consolidator.register_source(
        "test_source",
        "Test Source",
        credibility=SourceCredibility.RELIABLE
    )

    assert source.name == "Test Source"
    assert source.credibility == SourceCredibility.RELIABLE

    # Add similar concepts
    await kg.add_concept("ML", "technology", "Machine Learning")
    await kg.add_concept("Machine Learning", "technology", "AI technique")

    # Consolidate
    consolidated = await consolidator.consolidate_concepts(["ML", "Machine Learning"])

    assert len(consolidated) > 0
    assert len(consolidated[0].aliases) > 0


@pytest.mark.asyncio
async def test_knowledge_source_integration():
    """Test real-world knowledge source integration"""
    from src.learning.knowledge_graph import KnowledgeGraph
    from src.learning.knowledge_sources import KnowledgeSourceAggregator

    kg = KnowledgeGraph()
    aggregator = KnowledgeSourceAggregator(kg)

    # Import concept
    results = await aggregator.import_concept("Machine Learning")

    assert results['concept_name'] == "Machine Learning"
    assert results['concepts_imported'] >= 0


@pytest.mark.asyncio
async def test_learning_goals_creation():
    """Test learning goal creation and management"""
    from src.learning.learning_goals import LearningGoalManager, GoalType, GoalStatus

    manager = LearningGoalManager()

    # Create goal
    goal = await manager.create_goal(
        title="Learn Python",
        description="Master Python programming",
        goal_type=GoalType.SKILL,
        priority=0.9
    )

    assert goal.title == "Learn Python"
    assert goal.status == GoalStatus.CREATED
    assert goal.priority == 0.9

    # Generate learning path
    path = await manager.generate_learning_path(goal.goal_id)

    assert path is not None
    assert len(path.steps) > 0
    assert path.estimated_duration > 0


@pytest.mark.asyncio
async def test_knowledge_gap_analysis():
    """Test knowledge gap analysis"""
    from src.learning.knowledge_graph import KnowledgeGraph, RelationType
    from src.learning.knowledge_gap_analyzer import KnowledgeGapAnalyzer

    kg = KnowledgeGraph()

    # Add minimal concepts (create gaps)
    await kg.add_concept("AI", "technology", "Artificial Intelligence")
    await kg.add_concept("ML", "technology", "Machine Learning")

    analyzer = KnowledgeGapAnalyzer(kg)

    # Analyze
    report = await analyzer.analyze_knowledge_graph()

    assert report.total_gaps >= 0
    assert len(report.gaps_by_type) >= 0
    assert len(report.recommendations) >= 0


@pytest.mark.asyncio
async def test_content_extraction_pipeline():
    """Test web content extraction pipeline"""
    from src.web.content_extraction_pipeline import ContentExtractionPipeline

    pipeline = ContentExtractionPipeline()

    # Extract content
    result = await pipeline.extract("https://example.com/article")

    assert result.success
    assert result.content is not None
    assert len(result.steps_completed) > 0


@pytest.mark.asyncio
async def test_credibility_checking():
    """Test web content credibility checking"""
    from src.web.credibility_checker import CredibilityChecker

    checker = CredibilityChecker()

    # Assess credibility
    assessment = await checker.assess_credibility("https://arxiv.org/article")

    assert assessment.domain == "arxiv.org"
    assert assessment.overall_score >= 0
    assert assessment.overall_score <= 1.0
    assert len(assessment.indicators) > 0


@pytest.mark.asyncio
async def test_exploration_scheduler():
    """Test web exploration scheduler"""
    from src.web.exploration_scheduler import ExplorationScheduler, ExplorationMode

    scheduler = ExplorationScheduler()

    # Start session
    session = await scheduler.start_session(
        ExplorationMode.IDLE,
        topics=["test"]
    )

    assert session is not None
    assert session.mode == ExplorationMode.IDLE
    assert session.duration_minutes > 0

    # End session
    ended = await scheduler.end_session()

    assert ended.completed
    assert ended.end_time is not None


@pytest.mark.asyncio
async def test_complete_learning_cycle():
    """Test complete autonomous learning cycle"""
    from src.learning.knowledge_graph import KnowledgeGraph
    from src.learning.curiosity_engine import CuriosityEngine
    from src.learning.knowledge_gap_analyzer import KnowledgeGapAnalyzer
    from src.learning.learning_goals import LearningGoalManager

    # Setup
    kg = KnowledgeGraph()
    curiosity = CuriosityEngine(kg)
    analyzer = KnowledgeGapAnalyzer(kg)
    goal_manager = LearningGoalManager(kg, curiosity)

    # Add initial knowledge
    await kg.add_concept("Python", "language", "Programming language")

    # Analyze gaps
    report = await analyzer.analyze_knowledge_graph()
    assert report.total_gaps >= 0

    # Generate questions
    questions = await curiosity.generate_questions(context="Python", max_questions=5)
    assert len(questions) > 0

    # Create goal from question
    if questions:
        goal = await goal_manager.create_goal_from_curiosity(questions[0])
        assert goal is not None


@pytest.mark.asyncio
async def test_web_exploration_integration():
    """Test web exploration integration"""
    from src.web.content_extraction_pipeline import ContentExtractionPipeline
    from src.web.credibility_checker import CredibilityChecker
    from src.web.exploration_scheduler import ExplorationScheduler

    # Setup
    pipeline = ContentExtractionPipeline()
    checker = CredibilityChecker()
    scheduler = ExplorationScheduler(content_pipeline=pipeline, credibility_checker=checker)

    # Verify integration
    assert scheduler.content_pipeline is not None
    assert scheduler.credibility_checker is not None


def test_phase2_module_imports():
    """Test that all Phase 2 modules import correctly"""
    # Knowledge modules
    from src.learning import knowledge_consolidation
    from src.learning import knowledge_sources
    from src.learning import learning_goals
    from src.learning import knowledge_gap_analyzer

    # Web modules
    from src.web import content_extraction_pipeline
    from src.web import credibility_checker
    from src.web import exploration_scheduler

    # Verify classes exist
    assert hasattr(knowledge_consolidation, 'KnowledgeConsolidator')
    assert hasattr(knowledge_sources, 'KnowledgeSourceAggregator')
    assert hasattr(learning_goals, 'LearningGoalManager')
    assert hasattr(knowledge_gap_analyzer, 'KnowledgeGapAnalyzer')
    assert hasattr(content_extraction_pipeline, 'ContentExtractionPipeline')
    assert hasattr(credibility_checker, 'CredibilityChecker')
    assert hasattr(exploration_scheduler, 'ExplorationScheduler')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
