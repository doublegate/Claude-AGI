"""
Tests for Unified Knowledge API
================================

Tests unified API that coordinates Wikipedia and Wikidata including:
- Query routing and type detection
- Cross-source knowledge integration
- Multi-source answer synthesis
"""

import pytest
from datetime import datetime

from src.web.unified_knowledge_api import (
    UnifiedKnowledgeAPI,
    UnifiedKnowledgeResult,
    QueryType
)


@pytest.fixture
def api():
    """Create unified knowledge API instance"""
    return UnifiedKnowledgeAPI(language="en")


class TestUnifiedKnowledgeAPI:
    """Test unified knowledge API"""

    @pytest.mark.asyncio
    async def test_query_factual(self, api):
        """Test factual query handling"""
        result = await api.query(
            "What is Python?",
            query_type=QueryType.FACTUAL
        )

        assert isinstance(result, UnifiedKnowledgeResult)
        assert result.query == "What is Python?"
        assert result.query_type == QueryType.FACTUAL
        assert isinstance(result.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_query_exploratory(self, api):
        """Test exploratory query handling"""
        result = await api.query(
            "Explain machine learning",
            query_type=QueryType.EXPLORATORY
        )

        assert isinstance(result, UnifiedKnowledgeResult)
        assert result.query_type == QueryType.EXPLORATORY

    @pytest.mark.asyncio
    async def test_query_verification(self, api):
        """Test verification query handling"""
        result = await api.query(
            "Verify that Python was created by Guido van Rossum",
            query_type=QueryType.VERIFICATION
        )

        assert isinstance(result, UnifiedKnowledgeResult)
        assert result.query_type == QueryType.VERIFICATION
        assert 'verification' in result.structured_data or result.summary

    @pytest.mark.asyncio
    async def test_query_relationship(self, api):
        """Test relationship query handling"""
        result = await api.query(
            "relationship between Python and Guido van Rossum",
            query_type=QueryType.RELATIONSHIP
        )

        assert isinstance(result, UnifiedKnowledgeResult)
        assert result.query_type == QueryType.RELATIONSHIP

    @pytest.mark.asyncio
    async def test_query_comparison(self, api):
        """Test comparison query handling"""
        result = await api.query(
            "Compare Python and Java",
            query_type=QueryType.COMPARISON
        )

        assert isinstance(result, UnifiedKnowledgeResult)
        assert result.query_type == QueryType.COMPARISON

    @pytest.mark.asyncio
    async def test_query_temporal(self, api):
        """Test temporal query handling"""
        result = await api.query(
            "Timeline of Python programming language",
            query_type=QueryType.TEMPORAL
        )

        assert isinstance(result, UnifiedKnowledgeResult)
        assert result.query_type == QueryType.TEMPORAL

    @pytest.mark.asyncio
    async def test_query_auto_detect_type(self, api):
        """Test automatic query type detection"""
        # Test verification detection
        result = await api.query("Verify this fact")
        assert result.query_type == QueryType.VERIFICATION

        # Test comparison detection
        result = await api.query("Compare X versus Y")
        assert result.query_type == QueryType.COMPARISON

        # Test temporal detection
        result = await api.query("When did this happen?")
        assert result.query_type == QueryType.TEMPORAL

        # Test relationship detection
        result = await api.query("What is the connection between X and Y?")
        assert result.query_type == QueryType.RELATIONSHIP

        # Test exploratory detection
        result = await api.query("What is quantum computing?")
        assert result.query_type == QueryType.EXPLORATORY

    @pytest.mark.asyncio
    async def test_enrich_with_knowledge(self, api):
        """Test text enrichment with knowledge"""
        enrichment = await api.enrich_with_knowledge(
            "Python is a programming language created by Guido van Rossum.",
            entity_linking=True
        )

        assert isinstance(enrichment, dict)
        assert 'original_text' in enrichment
        assert 'entities' in enrichment
        assert 'linked_knowledge' in enrichment
        assert 'confidence' in enrichment

    @pytest.mark.asyncio
    async def test_get_multi_source_answer(self, api):
        """Test multi-source answer synthesis"""
        answer = await api.get_multi_source_answer(
            "Who created Python?",
            max_sources=5
        )

        assert isinstance(answer, dict)
        assert 'question' in answer
        assert 'sources_consulted' in answer
        assert 'consensus_answer' in answer
        assert 'supporting_facts' in answer
        assert 'confidence' in answer

    @pytest.mark.asyncio
    async def test_clear_all_caches(self, api):
        """Test clearing all caches"""
        # Perform some queries to populate caches
        await api.query("Test query")

        # Clear caches
        api.clear_all_caches()

        # Both caches should be empty
        assert len(api.wikipedia.cache) == 0
        assert len(api.wikidata.entity_cache) == 0

    @pytest.mark.asyncio
    async def test_query_with_structured_data(self, api):
        """Test query including structured data"""
        result = await api.query(
            "What is Python?",
            query_type=QueryType.FACTUAL,
            include_structured=True
        )

        assert isinstance(result.structured_data, dict)

    @pytest.mark.asyncio
    async def test_query_with_related_topics(self, api):
        """Test query including related topics"""
        result = await api.query(
            "Machine learning",
            query_type=QueryType.EXPLORATORY,
            include_related=True
        )

        assert isinstance(result.related_topics, list)

    @pytest.mark.asyncio
    async def test_query_confidence_scoring(self, api):
        """Test that queries return confidence scores"""
        result = await api.query("Test query")

        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_query_source_tracking(self, api):
        """Test that queries track sources"""
        result = await api.query(
            "Python programming",
            query_type=QueryType.FACTUAL
        )

        assert isinstance(result.sources, list)


class TestUnifiedKnowledgeResult:
    """Test unified knowledge result data structure"""

    def test_result_creation(self):
        """Test creating result"""
        result = UnifiedKnowledgeResult(
            query="Test query",
            query_type=QueryType.FACTUAL
        )

        assert result.query == "Test query"
        assert result.query_type == QueryType.FACTUAL
        assert result.wikipedia_article is None
        assert result.wikidata_entity is None
        assert len(result.key_facts) == 0
        assert len(result.related_topics) == 0
        assert result.confidence == 0.0

    def test_result_with_data(self):
        """Test result with populated data"""
        result = UnifiedKnowledgeResult(
            query="Test",
            query_type=QueryType.FACTUAL,
            summary="Test summary",
            key_facts=["Fact 1", "Fact 2"],
            confidence=0.85
        )

        assert result.summary == "Test summary"
        assert len(result.key_facts) == 2
        assert result.confidence == 0.85


class TestQueryType:
    """Test query type enum"""

    def test_query_type_values(self):
        """Test query type enum values"""
        assert QueryType.FACTUAL.value == "factual"
        assert QueryType.EXPLORATORY.value == "exploratory"
        assert QueryType.VERIFICATION.value == "verification"
        assert QueryType.RELATIONSHIP.value == "relationship"
        assert QueryType.COMPARISON.value == "comparison"
        assert QueryType.TEMPORAL.value == "temporal"

    def test_all_query_types_exist(self):
        """Test that all expected query types exist"""
        expected_types = [
            'FACTUAL', 'EXPLORATORY', 'VERIFICATION',
            'RELATIONSHIP', 'COMPARISON', 'TEMPORAL'
        ]

        for type_name in expected_types:
            assert hasattr(QueryType, type_name)
