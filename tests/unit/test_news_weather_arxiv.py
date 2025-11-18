"""
Tests for News, Weather, and arXiv Integrations
================================================
"""

import pytest
from datetime import datetime, timedelta

from src.web.news_integration import (
    NewsIntegration,
    NewsArticle,
    NewsCategory,
    NewsSentiment
)
from src.web.weather_integration import (
    WeatherIntegration,
    WeatherData,
    WeatherCondition,
    AlertSeverity
)
from src.web.arxiv_integration import (
    ArxivIntegration,
    ArxivPaper,
    ArxivCategory
)


class TestNewsIntegration:
    """Test news API integration"""

    @pytest.fixture
    def news_api(self):
        return NewsIntegration()

    @pytest.mark.asyncio
    async def test_get_headlines(self, news_api):
        """Test getting news headlines"""
        headlines = await news_api.get_headlines(
            category=NewsCategory.TECHNOLOGY,
            limit=5
        )

        assert isinstance(headlines, list)
        assert len(headlines) <= 5
        for article in headlines:
            assert isinstance(article, NewsArticle)

    @pytest.mark.asyncio
    async def test_search_news(self, news_api):
        """Test news search"""
        results = await news_api.search_news(
            query="artificial intelligence",
            limit=10
        )

        assert isinstance(results, list)
        assert len(results) <= 10

    @pytest.mark.asyncio
    async def test_get_sources(self, news_api):
        """Test getting news sources"""
        sources = await news_api.get_sources(
            category=NewsCategory.TECHNOLOGY
        )

        assert isinstance(sources, list)
        assert len(sources) > 0

    @pytest.mark.asyncio
    async def test_analyze_sentiment(self, news_api):
        """Test sentiment analysis"""
        article = NewsArticle(
            article_id="test",
            title="Great success in AI research",
            description="Amazing breakthrough achieved",
            content="",
            url="",
            source="test"
        )

        sentiment = await news_api.analyze_sentiment(article)
        assert isinstance(sentiment, NewsSentiment)

    @pytest.mark.asyncio
    async def test_trending_topics(self, news_api):
        """Test trending topics"""
        topics = await news_api.get_trending_topics(limit=5)

        assert isinstance(topics, list)
        assert len(topics) <= 5


class TestWeatherIntegration:
    """Test weather API integration"""

    @pytest.fixture
    def weather_api(self):
        return WeatherIntegration()

    @pytest.mark.asyncio
    async def test_get_current_weather(self, weather_api):
        """Test getting current weather"""
        weather = await weather_api.get_current_weather("London")

        assert weather is None or isinstance(weather, WeatherData)
        if weather:
            assert weather.location == "London"
            assert isinstance(weather.temperature, float)

    @pytest.mark.asyncio
    async def test_get_forecast(self, weather_api):
        """Test weather forecast"""
        forecast = await weather_api.get_forecast("Paris", days=3)

        assert isinstance(forecast, list)
        assert len(forecast) <= 3

    @pytest.mark.asyncio
    async def test_get_alerts(self, weather_api):
        """Test weather alerts"""
        alerts = await weather_api.get_alerts("Storm City")

        assert isinstance(alerts, list)

    @pytest.mark.asyncio
    async def test_weather_summary(self, weather_api):
        """Test comprehensive weather summary"""
        summary = await weather_api.get_weather_summary("New York")

        assert isinstance(summary, dict)
        assert 'location' in summary
        assert 'current' in summary


class TestArxivIntegration:
    """Test arXiv API integration"""

    @pytest.fixture
    def arxiv_api(self):
        return ArxivIntegration()

    @pytest.mark.asyncio
    async def test_search_papers(self, arxiv_api):
        """Test searching papers"""
        papers = await arxiv_api.search_papers(
            query="machine learning",
            max_results=5
        )

        assert isinstance(papers, list)
        assert len(papers) <= 5
        for paper in papers:
            assert isinstance(paper, ArxivPaper)

    @pytest.mark.asyncio
    async def test_get_paper(self, arxiv_api):
        """Test getting specific paper"""
        paper = await arxiv_api.get_paper("2024.00001")

        assert paper is None or isinstance(paper, ArxivPaper)

    @pytest.mark.asyncio
    async def test_get_recent_papers(self, arxiv_api):
        """Test getting recent papers"""
        papers = await arxiv_api.get_recent_papers(
            category=ArxivCategory.CS_AI,
            days=7,
            max_results=10
        )

        assert isinstance(papers, list)
        assert len(papers) <= 10

    @pytest.mark.asyncio
    async def test_get_author_profile(self, arxiv_api):
        """Test author profile"""
        profile = await arxiv_api.get_author_profile("John Doe")

        assert profile.name == "John Doe"
        assert isinstance(profile.total_papers, int)
        assert isinstance(profile.h_index, int)

    @pytest.mark.asyncio
    async def test_recommend_papers(self, arxiv_api):
        """Test paper recommendations"""
        recommendations = await arxiv_api.recommend_papers(
            interests=["AI", "ML"],
            max_per_interest=3
        )

        assert isinstance(recommendations, list)
