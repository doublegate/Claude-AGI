"""
arXiv Academic Database Integration for Claude-AGI
===================================================

Integrates with arXiv API to access academic papers including:
- Paper search by keywords, authors, categories
- Paper retrieval with metadata
- Citation tracking
- Author profiling
- Topic trend analysis
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ArxivCategory(Enum):
    """arXiv paper categories"""
    CS_AI = "cs.AI"  # Artificial Intelligence
    CS_LG = "cs.LG"  # Machine Learning
    CS_CL = "cs.CL"  # Computation and Language
    CS_CV = "cs.CV"  # Computer Vision
    MATH = "math"    # Mathematics
    PHYSICS = "physics"  # Physics
    QUANT_PH = "quant-ph"  # Quantum Physics
    STAT = "stat"    # Statistics
    BIO = "q-bio"    # Quantitative Biology


@dataclass
class ArxivPaper:
    """An arXiv academic paper"""
    paper_id: str
    title: str
    authors: List[str]
    abstract: str
    categories: List[str]
    published: datetime
    updated: datetime
    pdf_url: str
    arxiv_url: str
    doi: Optional[str] = None
    journal_ref: Optional[str] = None
    comments: Optional[str] = None
    primary_category: Optional[str] = None
    citations: int = 0
    relevance_score: float = 0.0


@dataclass
class Author:
    """Academic author profile"""
    name: str
    papers: List[str] = field(default_factory=list)
    total_papers: int = 0
    total_citations: int = 0
    h_index: int = 0
    primary_categories: List[str] = field(default_factory=list)
    collaborators: List[str] = field(default_factory=list)


class ArxivIntegration:
    """arXiv API integration for academic research"""

    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"
        self.cache: Dict[str, List[ArxivPaper]] = {}

    async def search_papers(
        self,
        query: str,
        category: Optional[ArxivCategory] = None,
        max_results: int = 10,
        sort_by: str = "relevance"
    ) -> List[ArxivPaper]:
        """Search for papers"""

        search_query = query
        if category:
            search_query = f"cat:{category.value} AND {query}"

        params = {
            'search_query': search_query,
            'start': 0,
            'max_results': max_results,
            'sortBy': sort_by,  # relevance, lastUpdatedDate, submittedDate
            'sortOrder': 'descending'
        }

        logger.info(f"Searching arXiv: query='{query}', category={category}")

        # Mock implementation
        papers = self._generate_mock_papers(query, max_results)

        return papers

    async def get_paper(self, paper_id: str) -> Optional[ArxivPaper]:
        """Get a specific paper by ID"""

        logger.info(f"Fetching paper: {paper_id}")

        # Mock implementation
        return ArxivPaper(
            paper_id=paper_id,
            title="Example Paper Title",
            authors=["John Doe", "Jane Smith"],
            abstract="This is an example abstract...",
            categories=["cs.AI", "cs.LG"],
            published=datetime.now(),
            updated=datetime.now(),
            pdf_url=f"https://arxiv.org/pdf/{paper_id}.pdf",
            arxiv_url=f"https://arxiv.org/abs/{paper_id}",
            primary_category="cs.AI"
        )

    async def get_papers_by_author(
        self,
        author_name: str,
        max_results: int = 20
    ) -> List[ArxivPaper]:
        """Get all papers by an author"""

        search_query = f"au:{author_name}"

        params = {
            'search_query': search_query,
            'start': 0,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }

        logger.info(f"Fetching papers by author: {author_name}")

        # Mock implementation
        return self._generate_mock_papers(author_name, max_results)

    async def get_recent_papers(
        self,
        category: ArxivCategory,
        days: int = 7,
        max_results: int = 20
    ) -> List[ArxivPaper]:
        """Get recently published papers in a category"""

        # Calculate date range
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=days)

        search_query = f"cat:{category.value}"

        logger.info(f"Fetching recent papers: category={category}, days={days}")

        # Mock implementation
        return self._generate_mock_papers(category.value, max_results)

    async def get_trending_papers(
        self,
        category: Optional[ArxivCategory] = None,
        timeframe: str = "week",
        limit: int = 10
    ) -> List[ArxivPaper]:
        """Get trending/popular papers"""

        logger.info(f"Fetching trending papers: category={category}, timeframe={timeframe}")

        # Mock implementation - would rank by downloads, citations, etc.
        papers = self._generate_mock_papers("trending", limit)

        # Sort by relevance/popularity
        papers.sort(key=lambda p: p.citations, reverse=True)

        return papers

    async def get_author_profile(self, author_name: str) -> Author:
        """Get author profile with statistics"""

        papers = await self.get_papers_by_author(author_name, max_results=100)

        # Calculate statistics
        total_citations = sum(p.citations for p in papers)
        categories = [cat for p in papers for cat in p.categories]
        primary_categories = list(set(categories))

        # Extract collaborators
        collaborators = set()
        for paper in papers:
            collaborators.update(paper.authors)
        collaborators.discard(author_name)

        # Calculate h-index
        citation_counts = sorted([p.citations for p in papers], reverse=True)
        h_index = 0
        for i, citations in enumerate(citation_counts, 1):
            if citations >= i:
                h_index = i
            else:
                break

        logger.info(f"Built profile for author: {author_name}")

        return Author(
            name=author_name,
            papers=[p.paper_id for p in papers],
            total_papers=len(papers),
            total_citations=total_citations,
            h_index=h_index,
            primary_categories=primary_categories,
            collaborators=list(collaborators)[:20]
        )

    async def find_related_papers(
        self,
        paper_id: str,
        limit: int = 10
    ) -> List[ArxivPaper]:
        """Find papers related to a given paper"""

        paper = await self.get_paper(paper_id)
        if not paper:
            return []

        # Search for papers with similar keywords from title/abstract
        keywords = paper.title.split()[:5]  # Simple keyword extraction
        query = ' '.join(keywords)

        related = await self.search_papers(query, max_results=limit + 1)

        # Filter out the original paper
        related = [p for p in related if p.paper_id != paper_id]

        logger.info(f"Found {len(related)} related papers for {paper_id}")

        return related[:limit]

    async def track_research_topic(
        self,
        topic: str,
        months: int = 6
    ) -> Dict[str, Any]:
        """Track evolution of a research topic"""

        papers = await self.search_papers(topic, max_results=100)

        # Group by month
        monthly_counts = {}
        for paper in papers:
            month_key = paper.published.strftime("%Y-%m")
            monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1

        logger.info(f"Tracking research topic: {topic}")

        return {
            'topic': topic,
            'total_papers': len(papers),
            'monthly_distribution': monthly_counts,
            'top_authors': self._get_top_authors(papers, limit=10),
            'top_categories': self._get_top_categories(papers),
            'growth_trend': 'increasing' if len(papers) > 50 else 'steady'
        }

    async def recommend_papers(
        self,
        interests: List[str],
        max_per_interest: int = 5
    ) -> List[ArxivPaper]:
        """Recommend papers based on interests"""

        recommendations = []

        for interest in interests:
            papers = await self.search_papers(
                interest,
                max_results=max_per_interest
            )
            recommendations.extend(papers)

        # Remove duplicates and sort by relevance
        seen = set()
        unique_recommendations = []
        for paper in recommendations:
            if paper.paper_id not in seen:
                seen.add(paper.paper_id)
                unique_recommendations.append(paper)

        logger.info(f"Generated {len(unique_recommendations)} recommendations")

        return unique_recommendations

    async def compare_research_areas(
        self,
        category1: ArxivCategory,
        category2: ArxivCategory,
        months: int = 12
    ) -> Dict[str, Any]:
        """Compare activity in two research areas"""

        papers1 = await self.get_recent_papers(category1, days=months*30, max_results=100)
        papers2 = await self.get_recent_papers(category2, days=months*30, max_results=100)

        return {
            'categories': [category1.value, category2.value],
            'period_months': months,
            'comparison': {
                'paper_count': {
                    category1.value: len(papers1),
                    category2.value: len(papers2)
                },
                'avg_citations': {
                    category1.value: sum(p.citations for p in papers1) / max(len(papers1), 1),
                    category2.value: sum(p.citations for p in papers2) / max(len(papers2), 1)
                },
                'top_authors': {
                    category1.value: self._get_top_authors(papers1, limit=5),
                    category2.value: self._get_top_authors(papers2, limit=5)
                }
            }
        }

    def _generate_mock_papers(self, query: str, count: int) -> List[ArxivPaper]:
        """Generate mock paper results"""
        papers = []

        for i in range(count):
            papers.append(ArxivPaper(
                paper_id=f"2024.{1000+i:05d}",
                title=f"Research Paper on {query} - Part {i+1}",
                authors=["Author A", "Author B"],
                abstract=f"This paper explores {query} and presents novel findings...",
                categories=["cs.AI", "cs.LG"],
                published=datetime.now(),
                updated=datetime.now(),
                pdf_url=f"https://arxiv.org/pdf/2024.{1000+i:05d}.pdf",
                arxiv_url=f"https://arxiv.org/abs/2024.{1000+i:05d}",
                primary_category="cs.AI",
                citations=100 - i*5,  # Decreasing citations
                relevance_score=1.0 - (i * 0.05)
            ))

        return papers

    def _get_top_authors(self, papers: List[ArxivPaper], limit: int) -> List[str]:
        """Get most prolific authors"""
        author_counts = {}

        for paper in papers:
            for author in paper.authors:
                author_counts[author] = author_counts.get(author, 0) + 1

        sorted_authors = sorted(
            author_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [author for author, _ in sorted_authors[:limit]]

    def _get_top_categories(self, papers: List[ArxivPaper]) -> List[str]:
        """Get most common categories"""
        category_counts = {}

        for paper in papers:
            for category in paper.categories:
                category_counts[category] = category_counts.get(category, 0) + 1

        sorted_categories = sorted(
            category_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [cat for cat, _ in sorted_categories[:5]]

    def clear_cache(self):
        """Clear the papers cache"""
        self.cache.clear()
        logger.info("arXiv cache cleared")
