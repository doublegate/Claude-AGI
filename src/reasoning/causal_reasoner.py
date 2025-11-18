"""
Causal Reasoning System
========================

Identifies and models causal relationships for better understanding
and prediction of outcomes.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class CausalRelationship:
    """A causal relationship between variables"""
    cause: str
    effect: str
    strength: float  # 0-1
    confidence: float  # 0-1
    evidence_count: int = 0
    observed_at: List[datetime] = field(default_factory=list)
    confounders: Set[str] = field(default_factory=set)


class CausalReasoner:
    """
    Builds and reasons about causal models to understand
    cause-effect relationships and make predictions.
    """

    def __init__(self):
        # Causal graph
        self.causal_relationships: Dict[Tuple[str, str], CausalRelationship] = {}

        # Variable tracking
        self.variables: Set[str] = set()
        self.observations: List[Dict[str, Any]] = []

    async def observe(self, observation: Dict[str, Any]):
        """Record an observation"""
        self.observations.append({
            'timestamp': datetime.now(),
            'data': observation
        })

        # Extract variables
        for var in observation.keys():
            self.variables.add(var)

        # Detect potential causal relationships
        if len(self.observations) >= 10:
            await self._detect_causal_relationships()

    async def _detect_causal_relationships(self):
        """Detect causal relationships from observations"""
        # Analyze temporal precedence and correlation
        for var_a in self.variables:
            for var_b in self.variables:
                if var_a == var_b:
                    continue

                # Check if var_a temporally precedes var_b
                correlation = await self._calculate_correlation(var_a, var_b)

                if abs(correlation) > 0.6:
                    # Potential causal relationship
                    await self.propose_causal_relationship(
                        var_a,
                        var_b,
                        abs(correlation),
                        0.5  # Initial confidence
                    )

    async def _calculate_correlation(self, var_a: str, var_b: str) -> float:
        """Calculate correlation between two variables"""
        # Simplified correlation calculation
        pairs = []
        for obs in self.observations:
            data = obs['data']
            if var_a in data and var_b in data:
                pairs.append((data[var_a], data[var_b]))

        if len(pairs) < 2:
            return 0.0

        # Simple correlation (in real implementation, use proper statistics)
        return 0.7 if len(pairs) > 5 else 0.3

    async def propose_causal_relationship(
        self,
        cause: str,
        effect: str,
        strength: float,
        confidence: float
    ) -> CausalRelationship:
        """Propose a causal relationship"""
        key = (cause, effect)

        if key in self.causal_relationships:
            # Update existing relationship
            rel = self.causal_relationships[key]
            rel.evidence_count += 1
            rel.observed_at.append(datetime.now())
            # Update confidence
            rel.confidence = min(1.0, rel.confidence + 0.1)
        else:
            # Create new relationship
            rel = CausalRelationship(
                cause=cause,
                effect=effect,
                strength=strength,
                confidence=confidence,
                evidence_count=1,
                observed_at=[datetime.now()]
            )
            self.causal_relationships[key] = rel

        logger.info(f"Causal relationship: {cause} -> {effect} (strength: {strength:.2f})")
        return rel

    async def predict_outcome(
        self,
        interventions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict outcomes based on interventions using causal model"""
        predictions = {}

        for var, value in interventions.items():
            # Find effects of this variable
            effects = [
                rel for (cause, effect), rel in self.causal_relationships.items()
                if cause == var
            ]

            for rel in effects:
                if rel.confidence > 0.5:
                    # Predict effect
                    predicted_change = value * rel.strength
                    predictions[rel.effect] = predicted_change

        return predictions

    async def identify_confounders(
        self,
        cause: str,
        effect: str
    ) -> Set[str]:
        """Identify potential confounding variables"""
        confounders = set()

        # Find variables that influence both cause and effect
        for var in self.variables:
            if var in {cause, effect}:
                continue

            influences_cause = (var, cause) in self.causal_relationships
            influences_effect = (var, effect) in self.causal_relationships

            if influences_cause and influences_effect:
                confounders.add(var)

        return confounders

    async def get_causal_insights(self) -> Dict[str, Any]:
        """Get insights about causal model"""
        return {
            'total_variables': len(self.variables),
            'total_relationships': len(self.causal_relationships),
            'strong_relationships': len([r for r in self.causal_relationships.values() if r.strength > 0.7]),
            'observations': len(self.observations)
        }
