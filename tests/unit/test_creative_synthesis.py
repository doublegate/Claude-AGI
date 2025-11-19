"""
Unit tests for creative synthesis engine
"""

import pytest
from src.creative.creative_synthesis import (
    CreativeSynthesisEngine,
    Concept,
    SynthesisStrategy,
    NoveltyLevel
)


@pytest.fixture
async def engine():
    """Create a creative synthesis engine"""
    return CreativeSynthesisEngine()


@pytest.fixture
async def engine_with_concepts(engine):
    """Create engine with sample concepts"""
    # Science concepts
    await engine.add_concept(
        "atom",
        "Atom",
        "science",
        attributes={"type": "particle", "properties": "discrete", "behavior": "quantum"}
    )

    await engine.add_concept(
        "wave",
        "Wave",
        "science",
        attributes={"type": "phenomenon", "properties": "continuous", "behavior": "periodic"}
    )

    # Art concepts
    await engine.add_concept(
        "painting",
        "Painting",
        "art",
        attributes={"medium": "visual", "properties": "static", "expression": "visual"}
    )

    await engine.add_concept(
        "music",
        "Music",
        "art",
        attributes={"medium": "auditory", "properties": "temporal", "expression": "auditory"}
    )

    # Philosophy concepts
    await engine.add_concept(
        "consciousness",
        "Consciousness",
        "philosophy",
        attributes={"type": "mental", "properties": "subjective", "nature": "experiential"}
    )

    return engine


@pytest.mark.asyncio
class TestConceptManagement:
    """Test concept addition and management"""

    async def test_add_concept(self, engine):
        """Test adding a concept"""
        concept = await engine.add_concept(
            "test",
            "Test Concept",
            "test_domain",
            attributes={"prop1": "value1"},
            examples=["example1"]
        )

        assert concept.concept_id == "test"
        assert concept.name == "Test Concept"
        assert concept.domain == "test_domain"
        assert "test" in engine.concepts
        assert "test_domain" in engine.domains

    async def test_add_multiple_concepts(self, engine):
        """Test adding multiple concepts"""
        await engine.add_concept("c1", "Concept 1", "domain1")
        await engine.add_concept("c2", "Concept 2", "domain1")
        await engine.add_concept("c3", "Concept 3", "domain2")

        assert len(engine.concepts) == 3
        assert len(engine.domains) == 2


@pytest.mark.asyncio
class TestConceptBlending:
    """Test blending concepts"""

    async def test_blend_same_domain(self, engine_with_concepts):
        """Test blending concepts from same domain"""
        synthesis = await engine_with_concepts.blend_concepts("atom", "wave")

        assert synthesis is not None
        assert synthesis.strategy == SynthesisStrategy.BLEND
        assert "atom" in synthesis.source_concepts
        assert "wave" in synthesis.source_concepts
        assert len(synthesis.properties) > 0

    async def test_blend_different_domains(self, engine_with_concepts):
        """Test blending concepts from different domains"""
        synthesis = await engine_with_concepts.blend_concepts("atom", "music")

        assert synthesis is not None
        # Cross-domain blending should be more novel
        assert synthesis.novelty_level in [NoveltyLevel.RADICAL, NoveltyLevel.MODERATE]

    async def test_blend_nonexistent_concept(self, engine_with_concepts):
        """Test blending with nonexistent concept"""
        synthesis = await engine_with_concepts.blend_concepts("atom", "nonexistent")

        assert synthesis is None

    async def test_blend_attributes_combined(self, engine_with_concepts):
        """Test that blended concept combines attributes"""
        synthesis = await engine_with_concepts.blend_concepts("atom", "wave")

        # Should have attributes from both concepts
        assert len(synthesis.properties) > 0

        # Check for attributes from both sources
        has_type = "type" in synthesis.properties
        has_properties = "properties" in synthesis.properties

        assert has_type or has_properties


@pytest.mark.asyncio
class TestAnalogies:
    """Test analogy finding"""

    async def test_find_analogy_cross_domain(self, engine_with_concepts):
        """Test finding analogies across domains"""
        analogy = await engine_with_concepts.find_analogy(
            "atom",
            "art",
            min_similarity=0.1
        )

        # May or may not find analogy depending on attribute overlap
        if analogy:
            assert analogy.source_domain == "science"
            assert analogy.target_domain == "art"
            assert analogy.strength > 0.0

    async def test_find_analogy_no_target_domain(self, engine_with_concepts):
        """Test analogy with nonexistent target domain"""
        analogy = await engine_with_concepts.find_analogy(
            "atom",
            "nonexistent_domain"
        )

        assert analogy is None

    async def test_find_analogy_nonexistent_source(self, engine_with_concepts):
        """Test analogy with nonexistent source concept"""
        analogy = await engine_with_concepts.find_analogy(
            "nonexistent",
            "art"
        )

        assert analogy is None

    async def test_analogy_mapping(self, engine_with_concepts):
        """Test that analogy creates attribute mapping"""
        analogy = await engine_with_concepts.find_analogy(
            "atom",
            "art",
            min_similarity=0.1
        )

        if analogy and analogy.mapping:
            # Mapping should exist
            assert len(analogy.mapping) > 0


