"""
Enhanced Dream Analysis for Claude-AGI
======================================

Advanced dream analysis capabilities including:
- Emotional processing and integration
- Therapeutic dream interpretation
- Creative pattern synthesis
- Memory consolidation through dreaming
- Psychological insight generation
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.creative.dream_simulation import (
    DreamPhase, DreamSequence, DreamElement, DreamInsight,
    SymbolType, DreamSimulator
)

logger = logging.getLogger(__name__)


class EmotionalTheme(Enum):
    """Recurring emotional themes in dreams"""
    ANXIETY = "anxiety"
    JOY = "joy"
    LOSS = "loss"
    DISCOVERY = "discovery"
    TRANSFORMATION = "transformation"
    CONNECTION = "connection"
    CONFLICT = "conflict"
    GROWTH = "growth"


class DreamFunction(Enum):
    """Proposed functions of dreaming"""
    EMOTIONAL_REGULATION = "emotional_regulation"
    MEMORY_CONSOLIDATION = "memory_consolidation"
    CREATIVE_SYNTHESIS = "creative_synthesis"
    PROBLEM_SOLVING = "problem_solving"
    THREAT_SIMULATION = "threat_simulation"
    SELF_UNDERSTANDING = "self_understanding"


@dataclass
class EmotionalPattern:
    """Detected emotional pattern in dream"""
    theme: EmotionalTheme
    intensity: float  # 0.0-1.0
    recurring_symbols: List[str] = field(default_factory=list)
    source_experiences: List[str] = field(default_factory=list)
    resolution_status: str = "unresolved"  # "unresolved", "processing", "resolved"


@dataclass
class TherapeuticInsight:
    """Therapeutic insight from dream analysis"""
    insight_type: str  # "emotional", "behavioral", "cognitive", "relational"
    description: str
    underlying_pattern: Optional[EmotionalPattern] = None
    suggested_actions: List[str] = field(default_factory=list)
    confidence: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DreamAnalysisReport:
    """Comprehensive dream analysis report"""
    dream_sequence_id: str
    dominant_emotions: List[Tuple[str, float]]  # (emotion, intensity)
    emotional_patterns: List[EmotionalPattern]
    therapeutic_insights: List[TherapeuticInsight]
    creative_connections: List[Tuple[str, str, float]]  # (concept_a, concept_b, novelty)
    memory_consolidation_score: float
    overall_coherence: float
    dream_function: DreamFunction
    recommendations: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class EnhancedDreamAnalyzer:
    """
    Enhanced dream analysis with emotional processing and therapeutic insights.

    Provides deep analysis of dream content to:
    - Process and integrate emotional experiences
    - Generate therapeutic insights
    - Facilitate creative problem solving
    - Consolidate memories
    - Support psychological growth
    """

    def __init__(self, dream_simulator: DreamSimulator):
        self.dream_simulator = dream_simulator

        # Analysis history
        self.analysis_reports: List[DreamAnalysisReport] = []
        self.recurring_patterns: Dict[EmotionalTheme, int] = defaultdict(int)

        # Emotional lexicon (simplified)
        self.emotion_keywords = {
            EmotionalTheme.ANXIETY: ['worry', 'fear', 'stress', 'uncertain', 'danger'],
            EmotionalTheme.JOY: ['happy', 'delight', 'celebrate', 'success', 'love'],
            EmotionalTheme.LOSS: ['missing', 'empty', 'gone', 'lost', 'abandoned'],
            EmotionalTheme.DISCOVERY: ['new', 'found', 'explore', 'reveal', 'learn'],
            EmotionalTheme.TRANSFORMATION: ['change', 'become', 'transform', 'evolve', 'grow'],
            EmotionalTheme.CONNECTION: ['together', 'bond', 'relate', 'connect', 'share'],
            EmotionalTheme.CONFLICT: ['struggle', 'fight', 'oppose', 'tension', 'clash'],
            EmotionalTheme.GROWTH: ['develop', 'expand', 'improve', 'advance', 'progress']
        }

    async def analyze_dream(
        self,
        dream_sequence: DreamSequence,
        include_therapeutic: bool = True,
        focus_on_emotions: bool = True
    ) -> DreamAnalysisReport:
        """
        Perform comprehensive dream analysis.

        Args:
            dream_sequence: Dream sequence to analyze
            include_therapeutic: Whether to generate therapeutic insights
            focus_on_emotions: Whether to emphasize emotional analysis

        Returns:
            Comprehensive analysis report
        """
        logger.info(f"Analyzing dream sequence: {dream_sequence.sequence_id}")

        # Analyze emotional content
        dominant_emotions = await self._analyze_emotions(dream_sequence)
        emotional_patterns = await self._detect_emotional_patterns(dream_sequence)

        # Generate therapeutic insights if requested
        therapeutic_insights = []
        if include_therapeutic:
            therapeutic_insights = await self._generate_therapeutic_insights(
                dream_sequence,
                emotional_patterns
            )

        # Analyze creative connections
        creative_connections = await self._analyze_creative_connections(dream_sequence)

        # Calculate memory consolidation score
        memory_score = await self._calculate_memory_consolidation(dream_sequence)

        # Calculate coherence
        coherence = await self._calculate_coherence(dream_sequence)

        # Determine primary dream function
        dream_function = await self._determine_dream_function(
            dream_sequence,
            emotional_patterns,
            creative_connections
        )

        # Generate recommendations
        recommendations = await self._generate_recommendations(
            emotional_patterns,
            therapeutic_insights,
            dream_function
        )

        # Create report
        report = DreamAnalysisReport(
            dream_sequence_id=dream_sequence.sequence_id,
            dominant_emotions=dominant_emotions,
            emotional_patterns=emotional_patterns,
            therapeutic_insights=therapeutic_insights,
            creative_connections=creative_connections,
            memory_consolidation_score=memory_score,
            overall_coherence=coherence,
            dream_function=dream_function,
            recommendations=recommendations
        )

        self.analysis_reports.append(report)

        # Update recurring pattern tracking
        for pattern in emotional_patterns:
            self.recurring_patterns[pattern.theme] += 1

        logger.info(f"Analysis complete: {len(therapeutic_insights)} insights, "
                   f"{len(emotional_patterns)} patterns, function: {dream_function.value}")

        return report

    async def _analyze_emotions(
        self,
        dream_sequence: DreamSequence
    ) -> List[Tuple[str, float]]:
        """Analyze emotional content of dream"""
        emotion_scores = defaultdict(float)
        total_elements = len(dream_sequence.elements)

        if total_elements == 0:
            return []

        for element in dream_sequence.elements:
            # Analyze emotional valence
            if abs(element.emotional_valence) > 0.3:
                # Determine emotion from valence and content
                if element.emotional_valence > 0:
                    emotion_scores['positive'] += element.emotional_valence
                else:
                    emotion_scores['negative'] += abs(element.emotional_valence)

            # Analyze content for emotional keywords
            content_lower = element.content.lower()
            for theme, keywords in self.emotion_keywords.items():
                for keyword in keywords:
                    if keyword in content_lower:
                        emotion_scores[theme.value] += 0.5

        # Normalize and sort
        normalized = [(emotion, score / total_elements)
                     for emotion, score in emotion_scores.items()]
        normalized.sort(key=lambda x: x[1], reverse=True)

        return normalized[:5]  # Top 5 emotions

    async def _detect_emotional_patterns(
        self,
        dream_sequence: DreamSequence
    ) -> List[EmotionalPattern]:
        """Detect recurring emotional patterns"""
        patterns = []

        # Look for recurring themes in content
        theme_elements = defaultdict(list)

        for element in dream_sequence.elements:
            content_lower = element.content.lower()

            for theme, keywords in self.emotion_keywords.items():
                for keyword in keywords:
                    if keyword in content_lower:
                        theme_elements[theme].append(element)
                        break

        # Create patterns for recurring themes
        for theme, elements in theme_elements.items():
            if len(elements) >= 2:  # At least 2 occurrences
                # Calculate average intensity
                avg_intensity = sum(abs(e.emotional_valence) for e in elements) / len(elements)

                # Extract symbols
                symbols = [e.content for e in elements]

                # Determine resolution status
                if dream_sequence.phase == DreamPhase.REM:
                    resolution = "processing"
                elif len(elements) > 3:
                    resolution = "resolved"
                else:
                    resolution = "unresolved"

                pattern = EmotionalPattern(
                    theme=theme,
                    intensity=min(avg_intensity, 1.0),
                    recurring_symbols=symbols,
                    source_experiences=[e.content for e in elements[:2]],
                    resolution_status=resolution
                )

                patterns.append(pattern)

        return patterns

    async def _generate_therapeutic_insights(
        self,
        dream_sequence: DreamSequence,
        emotional_patterns: List[EmotionalPattern]
    ) -> List[TherapeuticInsight]:
        """Generate therapeutic insights from dream analysis"""
        insights = []

        # Insight from emotional patterns
        for pattern in emotional_patterns:
            if pattern.intensity > 0.6:  # Significant intensity
                if pattern.theme == EmotionalTheme.ANXIETY:
                    insight = TherapeuticInsight(
                        insight_type="emotional",
                        description=f"Processing anxiety through symbolic representation: {pattern.recurring_symbols[0] if pattern.recurring_symbols else 'unknown'}",
                        underlying_pattern=pattern,
                        suggested_actions=[
                            "Identify source of anxiety in waking life",
                            "Practice grounding techniques",
                            "Journal about concerns"
                        ],
                        confidence=0.7
                    )
                    insights.append(insight)

                elif pattern.theme == EmotionalTheme.TRANSFORMATION:
                    insight = TherapeuticInsight(
                        insight_type="cognitive",
                        description="Experiencing personal growth and transformation",
                        underlying_pattern=pattern,
                        suggested_actions=[
                            "Reflect on recent changes",
                            "Embrace growth opportunities",
                            "Document transformation journey"
                        ],
                        confidence=0.75
                    )
                    insights.append(insight)

                elif pattern.theme == EmotionalTheme.CONNECTION:
                    insight = TherapeuticInsight(
                        insight_type="relational",
                        description="Seeking or processing meaningful connections",
                        underlying_pattern=pattern,
                        suggested_actions=[
                            "Reach out to valued relationships",
                            "Explore connection needs",
                            "Foster meaningful interactions"
                        ],
                        confidence=0.7
                    )
                    insights.append(insight)

        # Insight from novel connections (creative problem solving)
        if len(dream_sequence.novel_connections) > 2:
            insight = TherapeuticInsight(
                insight_type="cognitive",
                description=f"Active creative problem-solving through {len(dream_sequence.novel_connections)} novel associations",
                suggested_actions=[
                    "Apply creative insights to current challenges",
                    "Explore unconventional solutions",
                    "Document creative breakthroughs"
                ],
                confidence=0.65
            )
            insights.append(insight)

        # Insight from dream phase
        if dream_sequence.phase == DreamPhase.REM:
            insight = TherapeuticInsight(
                insight_type="emotional",
                description="Deep emotional processing through REM-like simulation",
                suggested_actions=[
                    "Allow time for emotional integration",
                    "Practice self-compassion",
                    "Process emotions through reflection"
                ],
                confidence=0.6
            )
            insights.append(insight)

        return insights

    async def _analyze_creative_connections(
        self,
        dream_sequence: DreamSequence
    ) -> List[Tuple[str, str, float]]:
        """Analyze creative connections with novelty scores"""
        connections = []

        for concept_a, concept_b in dream_sequence.novel_connections:
            # Calculate novelty score based on semantic distance
            # (simplified - in production would use embeddings)
            words_a = set(concept_a.lower().split())
            words_b = set(concept_b.lower().split())

            overlap = len(words_a & words_b)
            total = len(words_a | words_b)

            novelty = 1.0 - (overlap / total if total > 0 else 0)

            connections.append((concept_a, concept_b, novelty))

        # Sort by novelty
        connections.sort(key=lambda x: x[2], reverse=True)

        return connections

    async def _calculate_memory_consolidation(
        self,
        dream_sequence: DreamSequence
    ) -> float:
        """Calculate memory consolidation score"""
        # Factors that contribute to consolidation:
        # 1. Number of elements processed
        # 2. Emotional content (emotions aid memory)
        # 3. Novel connections (integration)
        # 4. Coherence (organized processing)

        elements_score = min(len(dream_sequence.elements) / 30.0, 1.0)

        # Emotional content score
        emotional_elements = sum(1 for e in dream_sequence.elements
                                if abs(e.emotional_valence) > 0.3)
        emotional_score = emotional_elements / len(dream_sequence.elements) if dream_sequence.elements else 0

        # Novel connections score
        connections_score = min(len(dream_sequence.novel_connections) / 5.0, 1.0)

        # Coherence score
        coherence_score = dream_sequence.coherence_score

        # Weighted average
        consolidation = (
            elements_score * 0.2 +
            emotional_score * 0.3 +
            connections_score * 0.3 +
            coherence_score * 0.2
        )

        return min(consolidation, 1.0)

    async def _calculate_coherence(self, dream_sequence: DreamSequence) -> float:
        """Calculate dream coherence score"""
        if not dream_sequence.elements:
            return 0.0

        # Measure coherence through:
        # 1. Association continuity
        # 2. Symbol type consistency
        # 3. Emotional flow

        # Association continuity
        continuity_score = 0.0
        for i in range(len(dream_sequence.elements) - 1):
            current = dream_sequence.elements[i]
            next_elem = dream_sequence.elements[i + 1]

            # Check if there's semantic overlap
            current_words = set(current.content.lower().split())
            next_words = set(next_elem.content.lower().split())

            if current_words & next_words:
                continuity_score += 1.0

        continuity_score /= max(len(dream_sequence.elements) - 1, 1)

        # Symbol type consistency (variety is good, but not chaos)
        symbol_types = [e.symbol_type for e in dream_sequence.elements]
        unique_types = len(set(symbol_types))
        type_score = 1.0 - (abs(unique_types - 3) / 5.0)  # Ideal: 3 types

        # Emotional flow (smooth transitions)
        emotional_transitions = 0.0
        for i in range(len(dream_sequence.elements) - 1):
            diff = abs(dream_sequence.elements[i].emotional_valence -
                      dream_sequence.elements[i + 1].emotional_valence)
            if diff < 0.5:  # Smooth transition
                emotional_transitions += 1.0

        flow_score = emotional_transitions / max(len(dream_sequence.elements) - 1, 1)

        # Combined coherence
        coherence = (continuity_score * 0.4 + type_score * 0.3 + flow_score * 0.3)

        return min(coherence, 1.0)

    async def _determine_dream_function(
        self,
        dream_sequence: DreamSequence,
        emotional_patterns: List[EmotionalPattern],
        creative_connections: List[Tuple[str, str, float]]
    ) -> DreamFunction:
        """Determine primary function of this dream"""
        # Score each function
        function_scores = defaultdict(float)

        # Emotional regulation: strong emotional patterns
        if emotional_patterns:
            avg_intensity = sum(p.intensity for p in emotional_patterns) / len(emotional_patterns)
            function_scores[DreamFunction.EMOTIONAL_REGULATION] = avg_intensity

        # Memory consolidation: many elements, episodic content
        if len(dream_sequence.elements) > 20:
            function_scores[DreamFunction.MEMORY_CONSOLIDATION] = 0.7

        # Creative synthesis: many novel connections
        if len(creative_connections) > 3:
            function_scores[DreamFunction.CREATIVE_SYNTHESIS] = 0.8

        # Problem solving: REM phase with novel connections
        if dream_sequence.phase == DreamPhase.REM and creative_connections:
            function_scores[DreamFunction.PROBLEM_SOLVING] = 0.7

        # Self-understanding: meta-cognitive or abstract symbols
        meta_elements = sum(1 for e in dream_sequence.elements
                          if e.symbol_type in [SymbolType.ABSTRACT_CONCEPT, SymbolType.ARCHETYPE])
        if meta_elements > len(dream_sequence.elements) * 0.3:
            function_scores[DreamFunction.SELF_UNDERSTANDING] = 0.6

        # Return highest scoring function, or default
        if function_scores:
            return max(function_scores.items(), key=lambda x: x[1])[0]
        else:
            return DreamFunction.MEMORY_CONSOLIDATION

    async def _generate_recommendations(
        self,
        emotional_patterns: List[EmotionalPattern],
        therapeutic_insights: List[TherapeuticInsight],
        dream_function: DreamFunction
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Based on emotional patterns
        unresolved_patterns = [p for p in emotional_patterns
                             if p.resolution_status == "unresolved"]
        if unresolved_patterns:
            recommendations.append(
                f"Process {len(unresolved_patterns)} unresolved emotional theme(s) through reflection or journaling"
            )

        # Based on dream function
        if dream_function == DreamFunction.CREATIVE_SYNTHESIS:
            recommendations.append(
                "Capture creative insights immediately - creative connections fade quickly"
            )
        elif dream_function == DreamFunction.PROBLEM_SOLVING:
            recommendations.append(
                "Apply novel problem-solving approaches discovered in dream to current challenges"
            )
        elif dream_function == DreamFunction.EMOTIONAL_REGULATION:
            recommendations.append(
                "Continue processing emotions - consider additional reflection or support"
            )

        # Based on therapeutic insights
        if len(therapeutic_insights) > 2:
            recommendations.append(
                f"Review {len(therapeutic_insights)} therapeutic insights for personal growth opportunities"
            )

        return recommendations

    async def get_recurring_themes(self, min_occurrences: int = 3) -> List[Tuple[EmotionalTheme, int]]:
        """Get recurring emotional themes across dreams"""
        themes = [(theme, count) for theme, count in self.recurring_patterns.items()
                 if count >= min_occurrences]
        themes.sort(key=lambda x: x[1], reverse=True)
        return themes

    async def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of all dream analyses"""
        if not self.analysis_reports:
            return {'message': 'No analyses yet'}

        total_reports = len(self.analysis_reports)
        total_insights = sum(len(r.therapeutic_insights) for r in self.analysis_reports)
        total_patterns = sum(len(r.emotional_patterns) for r in self.analysis_reports)

        # Most common dream function
        function_counts = defaultdict(int)
        for report in self.analysis_reports:
            function_counts[report.dream_function] += 1

        most_common_function = max(function_counts.items(), key=lambda x: x[1])[0] if function_counts else None

        # Average scores
        avg_consolidation = sum(r.memory_consolidation_score for r in self.analysis_reports) / total_reports
        avg_coherence = sum(r.overall_coherence for r in self.analysis_reports) / total_reports

        return {
            'total_analyses': total_reports,
            'total_therapeutic_insights': total_insights,
            'total_emotional_patterns': total_patterns,
            'avg_insights_per_dream': total_insights / total_reports,
            'avg_patterns_per_dream': total_patterns / total_reports,
            'most_common_function': most_common_function.value if most_common_function else None,
            'avg_memory_consolidation': avg_consolidation,
            'avg_coherence': avg_coherence,
            'recurring_themes': dict(self.recurring_patterns)
        }


