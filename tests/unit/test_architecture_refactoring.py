# tests/unit/test_architecture_refactoring.py
"""
Tests for the refactored architecture components.

This test suite ensures that the extracted ServiceRegistry, StateManager,
and EventBus components work correctly and that the refactored orchestrator
maintains compatibility.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.core.service_registry import ServiceRegistry, ServiceInterface
from src.core.state_manager import StateManager, SystemState, StateTransition
from src.core.event_bus import EventBus, Message, Event, Priority
from src.core.orchestrator_refactored import AGIOrchestrator


class MockService(ServiceInterface):
    """Mock service for testing"""
    def __init__(self, name: str):
        self.name = name
        self.initialized = False
        self.messages_received = []
        self.running = False
        
    async def initialize(self):
        self.initialized = True
        
    async def handle_message(self, message: Message):
        self.messages_received.append(message)
        
    async def run(self):
        self.running = True
        while self.running:
            await asyncio.sleep(0.1)
            
    async def close(self):
        self.running = False


class TestServiceRegistry:
    """Test ServiceRegistry functionality"""
    
    def test_register_service(self):
        """Test service registration"""
        registry = ServiceRegistry()
        service = MockService("test")
        
        registry.register("test", service, {"type": "mock"})
        
        assert registry.exists("test")
        assert registry.get("test") == service
        assert registry.get_metadata("test") == {"type": "mock"}
        
    def test_register_duplicate_raises_error(self):
        """Test that registering duplicate service raises error"""
        registry = ServiceRegistry()
        service = MockService("test")
        
        registry.register("test", service)
        
        with pytest.raises(ValueError):
            registry.register("test", service)
            
    def test_unregister_service(self):
        """Test service unregistration"""
        registry = ServiceRegistry()
        service = MockService("test")
        
        registry.register("test", service)
        registry.unregister("test")
        
        assert not registry.exists("test")
        assert registry.get("test") is None
        
    def test_list_services(self):
        """Test listing all services"""
        registry = ServiceRegistry()
        
        registry.register("service1", MockService("service1"))
        registry.register("service2", MockService("service2"))
        
        services = registry.list_services()
        assert len(services) == 2
        assert "service1" in services
        assert "service2" in services
        
    @pytest.mark.asyncio
    async def test_start_service(self):
        """Test starting a service"""
        registry = ServiceRegistry()
        service = MockService("test")
        
        registry.register("test", service)
        task = await registry.start_service("test", run_in_test_mode=True)
        
        assert task is not None
        assert service.running
        
        # Clean up
        await registry.stop_service("test")
        
    @pytest.mark.asyncio
    async def test_shutdown_all_services(self):
        """Test shutting down all services"""
        registry = ServiceRegistry()
        service1 = MockService("service1")
        service2 = MockService("service2")
        
        registry.register("service1", service1)
        registry.register("service2", service2)
        
        await registry.start_all_services(run_in_test_mode=True)
        
        assert service1.running
        assert service2.running
        
        await registry.shutdown_all_services()
        
        assert not service1.running
        assert not service2.running


class TestStateManager:
    """Test StateManager functionality"""
    
    def test_initial_state(self):
        """Test initial state is INITIALIZING"""
        manager = StateManager()
        assert manager.current_state == SystemState.INITIALIZING
        
    def test_get_valid_transitions(self):
        """Test getting valid transitions"""
        manager = StateManager()
        
        # From IDLE, many transitions are valid
        manager._current_state = SystemState.IDLE
        valid = manager.get_valid_transitions()
        
        assert SystemState.THINKING in valid
        assert SystemState.EXPLORING in valid
        assert SystemState.SLEEPING in valid
        assert SystemState.IDLE not in valid  # Can't transition to same state
        
    @pytest.mark.asyncio
    async def test_valid_transition(self):
        """Test a valid state transition"""
        manager = StateManager()
        manager._current_state = SystemState.IDLE
        
        success = await manager.transition_to(
            SystemState.THINKING,
            "Test transition"
        )
        
        assert success
        assert manager.current_state == SystemState.THINKING
        assert len(manager.state_history) == 1
        
        transition = manager.state_history[0]
        assert transition.from_state == SystemState.IDLE
        assert transition.to_state == SystemState.THINKING
        assert transition.reason == "Test transition"
        
    @pytest.mark.asyncio
    async def test_invalid_transition(self):
        """Test an invalid state transition"""
        manager = StateManager()
        manager._current_state = SystemState.SLEEPING
        
        # Can't go from SLEEPING to EXPLORING directly
        success = await manager.transition_to(SystemState.EXPLORING)
        
        assert not success
        assert manager.current_state == SystemState.SLEEPING
        assert len(manager.state_history) == 0
        
    @pytest.mark.asyncio
    async def test_transition_listeners(self):
        """Test state transition listeners"""
        manager = StateManager()
        manager._current_state = SystemState.IDLE
        
        transitions_received = []
        
        async def listener(transition: StateTransition):
            transitions_received.append(transition)
            
        manager.add_transition_listener(listener)
        
        await manager.transition_to(SystemState.THINKING, "Test")
        
        assert len(transitions_received) == 1
        assert transitions_received[0].to_state == SystemState.THINKING
        
    def test_get_state_statistics(self):
        """Test getting state statistics"""
        manager = StateManager()
        stats = manager.get_state_statistics()
        
        assert stats['current_state'] == SystemState.INITIALIZING.value
        assert stats['total_transitions'] == 0
        assert 'state_durations' in stats
        assert 'transition_counts' in stats


class TestEventBus:
    """Test EventBus functionality"""
    
    @pytest.mark.asyncio
    async def test_send_and_receive_message(self):
        """Test sending and receiving messages"""
        bus = EventBus()
        await bus.start()
        
        messages_received = []
        
        async def handler(message: Message):
            messages_received.append(message)
            
        bus.register_message_handler("test", handler)
        
        # Send message
        await bus.send("source", "test", "test_type", {"data": "test"})
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        assert len(messages_received) == 1
        assert messages_received[0].type == "test_type"
        assert messages_received[0].content == {"data": "test"}
        
        await bus.stop()
        
    @pytest.mark.asyncio
    async def test_broadcast_message(self):
        """Test broadcasting messages"""
        bus = EventBus()
        await bus.start()
        
        handler1_messages = []
        handler2_messages = []
        
        async def handler1(message: Message):
            if message.target == "handler1" or message.target == "broadcast":
                handler1_messages.append(message)
                
        async def handler2(message: Message):
            if message.target == "handler2" or message.target == "broadcast":
                handler2_messages.append(message)
                
        bus.register_message_handler("handler1", handler1)
        bus.register_message_handler("handler2", handler2)
        
        # Broadcast message
        await bus.send("source", "broadcast", "announcement", {"info": "test"})
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        assert len(handler1_messages) == 1
        assert len(handler2_messages) == 1
        
        await bus.stop()
        
    @pytest.mark.asyncio
    async def test_publish_subscribe_events(self):
        """Test publish-subscribe functionality"""
        bus = EventBus()
        
        events_received = []
        
        async def event_handler(event: Event):
            events_received.append(event)
            
        bus.subscribe("test_event", event_handler)
        
        # Publish event
        await bus.emit("test_event", "test_source", {"data": "test"})
        
        assert len(events_received) == 1
        assert events_received[0].type == "test_event"
        assert events_received[0].data == {"data": "test"}
        
    @pytest.mark.asyncio
    async def test_request_response(self):
        """Test request-response pattern"""
        bus = EventBus()
        await bus.start()
        
        # Set up responder
        async def responder(message: Message):
            if message.type == "request" and message.reply_to:
                response = Message(
                    source="responder",
                    target=message.reply_to,
                    type="response",
                    content={"result": "success"},
                    correlation_id=message.correlation_id
                )
                await bus.send_message(response)
                
        bus.register_message_handler("responder", responder)
        
        # Send request and wait for response
        response = await bus.request(
            "requester",
            "responder",
            "request",
            {"query": "test"},
            timeout=1.0
        )
        
        assert response is not None
        assert response.content == {"result": "success"}
        
        await bus.stop()


class TestRefactoredOrchestrator:
    """Test the refactored orchestrator"""
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test orchestrator initialization"""
        with patch('src.core.orchestrator_refactored.MemoryManager') as MockMemory, \
             patch('src.core.orchestrator_refactored.ConsciousnessStream') as MockConsciousness, \
             patch('src.core.orchestrator_refactored.EnhancedSafetyFramework') as MockSafety:
            
            # Set up mocks
            mock_memory = AsyncMock()
            mock_consciousness = MagicMock()
            mock_safety = MagicMock()
            
            MockMemory.return_value = mock_memory
            MockConsciousness.return_value = mock_consciousness
            MockSafety.return_value = mock_safety
            
            orchestrator = AGIOrchestrator()
            await orchestrator.initialize()
            
            # Check components are initialized
            assert orchestrator.running
            assert orchestrator.state == SystemState.IDLE
            
            # Check services are registered
            assert orchestrator.service_registry.exists("memory")
            assert orchestrator.service_registry.exists("consciousness")
            assert orchestrator.service_registry.exists("safety")
            
            # Clean up
            await orchestrator.shutdown()
            
    @pytest.mark.asyncio
    async def test_state_transitions(self):
        """Test state transitions through orchestrator"""
        with patch('src.core.orchestrator_refactored.MemoryManager'), \
             patch('src.core.orchestrator_refactored.ConsciousnessStream'), \
             patch('src.core.orchestrator_refactored.EnhancedSafetyFramework'):
            
            orchestrator = AGIOrchestrator()
            await orchestrator.initialize()
            
            # Test valid transition
            success = await orchestrator.transition_to(SystemState.THINKING, "Test")
            assert success
            assert orchestrator.state == SystemState.THINKING
            
            # Test invalid transition
            success = await orchestrator.transition_to(SystemState.SLEEPING, "Invalid")
            assert not success
            assert orchestrator.state == SystemState.THINKING
            
            await orchestrator.shutdown()
            
    @pytest.mark.asyncio
    async def test_message_routing(self):
        """Test message routing through orchestrator"""
        with patch('src.core.orchestrator_refactored.MemoryManager') as MockMemory, \
             patch('src.core.orchestrator_refactored.ConsciousnessStream'), \
             patch('src.core.orchestrator_refactored.EnhancedSafetyFramework'):
            
            # Set up mock with handle_message
            mock_memory = AsyncMock()
            mock_memory.handle_message = AsyncMock()
            MockMemory.return_value = mock_memory
            
            orchestrator = AGIOrchestrator()
            await orchestrator.initialize()
            
            # Send message to memory service
            await orchestrator.send_to_service("memory", "test_message", {"data": "test"})
            
            # Wait for message processing
            await asyncio.sleep(0.1)
            
            # Verify message was received
            assert mock_memory.handle_message.called
            
            await orchestrator.shutdown()
            
    def test_backwards_compatibility(self):
        """Test backwards compatibility properties"""
        orchestrator = AGIOrchestrator()
        
        # Test state property
        assert orchestrator.state == orchestrator.state_manager.current_state
        
        # Test services property
        assert orchestrator.services == orchestrator.service_registry.get_all_services()
        
        # Test message_queue property
        assert orchestrator.message_queue == orchestrator.event_bus._message_queue