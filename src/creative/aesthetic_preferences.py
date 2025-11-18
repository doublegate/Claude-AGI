"""
Aesthetic Preference Learning for Claude-AGI
=============================================

Develops and tracks aesthetic preferences including:
- Pattern preference learning from experience
- Style development and evolution
- Aesthetic judgment formation
- Creative signature recognition
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AestheticDimension(Enum):
    """Dimensions of aesthetic judgment"""
    SYMMETRY = "symmetry"
    COMPLEXITY = "complexity"
    HARMONY = "harmony"
    CONTRAST = "contrast"
    ORIGINALITY = "originality"
    ELEGANCE = "elegance"
    PLAYFULNESS = "playfulness"
    MINIMALISM = "minimalism"


@dataclass
class AestheticProfile:
    """User's aesthetic preferences"""
    preferences: Dict[AestheticDimension, float] = field(default_factory=dict)
    style_signatures: List[str] = field(default_factory=list)
    favorite_patterns: List[str] = field(default_factory=list)
    evolution_history: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


class AestheticLearner:
    """Learns and evolves aesthetic preferences"""

    def __init__(self):
        self.profile = AestheticProfile()
        self.exposure_history: List[Dict[str, Any]] = []

        # Initialize neutral preferences
        for dimension in AestheticDimension:
            self.profile.preferences[dimension] = 0.5

    async def rate_aesthetic(
        self,
        item: str,
        dimensions: Dict[AestheticDimension, float],
        rating: float
    ):
        """Learn from aesthetic rating"""
        self.exposure_history.append({
            'item': item,
            'dimensions': dimensions,
            'rating': rating,
            'timestamp': datetime.now()
        })

        # Update preferences based on rating
        learning_rate = 0.1
        for dim, value in dimensions.items():
            if rating > 0.7:  # Positive rating
                # Move preference toward this value
                current = self.profile.preferences[dim]
                self.profile.preferences[dim] = current + learning_rate * (value - current)
            elif rating < 0.3:  # Negative rating
                # Move preference away from this value
                current = self.profile.preferences[dim]
                self.profile.preferences[dim] = current - learning_rate * (value - current)

        self.profile.last_updated = datetime.now()

    async def get_aesthetic_judgment(
        self,
        item_dimensions: Dict[AestheticDimension, float]
    ) -> float:
        """Predict aesthetic judgment for item"""
        total_match = 0.0
        for dim, value in item_dimensions.items():
            preference = self.profile.preferences.get(dim, 0.5)
            # Calculate how well this matches preference
            match = 1.0 - abs(preference - value)
            total_match += match

        return total_match / len(item_dimensions) if item_dimensions else 0.5

    async def get_signature_style(self) -> Dict[str, Any]:
        """Get current aesthetic signature"""
        # Find dominant preferences
        strong_preferences = {
            dim.value: score
            for dim, score in self.profile.preferences.items()
            if score > 0.7 or score < 0.3
        }

        return {
            'preferences': strong_preferences,
            'style_keywords': self.profile.style_signatures,
            'maturity': len(self.exposure_history) / 100  # Style maturity score
        }

    async def get_statistics(self) -> Dict[str, Any]:
        """Get learning statistics"""
        return {
            'exposures': len(self.exposure_history),
            'preferences': {
                dim.value: round(score, 2)
                for dim, score in self.profile.preferences.items()
            },
            'last_updated': self.profile.last_updated.isoformat()
        }
