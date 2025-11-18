"""
Relationship Management System
===============================

Tracks and models relationships with users, managing preferences,
trust levels, and interaction history.
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class RelationshipType(Enum):
    """Types of relationships"""
    CASUAL = "casual"
    REGULAR = "regular"
    COLLABORATIVE = "collaborative"
    MENTOR_MENTEE = "mentor_mentee"
    CLOSE = "close"


@dataclass
class UserProfile:
    """Profile of a user"""
    user_id: str
    name: str
    relationship_type: RelationshipType
    trust_level: float = 0.5
    emotional_bond: float = 0.0
    preferences: Dict[str, Any] = field(default_factory=dict)
    interaction_count: int = 0
    first_interaction: datetime = field(default_factory=datetime.now)
    last_interaction: datetime = field(default_factory=datetime.now)
    topics_of_interest: Set[str] = field(default_factory=set)
    communication_style: Dict[str, float] = field(default_factory=dict)
    shared_experiences: List[Dict[str, Any]] = field(default_factory=list)


class RelationshipManager:
    """
    Manages relationships with users including trust, preferences,
    and interaction history.

    Optionally integrates with MultiUserManager for enhanced
    multi-user support with context isolation and privacy.
    """

    def __init__(self, multi_user_manager=None):
        self.profiles: Dict[str, UserProfile] = {}
        self.interaction_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.current_user: Optional[str] = None
        self.multi_user_manager = multi_user_manager

    async def get_or_create_profile(self, user_id: str, name: str = None) -> UserProfile:
        """Get existing profile or create new one"""
        if user_id in self.profiles:
            return self.profiles[user_id]

        profile = UserProfile(
            user_id=user_id,
            name=name or f"User{user_id[:8]}",
            relationship_type=RelationshipType.CASUAL
        )

        self.profiles[user_id] = profile
        logger.info(f"Created new user profile: {profile.name}")
        return profile

    async def record_interaction(
        self,
        user_id: str,
        interaction_type: str,
        content: Dict[str, Any],
        sentiment: Optional[float] = None
    ):
        """Record an interaction with a user"""
        profile = await self.get_or_create_profile(user_id)

        profile.interaction_count += 1
        profile.last_interaction = datetime.now()

        # Record interaction
        self.interaction_history[user_id].append({
            'timestamp': datetime.now(),
            'type': interaction_type,
            'content': content,
            'sentiment': sentiment
        })

        # Update relationship metrics
        await self._update_relationship_metrics(user_id, interaction_type, sentiment)

        # Learn preferences
        await self._learn_preferences(user_id, content)

    async def _update_relationship_metrics(
        self,
        user_id: str,
        interaction_type: str,
        sentiment: Optional[float]
    ):
        """Update trust and emotional bond based on interaction"""
        profile = self.profiles[user_id]

        # Increase trust with positive interactions
        if sentiment and sentiment > 0.5:
            profile.trust_level = min(1.0, profile.trust_level + 0.01)
            profile.emotional_bond = min(1.0, profile.emotional_bond + 0.005)

        # Regular interactions strengthen bond
        profile.emotional_bond = min(1.0, profile.emotional_bond + 0.001)

        # Update relationship type based on metrics
        if profile.interaction_count > 100 and profile.emotional_bond > 0.7:
            profile.relationship_type = RelationshipType.CLOSE
        elif profile.interaction_count > 50 and profile.trust_level > 0.6:
            profile.relationship_type = RelationshipType.COLLABORATIVE
        elif profile.interaction_count > 20:
            profile.relationship_type = RelationshipType.REGULAR

    async def _learn_preferences(self, user_id: str, content: Dict[str, Any]):
        """Learn user preferences from interactions"""
        profile = self.profiles[user_id]

        # Extract topics
        if 'topics' in content:
            profile.topics_of_interest.update(content['topics'])

        # Learn communication preferences
        if 'style' in content:
            style = content['style']
            if style not in profile.communication_style:
                profile.communication_style[style] = 0
            profile.communication_style[style] += 1

    async def get_personalized_response_style(self, user_id: str) -> Dict[str, Any]:
        """Get personalized response style for user"""
        if user_id not in self.profiles:
            return {
                'formality': 'medium',
                'detail_level': 'medium',
                'humor': False
            }

        profile = self.profiles[user_id]

        # Adjust based on relationship
        if profile.relationship_type == RelationshipType.CLOSE:
            return {
                'formality': 'casual',
                'detail_level': 'high',
                'humor': True,
                'personal_references': True
            }
        elif profile.relationship_type == RelationshipType.COLLABORATIVE:
            return {
                'formality': 'professional',
                'detail_level': 'high',
                'humor': False,
                'focus': 'productivity'
            }
        else:
            return {
                'formality': 'polite',
                'detail_level': 'medium',
                'humor': False
            }

    async def get_relationship_insights(self) -> Dict[str, Any]:
        """Get insights about relationships"""
        total_users = len(self.profiles)

        if total_users == 0:
            return {'message': 'No relationships yet'}

        relationship_distribution = defaultdict(int)
        for profile in self.profiles.values():
            relationship_distribution[profile.relationship_type.value] += 1

        avg_trust = sum(p.trust_level for p in self.profiles.values()) / total_users
        avg_bond = sum(p.emotional_bond for p in self.profiles.values()) / total_users

        return {
            'total_users': total_users,
            'relationship_distribution': dict(relationship_distribution),
            'average_trust_level': avg_trust,
            'average_emotional_bond': avg_bond,
            'close_relationships': relationship_distribution['close']
        }

    async def switch_user_context(self, user_id: str):
        """
        Switch to a different user's context.

        Uses MultiUserManager if available for enhanced isolation.

        Args:
            user_id: User to switch to
        """
        if self.multi_user_manager:
            # Use multi-user manager's session switching
            sessions = await self.multi_user_manager.get_user_sessions(user_id)
            if sessions:
                # Switch to most recent session
                await self.multi_user_manager.switch_to_session(sessions[-1].session_id)
            else:
                # Create new session if none exists
                session = await self.multi_user_manager.create_session(user_id)
                await self.multi_user_manager.switch_to_session(session.session_id)

        # Update current user
        self.current_user = user_id
        logger.info(f"Switched to user context: {user_id}")

    async def get_current_user_id(self) -> Optional[str]:
        """
        Get the currently active user ID.

        Uses MultiUserManager if available for accurate session tracking.

        Returns:
            Current user ID or None
        """
        if self.multi_user_manager:
            return await self.multi_user_manager.get_current_user_id()
        return self.current_user

    async def get_profile_for_current_user(self) -> Optional[UserProfile]:
        """Get profile for currently active user"""
        user_id = await self.get_current_user_id()
        if user_id and user_id in self.profiles:
            return self.profiles[user_id]
        return None
