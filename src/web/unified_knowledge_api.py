"""
Unified Knowledge API for Claude-AGI
=====================================

Coordinates Wikipedia and Wikidata to provide:
- Comprehensive knowledge retrieval
- Cross-source fact verification
- Multi-modal knowledge representation
- Intelligent query routing
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.web.wikipedia_integration import (
    WikipediaIntegration,
    WikipediaArticle,
    WikiSearchResult,
    WikipediaKnowledgeExtractor
)
from src.web.wikidata_integration import (
    WikidataIntegration,
    WikidataEntity,
    WikidataTriple,
    WikidataKnowledgeGraph
)

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of knowledge queries"""
    FACTUAL = "factual"              # Specific facts
    EXPLORATORY = "exploratory"      # Broad topic exploration
    VERIFICATION = "verification"    # Fact checking
    RELATIONSHIP = "relationship"    # Entity relationships
    COMPARISON = "comparison"        # Compare entities
    TEMPORAL = "temporal"            # Historical/timeline data


@dataclass
class UnifiedKnowledgeResult:
    """Combined result from Wikipedia and Wikidata"""
    query: str
    query_type: QueryType
    wikipedia_article: Optional[WikipediaArticle] = None
    wikidata_entity: Optional[WikidataEntity] = None
    summary: str = ""
    key_facts: List[str] = field(default_factory=list)
    related_topics: List[str] = field(default_factory=list)
    structured_data: Dict[str, Any] = field(default_factory=dict)
    sources: List[str] = field(default_factory=list)
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class UnifiedKnowledgeAPI:
    """Unified API coordinating Wikipedia and Wikidata"""

    def __init__(self, language: str = "en"):
        self.wikipedia = WikipediaIntegration(language=language)
        self.wikidata = WikidataIntegration(language=language)
        self.wiki_extractor = WikipediaKnowledgeExtractor(self.wikipedia)
        self.wikidata_graph = WikidataKnowledgeGraph(self.wikidata)
        self.language = language

    async def query(
        self,
        query_text: str,
        query_type: Optional[QueryType] = None,
        include_structured: bool = True,
        include_related: bool = True
    ) -> UnifiedKnowledgeResult:
        """Execute unified knowledge query"""

        # Auto-detect query type if not provided
        if not query_type:
            query_type = await self._detect_query_type(query_text)

        logger.info(f"Processing {query_type.value} query: {query_text}")

        result = UnifiedKnowledgeResult(
            query=query_text,
            query_type=query_type
        )

        # Route to appropriate handler
        if query_type == QueryType.FACTUAL:
            await self._handle_factual_query(query_text, result, include_structured)
        elif query_type == QueryType.EXPLORATORY:
            await self._handle_exploratory_query(query_text, result, include_related)
        elif query_type == QueryType.VERIFICATION:
            await self._handle_verification_query(query_text, result)
        elif query_type == QueryType.RELATIONSHIP:
            await self._handle_relationship_query(query_text, result)
        elif query_type == QueryType.COMPARISON:
            await self._handle_comparison_query(query_text, result)
        elif query_type == QueryType.TEMPORAL:
            await self._handle_temporal_query(query_text, result)

        return result

    async def _detect_query_type(self, query: str) -> QueryType:
        """Detect the type of query from text"""

        query_lower = query.lower()

        # Simple heuristic-based detection
        if any(word in query_lower for word in ['verify', 'true', 'false', 'correct']):
            return QueryType.VERIFICATION

        if any(word in query_lower for word in ['compare', 'difference', 'versus', 'vs']):
            return QueryType.COMPARISON

        if any(word in query_lower for word in ['when', 'timeline', 'history', 'year']):
            return QueryType.TEMPORAL

        if any(word in query_lower for word in ['related', 'connection', 'relationship']):
            return QueryType.RELATIONSHIP

        if any(word in query_lower for word in ['what is', 'who is', 'define', 'explain']):
            return QueryType.EXPLORATORY

        # Default to factual
        return QueryType.FACTUAL

    async def _handle_factual_query(
        self,
        query: str,
        result: UnifiedKnowledgeResult,
        include_structured: bool
    ):
        """Handle factual information queries"""

        # Try to find main entity in query
        search_results = await self.wikipedia.search(query, limit=1)

        if search_results:
            title = search_results[0].title

            # Get Wikipedia article
            result.wikipedia_article = await self.wikipedia.get_article(title)

            # Get Wikidata entity if requested
            if include_structured:
                wikidata_entity = await self.wikidata.get_entity_by_wikipedia_title(title)
                result.wikidata_entity = wikidata_entity

                if wikidata_entity:
                    # Extract structured data
                    triples = await self.wikidata.extract_triples(wikidata_entity.entity_id)
                    result.structured_data = await self._format_triples(triples)

            # Extract key facts
            if result.wikipedia_article:
                result.key_facts = await self.wiki_extractor.extract_key_facts(title)

            # Generate summary
            result.summary = await self._generate_summary(result)

            # Add sources
            if result.wikipedia_article:
                result.sources.append(result.wikipedia_article.url)

            result.confidence = 0.9 if result.wikipedia_article else 0.3

        logger.info(f"Factual query complete: {len(result.key_facts)} facts extracted")

    async def _handle_exploratory_query(
        self,
        query: str,
        result: UnifiedKnowledgeResult,
        include_related: bool
    ):
        """Handle broad topic exploration queries"""

        # Search Wikipedia for topic
        search_results = await self.wikipedia.search(query, limit=1)

        if search_results:
            title = search_results[0].title

            # Get full article
            result.wikipedia_article = await self.wikipedia.get_article(title)

            # Get related articles
            if include_related:
                related = await self.wikipedia.get_related_articles(title, limit=10)
                result.related_topics = related

            # Get Wikidata entity
            wikidata_entity = await self.wikidata.get_entity_by_wikipedia_title(title)
            result.wikidata_entity = wikidata_entity

            if wikidata_entity:
                # Build knowledge subgraph
                subgraph = await self.wikidata_graph.build_subgraph(
                    wikidata_entity.entity_id,
                    max_depth=2
                )
                result.structured_data['knowledge_graph'] = subgraph

            # Generate comprehensive summary
            result.summary = await self._generate_summary(result)

            result.confidence = 0.85

        logger.info(f"Exploratory query complete: {len(result.related_topics)} related topics")

    async def _handle_verification_query(
        self,
        query: str,
        result: UnifiedKnowledgeResult
    ):
        """Handle fact verification queries"""

        # Use Wikipedia's fact verification
        verification = await self.wikipedia.verify_fact(query)

        result.structured_data['verification'] = verification
        result.confidence = verification.get('confidence', 0.0)

        # Add supporting/contradicting evidence
        if verification.get('supporting_articles'):
            result.sources.extend(verification['supporting_articles'])

        # Generate verification summary
        if verification.get('verified') is True:
            result.summary = f"✓ Verified: {query}"
        elif verification.get('verified') is False:
            result.summary = f"✗ Not verified: {query}"
        else:
            result.summary = f"? Insufficient evidence: {query}"

        logger.info(f"Verification query complete: verified={verification.get('verified')}")

    async def _handle_relationship_query(
        self,
        query: str,
        result: UnifiedKnowledgeResult
    ):
        """Handle entity relationship queries"""

        # Extract entities from query (would use NLP in production)
        # For now, assume query format like "relationship between X and Y"

        # Search for entities
        search_results = await self.wikidata.search_entities(query, limit=2)

        if len(search_results) >= 2:
            entity1_id = search_results[0].get('id', '')
            entity2_id = search_results[1].get('id', '')

            # Find path between entities
            path = await self.wikidata_graph.find_path_between_entities(
                entity1_id,
                entity2_id,
                max_path_length=5
            )

            result.structured_data['relationship_path'] = path
            result.confidence = 0.7 if path else 0.3

            # Generate summary
            if path:
                result.summary = f"Found relationship path of length {len(path)}"
            else:
                result.summary = "No direct relationship found"

        logger.info(f"Relationship query complete")

    async def _handle_comparison_query(
        self,
        query: str,
        result: UnifiedKnowledgeResult
    ):
        """Handle entity comparison queries"""

        # Extract entities to compare (would use NLP in production)
        search_results = await self.wikipedia.search(query, limit=2)

        if len(search_results) >= 2:
            title1 = search_results[0].title
            title2 = search_results[1].title

            # Compare Wikipedia articles
            comparison = await self.wikipedia.compare_articles(title1, title2)

            result.structured_data['comparison'] = comparison
            result.confidence = 0.8

            # Generate summary
            similarity = comparison.get('content_similarity', 0.0)
            result.summary = f"Similarity: {similarity:.1%}"

        logger.info(f"Comparison query complete")

    async def _handle_temporal_query(
        self,
        query: str,
        result: UnifiedKnowledgeResult
    ):
        """Handle temporal/historical queries"""

        # Search for topic
        search_results = await self.wikipedia.search(query, limit=1)

        if search_results:
            title = search_results[0].title

            # Extract timeline
            timeline = await self.wiki_extractor.extract_timeline(title)

            result.structured_data['timeline'] = timeline
            result.confidence = 0.75

            # Generate summary
            if timeline:
                result.summary = f"Timeline with {len(timeline)} events"
            else:
                result.summary = "No timeline data available"

        logger.info(f"Temporal query complete: {len(result.structured_data.get('timeline', []))} events")

    async def _generate_summary(self, result: UnifiedKnowledgeResult) -> str:
        """Generate human-readable summary from result"""

        summary_parts = []

        if result.wikipedia_article:
            summary_parts.append(result.wikipedia_article.summary)

        if result.wikidata_entity:
            summary_parts.append(result.wikidata_entity.description)

        # Combine and truncate
        full_summary = " ".join(summary_parts)

        if len(full_summary) > 500:
            full_summary = full_summary[:497] + "..."

        return full_summary

    async def _format_triples(self, triples: List[WikidataTriple]) -> Dict[str, List[Any]]:
        """Format RDF triples into readable structure"""

        formatted = {}

        for triple in triples:
            prop = triple.predicate
            if prop not in formatted:
                formatted[prop] = []

            formatted[prop].append({
                'value': triple.object,
                'qualifiers': triple.qualifiers,
                'references': triple.references
            })

        return formatted

    async def enrich_with_knowledge(
        self,
        text: str,
        entity_linking: bool = True
    ) -> Dict[str, Any]:
        """Enrich text with knowledge from Wikipedia/Wikidata"""

        logger.info(f"Enriching text with knowledge (length: {len(text)})")

        enrichment = {
            'original_text': text,
            'entities': [],
            'linked_knowledge': {},
            'confidence': 0.0
        }

        # Would extract entities from text using NLP
        # Link to Wikipedia/Wikidata
        # Add contextual knowledge

        return enrichment

    async def get_multi_source_answer(
        self,
        question: str,
        max_sources: int = 5
    ) -> Dict[str, Any]:
        """Get answer synthesized from multiple sources"""

        logger.info(f"Finding multi-source answer for: {question}")

        # Search both Wikipedia and Wikidata
        wiki_results = await self.wikipedia.search(question, limit=max_sources)
        wikidata_results = await self.wikidata.search_entities(question, limit=max_sources)

        answer = {
            'question': question,
            'sources_consulted': len(wiki_results) + len(wikidata_results),
            'consensus_answer': None,
            'supporting_facts': [],
            'alternative_perspectives': [],
            'confidence': 0.0
        }

        # Would synthesize information from multiple sources
        # Identify consensus vs. divergent information
        # Rank by source credibility

        return answer

    def clear_all_caches(self):
        """Clear all cached data"""
        self.wikipedia.clear_cache()
        self.wikidata.clear_cache()
        logger.info("All caches cleared")
