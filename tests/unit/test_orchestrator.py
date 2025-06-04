# tests/unit/test_orchestrator.py

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import yaml

from src.core.orchestrator import AGIOrchestrator, SystemState, StateTransition, Message


class TestSystemState:
    """Test SystemState enum"""
    
    def test_system_states_exist(self):
        """Test that all required system states exist"""
        assert SystemState.IDLE
        assert SystemState.THINKING
        assert SystemState.EXPLORING
        assert SystemState.CREATING
        assert SystemState.REFLECTING
        assert SystemState.SLEEPING
        

class TestStateTransition:
    """Test StateTransition dataclass"""
    
    def test_state_transition_creation(self):
        """Test creating state transitions"""
        transition = StateTransition(
            from_state=SystemState.IDLE,
            to_state=SystemState.THINKING,
            timestamp=datetime.now(),
            reason="User input received"
        )
        
        assert transition.from_state == SystemState.IDLE
        assert transition.to_state == SystemState.THINKING
        assert transition.reason == "User input received"
        assert isinstance(transition.timestamp, datetime)
        

class TestMessage:
    """Test Message dataclass"""
    
    def test_message_creation(self):
        """Test creating messages"""
        msg = Message(
            source="test_service",
            target="orchestrator",
            type="test_message",
            content={"data": "test"},
            priority=7
        )
        
        assert msg.type == "test_message"
        assert msg.content == {"data": "test"}
        assert msg.source == "test_service"
        assert msg.target == "orchestrator"
        assert msg.priority == 7
        assert isinstance(msg.timestamp, float)
        
    def test_message_defaults(self):
        """Test message default values"""
        msg = Message(
            source="test",
            target="test",
            type="test",
            content="data"
        )
        
        assert msg.priority == 5
        assert msg.timestamp is not None
        

