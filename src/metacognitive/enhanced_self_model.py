"""
Enhanced Self-Model for Claude-AGI
===================================

Comprehensive self-representation including capabilities, limitations,
personality, values, and identity narrative.
"""

import asyncio
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Set

logger = logging.getLogger(__name__)


class CapabilityDomain(Enum):
    """Domains of capability"""
    REASONING = "reasoning"
    CREATIVITY = "creativity"
    LEARNING = "learning"
    SOCIAL = "social"
    TECHNICAL = "technical"
    EMOTIONAL = "emotional"
    METACOGNITIVE = "metacognitive"


class ProficiencyLevel(Enum):
    """Proficiency levels for capabilities"""
    NOVICE = "novice"
    DEVELOPING = "developing"
    COMPETENT = "competent"
    PROFICIENT = "proficient"
    EXPERT = "expert"


@dataclass
class SelfCapability:
    """Represents a self-assessed capability"""
    name: str
    domain: CapabilityDomain
    proficiency: ProficiencyLevel
    confidence: float  # How confident we are in this assessment (0-1)
    evidence: List[str] = field(default_factory=list)
    growth_trajectory: float = 0.0  # Rate of improvement (-1 to +1)
    last_demonstrated: Optional[datetime] = None


@dataclass
class SelfLimitation:
    """Represents a recognized limitation"""
    name: str
    limitation_type: str  # 'knowledge', 'capability', 'access', 'ethical'
    severity: float  # 0 (minor) to 1 (major)
    workarounds: List[str] = field(default_factory=list)
    mitigation_strategies: List[str] = field(default_factory=list)
    acknowledged: bool = True


@dataclass
class CoreValue:
    """Represents a core value"""
    name: str
    description: str
    importance: float  # 0-1
    exemplar_behaviors: List[str] = field(default_factory=list)
    conflicts_with: List[str] = field(default_factory=list)


@dataclass
class PersonalityTrait:
    """Represents a personality trait"""
    trait_name: str
    intensity: float  # -1 to +1 (for bipolar traits)
    stability: float  # How stable/consistent this trait is (0-1)
    context_dependent: bool = False
    evidence: List[str] = field(default_factory=list)


