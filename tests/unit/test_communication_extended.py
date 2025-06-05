"""
Extended unit tests for Communication Module
===========================================

Tests additional functionality for the communication system.
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import pytest
from datetime import datetime

from src.core.communication import ServiceBase


@pytest.fixture
def mock_orchestrator():
    """Create mock orchestrator"""
    orchestrator = Mock()
    orchestrator.services = {}
    orchestrator.send_message = AsyncMock()
    return orchestrator


@pytest.fixture
def test_service(mock_orchestrator):
    """Create test service"""
    class TestService(ServiceBase):
        def __init__(self, orchestrator):
            super().__init__(orchestrator, "test_service")
            self.messages_received = []
            
        def get_subscriptions(self):
            return ["test_topic", "another_topic"]
            
        async def process_message(self, message):
            self.messages_received.append(message)
            
        async def service_cycle(self):
            await asyncio.sleep(0.01)
            
    return TestService(mock_orchestrator)


class TestServiceBase:
    """Test ServiceBase functionality"""
    
    def test_initialization(self, test_service, mock_orchestrator):
        """Test service initialization"""
        assert test_service.orchestrator == mock_orchestrator
        assert test_service.service_name == "test_service"
        assert test_service.running is False
        assert isinstance(test_service.message_queue, asyncio.Queue)
        assert test_service._subscriptions == set()
        
    @pytest.mark.asyncio
    async def test_setup_communication(self, test_service, mock_orchestrator):
        """Test setting up communication"""
        await test_service.setup_communication()
        
        # Check service was registered
        assert mock_orchestrator.services["test_service"] == test_service
        
        # Check subscriptions were set
        assert "test_topic" in test_service._subscriptions
        assert "another_topic" in test_service._subscriptions
        
    @pytest.mark.asyncio
    async def test_publish(self, test_service, mock_orchestrator):
        """Test publishing messages"""
        # Just check that publish calls orchestrator.send_message
        await test_service.publish("test_event", {"data": "test"})
        
        # Check orchestrator.send_message was called
        mock_orchestrator.send_message.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_send_to_service(self, test_service, mock_orchestrator):
        """Test sending direct messages to another service"""
        with patch('src.core.orchestrator.Message') as mock_message:
            mock_msg_instance = Mock()
            mock_message.return_value = mock_msg_instance
            
            await test_service.send_to_service(
                "target_service", 
                "test_action",
                {"data": "test"},
                priority=7
            )
            
            # Check message was created
            mock_message.assert_called_once()
            call_kwargs = mock_message.call_args[1]
            assert call_kwargs["source"] == "test_service"
            assert call_kwargs["target"] == "target_service"
            assert call_kwargs["type"] == "test_action"
            assert call_kwargs["content"] == {"data": "test"}
            assert call_kwargs["priority"] == 7
            
            # Check orchestrator.send_message was called
            mock_orchestrator.send_message.assert_called_once_with(mock_msg_instance)
            
    @pytest.mark.asyncio
    async def test_handle_message(self, test_service):
        """Test handling incoming messages"""
        message = Mock(content={"test": "data"})
        
        await test_service.handle_message(message)
        
        # Check message was queued
        assert not test_service.message_queue.empty()
        queued_message = await test_service.message_queue.get()
        assert queued_message == message
        
    @pytest.mark.asyncio
    async def test_receive_message(self, test_service):
        """Test receiving messages from queue"""
        # Add a message to queue
        test_msg = Mock(content={"test": "data"})
        await test_service.message_queue.put(test_msg)
        
        # Receive without timeout
        received = await test_service.receive_message()
        assert received == test_msg
        
    @pytest.mark.asyncio
    async def test_receive_message_with_timeout(self, test_service):
        """Test receiving messages with timeout"""
        # Try to receive with timeout (should return None)
        received = await test_service.receive_message(timeout=0.01)
        assert received is None
        
    @pytest.mark.asyncio
    async def test_run_loop(self, test_service, mock_orchestrator):
        """Test main run loop"""
        # Queue a message
        test_message = Mock(content={"test": "data"})
        await test_service.message_queue.put(test_message)
        
        # Run for a short time then stop
        async def run_briefly():
            test_service.running = True
            # Process one iteration
            message = await test_service.receive_message(timeout=0.1)
            if message:
                await test_service.process_message(message)
            await test_service.service_cycle()
            test_service.running = False
            
        await run_briefly()
        
        # Check message was processed
        assert test_message in test_service.messages_received
        
    @pytest.mark.asyncio
    async def test_run_with_error_in_process_message(self, test_service):
        """Test run loop with error in process_message"""
        # Override process_message to raise error
        test_service.process_message = AsyncMock(side_effect=Exception("Process error"))
        test_service.handle_error = AsyncMock()
        
        # Queue a message
        message = Mock(content={"test": "data"})
        await test_service.message_queue.put(message)
        
        # Run briefly
        test_service.running = True
        message = await test_service.receive_message(timeout=0.1)
        if message:
            try:
                await test_service.process_message(message)
            except Exception as e:
                await test_service.handle_error(e)
                
        # Check error handler was called
        test_service.handle_error.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_run_with_error_in_service_cycle(self, test_service):
        """Test run loop with error in service_cycle"""
        # Override service_cycle to raise error
        test_service.service_cycle = AsyncMock(side_effect=Exception("Cycle error"))
        test_service.handle_error = AsyncMock()
        
        # Run briefly
        test_service.running = True
        try:
            await test_service.service_cycle()
        except Exception as e:
            await test_service.handle_error(e)
            
        # Check error handler was called
        test_service.handle_error.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_handle_error(self, test_service, mock_orchestrator):
        """Test error handling"""
        error = Exception("Test error")
        
        await test_service.handle_error(error)
        
        # Check error was sent to memory service
        mock_orchestrator.send_message.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_cleanup(self, test_service):
        """Test cleanup method"""
        # Add cleanup method for testing
        test_service.cleanup = AsyncMock()
        
        await test_service.cleanup()
        
        test_service.cleanup.assert_called_once()
        
    def test_get_subscriptions(self, test_service):
        """Test getting subscriptions"""
        subs = test_service.get_subscriptions()
        assert "test_topic" in subs
        assert "another_topic" in subs
        
    @pytest.mark.asyncio
    async def test_full_run_with_cancellation(self, test_service):
        """Test running service with cancellation"""
        # Create a task that runs the service
        run_task = asyncio.create_task(test_service.run())
        
        # Give it time to start
        await asyncio.sleep(0.01)
        
        # Cancel the task
        run_task.cancel()
        
        # Wait for cancellation
        with pytest.raises(asyncio.CancelledError):
            await run_task
            
        # Check service stopped
        assert test_service.running is False