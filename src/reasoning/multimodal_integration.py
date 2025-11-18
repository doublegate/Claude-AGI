"""
Multi-Modal Integration for Claude-AGI
=======================================

Integrates knowledge and reasoning across multiple domains:
- Cross-domain pattern recognition
- Knowledge transfer between modalities
- Holistic understanding development
- Domain boundary traversal
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class KnowledgeDomain(Enum):
    """Different knowledge domains"""
    LINGUISTIC = "linguistic"
    LOGICAL = "logical"
    MATHEMATICAL = "mathematical"
    SPATIAL = "spatial"
    MUSICAL = "musical"
    BODILY_KINESTHETIC = "bodily_kinesthetic"
    INTERPERSONAL = "interpersonal"
    INTRAPERSONAL = "intrapersonal"
    NATURALISTIC = "naturalistic"
    EXISTENTIAL = "existential"


@dataclass
class DomainConcept:
    """Concept in a specific domain"""
    concept_id: str
    domain: KnowledgeDomain
    content: str
    properties: Dict[str, Any] = field(default_factory=dict)
    connections: List[str] = field(default_factory=list)


@dataclass
class CrossDomainMapping:
    """Mapping between concepts in different domains"""
    mapping_id: str
    source_domain: KnowledgeDomain
    target_domain: KnowledgeDomain
    source_concept: str
    target_concept: str
    mapping_type: str  # analogy, transformation, abstraction
    confidence: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)


class MultiModalIntegrator:
    """
    Integrates knowledge across multiple domains and modalities.

    Enables the system to:
    - Recognize patterns that span domains
    - Transfer knowledge between modalities
    - Build holistic understanding
    - Make cross-domain analogies
    """

    def __init__(self):
        # Domain-specific knowledge
        self.domain_concepts: Dict[KnowledgeDomain, Dict[str, DomainConcept]] = defaultdict(dict)

        # Cross-domain mappings
        self.mappings: List[CrossDomainMapping] = []
        self.mapping_index: Dict[Tuple[KnowledgeDomain, KnowledgeDomain], List[CrossDomainMapping]] = defaultdict(list)

        # Pattern library (patterns that appear across domains)
        self.cross_domain_patterns: List[Dict[str, Any]] = []

    async def add_concept(
        self,
        domain: KnowledgeDomain,
        concept_id: str,
        content: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> DomainConcept:
        """Add a concept to a domain"""
        concept = DomainConcept(
            concept_id=concept_id,
            domain=domain,
            content=content,
            properties=properties or {}
        )

        self.domain_concepts[domain][concept_id] = concept
        logger.info(f"Added concept to {domain.value}: {content}")

        # Auto-detect potential cross-domain connections
        await self._detect_cross_domain_patterns(concept)

        return concept

    async def create_mapping(
        self,
        source_domain: KnowledgeDomain,
        target_domain: KnowledgeDomain,
        source_concept: str,
        target_concept: str,
        mapping_type: str = "analogy",
        confidence: float = 0.7
    ) -> CrossDomainMapping:
        """Create a mapping between concepts in different domains"""
        import uuid

        mapping = CrossDomainMapping(
            mapping_id=str(uuid.uuid4()),
            source_domain=source_domain,
            target_domain=target_domain,
            source_concept=source_concept,
            target_concept=target_concept,
            mapping_type=mapping_type,
            confidence=confidence
        )

        self.mappings.append(mapping)
        self.mapping_index[(source_domain, target_domain)].append(mapping)

        logger.info(f"Created {mapping_type} mapping: {source_domain.value}.{source_concept} -> {target_domain.value}.{target_concept}")

        return mapping

    async def find_analogies(
        self,
        concept_id: str,
        source_domain: KnowledgeDomain,
        target_domain: KnowledgeDomain
    ) -> List[CrossDomainMapping]:
        """Find analogies for a concept in another domain"""
        # Look for existing mappings
        domain_pair = (source_domain, target_domain)
        relevant_mappings = [
            m for m in self.mapping_index.get(domain_pair, [])
            if m.source_concept == concept_id
        ]

        # If no mappings exist, try to create new ones
        if not relevant_mappings:
            source_concept = self.domain_concepts[source_domain].get(concept_id)
            if source_concept:
                # Find structurally similar concepts in target domain
                similar = await self._find_structural_similarity(source_concept, target_domain)
                for target_id, similarity in similar:
                    if similarity > 0.6:
                        mapping = await self.create_mapping(
                            source_domain,
                            target_domain,
                            concept_id,
                            target_id,
                            mapping_type="analogy",
                            confidence=similarity
                        )
                        relevant_mappings.append(mapping)

        return relevant_mappings

    async def _find_structural_similarity(
        self,
        source_concept: DomainConcept,
        target_domain: KnowledgeDomain
    ) -> List[Tuple[str, float]]:
        """Find structurally similar concepts in target domain"""
        similar_concepts = []

        target_concepts = self.domain_concepts[target_domain]
        for target_id, target_concept in target_concepts.items():
            # Compare properties
            similarity = await self._calculate_structural_similarity(
                source_concept.properties,
                target_concept.properties
            )

            if similarity > 0:
                similar_concepts.append((target_id, similarity))

        similar_concepts.sort(key=lambda x: x[1], reverse=True)
        return similar_concepts[:5]  # Top 5 matches

    async def _calculate_structural_similarity(
        self,
        props_a: Dict[str, Any],
        props_b: Dict[str, Any]
    ) -> float:
        """Calculate similarity based on structural properties"""
        if not props_a or not props_b:
            return 0.0

        # Check for common keys
        common_keys = set(props_a.keys()) & set(props_b.keys())
        if not common_keys:
            return 0.0

        # Calculate similarity for common properties
        similarities = []
        for key in common_keys:
            val_a, val_b = props_a[key], props_b[key]

            # Handle different value types
            if type(val_a) == type(val_b):
                if isinstance(val_a, (int, float)):
                    # Numerical similarity
                    if val_a == 0 and val_b == 0:
                        sim = 1.0
                    else:
                        diff = abs(val_a - val_b)
                        max_val = max(abs(val_a), abs(val_b))
                        sim = 1.0 - (diff / max_val) if max_val > 0 else 1.0
                elif isinstance(val_a, str):
                    # String similarity (simple)
                    sim = 1.0 if val_a.lower() == val_b.lower() else 0.3
                else:
                    sim = 1.0 if val_a == val_b else 0.0

                similarities.append(sim)

        return sum(similarities) / len(similarities) if similarities else 0.0

    async def _detect_cross_domain_patterns(self, concept: DomainConcept):
        """Detect patterns that might exist across domains"""
        # Look for concepts in other domains with similar structure
        for other_domain in KnowledgeDomain:
            if other_domain == concept.domain:
                continue

            other_concepts = self.domain_concepts[other_domain]
            for other_id, other_concept in other_concepts.items():
                similarity = await self._calculate_structural_similarity(
                    concept.properties,
                    other_concept.properties
                )

                if similarity > 0.7:
                    # Found potential cross-domain pattern
                    await self.create_mapping(
                        concept.domain,
                        other_domain,
                        concept.concept_id,
                        other_id,
                        mapping_type="pattern_match",
                        confidence=similarity
                    )

    async def transfer_knowledge(
        self,
        concept_id: str,
        from_domain: KnowledgeDomain,
        to_domain: KnowledgeDomain
    ) -> Optional[DomainConcept]:
        """Transfer knowledge from one domain to another"""
        # Find the source concept
        source = self.domain_concepts[from_domain].get(concept_id)
        if not source:
            return None

        # Find existing mappings
        analogies = await self.find_analogies(concept_id, from_domain, to_domain)

        if analogies:
            # Use existing mapping
            mapping = analogies[0]
            target_id = mapping.target_concept
            target = self.domain_concepts[to_domain].get(target_id)
            if target:
                logger.info(f"Knowledge transferred: {from_domain.value}.{concept_id} -> {to_domain.value}.{target_id}")
                return target

        # Create new concept in target domain
        new_concept = await self.add_concept(
            to_domain,
            f"transferred_{concept_id}",
            f"Transferred from {from_domain.value}: {source.content}",
            properties=source.properties.copy()
        )

        return new_concept

    async def get_holistic_view(self, concept_id: str, domain: KnowledgeDomain) -> Dict[str, Any]:
        """Get holistic view of a concept across all domains"""
        source_concept = self.domain_concepts[domain].get(concept_id)
        if not source_concept:
            return {}

        view = {
            'source': {
                'domain': domain.value,
                'concept': source_concept.content,
                'properties': source_concept.properties
            },
            'related_domains': {}
        }

        # Find connections in all other domains
        for other_domain in KnowledgeDomain:
            if other_domain == domain:
                continue

            analogies = await self.find_analogies(concept_id, domain, other_domain)
            if analogies:
                view['related_domains'][other_domain.value] = [
                    {
                        'concept': m.target_concept,
                        'type': m.mapping_type,
                        'confidence': m.confidence
                    }
                    for m in analogies
                ]

        return view

    async def get_statistics(self) -> Dict[str, Any]:
        """Get multi-modal integration statistics"""
        domain_counts = {
            domain.value: len(concepts)
            for domain, concepts in self.domain_concepts.items()
        }

        return {
            'total_concepts': sum(len(c) for c in self.domain_concepts.values()),
            'concepts_per_domain': domain_counts,
            'total_mappings': len(self.mappings),
            'cross_domain_patterns': len(self.cross_domain_patterns),
            'domains_with_content': len(self.domain_concepts)
        }