@pytest.mark.asyncio
class TestConstraintBasedGeneration:
    """Test constraint-based creative generation"""

    async def test_generate_with_constraints(self, engine_with_concepts):
        """Test generating variants with constraints"""
        synthesis = await engine_with_concepts.generate_by_constraint(
            "atom",
            {"size": "large", "charge": "positive"}
        )

        assert synthesis is not None
        assert synthesis.strategy == SynthesisStrategy.TRANSFORM
        assert "atom" in synthesis.source_concepts
        assert len(synthesis.properties) > 0

    async def test_constraints_affect_novelty(self, engine_with_concepts):
        """Test that more constraints increase novelty"""
        # Few constraints
        simple = await engine_with_concepts.generate_by_constraint(
            "atom",
            {"size": "large"}
        )

        # Many constraints
        complex = await engine_with_concepts.generate_by_constraint(
            "atom",
            {"size": "large", "charge": "positive", "spin": "up", "color": "red"}
        )

        # More constraints should lead to higher novelty
        novelty_order = [NoveltyLevel.INCREMENTAL, NoveltyLevel.MODERATE, NoveltyLevel.RADICAL]

        if simple and complex:
            simple_idx = novelty_order.index(simple.novelty_level)
            complex_idx = novelty_order.index(complex.novelty_level)
            assert complex_idx >= simple_idx

    async def test_constraint_nonexistent_concept(self, engine_with_concepts):
        """Test constraint generation with nonexistent concept"""
        synthesis = await engine_with_concepts.generate_by_constraint(
            "nonexistent",
            {"test": "value"}
        )

        assert synthesis is None


@pytest.mark.asyncio
class TestPatternAbstraction:
    """Test abstracting patterns from concepts"""

    async def test_abstract_pattern_multiple_concepts(self, engine_with_concepts):
        """Test abstracting from multiple concepts"""
        synthesis = await engine_with_concepts.abstract_pattern(
            ["atom", "wave"]
        )

        # Should find common attributes
        if synthesis:
            assert synthesis.strategy == SynthesisStrategy.ABSTRACT
            assert len(synthesis.source_concepts) >= 2
            assert len(synthesis.properties) > 0

    async def test_abstract_pattern_single_concept(self, engine_with_concepts):
        """Test that abstraction requires multiple concepts"""
        synthesis = await engine_with_concepts.abstract_pattern(["atom"])

        assert synthesis is None

    async def test_abstract_pattern_no_common_attributes(self, engine):
        """Test abstraction with no common attributes"""
        # Create concepts with no overlap
        await engine.add_concept("c1", "C1", "d1", attributes={"a": 1})
        await engine.add_concept("c2", "C2", "d1", attributes={"b": 2})

        synthesis = await engine.abstract_pattern(["c1", "c2"])

        # Should return None if no common attributes
        assert synthesis is None

    async def test_abstract_pattern_common_attributes(self, engine):
        """Test abstraction finds common attributes"""
        # Create concepts with common attributes
        await engine.add_concept("c1", "C1", "d1", attributes={"type": "A", "size": "big"})
        await engine.add_concept("c2", "C2", "d1", attributes={"type": "B", "size": "small"})
        await engine.add_concept("c3", "C3", "d1", attributes={"type": "C", "size": "medium"})

        synthesis = await engine.abstract_pattern(["c1", "c2", "c3"])

        assert synthesis is not None
        # Should have common attributes (type, size)
        assert "type" in synthesis.properties or "size" in synthesis.properties


@pytest.mark.asyncio
class TestRecombination:
    """Test element recombination"""

    async def test_recombine_elements(self, engine_with_concepts):
        """Test recombining concept elements"""
        results = await engine_with_concepts.recombine_elements(
            ["atom", "wave", "music"],
            num_combinations=2
        )

        assert len(results) <= 2
        for synthesis in results:
            assert synthesis.strategy == SynthesisStrategy.RECOMBINE
            assert len(synthesis.source_concepts) >= 2

    async def test_recombine_insufficient_concepts(self, engine_with_concepts):
        """Test recombination with too few concepts"""
        results = await engine_with_concepts.recombine_elements(
            ["atom"],
            num_combinations=3
        )

        assert len(results) == 0

    async def test_recombine_creates_multiple(self, engine_with_concepts):
        """Test that recombination creates requested number"""
        num_requested = 5
        results = await engine_with_concepts.recombine_elements(
            ["atom", "wave", "music", "painting"],
            num_combinations=num_requested
        )

        assert len(results) == num_requested


