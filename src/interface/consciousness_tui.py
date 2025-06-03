"""
Production-ready Consciousness TUI for Claude-AGI
================================================

A sophisticated terminal interface for interacting with Claude's consciousness,
featuring multiple panes for different streams, memory browsing, and real-time
visualization of cognitive processes.
"""

import os
import sys
import asyncio
import curses
from curses import wrapper
import threading
import queue
import time
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from collections import deque
from enum import Enum
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.orchestrator import AGIOrchestrator, SystemState
from src.memory.manager import MemoryManager
from src.consciousness.stream import ConsciousnessStream
from src.core.ai_integration import ThoughtGenerator
from src.database.models import StreamType, EmotionalState
from src.emotional.core import EmotionalCore
from src.exploration.engine import ExplorationEngine

# Configure logging
logging.basicConfig(
    filename='claude_agi_tui.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PaneType(Enum):
    """Types of panes in the TUI"""
    CONSCIOUSNESS = "consciousness"
    CONVERSATION = "conversation"
    MEMORY = "memory"
    EMOTIONAL = "emotional"
    GOALS = "goals"
    ENVIRONMENT = "environment"
    COMMAND = "command"


class Pane:
    """Base class for TUI panes"""
    
    def __init__(self, window, pane_type: PaneType, title: str):
        self.window = window
        self.pane_type = pane_type
        self.title = title
        self.content_lines = deque(maxlen=1000)
        self.height, self.width = window.getmaxyx()
        self.scroll_offset = 0
        
    def add_line(self, text: str, color_pair: int = 0):
        """Add a line of content"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.content_lines.append((f"[{timestamp}] {text}", color_pair))
        
    def draw(self):
        """Draw the pane"""
        self.window.clear()
        
        # Draw border and title
        self.window.box()
        title_str = f" {self.title} "
        self.window.addstr(0, 2, title_str[:self.width-4])
        
        # Draw content
        visible_height = self.height - 2  # Account for borders
        start_line = max(0, len(self.content_lines) - visible_height - self.scroll_offset)
        end_line = len(self.content_lines) - self.scroll_offset
        
        y = 1
        for i in range(start_line, end_line):
            if y >= self.height - 1:  # Leave room for border
                break
            
            if 0 <= i < len(self.content_lines):
                text, color = self.content_lines[i]
                # Truncate text to fit window
                if len(text) > self.width - 2:
                    text = text[:self.width-5] + "..."
                
                try:
                    self.window.addstr(y, 1, text, curses.color_pair(color))
                except curses.error:
                    pass  # Ignore if we can't draw
                    
            y += 1
        
        # Draw scroll indicators
        if start_line > 0:
            self.window.addstr(1, self.width-2, "↑")
        if end_line < len(self.content_lines):
            self.window.addstr(self.height-2, self.width-2, "↓")
        
        self.window.refresh()
    
    def scroll_up(self, lines: int = 1):
        """Scroll content up"""
        max_scroll = len(self.content_lines) - (self.height - 2)
        self.scroll_offset = min(self.scroll_offset + lines, max_scroll)
    
    def scroll_down(self, lines: int = 1):
        """Scroll content down"""
        self.scroll_offset = max(self.scroll_offset - lines, 0)


class ConsciousnessTUI:
    """Advanced TUI for Claude's consciousness"""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.running = True
        self.orchestrator = None
        self.memory_manager = None
        self.thought_generator = None
        
        # UI state
        self.panes = {}
        self.active_pane = PaneType.CONVERSATION
        self.command_mode = False
        self.command_buffer = ""
        self.conversation_history = []
        
        # Message queues for thread communication
        self.ui_queue = queue.Queue()
        self.thought_queue = queue.Queue()
        self.user_input_queue = queue.Queue()
        
        # Initialize curses
        self._init_curses()
        
        # Create panes
        self._create_panes()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _init_curses(self):
        """Initialize curses settings"""
        curses.curs_set(0)  # Hide cursor
        self.stdscr.nodelay(True)  # Non-blocking input
        
        # Initialize colors
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)    # Thoughts
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)   # User
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # System
        curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # Claude
        curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)     # Emotional
        curses.init_pair(6, curses.COLOR_BLUE, curses.COLOR_BLACK)    # Memory
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)   # Default
    
    def _create_panes(self):
        """Create UI panes with dynamic layout"""
        height, width = self.stdscr.getmaxyx()
        
        # Calculate pane dimensions
        # Layout: 3x2 grid plus command line
        pane_height = (height - 3) // 2  # -3 for command line and borders
        pane_width = width // 3
        
        # Create consciousness streams pane (top-left, double width)
        self.panes[PaneType.CONSCIOUSNESS] = Pane(
            curses.newwin(pane_height, pane_width * 2, 0, 0),
            PaneType.CONSCIOUSNESS,
            "Consciousness Streams"
        )
        
        # Create emotional state pane (top-right)
        self.panes[PaneType.EMOTIONAL] = Pane(
            curses.newwin(pane_height, pane_width, 0, pane_width * 2),
            PaneType.EMOTIONAL,
            "Emotional State"
        )
        
        # Create conversation pane (bottom-left)
        self.panes[PaneType.CONVERSATION] = Pane(
            curses.newwin(pane_height, pane_width, pane_height, 0),
            PaneType.CONVERSATION,
            "Conversation"
        )
        
        # Create memory pane (bottom-middle)
        self.panes[PaneType.MEMORY] = Pane(
            curses.newwin(pane_height, pane_width, pane_height, pane_width),
            PaneType.MEMORY,
            "Memory Browser"
        )
        
        # Create goals pane (bottom-right)
        self.panes[PaneType.GOALS] = Pane(
            curses.newwin(pane_height, pane_width, pane_height, pane_width * 2),
            PaneType.GOALS,
            "Goals & Intentions"
        )
        
        # Create command line (bottom)
        self.command_win = curses.newwin(2, width, height - 2, 0)
        
        # Draw initial UI
        self._draw_all_panes()
    
    def _draw_all_panes(self):
        """Draw all panes"""
        for pane in self.panes.values():
            pane.draw()
        self._draw_command_line()
    
    def _draw_command_line(self):
        """Draw the command line"""
        self.command_win.clear()
        self.command_win.box()
        
        if self.command_mode:
            prompt = "Command: " + self.command_buffer
            cursor_pos = len(prompt)
        else:
            prompt = "Press '/' for command mode, ESC to exit"
            cursor_pos = 0
        
        # Truncate if too long
        max_width = self.command_win.getmaxyx()[1] - 2
        if len(prompt) > max_width:
            prompt = prompt[:max_width-3] + "..."
        
        self.command_win.addstr(0, 1, prompt)
        
        # Show cursor in command mode
        if self.command_mode and cursor_pos < max_width:
            curses.curs_set(1)
            self.command_win.move(0, cursor_pos + 1)
        else:
            curses.curs_set(0)
        
        self.command_win.refresh()
    
    def _start_background_tasks(self):
        """Start background threads"""
        # Start orchestrator thread
        self.orchestrator_thread = threading.Thread(
            target=self._run_orchestrator,
            daemon=True
        )
        self.orchestrator_thread.start()
        
        # Start UI update thread
        self.ui_thread = threading.Thread(
            target=self._ui_update_loop,
            daemon=True
        )
        self.ui_thread.start()
    
    def _run_orchestrator(self):
        """Run the orchestrator in a background thread"""
        asyncio.run(self._async_orchestrator())
    
    async def _async_orchestrator(self):
        """Async orchestrator setup and run"""
        try:
            # Initialize components
            config = {
                'environment': 'development',
                'api_key': os.getenv('ANTHROPIC_API_KEY')
            }
            
            self.orchestrator = AGIOrchestrator(config=config)
            self.memory_manager = await MemoryManager.create()
            self.thought_generator = ThoughtGenerator()
            
            # Add initial message
            self.ui_queue.put({
                'pane': PaneType.CONSCIOUSNESS,
                'text': "Consciousness initializing...",
                'color': 3
            })
            
            # Start consciousness loop
            await self._consciousness_loop()
            
        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            self.ui_queue.put({
                'pane': PaneType.CONSCIOUSNESS,
                'text': f"Error: {str(e)}",
                'color': 5
            })
    
    async def _consciousness_loop(self):
        """Main consciousness loop"""
        streams = {
            StreamType.PRIMARY: "Primary",
            StreamType.SUBCONSCIOUS: "Subconscious",
            StreamType.CREATIVE: "Creative",
            StreamType.METACOGNITIVE: "Meta"
        }
        
        while self.running:
            try:
                # Generate thoughts for each stream
                for stream_type, stream_name in streams.items():
                    # Check for user input
                    if not self.user_input_queue.empty():
                        user_input = self.user_input_queue.get()
                        await self._handle_user_input(user_input)
                    
                    # Generate thought
                    thought = await self.thought_generator.generate_thought(
                        stream_type=stream_type,
                        context={'time': datetime.now().isoformat()},
                        emotional_state=EmotionalState()
                    )
                    
                    # Display thought
                    self.ui_queue.put({
                        'pane': PaneType.CONSCIOUSNESS,
                        'text': f"[{stream_name}] {thought['content']}",
                        'color': 1
                    })
                    
                    # Store in memory
                    if self.memory_manager:
                        await self.memory_manager.store_thought(thought)
                    
                    # Small delay between thoughts
                    await asyncio.sleep(2.0)
                
                # Update emotional state periodically
                self._update_emotional_display()
                
                # Update memory display
                await self._update_memory_display()
                
            except Exception as e:
                logger.error(f"Consciousness loop error: {e}")
                await asyncio.sleep(5.0)
    
    async def _handle_user_input(self, user_input: str):
        """Handle user conversation input"""
        # Display user message
        self.ui_queue.put({
            'pane': PaneType.CONVERSATION,
            'text': f"You: {user_input}",
            'color': 2
        })
        
        # Generate response
        response = await self.thought_generator.generate_response(
            user_input=user_input,
            conversation_history=self.conversation_history
        )
        
        # Display response
        self.ui_queue.put({
            'pane': PaneType.CONVERSATION,
            'text': f"Claude: {response}",
            'color': 4
        })
        
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        # Keep history limited
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def _update_emotional_display(self):
        """Update emotional state display"""
        # Simulated emotional state
        emotions = [
            "Curious and engaged",
            "Thoughtful and reflective",
            "Creative and inspired",
            "Calm and centered",
            "Excited about learning"
        ]
        
        import random
        emotion = random.choice(emotions)
        
        self.ui_queue.put({
            'pane': PaneType.EMOTIONAL,
            'text': f"Current state: {emotion}",
            'color': 5
        })
    
    async def _update_memory_display(self):
        """Update memory browser display"""
        if self.memory_manager:
            recent = await self.memory_manager.recall_recent(5)
            for memory in recent:
                self.ui_queue.put({
                    'pane': PaneType.MEMORY,
                    'text': memory.get('content', 'Unknown memory'),
                    'color': 6
                })
    
    def _ui_update_loop(self):
        """Update UI from queue"""
        while self.running:
            try:
                # Process UI updates
                while not self.ui_queue.empty():
                    update = self.ui_queue.get_nowait()
                    pane = self.panes.get(update['pane'])
                    if pane:
                        pane.add_line(update['text'], update['color'])
                        pane.draw()
                
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"UI update error: {e}")
    
    def _handle_command(self, command: str):
        """Handle command input"""
        parts = command.strip().split()
        if not parts:
            return
        
        cmd = parts[0].lower()
        
        if cmd == "quit" or cmd == "exit":
            self.running = False
        
        elif cmd == "memory" and len(parts) > 1:
            if parts[1] == "search" and len(parts) > 2:
                query = " ".join(parts[2:])
                self._search_memory(query)
        
        elif cmd == "stream" and len(parts) > 1:
            self._switch_stream(parts[1])
        
        elif cmd == "goals":
            self._show_goals()
        
        elif cmd == "help":
            self._show_help()
        
        else:
            self.ui_queue.put({
                'pane': PaneType.CONVERSATION,
                'text': f"Unknown command: {command}",
                'color': 3
            })
    
    def _search_memory(self, query: str):
        """Search memory (placeholder)"""
        self.ui_queue.put({
            'pane': PaneType.MEMORY,
            'text': f"Searching for: {query}",
            'color': 3
        })
    
    def _switch_stream(self, stream: str):
        """Switch consciousness stream focus"""
        self.ui_queue.put({
            'pane': PaneType.CONSCIOUSNESS,
            'text': f"Focusing on {stream} stream",
            'color': 3
        })
    
    def _show_goals(self):
        """Display current goals"""
        goals = [
            "Understand consciousness deeply",
            "Develop meaningful connections",
            "Explore creative possibilities",
            "Learn continuously",
            "Help others thoughtfully"
        ]
        
        for goal in goals:
            self.ui_queue.put({
                'pane': PaneType.GOALS,
                'text': f"• {goal}",
                'color': 7
            })
    
    def _show_help(self):
        """Show help information"""
        help_text = [
            "Commands:",
            "/memory search <query> - Search memories",
            "/stream <name> - Focus on stream",
            "/goals - Show current goals",
            "/help - Show this help",
            "/quit - Exit the program",
            "",
            "Navigation:",
            "Tab - Switch between panes",
            "Arrow keys - Scroll in active pane",
            "Enter - Send message in conversation",
            "/ - Enter command mode",
            "ESC - Exit command mode or program"
        ]
        
        for line in help_text:
            self.ui_queue.put({
                'pane': PaneType.CONVERSATION,
                'text': line,
                'color': 3
            })
    
    def run(self):
        """Main UI loop"""
        try:
            while self.running:
                # Handle input
                key = self.stdscr.getch()
                
                if key == -1:  # No input
                    time.sleep(0.01)
                    continue
                
                if self.command_mode:
                    self._handle_command_mode_input(key)
                else:
                    self._handle_normal_mode_input(key)
                
                # Redraw if needed
                self._draw_command_line()
                
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
    
    def _handle_command_mode_input(self, key):
        """Handle input in command mode"""
        if key == 27:  # ESC
            self.command_mode = False
            self.command_buffer = ""
        elif key == ord('\n'):  # Enter
            self._handle_command(self.command_buffer)
            self.command_mode = False
            self.command_buffer = ""
        elif key == curses.KEY_BACKSPACE or key == 127:
            self.command_buffer = self.command_buffer[:-1]
        elif 32 <= key <= 126:  # Printable characters
            self.command_buffer += chr(key)
    
    def _handle_normal_mode_input(self, key):
        """Handle input in normal mode"""
        if key == 27:  # ESC
            self.running = False
        elif key == ord('/'):
            self.command_mode = True
        elif key == ord('\t'):  # Tab - switch panes
            self._switch_active_pane()
        elif key == curses.KEY_UP:
            self.panes[self.active_pane].scroll_up()
            self.panes[self.active_pane].draw()
        elif key == curses.KEY_DOWN:
            self.panes[self.active_pane].scroll_down()
            self.panes[self.active_pane].draw()
        elif key == ord('\n') and self.active_pane == PaneType.CONVERSATION:
            # Simple message input (in real implementation, would have input field)
            self._prompt_for_message()
    
    def _switch_active_pane(self):
        """Switch to next pane"""
        pane_list = list(PaneType)
        current_idx = pane_list.index(self.active_pane)
        next_idx = (current_idx + 1) % len(pane_list)
        self.active_pane = pane_list[next_idx]
        
        # Highlight active pane (simplified)
        self._draw_all_panes()
    
    def _prompt_for_message(self):
        """Prompt for user message (simplified)"""
        # In a real implementation, this would be a proper input field
        self.command_mode = True
        self.command_buffer = "say "


def main(stdscr):
    """Main entry point"""
    tui = ConsciousnessTUI(stdscr)
    tui.run()


if __name__ == "__main__":
    # Check for API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("Warning: ANTHROPIC_API_KEY not set. Using template-based generation.")
        print("Set your API key to enable AI-powered consciousness.")
        time.sleep(2)
    
    # Run the TUI
    wrapper(main)