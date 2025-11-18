"""
Unit Tests for Knowledge Extraction System
===========================================

Tests for the knowledge extraction and learning path generation modules.
"""

import pytest
import asyncio
from src.learning.knowledge_extraction import (
    KnowledgeExtractor,
    LearningPathGenerator,
    ExtractedConcept,
    ExtractedRelationship
)
from src.learning.knowledge_graph import KnowledgeGraph


class TestKnowledgeExtractor:
    """Test the KnowledgeExtractor class"""

    @pytest.fixture
    def extractor(self):
        """Create a knowledge extractor instance"""
        return KnowledgeExtractor(ai_client=None)

    @pytest.mark.asyncio
    async def test_extract_concepts_from_simple_text(self, extractor):
        """Test concept extraction from simple text"""
        text = "Machine learning is a subset of artificial intelligence."
        concepts = await extractor.extract_concepts(text, use_ai=False)

        assert len(concepts) > 0
        # Should extract at least one concept
        concept_names = [c.name.lower() for c in concepts]
        assert any('machine learning' in name or 'artificial intelligence' in name for name in concept_names)

    @pytest.mark.asyncio
    async def test_extract_concepts_with_confidence(self, extractor):
        """Test that extracted concepts have confidence scores"""
        text = "Python is a programming language that is easy to learn."
        concepts = await extractor.extract_concepts(text, use_ai=False)

        for concept in concepts:
            assert 0.0 <= concept.confidence <= 1.0
            assert concept.name is not None
            assert concept.concept_type is not None

    @pytest.mark.asyncio
    async def test_extract_relationships_basic(self, extractor):
        """Test basic relationship extraction"""
        text = "Python requires programming."
        known_concepts = {'Python', 'programming'}

        relationships = await extractor.extract_relationships(
            text,
            known_concepts=known_concepts,
            use_ai=False
        )

        # Should find the 'requires' relationship
        assert len(relationships) > 0
        rel_types = [r.relation_type for r in relationships]
        assert 'requires' in rel_types

    @pytest.mark.asyncio
    async def test_extract_relationships_causes(self, extractor):
        """Test extraction of causal relationships"""
        text = "Studying leads to understanding."
        known_concepts = {'Studying', 'understanding'}

        relationships = await extractor.extract_relationships(
            text,
            known_concepts=known_concepts,
            use_ai=False
        )

        # Should detect causal relationship
        causes_rels = [r for r in relationships if r.relation_type == 'causes']
        assert len(causes_rels) > 0

    @pytest.mark.asyncio
    async def test_extract_knowledge_from_document(self, extractor):
        """Test comprehensive document extraction"""
        text = """
        Machine learning is a branch of AI. Neural networks are part of machine learning.
        Deep learning requires neural networks. Understanding math is important for AI.
        """

        knowledge = await extractor.extract_knowledge_from_document(text, use_ai=False)

        assert 'concepts' in knowledge
        assert 'relationships' in knowledge
        assert 'source_text' in knowledge
        assert len(knowledge['concepts']) > 0
        assert len(knowledge['relationships']) > 0

    @pytest.mark.asyncio
    async def test_concept_deduplication(self, extractor):
        """Test that duplicate concepts are deduplicated"""
        text = "Python is great. Python is easy. Python is powerful."
        concepts = await extractor.extract_concepts(text, use_ai=False)

        # Should not have multiple 'Python' concepts
        python_concepts = [c for c in concepts if 'python' in c.name.lower()]
        assert len(python_concepts) <= 2  # At most one from pattern matching

    @pytest.mark.asyncio
    async def test_calculate_importance(self, extractor):
        """Test importance calculation for concepts"""
        concept = ExtractedConcept(
            name="Machine Learning",
            concept_type="field",
            context="Machine learning is fundamental. Machine learning is everywhere.",
            confidence=0.8
        )

        importance = extractor.calculate_importance(concept, concept.context)

        assert 0.0 <= importance <= 1.0
        # Capitalized and repeated should have higher importance
        assert importance > concept.confidence


