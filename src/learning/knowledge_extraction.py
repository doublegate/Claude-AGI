"""
Knowledge Extraction from Text
================================

NLP-based extraction of concepts and relationships from unstructured text.
Uses AI-powered analysis for entity recognition and relationship extraction.
"""

import asyncio
import logging
import re
from typing import List, Dict, Any, Tuple, Set, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ExtractedConcept:
    """Represents a concept extracted from text"""
    name: str
    concept_type: str
    context: str
    confidence: float
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedRelationship:
    """Represents a relationship extracted from text"""
    source: str
    target: str
    relation_type: str
    context: str
    confidence: float


class KnowledgeExtractor:
    """
    Extracts structured knowledge from unstructured text using NLP.
    Uses AI-powered analysis to identify concepts and relationships.
    """

    def __init__(self, ai_client=None):
        self.ai_client = ai_client
        self.concept_patterns = self._build_concept_patterns()
        self.relationship_patterns = self._build_relationship_patterns()

    def _build_concept_patterns(self) -> Dict[str, List[str]]:
        """Build regex patterns for concept extraction"""
        return {
            'definition': [
                r'(\w+) is (?:a |an )?(\w+)',
                r'(\w+) refers to (\w+)',
                r'(\w+) means (\w+)',
            ],
            'property': [
                r'(\w+) (?:has|have) (\w+)',
                r'(\w+) (?:is|are) (\w+)',
            ],
            'action': [
                r'(\w+) (?:can|could|may) (\w+)',
                r'(\w+) (?:does|do) (\w+)',
            ]
        }

    def _build_relationship_patterns(self) -> Dict[str, List[str]]:
        """Build regex patterns for relationship extraction"""
        return {
            'causes': [
                r'(\w+) causes (\w+)',
                r'(\w+) leads to (\w+)',
                r'(\w+) results in (\w+)',
            ],
            'part_of': [
                r'(\w+) is part of (\w+)',
                r'(\w+) belongs to (\w+)',
                r'(\w+) is (?:a |an )?component of (\w+)',
            ],
            'requires': [
                r'(\w+) requires (\w+)',
                r'(\w+) needs (\w+)',
                r'(\w+) depends on (\w+)',
            ],
            'similar_to': [
                r'(\w+) is similar to (\w+)',
                r'(\w+) is like (\w+)',
                r'(\w+) resembles (\w+)',
            ]
        }

    async def extract_concepts(self, text: str, use_ai: bool = True) -> List[ExtractedConcept]:
        """
        Extract concepts from text using pattern matching and optionally AI.

        Args:
            text: The text to analyze
            use_ai: Whether to use AI for enhanced extraction

        Returns:
            List of extracted concepts
        """
        concepts = []

        # Pattern-based extraction
        for concept_type, patterns in self.concept_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    if len(match.groups()) >= 2:
                        name = match.group(1)
                        value = match.group(2)

                        concepts.append(ExtractedConcept(
                            name=name,
                            concept_type=concept_type,
                            context=match.group(0),
                            confidence=0.7,  # Pattern-based confidence
                            properties={'value': value}
                        ))

        # AI-powered extraction (if available)
        if use_ai and self.ai_client:
            ai_concepts = await self._ai_extract_concepts(text)
            concepts.extend(ai_concepts)

        # Deduplicate by name
        seen = set()
        unique_concepts = []
        for concept in concepts:
            if concept.name.lower() not in seen:
                seen.add(concept.name.lower())
                unique_concepts.append(concept)

        return unique_concepts

    async def _ai_extract_concepts(self, text: str) -> List[ExtractedConcept]:
        """Use AI to extract concepts from text"""
        concepts = []

        if not self.ai_client:
            return concepts

        try:
            # Use AI to identify key concepts
            prompt = f"""Analyze this text and extract key concepts.

Text: {text}

For each concept, provide:
1. Name (the concept term)
2. Type (e.g., person, place, idea, technology, process)
3. Brief description

Format as JSON array: [{{"name": "...", "type": "...", "description": "..."}}]"""

            # This would use the AI client - simplified for now
            # response = await self.ai_client.generate(prompt)
            # Parse response and create ExtractedConcept objects

        except Exception as e:
            logger.error(f"AI concept extraction failed: {e}")

        return concepts

    async def extract_relationships(
        self,
        text: str,
        known_concepts: Optional[Set[str]] = None,
        use_ai: bool = True
    ) -> List[ExtractedRelationship]:
        """
        Extract relationships between concepts from text.

        Args:
            text: The text to analyze
            known_concepts: Set of known concept names to look for
            use_ai: Whether to use AI for enhanced extraction

        Returns:
            List of extracted relationships
        """
        relationships = []

        # Pattern-based extraction
        for relation_type, patterns in self.relationship_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    if len(match.groups()) >= 2:
                        source = match.group(1)
                        target = match.group(2)

                        # Filter by known concepts if provided
                        if known_concepts:
                            if source.lower() not in {c.lower() for c in known_concepts}:
                                continue
                            if target.lower() not in {c.lower() for c in known_concepts}:
                                continue

                        relationships.append(ExtractedRelationship(
                            source=source,
                            target=target,
                            relation_type=relation_type,
                            context=match.group(0),
                            confidence=0.7
                        ))

        # AI-powered extraction (if available)
        if use_ai and self.ai_client and known_concepts:
            ai_relationships = await self._ai_extract_relationships(text, known_concepts)
            relationships.extend(ai_relationships)

        return relationships

    async def _ai_extract_relationships(
        self,
        text: str,
        known_concepts: Set[str]
    ) -> List[ExtractedRelationship]:
        """Use AI to extract relationships from text"""
        relationships = []

        if not self.ai_client:
            return relationships

        try:
            # Use AI to identify relationships between known concepts
            concepts_list = ', '.join(list(known_concepts)[:20])  # Limit for prompt size

            prompt = f"""Analyze this text and identify relationships between these concepts: {concepts_list}

Text: {text}

For each relationship, provide:
1. Source concept
2. Target concept
3. Relationship type (causes, requires, part_of, similar_to, etc.)
4. Brief explanation

Format as JSON array: [{{"source": "...", "target": "...", "type": "...", "explanation": "..."}}]"""

            # This would use the AI client - simplified for now
            # response = await self.ai_client.generate(prompt)
            # Parse response and create ExtractedRelationship objects

        except Exception as e:
            logger.error(f"AI relationship extraction failed: {e}")

        return relationships

    async def extract_knowledge_from_document(
        self,
        text: str,
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Extract comprehensive knowledge from a document.

        Args:
            text: The document text
            use_ai: Whether to use AI for enhanced extraction

        Returns:
            Dictionary with extracted concepts and relationships
        """
        # Extract concepts first
        concepts = await self.extract_concepts(text, use_ai=use_ai)

        # Get concept names for relationship extraction
        concept_names = {c.name for c in concepts}

        # Extract relationships
        relationships = await self.extract_relationships(
            text,
            known_concepts=concept_names,
            use_ai=use_ai
        )

        return {
            'concepts': concepts,
            'relationships': relationships,
            'source_text': text,
            'extraction_timestamp': asyncio.get_event_loop().time()
        }

    def calculate_importance(self, concept: ExtractedConcept, context: str) -> float:
        """
        Calculate the importance of a concept based on various factors.

        Args:
            concept: The extracted concept
            context: The context where it was found

        Returns:
            Importance score (0-1)
        """
        importance = concept.confidence

        # Boost importance based on capitalization
        if concept.name[0].isupper():
            importance += 0.1

        # Boost importance if it appears multiple times in context
        count = context.lower().count(concept.name.lower())
        importance += min(0.2, count * 0.05)

        # Boost importance based on position (earlier is more important)
        position = context.lower().find(concept.name.lower())
        if position < len(context) * 0.2:
            importance += 0.1

        return min(1.0, importance)


class LearningPathGenerator:
    """
    Generates learning paths through the knowledge graph.
    Uses graph traversal algorithms to find optimal learning sequences.
    """

    def __init__(self, knowledge_graph):
        self.knowledge_graph = knowledge_graph

    async def find_learning_path(
        self,
        start_concept: str,
        end_concept: str,
        max_depth: int = 10
    ) -> Optional[List[str]]:
        """
        Find a learning path from start concept to end concept.
        Uses BFS to find shortest path through prerequisite relationships.

        Args:
            start_concept: Starting concept name
            end_concept: Target concept name
            max_depth: Maximum path length

        Returns:
            List of concept names forming the learning path, or None if no path exists
        """
        # Get concept IDs
        start_id = self.knowledge_graph.concept_by_name.get(start_concept)
        end_id = self.knowledge_graph.concept_by_name.get(end_concept)

        if not start_id or not end_id:
            return None

        # BFS to find shortest path
        queue = [(start_id, [start_id])]
        visited = {start_id}

        while queue:
            current_id, path = queue.pop(0)

            if len(path) > max_depth:
                continue

            if current_id == end_id:
                # Convert IDs to names
                return [self.knowledge_graph.concepts[cid].name for cid in path]

            # Explore neighbors (outgoing edges)
            for edge_id in self.knowledge_graph.outgoing_edges.get(current_id, []):
                relationship = self.knowledge_graph.relationships.get(edge_id)
                if not relationship:
                    continue

                # Prefer prerequisite/foundational relationships
                if relationship.relation_type in ['REQUIRES', 'PART_OF', 'IS_A']:
                    next_id = relationship.target_id

                    if next_id not in visited:
                        visited.add(next_id)
                        queue.append((next_id, path + [next_id]))

        return None

    async def identify_knowledge_gaps(
        self,
        known_concepts: Set[str],
        target_concept: str
    ) -> List[str]:
        """
        Identify missing concepts needed to understand a target concept.

        Args:
            known_concepts: Set of concept names already known
            target_concept: The concept to understand

        Returns:
            List of concept names representing knowledge gaps
        """
        gaps = []

        target_id = self.knowledge_graph.concept_by_name.get(target_concept)
        if not target_id:
            return gaps

        # Find all prerequisite concepts
        visited = set()
        to_explore = [target_id]

        while to_explore:
            current_id = to_explore.pop(0)

            if current_id in visited:
                continue
            visited.add(current_id)

            current_concept = self.knowledge_graph.concepts[current_id]

            # Check if this is a gap
            if current_concept.name not in known_concepts:
                gaps.append(current_concept.name)

            # Explore prerequisites
            for edge_id in self.knowledge_graph.incoming_edges.get(current_id, []):
                relationship = self.knowledge_graph.relationships.get(edge_id)
                if not relationship:
                    continue

                if relationship.relation_type == 'REQUIRES':
                    to_explore.append(relationship.source_id)

        return gaps

    async def suggest_next_concepts(
        self,
        known_concepts: Set[str],
        max_suggestions: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Suggest next concepts to learn based on what's already known.

        Args:
            known_concepts: Set of concept names already known
            max_suggestions: Maximum number of suggestions

        Returns:
            List of (concept_name, score) tuples, sorted by score
        """
        suggestions = {}

        # Find concepts that are just beyond the current knowledge frontier
        for concept_name in known_concepts:
            concept_id = self.knowledge_graph.concept_by_name.get(concept_name)
            if not concept_id:
                continue

            # Look at concepts reachable from known concepts
            for edge_id in self.knowledge_graph.outgoing_edges.get(concept_id, []):
                relationship = self.knowledge_graph.relationships.get(edge_id)
                if not relationship:
                    continue

                next_concept = self.knowledge_graph.concepts[relationship.target_id]

                if next_concept.name not in known_concepts:
                    # Score based on relationship strength and type
                    score = relationship.strength

                    # Boost score for logical progression relationships
                    if relationship.relation_type in ['IS_A', 'PART_OF']:
                        score *= 1.5

                    # Accumulate scores from multiple known concepts
                    if next_concept.name in suggestions:
                        suggestions[next_concept.name] += score
                    else:
                        suggestions[next_concept.name] = score

        # Sort by score and return top suggestions
        sorted_suggestions = sorted(
            suggestions.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_suggestions[:max_suggestions]
