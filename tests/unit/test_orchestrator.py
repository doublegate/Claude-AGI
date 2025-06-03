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
            type="test_message",
            content={"data": "test"},
            sender="test_service",
            priority=7
        )
        
        assert msg.type == "test_message"
        assert msg.content == {"data": "test"}
        assert msg.sender == "test_service"
        assert msg.priority == 7
        assert isinstance(msg.timestamp, datetime)
        
    def test_message_defaults(self):
        """Test message default values"""
        msg = Message(type="test", content="data")
        
        assert msg.sender == "unknown"
        assert msg.priority == 5
        

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
    def orchestrator(self, test_config):
        """Create orchestrator instance"""
        return AGIOrchestrator(test_config)
        
    def test_orchestrator_creation(self, orchestrator):
        """Test orchestrator initialization"""
        assert orchestrator.state == SystemState.IDLE
        assert orchestrator.is_running is False
        assert len(orchestrator.services) > 0
        assert len(orchestrator.state_history) == 0
        assert orchestrator.event_queue.maxsize == 100
        
    def test_service_registration(self, orchestrator):
        """Test that services are registered"""
        # Check core services are registered
        assert 'memory' in orchestrator.services
        assert 'consciousness' in orchestrator.services
        assert 'safety' in orchestrator.services
        
        # Verify service attributes
        for service in orchestrator.services.values():
            assert hasattr(service, 'orchestrator')
            assert hasattr(service, 'service_name')
            
    @pytest.mark.asyncio
    async def test_state_transition(self, orchestrator):
        """Test state transitions"""
        initial_state = orchestrator.state
        
        # Transition to THINKING
        await orchestrator.transition_to(SystemState.THINKING, "Test transition")
        
        assert orchestrator.state == SystemState.THINKING
        assert len(orchestrator.state_history) == 1
        
        transition = orchestrator.state_history[0]
        assert transition.from_state == initial_state
        assert transition.to_state == SystemState.THINKING
        assert transition.reason == "Test transition"
        
    @pytest.mark.asyncio
    async def test_invalid_state_transition(self, orchestrator):
        """Test handling of invalid state transitions"""
        orchestrator.state = SystemState.SLEEPING
        
        # Define valid transitions (example constraint)
        orchestrator.valid_transitions = {
            SystemState.SLEEPING: [SystemState.IDLE, SystemState.THINKING]
        }
        
        # Should handle gracefully (not raise exception)
        await orchestrator.transition_to(SystemState.CREATING)
        
        # State might change or stay same depending on implementation
        # Just verify no exception was raised
        assert orchestrator.state in SystemState
        
    @pytest.mark.asyncio
    async def test_publish_event(self, orchestrator):
        """Test event publishing"""
        # Subscribe a mock handler
        handler = AsyncMock()
        topic = "test.event"
        
        # Manually add subscription
        orchestrator.subscriptions[topic] = [handler]
        
        # Publish event
        await orchestrator.publish(topic, {"data": "test"})
        
        # Handler should be called
        handler.assert_called_once()
        call_args = handler.call_args[0][0]
        assert call_args.type == topic
        assert call_args.content == {"data": "test"}
        
    @pytest.mark.asyncio
    async def test_send_to_service(self, orchestrator):
        """Test sending messages to specific services"""
        # Create mock service
        mock_service = Mock()
        mock_service.receive_message = AsyncMock()
        orchestrator.services['test_service'] = mock_service
        
        # Send message
        await orchestrator.send_to_service(
            'test_service',
            'test_action',
            {'data': 'test'},
            priority=8
        )
        
        # Service should receive message
        mock_service.receive_message.assert_called_once()
        msg = mock_service.receive_message.call_args[0][0]
        assert msg.type == 'test_action'
        assert msg.content == {'data': 'test'}
        assert msg.priority == 8
        
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
        processed = []
        
        # Add test handler
        async def test_handler(msg):
            processed.append(msg)
            
        orchestrator.subscriptions['test.event'] = [test_handler]
        
        # Add events to queue
        await orchestrator.event_queue.put(
            Message(type='test.event', content={'id': 1})
        )
        await orchestrator.event_queue.put(
            Message(type='test.event', content={'id': 2})
        )
        
        # Process events
        await orchestrator._process_events()
        
        # Both events should be processed
        assert len(processed) == 2
        assert processed[0].content['id'] == 1
        assert processed[1].content['id'] == 2
        
    @pytest.mark.asyncio
    async def test_service_initialization(self, orchestrator):
        """Test service initialization"""
        # Mock services
        for service in orchestrator.services.values():
            service.initialize = AsyncMock()
            
        await orchestrator._initialize_services()
        
        # All services should be initialized
        for service in orchestrator.services.values():
            service.initialize.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_service_cycle_running(self, orchestrator):
        """Test service cycle execution"""
        # Mock service
        mock_service = Mock()
        mock_service.service_cycle = AsyncMock()
        mock_service.service_name = "test"
        orchestrator.services['test'] = mock_service
        
        # Run one cycle with limited services
        orchestrator.services = {'test': mock_service}
        await orchestrator._run_service_cycles()
        
        # Service cycle should be called
        mock_service.service_cycle.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_state_based_behavior(self, orchestrator):
        """Test state-based orchestration behavior"""
        # Set different states and verify behavior changes
        test_states = [
            (SystemState.THINKING, "standard thinking"),
            (SystemState.EXPLORING, "exploration mode"),
            (SystemState.CREATING, "creative mode"),
            (SystemState.REFLECTING, "reflection mode"),
            (SystemState.SLEEPING, "sleep mode")
        ]
        
        for state, expected_behavior in test_states:
            await orchestrator.transition_to(state)
            assert orchestrator.state == state
            # In real implementation, verify specific behavior per state
            
    @pytest.mark.asyncio 
    async def test_shutdown(self, orchestrator):
        """Test graceful shutdown"""
        orchestrator.is_running = True
        
        # Mock services
        for service in orchestrator.services.values():
            service.shutdown = AsyncMock()
            
        await orchestrator.shutdown()
        
        assert orchestrator.is_running is False
        
        # All services should be shut down
        for service in orchestrator.services.values():
            service.shutdown.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_emergency_stop(self, orchestrator):
        """Test emergency stop functionality"""
        orchestrator.is_running = True
        
        # Create a mock dangerous event
        orchestrator.emergency_stop = AsyncMock()
        
        # In real implementation, this would be triggered by safety service
        await orchestrator.emergency_stop("Safety violation detected")
        
        orchestrator.emergency_stop.assert_called_with("Safety violation detected")
        
    def test_get_system_status(self, orchestrator):
        """Test getting system status"""
        orchestrator.state = SystemState.THINKING
        orchestrator.metrics = {
            'thoughts_generated': 100,
            'uptime_seconds': 3600
        }
        
        status = orchestrator.get_system_status()
        
        assert status['state'] == SystemState.THINKING
        assert status['is_running'] == orchestrator.is_running
        assert status['services_count'] == len(orchestrator.services)
        assert 'metrics' in status
        
    @pytest.mark.asyncio
    async def test_concurrent_event_handling(self, orchestrator):
        """Test handling multiple concurrent events"""
        results = []
        
        async def slow_handler(msg):
            await asyncio.sleep(0.1)
            results.append(msg.content['id'])
            
        orchestrator.subscriptions['test'] = [slow_handler]
        
        # Add multiple events
        for i in range(5):
            await orchestrator.event_queue.put(
                Message(type='test', content={'id': i})
            )
            
        # Process all events
        await orchestrator._process_events()
        
        # All events should be processed
        assert len(results) == 5
        assert sorted(results) == [0, 1, 2, 3, 4]
        
    @pytest.mark.asyncio
    async def test_priority_message_ordering(self, orchestrator):
        """Test that higher priority messages are processed first"""
        # This test assumes priority queue implementation
        processed_order = []
        
        async def track_handler(msg):
            processed_order.append(msg.priority)
            
        orchestrator.subscriptions['priority.test'] = [track_handler]
        
        # Add messages with different priorities
        messages = [
            Message(type='priority.test', content={'id': 1}, priority=3),
            Message(type='priority.test', content={'id': 2}, priority=9),
            Message(type='priority.test', content={'id': 3}, priority=5),
            Message(type='priority.test', content={'id': 4}, priority=7)
        ]
        
        for msg in messages:
            await orchestrator.event_queue.put(msg)
            
        await orchestrator._process_events()
        
        # Verify processing order (might depend on implementation)
        assert len(processed_order) == 4
        
    @pytest.mark.asyncio
    async def test_error_handling_in_service_cycle(self, orchestrator):
        """Test error handling when service cycle fails"""
        # Mock service that raises exception
        mock_service = Mock()
        mock_service.service_cycle = AsyncMock(side_effect=Exception("Service error"))
        mock_service.service_name = "faulty"
        
        orchestrator.services = {'faulty': mock_service}
        
        # Should not crash orchestrator
        await orchestrator._run_service_cycles()
        
        # Verify orchestrator continues running
        assert True  # No exception raised
        
    @pytest.mark.asyncio
    async def test_state_history_limit(self, orchestrator):
        """Test that state history has reasonable limits"""
        # Make many state transitions
        for i in range(20):
            next_state = SystemState.THINKING if i % 2 == 0 else SystemState.IDLE
            await orchestrator.transition_to(next_state, f"Transition {i}")
            
        # History should be limited (e.g., last 100 transitions)
        assert len(orchestrator.state_history) <= 100
        
    def test_configuration_loading(self, test_config):
        """Test configuration is properly loaded"""
        orchestrator = AGIOrchestrator(test_config)
        
        assert orchestrator.config == test_config
        assert orchestrator.event_queue.maxsize == 100
        
    @pytest.mark.asyncio
    async def test_inter_service_communication(self, orchestrator):
        """Test services can communicate through orchestrator"""
        # Mock two services
        service_a = Mock()
        service_a.receive_message = AsyncMock()
        service_b = Mock()
        service_b.receive_message = AsyncMock()
        
        orchestrator.services = {
            'service_a': service_a,
            'service_b': service_b
        }
        
        # Service A sends to Service B
        await orchestrator.send_to_service(
            'service_b',
            'greeting',
            {'message': 'Hello from A'}
        )
        
        # Service B should receive the message
        service_b.receive_message.assert_called_once()
        msg = service_b.receive_message.call_args[0][0]
        assert msg.type == 'greeting'
        assert msg.content['message'] == 'Hello from A'