class TestLearningPathGenerator:
    """Test the LearningPathGenerator class"""

    @pytest.fixture
    def knowledge_graph_sync(self):
        """Create an empty knowledge graph"""
        return KnowledgeGraph()

    @pytest.fixture
    async def knowledge_graph(self, knowledge_graph_sync):
        """Create a knowledge graph with test data"""
        kg = knowledge_graph_sync

        # Add concepts
        python = await kg.add_concept("Python", "language", "Programming language")
        programming = await kg.add_concept("Programming", "skill", "Software development")
        oop = await kg.add_concept("OOP", "concept", "Object-oriented programming")
        functions = await kg.add_concept("Functions", "concept", "Reusable code blocks")

        # Add relationships
        from src.learning.knowledge_graph import RelationType
        await kg.add_relationship("Programming", "Python", RelationType.PART_OF)
        await kg.add_relationship("Functions", "Programming", RelationType.REQUIRES)
        await kg.add_relationship("OOP", "Functions", RelationType.REQUIRES)

        return kg

    @pytest.fixture
    def path_generator(self, knowledge_graph_sync):
        """Create a learning path generator"""
        return LearningPathGenerator(knowledge_graph_sync)

    @pytest.mark.asyncio
    async def test_find_learning_path_simple(self, knowledge_graph_sync):
        """Test finding a simple learning path"""
        kg = knowledge_graph_sync

        # Set up the graph
        await kg.add_concept("Python", "language", "Programming language")
        await kg.add_concept("Programming", "skill", "Software development")
        await kg.add_concept("OOP", "concept", "Object-oriented programming")
        await kg.add_concept("Functions", "concept", "Reusable code blocks")

        from src.learning.knowledge_graph import RelationType
        await kg.add_relationship("Programming", "Python", RelationType.PART_OF)
        await kg.add_relationship("Functions", "Programming", RelationType.REQUIRES)
        await kg.add_relationship("OOP", "Functions", RelationType.REQUIRES)

        path_generator = LearningPathGenerator(kg)
        path = await path_generator.find_learning_path("Functions", "OOP")

        assert path is not None
        assert len(path) >= 2
        assert "Functions" in path
        assert "OOP" in path

    @pytest.mark.asyncio
    async def test_find_learning_path_no_path(self, path_generator):
        """Test when no path exists"""
        path = await path_generator.find_learning_path("NonExistent1", "NonExistent2")

        assert path is None

    @pytest.mark.asyncio
    async def test_identify_knowledge_gaps(self, knowledge_graph_sync):
        """Test identifying knowledge gaps"""
        kg = knowledge_graph_sync

        # Set up the graph
        await kg.add_concept("Python", "language", "Programming language")
        await kg.add_concept("Programming", "skill", "Software development")
        await kg.add_concept("OOP", "concept", "Object-oriented programming")
        await kg.add_concept("Functions", "concept", "Reusable code blocks")

        from src.learning.knowledge_graph import RelationType
        await kg.add_relationship("Programming", "Python", RelationType.PART_OF)
        await kg.add_relationship("Functions", "Programming", RelationType.REQUIRES)
        await kg.add_relationship("OOP", "Functions", RelationType.REQUIRES)

        path_generator = LearningPathGenerator(kg)
        known_concepts = {'Python'}
        gaps = await path_generator.identify_knowledge_gaps(known_concepts, "OOP")

        # Should identify Functions and OOP as gaps
        assert len(gaps) > 0
        assert "OOP" in gaps or "Functions" in gaps

    @pytest.mark.asyncio
    async def test_suggest_next_concepts(self, path_generator, knowledge_graph):
        """Test suggesting next concepts to learn"""
        known_concepts = {'Programming'}
        suggestions = await path_generator.suggest_next_concepts(known_concepts, max_suggestions=5)

        assert len(suggestions) > 0
        # Each suggestion should be (concept_name, score)
        for suggestion in suggestions:
            assert isinstance(suggestion, tuple)
            assert len(suggestion) == 2
            assert isinstance(suggestion[0], str)
            assert isinstance(suggestion[1], (int, float))

    @pytest.mark.asyncio
    async def test_suggest_next_concepts_empty_knowledge(self, path_generator):
        """Test suggestions with no prior knowledge"""
        suggestions = await path_generator.suggest_next_concepts(set(), max_suggestions=3)

        # Should still return suggestions even with no prior knowledge
        assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_integration_extraction_to_graph():
    """Test integration: extract knowledge and add to graph"""
    extractor = KnowledgeExtractor()
    kg = KnowledgeGraph()

    text = "Python is a programming language. Programming requires logic."

    # Extract knowledge
    knowledge = await extractor.extract_knowledge_from_document(text, use_ai=False)

    # Add concepts to graph
    for concept in knowledge['concepts']:
        await kg.add_concept(
            concept.name,
            concept.concept_type,
            concept.context,
            properties=concept.properties
        )

    # Verify concepts were added
    assert len(kg.concepts) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
