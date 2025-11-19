"""
Creative Synthesis Engine for Claude-AGI
=========================================

Advanced creative synthesis capabilities that combine disparate concepts,
memories, and ideas to generate novel insights and creative outputs.

Features:
- Conceptual blending and fusion
- Analogical reasoning and transfer
- Novel pattern generation
- Cross-domain creativity
- Constraint-based creativity
- Generative ideation
"""

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class SynthesisStrategy(Enum):
    """Strategies for creative synthesis"""
    BLEND = "blend"  # Blend two concepts
    TRANSFORM = "transform"  # Transform a concept
    CONTRAST = "contrast"  # Combine contrasting ideas
    ABSTRACT = "abstract"  # Abstract from specifics
    ANALOGIZE = "analogize"  # Find analogies
    RECOMBINE = "recombine"  # Recombine elements


class NoveltyLevel(Enum):
    """Novelty levels for generated ideas"""
    INCREMENTAL = "incremental"  # Small variation
    MODERATE = "moderate"  # Notable change
    RADICAL = "radical"  # Highly novel
    TRANSFORMATIVE = "transformative"  # Paradigm shift


@dataclass
class Concept:
    """Represents a concept for synthesis"""
    concept_id: str
    name: str
    domain: str  # Domain (e.g., "science", "art", "philosophy")
    attributes: Dict[str, Any] = field(default_factory=dict)
    relations: List[str] = field(default_factory=list)  # Related concept IDs
    examples: List[str] = field(default_factory=list)


@dataclass
class CreativeSynthesis:
    """Result of creative synthesis"""
    synthesis_id: str
    strategy: SynthesisStrategy
    source_concepts: List[str]  # Concept IDs
    synthesized_concept: str
    description: str
    novelty_level: NoveltyLevel
    confidence: float  # 0.0-1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Analogy:
    """Represents an analogy between domains"""
    analogy_id: str
    source_domain: str
    target_domain: str
    source_concept: str
    target_concept: str
    mapping: Dict[str, str]  # Source attribute -> Target attribute
    strength: float  # 0.0-1.0
    explanation: str = ""


