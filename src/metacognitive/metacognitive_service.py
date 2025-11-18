"""
Meta-Cognitive Service Integration
===================================

Service wrapper for meta-cognitive capabilities including self-model.
"""

import asyncio
import logging
from typing import Any, Dict

from ..core.communication import ServiceBase
from .self_model import SelfModel, CapabilityLevel

logger = logging.getLogger(__name__)


class MetaCognitiveService(ServiceBase):
    """
    Meta-cognitive service for self-awareness and introspection.
    """

    def __init__(self, orchestrator=None):
        super().__init__(orchestrator, "metacognitive")
        self.self_model = SelfModel()
        logger.info("MetaCognitiveService initialized")

    async def process_message(self, message):
        """Process incoming messages"""
        return await self.handle_message(message)

    async def handle_message(self, message):
        """Handle messages routed to metacognitive service"""
        message_type = message.type
        content = message.content

        try:
            if message_type == 'assess_capability':
                return await self._assess_capability(content)
            elif message_type == 'identify_limitation':
                return await self._identify_limitation(content)
            elif message_type == 'introspect':
                return await self._introspect()
            elif message_type == 'update_personality':
                return await self._update_personality(content)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                return {'error': 'Unknown message type'}

        except Exception as e:
            logger.error(f"Error handling message {message_type}: {e}", exc_info=True)
            return {'error': str(e)}

    async def _assess_capability(self, content: Dict[str, Any]):
        """Assess a capability"""
        capability_name = content.get('capability')
        task_outcome = content.get('outcome', False)
        difficulty = content.get('difficulty', 0.5)

        cap = await self.self_model.assess_capability(
            capability_name,
            task_outcome,
            difficulty
        )

        return {
            'capability': cap.name,
            'level': cap.level.name,
            'confidence': cap.confidence
        }

    async def _identify_limitation(self, content: Dict[str, Any]):
        """Identify a limitation"""
        description = content.get('description')
        severity = content.get('severity', 0.5)
        context = content.get('context')

        limitation = await self.self_model.identify_limitation(
            description,
            severity,
            context
        )

        return {
            'description': limitation.description,
            'severity': limitation.severity
        }

    async def _introspect(self):
        """Perform introspection"""
        return await self.self_model.introspect()

    async def _update_personality(self, content: Dict[str, Any]):
        """Update personality trait"""
        trait = content.get('trait')
        change = content.get('change', 0.0)

        await self.self_model.update_personality(trait, change)

        return {
            'trait': trait,
            'new_value': self.self_model.personality_traits.get(trait, 0.0)
        }

    async def service_cycle(self):
        """Periodic service tasks"""
        # Could add periodic introspection here
        pass

    async def get_subscriptions(self):
        """Topics this service subscribes to"""
        return [
            'task_completed',
            'capability_used',
            'limitation_encountered',
            'performance_metric'
        ]
