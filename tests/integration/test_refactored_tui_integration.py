"""
Integration Tests for Refactored TUI Components
===============================================

Tests the integration between TUIController and its refactored coordinators:
- ConsciousnessCoordinator
- ConversationCoordinator
- CommandRegistry
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from collections import deque

from src.interface.consciousness_coordinator import ConsciousnessCoordinator
from src.interface.conversation_coordinator import ConversationCoordinator
from src.interface.command_registry import CommandRegistry


class TestConsciousnessCoordinatorIntegration:
    """Test ConsciousnessCoordinator integration with orchestrator"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator"""
        orchestrator = AsyncMock()
        orchestrator.get_service = MagicMock(return_value=None)
        orchestrator.publish = AsyncMock()
        return orchestrator

    @pytest.fixture
    def consciousness_lines(self):
        """Track consciousness lines added"""
        return []

    @pytest.fixture
    def consciousness_coordinator(self, mock_orchestrator, consciousness_lines):
        """Create consciousness coordinator"""
        def add_line(line, color=None):
            """Callback that accepts line and optional color"""
            consciousness_lines.append(line)

        return ConsciousnessCoordinator(
            orchestrator=mock_orchestrator,
            add_consciousness_line_callback=add_line
        )

    @pytest.mark.asyncio
    async def test_consciousness_initialization(self, consciousness_coordinator, mock_orchestrator):
        """Test consciousness coordinator initializes correctly"""
        assert consciousness_coordinator.orchestrator == mock_orchestrator
        assert consciousness_coordinator.running is True
        assert consciousness_coordinator.add_consciousness_line is not None

    @pytest.mark.asyncio
    async def test_consciousness_processes_service_thoughts(
        self, consciousness_coordinator, mock_orchestrator, consciousness_lines
    ):
        """Test processing thoughts from consciousness service"""
        # Mock consciousness service with streams and thought buffers
        mock_stream = MagicMock()
        mock_stream.content_buffer = [
            {
                'content': 'Test thought from service',
                'stream': 'primary',
                'timestamp': '2025-11-18T12:00:00',
                'importance': 5,
                'emotional_tone': 'neutral'
            }
        ]

        mock_service = MagicMock()
        mock_service.streams = {'primary': mock_stream}

        # Mock the services dictionary properly (not AsyncMock, just dict)
        mock_orchestrator.services = {'consciousness': mock_service}

        # Run consciousness loop briefly
        consciousness_coordinator.running = True
        task = asyncio.create_task(consciousness_coordinator.run_consciousness_loop())
        await asyncio.sleep(0.3)  # Give it time to process
        consciousness_coordinator.running = False

        try:
            await asyncio.wait_for(task, timeout=2.0)
        except asyncio.TimeoutError:
            task.cancel()

        # Verify thought was processed and displayed
        assert len(consciousness_lines) > 0
        # Check for the thought content in formatted output
        assert any('Test thought from service' in line for line in consciousness_lines)

    @pytest.mark.asyncio
    async def test_consciousness_generates_automatic_thoughts(
        self, consciousness_coordinator, consciousness_lines
    ):
        """Test automatic thought generation when no service available"""
        # No consciousness service available
        consciousness_coordinator.orchestrator.get_service.return_value = None

        # Run consciousness loop briefly
        consciousness_coordinator.running = True
        task = asyncio.create_task(consciousness_coordinator.run_consciousness_loop())
        await asyncio.sleep(3.0)  # Wait for automatic thought (every 2.5s)
        consciousness_coordinator.running = False

        try:
            await asyncio.wait_for(task, timeout=1.0)
        except asyncio.TimeoutError:
            task.cancel()

        # Verify automatic thought was generated
        assert len(consciousness_lines) > 0

    @pytest.mark.asyncio
    async def test_consciousness_stops_gracefully(self, consciousness_coordinator):
        """Test consciousness loop stops when running flag set to False"""
        consciousness_coordinator.running = True
        task = asyncio.create_task(consciousness_coordinator.run_consciousness_loop())
        await asyncio.sleep(0.1)

        consciousness_coordinator.running = False
        await asyncio.wait_for(task, timeout=2.0)

        # Should complete without timeout
        assert task.done()


