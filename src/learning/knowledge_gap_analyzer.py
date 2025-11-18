"""
Knowledge Gap Analysis System
==============================

Identifies and analyzes gaps in the knowledge graph to drive
targeted learning and exploration.
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Set, Optional, Tuple
import re

logger = logging.getLogger(__name__)


class GapType(Enum):
    """Types of knowledge gaps"""
    MISSING_CONCEPT = "missing_concept"  # Referenced but not defined
    WEAK_UNDERSTANDING = "weak_understanding"  # Few connections
    MISSING_RELATIONSHIP = "missing_relationship"  # Expected but absent
    CONTRADICTION = "contradiction"  # Conflicting information
    INCOMPLETE_COVERAGE = "incomplete_coverage"  # Partial knowledge
    OUTDATED_INFORMATION = "outdated_information"  # Needs update


class GapSeverity(Enum):
    """Severity levels for knowledge gaps"""
    CRITICAL = 1.0
    HIGH = 0.8
    MEDIUM = 0.5
    LOW = 0.3
    MINIMAL = 0.1


@dataclass
class KnowledgeGap:
    """Represents an identified knowledge gap"""
    gap_id: str
    gap_type: GapType
    severity: GapSeverity
    topic: str
    description: str
    evidence: List[str] = field(default_factory=list)
    affected_concepts: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    discovered_at: datetime = field(default_factory=datetime.now)
    addressed: bool = False


@dataclass
class GapAnalysisReport:
    """Report of knowledge gap analysis"""
    analysis_id: str
    timestamp: datetime
    total_gaps: int
    gaps_by_type: Dict[str, int]
    gaps_by_severity: Dict[str, int]
    critical_gaps: List[KnowledgeGap]
    recommendations: List[str]


class KnowledgeGapAnalyzer:
    """
    Analyzes the knowledge graph to identify gaps, weaknesses,
    and areas needing attention.
    """

    def __init__(self, knowledge_graph):
        self.knowledge_graph = knowledge_graph
        self.identified_gaps: Dict[str, KnowledgeGap] = {}
        self.analysis_history: List[GapAnalysisReport] = []

        # Analysis parameters
        self.min_connections_threshold = 3
        self.weak_confidence_threshold = 0.5
        self.stale_concept_days = 90

    async def analyze_knowledge_graph(self) -> GapAnalysisReport:
        """
        Perform comprehensive analysis of the knowledge graph.

        Returns:
            Analysis report with identified gaps
        """
        import uuid

        logger.info("Starting knowledge gap analysis...")

        # Run all analysis methods
        gaps = []

        # 1. Find missing concepts
        missing = await self._find_missing_concepts()
        gaps.extend(missing)

        # 2. Find weakly connected concepts
        weak = await self._find_weak_concepts()
        gaps.extend(weak)

        # 3. Find missing relationships
        missing_rels = await self._find_missing_relationships()
        gaps.extend(missing_rels)

        # 4. Find contradictions
        contradictions = await self._find_contradictions()
        gaps.extend(contradictions)

        # 5. Find incomplete coverage
        incomplete = await self._find_incomplete_coverage()
        gaps.extend(incomplete)

        # Store gaps
        for gap in gaps:
            self.identified_gaps[gap.gap_id] = gap

        # Generate report
        gaps_by_type = defaultdict(int)
        gaps_by_severity = defaultdict(int)
        critical_gaps = []

        for gap in gaps:
            gaps_by_type[gap.gap_type.value] += 1
            gaps_by_severity[gap.severity.name] += 1

            if gap.severity in [GapSeverity.CRITICAL, GapSeverity.HIGH]:
                critical_gaps.append(gap)

        # Generate recommendations
        recommendations = await self._generate_recommendations(gaps)

        report = GapAnalysisReport(
            analysis_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            total_gaps=len(gaps),
            gaps_by_type=dict(gaps_by_type),
            gaps_by_severity=dict(gaps_by_severity),
            critical_gaps=critical_gaps[:10],  # Top 10
            recommendations=recommendations
        )

        self.analysis_history.append(report)

        logger.info(
            f"Analysis complete: {len(gaps)} gaps found "
            f"({len(critical_gaps)} critical)"
        )

        return report

    async def _find_missing_concepts(self) -> List[KnowledgeGap]:
        """Find concepts that are referenced but not defined"""
        gaps = []

        # Track referenced but missing concepts
        referenced = set()
        defined = set(self.knowledge_graph.concept_by_name.keys())

        # Check relationships for references to missing concepts
        for rel in self.knowledge_graph.relationships.values():
            source_concept = self.knowledge_graph.concepts.get(rel.source_id)
            target_concept = self.knowledge_graph.concepts.get(rel.target_id)

            if source_concept:
                referenced.add(source_concept.name)
            if target_concept:
                referenced.add(target_concept.name)

        # Find missing
        missing = referenced - defined

        for concept_name in missing:
            import uuid
            gap = KnowledgeGap(
                gap_id=str(uuid.uuid4()),
                gap_type=GapType.MISSING_CONCEPT,
                severity=GapSeverity.HIGH,
                topic=concept_name,
                description=f"Concept '{concept_name}' is referenced but not defined",
                evidence=[f"Referenced in relationships but not in knowledge graph"],
                recommended_actions=[
                    f"Research and add concept: {concept_name}",
                    "Define relationships and properties"
                ]
            )
            gaps.append(gap)

        return gaps

    async def _find_weak_concepts(self) -> List[KnowledgeGap]:
        """Find concepts with few connections (weak understanding)"""
        gaps = []

        for concept_id, concept in self.knowledge_graph.concepts.items():
            # Count connections
            outgoing = len(self.knowledge_graph.outgoing_edges.get(concept_id, []))
            incoming = len(self.knowledge_graph.incoming_edges.get(concept_id, []))
            total_connections = outgoing + incoming

            # Check if weakly connected
            if total_connections < self.min_connections_threshold:
                import uuid

                severity = GapSeverity.MEDIUM
                if total_connections == 0:
                    severity = GapSeverity.HIGH
                elif total_connections == 1:
                    severity = GapSeverity.MEDIUM
                else:
                    severity = GapSeverity.LOW

                gap = KnowledgeGap(
                    gap_id=str(uuid.uuid4()),
                    gap_type=GapType.WEAK_UNDERSTANDING,
                    severity=severity,
                    topic=concept.name,
                    description=f"Concept '{concept.name}' has only {total_connections} connections",
                    evidence=[
                        f"Outgoing relationships: {outgoing}",
                        f"Incoming relationships: {incoming}"
                    ],
                    affected_concepts=[concept.name],
                    recommended_actions=[
                        f"Explore relationships for {concept.name}",
                        "Research how it connects to other concepts",
                        "Add missing relationships"
                    ]
                )
                gaps.append(gap)

        return gaps

    async def _find_missing_relationships(self) -> List[KnowledgeGap]:
        """Find expected relationships that are missing"""
        gaps = []

        # Heuristics for expected relationships
        for concept_id, concept in self.knowledge_graph.concepts.items():
            concept_name = concept.name.lower()

            # Check for common relationship patterns
            expected_relationships = []

            # If it's a technology, expect "requires", "used_for"
            if any(word in concept_name for word in ['algorithm', 'method', 'technique', 'technology']):
                # Check if has "requires" relationships
                has_requires = any(
                    self.knowledge_graph.relationships.get(edge_id).relation_type.value == 'requires'
                    for edge_id in self.knowledge_graph.outgoing_edges.get(concept_id, [])
                    if self.knowledge_graph.relationships.get(edge_id)
                )

                if not has_requires:
                    expected_relationships.append("requires")

            # If it's a concept type, expect "part_of" or "is_a"
            if concept.concept_type in ['technology', 'method', 'theory']:
                has_taxonomy = any(
                    self.knowledge_graph.relationships.get(edge_id).relation_type.value in ['part_of', 'is_a']
                    for edge_id in self.knowledge_graph.outgoing_edges.get(concept_id, [])
                    if self.knowledge_graph.relationships.get(edge_id)
                )

                if not has_taxonomy:
                    expected_relationships.append("part_of or is_a")

            # Create gap if missing expected relationships
            if expected_relationships:
                import uuid
                gap = KnowledgeGap(
                    gap_id=str(uuid.uuid4()),
                    gap_type=GapType.MISSING_RELATIONSHIP,
                    severity=GapSeverity.MEDIUM,
                    topic=concept.name,
                    description=f"Expected relationships missing for '{concept.name}'",
                    evidence=[f"Missing: {', '.join(expected_relationships)}"],
                    affected_concepts=[concept.name],
                    recommended_actions=[
                        f"Research {rel} relationships for {concept.name}"
                        for rel in expected_relationships
                    ]
                )
                gaps.append(gap)

        return gaps

    async def _find_contradictions(self) -> List[KnowledgeGap]:
        """Find contradictory information in the knowledge graph"""
        gaps = []

        # Check for conflicting relationships
        for concept_id, concept in self.knowledge_graph.concepts.items():
            outgoing = self.knowledge_graph.outgoing_edges.get(concept_id, [])

            # Group by relationship type
            rels_by_type = defaultdict(list)
            for edge_id in outgoing:
                rel = self.knowledge_graph.relationships.get(edge_id)
                if rel:
                    rels_by_type[rel.relation_type].append(rel)

            # Check for contradictions
            from src.learning.knowledge_graph import RelationType

            # Check "is_a" contradictions (can't be multiple types)
            if RelationType.IS_A in rels_by_type:
                is_a_rels = rels_by_type[RelationType.IS_A]
                if len(is_a_rels) > 1:
                    import uuid
                    gap = KnowledgeGap(
                        gap_id=str(uuid.uuid4()),
                        gap_type=GapType.CONTRADICTION,
                        severity=GapSeverity.HIGH,
                        topic=concept.name,
                        description=f"'{concept.name}' has contradictory IS_A relationships",
                        evidence=[
                            f"Multiple IS_A relationships: {[self.knowledge_graph.concepts.get(r.target_id).name for r in is_a_rels if self.knowledge_graph.concepts.get(r.target_id)]}"
                        ],
                        affected_concepts=[concept.name],
                        recommended_actions=[
                            "Review and resolve contradictory classifications",
                            "Determine correct IS_A relationship"
                        ]
                    )
                    gaps.append(gap)

        return gaps

    async def _find_incomplete_coverage(self) -> List[KnowledgeGap]:
        """Find areas with incomplete knowledge coverage"""
        gaps = []

        # Analyze concept types coverage
        type_counts = defaultdict(int)
        for concept in self.knowledge_graph.concepts.values():
            type_counts[concept.concept_type] += 1

        # Find underrepresented types
        avg_count = sum(type_counts.values()) / len(type_counts) if type_counts else 0

        for concept_type, count in type_counts.items():
            if count < avg_count * 0.5:  # Less than 50% of average
                import uuid
                gap = KnowledgeGap(
                    gap_id=str(uuid.uuid4()),
                    gap_type=GapType.INCOMPLETE_COVERAGE,
                    severity=GapSeverity.LOW,
                    topic=f"{concept_type} concepts",
                    description=f"Underrepresented concept type: {concept_type}",
                    evidence=[f"Only {count} concepts (avg: {avg_count:.1f})"],
                    recommended_actions=[
                        f"Explore and add more {concept_type} concepts",
                        "Research major topics in this area"
                    ]
                )
                gaps.append(gap)

        return gaps

    async def _generate_recommendations(
        self,
        gaps: List[KnowledgeGap]
    ) -> List[str]:
        """Generate actionable recommendations based on gaps"""
        recommendations = []

        # Prioritize by severity
        critical = [g for g in gaps if g.severity == GapSeverity.CRITICAL]
        high = [g for g in gaps if g.severity == GapSeverity.HIGH]

        if critical:
            recommendations.append(
                f"URGENT: Address {len(critical)} critical knowledge gaps immediately"
            )

        if high:
            recommendations.append(
                f"HIGH PRIORITY: Focus on {len(high)} high-severity gaps"
            )

        # Type-specific recommendations
        gap_types = defaultdict(list)
        for gap in gaps:
            gap_types[gap.gap_type].append(gap)

        if GapType.MISSING_CONCEPT in gap_types:
            count = len(gap_types[GapType.MISSING_CONCEPT])
            recommendations.append(
                f"Research and add {count} missing concepts to knowledge graph"
            )

        if GapType.WEAK_UNDERSTANDING in gap_types:
            count = len(gap_types[GapType.WEAK_UNDERSTANDING])
            recommendations.append(
                f"Strengthen understanding of {count} weakly connected concepts"
            )

        if GapType.CONTRADICTION in gap_types:
            count = len(gap_types[GapType.CONTRADICTION])
            recommendations.append(
                f"URGENT: Resolve {count} contradictions in knowledge graph"
            )

        # Add general recommendations
        if len(gaps) > 50:
            recommendations.append(
                "Consider comprehensive knowledge audit and refactoring"
            )

        return recommendations

    async def get_priority_gaps(
        self,
        max_count: int = 10,
        min_severity: GapSeverity = GapSeverity.MEDIUM
    ) -> List[KnowledgeGap]:
        """
        Get highest priority knowledge gaps.

        Args:
            max_count: Maximum gaps to return
            min_severity: Minimum severity threshold

        Returns:
            List of priority gaps
        """
        # Filter by severity
        filtered = [
            gap for gap in self.identified_gaps.values()
            if gap.severity.value >= min_severity.value and not gap.addressed
        ]

        # Sort by severity
        sorted_gaps = sorted(
            filtered,
            key=lambda g: (g.severity.value, g.discovered_at),
            reverse=True
        )

        return sorted_gaps[:max_count]

    async def mark_gap_addressed(self, gap_id: str):
        """Mark a knowledge gap as addressed"""
        if gap_id in self.identified_gaps:
            self.identified_gaps[gap_id].addressed = True
            logger.info(f"Marked gap as addressed: {gap_id}")

    def get_gap_statistics(self) -> Dict[str, any]:
        """Get statistics about identified gaps"""
        total = len(self.identified_gaps)
        addressed = len([g for g in self.identified_gaps.values() if g.addressed])
        unaddressed = total - addressed

        by_type = defaultdict(int)
        by_severity = defaultdict(int)

        for gap in self.identified_gaps.values():
            if not gap.addressed:
                by_type[gap.gap_type.value] += 1
                by_severity[gap.severity.name] += 1

        return {
            'total_gaps': total,
            'addressed': addressed,
            'unaddressed': unaddressed,
            'by_type': dict(by_type),
            'by_severity': dict(by_severity),
            'total_analyses': len(self.analysis_history)
        }


async def demo():
    """Demo knowledge gap analysis"""
    from src.learning.knowledge_graph import KnowledgeGraph, RelationType

    # Create knowledge graph with some gaps
    kg = KnowledgeGraph()

    # Add some concepts
    await kg.add_concept("Machine Learning", "technology", "AI subfield")
    await kg.add_concept("Python", "language", "Programming language")
    await kg.add_concept("Algorithm", "concept", "Step-by-step procedure")

    # Add minimal relationships (creating weak understanding)
    await kg.add_relationship("Machine Learning", "Python", RelationType.USES)

    # Create analyzer
    analyzer = KnowledgeGapAnalyzer(kg)

    # Analyze
    report = await analyzer.analyze_knowledge_graph()

    print(f"\n=== Knowledge Gap Analysis Report ===")
    print(f"Total gaps found: {report.total_gaps}")
    print(f"\nBy type:")
    for gap_type, count in report.gaps_by_type.items():
        print(f"  {gap_type}: {count}")

    print(f"\nBy severity:")
    for severity, count in report.gaps_by_severity.items():
        print(f"  {severity}: {count}")

    print(f"\nCritical gaps:")
    for gap in report.critical_gaps[:5]:
        print(f"  - {gap.topic}: {gap.description}")

    print(f"\nRecommendations:")
    for rec in report.recommendations:
        print(f"  • {rec}")

    # Statistics
    stats = analyzer.get_gap_statistics()
    print(f"\nGap Statistics:")
    print(f"  Unaddressed gaps: {stats['unaddressed']}")


if __name__ == "__main__":
    asyncio.run(demo())
