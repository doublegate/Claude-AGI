"""
Unit Tests for Web Content Processor
=====================================

Tests for web content extraction, processing, and synthesis.
"""

import pytest
from datetime import datetime
from src.web.content_processor import (
    WebContentProcessor,
    InformationSynthesizer,
    ProcessedContent,
    ContentType,
    ContentSummary
)


class TestWebContentProcessor:
    """Test the WebContentProcessor class"""

    @pytest.fixture
    def processor(self):
        """Create a web content processor"""
        return WebContentProcessor(ai_client=None)

    @pytest.fixture
    def sample_html(self):
        """Sample HTML content for testing"""
        return """
        <html>
        <head>
            <title>Machine Learning Guide</title>
            <meta name="author" content="AI Researcher">
            <meta property="article:published_time" content="2025-01-01">
        </head>
        <body>
            <article>
                <h1>Understanding Machine Learning</h1>
                <p>Machine learning is a subset of artificial intelligence.
                   It enables computers to learn from data without explicit programming.</p>
                <p>Key concepts include supervised learning, unsupervised learning,
                   and reinforcement learning.</p>
            </article>
            <script>console.log('test');</script>
        </body>
        </html>
        """

    @pytest.mark.asyncio
    async def test_process_url_basic(self, processor, sample_html):
        """Test basic URL processing"""
        content = await processor.process_url(
            url="https://example.com/article",
            html_content=sample_html,
            use_ai=False
        )

        assert content is not None
        assert content.title == "Machine Learning Guide"
        assert content.url == "https://example.com/article"
        assert "machine learning" in content.content.lower()

    @pytest.mark.asyncio
    async def test_clean_html_removes_scripts(self, processor):
        """Test that HTML cleaning removes scripts and styles"""
        html = """
        <html>
        <body>
            <p>Content here</p>
            <script>alert('bad');</script>
            <style>body { color: red; }</style>
            <p>More content</p>
        </body>
        </html>
        """

        clean_text = processor._clean_html(html)

        assert "Content here" in clean_text
        assert "More content" in clean_text
        assert "alert" not in clean_text
        assert "color: red" not in clean_text

    @pytest.mark.asyncio
    async def test_extract_title(self, processor, sample_html):
        """Test title extraction"""
        title = processor._extract_title(sample_html)

        assert title == "Machine Learning Guide"

    @pytest.mark.asyncio
    async def test_extract_title_with_og_tag(self, processor):
        """Test title extraction from Open Graph meta tag"""
        html = '<html><meta property="og:title" content="OG Title"></html>'

        title = processor._extract_title(html)

        assert title == "OG Title"

    @pytest.mark.asyncio
    async def test_extract_author(self, processor, sample_html):
        """Test author extraction"""
        author = processor._extract_author(sample_html)

        assert author == "AI Researcher"

    @pytest.mark.asyncio
    async def test_detect_content_type_article(self, processor):
        """Test content type detection for articles"""
        url = "https://blog.example.com/article-title"
        html = "<article>Content</article>"

        content_type = processor._detect_content_type(url, html)

        # Should detect as article or blog post
        assert content_type in [ContentType.ARTICLE, ContentType.BLOG_POST]

    @pytest.mark.asyncio
    async def test_detect_content_type_academic(self, processor):
        """Test content type detection for academic papers"""
        url = "https://arxiv.org/abs/1234.5678"
        html = "<html></html>"

        content_type = processor._detect_content_type(url, html)

        assert content_type == ContentType.ACADEMIC_PAPER

    @pytest.mark.asyncio
    async def test_detect_content_type_news(self, processor):
        """Test content type detection for news"""
        url = "https://www.bbc.com/news/article-123"
        html = "<html></html>"

        content_type = processor._detect_content_type(url, html)

        assert content_type == ContentType.NEWS

    @pytest.mark.asyncio
    async def test_detect_content_type_forum(self, processor):
        """Test content type detection for forums"""
        url = "https://stackoverflow.com/questions/123"
        html = "<html></html>"

        content_type = processor._detect_content_type(url, html)

        assert content_type == ContentType.FORUM_POST

    @pytest.mark.asyncio
    async def test_assess_credibility_high(self, processor):
        """Test credibility assessment for high-credibility sources"""
        score = await processor._assess_credibility("arxiv.org", ContentType.ACADEMIC_PAPER)

        assert score >= 0.8  # Should be high credibility

    @pytest.mark.asyncio
    async def test_assess_credibility_medium(self, processor):
        """Test credibility assessment for medium-credibility sources"""
        score = await processor._assess_credibility("medium.com", ContentType.BLOG_POST)

        assert 0.5 <= score < 0.9  # Should be medium credibility

    @pytest.mark.asyncio
    async def test_assess_credibility_edu_domain(self, processor):
        """Test credibility assessment for .edu domains"""
        score = await processor._assess_credibility("university.edu", ContentType.ARTICLE)

        assert score >= 0.8  # .edu should have high credibility

    @pytest.mark.asyncio
    async def test_extract_key_points(self, processor):
        """Test key point extraction"""
        text = """
        Machine learning is important for modern AI. Key findings show that
        deep learning demonstrates significant improvements. Research reveals
        that neural networks can learn complex patterns. This is notable for
        future developments.
        """

        key_points = processor._extract_key_points(text)

        assert len(key_points) > 0
        # Should extract sentences with key phrases
        assert any("important" in point.lower() or "key" in point.lower() for point in key_points)

    @pytest.mark.asyncio
    async def test_summarize_content(self, processor, sample_html):
        """Test content summarization"""
        content = await processor.process_url(
            "https://example.com/article",
            sample_html,
            use_ai=False
        )

        summary = await processor.summarize_content(content, use_ai=False)

        assert isinstance(summary, ContentSummary)
        assert len(summary.main_ideas) > 0
        # Related topics should be extracted
        assert isinstance(summary.related_topics, list)

    @pytest.mark.asyncio
    async def test_summarize_content_questions(self, processor):
        """Test that summary extracts questions"""
        html = """
        <html><body>
        <p>What is machine learning? How does it work?
           These are important questions.</p>
        </body></html>
        """

        content = await processor.process_url("https://example.com", html)
        summary = await processor.summarize_content(content)

        assert len(summary.questions_raised) > 0
        # Should have extracted questions
        assert any('?' in q for q in summary.questions_raised)

    @pytest.mark.asyncio
    async def test_extract_citations(self, processor, sample_html):
        """Test citation extraction"""
        content = await processor.process_url("https://example.com", sample_html)

        citations = await processor.extract_citations(content)

        # Should return a list (may be empty for this sample)
        assert isinstance(citations, list)

    @pytest.mark.asyncio
    async def test_extract_citations_with_urls(self, processor):
        """Test citation extraction with URLs"""
        html = """
        <html><body>
        <p>See https://example.com/ref1 for details.
           Also check https://example.com/ref2.</p>
        </body></html>
        """

        content = await processor.process_url("https://example.com", html)
        citations = await processor.extract_citations(content)

        assert len(citations) > 0
        # Should extract URLs
        assert any('https://' in citation for citation in citations)

    @pytest.mark.asyncio
    async def test_get_reading_time(self, processor):
        """Test reading time estimation"""
        content = ProcessedContent(
            url="https://example.com",
            title="Test",
            content=" ".join(["word"] * 400),  # 400 words
            content_type=ContentType.ARTICLE,
            source_domain="example.com"
        )

        reading_time = processor.get_reading_time(content)

        assert reading_time == 2  # 400 words / 200 wpm = 2 minutes

    @pytest.mark.asyncio
    async def test_cache_processed_content(self, processor, sample_html):
        """Test that processed content is cached"""
        url = "https://example.com/cached"

        # First processing
        content1 = await processor.process_url(url, sample_html)

        # Check cache
        assert url in processor.content_cache
        assert processor.content_cache[url] == content1