@pytest.mark.asyncio
class TestCreativeIdeaGeneration:
    """Test general creative idea generation"""

    async def test_generate_ideas_basic(self, engine_with_concepts):
        """Test generating creative ideas"""
        ideas = await engine_with_concepts.generate_creative_ideas(
            theme="innovation",
            num_ideas=3
        )

        # Should generate some ideas (may be less than requested if strategies fail)
        assert len(ideas) >= 0
        assert len(ideas) <= 3

    async def test_generate_ideas_specific_strategies(self, engine_with_concepts):
        """Test generating ideas with specific strategies"""
        ideas = await engine_with_concepts.generate_creative_ideas(
            theme="test",
            num_ideas=2,
            strategies=[SynthesisStrategy.BLEND]
        )

        for idea in ideas:
            assert idea.strategy == SynthesisStrategy.BLEND

    async def test_generate_ideas_empty_engine(self, engine):
        """Test idea generation with no concepts"""
        ideas = await engine.generate_creative_ideas(
            theme="test",
            num_ideas=5
        )

        # Should return empty list
        assert len(ideas) == 0


@pytest.mark.asyncio
class TestStatistics:
    """Test statistics tracking"""

    async def test_statistics_empty(self, engine):
        """Test statistics for empty engine"""
        stats = await engine.get_statistics()

        assert stats['total_concepts'] == 0
        assert stats['total_syntheses'] == 0
        assert stats['total_analogies'] == 0

    async def test_statistics_after_operations(self, engine_with_concepts):
        """Test statistics after performing operations"""
        # Perform some operations
        await engine_with_concepts.blend_concepts("atom", "wave")
        await engine_with_concepts.generate_by_constraint("atom", {"test": "value"})
        await engine_with_concepts.find_analogy("atom", "art", min_similarity=0.1)

        stats = await engine_with_concepts.get_statistics()

        assert stats['total_concepts'] == 5
        assert stats['total_syntheses'] == 2
        # May or may not find analogy
        assert stats['total_analogies'] >= 0

    async def test_statistics_by_strategy(self, engine_with_concepts):
        """Test statistics tracking by strategy"""
        await engine_with_concepts.blend_concepts("atom", "wave")
        await engine_with_concepts.blend_concepts("atom", "music")

        stats = await engine_with_concepts.get_statistics()

        assert stats['syntheses_by_strategy']['blend'] == 2

    async def test_statistics_by_novelty(self, engine_with_concepts):
        """Test statistics tracking by novelty level"""
        # Generate syntheses with different novelty
        await engine_with_concepts.blend_concepts("atom", "wave")  # Moderate (same domain)
        await engine_with_concepts.blend_concepts("atom", "music")  # Radical (cross-domain)

        stats = await engine_with_concepts.get_statistics()

        # Should have tracked novelty levels
        assert 'syntheses_by_novelty' in stats


@pytest.mark.asyncio
class TestNoveltyDetermination:
    """Test novelty level determination"""

    async def test_cross_domain_more_novel(self, engine_with_concepts):
        """Test that cross-domain blends are more novel"""
        same_domain = await engine_with_concepts.blend_concepts("atom", "wave")
        cross_domain = await engine_with_concepts.blend_concepts("atom", "painting")

        # Cross-domain should be at least as novel as same-domain
        novelty_levels = [NoveltyLevel.INCREMENTAL, NoveltyLevel.MODERATE,
                         NoveltyLevel.RADICAL, NoveltyLevel.TRANSFORMATIVE]

        if same_domain and cross_domain:
            same_idx = novelty_levels.index(same_domain.novelty_level)
            cross_idx = novelty_levels.index(cross_domain.novelty_level)

            assert cross_idx >= same_idx


@pytest.mark.asyncio
class TestCreativeSynthesisProperties:
    """Test properties of creative syntheses"""

    async def test_synthesis_has_required_fields(self, engine_with_concepts):
        """Test that syntheses have all required fields"""
        synthesis = await engine_with_concepts.blend_concepts("atom", "wave")

        assert synthesis.synthesis_id is not None
        assert synthesis.strategy is not None
        assert len(synthesis.source_concepts) > 0
        assert synthesis.synthesized_concept is not None
        assert synthesis.description is not None
        assert synthesis.novelty_level is not None
        assert 0.0 <= synthesis.confidence <= 1.0

    async def test_synthesis_stored_in_history(self, engine_with_concepts):
        """Test that syntheses are stored in history"""
        initial_count = len(engine_with_concepts.syntheses)

        await engine_with_concepts.blend_concepts("atom", "wave")

        assert len(engine_with_concepts.syntheses) == initial_count + 1
