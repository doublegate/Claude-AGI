"""
Dream Simulation System for Claude-AGI
=======================================

Implements dream-like cognitive processes including:
- Free association between unrelated concepts
- Memory recombination and creative synthesis
- Symbolic and metaphorical processing
- Insight generation through pattern emergence
- Creative problem solving via unconscious processing
"""

import asyncio
import logging
import random
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class DreamPhase(Enum):
    """Phases of dream simulation (inspired by sleep stages)"""
    LIGHT = "light"  # Gentle connections, recent memories
    DEEP = "deep"  # More abstract, distant associations
    REM = "rem"  # Vivid, creative, emotionally charged
    HYPNAGOGIC = "hypnagogic"  # Transitional, surreal


class SymbolType(Enum):
    """Types of symbolic content"""
    METAPHOR = "metaphor"
    ARCHETYPE = "archetype"
    PERSONAL_SYMBOL = "personal_symbol"
    ABSTRACT_CONCEPT = "abstract_concept"
    EMOTIONAL_SYMBOL = "emotional_symbol"


@dataclass
class DreamElement:
    """A single element in a dream sequence"""
    element_id: str
    content: str
    symbol_type: SymbolType
    associations: List[str] = field(default_factory=list)
    emotional_valence: float = 0.0
    activation_level: float = 1.0
    source_memory_ids: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DreamSequence:
    """A sequence of connected dream elements"""
    sequence_id: str
    phase: DreamPhase
    elements: List[DreamElement] = field(default_factory=list)
    coherence_score: float = 0.5
    novel_connections: List[Tuple[str, str]] = field(default_factory=list)
    insights_generated: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None