class TestInformationSynthesizer:
    """Test the InformationSynthesizer class"""

    @pytest.fixture
    def synthesizer(self):
        """Create an information synthesizer"""
        return InformationSynthesizer()

    @pytest.fixture
    def sample_contents(self):
        """Create sample processed contents"""
        return [
            ProcessedContent(
                url="https://source1.com",
                title="AI Overview",
                content="AI is transforming technology. Machine learning enables computers to learn.",
                content_type=ContentType.ARTICLE,
                source_domain="source1.com",
                credibility_score=0.9
            ),
            ProcessedContent(
                url="https://source2.com",
                title="Machine Learning",
                content="Machine learning is a key part of AI. It enables pattern recognition.",
                content_type=ContentType.ACADEMIC_PAPER,
                source_domain="source2.com",
                credibility_score=0.95
            ),
            ProcessedContent(
                url="https://source3.com",
                title="AI Applications",
                content="AI has many applications. Machine learning is widely used.",
                content_type=ContentType.BLOG_POST,
                source_domain="source3.com",
                credibility_score=0.7
            )
        ]

    @pytest.mark.asyncio
    async def test_add_source(self, synthesizer, sample_contents):
        """Test adding sources"""
        await synthesizer.add_source(sample_contents[0])

        assert len(synthesizer.processed_sources) == 1

    @pytest.mark.asyncio
    async def test_find_consensus_basic(self, synthesizer, sample_contents):
        """Test finding consensus across sources"""
        for content in sample_contents:
            await synthesizer.add_source(content)

        consensus = await synthesizer.find_consensus("machine learning")

        assert 'consensus' in consensus
        assert 'strength' in consensus
        assert 'source_count' in consensus
        assert consensus['source_count'] == 3  # All sources mention it

    @pytest.mark.asyncio
    async def test_find_consensus_high_credibility(self, synthesizer, sample_contents):
        """Test consensus with high-credibility sources"""
        for content in sample_contents:
            await synthesizer.add_source(content)

        consensus = await synthesizer.find_consensus("AI")

        # With 2/3 high-credibility sources, should have consensus
        assert consensus['consensus'] is True
        assert consensus['average_credibility'] > 0.8

    @pytest.mark.asyncio
    async def test_find_consensus_no_sources(self, synthesizer):
        """Test consensus when no sources found"""
        consensus = await synthesizer.find_consensus("nonexistent topic")

        assert consensus['consensus'] is False
        assert 'reason' in consensus

    @pytest.mark.asyncio
    async def test_generate_synthesis(self, synthesizer, sample_contents):
        """Test generating synthesis"""
        for content in sample_contents:
            await synthesizer.add_source(content)

        synthesis = await synthesizer.generate_synthesis("machine learning", max_sources=5)

        assert isinstance(synthesis, str)
        assert len(synthesis) > 0
        # Should mention number of sources
        assert "source" in synthesis.lower()

    @pytest.mark.asyncio
    async def test_identify_contradictions(self, synthesizer):
        """Test identifying contradictions"""
        contradictions = await synthesizer.identify_contradictions()

        # Should return a list (may be empty)
        assert isinstance(contradictions, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
