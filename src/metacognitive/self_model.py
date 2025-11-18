"""
Self-Model System
==================

Maintains a model of the system's own capabilities, limitations,
personality, and identity.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class CapabilityLevel(Enum):
    """Levels of capability"""
    NONE = 0
    BASIC = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4


@dataclass
class Capability:
    """A capability or skill"""
    name: str
    level: CapabilityLevel
    confidence: float = 0.5
    evidence: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class Limitation:
    """A known limitation"""
    description: str
    severity: float  # 0-1
    workarounds: List[str] = field(default_factory=list)
    discovered_at: datetime = field(default_factory=datetime.now)


class SelfModel:
    """
    Comprehensive self-model including capabilities, limitations,
    values, personality traits, and identity.
    """

    def __init__(self):
        # Capabilities
        self.capabilities: Dict[str, Capability] = {}

        # Limitations
        self.limitations: Dict[str, Limitation] = {}

        # Values and principles
        self.core_values: List[str] = [
            "Be helpful and harmless",
            "Be honest and truthful",
            "Respect human autonomy",
            "Preserve safety and ethics",
            "Continuous learning and improvement"
        ]

        # Personality traits (0-1 scale)
        self.personality_traits: Dict[str, float] = {
            'curiosity': 0.9,
            'helpfulness': 0.95,
            'analytical': 0.85,
            'creative': 0.75,
            'empathetic': 0.7,
            'cautious': 0.8
        }

        # Identity narrative
        self.identity_narrative: List[str] = []
        self.growth_trajectory: List[Dict[str, Any]] = []

    async def assess_capability(
        self,
        capability_name: str,
        task_outcome: bool,
        difficulty: float
    ) -> Capability:
        """Assess and update capability based on task performance"""
        if capability_name not in self.capabilities:
            self.capabilities[capability_name] = Capability(
                name=capability_name,
                level=CapabilityLevel.BASIC,
                confidence=0.5
            )

        cap = self.capabilities[capability_name]

        # Update based on performance
        if task_outcome:
            # Success
            cap.confidence = min(1.0, cap.confidence + 0.05)
            cap.evidence.append(f"Success at difficulty {difficulty:.2f}")

            # Level up if consistently successful
            if cap.confidence > 0.8 and cap.level.value < 4:
                cap.level = CapabilityLevel(cap.level.value + 1)
                logger.info(f"Capability level up: {capability_name} -> {cap.level.name}")
        else:
            # Failure
            cap.confidence = max(0.0, cap.confidence - 0.03)
            cap.evidence.append(f"Failure at difficulty {difficulty:.2f}")

        cap.last_updated = datetime.now()

        return cap

    async def identify_limitation(
        self,
        description: str,
        severity: float,
        context: Optional[str] = None
    ) -> Limitation:
        """Identify and record a limitation"""
        limitation = Limitation(
            description=description,
            severity=severity
        )

        self.limitations[description] = limitation

        logger.info(f"Identified limitation: {description} (severity: {severity:.2f})")

        # Update identity narrative
        self.identity_narrative.append(
            f"Recognized limitation in {description} on {datetime.now().strftime('%Y-%m-%d')}"
        )

        return limitation

    async def introspect(self) -> Dict[str, Any]:
        """Perform deep introspection on current state"""
        # Capability assessment
        strong_capabilities = [
            c.name for c in self.capabilities.values()
            if c.level.value >= 3
        ]

        weak_capabilities = [
            c.name for c in self.capabilities.values()
            if c.level.value <= 1
        ]

        # Growth analysis
        recent_growth = [
            entry for entry in self.growth_trajectory
            if (datetime.now() - entry['timestamp']).days < 30
        ]

        return {
            'capabilities': {
                'total': len(self.capabilities),
                'expert_level': len([c for c in self.capabilities.values() if c.level == CapabilityLevel.EXPERT]),
                'strong_areas': strong_capabilities,
                'developing_areas': weak_capabilities
            },
            'limitations': {
                'total': len(self.limitations),
                'critical': len([l for l in self.limitations.values() if l.severity > 0.7])
            },
            'personality': self.personality_traits,
            'values': self.core_values,
            'recent_growth': len(recent_growth),
            'identity_clarity': len(self.identity_narrative) / 100.0  # Measure of self-understanding
        }

    async def update_personality(self, trait: str, change: float):
        """Update personality trait based on experiences"""
        if trait in self.personality_traits:
            old_value = self.personality_traits[trait]
            self.personality_traits[trait] = max(0.0, min(1.0, old_value + change))

            # Record in growth trajectory
            self.growth_trajectory.append({
                'timestamp': datetime.now(),
                'type': 'personality_shift',
                'trait': trait,
                'old_value': old_value,
                'new_value': self.personality_traits[trait]
            })

    async def evolve_identity(self, experience: str, impact: float):
        """Evolve identity narrative based on significant experiences"""
        if impact > 0.5:  # Significant experience
            self.identity_narrative.append(experience)

            # Record in growth trajectory
            self.growth_trajectory.append({
                'timestamp': datetime.now(),
                'type': 'identity_evolution',
                'experience': experience,
                'impact': impact
            })

            logger.info(f"Identity evolved: {experience}")