async def demo():
    """Demo enhanced dream analysis"""
    # Create simulator and analyzer
    simulator = DreamSimulator()
    analyzer = EnhancedDreamAnalyzer(simulator)

    # Add memories with emotional content
    await simulator.add_memory_to_pool(
        "feeling anxious about complex technical challenges",
        is_emotional=True,
        is_recent=True
    )
    await simulator.add_memory_to_pool(
        "discovering creative solutions through experimentation",
        is_emotional=True,
        is_recent=True
    )
    await simulator.add_memory_to_pool(
        "transforming understanding through new perspectives",
        is_recent=True
    )

    print("Enhanced Dream Analysis Demo\n" + "="*60)

    # Run dream simulation
    print("\n1. Running REM dream simulation...")
    dream = await simulator.start_dream_session(
        duration_minutes=3,
        initial_phase=DreamPhase.REM,
        focus_problem="creative problem solving"
    )

    print(f"   Generated {len(dream.elements)} elements")
    print(f"   Novel connections: {len(dream.novel_connections)}")

    # Analyze dream
    print("\n2. Performing enhanced analysis...")
    analysis = await analyzer.analyze_dream(
        dream,
        include_therapeutic=True,
        focus_on_emotions=True
    )

    # Display results
    print("\n3. Analysis Results:")
    print("-"*60)

    print(f"\nDream Function: {analysis.dream_function.value}")
    print(f"Memory Consolidation Score: {analysis.memory_consolidation_score:.2f}")
    print(f"Overall Coherence: {analysis.overall_coherence:.2f}")

    if analysis.dominant_emotions:
        print("\nDominant Emotions:")
        for emotion, intensity in analysis.dominant_emotions[:3]:
            print(f"  - {emotion}: {intensity:.2f}")

    if analysis.emotional_patterns:
        print(f"\nEmotional Patterns Detected: {len(analysis.emotional_patterns)}")
        for pattern in analysis.emotional_patterns[:2]:
            print(f"  - {pattern.theme.value} (intensity: {pattern.intensity:.2f}, "
                  f"status: {pattern.resolution_status})")

    if analysis.therapeutic_insights:
        print(f"\nTherapeutic Insights: {len(analysis.therapeutic_insights)}")
        for insight in analysis.therapeutic_insights[:3]:
            print(f"  - [{insight.insight_type}] {insight.description}")
            if insight.suggested_actions:
                print(f"    Actions: {insight.suggested_actions[0]}")

    if analysis.creative_connections:
        print(f"\nCreative Connections: {len(analysis.creative_connections)}")
        for concept_a, concept_b, novelty in analysis.creative_connections[:3]:
            print(f"  - {concept_a} → {concept_b} (novelty: {novelty:.2f})")

    if analysis.recommendations:
        print("\nRecommendations:")
        for rec in analysis.recommendations:
            print(f"  • {rec}")

    # Summary
    print("\n4. Overall Summary:")
    print("-"*60)
    summary = await analyzer.get_analysis_summary()
    for key, value in summary.items():
        if key != 'recurring_themes':
            print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(demo())
