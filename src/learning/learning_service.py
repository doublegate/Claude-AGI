"""
Learning Service Integration
=============================

Service wrapper that integrates all learning components with the orchestrator.
"""

import asyncio
import logging
from typing import Any, Dict

from ..core.communication import ServiceBase
from .goal_manager import GoalManager
from .knowledge_graph import KnowledgeGraph
from .skill_system import SkillSystem
from .transfer_learning import TransferLearningEngine

logger = logging.getLogger(__name__)


class LearningService(ServiceBase):
    """
    Integrated learning service that coordinates goal management,
    knowledge representation, skill acquisition, and transfer learning.
    """

    def __init__(self, orchestrator=None):
        super().__init__(orchestrator, "learning_system")

        # Initialize all learning components
        self.goal_manager = GoalManager()
        self.knowledge_graph = KnowledgeGraph()
        self.skill_system = SkillSystem()
        self.transfer_engine = TransferLearningEngine()

        logger.info("LearningService initialized with all components")

    async def process_message(self, message):
        """Process incoming messages"""
        return await self.handle_message(message)

    async def handle_message(self, message):
        """Handle messages routed to learning service"""
        message_type = message.type
        content = message.content

        try:
            if message_type == 'create_goal':
                return await self._handle_create_goal(content)
            elif message_type == 'update_goal_progress':
                return await self._handle_update_goal_progress(content)
            elif message_type == 'add_knowledge':
                return await self._handle_add_knowledge(content)
            elif message_type == 'query_knowledge':
                return await self._handle_query_knowledge(content)
            elif message_type == 'practice_skill':
                return await self._handle_practice_skill(content)
            elif message_type == 'get_learning_status':
                return await self._get_learning_status()
            else:
                logger.warning(f"Unknown message type: {message_type}")
                return {'error': 'Unknown message type'}

        except Exception as e:
            logger.error(f"Error handling message {message_type}: {e}", exc_info=True)
            return {'error': str(e)}

    async def _handle_create_goal(self, content: Dict[str, Any]):
        """Handle goal creation"""
        from .goal_manager import GoalType, GoalPriority

        goal = await self.goal_manager.create_goal(
            description=content.get('description', ''),
            goal_type=GoalType[content.get('goal_type', 'SESSION')],
            priority=GoalPriority[content.get('priority', 'MEDIUM')],
            success_criteria=content.get('success_criteria', [])
        )

        # Auto-activate if requested
        if content.get('auto_activate', False):
            await self.goal_manager.activate_goal(goal.id)

        return {'goal_id': goal.id, 'status': goal.status.value}

    async def _handle_update_goal_progress(self, content: Dict[str, Any]):
        """Handle goal progress update"""
        goal_id = content.get('goal_id')
        progress = content.get('progress', 0.0)
        milestone = content.get('milestone')

        await self.goal_manager.update_progress(goal_id, progress, milestone)
        return {'goal_id': goal_id, 'progress': progress}

    async def _handle_add_knowledge(self, content: Dict[str, Any]):
        """Handle adding knowledge to graph"""
        concept_name = content.get('concept')
        concept_type = content.get('type', 'general')
        description = content.get('description', '')

        concept = await self.knowledge_graph.add_concept(
            name=concept_name,
            concept_type=concept_type,
            description=description
        )

        # Add relationships if provided
        if 'relationships' in content:
            for rel in content['relationships']:
                from .knowledge_graph import RelationType
                await self.knowledge_graph.add_relationship(
                    concept_name,
                    rel['target'],
                    RelationType[rel['type']]
                )

        return {'concept_id': concept.id, 'name': concept.name}

    async def _handle_query_knowledge(self, content: Dict[str, Any]):
        """Handle knowledge graph queries"""
        query_type = content.get('query_type', 'related')
        concept = content.get('concept')

        if query_type == 'related':
            related = await self.knowledge_graph.get_related_concepts(concept)
            return {
                'concept': concept,
                'related': [{'name': c.name, 'relation': r.relation_type.value}
                           for c, r in related[:10]]
            }
        elif query_type == 'path':
            target = content.get('target')
            path = await self.knowledge_graph.find_path(concept, target)
            return {'path': path}
        elif query_type == 'statistics':
            stats = await self.knowledge_graph.get_statistics()
            return stats

        return {'error': 'Unknown query type'}

    async def _handle_practice_skill(self, content: Dict[str, Any]):
        """Handle skill practice"""
        skill_name = content.get('skill_name')
        performance = content.get('performance', 0.5)
        success = content.get('success', False)
        duration = content.get('duration', 60.0)

        # Find or create skill
        from .skill_system import SkillDomain

        existing_skill = self.skill_system._find_skill_by_name(skill_name)

        if not existing_skill:
            # Create new skill
            domain = SkillDomain[content.get('domain', 'COGNITIVE')]
            existing_skill = await self.skill_system.create_skill(
                name=skill_name,
                domain=domain,
                description=content.get('description', f'Skill: {skill_name}')
            )

        # Practice the skill
        result = await self.skill_system.practice_skill(
            existing_skill.skill_id,
            duration,
            performance,
            success
        )

        # Check for transfer learning opportunities
        if success and existing_skill.proficiency > 0.5:
            # Identify transferable patterns
            pattern = await self.transfer_engine.identify_transferable_pattern(
                skill_name,
                existing_skill.domain.value,
                {'type': 'skill_practice', 'success': True}
            )

        return result

    async def _get_learning_status(self):
        """Get comprehensive learning status"""
        goal_insights = await self.goal_manager.reflect_on_progress()
        skill_insights = await self.skill_system.get_skill_insights()
        knowledge_stats = await self.knowledge_graph.get_statistics()
        transfer_effectiveness = await self.transfer_engine.analyze_transfer_effectiveness()

        return {
            'goals': goal_insights,
            'skills': skill_insights,
            'knowledge': knowledge_stats,
            'transfer_learning': transfer_effectiveness
        }

    async def service_cycle(self):
        """Periodic service tasks"""
        try:
            # Apply skill decay
            await self.skill_system.apply_skill_decay()

            # Prune weak knowledge connections
            await self.knowledge_graph.prune_weak_connections()

            # Meta-learn from transfer patterns
            await self.transfer_engine.meta_learn_from_transfers()

        except Exception as e:
            logger.error(f"Error in learning service cycle: {e}", exc_info=True)

    async def get_subscriptions(self):
        """Topics this service subscribes to"""
        return [
            'experience',
            'goal_created',
            'skill_used',
            'knowledge_acquired',
            'learning_opportunity'
        ]
