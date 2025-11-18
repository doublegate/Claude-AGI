"""
Knowledge Consolidation System
================================

Consolidates and validates knowledge from multiple sources,
ensuring consistency and accuracy in the knowledge graph.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ConflictResolutionStrategy(Enum):
    """Strategies for resolving conflicting information"""
    MOST_RECENT = "most_recent"
    HIGHEST_CONFIDENCE = "highest_confidence"
    MOST_SOURCES = "most_sources"
    MANUAL_REVIEW = "manual_review"


class SourceCredibility(Enum):
    """Credibility levels for information sources"""
    VERIFIED = 1.0
    TRUSTED = 0.9
    RELIABLE = 0.75
    QUESTIONABLE = 0.5
    UNVERIFIED = 0.3


@dataclass
class KnowledgeSource:
    """Represents a source of knowledge"""
    source_id: str
    name: str
    url: Optional[str]
    credibility: SourceCredibility
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    accuracy_score: float = 0.8


@dataclass
class ConsolidatedConcept:
    """A concept consolidated from multiple sources"""
    concept_id: str
    canonical_name: str
    aliases: Set[str] = field(default_factory=set)
    sources: List[KnowledgeSource] = field(default_factory=list)
    confidence: float = 0.8
    last_updated: datetime = field(default_factory=datetime.now)
    consolidation_count: int = 0


@dataclass
class ConflictingInformation:
    """Represents conflicting information that needs resolution"""
    concept_id: str
    field_name: str
    values: List[Tuple[any, KnowledgeSource, float]]  # (value, source, confidence)
    resolution_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.HIGHEST_CONFIDENCE
    resolved: bool = False
    resolved_value: Optional[any] = None


class KnowledgeConsolidator:
    """
    Consolidates knowledge from multiple sources, resolving conflicts
    and maintaining consistency in the knowledge graph.
    """

    def __init__(self, knowledge_graph):
        self.knowledge_graph = knowledge_graph
        self.sources: Dict[str, KnowledgeSource] = {}
        self.consolidation_history: List[Dict] = []
        self.conflicts: List[ConflictingInformation] = []

    async def register_source(
        self,
        source_id: str,
        name: str,
        url: Optional[str] = None,
        credibility: SourceCredibility = SourceCredibility.UNVERIFIED
    ) -> KnowledgeSource:
        """Register a new knowledge source"""
        source = KnowledgeSource(
            source_id=source_id,
            name=name,
            url=url,
            credibility=credibility
        )
        self.sources[source_id] = source
        logger.info(f"Registered knowledge source: {name} ({credibility.name})")
        return source

    async def consolidate_concepts(
        self,
        concept_names: List[str],
        strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.HIGHEST_CONFIDENCE
    ) -> List[ConsolidatedConcept]:
        """
        Consolidate multiple concepts that may represent the same entity.

        Args:
            concept_names: List of concept names to consolidate
            strategy: Strategy for resolving conflicts

        Returns:
            List of consolidated concepts
        """
        consolidated = []

        # Group similar concepts
        concept_groups = await self._group_similar_concepts(concept_names)

        for group in concept_groups:
            # Get concepts from graph
            concepts = []
            for name in group:
                concept_id = self.knowledge_graph.concept_by_name.get(name)
                if concept_id:
                    concept = self.knowledge_graph.concepts.get(concept_id)
                    if concept:
                        concepts.append(concept)

            if not concepts:
                continue

            # Create consolidated concept
            consolidated_concept = await self._consolidate_concept_group(
                concepts,
                strategy
            )

            consolidated.append(consolidated_concept)

        return consolidated

    async def _group_similar_concepts(self, concept_names: List[str]) -> List[List[str]]:
        """Group concepts that likely represent the same entity"""
        groups = []
        processed = set()

        for name in concept_names:
            if name in processed:
                continue

            # Start new group
            group = [name]
            processed.add(name)

            # Find similar concepts
            for other_name in concept_names:
                if other_name in processed:
                    continue

                similarity = await self._calculate_concept_similarity(name, other_name)
                if similarity > 0.85:  # High similarity threshold
                    group.append(other_name)
                    processed.add(other_name)

            groups.append(group)

        return groups

    async def _calculate_concept_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two concept names"""
        name1_lower = name1.lower().strip()
        name2_lower = name2.lower().strip()

        # Exact match
        if name1_lower == name2_lower:
            return 1.0

        # Check if one is substring of other
        if name1_lower in name2_lower or name2_lower in name1_lower:
            return 0.9

        # Token overlap
        tokens1 = set(name1_lower.split())
        tokens2 = set(name2_lower.split())

        if not tokens1 or not tokens2:
            return 0.0

        overlap = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)

        return overlap / union if union > 0 else 0.0

    async def _consolidate_concept_group(
        self,
        concepts: List,
        strategy: ConflictResolutionStrategy
    ) -> ConsolidatedConcept:
        """Consolidate a group of similar concepts"""
        # Choose canonical name (most common or highest confidence)
        canonical_name = max(
            concepts,
            key=lambda c: c.confidence * c.access_count
        ).name

        # Collect all aliases
        aliases = {c.name for c in concepts if c.name != canonical_name}

        # Aggregate sources (placeholder - would track actual sources)
        sources = []

        # Calculate consolidated confidence
        avg_confidence = sum(c.confidence for c in concepts) / len(concepts)

        consolidated = ConsolidatedConcept(
            concept_id=concepts[0].id,
            canonical_name=canonical_name,
            aliases=aliases,
            sources=sources,
            confidence=avg_confidence,
            consolidation_count=len(concepts)
        )

        # Record consolidation
        self.consolidation_history.append({
            'timestamp': datetime.now(),
            'canonical_name': canonical_name,
            'merged_concepts': [c.name for c in concepts],
            'strategy': strategy.value
        })

        logger.info(f"Consolidated {len(concepts)} concepts into: {canonical_name}")

        return consolidated

    async def detect_conflicts(
        self,
        concept_id: str
    ) -> List[ConflictingInformation]:
        """Detect conflicting information about a concept"""
        conflicts = []

        concept = self.knowledge_graph.concepts.get(concept_id)
        if not concept:
            return conflicts

        # Check for conflicting relationships
        outgoing = self.knowledge_graph.outgoing_edges.get(concept_id, [])

        # Group relationships by type
        from collections import defaultdict
        rel_by_type = defaultdict(list)

        for edge_id in outgoing:
            rel = self.knowledge_graph.relationships.get(edge_id)
            if rel:
                rel_by_type[rel.relation_type].append(rel)

        # Detect conflicting relationships of same type
        for rel_type, rels in rel_by_type.items():
            if len(rels) > 1:
                # Check if they point to different targets
                targets = {r.target_id for r in rels}
                if len(targets) > 1:
                    conflict = ConflictingInformation(
                        concept_id=concept_id,
                        field_name=f"relationship_{rel_type.value}",
                        values=[(r.target_id, None, r.strength) for r in rels]
                    )
                    conflicts.append(conflict)

        return conflicts

    async def resolve_conflict(
        self,
        conflict: ConflictingInformation
    ) -> any:
        """Resolve a conflicting piece of information"""
        if conflict.resolved:
            return conflict.resolved_value

        strategy = conflict.resolution_strategy

        if strategy == ConflictResolutionStrategy.HIGHEST_CONFIDENCE:
            # Choose value with highest confidence
            best = max(conflict.values, key=lambda x: x[2])
            resolved_value = best[0]

        elif strategy == ConflictResolutionStrategy.MOST_RECENT:
            # Choose most recent value (would need timestamps)
            resolved_value = conflict.values[-1][0]

        elif strategy == ConflictResolutionStrategy.MOST_SOURCES:
            # Count occurrences of each value
            from collections import Counter
            value_counts = Counter(v[0] for v in conflict.values)
            resolved_value = value_counts.most_common(1)[0][0]

        else:  # MANUAL_REVIEW
            # Mark for manual review
            logger.warning(f"Conflict requires manual review: {conflict.concept_id}")
            return None

        conflict.resolved = True
        conflict.resolved_value = resolved_value

        logger.info(f"Resolved conflict for {conflict.concept_id}: {resolved_value}")

        return resolved_value

    async def validate_cross_references(
        self,
        concept_id: str,
        max_depth: int = 2
    ) -> Dict[str, bool]:
        """
        Validate cross-references in the knowledge graph.

        Args:
            concept_id: Starting concept
            max_depth: Maximum depth to traverse

        Returns:
            Dictionary of validation results
        """
        results = {
            'valid': True,
            'orphaned_references': [],
            'circular_references': [],
            'broken_links': []
        }

        visited = set()
        path = []

        async def validate_recursive(cid: str, depth: int):
            if depth > max_depth:
                return

            if cid in path:
                # Circular reference detected
                results['circular_references'].append(path + [cid])
                results['valid'] = False
                return

            if cid in visited:
                return

            visited.add(cid)
            path.append(cid)

            # Check if concept exists
            concept = self.knowledge_graph.concepts.get(cid)
            if not concept:
                results['broken_links'].append(cid)
                results['valid'] = False
                path.pop()
                return

            # Check outgoing relationships
            for edge_id in self.knowledge_graph.outgoing_edges.get(cid, []):
                rel = self.knowledge_graph.relationships.get(edge_id)
                if rel:
                    # Validate target exists
                    if rel.target_id not in self.knowledge_graph.concepts:
                        results['broken_links'].append(rel.target_id)
                        results['valid'] = False
                    else:
                        await validate_recursive(rel.target_id, depth + 1)

            path.pop()

        await validate_recursive(concept_id, 0)

        return results

    async def consolidate_from_sources(
        self,
        topic: str,
        sources: List[KnowledgeSource],
        max_concepts: int = 100
    ) -> ConsolidatedConcept:
        """
        Consolidate knowledge about a topic from multiple sources.

        Args:
            topic: Topic to consolidate
            sources: List of knowledge sources
            max_concepts: Maximum number of concepts to process

        Returns:
            Consolidated concept
        """
        # Get all concepts related to topic
        related_concepts = []

        for concept_id, concept in self.knowledge_graph.concepts.items():
            if topic.lower() in concept.name.lower():
                related_concepts.append(concept)

            if len(related_concepts) >= max_concepts:
                break

        if not related_concepts:
            logger.warning(f"No concepts found for topic: {topic}")
            return None

        # Consolidate related concepts
        consolidated = await self._consolidate_concept_group(
            related_concepts,
            ConflictResolutionStrategy.HIGHEST_CONFIDENCE
        )

        # Add source information
        consolidated.sources = sources

        return consolidated

    def get_consolidation_stats(self) -> Dict[str, any]:
        """Get statistics about consolidation operations"""
        return {
            'total_sources': len(self.sources),
            'consolidation_operations': len(self.consolidation_history),
            'active_conflicts': len([c for c in self.conflicts if not c.resolved]),
            'resolved_conflicts': len([c for c in self.conflicts if c.resolved]),
            'source_breakdown': {
                level.name: len([s for s in self.sources.values() if s.credibility == level])
                for level in SourceCredibility
            }
        }


