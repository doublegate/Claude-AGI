"""
News API Integration for Claude-AGI
====================================

Integrates with news APIs to retrieve current events including:
- Breaking news and headlines
- Topic-specific news searches
- Source-based filtering
- Sentiment analysis
- Trending topics
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class NewsCategory(Enum):
    """News article categories"""
    GENERAL = "general"
    BUSINESS = "business"
    TECHNOLOGY = "technology"
    SCIENCE = "science"
    HEALTH = "health"
    SPORTS = "sports"
    ENTERTAINMENT = "entertainment"
    POLITICS = "politics"


class NewsSentiment(Enum):
    """Article sentiment classification"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


@dataclass
class NewsArticle:
    """A news article with metadata"""
    article_id: str
    title: str
    description: str
    content: str
    url: str
    source: str
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    category: NewsCategory = NewsCategory.GENERAL
    sentiment: NewsSentiment = NewsSentiment.NEUTRAL
    keywords: List[str] = field(default_factory=list)
    image_url: Optional[str] = None
    relevance_score: float = 0.0


@dataclass
class NewsSource:
    """A news source/publication"""
    source_id: str
    name: str
    description: str
    url: str
    category: NewsCategory
    language: str = "en"
    country: str = "us"
    credibility_score: float = 0.5


class NewsIntegration:
    """News API integration for current events"""

    def __init__(self, api_key: Optional[str] = None, language: str = "en"):
        self.api_key = api_key
        self.language = language
        self.base_url = "https://newsapi.org/v2"
        self.cache: Dict[str, List[NewsArticle]] = {}
        self.cache_expiry: Dict[str, datetime] = {}
        self.cache_duration = timedelta(minutes=15)

    async def get_headlines(
        self,
        category: Optional[NewsCategory] = None,
        country: str = "us",
        limit: int = 10
    ) -> List[NewsArticle]:
        """Get current top headlines"""

        cache_key = f"headlines_{category}_{country}"

        # Check cache
        if self._is_cached(cache_key):
            logger.info(f"Retrieved headlines from cache: {cache_key}")
            return self.cache[cache_key][:limit]

        params = {
            'country': country,
            'pageSize': limit,
            'apiKey': self.api_key or 'demo'
        }

        if category:
            params['category'] = category.value

        logger.info(f"Fetching headlines: category={category}, country={country}")

        # Mock implementation for demonstration
        articles = self._generate_mock_headlines(category, limit)

        # Cache results
        self.cache[cache_key] = articles
        self.cache_expiry[cache_key] = datetime.now() + self.cache_duration

        return articles

    async def search_news(
        self,
        query: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        sources: Optional[List[str]] = None,
        sort_by: str = "relevancy",
        limit: int = 10
    ) -> List[NewsArticle]:
        """Search for news articles"""

        cache_key = f"search_{query}_{from_date}_{to_date}"

        # Check cache
        if self._is_cached(cache_key):
            logger.info(f"Retrieved search results from cache: {query}")
            return self.cache[cache_key][:limit]

        params = {
            'q': query,
            'sortBy': sort_by,
            'pageSize': limit,
            'apiKey': self.api_key or 'demo'
        }

        if from_date:
            params['from'] = from_date.isoformat()
        if to_date:
            params['to'] = to_date.isoformat()
        if sources:
            params['sources'] = ','.join(sources)

        logger.info(f"Searching news: query='{query}', from={from_date}, to={to_date}")

        # Mock implementation
        articles = self._generate_mock_search_results(query, limit)

        # Cache results
        self.cache[cache_key] = articles
        self.cache_expiry[cache_key] = datetime.now() + self.cache_duration

        return articles

    async def get_sources(
        self,
        category: Optional[NewsCategory] = None,
        language: Optional[str] = None,
        country: Optional[str] = None
    ) -> List[NewsSource]:
        """Get available news sources"""

        params = {
            'apiKey': self.api_key or 'demo'
        }

        if category:
            params['category'] = category.value
        if language:
            params['language'] = language
        if country:
            params['country'] = country

        logger.info(f"Fetching news sources: category={category}, lang={language}")

        # Mock implementation
        sources = [
            NewsSource(
                source_id="bbc-news",
                name="BBC News",
                description="The BBC is the world's largest broadcasting organisation",
                url="https://www.bbc.com",
                category=NewsCategory.GENERAL,
                credibility_score=0.95
            ),
            NewsSource(
                source_id="techcrunch",
                name="TechCrunch",
                description="Startup and technology news",
                url="https://techcrunch.com",
                category=NewsCategory.TECHNOLOGY,
                credibility_score=0.88
            )
        ]

        return sources

    async def analyze_sentiment(self, article: NewsArticle) -> NewsSentiment:
        """Analyze sentiment of article"""

        # Simple keyword-based sentiment analysis (production would use NLP model)
        text = f"{article.title} {article.description}".lower()

        positive_words = ['good', 'great', 'positive', 'success', 'win', 'benefit', 'growth']
        negative_words = ['bad', 'crisis', 'fail', 'problem', 'concern', 'threat', 'decline']

        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)

        if positive_count > negative_count:
            return NewsSentiment.POSITIVE
        elif negative_count > positive_count:
            return NewsSentiment.NEGATIVE
        elif positive_count > 0 and negative_count > 0:
            return NewsSentiment.MIXED
        else:
            return NewsSentiment.NEUTRAL

    async def get_trending_topics(
        self,
        timeframe: str = "day",
        limit: int = 10
    ) -> List[str]:
        """Get currently trending topics"""

        logger.info(f"Fetching trending topics: timeframe={timeframe}")

        # Mock implementation
        trending = [
            "artificial intelligence",
            "climate change",
            "space exploration",
            "quantum computing",
            "renewable energy",
            "cybersecurity",
            "healthcare innovation",
            "electric vehicles",
            "cryptocurrency",
            "machine learning"
        ]

        return trending[:limit]

    async def monitor_topic(
        self,
        topic: str,
        alert_threshold: int = 5
    ) -> Dict[str, Any]:
        """Monitor a topic for news activity"""

        articles = await self.search_news(topic, limit=50)

        # Calculate activity metrics
        recent_articles = [
            a for a in articles
            if a.published_at and
            (datetime.now() - a.published_at).days <= 1
        ]

        return {
            'topic': topic,
            'total_articles': len(articles),
            'recent_articles_24h': len(recent_articles),
            'alert_triggered': len(recent_articles) >= alert_threshold,
            'top_sources': self._get_top_sources(articles, limit=5),
            'average_sentiment': self._calculate_average_sentiment(articles)
        }

    async def compare_coverage(
        self,
        topic: str,
        sources: List[str]
    ) -> Dict[str, Any]:
        """Compare how different sources cover a topic"""

        comparison = {
            'topic': topic,
            'sources_analyzed': len(sources),
            'coverage_by_source': {}
        }

        for source in sources:
            articles = await self.search_news(
                topic,
                sources=[source],
                limit=10
            )

            comparison['coverage_by_source'][source] = {
                'article_count': len(articles),
                'avg_sentiment': self._calculate_average_sentiment(articles),
                'recent_coverage': len([
                    a for a in articles
                    if a.published_at and
                    (datetime.now() - a.published_at).days <= 7
                ])
            }

        return comparison

    def _is_cached(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self.cache:
            return False

        if key not in self.cache_expiry:
            return False

        return datetime.now() < self.cache_expiry[key]

    def _generate_mock_headlines(
        self,
        category: Optional[NewsCategory],
        limit: int
    ) -> List[NewsArticle]:
        """Generate mock headlines for demonstration"""

        mock_titles = [
            ("AI Breakthrough Announced", NewsSentiment.POSITIVE),
            ("Tech Companies Report Strong Growth", NewsSentiment.POSITIVE),
            ("New Climate Initiative Launched", NewsSentiment.NEUTRAL),
            ("Healthcare Innovation Shows Promise", NewsSentiment.POSITIVE),
            ("Economic Indicators Mixed", NewsSentiment.MIXED),
        ]

        articles = []
        for i, (title, sentiment) in enumerate(mock_titles[:limit]):
            articles.append(NewsArticle(
                article_id=f"mock_{i}",
                title=title,
                description=f"Description for {title}",
                content=f"Full content for {title}",
                url=f"https://example.com/article/{i}",
                source="Example News",
                published_at=datetime.now() - timedelta(hours=i),
                category=category or NewsCategory.GENERAL,
                sentiment=sentiment
            ))

        return articles

    def _generate_mock_search_results(
        self,
        query: str,
        limit: int
    ) -> List[NewsArticle]:
        """Generate mock search results"""

        articles = []
        for i in range(limit):
            articles.append(NewsArticle(
                article_id=f"search_{i}",
                title=f"Article about {query} - {i}",
                description=f"This article discusses {query}",
                content=f"Full content about {query}",
                url=f"https://example.com/search/{i}",
                source="Search News",
                published_at=datetime.now() - timedelta(hours=i),
                relevance_score=1.0 - (i * 0.1)
            ))

        return articles

    def _get_top_sources(
        self,
        articles: List[NewsArticle],
        limit: int
    ) -> List[str]:
        """Get most frequent sources"""

        source_counts = {}
        for article in articles:
            source_counts[article.source] = source_counts.get(article.source, 0) + 1

        sorted_sources = sorted(
            source_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [source for source, _ in sorted_sources[:limit]]

    def _calculate_average_sentiment(
        self,
        articles: List[NewsArticle]
    ) -> str:
        """Calculate average sentiment"""

        if not articles:
            return "neutral"

        sentiment_scores = {
            NewsSentiment.POSITIVE: 1.0,
            NewsSentiment.NEUTRAL: 0.0,
            NewsSentiment.NEGATIVE: -1.0,
            NewsSentiment.MIXED: 0.0
        }

        avg_score = sum(sentiment_scores[a.sentiment] for a in articles) / len(articles)

        if avg_score > 0.3:
            return "positive"
        elif avg_score < -0.3:
            return "negative"
        else:
            return "neutral"

    def clear_cache(self):
        """Clear the news cache"""
        self.cache.clear()
        self.cache_expiry.clear()
        logger.info("News cache cleared")