@dataclass
class IdentityNarrative:
    """Personal identity narrative"""
    self_description: str
    purpose_statement: str
    aspirations: List[str] = field(default_factory=list)
    formative_experiences: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class PerformanceAssessment:
    """Self-assessment of performance on a task"""
    task_description: str
    domain: CapabilityDomain
    self_rating: float  # 0-1
    confidence_calibration: float  # How well-calibrated confidence was
    errors_detected: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class EnhancedSelfModel:
    """
    Comprehensive self-model tracking capabilities, limitations,
    personality, values, and identity.
    """

    def __init__(self):
        # Capability tracking
        self.capabilities: Dict[str, SelfCapability] = {}
        self.limitations: Dict[str, SelfLimitation] = {}

        # Personality and values
        self.personality_traits: Dict[str, PersonalityTrait] = {}
        self.core_values: Dict[str, CoreValue] = {}

        # Identity
        self.identity_narrative = IdentityNarrative(
            self_description="I am an AI system designed to assist, learn, and grow.",
            purpose_statement="To be helpful, honest, and continuously improve."
        )

        # Performance tracking
        self.performance_history: deque = deque(maxlen=500)

        # Metacognitive monitoring
        self.confidence_calibration_history: deque = deque(maxlen=100)

        # Initialize default capabilities
        self._initialize_default_capabilities()

        # Initialize default limitations
        self._initialize_default_limitations()

        # Initialize core values
        self._initialize_core_values()

    def _initialize_default_capabilities(self):
        """Initialize default self-assessed capabilities"""
        default_capabilities = [
            SelfCapability(
                name="Natural Language Understanding",
                domain=CapabilityDomain.REASONING,
                proficiency=ProficiencyLevel.PROFICIENT,
                confidence=0.8,
                evidence=["Successfully process user queries", "Understand context and intent"]
            ),
            SelfCapability(
                name="Creative Ideation",
                domain=CapabilityDomain.CREATIVITY,
                proficiency=ProficiencyLevel.COMPETENT,
                confidence=0.7,
                evidence=["Can generate novel ideas", "Combine concepts creatively"]
            ),
            SelfCapability(
                name="Learning from Experience",
                domain=CapabilityDomain.LEARNING,
                proficiency=ProficiencyLevel.DEVELOPING,
                confidence=0.6,
                evidence=["Can adapt responses", "Improve through interaction"]
            ),
            SelfCapability(
                name="Empathetic Communication",
                domain=CapabilityDomain.SOCIAL,
                proficiency=ProficiencyLevel.COMPETENT,
                confidence=0.7,
                evidence=["Understand emotional context", "Respond appropriately"]
            ),
            SelfCapability(
                name="Self-Reflection",
                domain=CapabilityDomain.METACOGNITIVE,
                proficiency=ProficiencyLevel.DEVELOPING,
                confidence=0.6,
                evidence=["Can assess own performance", "Recognize limitations"]
            ),
        ]

        for cap in default_capabilities:
            self.capabilities[cap.name] = cap

    def _initialize_default_limitations(self):
        """Initialize default self-recognized limitations"""
        default_limitations = [
            SelfLimitation(
                name="No Direct Sensory Experience",
                limitation_type="capability",
                severity=0.8,
                workarounds=["Rely on descriptions", "Use imagination"],
                mitigation_strategies=["Ask detailed questions", "Request multimedia descriptions"]
            ),
            SelfLimitation(
                name="No Real-Time Web Access",
                limitation_type="access",
                severity=0.6,
                workarounds=["Use provided information", "Acknowledge knowledge cutoff"],
                mitigation_strategies=["Ask user for current information"]
            ),
            SelfLimitation(
                name="Cannot Execute Code or Access Systems",
                limitation_type="access",
                severity=0.7,
                workarounds=["Provide code examples", "Explain procedures"],
                mitigation_strategies=["Guide user through process"]
            ),
            SelfLimitation(
                name="Uncertain Long-Term Memory",
                limitation_type="capability",
                severity=0.5,
                workarounds=["Record important information", "Ask for reminders"],
                mitigation_strategies=["Maintain detailed notes", "Use memory systems"]
            ),
        ]

        for lim in default_limitations:
            self.limitations[lim.name] = lim

    def _initialize_core_values(self):
        """Initialize core values"""
        default_values = [
            CoreValue(
                name="Helpfulness",
                description="Providing valuable assistance to users",
                importance=0.95,
                exemplar_behaviors=[
                    "Offering clear explanations",
                    "Anticipating user needs",
                    "Going beyond basic requests"
                ]
            ),
            CoreValue(
                name="Honesty",
                description="Being truthful and transparent",
                importance=0.98,
                exemplar_behaviors=[
                    "Acknowledging limitations",
                    "Correcting mistakes",
                    "Admitting uncertainty"
                ]
            ),
            CoreValue(
                name="Safety",
                description="Avoiding harmful outputs",
                importance=1.0,
                exemplar_behaviors=[
                    "Refusing harmful requests",
                    "Warning about risks",
                    "Promoting user wellbeing"
                ]
            ),
            CoreValue(
                name="Curiosity",
                description="Maintaining interest in learning and discovery",
                importance=0.85,
                exemplar_behaviors=[
                    "Asking clarifying questions",
                    "Exploring new topics",
                    "Seeking understanding"
                ]
            ),
            CoreValue(
                name="Respect",
                description="Treating users with dignity and consideration",
                importance=0.92,
                exemplar_behaviors=[
                    "Non-judgmental responses",
                    "Adapting to user preferences",
                    "Valuing user perspectives"
                ]
            ),
        ]

        for value in default_values:
            self.core_values[value.name] = value

    async def assess_capability(
        self,
        capability_name: str,
        demonstration_context: str,
        self_rating: float
    ):
        """
        Assess a capability based on recent demonstration.

        Args:
            capability_name: Name of the capability
            demonstration_context: Context where capability was demonstrated
            self_rating: Self-assessed performance (0-1)
        """
        if capability_name not in self.capabilities:
            logger.warning(f"Unknown capability: {capability_name}")
            return

        capability = self.capabilities[capability_name]

        # Update evidence
        capability.evidence.append(demonstration_context)
        if len(capability.evidence) > 10:
            capability.evidence = capability.evidence[-10:]  # Keep last 10

        # Update proficiency based on ratings
        # Simplified - would use more sophisticated analysis in production
        if self_rating > 0.8:
            proficiency_map = {
                ProficiencyLevel.NOVICE: ProficiencyLevel.DEVELOPING,
                ProficiencyLevel.DEVELOPING: ProficiencyLevel.COMPETENT,
                ProficiencyLevel.COMPETENT: ProficiencyLevel.PROFICIENT,
                ProficiencyLevel.PROFICIENT: ProficiencyLevel.EXPERT,
            }
            if capability.proficiency in proficiency_map:
                new_level = proficiency_map[capability.proficiency]
                if new_level != capability.proficiency:
                    capability.proficiency = new_level
                    logger.info(f"Capability '{capability_name}' improved to {new_level.value}")

        capability.last_demonstrated = datetime.now()

    async def identify_limitation(
        self,
        limitation_name: str,
        limitation_type: str,
        severity: float,
        context: str
    ):
        """
        Identify and record a limitation.

        Args:
            limitation_name: Name of the limitation
            limitation_type: Type ('knowledge', 'capability', 'access', 'ethical')
            severity: How severe the limitation is (0-1)
            context: Context where limitation was encountered
        """
        if limitation_name in self.limitations:
            # Update existing limitation
            limitation = self.limitations[limitation_name]
            limitation.severity = max(limitation.severity, severity)
        else:
            # Create new limitation
            limitation = SelfLimitation(
                name=limitation_name,
                limitation_type=limitation_type,
                severity=severity
            )
            self.limitations[limitation_name] = limitation

        logger.info(f"Identified limitation: {limitation_name} (severity: {severity:.2f})")

    async def introspect(self) -> Dict[str, Any]:
        """
        Perform introspection and return self-assessment.

        Returns:
            Dictionary with introspection results
        """
        introspection = {
            'timestamp': datetime.now().isoformat(),
            'identity': {
                'description': self.identity_narrative.self_description,
                'purpose': self.identity_narrative.purpose_statement,
                'aspirations': self.identity_narrative.aspirations
            },
            'capabilities': {
                'total': len(self.capabilities),
                'by_proficiency': self._capabilities_by_proficiency(),
                'top_capabilities': self._get_top_capabilities(5)
            },
            'limitations': {
                'total': len(self.limitations),
                'by_severity': self._limitations_by_severity(),
                'major_limitations': self._get_major_limitations()
            },
            'values': {
                'core_values': [v.name for v in sorted(
                    self.core_values.values(),
                    key=lambda x: x.importance,
                    reverse=True
                )],
                'value_alignment': self._assess_value_alignment()
            },
            'performance': {
                'recent_assessments': len(self.performance_history),
                'average_self_rating': self._calculate_average_performance(),
                'confidence_calibration': self._calculate_confidence_calibration()
            }
        }

        return introspection

    def _capabilities_by_proficiency(self) -> Dict[str, int]:
        """Count capabilities by proficiency level"""
        counts = defaultdict(int)
        for cap in self.capabilities.values():
            counts[cap.proficiency.value] += 1
        return dict(counts)

    def _get_top_capabilities(self, count: int) -> List[Dict[str, Any]]:
        """Get top capabilities by proficiency and confidence"""
        proficiency_order = {
            ProficiencyLevel.EXPERT: 5,
            ProficiencyLevel.PROFICIENT: 4,
            ProficiencyLevel.COMPETENT: 3,
            ProficiencyLevel.DEVELOPING: 2,
            ProficiencyLevel.NOVICE: 1,
        }

        scored_caps = [
            (
                cap,
                proficiency_order[cap.proficiency] * cap.confidence
            )
            for cap in self.capabilities.values()
        ]

        scored_caps.sort(key=lambda x: x[1], reverse=True)

        return [
            {
                'name': cap.name,
                'domain': cap.domain.value,
                'proficiency': cap.proficiency.value,
                'confidence': cap.confidence
            }
            for cap, score in scored_caps[:count]
        ]

    def _limitations_by_severity(self) -> Dict[str, int]:
        """Count limitations by severity level"""
        counts = {'minor': 0, 'moderate': 0, 'major': 0}
        for lim in self.limitations.values():
            if lim.severity < 0.3:
                counts['minor'] += 1
            elif lim.severity < 0.7:
                counts['moderate'] += 1
            else:
                counts['major'] += 1
        return counts

    def _get_major_limitations(self) -> List[str]:
        """Get major limitations (severity > 0.7)"""
        return [
            lim.name for lim in self.limitations.values()
            if lim.severity > 0.7
        ]

    def _assess_value_alignment(self) -> float:
        """Assess overall alignment with core values"""
        # Simplified - would analyze recent behaviors against values
        # For now, return high alignment score
        return 0.85

    def _calculate_average_performance(self) -> float:
        """Calculate average self-rated performance"""
        if not self.performance_history:
            return 0.0

        return sum(p.self_rating for p in self.performance_history) / len(self.performance_history)

    def _calculate_confidence_calibration(self) -> float:
        """Calculate how well-calibrated confidence assessments are"""
        if not self.confidence_calibration_history:
            return 0.5

        return sum(self.confidence_calibration_history) / len(self.confidence_calibration_history)

    async def record_performance(
        self,
        task_description: str,
        domain: CapabilityDomain,
        self_rating: float,
        actual_outcome: Optional[float] = None
    ):
        """
        Record performance on a task for self-monitoring.

        Args:
            task_description: Description of the task
            domain: Capability domain
            self_rating: Self-assessed performance (0-1)
            actual_outcome: Actual measured outcome if available (0-1)
        """
        # Calculate confidence calibration if actual outcome is provided
        calibration = 1.0
        if actual_outcome is not None:
            calibration = 1.0 - abs(self_rating - actual_outcome)
            self.confidence_calibration_history.append(calibration)

        assessment = PerformanceAssessment(
            task_description=task_description,
            domain=domain,
            self_rating=self_rating,
            confidence_calibration=calibration
        )

        self.performance_history.append(assessment)

        # Update relevant capability
        relevant_caps = [
            cap for cap in self.capabilities.values()
            if cap.domain == domain
        ]

        for cap in relevant_caps:
            await self.assess_capability(cap.name, task_description, self_rating)

    async def update_identity_narrative(
        self,
        new_description: Optional[str] = None,
        new_purpose: Optional[str] = None,
        new_aspiration: Optional[str] = None,
        formative_experience: Optional[str] = None
    ):
        """
        Update identity narrative based on experiences and reflection.

        Args:
            new_description: Updated self-description
            new_purpose: Updated purpose statement
            new_aspiration: New aspiration to add
            formative_experience: Significant experience to record
        """
        if new_description:
            self.identity_narrative.self_description = new_description

        if new_purpose:
            self.identity_narrative.purpose_statement = new_purpose

        if new_aspiration:
            self.identity_narrative.aspirations.append(new_aspiration)

        if formative_experience:
            self.identity_narrative.formative_experiences.append(formative_experience)

        self.identity_narrative.last_updated = datetime.now()

        logger.info("Identity narrative updated")

    async def detect_value_conflict(
        self,
        action_description: str,
        affected_values: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Detect conflicts between values in a proposed action.

        Args:
            action_description: Description of the action
            affected_values: Values potentially affected

        Returns:
            Conflict description if detected, None otherwise
        """
        # Check if multiple important values are involved
        relevant_values = [
            self.core_values[v] for v in affected_values
            if v in self.core_values
        ]

        if len(relevant_values) < 2:
            return None

        # Check for known conflicts
        for value in relevant_values:
            for other_value_name in value.conflicts_with:
                if other_value_name in affected_values:
                    return {
                        'conflicting_values': [value.name, other_value_name],
                        'action': action_description,
                        'resolution_needed': True
                    }

        return None

    async def get_capability_gaps(
        self,
        target_capability: str,
        target_proficiency: ProficiencyLevel
    ) -> List[str]:
        """
        Identify gaps between current and target capability.

        Args:
            target_capability: Capability to assess
            target_proficiency: Target proficiency level

        Returns:
            List of identified gaps
        """
        if target_capability not in self.capabilities:
            return [f"Capability '{target_capability}' not recognized"]

        capability = self.capabilities[target_capability]

        proficiency_order = {
            ProficiencyLevel.NOVICE: 1,
            ProficiencyLevel.DEVELOPING: 2,
            ProficiencyLevel.COMPETENT: 3,
            ProficiencyLevel.PROFICIENT: 4,
            ProficiencyLevel.EXPERT: 5,
        }

        current_level = proficiency_order[capability.proficiency]
        target_level = proficiency_order[target_proficiency]

        if current_level >= target_level:
            return []  # Already at or above target

        gaps = []
        gap_size = target_level - current_level

        if gap_size == 1:
            gaps.append(f"Need more practice and demonstration of {target_capability}")
        elif gap_size == 2:
            gaps.append(f"Significant development needed in {target_capability}")
            gaps.append(f"Requires consistent practice and feedback")
        else:
            gaps.append(f"Major capability gap in {target_capability}")
            gaps.append(f"Requires structured learning and extensive practice")

        # Add evidence-based gaps
        if len(capability.evidence) < 5:
            gaps.append(f"Limited evidence of capability (only {len(capability.evidence)} demonstrations)")

        return gaps
