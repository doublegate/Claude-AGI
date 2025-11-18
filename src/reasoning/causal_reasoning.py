"""
Advanced Causal Reasoning for Claude-AGI
=========================================

Implements causal reasoning capabilities including:
- Variable identification and tracking
- Correlation detection and analysis
- Causation inference from observations
- Predictive model testing and refinement
- Causal model updating based on evidence
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class CausalRelationType(Enum):
    """Types of causal relationships"""
    DIRECT_CAUSE = "direct_cause"
    CONTRIBUTING_FACTOR = "contributing_factor"
    NECESSARY_CONDITION = "necessary_condition"
    SUFFICIENT_CONDITION = "sufficient_condition"
    PREVENTIVE = "preventive"
    CORRELATION_ONLY = "correlation_only"


@dataclass
class Variable:
    """A variable in the causal model"""
    var_id: str
    name: str
    var_type: str  # continuous, discrete, binary
    observed_values: List[Any] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CausalRelation:
    """A causal relationship between variables"""
    relation_id: str
    cause_var: str
    effect_var: str
    relation_type: CausalRelationType
    strength: float  # 0-1, strength of causal influence
    confidence: float  # 0-1, confidence in this relationship
    evidence: List[str] = field(default_factory=list)
    discovered_at: datetime = field(default_factory=datetime.now)


@dataclass
class Observation:
    """An observation of variables"""
    observation_id: str
    variables: Dict[str, Any]  # var_id -> value
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)


class CausalReasoner:
    """
    Performs causal reasoning to understand cause-effect relationships.

    Capabilities:
    - Identify variables in a system
    - Detect correlations
    - Infer causation
    - Test predictions
    - Update models based on evidence
    """

    def __init__(self):
        # Variables being tracked
        self.variables: Dict[str, Variable] = {}

        # Causal relationships
        self.causal_relations: List[CausalRelation] = []
        self.relation_index: Dict[str, List[CausalRelation]] = defaultdict(list)

        # Observations
        self.observations: deque = deque(maxlen=1000)

        # Correlation cache
        self.correlations: Dict[Tuple[str, str], float] = {}

        # Prediction history (for model testing)
        self.predictions: List[Dict[str, Any]] = []

    async def add_variable(
        self,
        var_id: str,
        name: str,
        var_type: str = "continuous"
    ) -> Variable:
        """Add a variable to track"""
        var = Variable(
            var_id=var_id,
            name=name,
            var_type=var_type
        )

        self.variables[var_id] = var
        logger.info(f"Added variable: {name} ({var_type})")

        return var

    async def record_observation(
        self,
        observation_id: str,
        variables: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Observation:
        """Record an observation of variables"""
        obs = Observation(
            observation_id=observation_id,
            variables=variables,
            context=context or {}
        )

        self.observations.append(obs)

        # Update variable values
        for var_id, value in variables.items():
            if var_id in self.variables:
                self.variables[var_id].observed_values.append(value)

        # Invalidate correlation cache
        self.correlations.clear()

        return obs

    async def detect_correlation(
        self,
        var_a_id: str,
        var_b_id: str
    ) -> float:
        """Detect correlation between two variables"""
        # Check cache
        cache_key = tuple(sorted([var_a_id, var_b_id]))
        if cache_key in self.correlations:
            return self.correlations[cache_key]

        var_a = self.variables.get(var_a_id)
        var_b = self.variables.get(var_b_id)

        if not var_a or not var_b:
            return 0.0

        # Simple correlation calculation
        # (In production, would use proper statistical methods)
        values_a = var_a.observed_values
        values_b = var_b.observed_values

        if len(values_a) < 2 or len(values_b) < 2:
            return 0.0

        # Use paired observations
        n = min(len(values_a), len(values_b))
        pairs = list(zip(values_a[:n], values_b[:n]))

        # Simple covariance approximation
        try:
            mean_a = sum(float(v) for v, _ in pairs) / n
            mean_b = sum(float(v) for _, v in pairs) / n

            cov = sum((float(a) - mean_a) * (float(b) - mean_b) for a, b in pairs) / n
            std_a = (sum((float(a) - mean_a) ** 2 for a, _ in pairs) / n) ** 0.5
            std_b = (sum((float(b) - mean_b) ** 2 for _, b in pairs) / n) ** 0.5

            if std_a > 0 and std_b > 0:
                correlation = cov / (std_a * std_b)
            else:
                correlation = 0.0

            # Clamp to [-1, 1]
            correlation = max(-1.0, min(1.0, correlation))

        except (ValueError, TypeError):
            correlation = 0.0

        # Cache result
        self.correlations[cache_key] = correlation

        return correlation

    async def infer_causation(
        self,
        var_a_id: str,
        var_b_id: str,
        temporal_evidence: bool = False
    ) -> Optional[CausalRelation]:
        """Infer potential causal relationship"""
        # First check correlation
        correlation = await self.detect_correlation(var_a_id, var_b_id)

        if abs(correlation) < 0.3:
            # Too weak for causation
            return None

        # Determine direction (simplified heuristic)
        # In production, would use more sophisticated methods
        # (Granger causality, do-calculus, etc.)

        import uuid

        # Check temporal ordering if evidence provided
        if temporal_evidence:
            relation_type = CausalRelationType.DIRECT_CAUSE
            confidence = 0.7
        else:
            # Without temporal evidence, less confident
            relation_type = CausalRelationType.CONTRIBUTING_FACTOR
            confidence = 0.5

        relation = CausalRelation(
            relation_id=str(uuid.uuid4()),
            cause_var=var_a_id,
            effect_var=var_b_id,
            relation_type=relation_type,
            strength=abs(correlation),
            confidence=confidence,
            evidence=[f"Correlation: {correlation:.2f}"]
        )

        self.causal_relations.append(relation)
        self.relation_index[var_a_id].append(relation)

        logger.info(f"Inferred causation: {var_a_id} -> {var_b_id} (confidence: {confidence:.2f})")

        return relation

    async def make_prediction(
        self,
        cause_var_id: str,
        cause_value: Any,
        effect_var_id: str
    ) -> Optional[Any]:
        """Predict effect given cause value"""
        # Find causal relations
        relations = [
            r for r in self.relation_index.get(cause_var_id, [])
            if r.effect_var == effect_var_id
        ]

        if not relations:
            return None

        # Use strongest relation
        relation = max(relations, key=lambda r: r.strength * r.confidence)

        # Simple linear prediction (in production, would be more sophisticated)
        effect_var = self.variables.get(effect_var_id)
        if not effect_var or not effect_var.observed_values:
            return None

        # Predict based on strength and typical effect values
        mean_effect = sum(float(v) for v in effect_var.observed_values) / len(effect_var.observed_values)

        # Scale by causal strength
        predicted_change = relation.strength * float(cause_value)
        prediction = mean_effect + predicted_change

        # Record prediction
        self.predictions.append({
            'cause_var': cause_var_id,
            'cause_value': cause_value,
            'effect_var': effect_var_id,
            'predicted_effect': prediction,
            'relation_id': relation.relation_id,
            'timestamp': datetime.now()
        })

        return prediction

    async def test_prediction(
        self,
        prediction_index: int,
        actual_effect: Any
    ) -> float:
        """Test a prediction against actual outcome"""
        if prediction_index >= len(self.predictions):
            return 0.0

        pred = self.predictions[prediction_index]
        predicted = pred['predicted_effect']

        try:
            error = abs(float(predicted) - float(actual_effect))
            # Normalize error to 0-1 score
            accuracy = 1.0 / (1.0 + error)
        except (ValueError, TypeError):
            accuracy = 0.0

        pred['actual_effect'] = actual_effect
        pred['accuracy'] = accuracy

        return accuracy

    async def update_causal_model(
        self,
        relation_id: str,
        new_strength: Optional[float] = None,
        new_confidence: Optional[float] = None,
        additional_evidence: Optional[str] = None
    ):
        """Update causal model based on new evidence"""
        # Find relation
        relation = None
        for r in self.causal_relations:
            if r.relation_id == relation_id:
                relation = r
                break

        if not relation:
            return

        if new_strength is not None:
            relation.strength = max(0.0, min(1.0, new_strength))

        if new_confidence is not None:
            relation.confidence = max(0.0, min(1.0, new_confidence))

        if additional_evidence:
            relation.evidence.append(additional_evidence)

        logger.info(f"Updated causal model: {relation.cause_var} -> {relation.effect_var}")

    async def get_causes(self, effect_var_id: str) -> List[CausalRelation]:
        """Get all known causes of an effect"""
        causes = []
        for relation in self.causal_relations:
            if relation.effect_var == effect_var_id:
                causes.append(relation)

        causes.sort(key=lambda r: r.strength * r.confidence, reverse=True)
        return causes

    async def get_effects(self, cause_var_id: str) -> List[CausalRelation]:
        """Get all known effects of a cause"""
        return self.relation_index.get(cause_var_id, [])

    async def get_statistics(self) -> Dict[str, Any]:
        """Get causal reasoning statistics"""
        if not self.causal_relations:
            return {'message': 'No causal relations yet'}

        avg_strength = sum(r.strength for r in self.causal_relations) / len(self.causal_relations)
        avg_confidence = sum(r.confidence for r in self.causal_relations) / len(self.causal_relations)

        # Calculate prediction accuracy
        tested_predictions = [p for p in self.predictions if 'accuracy' in p]
        avg_prediction_accuracy = (
            sum(p['accuracy'] for p in tested_predictions) / len(tested_predictions)
            if tested_predictions else 0.0
        )

        return {
            'total_variables': len(self.variables),
            'total_observations': len(self.observations),
            'total_causal_relations': len(self.causal_relations),
            'avg_causal_strength': round(avg_strength, 2),
            'avg_confidence': round(avg_confidence, 2),
            'total_predictions': len(self.predictions),
            'tested_predictions': len(tested_predictions),
            'avg_prediction_accuracy': round(avg_prediction_accuracy, 2)
        }
