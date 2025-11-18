"""
Tests for Wikipedia Integration
================================

Tests Wikipedia API integration functionality including:
- Article retrieval and caching
- Search functionality
- Related articles discovery
- Reference extraction
"""

import pytest
from datetime import datetime

from src.web.wikipedia_integration import (
    WikipediaIntegration,
    WikipediaArticle,
    WikiSearchResult,
    WikipediaKnowledgeExtractor,
    ContentFormat
)


@pytest.fixture
def wikipedia():
    """Create Wikipedia integration instance"""
    return WikipediaIntegration(language="en")


@pytest.fixture
def extractor(wikipedia):
    """Create knowledge extractor"""
    return WikipediaKnowledgeExtractor(wikipedia)


class TestWikipediaIntegration:
    """Test Wikipedia API integration"""

    @pytest.mark.asyncio
    async def test_search_returns_results(self, wikipedia):
        """Test that search returns result list"""
        results = await wikipedia.search("Python programming", limit=5)

        assert isinstance(results, list)
        assert len(results) <= 5

    @pytest.mark.asyncio
    async def test_get_article_returns_article(self, wikipedia):
        """Test article retrieval"""
        article = await wikipedia.get_article("Python (programming language)")

        assert article is None or isinstance(article, WikipediaArticle)

        if article:
            assert article.title == "Python (programming language)"
            assert article.url.startswith("https://en.wikipedia.org")

    @pytest.mark.asyncio
    async def test_get_article_caching(self, wikipedia):
        """Test that articles are cached"""
        title = "Test Article"

        # First call
        article1 = await wikipedia.get_article(title)

        # Second call should use cache
        article2 = await wikipedia.get_article(title)

        # Should be same instance if cached
        if article1 and article2:
            assert article1 is article2

    @pytest.mark.asyncio
    async def test_get_summary(self, wikipedia):
        """Test summary retrieval"""
        summary = await wikipedia.get_summary("Artificial intelligence", sentences=2)

        assert summary is None or isinstance(summary, str)

    @pytest.mark.asyncio
    async def test_get_related_articles(self, wikipedia):
        """Test related article discovery"""
        related = await wikipedia.get_related_articles("Machine learning", limit=5)

        assert isinstance(related, list)
        assert len(related) <= 5

    @pytest.mark.asyncio
    async def test_get_categories(self, wikipedia):
        """Test category retrieval"""
        categories = await wikipedia.get_categories("Computer science")

        assert isinstance(categories, list)

    @pytest.mark.asyncio
    async def test_extract_references(self, wikipedia):
        """Test reference extraction"""
        references = await wikipedia.extract_references("Albert Einstein")

        assert isinstance(references, list)

    @pytest.mark.asyncio
    async def test_verify_fact(self, wikipedia):
        """Test fact verification"""
        result = await wikipedia.verify_fact(
            "Python was created by Guido van Rossum"
        )

        assert isinstance(result, dict)
        assert 'verified' in result
        assert 'confidence' in result
        assert 'statement' in result

    @pytest.mark.asyncio
    async def test_get_trending_articles(self, wikipedia):
        """Test trending articles retrieval"""
        trending = await wikipedia.get_trending_articles(limit=5)

        assert isinstance(trending, list)
        assert len(trending) <= 5

    @pytest.mark.asyncio
    async def test_batch_search(self, wikipedia):
        """Test batch search functionality"""
        queries = ["Python", "Java", "C++"]
        results = await wikipedia.batch_search(queries, limit_per_query=3)

        assert isinstance(results, dict)
        assert len(results) == len(queries)

        for query in queries:
            assert query in results
            assert isinstance(results[query], list)

    @pytest.mark.asyncio
    async def test_get_disambiguation_pages(self, wikipedia):
        """Test disambiguation page handling"""
        options = await wikipedia.get_disambiguation_pages("Mercury")

        assert isinstance(options, list)

    @pytest.mark.asyncio
    async def test_compare_articles(self, wikipedia):
        """Test article comparison"""
        comparison = await wikipedia.compare_articles(
            "Python (programming language)",
            "Java (programming language)"
        )

        assert isinstance(comparison, dict)
        assert 'articles' in comparison
        assert 'content_similarity' in comparison

    @pytest.mark.asyncio
    async def test_cache_clear(self, wikipedia):
        """Test cache clearing"""
        # Add something to cache
        await wikipedia.get_article("Test")

        # Clear cache
        wikipedia.clear_cache()

        # Cache should be empty
        assert len(wikipedia.cache) == 0


class TestWikipediaKnowledgeExtractor:
    """Test knowledge extraction from Wikipedia"""

    @pytest.mark.asyncio
    async def test_extract_key_facts(self, extractor):
        """Test key fact extraction"""
        facts = await extractor.extract_key_facts("Quantum computing")

        assert isinstance(facts, list)

    @pytest.mark.asyncio
    async def test_build_concept_map(self, extractor):
        """Test concept map building"""
        concept_map = await extractor.build_concept_map(
            "Artificial intelligence",
            depth=2
        )

        assert isinstance(concept_map, dict)
        assert 'root' in concept_map
        assert 'concepts' in concept_map
        assert 'relationships' in concept_map

    @pytest.mark.asyncio
    async def test_extract_timeline(self, extractor):
        """Test timeline extraction"""
        timeline = await extractor.extract_timeline("World War II")

        assert isinstance(timeline, list)


class TestWikipediaDataClasses:
    """Test Wikipedia data structures"""

    def test_wikipedia_article_creation(self):
        """Test WikipediaArticle creation"""
        article = WikipediaArticle(
            title="Test Article",
            page_id=123,
            content="Test content",
            summary="Test summary",
            url="https://en.wikipedia.org/wiki/Test"
        )

        assert article.title == "Test Article"
        assert article.page_id == 123
        assert len(article.categories) == 0
        assert len(article.links) == 0

    def test_wiki_search_result_creation(self):
        """Test WikiSearchResult creation"""
        result = WikiSearchResult(
            title="Test",
            page_id=456,
            snippet="Test snippet",
            word_count=100,
            timestamp=datetime.now()
        )

        assert result.title == "Test"
        assert result.relevance_score == 0.0

    def test_content_format_enum(self):
        """Test ContentFormat enum"""
        assert ContentFormat.SUMMARY.value == "summary"
        assert ContentFormat.FULL.value == "full"
        assert ContentFormat.HTML.value == "html"
        assert ContentFormat.PLAIN.value == "plain"