class TestAGIOrchestrator:
    """Test AGI Orchestrator"""
    
    @pytest.fixture
    def test_config(self):
        """Create test configuration"""
        return {
            'services': {
                'memory': {'enabled': True},
                'consciousness': {'enabled': True},
                'safety': {'enabled': True}
            },
            'orchestrator': {
                'state_transition_delay': 0.1,
                'max_queue_size': 100
            }
        }
        
    @pytest.fixture
    async def orchestrator(self, test_config):
        """Create orchestrator instance"""
        orch = AGIOrchestrator(test_config)
        yield orch
        # Cleanup - cancel any running tasks
        for task in orch.tasks:
            task.cancel()
        if orch.tasks:
            await asyncio.gather(*orch.tasks, return_exceptions=True)
        
    def test_orchestrator_creation(self, orchestrator):
        """Test orchestrator initialization"""
        assert orchestrator.state == SystemState.INITIALIZING
        assert orchestrator.running is False
        assert len(orchestrator.services) == 0  # Not initialized yet
        assert len(orchestrator.state_history) == 0
        assert hasattr(orchestrator, 'message_queue')
        
    @pytest.mark.asyncio
    async def test_service_registration(self, orchestrator):
        """Test that services are registered after initialization"""
        # Services should be empty before initialization
        assert len(orchestrator.services) == 0
        
        # Initialize the orchestrator
        await orchestrator.initialize()
        
        # Check core services are registered
        assert 'memory' in orchestrator.services
        assert 'consciousness' in orchestrator.services
        assert 'safety' in orchestrator.services
        
        # State should be IDLE after initialization
        assert orchestrator.state == SystemState.IDLE
            
    @pytest.mark.asyncio
    async def test_state_transition(self, orchestrator):
        """Test state transitions"""
        # Initialize first to get to IDLE state
        await orchestrator.initialize()
        initial_state = orchestrator.state
        
        # Transition to THINKING
        await orchestrator.transition_to(SystemState.THINKING)
        
        assert orchestrator.state == SystemState.THINKING
        assert len(orchestrator.state_history) == 1
        
        transition = orchestrator.state_history[0]
        assert transition.from_state == initial_state
        assert transition.to_state == SystemState.THINKING
        assert "User requested transition" in transition.reason
        
    @pytest.mark.asyncio
    async def test_invalid_state_transition(self, orchestrator):
        """Test handling of invalid state transitions"""
        await orchestrator.initialize()
        orchestrator.state = SystemState.SLEEPING
        
        # Try invalid transition from SLEEPING to CREATING
        # (Only IDLE is valid from SLEEPING)
        initial_state = orchestrator.state
        await orchestrator.transition_to(SystemState.CREATING)
        
        # State should remain unchanged for invalid transition
        assert orchestrator.state == initial_state
        
    @pytest.mark.asyncio
    async def test_publish_event(self, orchestrator):
        """Test event publishing"""
        await orchestrator.initialize()
        
        # Subscribe a service to an event
        topic = "test.event"
        orchestrator.subscribe("memory", topic)
        
        # Mock the message queue to track published messages
        published_messages = []
        original_send = orchestrator.send_message
        
        async def mock_send(msg):
            published_messages.append(msg)
            await original_send(msg)
            
        orchestrator.send_message = mock_send
        
        # Publish event
        await orchestrator.publish(topic, {"data": "test"})
        
        # Check that message was sent
        assert len(published_messages) == 1
        msg = published_messages[0]
        assert msg.target == "memory"
        assert msg.type == "event"
        assert msg.content['event_type'] == topic
        assert msg.content['data'] == {"data": "test"}
        
    @pytest.mark.asyncio
    async def test_send_to_service(self, orchestrator):
        """Test sending messages to specific services"""
        await orchestrator.initialize()
        
        # Track messages sent
        sent_messages = []
        original_send = orchestrator.send_message
        
        async def mock_send(msg):
            sent_messages.append(msg)
            
        orchestrator.send_message = mock_send
        
        # Send message
        await orchestrator.send_to_service(
            'memory',
            'test_action',
            {'data': 'test'}
        )
        
        # Check message was sent correctly
        assert len(sent_messages) == 1
        msg = sent_messages[0]
        assert msg.type == 'test_action'
        assert msg.content == {'data': 'test'}
        assert msg.target == 'memory'
        assert msg.source == 'orchestrator'
        
    @pytest.mark.asyncio
    async def test_send_to_nonexistent_service(self, orchestrator):
        """Test sending to non-existent service"""
        # Should not raise exception
        await orchestrator.send_to_service(
            'nonexistent',
            'action',
            {'data': 'test'}
        )
        
        # Verify no exception was raised
        assert True
        
    @pytest.mark.asyncio
    async def test_process_events_queue(self, orchestrator):
        """Test event queue processing"""
        await orchestrator.initialize()
        
        # Add messages to queue
        msg1 = Message(
            source='test', 
            target='memory',
            type='test.event', 
            content={'id': 1}
        )
        msg2 = Message(
            source='test',
            target='memory', 
            type='test.event', 
            content={'id': 2}
        )
        
        await orchestrator.send_message(msg1)
        await orchestrator.send_message(msg2)
        
        # Process events
        await orchestrator.process_events_queue()
        
        # Queue should be empty after processing
        assert orchestrator.message_queue.empty()
        
    @pytest.mark.asyncio
    async def test_service_initialization(self, orchestrator):
        """Test service initialization"""
        # Services should be empty before init
        assert len(orchestrator.services) == 0
        
        await orchestrator._initialize_services()
        
        # Core services should be initialized
        assert 'memory' in orchestrator.services
        assert 'consciousness' in orchestrator.services
        assert 'safety' in orchestrator.services
            
    @pytest.mark.asyncio
    async def test_service_cycle_running(self, orchestrator):
        """Test service cycle execution"""
        await orchestrator.initialize()
        
        # Check that services have been started as tasks
        assert len(orchestrator.tasks) > 0
        
        # Cancel tasks for cleanup
        for task in orchestrator.tasks:
            task.cancel()
        
    @pytest.mark.asyncio
    async def test_state_based_behavior(self, orchestrator):
        """Test state-based orchestration behavior"""
        await orchestrator.initialize()
        
        # Test valid transitions from IDLE
        test_states = [
            SystemState.THINKING,
            SystemState.EXPLORING,
            SystemState.CREATING,
            SystemState.REFLECTING
        ]
        
        for state in test_states:
            orchestrator.state = SystemState.IDLE  # Reset to IDLE
            await orchestrator.transition_to(state)
            assert orchestrator.state == state
            
    @pytest.mark.asyncio 
    async def test_shutdown(self, orchestrator):
        """Test graceful shutdown"""
        await orchestrator.initialize()
        orchestrator.running = True
        
        await orchestrator.shutdown()
        
        assert orchestrator.running is False
        assert orchestrator.state == SystemState.SLEEPING
            
    @pytest.mark.asyncio
    async def test_emergency_stop(self, orchestrator):
        """Test emergency stop functionality"""
        await orchestrator.initialize()
        orchestrator.running = True
        
        # Call emergency stop
        await orchestrator.emergency_stop("Safety violation detected")
        
        # Should transition to SLEEPING and stop running
        assert orchestrator.state == SystemState.SLEEPING
        assert orchestrator.running is False
        
    def test_get_system_status(self, orchestrator):
        """Test getting system status"""
        orchestrator.state = SystemState.THINKING
        orchestrator.running = True
        
        status = orchestrator.get_system_status()
        
        assert status['state'] == 'thinking'
        assert status['running'] == True
        assert 'services' in status
        assert 'queue_size' in status
        
    @pytest.mark.asyncio
    async def test_concurrent_event_handling(self, orchestrator):
        """Test handling multiple concurrent events"""
        await orchestrator.initialize()
        
        # Add multiple messages
        for i in range(5):
            msg = Message(
                source='test',
                target='memory',
                type='test',
                content={'id': i}
            )
            await orchestrator.send_message(msg)
            
        # Process all events
        await orchestrator.process_events_queue()
        
        # Queue should be empty
        assert orchestrator.message_queue.empty()
        
    @pytest.mark.asyncio
    async def test_priority_message_ordering(self, orchestrator):
        """Test that higher priority messages are processed first"""
        await orchestrator.initialize()
        
        # Add messages with different priorities
        messages = [
            Message(source='test', target='memory', type='test', content={'id': 1}, priority=9),
            Message(source='test', target='memory', type='test', content={'id': 2}, priority=1),
            Message(source='test', target='memory', type='test', content={'id': 3}, priority=5)
        ]
        
        for msg in messages:
            await orchestrator.send_message(msg)
            
        # The priority queue should order them correctly
        # Lower priority number = higher priority
        first_msg = await orchestrator.message_queue.get()
        assert first_msg.priority == 1  # Highest priority
        
    @pytest.mark.asyncio
    async def test_error_handling_in_service_cycle(self, orchestrator):
        """Test error handling when service fails"""
        await orchestrator.initialize()
        
        # Send a message to trigger error handling
        error_msg = Message(
            source='test',
            target='nonexistent',  # Invalid target
            type='test',
            content={'data': 'test'}
        )
        
        # Should handle gracefully without crashing
        await orchestrator.route_message(error_msg)
        
        # Orchestrator should still be functional
        assert orchestrator.state in SystemState
        
    @pytest.mark.asyncio
    async def test_state_history_limit(self, orchestrator):
        """Test that state history is recorded"""
        await orchestrator.initialize()
        
        # Make several state transitions
        await orchestrator.transition_to(SystemState.THINKING)
        await orchestrator.transition_to(SystemState.IDLE)
        await orchestrator.transition_to(SystemState.EXPLORING)
        
        # History should be recorded
        assert len(orchestrator.state_history) >= 3
        
    def test_configuration_loading(self, test_config):
        """Test configuration is properly loaded"""
        orchestrator = AGIOrchestrator(test_config)
        
        assert orchestrator.config == test_config
        assert hasattr(orchestrator, 'message_queue')
        
    @pytest.mark.asyncio
    async def test_inter_service_communication(self, orchestrator):
        """Test services can communicate through orchestrator"""
        await orchestrator.initialize()
        
        # Track messages sent
        messages = []
        original_route = orchestrator.route_message
        
        async def track_route(msg):
            messages.append(msg)
            await original_route(msg)
            
        orchestrator.route_message = track_route
        
        # Send message from one service to another
        await orchestrator.send_to_service(
            'memory',
            'greeting',
            {'message': 'Hello'}
        )
        
        # Process the message
        msg = await orchestrator.message_queue.get()
        await orchestrator.route_message(msg)
        
        # Message should have been routed
        assert len(messages) == 1
        assert messages[0].type == 'greeting'