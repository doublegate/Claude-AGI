"""
TUI Controller for Claude-AGI
=============================

Coordinates between UI rendering, event handling, and core AGI components.
Implements the controller pattern to separate concerns and manage interactions.
"""

import asyncio
import logging
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..consciousness.stream import ConsciousnessStream
from ..core.ai_integration import ThoughtGenerator
from ..core.orchestrator import AGIOrchestrator, Message, SystemState
from ..database.models import EmotionalState, Goal, Interest, StreamType
from ..memory.manager import MemoryManager
from .commands import AdvancedCommands
from .event_handler import EventHandler
from .ui_renderer import PaneType, UIRenderer

logger = logging.getLogger(__name__)


class TUIController:
    """
    Controls TUI interactions and coordinates AGI components
    
    Responsibilities:
    - Coordinate UI rendering and event handling
    - Interface between TUI and AGI core components
    - Handle command routing and execution
    - Manage application state and lifecycle
    - Process consciousness streams and user interactions
    """
    
    def __init__(self, config: Dict[str, Any], orchestrator: AGIOrchestrator):
        """Initialize TUI controller with configuration and components"""
        self.config = config
        self.orchestrator = orchestrator
        
        # UI components (will be set during initialization)
        self.ui_renderer: Optional[UIRenderer] = None
        self.event_handler: Optional[EventHandler] = None
        
        # AGI components
        self.memory_manager: Optional[MemoryManager] = None
        self.consciousness: Optional[ConsciousnessStream] = None
        self.safety = None
        self.thought_generator = ThoughtGenerator()
        self.thought_queue = asyncio.Queue()
        
        # Application state
        self.running = True
        self.total_thoughts = 0
        self.status_message = "Claude-AGI System Initialized"
        
        # Emotional state tracking
        self.emotional_history = deque(maxlen=100)
        self.current_emotional_state = EmotionalState(valence=0.0, arousal=0.5)
        
        # Goals tracking
        self.active_goals: List[Goal] = []
        self.completed_goals: List[Goal] = []
        
        # Conversation context
        self.conversation_history = deque(maxlen=20)
        self.in_conversation = False
        
        # Performance metrics
        self.metrics = {
            'thoughts_generated': 0,
            'memories_stored': 0,
            'goals_completed': 0,
            'uptime_start': datetime.now()
        }
        
        # Command registry
        self.commands = {
            'memory': self.memory_command,
            'stream': self.stream_command,
            'emotional': self.emotional_command,
            'goals': self.goals_command,
            'layout': self.layout_command,
            'state': self.state_command,
            'metrics': self.metrics_command,
            'safety': self.safety_command,
            'quit': self.quit_command,
            'dream': self.dream_command,
            'reflect': self.reflect_command,
            'explore': self.explore_command,
            'discoveries': self.discoveries_command,
            'help': self.show_help,
        }
        
        # Task management
        self.background_tasks: List[asyncio.Task] = []
        
        # Advanced command processor
        self.advanced_commands = AdvancedCommands()
    
    def initialize_ui(self, stdscr):
        """Initialize UI components with curses screen"""
        logger.info("Initializing TUI components")
        
        # Create UI components
        self.ui_renderer = UIRenderer(stdscr)
        self.event_handler = EventHandler(stdscr, self.route_command)
        
        # Set up event handling
        self.event_handler.set_event_callback(self.handle_event)
        
        # Initialize AGI components
        self._initialize_agi_components()
        
        logger.info("TUI initialization complete")
    
    def _initialize_agi_components(self):
        """Initialize AGI components after UI setup"""
        # These will be set by the main application
        # This method provides a hook for initialization
        pass
    
    async def run(self):
        """Main controller loop"""
        logger.info("Starting TUI controller")
        
        try:
            # Start background tasks
            await self._start_background_tasks()
            
            # Main event loop
            while self.running and self.event_handler.is_running():
                try:
                    # Update UI with current state
                    await self._update_ui()
                    
                    # Small delay to prevent excessive CPU usage
                    await asyncio.sleep(0.1)
                    
                except KeyboardInterrupt:
                    logger.info("Keyboard interrupt received")
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Fatal error in TUI controller: {e}")
        finally:
            await self._cleanup()
        
        logger.info("TUI controller stopped")
    
    async def _start_background_tasks(self):
        """Start all background tasks"""
        logger.info("Starting background tasks")
        
        # Input handling task
        input_task = asyncio.create_task(self.event_handler.input_loop())
        self.background_tasks.append(input_task)
        
        # Consciousness processing task
        consciousness_task = asyncio.create_task(self._consciousness_loop())
        self.background_tasks.append(consciousness_task)
        
        # UI refresh task
        refresh_task = asyncio.create_task(self._ui_refresh_loop())
        self.background_tasks.append(refresh_task)
    
    async def _consciousness_loop(self):
        """Process consciousness streams continuously"""
        logger.info("Starting consciousness processing loop")
        
        while self.running:
            try:
                if self.thought_generator and hasattr(self.thought_generator, 'generate_thought'):
                    # Generate a thought
                    thought = await self.thought_generator.generate_thought(
                        "continuous_consciousness",
                        context={"stream": "primary", "mode": "exploration"}
                    )
                    
                    if thought:
                        self.total_thoughts += 1
                        self.metrics['thoughts_generated'] = self.total_thoughts
                        
                        # Add to consciousness pane
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        formatted_thought = f"[{timestamp}] {thought}"
                        
                        self.ui_renderer.add_line_to_pane(
                            PaneType.CONSCIOUSNESS, 
                            formatted_thought
                        )
                        
                        # Store in memory if available
                        if self.memory_manager:
                            await self._store_thought_in_memory(thought)
                
                # Wait before next thought (human-like pacing)
                await asyncio.sleep(2.0)
                
            except asyncio.CancelledError:
                logger.info("Consciousness loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in consciousness loop: {e}")
                await asyncio.sleep(5)
        
        logger.info("Consciousness processing loop ended")
    
    async def _ui_refresh_loop(self):
        """Refresh UI periodically"""
        while self.running:
            try:
                # Let UI refresh itself
                await asyncio.sleep(1.0)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in UI refresh loop: {e}")
                await asyncio.sleep(1)
    
    async def _update_ui(self):
        """Update UI with current state"""
        if not self.ui_renderer or not self.event_handler:
            return
        
        try:
            # Update active pane
            current_focus = self.event_handler.get_current_focus()
            self.ui_renderer.set_active_pane(current_focus)
            
            # Draw all panes
            self.ui_renderer.draw_all_panes()
            
            # Draw status bar
            self.ui_renderer.draw_status_bar(self.status_message, self.metrics)
            
            # Draw input line
            input_text, is_command_mode = self.event_handler.get_current_input()
            self.ui_renderer.draw_input_line(input_text, is_command_mode)
            
            # Refresh display
            self.ui_renderer.refresh_all()
            
        except Exception as e:
            logger.error(f"Error updating UI: {e}")
    
    async def handle_event(self, event_type: str, data: Dict[str, Any]):
        """Handle events from the event handler"""
        try:
            if event_type == 'quit_requested':
                await self.quit_command([])
                
            elif event_type == 'focus_changed':
                pane = data.get('pane')
                if pane:
                    self.ui_renderer.set_active_pane(pane)
                    
            elif event_type == 'clear_pane':
                pane = data.get('pane')
                if pane:
                    self.ui_renderer.clear_pane_buffer(pane)
                    
            elif event_type == 'layout_changed':
                layout = data.get('layout')
                if layout:
                    self.ui_renderer.set_layout_mode(layout)
                    self.status_message = f"Layout changed to {layout}"
                    
            elif event_type == 'user_message':
                message = data.get('message')
                if message:
                    await self.handle_user_message(message)
                    
            elif event_type == 'system_message':
                message = data.get('message')
                if message:
                    self.add_system_line(message)
                    
            elif event_type == 'help_requested':
                args = data.get('args', [])
                await self.show_help(args)
                
            elif event_type == 'unknown_command':
                command = data.get('command')
                self.add_system_line(f"Unknown command: /{command}")
                
            elif event_type == 'command_error':
                command = data.get('command')
                error = data.get('error')
                self.add_system_line(f"Error in /{command}: {error}")
                
        except Exception as e:
            logger.error(f"Error handling event {event_type}: {e}")
    
    async def route_command(self, command: str, args: List[str]):
        """Route command to appropriate handler"""
        if command in self.commands:
            try:
                await self.commands[command](args)
            except Exception as e:
                logger.error(f"Error executing command {command}: {e}")
                self.add_system_line(f"Error in /{command}: {str(e)}")
        else:
            self.add_system_line(f"Unknown command: /{command}")
    
    async def handle_user_message(self, message: str):
        """Handle user message input"""
        try:
            # Add user message to chat
            self.add_chat_line(f"You: {message}")
            
            # Add to conversation context
            self.conversation_history.append({"role": "user", "content": message})
            self.in_conversation = True
            
            # Generate response
            response = await self._generate_response(message)
            
            # Add response to chat
            self.add_chat_line(f"Claude: {response}")
            
            # Add to conversation context
            self.conversation_history.append({"role": "assistant", "content": response})
            
        except Exception as e:
            logger.error(f"Error handling user message: {e}")
            self.add_chat_line(f"Error: {str(e)}")
    
    async def _generate_response(self, user_input: str) -> str:
        """Generate response to user input"""
        try:
            # Use thought generator if available
            if self.thought_generator and hasattr(self.thought_generator, 'generate_thought'):
                response = await self.thought_generator.generate_thought(
                    f"respond_to_user: {user_input}",
                    context={"conversation": list(self.conversation_history)}
                )
                return response or "I'm processing your message..."
            else:
                return "I'm still initializing my response systems..."
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I encountered an error processing your message."
    
    async def _store_thought_in_memory(self, thought: str):
        """Store thought in memory system"""
        try:
            if self.memory_manager:
                # Create memory entry
                memory_data = {
                    'content': thought,
                    'timestamp': datetime.now(),
                    'type': 'thought',
                    'importance': 0.5,
                    'source': 'consciousness_stream'
                }
                
                # Store in memory
                await self.memory_manager.store_memory(memory_data)
                self.metrics['memories_stored'] += 1
                
        except Exception as e:
            logger.error(f"Error storing thought in memory: {e}")
    
    # UI Helper Methods
    def add_consciousness_line(self, text: str):
        """Add line to consciousness pane"""
        if self.ui_renderer:
            self.ui_renderer.add_line_to_pane(PaneType.CONSCIOUSNESS, text)
    
    def add_chat_line(self, text: str):
        """Add line to chat pane"""
        if self.ui_renderer:
            self.ui_renderer.add_line_to_pane(PaneType.CHAT, text)
    
    def add_system_line(self, text: str):
        """Add system message to chat pane"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        system_line = f"[{timestamp}] SYSTEM: {text}"
        if self.ui_renderer:
            self.ui_renderer.add_line_to_pane(PaneType.CHAT, system_line)
    
    def add_memory_line(self, text: str):
        """Add line to memory pane"""
        if self.ui_renderer:
            self.ui_renderer.add_line_to_pane(PaneType.MEMORY, text)
    
    def add_emotional_line(self, text: str):
        """Add line to emotional pane"""
        if self.ui_renderer:
            self.ui_renderer.add_line_to_pane(PaneType.EMOTIONAL, text)
    
    def add_goals_line(self, text: str):
        """Add line to goals pane"""
        if self.ui_renderer:
            self.ui_renderer.add_line_to_pane(PaneType.GOALS, text)
    
    # Command Implementations (delegate to original implementations)
    async def memory_command(self, args: List[str]):
        """Handle memory-related commands"""
        if not args:
            self.add_system_line("Memory commands: store, recall, search, stats, clear")
            return
        
        subcmd = args[0]
        
        if subcmd == "stats":
            if self.memory_manager:
                # Get memory statistics
                stats = await self._get_memory_stats()
                self.add_memory_line(f"Memory Statistics:")
                self.add_memory_line(f"  Working: {stats.get('working_count', 0)} items")
                self.add_memory_line(f"  Episodic: {stats.get('episodic_count', 0)} memories")
                self.add_memory_line(f"  Semantic: {stats.get('semantic_count', 0)} concepts")
            else:
                self.add_system_line("Memory manager not initialized")
        
        elif subcmd == "recall":
            query = " ".join(args[1:]) if len(args) > 1 else "recent"
            memories = await self._recall_memories(query)
            
            self.add_memory_line(f"Recalling memories about: {query}")
            for memory in memories[:5]:  # Show top 5
                timestamp = memory.get('timestamp', 'Unknown')
                content = memory.get('content', 'No content')[:100]
                self.add_memory_line(f"  [{timestamp}] {content}...")
        
        elif subcmd == "search":
            if len(args) < 2:
                self.add_system_line("Usage: /memory search <query>")
                return
            
            query = " ".join(args[1:])
            results = await self._search_memories(query)
            
            self.add_memory_line(f"Search results for: {query}")
            for result in results[:5]:
                relevance = result.get('relevance', 0)
                content = result.get('content', 'No content')[:80]
                self.add_memory_line(f"  [{relevance:.2f}] {content}...")
        
        elif subcmd == "clear":
            if self.memory_manager:
                # Clear working memory only for safety
                await self.memory_manager.clear_working_memory()
                self.add_memory_line("Working memory cleared")
            else:
                self.add_system_line("Memory manager not initialized")
        
        else:
            self.add_system_line(f"Unknown memory command: {subcmd}")
    
    async def _get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        if self.memory_manager:
            try:
                return await self.memory_manager.get_statistics()
            except:
                pass
        
        return {
            'working_count': 0,
            'episodic_count': 0,
            'semantic_count': 0
        }
    
    async def _recall_memories(self, query: str) -> List[Dict[str, Any]]:
        """Recall memories by query"""
        if self.memory_manager:
            try:
                return await self.memory_manager.recall_memories(query, limit=5)
            except:
                pass
        
        return []
    
    async def _search_memories(self, query: str) -> List[Dict[str, Any]]:
        """Search memories"""
        if self.memory_manager:
            try:
                return await self.memory_manager.search_memories(query, limit=5)
            except:
                pass
        
        return []
    
    # Additional command stubs (to be implemented)
    async def stream_command(self, args: List[str]):
        """Handle consciousness stream commands"""
        self.add_system_line("Stream commands not yet implemented")
    
    async def emotional_command(self, args: List[str]):
        """Handle emotional state commands"""
        self.add_system_line("Emotional commands not yet implemented")
    
    async def goals_command(self, args: List[str]):
        """Handle goals commands"""
        self.add_system_line("Goals commands not yet implemented")
    
    async def layout_command(self, args: List[str]):
        """Handle layout commands - already handled by event system"""
        pass
    
    async def state_command(self, args: List[str]):
        """Handle state commands"""
        self.add_system_line("State commands not yet implemented")
    
    async def metrics_command(self, args: List[str]):
        """Handle metrics commands"""
        uptime = datetime.now() - self.metrics['uptime_start']
        self.add_system_line(f"Metrics:")
        self.add_system_line(f"  Thoughts: {self.metrics['thoughts_generated']}")
        self.add_system_line(f"  Memories: {self.metrics['memories_stored']}")
        self.add_system_line(f"  Goals: {self.metrics['goals_completed']}")
        self.add_system_line(f"  Uptime: {str(uptime).split('.')[0]}")
    
    async def safety_command(self, args: List[str]):
        """Handle safety commands"""
        self.add_system_line("Safety commands not yet implemented")
    
    async def quit_command(self, args: List[str]):
        """Handle quit command"""
        self.add_system_line("Shutting down Claude-AGI...")
        self.running = False
        if self.event_handler:
            self.event_handler.stop()
    
    async def dream_command(self, args: List[str]):
        """Handle dream commands"""
        await self.advanced_commands.dream_command(args, self.add_system_line)
    
    async def reflect_command(self, args: List[str]):
        """Handle reflection commands"""
        await self.advanced_commands.reflect_command(args, self.add_system_line)
    
    async def explore_command(self, args: List[str]):
        """Handle exploration commands"""
        await self.advanced_commands.explore_command(args, self.add_system_line)
    
    async def discoveries_command(self, args: List[str]):
        """Handle discoveries commands"""
        await self.advanced_commands.discoveries_command(args, self.add_system_line)
    
    async def show_help(self, args: List[str]):
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
    
    # Component setters
    def set_memory_manager(self, memory_manager: MemoryManager):
        """Set memory manager component"""
        self.memory_manager = memory_manager
        self._update_advanced_commands()
    
    def set_consciousness_stream(self, consciousness: ConsciousnessStream):
        """Set consciousness stream component"""
        self.consciousness = consciousness
        self._update_advanced_commands()
    
    def set_safety_framework(self, safety):
        """Set safety framework component"""
        self.safety = safety
        
        # Update advanced commands with all components
        self._update_advanced_commands()
    
    def _update_advanced_commands(self):
        """Update advanced commands with current components"""
        self.advanced_commands.set_components(
            memory_manager=self.memory_manager,
            consciousness_stream=self.consciousness,
            thought_generator=self.thought_generator,
            exploration_engine=getattr(self, 'exploration_engine', None),
            safety_framework=self.safety
        )
    
    # Cleanup
    async def _cleanup(self):
        """Clean up resources and stop background tasks"""
        logger.info("Cleaning up TUI controller")
        
        # Cancel all background tasks
        for task in self.background_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to finish
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # Stop event handler
        if self.event_handler:
            self.event_handler.stop()
        
        logger.info("TUI controller cleanup complete")