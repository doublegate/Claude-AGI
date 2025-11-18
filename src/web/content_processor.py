"""
Web Content Processing for Claude-AGI
======================================

Extracts, cleans, and processes web content for knowledge extraction.
Supports articles, forums, academic papers, and various content types.
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Types of web content"""
    ARTICLE = "article"
    BLOG_POST = "blog_post"
    FORUM_POST = "forum_post"
    ACADEMIC_PAPER = "academic_paper"
    NEWS = "news"
    DOCUMENTATION = "documentation"
    SOCIAL_MEDIA = "social_media"
    VIDEO = "video"
    UNKNOWN = "unknown"


@dataclass
class ProcessedContent:
    """Represents processed web content"""
    url: str
    title: str
    content: str
    content_type: ContentType
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    source_domain: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    key_points: List[str] = field(default_factory=list)
    extracted_concepts: List[str] = field(default_factory=list)
    credibility_score: float = 0.5
    processed_at: datetime = field(default_factory=datetime.now)


@dataclass
class ContentSummary:
    """Summary of processed content"""
    main_ideas: List[str]
    key_facts: List[str]
    interesting_points: List[str]
    related_topics: List[str]
    questions_raised: List[str]


class WebContentProcessor:
    """
    Processes web content for knowledge extraction.
    Handles cleaning, extraction, and structuring of web data.
    """

    def __init__(self, ai_client=None):
        self.ai_client = ai_client
        self.content_cache: Dict[str, ProcessedContent] = {}

    async def process_url(
        self,
        url: str,
        html_content: str,
        use_ai: bool = True
    ) -> Optional[ProcessedContent]:
        """
        Process a web page from HTML content.

        Args:
            url: The URL of the page
            html_content: Raw HTML content
            use_ai: Whether to use AI for enhanced processing

        Returns:
            Processed content or None if processing failed
        """
        try:
            # Extract basic metadata
            title = self._extract_title(html_content)
            author = self._extract_author(html_content)
            published_date = self._extract_date(html_content)

            # Clean and extract main content
            clean_text = self._clean_html(html_content)

            # Detect content type
            content_type = self._detect_content_type(url, html_content)

            # Get source domain
            domain = urlparse(url).netloc

            # Assess credibility
            credibility = await self._assess_credibility(domain, content_type)

            # Extract key information
            key_points = self._extract_key_points(clean_text)

            processed = ProcessedContent(
                url=url,
                title=title,
                content=clean_text,
                content_type=content_type,
                author=author,
                published_date=published_date,
                source_domain=domain,
                key_points=key_points,
                credibility_score=credibility
            )

            # AI-enhanced processing
            if use_ai and self.ai_client:
                processed = await self._ai_enhance_content(processed)

            # Cache the processed content
            self.content_cache[url] = processed

            return processed

        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            return None

    def _clean_html(self, html: str) -> str:
        """
        Clean HTML and extract readable text.
        This is a simplified version - in production would use BeautifulSoup4.
        """
        # Remove scripts and styles
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)

        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove common navigation/footer text
        text = re.sub(r'(Skip to content|Subscribe|Share|Tweet|Like)', '', text, flags=re.IGNORECASE)

        return text.strip()

    def _extract_title(self, html: str) -> str:
        """Extract page title from HTML"""
        match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Try og:title meta tag
        match = re.search(r'<meta property="og:title" content="([^"]+)"', html, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return "Untitled"

    def _extract_author(self, html: str) -> Optional[str]:
        """Extract author from HTML metadata"""
        # Try author meta tag
        match = re.search(r'<meta name="author" content="([^"]+)"', html, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Try article:author meta tag
        match = re.search(r'<meta property="article:author" content="([^"]+)"', html, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return None

    def _extract_date(self, html: str) -> Optional[datetime]:
        """Extract publication date from HTML metadata"""
        # Try various date meta tags
        patterns = [
            r'<meta property="article:published_time" content="([^"]+)"',
            r'<meta name="publish-date" content="([^"]+)"',
            r'<meta name="date" content="([^"]+)"',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                try:
                    # Simplified date parsing - would use dateutil in production
                    date_str = match.group(1)
                    # Return None for now - full date parsing would be complex
                    return None
                except Exception:
                    continue

        return None

    def _detect_content_type(self, url: str, html: str) -> ContentType:
        """Detect the type of content"""
        url_lower = url.lower()
        html_lower = html.lower()

        # Academic papers
        if any(domain in url_lower for domain in ['arxiv.org', 'scholar.google', 'ieee.org', 'acm.org']):
            return ContentType.ACADEMIC_PAPER

        # News sites
        if any(domain in url_lower for domain in ['news', 'bbc.', 'cnn.', 'nytimes', 'reuters']):
            return ContentType.NEWS

        # Forums
        if any(pattern in url_lower for pattern in ['forum', 'reddit.com', 'stackoverflow']):
            return ContentType.FORUM_POST

        # Documentation
        if any(pattern in url_lower for pattern in ['docs.', 'documentation', '/api/', '/reference/']):
            return ContentType.DOCUMENTATION

        # Blog indicators
        if any(pattern in html_lower for pattern in ['<article', 'blog-post', 'entry-content']):
            return ContentType.BLOG_POST

        # Video
        if any(domain in url_lower for domain in ['youtube.', 'vimeo.']):
            return ContentType.VIDEO

        # Default to article
        return ContentType.ARTICLE

    async def _assess_credibility(self, domain: str, content_type: ContentType) -> float:
        """
        Assess the credibility of a source.

        Args:
            domain: Source domain
            content_type: Type of content

        Returns:
            Credibility score (0-1)
        """
        score = 0.5  # Default moderate credibility

        # Known high-credibility domains
        high_credibility = [
            'arxiv.org', 'scholar.google', 'ieee.org', 'acm.org',
            'nature.com', 'science.org', 'wikipedia.org',
            'gov', 'edu', 'scientificamerican.com'
        ]

        # Known medium-credibility domains
        medium_credibility = [
            'medium.com', 'stackoverflow.com', 'github.com',
            'techcrunch.com', 'wired.com', 'arstechnica.com'
        ]

        if any(hc in domain for hc in high_credibility):
            score = 0.9
        elif any(mc in domain for mc in medium_credibility):
            score = 0.7
        elif domain.endswith('.edu') or domain.endswith('.gov'):
            score = 0.85

        # Adjust based on content type
        if content_type == ContentType.ACADEMIC_PAPER:
            score = min(1.0, score + 0.1)
        elif content_type == ContentType.SOCIAL_MEDIA:
            score = max(0.0, score - 0.2)

        return score

    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from text using simple heuristics"""
        key_points = []

        # Split into sentences
        sentences = re.split(r'[.!?]+', text)

        for sentence in sentences[:20]:  # Limit to first 20 sentences
            sentence = sentence.strip()

            if len(sentence) < 20 or len(sentence) > 200:
                continue

            # Look for key phrases
            if any(phrase in sentence.lower() for phrase in [
                'important', 'key', 'significant', 'notable', 'discovered',
                'found that', 'shows that', 'demonstrates', 'reveals'
            ]):
                key_points.append(sentence)

            if len(key_points) >= 5:
                break

        return key_points

    async def _ai_enhance_content(self, content: ProcessedContent) -> ProcessedContent:
        """Use AI to enhance content processing"""
        if not self.ai_client:
            return content

        try:
            # Extract concepts using AI
            # This would use the AI client in production
            # concepts = await self.ai_client.extract_concepts(content.content)
            # content.extracted_concepts = concepts

            # Generate better summary
            # summary = await self.ai_client.summarize(content.content)
            # content.metadata['ai_summary'] = summary

            pass

        except Exception as e:
            logger.error(f"AI enhancement failed: {e}")

        return content

    async def summarize_content(
        self,
        content: ProcessedContent,
        use_ai: bool = True
    ) -> ContentSummary:
        """
        Generate a comprehensive summary of content.

        Args:
            content: The processed content to summarize
            use_ai: Whether to use AI for summarization

        Returns:
            Content summary
        """
        # Extract main ideas (first few sentences)
        sentences = re.split(r'[.!?]+', content.content)
        main_ideas = [s.strip() for s in sentences[:3] if len(s.strip()) > 20]

        # Key facts are the key points we already extracted
        key_facts = content.key_points

        # Interesting points (sentences with certain keywords)
        interesting_points = []
        for sentence in sentences:
            sentence = sentence.strip()
            if any(word in sentence.lower() for word in ['surprising', 'interesting', 'remarkable', 'unexpected']):
                if len(sentence) > 20 and len(sentence) < 200:
                    interesting_points.append(sentence)
                    if len(interesting_points) >= 3:
                        break

        # Related topics (capitalized multi-word phrases)
        related_topics = []
        for match in re.finditer(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', content.content):
            topic = match.group(1)
            if topic not in related_topics and len(topic) < 50:
                related_topics.append(topic)
                if len(related_topics) >= 5:
                    break

        # Questions raised (sentences that start with question words or originally had ?)
        questions = []
        for i, sentence in enumerate(sentences):
            sentence_stripped = sentence.strip()
            # Check if it's a question by looking for question words at start
            question_words = ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'whose', 'whom', 'is', 'are', 'can', 'could', 'would', 'should', 'do', 'does', 'did']
            is_question = any(sentence_stripped.lower().startswith(word) for word in question_words)

            if is_question:
                question = sentence_stripped if sentence_stripped.endswith('?') else sentence_stripped + '?'
                if len(question) > 10 and len(question) < 150:
                    questions.append(question)
                    if len(questions) >= 3:
                        break

        return ContentSummary(
            main_ideas=main_ideas,
            key_facts=key_facts,
            interesting_points=interesting_points,
            related_topics=related_topics,
            questions_raised=questions
        )

    async def extract_citations(self, content: ProcessedContent) -> List[str]:
        """Extract citations and references from content"""
        citations = []

        # Look for URLs in the text
        urls = re.findall(r'https?://[^\s<>"]+', content.content)
        citations.extend(urls[:10])  # Limit to 10

        # Look for typical citation patterns
        # [Author, Year]
        author_year_citations = re.findall(r'\[([A-Z][a-z]+,?\s+\d{4})\]', content.content)
        citations.extend(author_year_citations)

        # (Author Year)
        paren_citations = re.findall(r'\(([A-Z][a-z]+\s+\d{4})\)', content.content)
        citations.extend(paren_citations)

        return list(set(citations))  # Remove duplicates

    def get_reading_time(self, content: ProcessedContent) -> int:
        """Estimate reading time in minutes (assuming 200 words per minute)"""
        word_count = len(content.content.split())
        return max(1, word_count // 200)


class InformationSynthesizer:
    """
    Synthesizes information from multiple sources.
    Identifies patterns, contradictions, and consensus.
    """

    def __init__(self):
        self.processed_sources: List[ProcessedContent] = []

    async def add_source(self, content: ProcessedContent):
        """Add a processed source for synthesis"""
        self.processed_sources.append(content)

    async def find_consensus(self, topic: str) -> Dict[str, Any]:
        """
        Find consensus across multiple sources on a topic.

        Args:
            topic: The topic to analyze

        Returns:
            Dictionary with consensus information
        """
        topic_lower = topic.lower()

        # Find sources mentioning the topic
        relevant_sources = [
            source for source in self.processed_sources
            if topic_lower in source.content.lower()
        ]

        if not relevant_sources:
            return {'consensus': False, 'reason': 'No sources found'}

        # Extract statements about the topic from each source
        statements = {}
        for source in relevant_sources:
            # Find sentences mentioning the topic
            sentences = re.split(r'[.!?]+', source.content)
            topic_sentences = [
                s.strip() for s in sentences
                if topic_lower in s.lower() and len(s.strip()) > 20
            ]

            if topic_sentences:
                statements[source.url] = topic_sentences[:3]  # Top 3 sentences

        # Calculate agreement (simplified - would use NLP similarity in production)
        high_credibility_count = sum(
            1 for s in relevant_sources if s.credibility_score > 0.7
        )

        consensus_strength = high_credibility_count / len(relevant_sources) if relevant_sources else 0.0

        return {
            'consensus': consensus_strength > 0.5,
            'strength': consensus_strength,
            'source_count': len(relevant_sources),
            'statements': statements,
            'average_credibility': sum(s.credibility_score for s in relevant_sources) / len(relevant_sources)
        }

    async def identify_contradictions(self) -> List[Dict[str, Any]]:
        """Identify contradictions between sources"""
        contradictions = []

        # Simplified - would use semantic analysis in production
        # Look for sources with opposing sentiment on same topics

        return contradictions

    async def generate_synthesis(self, topic: str, max_sources: int = 5) -> str:
        """
        Generate a synthesis of information from multiple sources.

        Args:
            topic: Topic to synthesize
            max_sources: Maximum number of sources to use

        Returns:
            Synthesized text
        """
        consensus = await self.find_consensus(topic)

        if not consensus.get('consensus'):
            return f"Insufficient consensus found on '{topic}' across {consensus.get('source_count', 0)} sources."

        synthesis_parts = [
            f"Based on {consensus['source_count']} sources (average credibility: {consensus['average_credibility']:.2f}):",
            f"",
            f"Consensus strength: {consensus['strength']:.0%}",
            f""
        ]

        # Add key statements from high-credibility sources
        if 'statements' in consensus:
            synthesis_parts.append("Key findings:")
            for url, statements in list(consensus['statements'].items())[:max_sources]:
                if statements:
                    synthesis_parts.append(f"- {statements[0]}")

        return "\n".join(synthesis_parts)