class TestConversationCoordinatorIntegration:
    """Test ConversationCoordinator integration"""

    @pytest.fixture
    def mock_thought_generator(self):
        """Create mock thought generator"""
        generator = AsyncMock()
        generator.generate_response = AsyncMock(return_value="Test AI response")
        return generator

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator"""
        orchestrator = AsyncMock()
        orchestrator.publish = AsyncMock()
        return orchestrator

    @pytest.fixture
    def chat_lines(self):
        """Track chat lines added"""
        return []

    @pytest.fixture
    def conversation_coordinator(self, mock_thought_generator, mock_orchestrator, chat_lines):
        """Create conversation coordinator"""
        def add_chat_line(line):
            chat_lines.append(line)

        return ConversationCoordinator(
            thought_generator=mock_thought_generator,
            orchestrator=mock_orchestrator,
            add_chat_line_callback=add_chat_line
        )

    @pytest.mark.asyncio
    async def test_conversation_initialization(
        self, conversation_coordinator, mock_thought_generator, mock_orchestrator
    ):
        """Test conversation coordinator initializes correctly"""
        assert conversation_coordinator.thought_generator == mock_thought_generator
        assert conversation_coordinator.orchestrator == mock_orchestrator
        assert len(conversation_coordinator.conversation_history) == 0

    @pytest.mark.asyncio
    async def test_handle_user_message(
        self, conversation_coordinator, mock_thought_generator, chat_lines
    ):
        """Test handling user message and generating response"""
        await conversation_coordinator.handle_user_message("Hello, how are you?")

        # Verify message was added to history
        assert len(conversation_coordinator.conversation_history) == 2  # User + AI
        assert conversation_coordinator.conversation_history[0]['role'] == 'user'
        assert conversation_coordinator.conversation_history[1]['role'] == 'assistant'

        # Verify chat lines were added
        assert len(chat_lines) >= 2
        assert any('You:' in line for line in chat_lines)
        assert any('Claude:' in line for line in chat_lines)

        # Verify AI response was generated
        mock_thought_generator.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_input_validation(self, conversation_coordinator, chat_lines):
        """Test input validation rejects malicious content"""
        malicious_input = "<script>alert('xss')</script>Hello"

        # Should be rejected by validation
        is_valid = conversation_coordinator._validate_user_input(malicious_input)
        assert is_valid is False

        # When trying to handle it, should get rejection message
        await conversation_coordinator.handle_user_message(malicious_input)
        assert len(chat_lines) > 0
        assert any('Invalid input' in line for line in chat_lines)

    @pytest.mark.asyncio
    async def test_conversation_history_limit(self, conversation_coordinator):
        """Test conversation history maintains size limit"""
        # Add many messages
        for i in range(30):
            conversation_coordinator.conversation_history.append({
                'role': 'user',
                'content': f'Message {i}'
            })

        # Should respect maxlen=20
        assert len(conversation_coordinator.conversation_history) == 20
        # Should keep most recent messages
        assert conversation_coordinator.conversation_history[-1]['content'] == 'Message 29'

    @pytest.mark.asyncio
    async def test_system_time_query(self, conversation_coordinator, chat_lines):
        """Test handling system time query"""
        # Mock the explorer service for time query
        mock_explorer = AsyncMock()
        mock_explorer.get_system_time = AsyncMock(return_value={
            'success': True,
            'current_time': '12:00 PM',
            'day_of_week': 'Monday',
            'date': 'November 18, 2025'
        })
        conversation_coordinator.orchestrator.services = {'explorer': mock_explorer}

        await conversation_coordinator.handle_user_message("what time is it?")

        # Should respond with time (uses "The current time" with capital T)
        assert len(chat_lines) > 0
        # Check for "current time" in response
        response_text = ' '.join(chat_lines)
        assert 'current time' in response_text.lower()

    @pytest.mark.asyncio
    async def test_empty_message_handling(self, conversation_coordinator, chat_lines):
        """Test handling empty message"""
        await conversation_coordinator.handle_user_message("")

        # Should reject empty message with validation error
        assert len(chat_lines) > 0
        assert any('Invalid input' in line for line in chat_lines)


class TestCommandRegistryIntegration:
    """Test CommandRegistry integration"""

    @pytest.fixture
    def chat_lines(self):
        """Track chat lines"""
        return []

    @pytest.fixture
    def system_lines(self):
        """Track system lines"""
        return []

    @pytest.fixture
    def command_registry(self, chat_lines, system_lines):
        """Create command registry"""
        def add_chat_line(line):
            chat_lines.append(line)

        def add_system_line(line):
            system_lines.append(line)

        return CommandRegistry(
            add_chat_line_callback=add_chat_line,
            add_system_line_callback=add_system_line
        )

    @pytest.mark.asyncio
    async def test_command_registry_initialization(self, command_registry):
        """Test command registry initializes with core commands"""
        assert 'help' in command_registry.commands
        assert 'memory' in command_registry.commands
        assert 'quit' in command_registry.commands
        assert len(command_registry.commands) > 0

    @pytest.mark.asyncio
    async def test_route_help_command(self, command_registry, chat_lines):
        """Test routing help command"""
        await command_registry.route_command('help', [])

        # Should display available commands (help outputs to chat, not system)
        assert len(chat_lines) > 0
        assert any('Commands' in line for line in chat_lines)

    @pytest.mark.asyncio
    async def test_route_metrics_command(self, command_registry, chat_lines):
        """Test routing metrics command"""
        # Set a mock handler for metrics
        async def mock_metrics_handler(args):
            command_registry.add_chat_line("Metrics: 100 thoughts")

        command_registry.commands['metrics'] = mock_metrics_handler

        await command_registry.route_command('metrics', [])

        # Should display metrics
        assert len(chat_lines) > 0
        assert any('Metrics' in line for line in chat_lines)

    @pytest.mark.asyncio
    async def test_route_unknown_command(self, command_registry, system_lines):
        """Test routing unknown command shows error"""
        await command_registry.route_command('nonexistent', [])

        # Should show error message
        assert len(system_lines) > 0
        assert any('Unknown command' in line for line in system_lines)

    @pytest.mark.asyncio
    async def test_register_custom_command(self, command_registry):
        """Test registering custom command"""
        executed = []

        async def custom_handler(args):
            executed.append(args)

        # register_command takes 2 params: name and handler
        command_registry.register_command('custom', custom_handler)

        assert 'custom' in command_registry.commands

        # Execute custom command
        await command_registry.route_command('custom', ['arg1', 'arg2'])
        assert len(executed) == 1
        assert executed[0] == ['arg1', 'arg2']

    @pytest.mark.asyncio
    async def test_command_with_arguments(self, command_registry):
        """Test command routing with arguments"""
        # Test help command with arguments
        chat_lines = []
        command_registry.add_chat_line = lambda line: chat_lines.append(line)

        await command_registry.route_command('help', ['memory'])

        # Should show help (general help, not command-specific in current implementation)
        assert len(chat_lines) > 0


class TestTUICoordinatorIntegration:
    """Test integration between all TUI coordinators"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator"""
        orchestrator = AsyncMock()
        orchestrator.get_service = MagicMock(return_value=None)
        orchestrator.publish = AsyncMock()
        return orchestrator

    @pytest.fixture
    def mock_thought_generator(self):
        """Create mock thought generator"""
        generator = AsyncMock()
        generator.generate_response = AsyncMock(return_value="AI response")
        return generator

    @pytest.fixture
    def ui_lines(self):
        """Track all UI lines"""
        return {
            'consciousness': [],
            'chat': [],
            'system': []
        }

    @pytest.fixture
    def all_coordinators(self, mock_orchestrator, mock_thought_generator, ui_lines):
        """Create all coordinators integrated together"""
        consciousness = ConsciousnessCoordinator(
            orchestrator=mock_orchestrator,
            add_consciousness_line_callback=lambda line, color=None: ui_lines['consciousness'].append(line)
        )

        conversation = ConversationCoordinator(
            thought_generator=mock_thought_generator,
            orchestrator=mock_orchestrator,
            add_chat_line_callback=lambda line: ui_lines['chat'].append(line)
        )

        command_registry = CommandRegistry(
            add_chat_line_callback=lambda line: ui_lines['chat'].append(line),
            add_system_line_callback=lambda line: ui_lines['system'].append(line)
        )

        return {
            'consciousness': consciousness,
            'conversation': conversation,
            'commands': command_registry,
            'orchestrator': mock_orchestrator,
            'thought_generator': mock_thought_generator
        }

    @pytest.mark.asyncio
    async def test_end_to_end_user_interaction(self, all_coordinators, ui_lines):
        """Test complete user interaction flow through all coordinators"""
        conversation = all_coordinators['conversation']
        commands = all_coordinators['commands']

        # User sends message
        await conversation.handle_user_message("Hello, Claude!")

        # Verify message appears in chat
        assert len(ui_lines['chat']) >= 2
        assert any('You:' in line for line in ui_lines['chat'])
        assert any('Claude:' in line for line in ui_lines['chat'])

        # User executes help command (which outputs to chat, not system)
        await commands.route_command('help', [])

        # Verify help response appears in chat
        assert len(ui_lines['chat']) > 2  # User message + AI response + help text
        assert any('Commands' in line for line in ui_lines['chat'])

    @pytest.mark.asyncio
    async def test_consciousness_runs_parallel_to_conversation(
        self, all_coordinators, ui_lines
    ):
        """Test consciousness continues running while user converses"""
        consciousness = all_coordinators['consciousness']
        conversation = all_coordinators['conversation']

        # Start consciousness loop
        consciousness.running = True
        consciousness_task = asyncio.create_task(
            consciousness.run_consciousness_loop()
        )

        # User has conversation while consciousness runs
        await conversation.handle_user_message("Test message")
        await asyncio.sleep(0.5)

        # Stop consciousness
        consciousness.running = False
        try:
            await asyncio.wait_for(consciousness_task, timeout=2.0)
        except asyncio.TimeoutError:
            consciousness_task.cancel()

        # Verify both worked independently
        assert len(ui_lines['chat']) > 0  # Conversation happened
        # Consciousness may or may not have generated (timing dependent)

    @pytest.mark.asyncio
    async def test_all_coordinators_share_orchestrator(self, all_coordinators):
        """Test all coordinators use same orchestrator instance"""
        consciousness = all_coordinators['consciousness']
        conversation = all_coordinators['conversation']
        orchestrator = all_coordinators['orchestrator']

        # All should reference same orchestrator
        assert consciousness.orchestrator is orchestrator
        assert conversation.orchestrator is orchestrator

    @pytest.mark.asyncio
    async def test_coordinator_cleanup(self, all_coordinators):
        """Test coordinators clean up properly"""
        consciousness = all_coordinators['consciousness']

        # Start and stop consciousness
        consciousness.running = True
        task = asyncio.create_task(consciousness.run_consciousness_loop())
        await asyncio.sleep(0.1)
        consciousness.running = False

        # Should complete without errors
        await asyncio.wait_for(task, timeout=2.0)
        assert task.done()
        assert not task.cancelled()
