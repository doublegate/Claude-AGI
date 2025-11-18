"""
Social Intelligence Service Integration
========================================

Service wrapper for social intelligence and relationship management.
"""

import asyncio
import logging
from typing import Any, Dict

from ..core.communication import ServiceBase
from .relationship_manager import RelationshipManager

logger = logging.getLogger(__name__)


class SocialService(ServiceBase):
    """
    Social intelligence service managing user relationships and interactions.
    """

    def __init__(self, orchestrator=None):
        super().__init__(orchestrator, "social_intelligence")
        self.relationship_manager = RelationshipManager()
        logger.info("SocialService initialized")

    async def process_message(self, message):
        """Process incoming messages"""
        return await self.handle_message(message)

    async def handle_message(self, message):
        """Handle messages routed to social service"""
        message_type = message.type
        content = message.content

        try:
            if message_type == 'user_interaction':
                return await self._handle_interaction(content)
            elif message_type == 'get_user_profile':
                return await self._get_user_profile(content)
            elif message_type == 'get_response_style':
                return await self._get_response_style(content)
            elif message_type == 'get_relationship_insights':
                return await self._get_insights()
            else:
                logger.warning(f"Unknown message type: {message_type}")
                return {'error': 'Unknown message type'}

        except Exception as e:
            logger.error(f"Error handling message {message_type}: {e}", exc_info=True)
            return {'error': str(e)}

    async def _handle_interaction(self, content: Dict[str, Any]):
        """Record and process user interaction"""
        user_id = content.get('user_id')
        interaction_type = content.get('type', 'conversation')
        interaction_content = content.get('content', {})
        sentiment = content.get('sentiment')

        await self.relationship_manager.record_interaction(
            user_id,
            interaction_type,
            interaction_content,
            sentiment
        )

        return {'status': 'recorded', 'user_id': user_id}

    async def _get_user_profile(self, content: Dict[str, Any]):
        """Get user profile"""
        user_id = content.get('user_id')
        name = content.get('name')

        profile = await self.relationship_manager.get_or_create_profile(user_id, name)

        return {
            'user_id': profile.user_id,
            'name': profile.name,
            'relationship_type': profile.relationship_type.value,
            'trust_level': profile.trust_level,
            'emotional_bond': profile.emotional_bond,
            'interaction_count': profile.interaction_count
        }

    async def _get_response_style(self, content: Dict[str, Any]):
        """Get personalized response style for user"""
        user_id = content.get('user_id')

        style = await self.relationship_manager.get_personalized_response_style(user_id)
        return style

    async def _get_insights(self):
        """Get relationship insights"""
        return await self.relationship_manager.get_relationship_insights()

    async def service_cycle(self):
        """Periodic service tasks"""
        # Could add relationship maintenance tasks here
        pass

    async def get_subscriptions(self):
        """Topics this service subscribes to"""
        return [
            'user_message',
            'interaction_event',
            'sentiment_detected'
        ]