@dataclass
class DreamInsight:
    """An insight generated during dream processing"""
    insight_id: str
    content: str
    confidence: float
    source_elements: List[str] = field(default_factory=list)
    practical_applications: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class DreamSimulator:
    """
    Simulates dream-like cognitive processes for creative problem solving
    and insight generation.

    Dream simulation allows the system to:
    - Make unexpected connections between concepts
    - Process experiences symbolically
    - Consolidate learning in creative ways
    - Generate insights through pattern emergence
    """

    def __init__(self):
        # Dream state
        self.current_phase: Optional[DreamPhase] = None
        self.active_dream: Optional[DreamSequence] = None

        # Memory pools for dream content
        self.recent_memories: deque = deque(maxlen=100)
        self.long_term_memories: List[Dict[str, Any]] = []
        self.emotional_memories: List[Dict[str, Any]] = []

        # Association network
        self.concept_associations: Dict[str, Set[str]] = defaultdict(set)
        self.symbol_meanings: Dict[str, List[str]] = defaultdict(list)

        # Dream history
        self.dream_sessions: deque = deque(maxlen=50)
        self.insights_discovered: List[DreamInsight] = []

        # Parameters
        self.association_strength_threshold = 0.3
        self.max_association_distance = 3  # How many hops for remote associations

    async def start_dream_session(
        self,
        duration_minutes: int = 10,
        initial_phase: DreamPhase = DreamPhase.LIGHT,
        focus_problem: Optional[str] = None
    ) -> DreamSequence:
        """
        Start a dream simulation session.

        Args:
            duration_minutes: How long to dream
            initial_phase: Starting dream phase
            focus_problem: Optional problem to process during dreaming

        Returns:
            Dream sequence generated
        """
        import uuid

        sequence = DreamSequence(
            sequence_id=str(uuid.uuid4()),
            phase=initial_phase
        )

        self.current_phase = initial_phase
        self.active_dream = sequence

        logger.info(f"Started dream session: {initial_phase.value}")

        if focus_problem:
            sequence.insights_generated.append(f"Focusing on: {focus_problem}")

        # Generate dream content
        await self._generate_dream_content(sequence, duration_minutes, focus_problem)

        # Extract insights
        insights = await self._extract_insights(sequence)
        sequence.insights_generated.extend([i.content for i in insights])
        self.insights_discovered.extend(insights)

        # Complete session
        sequence.end_time = datetime.now()
        self.dream_sessions.append(sequence)
        self.active_dream = None
        self.current_phase = None

        logger.info(f"Completed dream session: {len(sequence.elements)} elements, {len(insights)} insights")

        return sequence

    async def _generate_dream_content(
        self,
        sequence: DreamSequence,
        duration: int,
        focus: Optional[str]
    ):
        """Generate dream content through free association"""
        # Estimate number of elements based on duration and phase
        phase_speeds = {
            DreamPhase.LIGHT: 3,  # 3 elements per minute
            DreamPhase.DEEP: 2,  # Slower, more abstract
            DreamPhase.REM: 5,  # Faster, more vivid
            DreamPhase.HYPNAGOGIC: 4  # Moderate speed, surreal
        }

        num_elements = duration * phase_speeds[sequence.phase]

        # Start with seed concept
        if focus:
            seed_concept = focus
        elif self.recent_memories:
            seed_concept = random.choice(list(self.recent_memories))['content']
        else:
            seed_concept = "exploration"

        # Generate elements through free association
        current_concept = seed_concept

        for i in range(num_elements):
            element = await self._create_dream_element(
                current_concept,
                sequence.phase,
                element_index=i
            )

            sequence.elements.append(element)

            # Free associate to next concept
            current_concept = await self._free_associate(current_concept, sequence.phase)

            # Occasionally make distant connections (REM phase)
            if sequence.phase == DreamPhase.REM and random.random() < 0.3:
                distant_concept = await self._find_distant_association(current_concept)
                if distant_concept:
                    sequence.novel_connections.append((current_concept, distant_concept))
                    current_concept = distant_concept

    async def _create_dream_element(
        self,
        concept: str,
        phase: DreamPhase,
        element_index: int
    ) -> DreamElement:
        """Create a single dream element"""
        import uuid

        # Determine symbol type based on phase
        symbol_type_weights = {
            DreamPhase.LIGHT: {
                SymbolType.PERSONAL_SYMBOL: 0.5,
                SymbolType.METAPHOR: 0.3,
                SymbolType.ABSTRACT_CONCEPT: 0.2
            },
            DreamPhase.DEEP: {
                SymbolType.ABSTRACT_CONCEPT: 0.4,
                SymbolType.ARCHETYPE: 0.3,
                SymbolType.METAPHOR: 0.3
            },
            DreamPhase.REM: {
                SymbolType.METAPHOR: 0.4,
                SymbolType.EMOTIONAL_SYMBOL: 0.3,
                SymbolType.ARCHETYPE: 0.3
            },
            DreamPhase.HYPNAGOGIC: {
                SymbolType.ABSTRACT_CONCEPT: 0.5,
                SymbolType.METAPHOR: 0.5
            }
        }

        weights = symbol_type_weights[phase]
        symbol_type = random.choices(
            list(weights.keys()),
            weights=list(weights.values())
        )[0]

        # Get associations
        associations = list(self.concept_associations.get(concept, set()))[:5]

        # Calculate emotional valence (REM has more extreme emotions)
        if phase == DreamPhase.REM:
            emotional_valence = random.choice([-0.8, -0.6, 0.6, 0.8])
        else:
            emotional_valence = random.uniform(-0.3, 0.3)

        element = DreamElement(
            element_id=str(uuid.uuid4()),
            content=concept,
            symbol_type=symbol_type,
            associations=associations,
            emotional_valence=emotional_valence,
            activation_level=1.0 - (element_index * 0.02)  # Gradual decay
        )

        return element

    async def _free_associate(self, concept: str, phase: DreamPhase) -> str:
        """
        Perform free association from current concept.

        Args:
            concept: Current concept
            phase: Dream phase (affects association style)

        Returns:
            Associated concept
        """
        # Get direct associations
        direct_associations = self.concept_associations.get(concept, set())

        if direct_associations and random.random() < 0.7:
            # Use direct association
            return random.choice(list(direct_associations))

        # Generate creative association
        association_patterns = {
            DreamPhase.LIGHT: self._associate_similar,
            DreamPhase.DEEP: self._associate_abstract,
            DreamPhase.REM: self._associate_metaphorical,
            DreamPhase.HYPNAGOGIC: self._associate_surreal
        }

        associate_func = association_patterns[phase]
        return await associate_func(concept)

    async def _associate_similar(self, concept: str) -> str:
        """Associate to similar concept"""
        # Simple word-based association
        words = concept.lower().split()
        if words:
            base_word = random.choice(words)
            # Add variation
            variations = [
                f"{base_word}s",
                f"un{base_word}",
                f"{base_word}ing",
                f"new {base_word}",
                f"{base_word} system"
            ]
            return random.choice(variations)
        return "related concept"

    async def _associate_abstract(self, concept: str) -> str:
        """Associate to more abstract concept"""
        abstractions = [
            f"the nature of {concept}",
            f"essence of {concept}",
            f"pattern underlying {concept}",
            f"principle of {concept}",
            f"structure of {concept}"
        ]
        return random.choice(abstractions)

    async def _associate_metaphorical(self, concept: str) -> str:
        """Associate through metaphor"""
        metaphors = [
            f"{concept} as journey",
            f"{concept} like water flowing",
            f"{concept} transforming",
            f"dance of {concept}",
            f"{concept} blooming"
        ]
        return random.choice(metaphors)

    async def _associate_surreal(self, concept: str) -> str:
        """Create surreal association"""
        surreal_elements = [
            f"inverted {concept}",
            f"{concept} dissolving into light",
            f"echo of {concept}",
            f"{concept} between dimensions",
            f"shadow-{concept}"
        ]
        return random.choice(surreal_elements)

    async def _find_distant_association(self, concept: str) -> Optional[str]:
        """Find distant (multi-hop) association"""
        if not self.concept_associations:
            return None

        current = concept
        for _ in range(self.max_association_distance):
            associations = self.concept_associations.get(current, set())
            if associations:
                current = random.choice(list(associations))
            else:
                break

        return current if current != concept else None

    async def _extract_insights(self, sequence: DreamSequence) -> List[DreamInsight]:
        """Extract insights from dream sequence"""
        insights = []

        # Look for patterns in novel connections
        for connection in sequence.novel_connections:
            concept_a, concept_b = connection

            insight_content = f"Unexpected connection: {concept_a} relates to {concept_b}"

            import uuid
            insight = DreamInsight(
                insight_id=str(uuid.uuid4()),
                content=insight_content,
                confidence=0.6,
                source_elements=[concept_a, concept_b]
            )
            insights.append(insight)

        # Look for recurring symbols
        symbol_counts = defaultdict(int)
        for element in sequence.elements:
            symbol_counts[element.symbol_type] += 1

        if symbol_counts:
            dominant_symbol = max(symbol_counts.items(), key=lambda x: x[1])
            if dominant_symbol[1] > 3:
                import uuid
                insight = DreamInsight(
                    insight_id=str(uuid.uuid4()),
                    content=f"Recurring theme: {dominant_symbol[0].value}",
                    confidence=0.7,
                    source_elements=[e.content for e in sequence.elements[:3]]
                )
                insights.append(insight)

        return insights

    async def add_memory_to_pool(
        self,
        content: str,
        is_emotional: bool = False,
        is_recent: bool = True
    ):
        """Add memory to dream processing pools"""
        memory = {
            'content': content,
            'timestamp': datetime.now(),
            'emotional': is_emotional
        }

        if is_recent:
            self.recent_memories.append(memory)

        if is_emotional:
            self.emotional_memories.append(memory)
        else:
            self.long_term_memories.append(memory)

        # Update associations
        words = content.lower().split()
        for i, word in enumerate(words[:-1]):
            next_word = words[i + 1]
            self.concept_associations[word].add(next_word)

    async def get_dream_insights(self, limit: int = 10) -> List[DreamInsight]:
        """Get recent dream insights"""
        return self.insights_discovered[-limit:]

    async def get_statistics(self) -> Dict[str, Any]:
        """Get dream simulation statistics"""
        total_dreams = len(self.dream_sessions)

        if total_dreams == 0:
            return {'message': 'No dream sessions yet'}

        total_elements = sum(len(d.elements) for d in self.dream_sessions)
        total_insights = len(self.insights_discovered)
        novel_connections = sum(len(d.novel_connections) for d in self.dream_sessions)

        return {
            'total_dream_sessions': total_dreams,
            'total_elements_generated': total_elements,
            'total_insights': total_insights,
            'novel_connections_discovered': novel_connections,
            'avg_elements_per_dream': total_elements / total_dreams,
            'avg_insights_per_dream': total_insights / total_dreams,
            'memory_pools': {
                'recent': len(self.recent_memories),
                'long_term': len(self.long_term_memories),
                'emotional': len(self.emotional_memories)
            }
        }


