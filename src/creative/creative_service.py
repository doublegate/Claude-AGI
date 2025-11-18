"""
Creative Service Integration
=============================

Service wrapper for creative capabilities including novelty detection.
"""

import asyncio
import logging
from typing import Any, Dict

from ..core.communication import ServiceBase
from .novelty_detector import NoveltyDetector, CreativeWork

logger = logging.getLogger(__name__)


class CreativeService(ServiceBase):
    """
    Creative service for evaluating and generating creative works.
    """

    def __init__(self, orchestrator=None):
        super().__init__(orchestrator, "creative_system")
        self.novelty_detector = NoveltyDetector()
        logger.info("CreativeService initialized")

    async def process_message(self, message):
        """Process incoming messages"""
        return await self.handle_message(message)

    async def handle_message(self, message):
        """Handle messages routed to creative service"""
        message_type = message.type
        content = message.content

        try:
            if message_type == 'evaluate_novelty':
                return await self._evaluate_novelty(content)
            elif message_type == 'get_creative_insights':
                return await self._get_insights()
            else:
                logger.warning(f"Unknown message type: {message_type}")
                return {'error': 'Unknown message type'}

        except Exception as e:
            logger.error(f"Error handling message {message_type}: {e}", exc_info=True)
            return {'error': str(e)}

    async def _evaluate_novelty(self, content: Dict[str, Any]):
        """Evaluate novelty of creative work"""
        import uuid

        work = CreativeWork(
            work_id=content.get('work_id', str(uuid.uuid4())),
            content=content.get('content', ''),
            work_type=content.get('work_type', 'text')
        )

        result = await self.novelty_detector.evaluate_novelty(work)

        return result

    async def _get_insights(self):
        """Get creative insights"""
        return {
            'total_works': len(self.novelty_detector.existing_works),
            'patterns_tracked': len(self.novelty_detector.pattern_library),
            'novelty_threshold': self.novelty_detector.novelty_threshold
        }

    async def service_cycle(self):
        """Periodic service tasks"""
        # Could add periodic novelty analysis here
        pass

    async def get_subscriptions(self):
        """Topics this service subscribes to"""
        return [
            'creative_work_generated',
            'novelty_check_requested'
        ]
