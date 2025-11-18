"""
Web Content Extraction Pipeline
=================================

Complete pipeline for extracting, processing, and storing content from web sources.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Set
from urllib.parse import urlparse
import hashlib

logger = logging.getLogger(__name__)


class ContentQuality(Enum):
    """Quality assessment of extracted content"""
    EXCELLENT = 1.0
    GOOD = 0.8
    FAIR = 0.6
    POOR = 0.4
    UNUSABLE = 0.2


@dataclass
class ExtractedContent:
    """Represents extracted web content"""
    url: str
    title: str
    content: str
    content_type: str
    author: Optional[str] = None
    publication_date: Optional[datetime] = None
    extraction_date: datetime = field(default_factory=datetime.now)
    quality: ContentQuality = ContentQuality.GOOD
    credibility_score: float = 0.7
    key_concepts: List[str] = field(default_factory=list)
    summary: str = ""
    metadata: Dict[str, any] = field(default_factory=dict)
    links: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)


@dataclass
class ExtractionResult:
    """Result of content extraction"""
    success: bool
    content: Optional[ExtractedContent]
    error: Optional[str] = None
    processing_time: float = 0.0
    steps_completed: List[str] = field(default_factory=list)


class ContentExtractionPipeline:
    """
    Complete pipeline for extracting and processing web content.
    """

    def __init__(self, knowledge_graph=None):
        self.knowledge_graph = knowledge_graph
        self.extraction_cache: Dict[str, ExtractedContent] = {}
        self.extraction_history: List[ExtractionResult] = []

        # Pipeline parameters
        self.max_content_length = 100000  # 100KB
        self.timeout_seconds = 30
        self.user_agent = "Claude-AGI/2.0 Learning Bot"

    async def extract(self, url: str) -> ExtractionResult:
        """
        Extract content from URL through complete pipeline.

        Args:
            url: URL to extract from

        Returns:
            Extraction result
        """
        start_time = datetime.now()
        steps = []

        try:
            # Check cache
            url_hash = hashlib.md5(url.encode()).hexdigest()
            if url_hash in self.extraction_cache:
                logger.info(f"Content cached for: {url}")
                return ExtractionResult(
                    success=True,
                    content=self.extraction_cache[url_hash],
                    steps_completed=["cache_hit"]
                )

            # Step 1: Fetch content
            logger.info(f"Fetching content from: {url}")
            html_content = await self._fetch_content(url)
            steps.append("fetch")

            if not html_content:
                return ExtractionResult(
                    success=False,
                    content=None,
                    error="Failed to fetch content"
                )

            # Step 2: Parse HTML
            parsed = await self._parse_html(html_content, url)
            steps.append("parse")

            # Step 3: Extract metadata
            metadata = await self._extract_metadata(parsed)
            steps.append("metadata")

            # Step 4: Clean content
            cleaned_content = await self._clean_content(parsed.get('content', ''))
            steps.append("clean")

            # Step 5: Assess quality
            quality = await self._assess_quality(cleaned_content, parsed)
            steps.append("quality")

            # Step 6: Extract key concepts
            concepts = await self._extract_concepts(cleaned_content)
            steps.append("concepts")

            # Step 7: Generate summary
            summary = await self._generate_summary(cleaned_content)
            steps.append("summary")

            # Step 8: Extract links
            links = await self._extract_links(parsed, url)
            steps.append("links")

            # Create ExtractedContent
            content = ExtractedContent(
                url=url,
                title=parsed.get('title', 'Untitled'),
                content=cleaned_content,
                content_type=parsed.get('content_type', 'article'),
                author=metadata.get('author'),
                publication_date=metadata.get('publication_date'),
                quality=quality,
                key_concepts=concepts,
                summary=summary,
                metadata=metadata,
                links=links
            )

            # Cache
            self.extraction_cache[url_hash] = content

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()

            result = ExtractionResult(
                success=True,
                content=content,
                processing_time=processing_time,
                steps_completed=steps
            )

            self.extraction_history.append(result)

            logger.info(
                f"Successfully extracted content from {url} "
                f"({processing_time:.2f}s, {len(steps)} steps)"
            )

            return result

        except Exception as e:
            logger.error(f"Extraction failed for {url}: {e}")
            result = ExtractionResult(
                success=False,
                content=None,
                error=str(e),
                processing_time=(datetime.now() - start_time).total_seconds(),
                steps_completed=steps
            )
            self.extraction_history.append(result)
            return result

    async def _fetch_content(self, url: str) -> Optional[str]:
        """Fetch content from URL"""
        # In production, would use aiohttp
        # async with aiohttp.ClientSession() as session:
        #     async with session.get(url, timeout=self.timeout_seconds) as response:
        #         return await response.text()

        # Simulation
        return f"""
        <html>
        <head><title>Sample Article</title></head>
        <body>
            <h1>Understanding Machine Learning</h1>
            <p>Machine learning is a powerful approach to artificial intelligence...</p>
        </body>
        </html>
        """

    async def _parse_html(self, html: str, url: str) -> Dict[str, any]:
        """Parse HTML content"""
        # In production, would use BeautifulSoup4 or lxml
        # from bs4 import BeautifulSoup
        # soup = BeautifulSoup(html, 'lxml')

        # Simulation
        return {
            'title': 'Understanding Machine Learning',
            'content': 'Machine learning is a powerful approach to artificial intelligence...',
            'content_type': 'article',
            'raw_html': html
        }

    async def _extract_metadata(self, parsed: Dict) -> Dict[str, any]:
        """Extract metadata from parsed content"""
        metadata = {
            'author': None,
            'publication_date': None,
            'tags': [],
            'description': ''
        }

        # Would extract from meta tags, JSON-LD, Open Graph, etc.

        return metadata

    async def _clean_content(self, content: str) -> str:
        """Clean and normalize content"""
        # Remove extra whitespace
        cleaned = ' '.join(content.split())

        # Truncate if too long
        if len(cleaned) > self.max_content_length:
            cleaned = cleaned[:self.max_content_length] + '...'

        return cleaned

    async def _assess_quality(
        self,
        content: str,
        parsed: Dict
    ) -> ContentQuality:
        """Assess content quality"""
        score = 1.0

        # Check content length
        if len(content) < 200:
            score *= 0.5

        # Check for title
        if not parsed.get('title'):
            score *= 0.8

        # Map score to quality enum
        if score >= 0.9:
            return ContentQuality.EXCELLENT
        elif score >= 0.7:
            return ContentQuality.GOOD
        elif score >= 0.5:
            return ContentQuality.FAIR
        elif score >= 0.3:
            return ContentQuality.POOR
        else:
            return ContentQuality.UNUSABLE

    async def _extract_concepts(self, content: str) -> List[str]:
        """Extract key concepts from content"""
        # In production, would use NLP
        concepts = []

        # Simple keyword extraction
        keywords = ['machine learning', 'AI', 'neural network', 'algorithm']
        for keyword in keywords:
            if keyword.lower() in content.lower():
                concepts.append(keyword)

        return concepts

    async def _generate_summary(self, content: str) -> str:
        """Generate content summary"""
        # In production, would use extractive or abstractive summarization

        # Simple: first 200 characters
        if len(content) > 200:
            return content[:200] + '...'
        return content

    async def _extract_links(self, parsed: Dict, base_url: str) -> List[str]:
        """Extract and normalize links"""
        # Would extract from parsed HTML and make absolute URLs
        links = []

        return links

    async def batch_extract(
        self,
        urls: List[str],
        max_concurrent: int = 5
    ) -> List[ExtractionResult]:
        """
        Extract content from multiple URLs concurrently.

        Args:
            urls: List of URLs
            max_concurrent: Maximum concurrent extractions

        Returns:
            List of extraction results
        """
        results = []

        # Process in batches
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i:i + max_concurrent]
            batch_results = await asyncio.gather(
                *[self.extract(url) for url in batch],
                return_exceptions=True
            )
            results.extend(batch_results)

        return results

    async def store_in_knowledge_graph(
        self,
        content: ExtractedContent
    ) -> bool:
        """
        Store extracted content in knowledge graph.

        Args:
            content: Extracted content

        Returns:
            Success status
        """
        if not self.knowledge_graph:
            return False

        try:
            # Add concepts to knowledge graph
            for concept_name in content.key_concepts:
                await self.knowledge_graph.add_concept(
                    name=concept_name,
                    concept_type='learned',
                    description=f"From: {content.title}",
                    properties={
                        'source_url': content.url,
                        'source_title': content.title,
                        'extraction_date': content.extraction_date.isoformat()
                    }
                )

            logger.info(
                f"Stored {len(content.key_concepts)} concepts from {content.url}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to store in knowledge graph: {e}")
            return False

    def get_extraction_statistics(self) -> Dict[str, any]:
        """Get statistics about extractions"""
        total = len(self.extraction_history)
        successful = len([r for r in self.extraction_history if r.success])
        failed = total - successful

        avg_time = (
            sum(r.processing_time for r in self.extraction_history) / total
            if total > 0 else 0
        )

        return {
            'total_extractions': total,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / total if total > 0 else 0,
            'average_processing_time': avg_time,
            'cached_content': len(self.extraction_cache)
        }


async def demo():
    """Demo content extraction pipeline"""
    from src.learning.knowledge_graph import KnowledgeGraph

    kg = KnowledgeGraph()
    pipeline = ContentExtractionPipeline(kg)

    # Extract content
    url = "https://example.com/ml-article"
    result = await pipeline.extract(url)

    if result.success:
        content = result.content
        print(f"\n=== Extracted Content ===")
        print(f"Title: {content.title}")
        print(f"Quality: {content.quality.name}")
        print(f"Concepts: {content.key_concepts}")
        print(f"Summary: {content.summary[:100]}...")
        print(f"Processing time: {result.processing_time:.2f}s")

        # Store in knowledge graph
        await pipeline.store_in_knowledge_graph(content)

    # Statistics
    stats = pipeline.get_extraction_statistics()
    print(f"\n=== Extraction Statistics ===")
    print(f"Total extractions: {stats['total_extractions']}")
    print(f"Success rate: {stats['success_rate']:.1%}")
    print(f"Avg processing time: {stats['average_processing_time']:.2f}s")


if __name__ == "__main__":
    asyncio.run(demo())