async def demo():
    """Demo knowledge consolidation"""
    from src.learning.knowledge_graph import KnowledgeGraph

    kg = KnowledgeGraph()
    consolidator = KnowledgeConsolidator(kg)

    # Register sources
    await consolidator.register_source(
        "wikipedia",
        "Wikipedia",
        "https://wikipedia.org",
        SourceCredibility.RELIABLE
    )

    await consolidator.register_source(
        "research_paper",
        "Academic Paper",
        None,
        SourceCredibility.VERIFIED
    )

    # Add some test concepts
    await kg.add_concept("Machine Learning", "technology", "AI subfield")
    await kg.add_concept("ML", "technology", "Machine learning abbreviation")
    await kg.add_concept("machine learning", "technology", "Same as ML")

    # Consolidate
    concepts = ["Machine Learning", "ML", "machine learning"]
    consolidated = await consolidator.consolidate_concepts(concepts)

    print(f"\nConsolidated {len(concepts)} concepts:")
    for c in consolidated:
        print(f"  {c.canonical_name}")
        print(f"    Aliases: {c.aliases}")
        print(f"    Confidence: {c.confidence:.2f}")

    # Stats
    stats = consolidator.get_consolidation_stats()
    print(f"\nConsolidation Stats:")
    print(f"  Total sources: {stats['total_sources']}")
    print(f"  Operations: {stats['consolidation_operations']}")


if __name__ == "__main__":
    asyncio.run(demo())
