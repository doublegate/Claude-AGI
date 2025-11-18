"""
Web Service Integration
========================

Service wrapper for web capabilities including fact verification.
"""

import asyncio
import logging
from typing import Any, Dict

from ..core.communication import ServiceBase
from .fact_verification import FactVerificationSystem

logger = logging.getLogger(__name__)


class WebService(ServiceBase):
    """
    Web service for fact verification and web exploration.
    """

    def __init__(self, orchestrator=None):
        super().__init__(orchestrator, "web_system")
        self.fact_verifier = FactVerificationSystem()
        logger.info("WebService initialized")

    async def process_message(self, message):
        """Process incoming messages"""
        return await self.handle_message(message)

    async def handle_message(self, message):
        """Handle messages routed to web service"""
        message_type = message.type
        content = message.content

        try:
            if message_type == 'verify_fact':
                return await self._verify_fact(content)
            elif message_type == 'check_consistency':
                return await self._check_consistency(content)
            elif message_type == 'get_verification_insights':
                return await self._get_insights()
            else:
                logger.warning(f"Unknown message type: {message_type}")
                return {'error': 'Unknown message type'}

        except Exception as e:
            logger.error(f"Error handling message {message_type}: {e}", exc_info=True)
            return {'error': str(e)}

    async def _verify_fact(self, content: Dict[str, Any]):
        """Verify a factual claim"""
        claim_text = content.get('claim', '')
        domain = content.get('domain', 'general')
        sources = content.get('sources', [])

        claim = await self.fact_verifier.verify_fact(claim_text, domain, sources)

        return {
            'claim_id': claim.claim_id,
            'status': claim.status.value,
            'confidence': claim.confidence,
            'sources_supporting': len(claim.sources_supporting),
            'sources_contradicting': len(claim.sources_contradicting)
        }

    async def _check_consistency(self, content: Dict[str, Any]):
        """Check consistency across claims"""
        claims = content.get('claims', [])
        domain = content.get('domain', 'general')

        result = await self.fact_verifier.check_consistency(claims, domain)
        return result

    async def _get_insights(self):
        """Get fact verification insights"""
        return await self.fact_verifier.get_verification_insights()

    async def service_cycle(self):
        """Periodic service tasks"""
        # Could add periodic verification cleanup here
        pass

    async def get_subscriptions(self):
        """Topics this service subscribes to"""
        return [
            'fact_claim_made',
            'verification_requested',
            'source_encountered'
        ]