class CreativeSynthesisEngine:
    """
    Generates novel ideas through creative synthesis.

    Combines concepts, finds analogies, and generates novel patterns
    to enable creative thinking and problem-solving.
    """

    def __init__(self):
        # Concept storage
        self.concepts: Dict[str, Concept] = {}

        # Synthesis history
        self.syntheses: List[CreativeSynthesis] = []

        # Analogies
        self.analogies: List[Analogy] = []

        # Domain knowledge
        self.domains: Set[str] = set()

        # Synthesis templates
        self.templates = self._initialize_templates()

        # Statistics
        self.stats = {
            'total_syntheses': 0,
            'syntheses_by_strategy': {},
            'syntheses_by_novelty': {}
        }

    def _initialize_templates(self) -> Dict[SynthesisStrategy, List[str]]:
        """Initialize synthesis templates"""
        return {
            SynthesisStrategy.BLEND: [
                "What if we combined {concept1} with {concept2}?",
                "Imagine {concept1} having the properties of {concept2}",
                "A fusion of {concept1} and {concept2} could be..."
            ],
            SynthesisStrategy.TRANSFORM: [
                "What if {concept1} were transformed by {attribute}?",
                "How would {concept1} change if {constraint}?",
                "{concept1} reimagined as {new_form}"
            ],
            SynthesisStrategy.CONTRAST: [
                "Combining opposite ideas: {concept1} meets {concept2}",
                "Reconciling {concept1} and {concept2}",
                "What emerges from the tension between {concept1} and {concept2}?"
            ],
            SynthesisStrategy.ABSTRACT: [
                "The underlying pattern in {concept1} is...",
                "Abstracting from {concept1}, we get...",
                "The essence of {concept1} applied universally"
            ],
            SynthesisStrategy.ANALOGIZE: [
                "{concept1} in {domain1} is like {concept2} in {domain2}",
                "Drawing parallels between {concept1} and {concept2}",
                "Transferring principles from {concept1} to {concept2}"
            ]
        }

    async def add_concept(
        self,
        concept_id: str,
        name: str,
        domain: str,
        attributes: Optional[Dict[str, Any]] = None,
        examples: Optional[List[str]] = None
    ) -> Concept:
        """
        Add a concept to the synthesis engine

        Args:
            concept_id: Unique identifier
            name: Concept name
            domain: Conceptual domain
            attributes: Concept attributes
            examples: Example instances

        Returns:
            Created Concept
        """
        concept = Concept(
            concept_id=concept_id,
            name=name,
            domain=domain,
            attributes=attributes or {},
            examples=examples or []
        )

        self.concepts[concept_id] = concept
        self.domains.add(domain)

        logger.info(f"Added concept: {name} ({domain})")
        return concept

    async def blend_concepts(
        self,
        concept1_id: str,
        concept2_id: str,
        blend_ratio: float = 0.5
    ) -> Optional[CreativeSynthesis]:
        """
        Blend two concepts to create a novel hybrid

        Args:
            concept1_id: First concept ID
            concept2_id: Second concept ID
            blend_ratio: Ratio of influence (0.0-1.0)

        Returns:
            CreativeSynthesis result
        """
        concept1 = self.concepts.get(concept1_id)
        concept2 = self.concepts.get(concept2_id)

        if not concept1 or not concept2:
            return None

        # Generate blended concept
        blended_name = f"{concept1.name}-{concept2.name} Hybrid"

        # Combine attributes with weighting
        blended_attributes = {}
        all_attrs = set(concept1.attributes.keys()) | set(concept2.attributes.keys())

        for attr in all_attrs:
            if attr in concept1.attributes and attr in concept2.attributes:
                # Both have attribute - blend
                blended_attributes[attr] = {
                    'from_concept1': concept1.attributes[attr],
                    'from_concept2': concept2.attributes[attr],
                    'blend': f"Combination of {concept1.name} and {concept2.name} {attr}"
                }
            elif attr in concept1.attributes:
                blended_attributes[attr] = concept1.attributes[attr]
            else:
                blended_attributes[attr] = concept2.attributes[attr]

        # Determine novelty
        cross_domain = concept1.domain != concept2.domain
        novelty_level = (
            NoveltyLevel.RADICAL if cross_domain
            else NoveltyLevel.MODERATE
        )

        # Create description
        template = random.choice(self.templates[SynthesisStrategy.BLEND])
        description = template.format(
            concept1=concept1.name,
            concept2=concept2.name
        )

        # Create synthesis
        import uuid
        synthesis = CreativeSynthesis(
            synthesis_id=str(uuid.uuid4()),
            strategy=SynthesisStrategy.BLEND,
            source_concepts=[concept1_id, concept2_id],
            synthesized_concept=blended_name,
            description=description,
            novelty_level=novelty_level,
            confidence=0.7 if cross_domain else 0.8,
            properties=blended_attributes
        )

        self.syntheses.append(synthesis)
        self._update_stats(synthesis)

        logger.info(f"Blended concepts: {blended_name}")
        return synthesis

    async def find_analogy(
        self,
        source_concept_id: str,
        target_domain: str,
        min_similarity: float = 0.3
    ) -> Optional[Analogy]:
        """
        Find analogies between concepts in different domains

        Args:
            source_concept_id: Source concept to map
            target_domain: Target domain to find analogy
            min_similarity: Minimum similarity threshold

        Returns:
            Analogy if found
        """
        source = self.concepts.get(source_concept_id)
        if not source:
            return None

        # Find concepts in target domain
        target_concepts = [
            c for c in self.concepts.values()
            if c.domain == target_domain
        ]

        if not target_concepts:
            return None

        # Find best matching concept based on structural similarity
        best_match = None
        best_score = 0.0
        best_mapping = {}

        for target in target_concepts:
            # Calculate structural similarity
            common_attrs = set(source.attributes.keys()) & set(target.attributes.keys())

            if not common_attrs:
                continue

            # Simple similarity based on shared attribute structure
            similarity = len(common_attrs) / max(
                len(source.attributes),
                len(target.attributes)
            )

            if similarity > best_score and similarity >= min_similarity:
                best_score = similarity
                best_match = target

                # Create attribute mapping
                best_mapping = {
                    attr: attr for attr in common_attrs
                }

        if not best_match:
            return None

        # Create analogy
        import uuid
        analogy = Analogy(
            analogy_id=str(uuid.uuid4()),
            source_domain=source.domain,
            target_domain=target_domain,
            source_concept=source.name,
            target_concept=best_match.name,
            mapping=best_mapping,
            strength=best_score,
            explanation=f"{source.name} in {source.domain} is analogous to {best_match.name} in {target_domain}"
        )

        self.analogies.append(analogy)

        logger.info(f"Found analogy: {source.name} -> {best_match.name} (strength: {best_score:.2f})")
        return analogy

    async def generate_by_constraint(
        self,
        base_concept_id: str,
        constraints: Dict[str, Any]
    ) -> Optional[CreativeSynthesis]:
        """
        Generate creative variations by applying constraints

        Args:
            base_concept_id: Base concept to transform
            constraints: Constraints to apply

        Returns:
            CreativeSynthesis result
        """
        base = self.concepts.get(base_concept_id)
        if not base:
            return None

        # Apply constraints to generate variant
        variant_name = f"{base.name} (constrained)"

        # Modify attributes based on constraints
        modified_attributes = base.attributes.copy()
        for constraint_key, constraint_value in constraints.items():
            if constraint_key in modified_attributes:
                modified_attributes[constraint_key] = constraint_value
            else:
                modified_attributes[f"new_{constraint_key}"] = constraint_value

        # Determine novelty based on constraint impact
        num_changed = len(constraints)
        if num_changed >= 3:
            novelty_level = NoveltyLevel.RADICAL
        elif num_changed == 2:
            novelty_level = NoveltyLevel.MODERATE
        else:
            novelty_level = NoveltyLevel.INCREMENTAL

        # Create description
        constraint_desc = ", ".join(f"{k}={v}" for k, v in list(constraints.items())[:3])
        description = f"{base.name} transformed with constraints: {constraint_desc}"

        # Create synthesis
        import uuid
        synthesis = CreativeSynthesis(
            synthesis_id=str(uuid.uuid4()),
            strategy=SynthesisStrategy.TRANSFORM,
            source_concepts=[base_concept_id],
            synthesized_concept=variant_name,
            description=description,
            novelty_level=novelty_level,
            confidence=0.75,
            properties=modified_attributes
        )

        self.syntheses.append(synthesis)
        self._update_stats(synthesis)

        logger.info(f"Generated constrained variant: {variant_name}")
        return synthesis

    async def abstract_pattern(
        self,
        concept_ids: List[str]
    ) -> Optional[CreativeSynthesis]:
        """
        Abstract a common pattern from multiple concepts

        Args:
            concept_ids: Concepts to abstract from

        Returns:
            CreativeSynthesis with abstracted pattern
        """
        if len(concept_ids) < 2:
            return None

        concepts = [self.concepts.get(cid) for cid in concept_ids]
        concepts = [c for c in concepts if c is not None]

        if len(concepts) < 2:
            return None

        # Find common attributes
        common_attrs = set(concepts[0].attributes.keys())
        for concept in concepts[1:]:
            common_attrs &= set(concept.attributes.keys())

        if not common_attrs:
            return None

        # Create abstract pattern
        pattern_name = f"Abstract Pattern from {len(concepts)} Concepts"

        # Extract common attribute values
        abstracted_attributes = {}
        for attr in common_attrs:
            values = [c.attributes[attr] for c in concepts]
            # Create abstraction description
            abstracted_attributes[attr] = {
                'pattern': f"Common {attr} across concepts",
                'instances': values[:3]  # Sample instances
            }

        # Create description
        concept_names = ", ".join(c.name for c in concepts[:3])
        description = f"Abstract pattern extracted from: {concept_names}"

        # Create synthesis
        import uuid
        synthesis = CreativeSynthesis(
            synthesis_id=str(uuid.uuid4()),
            strategy=SynthesisStrategy.ABSTRACT,
            source_concepts=concept_ids,
            synthesized_concept=pattern_name,
            description=description,
            novelty_level=NoveltyLevel.MODERATE,
            confidence=0.65,
            properties=abstracted_attributes
        )

        self.syntheses.append(synthesis)
        self._update_stats(synthesis)

        logger.info(f"Abstracted pattern from {len(concepts)} concepts")
        return synthesis

    async def recombine_elements(
        self,
        concept_ids: List[str],
        num_combinations: int = 3
    ) -> List[CreativeSynthesis]:
        """
        Generate creative recombinations of concept elements

        Args:
            concept_ids: Concepts to recombine
            num_combinations: Number of combinations to generate

        Returns:
            List of CreativeSynthesis results
        """
        concepts = [self.concepts.get(cid) for cid in concept_ids]
        concepts = [c for c in concepts if c is not None]

        if len(concepts) < 2:
            return []

        results = []

        for i in range(num_combinations):
            # Randomly select elements from different concepts
            selected_concepts = random.sample(concepts, min(3, len(concepts)))

            # Combine attributes from selected concepts
            combined_name = " + ".join(c.name for c in selected_concepts)

            combined_attributes = {}
            for concept in selected_concepts:
                for attr, value in concept.attributes.items():
                    if attr not in combined_attributes:
                        combined_attributes[attr] = []
                    combined_attributes[attr].append({
                        'from': concept.name,
                        'value': value
                    })

            # Determine novelty
            num_sources = len(selected_concepts)
            if num_sources >= 3:
                novelty_level = NoveltyLevel.RADICAL
            else:
                novelty_level = NoveltyLevel.MODERATE

            description = f"Recombination #{i+1}: {combined_name}"

            # Create synthesis
            import uuid
            synthesis = CreativeSynthesis(
                synthesis_id=str(uuid.uuid4()),
                strategy=SynthesisStrategy.RECOMBINE,
                source_concepts=[c.concept_id for c in selected_concepts],
                synthesized_concept=combined_name,
                description=description,
                novelty_level=novelty_level,
                confidence=0.6,
                properties=combined_attributes
            )

            results.append(synthesis)
            self.syntheses.append(synthesis)
            self._update_stats(synthesis)

        logger.info(f"Generated {len(results)} recombinations")
        return results

    async def generate_creative_ideas(
        self,
        theme: str,
        num_ideas: int = 5,
        strategies: Optional[List[SynthesisStrategy]] = None
    ) -> List[CreativeSynthesis]:
        """
        Generate creative ideas around a theme using various strategies

        Args:
            theme: Theme or prompt for idea generation
            num_ideas: Number of ideas to generate
            strategies: Synthesis strategies to use (None = all)

        Returns:
            List of generated ideas
        """
        if strategies is None:
            strategies = list(SynthesisStrategy)

        ideas = []

        # Get relevant concepts (simplified - in production, would use semantic search)
        relevant_concepts = list(self.concepts.values())[:10]

        if not relevant_concepts:
            logger.warning("No concepts available for idea generation")
            return []

        for _ in range(num_ideas):
            # Select random strategy
            strategy = random.choice(strategies)

            # Generate based on strategy
            if strategy == SynthesisStrategy.BLEND and len(relevant_concepts) >= 2:
                sample = random.sample(relevant_concepts, 2)
                idea = await self.blend_concepts(sample[0].concept_id, sample[1].concept_id)

            elif strategy == SynthesisStrategy.TRANSFORM:
                base = random.choice(relevant_concepts)
                constraints = {'theme': theme, 'variation': random.randint(1, 5)}
                idea = await self.generate_by_constraint(base.concept_id, constraints)

            elif strategy == SynthesisStrategy.ABSTRACT and len(relevant_concepts) >= 3:
                sample = random.sample(relevant_concepts, min(3, len(relevant_concepts)))
                idea = await self.abstract_pattern([c.concept_id for c in sample])

            elif strategy == SynthesisStrategy.RECOMBINE and len(relevant_concepts) >= 2:
                sample = random.sample(relevant_concepts, min(4, len(relevant_concepts)))
                combos = await self.recombine_elements([c.concept_id for c in sample], 1)
                idea = combos[0] if combos else None

            else:
                continue

            if idea:
                ideas.append(idea)

        logger.info(f"Generated {len(ideas)} creative ideas for theme: {theme}")
        return ideas

    def _update_stats(self, synthesis: CreativeSynthesis):
        """Update statistics"""
        self.stats['total_syntheses'] += 1

        strategy_key = synthesis.strategy.value
        self.stats['syntheses_by_strategy'][strategy_key] = (
            self.stats['syntheses_by_strategy'].get(strategy_key, 0) + 1
        )

        novelty_key = synthesis.novelty_level.value
        self.stats['syntheses_by_novelty'][novelty_key] = (
            self.stats['syntheses_by_novelty'].get(novelty_key, 0) + 1
        )

    async def get_statistics(self) -> Dict[str, Any]:
        """Get synthesis statistics"""
        avg_confidence = (
            sum(s.confidence for s in self.syntheses) / len(self.syntheses)
            if self.syntheses else 0.0
        )

        return {
            'total_concepts': len(self.concepts),
            'total_domains': len(self.domains),
            'total_syntheses': self.stats['total_syntheses'],
            'syntheses_by_strategy': dict(self.stats['syntheses_by_strategy']),
            'syntheses_by_novelty': dict(self.stats['syntheses_by_novelty']),
            'total_analogies': len(self.analogies),
            'avg_synthesis_confidence': round(avg_confidence, 3)
        }
