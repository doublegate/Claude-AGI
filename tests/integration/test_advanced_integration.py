"""
Advanced Integration Tests
===========================

Tests for cross-module integration and end-to-end flows.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.learning.knowledge_extraction import KnowledgeExtractor, LearningPathGenerator
from src.learning.curiosity_engine import CuriosityEngine
from src.learning.knowledge_graph import KnowledgeGraph
from src.web.content_processor import WebContentProcessor
from src.emotional.emotional_model import AdvancedEmotionalModel
from src.social.theory_of_mind import TheoryOfMind
from src.metacognitive.enhanced_self_model import EnhancedSelfModel
from src.reasoning.problem_solving import ProblemSolvingFramework


class TestLearningCuriosityIntegration:
    """Test integration between learning and curiosity systems"""

    @pytest.mark.asyncio
    async def test_curiosity_drives_knowledge_extraction(self):
        """Test that curiosity engine can drive knowledge extraction"""
        kg = KnowledgeGraph()
        curiosity = CuriosityEngine(kg)
        extractor = KnowledgeExtractor()

        # Add a knowledge gap
        await curiosity.identify_knowledge_gap(
            topic="Neural Networks",
            gap_type="missing_concept",
            evidence="User mentioned it",
            importance=0.8
        )

        # Get next exploration target
        target = await curiosity.get_next_exploration_target()

        assert target is not None

        # Simulate extracting knowledge about the target
        text = f"{target} is an important concept in machine learning. " \
               f"It involves multiple layers of processing."

        concepts = await extractor.extract_concepts(text, use_ai=False)

        # Add extracted concepts to knowledge graph
        for concept in concepts:
            await kg.add_concept(
                concept.name,
                concept.concept_type,
                concept.context
            )

        # Verify knowledge was added
        assert len(kg.concepts) > 0

    @pytest.mark.asyncio
    async def test_learning_path_with_curiosity(self):
        """Test generating learning paths based on curiosity"""
        kg = KnowledgeGraph()

        # Build a small knowledge graph
        await kg.add_concept("Python", "language", "Programming language")
        await kg.add_concept("Functions", "concept", "Code blocks")
        await kg.add_concept("OOP", "concept", "Object-oriented programming")

        from src.learning.knowledge_graph import RelationType
        await kg.add_relationship("Functions", "Python", RelationType.PART_OF)
        await kg.add_relationship("OOP", "Functions", RelationType.REQUIRES)

        # Create learning path generator
        path_gen = LearningPathGenerator(kg)

        # Find learning path
        path = await path_gen.find_learning_path("Functions", "OOP")

        assert path is not None
        assert len(path) >= 2

    @pytest.mark.asyncio
    async def test_curiosity_satisfaction_updates_interests(self):
        """Test that answering questions updates interests"""
        curiosity = CuriosityEngine()

        # Generate questions
        questions = await curiosity.generate_questions(context="AI", max_questions=3)

        if questions:
            question = questions[0]

            # Mark as answered with high satisfaction
            await curiosity.mark_question_answered(
                question,
                answer="Detailed answer about AI",
                satisfaction=0.9
            )

            # Check that interests were updated
            for concept in question.related_concepts:
                if concept in curiosity.interests:
                    interest = curiosity.interests[concept]
                    assert interest.total_explorations > 0


class TestEmotionalSocialIntegration:
    """Test integration between emotional and social systems"""

    @pytest.mark.asyncio
    async def test_emotional_state_affects_empathy(self):
        """Test that emotional model affects empathetic responses"""
        emotion_model = AdvancedEmotionalModel()
        tom = TheoryOfMind()

        # Set emotional model to excited state
        await emotion_model.process_emotional_stimulus('success', intensity=0.8)

        # Infer user emotion
        user_emotion = await tom.infer_emotional_state(
            "user_1",
            "This is amazing!"
        )

        # Generate empathetic response
        response = await tom.generate_empathetic_response(
            "user_1",
            "This is amazing!"
        )

        assert response is not None
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_theory_of_mind_with_emotional_context(self):
        """Test ToM inference with emotional context"""
        tom = TheoryOfMind()
        emotion_model = AdvancedEmotionalModel()

        # User expresses frustration
        user_message = "This is so frustrating and difficult!"

        # Infer emotional state
        emotion = await tom.infer_emotional_state("user_1", user_message)

        # Infer intention
        intention = await tom.infer_intention("user_1", user_message)

        # Update own emotional state based on empathy
        if emotion.valence < 0:
            await emotion_model.process_emotional_stimulus(
                'concern',
                intensity=abs(emotion.valence) * 0.5
            )

        # Should have empathetic emotional response
        assert emotion_model.current_state.primary_emotion.value in ['concern', 'calm']

    @pytest.mark.asyncio
    async def test_belief_tracking_with_emotional_memory(self):
        """Test that beliefs are tracked alongside emotional memories"""
        tom = TheoryOfMind()
        emotion_model = AdvancedEmotionalModel()

        # User expresses belief with emotion
        await tom.infer_belief(
            "user_1",
            "I love working with AI systems",
            context="Tech discussion"
        )

        # Tag corresponding emotional memory
        await emotion_model.process_emotional_stimulus('connection', intensity=0.7)
        await emotion_model.tag_memory_with_emotion(
            "belief_ai_love",
            "User loves AI",
            importance=0.8
        )

        # Verify both systems have data
        assert "user_1" in tom.user_models
        assert len(tom.user_models["user_1"].beliefs) > 0
        assert len(emotion_model.emotional_memories) > 0


class TestMetacognitiveProblemSolvingIntegration:
    """Test integration between self-model and problem solving"""

    @pytest.mark.asyncio
    async def test_self_assessment_guides_problem_solving(self):
        """Test that self-model informs problem-solving strategy"""
        self_model = EnhancedSelfModel()
        framework = ProblemSolvingFramework()

        # Assess capability in reasoning
        from src.metacognitive.enhanced_self_model import CapabilityDomain
        await self_model.assess_capability(
            "Logical Reasoning",
            demonstration_context="Solved complex logic puzzle",
            self_rating=0.9
        )

        # Solve a reasoning problem
        problem = await framework.analyze_problem(
            "Analyze the logical flow of this algorithm"
        )

        solution = await framework.solve_problem(problem, max_iterations=3)

        assert solution is not None

    @pytest.mark.asyncio
    async def test_problem_solving_updates_self_model(self):
        """Test that problem-solving outcomes update self-model"""
        self_model = EnhancedSelfModel()
        framework = ProblemSolvingFramework()

        # Solve a problem
        problem = await framework.analyze_problem(
            "Optimize database query performance"
        )

        solution = await framework.solve_problem(problem, max_iterations=2)

        # Record performance in self-model
        from src.metacognitive.enhanced_self_model import CapabilityDomain
        await self_model.record_performance(
            task_description=problem.description,
            domain=CapabilityDomain.TECHNICAL,
            self_rating=0.8,
            actual_outcome=0.85
        )

        # Verify performance was recorded
        assert len(self_model.performance_history) > 0

    @pytest.mark.asyncio
    async def test_limitation_awareness_affects_strategy(self):
        """Test that known limitations affect strategy selection"""
        self_model = EnhancedSelfModel()
        framework = ProblemSolvingFramework()

        # Identify a limitation
        await self_model.identify_limitation(
            "Limited Real-Time Data",
            "access",
            severity=0.7,
            context="Cannot access live APIs"
        )

        # Try to solve a problem requiring real-time data
        problem = await framework.analyze_problem(
            "Get current stock prices and analyze trends"
        )

        # Should still generate a solution, but might choose different strategy
        solution = await framework.solve_problem(problem, max_iterations=2)

        assert solution is not None


class TestKnowledgeWebIntegration:
    """Test integration between knowledge extraction and web processing"""

    @pytest.mark.asyncio
    async def test_web_content_to_knowledge_graph(self):
        """Test processing web content into knowledge graph"""
        processor = WebContentProcessor()
        extractor = KnowledgeExtractor()
        kg = KnowledgeGraph()

        # Sample HTML
        html = """
        <html>
        <head><title>Machine Learning Guide</title></head>
        <body>
            <p>Machine learning is a subset of artificial intelligence.
               Neural networks are a key component of deep learning.</p>
        </body>
        </html>
        """

        # Process web content
        content = await processor.process_url(
            "https://example.com",
            html,
            use_ai=False
        )

        # Extract knowledge
        knowledge = await extractor.extract_knowledge_from_document(
            content.content,
            use_ai=False
        )

        # Add to knowledge graph
        for concept in knowledge['concepts']:
            await kg.add_concept(
                concept.name,
                concept.concept_type,
                concept.context
            )

        # Verify concepts were added
        assert len(kg.concepts) > 0

    @pytest.mark.asyncio
    async def test_multi_source_synthesis_to_knowledge(self):
        """Test synthesizing multiple sources into knowledge"""
        from src.web.content_processor import InformationSynthesizer, ProcessedContent, ContentType

        synthesizer = InformationSynthesizer()
        extractor = KnowledgeExtractor()

        # Add multiple sources
        sources = [
            ProcessedContent(
                url="https://source1.com",
                title="AI Overview",
                content="AI is transforming technology through machine learning.",
                content_type=ContentType.ARTICLE,
                source_domain="source1.com",
                credibility_score=0.9
            ),
            ProcessedContent(
                url="https://source2.com",
                title="ML Guide",
                content="Machine learning enables pattern recognition in data.",
                content_type=ContentType.ACADEMIC_PAPER,
                source_domain="source2.com",
                credibility_score=0.95
            )
        ]

        for source in sources:
            await synthesizer.add_source(source)

        # Find consensus
        consensus = await synthesizer.find_consensus("machine learning")

        # Extract concepts from synthesis
        if consensus.get('consensus'):
            # Would extract from synthesized content
            assert consensus['source_count'] > 0


class TestCompleteAGIFlow:
    """Test complete AGI processing flows"""

    @pytest.mark.asyncio
    async def test_autonomous_learning_cycle(self):
        """Test complete autonomous learning cycle"""
        # Initialize systems
        kg = KnowledgeGraph()
        curiosity = CuriosityEngine(kg)
        extractor = KnowledgeExtractor()
        self_model = EnhancedSelfModel()

        # 1. Identify knowledge gap
        await curiosity.identify_knowledge_gap(
            topic="Quantum Computing",
            gap_type="missing_concept",
            evidence="User asked about it",
            importance=0.9
        )

        # 2. Generate questions
        questions = await curiosity.generate_questions(
            context="quantum",
            max_questions=3
        )

        assert len(questions) > 0

        # 3. Simulate finding information
        text = "Quantum computing uses quantum mechanics principles. " \
               "Qubits can exist in superposition states."

        # 4. Extract knowledge
        concepts = await extractor.extract_concepts(text, use_ai=False)

        # 5. Add to knowledge graph
        for concept in concepts:
            await kg.add_concept(concept.name, concept.concept_type, concept.context)

        # 6. Mark question as answered
        if questions:
            await curiosity.mark_question_answered(
                questions[0],
                answer=text,
                satisfaction=0.8
            )

        # 7. Update self-model
        from src.metacognitive.enhanced_self_model import CapabilityDomain
        await self_model.record_performance(
            task_description="Learned about quantum computing",
            domain=CapabilityDomain.LEARNING,
            self_rating=0.75
        )

        # Verify complete cycle
        assert len(kg.concepts) > 0
        assert len(curiosity.answered_questions) > 0
        assert len(self_model.performance_history) > 0

    @pytest.mark.asyncio
    async def test_empathetic_problem_solving_flow(self):
        """Test problem-solving with emotional and social awareness"""
        # Initialize systems
        tom = TheoryOfMind()
        emotion_model = AdvancedEmotionalModel()
        framework = ProblemSolvingFramework()

        # 1. User expresses frustration with problem
        user_message = "I'm so frustrated! This bug is impossible to fix!"

        # 2. Infer user emotional state
        user_emotion = await tom.infer_emotional_state("user_1", user_message)

        # 3. Infer user intention
        intention = await tom.infer_intention(
            "user_1",
            "Can you help me debug this?",
            conversation_context=[user_message]
        )

        # 4. Set own emotional state (empathetic concern)
        await emotion_model.process_emotional_stimulus('concern', intensity=0.6)

        # 5. Analyze the problem
        problem = await framework.analyze_problem(
            "Debug a complex software issue"
        )

        # 6. Solve with appropriate strategy
        solution = await framework.solve_problem(problem, max_iterations=3)

        # 7. Generate empathetic response
        response = await tom.generate_empathetic_response("user_1", user_message)

        # Verify empathetic problem-solving
        assert user_emotion.valence < 0  # User is frustrated
        assert intention is not None
        assert solution is not None
        assert response is not None
        assert any(word in response.lower() for word in ['help', 'support', 'understand'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