async def demo():
    """Demo dream simulation"""
    simulator = DreamSimulator()

    # Add some memories
    await simulator.add_memory_to_pool("learning new programming concepts", is_recent=True)
    await simulator.add_memory_to_pool("exploring creative problem solving", is_recent=True)
    await simulator.add_memory_to_pool("feeling excited about discovery", is_emotional=True, is_recent=True)
    await simulator.add_memory_to_pool("understanding complex systems", is_recent=False)

    print("Dream Simulation Demo\n" + "="*50)

    # Run different dream phases
    for phase in [DreamPhase.LIGHT, DreamPhase.REM]:
        print(f"\n{phase.value.upper()} Dream Phase:")
        print("-" * 50)

        sequence = await simulator.start_dream_session(
            duration_minutes=2,
            initial_phase=phase,
            focus_problem="creative problem solving"
        )

        print(f"Generated {len(sequence.elements)} dream elements")
        print(f"Novel connections: {len(sequence.novel_connections)}")
        print(f"Insights: {len(sequence.insights_generated)}")

        if sequence.insights_generated:
            print("\nInsights discovered:")
            for insight in sequence.insights_generated[:3]:
                print(f"  - {insight}")

    # Statistics
    stats = await simulator.get_statistics()
    print(f"\n\nStatistics:\n{'-'*50}")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(demo())
