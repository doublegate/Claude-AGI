"""
Command Registry for Claude-AGI TUI
===================================

Centralizes all command registration, routing, and execution.
Extracted from TUIController to follow Single Responsibility Principle.
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..database.models import EmotionalState, Goal

logger = logging.getLogger(__name__)


class CommandRegistry:
    """
    Centralized command registry and router

    Responsibilities:
    - Register all available commands
    - Route commands to appropriate handlers
    - Validate command arguments
    - Provide command help and documentation
    """

    def __init__(self, add_chat_line_callback: Callable, add_system_line_callback: Callable):
        """
        Initialize command registry

        Args:
            add_chat_line_callback: Callback to add chat messages
            add_system_line_callback: Callback to add system messages
        """
        self.add_chat_line = add_chat_line_callback
        self.add_system_line = add_system_line_callback

        # Command registry
        self.commands: Dict[str, Callable] = {}
        self._register_core_commands()

        # External handlers (set by controller)
        self.advanced_commands = None
        self.memory_handler = None
        self.consciousness_handler = None
        self.emotional_handler = None
        self.goals_handler = None
        self.layout_handler = None
        self.metrics_handler = None

    def _register_core_commands(self):
        """Register core TUI commands"""
        self.commands = {
            'help': self.help_command,
            'quit': self.quit_command,
            'exit': self.quit_command,
            'memory': self.memory_command,
            'stream': self.stream_command,
            'emotional': self.emotional_command,
            'goals': self.goals_command,
            'layout': self.layout_command,
            'state': self.state_command,
            'metrics': self.metrics_command,
            'safety': self.safety_command,
            # Advanced commands (delegated)
            'dream': self.dream_command,
            'reflect': self.reflect_command,
            'explore': self.explore_command,
            'discoveries': self.discoveries_command,
        }

    def set_handlers(self, **kwargs):
        """Set external command handlers"""
        for key, value in kwargs.items():
            setattr(self, key, value)

    async def route_command(self, command: str, args: List[str]):
        """Route command to appropriate handler with validation"""
        # Validate command name
        if not command or not isinstance(command, str) or len(command) > 50:
            self.add_system_line("Invalid command format")
            return

        # Validate command arguments
        if not self._validate_command_args(args):
            self.add_system_line("Invalid command arguments detected")
            return

        if command in self.commands:
            try:
                await self.commands[command](args)
            except Exception as e:
                logger.error(f"Error executing command {command}: {e}")
                self.add_system_line(f"Error in /{command}: Command execution failed")
        else:
            self.add_system_line(f"Unknown command: /{command}")

    def _validate_command_args(self, args: List[str]) -> bool:
        """Validate command arguments for safety"""
        if not args:
            return True

        for arg in args:
            if not isinstance(arg, str):
                return False
            if len(arg) > 100:  # Individual argument length limit
                return False
            # Check for path traversal in arguments
            if '..' in arg or '/' in arg or '\\' in arg:
                if not self._is_safe_path_reference(arg):
                    return False

        return True

    def _is_safe_path_reference(self, path: str) -> bool:
        """Check if a path reference is safe (within allowed directories)"""
        # For now, be very restrictive - no path references allowed
        # This can be expanded later to allow specific safe paths
        return False

    # Core command implementations

    async def help_command(self, args: List[str]):
        """Show help information"""
        help_text = [
            "Claude-AGI Commands:",
            "",
            "Core Commands:",
            "  /memory <cmd>    - Memory operations (store, recall, search, stats)",
            "  /stream <cmd>    - Consciousness stream control",
            "  /emotional <cmd> - Emotional state management",
            "  /goals <cmd>     - Goal and interest management",
            "",
            "Interface Commands:",
            "  /layout <mode>   - Change layout (standard, memory_focus, emotional_focus)",
            "  /focus <pane>    - Focus on specific pane",
            "  /clear [pane]    - Clear pane content",
            "  /metrics         - Show performance metrics",
            "",
            "Advanced Commands:",
            "  /dream <cmd>     - Dream generation and analysis",
            "  /reflect <cmd>   - Self-reflection and introspection",
            "  /explore <cmd>   - Web exploration and discovery",
            "  /discoveries     - View recent discoveries",
            "",
            "Navigation:",
            "  Tab              - Cycle through panes",
            "  /                - Enter command mode",
            "  Escape           - Exit command mode",
            "  Up/Down Arrows   - Command history",
            "",
            "Type '/help <command>' for detailed help on specific commands."
        ]

        for line in help_text:
            self.add_chat_line(line)

    async def quit_command(self, args: List[str]):
        """Handle quit command - delegate to quit handler"""
        if self.quit_handler:
            await self.quit_handler(args)
        else:
            self.add_system_line("Quitting...")

    async def memory_command(self, args: List[str]):
        """Delegate memory commands to memory handler"""
        if self.memory_handler:
            await self.memory_handler(args)
        else:
            self.add_system_line("Memory handler not available")

    async def stream_command(self, args: List[str]):
        """Delegate stream commands to consciousness handler"""
        if self.consciousness_handler:
            await self.consciousness_handler(args)
        else:
            self.add_system_line("Consciousness handler not available")

    async def emotional_command(self, args: List[str]):
        """Delegate emotional commands to emotional handler"""
        if self.emotional_handler:
            await self.emotional_handler(args)
        else:
            self.add_system_line("Emotional handler not available")

    async def goals_command(self, args: List[str]):
        """Delegate goals commands to goals handler"""
        if self.goals_handler:
            await self.goals_handler(args)
        else:
            self.add_system_line("Goals handler not available")

    async def layout_command(self, args: List[str]):
        """Delegate layout commands to layout handler"""
        if self.layout_handler:
            await self.layout_handler(args)
        else:
            self.add_system_line("Layout handler not available")

    async def state_command(self, args: List[str]):
        """Delegate state commands to state handler"""
        if self.state_handler:
            await self.state_handler(args)
        else:
            self.add_system_line("State handler not available")

    async def metrics_command(self, args: List[str]):
        """Delegate metrics commands to metrics handler"""
        if self.metrics_handler:
            await self.metrics_handler(args)
        else:
            self.add_system_line("Metrics handler not available")

    async def safety_command(self, args: List[str]):
        """Handle safety commands"""
        self.add_system_line("Safety commands not yet implemented")

    # Advanced command delegations

    async def dream_command(self, args: List[str]):
        """Delegate dream commands to advanced commands handler"""
        if self.advanced_commands:
            await self.advanced_commands.dream_command(args, self.add_system_line)
        else:
            self.add_system_line("Dream commands not available")

    async def reflect_command(self, args: List[str]):
        """Delegate reflection commands to advanced commands handler"""
        if self.advanced_commands:
            await self.advanced_commands.reflect_command(args, self.add_system_line)
        else:
            self.add_system_line("Reflection commands not available")

    async def explore_command(self, args: List[str]):
        """Delegate exploration commands to advanced commands handler"""
        if self.advanced_commands:
            await self.advanced_commands.explore_command(args, self.add_system_line)
        else:
            self.add_system_line("Exploration commands not available")

    async def discoveries_command(self, args: List[str]):
        """Delegate discoveries commands to advanced commands handler"""
        if self.advanced_commands:
            await self.advanced_commands.discoveries_command(args, self.add_system_line)
        else:
            self.add_system_line("Discoveries commands not available")

    def get_available_commands(self) -> List[str]:
        """Get list of available commands"""
        return sorted(self.commands.keys())

    def has_command(self, command: str) -> bool:
        """Check if command is registered"""
        return command in self.commands

    def register_command(self, name: str, handler: Callable):
        """Register a new command handler"""
        self.commands[name] = handler
        logger.info(f"Registered command: /{name}")

    def unregister_command(self, name: str):
        """Unregister a command"""
        if name in self.commands:
            del self.commands[name]
            logger.info(f"Unregistered command: /{name}")
