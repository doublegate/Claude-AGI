"""
Reasoning Service Integration
==============================

Service wrapper for causal reasoning and prediction.
"""

import asyncio
import logging
from typing import Any, Dict

from ..core.communication import ServiceBase
from .causal_reasoner import CausalReasoner

logger = logging.getLogger(__name__)


class ReasoningService(ServiceBase):
    """
    Reasoning service for causal analysis and predictions.
    """

    def __init__(self, orchestrator=None):
        super().__init__(orchestrator, "reasoning")
        self.causal_reasoner = CausalReasoner()
        logger.info("ReasoningService initialized")

    async def process_message(self, message):
        """Process incoming messages"""
        return await self.handle_message(message)

    async def handle_message(self, message):
        """Handle messages routed to reasoning service"""
        message_type = message.type
        content = message.content

        try:
            if message_type == 'observe':
                return await self._observe(content)
            elif message_type == 'propose_causal_relationship':
                return await self._propose_relationship(content)
            elif message_type == 'predict_outcome':
                return await self._predict_outcome(content)
            elif message_type == 'get_causal_insights':
                return await self._get_insights()
            else:
                logger.warning(f"Unknown message type: {message_type}")
                return {'error': 'Unknown message type'}

        except Exception as e:
            logger.error(f"Error handling message {message_type}: {e}", exc_info=True)
            return {'error': str(e)}

    async def _observe(self, content: Dict[str, Any]):
        """Record observation"""
        observation = content.get('observation', {})
        await self.causal_reasoner.observe(observation)
        return {'status': 'observed', 'variables': len(observation)}

    async def _propose_relationship(self, content: Dict[str, Any]):
        """Propose causal relationship"""
        cause = content.get('cause')
        effect = content.get('effect')
        strength = content.get('strength', 0.5)
        confidence = content.get('confidence', 0.5)

        rel = await self.causal_reasoner.propose_causal_relationship(
            cause, effect, strength, confidence
        )

        return {
            'cause': rel.cause,
            'effect': rel.effect,
            'strength': rel.strength,
            'confidence': rel.confidence
        }

    async def _predict_outcome(self, content: Dict[str, Any]):
        """Predict outcomes based on interventions"""
        interventions = content.get('interventions', {})
        predictions = await self.causal_reasoner.predict_outcome(interventions)
        return {'predictions': predictions}

    async def _get_insights(self):
        """Get causal reasoning insights"""
        return await self.causal_reasoner.get_causal_insights()

    async def service_cycle(self):
        """Periodic service tasks"""
        # Could add periodic causal analysis here
        pass

    async def get_subscriptions(self):
        """Topics this service subscribes to"""
        return [
            'observation',
            'cause_effect_detected',
            'prediction_requested'
        ]
