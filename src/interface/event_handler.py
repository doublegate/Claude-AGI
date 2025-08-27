"""
Event Handler for Claude-AGI TUI
================================

Handles all user input and event processing for the terminal interface including:
- Keyboard input processing
- Command parsing and routing
- Navigation between panes
- Input history management
"""

import asyncio
import curses
import logging
from collections import deque
from typing import Any, Callable, Dict, List, Optional

from .ui_renderer import PaneType

logger = logging.getLogger(__name__)


class EventHandler:
    """
    Handles user input and events for Claude-AGI TUI
    
    Responsibilities:
    - Keyboard input processing
    - Command mode handling
    - Navigation between panes
    - Input history management
    - Event routing to appropriate handlers
    """
    
    def __init__(self, stdscr, command_router: Optional[Callable] = None):
        """Initialize event handler"""
        self.stdscr = stdscr
        self.command_router = command_router
        
        # Input state
        self.input_buffer = ""
        self.command_mode = False
        self.command_buffer = ""
        self.running = True
        
        # Navigation state
        self.current_focus = PaneType.CHAT
        
        # Input history
        self.command_history = deque(maxlen=50)
        self.history_index = -1
        
        # Event handlers registry
        self.event_handlers: Dict[str, Callable] = {
            'quit': self._handle_quit,
            'focus': self._handle_focus_change,
            'clear': self._handle_clear_pane,
            'layout': self._handle_layout_change,
            'help': self._handle_help_request,
        }
        
        # Key bindings
        self.key_bindings = {
            ord('\t'): self._handle_tab,           # Tab for pane navigation
            27: self._handle_escape,               # Escape key
            ord('\n'): self._handle_enter,         # Enter key
            curses.KEY_UP: self._handle_up_arrow,  # History navigation
            curses.KEY_DOWN: self._handle_down_arrow,
            curses.KEY_LEFT: self._handle_left_arrow,
            curses.KEY_RIGHT: self._handle_right_arrow,
            curses.KEY_BACKSPACE: self._handle_backspace,
            127: self._handle_backspace,           # Delete key
            ord('/'): self._handle_slash,          # Command mode
        }
        
        # Configure curses for non-blocking input
        self.stdscr.nodelay(True)
        self.stdscr.timeout(100)  # 100ms timeout
    
    async def input_loop(self):
        """Main input processing loop"""
        logger.info("Starting input event loop")
        
        while self.running:
            try:
                # Get user input with timeout
                key = self.stdscr.getch()
                
                if key == -1:
                    # No input available, yield control
                    await asyncio.sleep(0.01)
                    continue
                
                await self._process_key(key)
                
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
                await self._handle_quit()
                break
            except Exception as e:
                logger.error(f"Error in input loop: {e}")
                await asyncio.sleep(0.1)
        
        logger.info("Input event loop ended")
    
    async def _process_key(self, key: int):
        """Process a single key press"""
        try:
            # Check for special key bindings first
            if key in self.key_bindings:
                await self.key_bindings[key]()
                return
            
            # Handle printable characters
            if 32 <= key <= 126:  # Printable ASCII range
                char = chr(key)
                
                if self.command_mode:
                    self.command_buffer += char
                else:
                    self.input_buffer += char
                    
        except Exception as e:
            logger.error(f"Error processing key {key}: {e}")
    
    async def _handle_tab(self):
        """Handle tab key - cycle through panes"""
        pane_types = list(PaneType)
        current_index = pane_types.index(self.current_focus)
        next_index = (current_index + 1) % len(pane_types)
        self.current_focus = pane_types[next_index]
        
        # Emit focus change event
        await self._emit_event('focus_changed', {'pane': self.current_focus})
    
    async def _handle_escape(self):
        """Handle escape key - exit command mode or quit"""
        if self.command_mode:
            self.command_mode = False
            self.command_buffer = ""
        else:
            # Double-escape to quit
            await self._handle_quit()
    
    async def _handle_enter(self):
        """Handle enter key - execute command or send message"""
        if self.command_mode:
            command = self.command_buffer.strip()
            if command:
                await self._execute_command(command)
                self.command_history.append(f"/{command}")
            
            self.command_mode = False
            self.command_buffer = ""
            
        else:
            message = self.input_buffer.strip()
            if message:
                await self._emit_event('user_message', {'message': message})
                self.command_history.append(message)
            
            self.input_buffer = ""
        
        # Reset history navigation
        self.history_index = -1
    
    async def _handle_up_arrow(self):
        """Handle up arrow - navigate command history"""
        if self.command_history:
            if self.history_index == -1:
                self.history_index = len(self.command_history) - 1
            elif self.history_index > 0:
                self.history_index -= 1
            
            if 0 <= self.history_index < len(self.command_history):
                historical_command = self.command_history[self.history_index]
                
                if historical_command.startswith('/'):
                    self.command_mode = True
                    self.command_buffer = historical_command[1:]
                    self.input_buffer = ""
                else:
                    self.command_mode = False
                    self.command_buffer = ""
                    self.input_buffer = historical_command
    
    async def _handle_down_arrow(self):
        """Handle down arrow - navigate command history"""
        if self.command_history and self.history_index != -1:
            self.history_index += 1
            
            if self.history_index >= len(self.command_history):
                # Clear input when going past end
                self.history_index = -1
                self.input_buffer = ""
                self.command_buffer = ""
                self.command_mode = False
            else:
                historical_command = self.command_history[self.history_index]
                
                if historical_command.startswith('/'):
                    self.command_mode = True
                    self.command_buffer = historical_command[1:]
                    self.input_buffer = ""
                else:
                    self.command_mode = False
                    self.command_buffer = ""
                    self.input_buffer = historical_command
    
    async def _handle_left_arrow(self):
        """Handle left arrow - cursor movement (future enhancement)"""
        # Future enhancement: cursor positioning within input
        pass
    
    async def _handle_right_arrow(self):
        """Handle right arrow - cursor movement (future enhancement)"""
        # Future enhancement: cursor positioning within input
        pass
    
    async def _handle_backspace(self):
        """Handle backspace - delete character"""
        if self.command_mode:
            if self.command_buffer:
                self.command_buffer = self.command_buffer[:-1]
        else:
            if self.input_buffer:
                self.input_buffer = self.input_buffer[:-1]
    
    async def _handle_slash(self):
        """Handle slash key - enter command mode"""
        if not self.command_mode and not self.input_buffer:
            self.command_mode = True
            self.command_buffer = ""
    
    async def _execute_command(self, command: str):
        """Execute a slash command"""
        try:
            parts = command.strip().split()
            if not parts:
                return
            
            cmd_name = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            # Check built-in event handlers first
            if cmd_name in self.event_handlers:
                await self.event_handlers[cmd_name](args)
            elif self.command_router:
                # Route to external command handler
                await self.command_router(cmd_name, args)
            else:
                await self._emit_event('unknown_command', {'command': cmd_name, 'args': args})
                
        except Exception as e:
            logger.error(f"Error executing command '{command}': {e}")
            await self._emit_event('command_error', {'command': command, 'error': str(e)})
    
    async def _handle_quit(self, args: List[str] = None):
        """Handle quit command"""
        self.running = False
        await self._emit_event('quit_requested', {})
    
    async def _handle_focus_change(self, args: List[str]):
        """Handle focus change command"""
        if not args:
            await self._emit_event('system_message', {
                'message': f"Available panes: {', '.join([pt.value for pt in PaneType])}"
            })
            return
        
        pane_name = args[0].lower()
        
        # Find matching pane type
        for pane_type in PaneType:
            if pane_type.value.lower() == pane_name:
                self.current_focus = pane_type
                await self._emit_event('focus_changed', {'pane': pane_type})
                return
        
        await self._emit_event('system_message', {
            'message': f"Unknown pane: {pane_name}"
        })
    
    async def _handle_clear_pane(self, args: List[str]):
        """Handle clear pane command"""
        if args:
            pane_name = args[0].lower()
            for pane_type in PaneType:
                if pane_type.value.lower() == pane_name:
                    await self._emit_event('clear_pane', {'pane': pane_type})
                    return
        else:
            # Clear current pane
            await self._emit_event('clear_pane', {'pane': self.current_focus})
    
    async def _handle_layout_change(self, args: List[str]):
        """Handle layout change command"""
        if not args:
            await self._emit_event('system_message', {
                'message': "Available layouts: standard, memory_focus, emotional_focus"
            })
            return
        
        layout = args[0].lower()
        valid_layouts = ["standard", "memory_focus", "emotional_focus"]
        
        if layout in valid_layouts:
            await self._emit_event('layout_changed', {'layout': layout})
        else:
            await self._emit_event('system_message', {
                'message': f"Unknown layout: {layout}. Available: {', '.join(valid_layouts)}"
            })
    
    async def _handle_help_request(self, args: List[str]):
        """Handle help command"""
        await self._emit_event('help_requested', {'args': args})
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to be handled by the controller"""
        # This will be called by the controller's event system
        if hasattr(self, 'event_callback') and self.event_callback:
            try:
                await self.event_callback(event_type, data)
            except Exception as e:
                logger.error(f"Error in event callback for {event_type}: {e}")
    
    def set_event_callback(self, callback: Callable):
        """Set the callback function for event handling"""
        self.event_callback = callback
    
    def set_command_router(self, router: Callable):
        """Set the command router function"""
        self.command_router = router
    
    def get_current_input(self) -> tuple[str, bool]:
        """Get current input state"""
        if self.command_mode:
            return self.command_buffer, True
        else:
            return self.input_buffer, False
    
    def get_current_focus(self) -> PaneType:
        """Get currently focused pane"""
        return self.current_focus
    
    def set_focus(self, pane_type: PaneType):
        """Set focus to specific pane"""
        self.current_focus = pane_type
    
    def add_to_history(self, item: str):
        """Add item to command history"""
        self.command_history.append(item)
    
    def clear_input(self):
        """Clear current input"""
        self.input_buffer = ""
        self.command_buffer = ""
        self.command_mode = False
        self.history_index = -1
    
    def is_running(self) -> bool:
        """Check if event handler is still running"""
        return self.running
    
    def stop(self):
        """Stop the event handler"""
        self.running = False