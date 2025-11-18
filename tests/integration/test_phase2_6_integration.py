"""
Integration Tests for Phase 2-6 Services with Refactored Orchestrator
======================================================================

Verifies all Phase 2-6 services are properly registered and can communicate.
"""

import pytest
import asyncio
from unittest.mock import patch

from src.core.orchestrator_refactored import AGIOrchestrator
from src.core.event_bus import Message, Priority
from src.learning.goal_manager import GoalType, GoalPriority
from src.learning.knowledge_graph import RelationType
from src.learning.skill_system import SkillDomain


class TestPhase2To6Integration:
    """Test integration of Phase 2-6 services with refactored orchestrator"""

    @pytest.fixture
    async def orchestrator(self):
        """Create and initialize orchestrator with all services"""
        with patch('src.core.orchestrator_refactored.os.environ.get', return_value='1'):
            orch = AGIOrchestrator()
            await orch.initialize()
            yield orch
            await orch.shutdown()

    @pytest.mark.asyncio
    async def test_all_services_registered(self, orchestrator):
        """Test that all Phase 1-6 services are registered"""
        services = orchestrator.service_registry.list_services()

        # Phase 1 Core Infrastructure
        assert 'memory' in services
        assert 'consciousness' in services
        assert 'safety' in services

        # Phase 1 Cognitive
        assert 'emotional' in services
        assert 'learning' in services
        assert 'explorer' in services
        assert 'creative' in services
        assert 'meta' in services
        assert 'social' in services

        # Phase 2 Advanced
        assert 'learning_system' in services
        assert 'web_system' in services
        assert 'self_modification' in services

        # Phase 3 Social
        assert 'social_system' in services

        # Phase 4 Creative
        assert 'creative_system' in services

        # Phase 5 Meta-Cognitive
        assert 'metacognitive_system' in services

        # Phase 6 Reasoning
        assert 'reasoning_system' in services

    @pytest.mark.asyncio
    async def test_learning_service_create_goal(self, orchestrator):
        """Test learning service can create goals"""
        learning = orchestrator.get_service('learning_system')
        assert learning is not None

        message = Message(
            source='test',
            target='learning_system',
            type='create_goal',
            content={
                'description': 'Test learning goal',
                'goal_type': 'SESSION',
                'priority': 'HIGH',
                'success_criteria': ['Complete test']
            }
        )

        response = await learning.handle_message(message)
        assert 'goal_id' in response
        assert response['status'] == 'PROPOSED'

    @pytest.mark.asyncio
    async def test_learning_service_add_knowledge(self, orchestrator):
        """Test learning service can add knowledge to graph"""
        learning = orchestrator.get_service('learning_system')

        message = Message(
            source='test',
            target='learning_system',
            type='add_knowledge',
            content={
                'concept': 'Test Concept',
                'type': 'idea',
                'description': 'A test concept'
            }
        )

        response = await learning.handle_message(message)
        assert 'concept_id' in response
        assert response['name'] == 'Test Concept'

    @pytest.mark.asyncio
    async def test_learning_service_practice_skill(self, orchestrator):
        """Test learning service skill practice"""
        learning = orchestrator.get_service('learning_system')

        message = Message(
            source='test',
            target='learning_system',
            type='practice_skill',
            content={
                'skill_name': 'Test Skill',
                'domain': 'COGNITIVE',
                'performance': 0.8,
                'success': True,
                'duration': 60.0
            }
        )

        response = await learning.handle_message(message)
        assert 'new_proficiency' in response
        assert response['new_proficiency'] > 0.0

    @pytest.mark.asyncio
    async def test_social_service_user_interaction(self, orchestrator):
        """Test social service handles user interactions"""
        social = orchestrator.get_service('social_system')
        assert social is not None

        message = Message(
            source='test',
            target='social_system',
            type='user_interaction',
            content={
                'user_id': 'test_user',
                'interaction_type': 'message',
                'sentiment': 0.8,
                'content': 'Hello, how are you?'
            }
        )

        response = await social.handle_message(message)
        assert 'user_id' in response
        assert response['user_id'] == 'test_user'

    @pytest.mark.asyncio
    async def test_creative_service_evaluate_novelty(self, orchestrator):
        """Test creative service novelty evaluation"""
        creative = orchestrator.get_service('creative_system')
        assert creative is not None

        message = Message(
            source='test',
            target='creative_system',
            type='evaluate_novelty',
            content={
                'content': 'A unique creative idea about quantum consciousness',
                'work_type': 'text'
            }
        )

        response = await creative.handle_message(message)
        assert 'novelty_score' in response
        assert 'is_novel' in response

    @pytest.mark.asyncio
    async def test_web_service_verify_fact(self, orchestrator):
        """Test web service fact verification"""
        web = orchestrator.get_service('web_system')
        assert web is not None

        message = Message(
            source='test',
            target='web_system',
            type='verify_fact',
            content={
                'claim': 'Water is composed of H2O',
                'sources': []
            }
        )

        response = await web.handle_message(message)
        assert 'claim' in response
        assert 'confidence' in response

    @pytest.mark.asyncio
    async def test_metacognitive_service_assess_capability(self, orchestrator):
        """Test metacognitive service capability assessment"""
        meta = orchestrator.get_service('metacognitive_system')
        assert meta is not None

        message = Message(
            source='test',
            target='metacognitive_system',
            type='assess_capability',
            content={
                'capability_name': 'reasoning',
                'domain': 'cognitive'
            }
        )

        response = await meta.handle_message(message)
        assert 'capability_id' in response

    @pytest.mark.asyncio
    async def test_reasoning_service_observe(self, orchestrator):
        """Test reasoning service observation recording"""
        reasoning = orchestrator.get_service('reasoning_system')
        assert reasoning is not None

        message = Message(
            source='test',
            target='reasoning_system',
            type='observe',
            content={
                'event_a': 'rain',
                'event_b': 'wet ground',
                'time_delta': 5.0
            }
        )

        response = await reasoning.handle_message(message)
        assert 'observation_id' in response

    @pytest.mark.asyncio
    async def test_all_services_have_subscriptions(self, orchestrator):
        """Test all Phase 2-6 services define event subscriptions"""
        phase2_6_services = [
            'learning_system',
            'social_system',
            'creative_system',
            'web_system',
            'metacognitive_system',
            'reasoning_system'
        ]

        for service_name in phase2_6_services:
            service = orchestrator.get_service(service_name)
            assert service is not None
            assert hasattr(service, 'get_subscriptions')

            subscriptions = await service.get_subscriptions()
            assert isinstance(subscriptions, list)
            assert len(subscriptions) > 0  # Should subscribe to at least one topic

    @pytest.mark.asyncio
    async def test_event_bus_message_delivery(self, orchestrator):
        """Test event bus delivers messages to services"""
        # Send message through orchestrator
        await orchestrator.send_to_service(
            'learning_system',
            'get_learning_status',
            {}
        )

        # Give time for async processing
        await asyncio.sleep(0.1)

        # Check event bus processed the message
        metrics = orchestrator.event_bus.get_metrics()
        assert metrics['total_messages'] >= 1

    @pytest.mark.asyncio
    async def test_service_lifecycle_startup(self, orchestrator):
        """Test all services start up correctly"""
        # All services should be registered
        services = orchestrator.service_registry.get_all_services()
        assert len(services) >= 16

        # Orchestrator should be running
        assert orchestrator.running is True

        # State should be IDLE after initialization
        from src.core.state_manager import SystemState
        assert orchestrator.state_manager.current_state == SystemState.IDLE

    @pytest.mark.asyncio
    async def test_service_lifecycle_shutdown(self):
        """Test all services shut down cleanly"""
        with patch('src.core.orchestrator_refactored.os.environ.get', return_value='1'):
            orch = AGIOrchestrator()
            await orch.initialize()

            # Verify running
            assert orch.running is True

            # Shutdown
            await orch.shutdown()

            # Verify stopped
            assert orch.running is False

            # State should be SLEEPING
            from src.core.state_manager import SystemState
            assert orch.state_manager.current_state == SystemState.SLEEPING

    @pytest.mark.asyncio
    async def test_learning_service_full_workflow(self, orchestrator):
        """Test complete learning workflow: goal -> knowledge -> skill"""
        learning = orchestrator.get_service('learning_system')

        # 1. Create a goal
        goal_msg = Message(
            source='test',
            target='learning_system',
            type='create_goal',
            content={
                'description': 'Learn machine learning',
                'goal_type': 'LONG_TERM',
                'priority': 'HIGH',
                'success_criteria': ['Understand basics', 'Build model']
            }
        )
        goal_response = await learning.handle_message(goal_msg)
        goal_id = goal_response['goal_id']

        # 2. Add knowledge
        knowledge_msg = Message(
            source='test',
            target='learning_system',
            type='add_knowledge',
            content={
                'concept': 'Neural Networks',
                'type': 'technique',
                'description': 'ML technique using layered nodes'
            }
        )
        knowledge_response = await learning.handle_message(knowledge_msg)
        assert knowledge_response['name'] == 'Neural Networks'

        # 3. Practice skill
        skill_msg = Message(
            source='test',
            target='learning_system',
            type='practice_skill',
            content={
                'skill_name': 'ML Training',
                'domain': 'TECHNICAL',
                'performance': 0.7,
                'success': True,
                'duration': 120.0
            }
        )
        skill_response = await learning.handle_message(skill_msg)
        assert skill_response['new_proficiency'] > 0.0

        # 4. Update goal progress
        progress_msg = Message(
            source='test',
            target='learning_system',
            type='update_goal_progress',
            content={
                'goal_id': goal_id,
                'progress': 0.5,
                'milestone': 'Completed basics'
            }
        )
        progress_response = await learning.handle_message(progress_msg)
        assert progress_response['progress'] == 0.5

    @pytest.mark.asyncio
    async def test_cross_service_communication(self, orchestrator):
        """Test services can communicate through event bus"""
        # Learning service creates knowledge
        learning = orchestrator.get_service('learning_system')
        knowledge_msg = Message(
            source='test',
            target='learning_system',
            type='add_knowledge',
            content={
                'concept': 'Creativity',
                'type': 'concept',
                'description': 'Ability to create novel ideas'
            }
        )
        await learning.handle_message(knowledge_msg)

        # Creative service could use this knowledge
        creative = orchestrator.get_service('creative_system')
        insights_msg = Message(
            source='test',
            target='creative_system',
            type='get_creative_insights',
            content={}
        )
        insights = await creative.handle_message(insights_msg)
        assert 'total_works' in insights

    @pytest.mark.asyncio
    async def test_state_transitions_notify_services(self, orchestrator):
        """Test services receive state transition notifications"""
        from src.core.state_manager import SystemState

        # Transition to THINKING state
        await orchestrator.transition_to(SystemState.THINKING, "Testing state transition")

        # Give time for event propagation
        await asyncio.sleep(0.1)

        # Check event bus processed state change event
        metrics = orchestrator.event_bus.get_metrics()
        assert metrics['total_events'] >= 1

    @pytest.mark.asyncio
    async def test_system_status_includes_all_services(self, orchestrator):
        """Test system status includes all Phase 1-6 services"""
        status = orchestrator.get_system_status()

        assert 'services' in status
        assert 'service_statuses' in status
        assert 'state' in status
        assert 'running' in status

        # Should have all 16+ services
        assert len(status['services']) >= 16


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
