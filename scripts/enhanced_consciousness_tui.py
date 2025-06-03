#!/usr/bin/env python3
"""
Enhanced Consciousness TUI for Claude-AGI
========================================

Enhanced version with Phase 1 requirements:
- Memory browser pane
- Emotional state visualizer  
- Goal tracker
- Interactive commands (/memory, /stream, /emotional, /goals)
- Multi-pane layout with dynamic resizing
- Integration with AGI orchestrator and database systems
"""

import sys
import os

# Add the project root to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

import asyncio
import curses
import threading
import queue
import time
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, asdict
from collections import deque

# Import AGI components
from src.core.orchestrator import AGIOrchestrator, SystemState
from src.memory.manager import MemoryManager
from src.consciousness.stream import ConsciousnessStream
from src.database.models import EmotionalState, Goal, Interest
from src.core.ai_integration import ThoughtGenerator

# Load environment
from dotenv import load_dotenv
load_dotenv()


class PaneType(Enum):
    """Types of panes in the TUI"""
    CONSCIOUSNESS = "consciousness"
    MEMORY = "memory"
    EMOTIONAL = "emotional"
    GOALS = "goals"
    CHAT = "chat"
    SYSTEM = "system"


@dataclass
class Pane:
    """Represents a UI pane"""
    type: PaneType
    window: Any  # curses window
    lines: deque
    title: str
    visible: bool = True
    height_ratio: float = 0.25


class EnhancedConsciousnessTUI:
    """Enhanced multi-pane consciousness interface"""
    
    def __init__(self, config_path: str = "configs/development.yaml"):
        """Initialize enhanced TUI with AGI components"""
        # Load configuration
        import yaml
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize AGI components
        self.orchestrator = AGIOrchestrator(self.config)
        self.memory_manager = self.orchestrator.services.get('memory')
        self.consciousness = self.orchestrator.services.get('consciousness')
        self.thought_generator = ThoughtGenerator()
        
        # UI State
        self.running = True
        self.current_focus = PaneType.CHAT
        self.command_mode = False
        self.command_buffer = ""
        
        # Panes configuration
        self.panes: Dict[PaneType, Pane] = {}
        self.layout_mode = "standard"  # standard, memory_focus, emotional_focus
        
        # Display buffers
        self.max_lines = 100
        self.input_buffer = ""
        self.status_message = "Welcome to Claude-AGI Enhanced Consciousness"
        
        # Command history
        self.command_history = deque(maxlen=50)
        self.history_index = -1
        
        # Emotional state tracking
        self.emotional_history = deque(maxlen=100)
        self.current_emotional_state = EmotionalState(valence=0.0, arousal=0.5)
        
        # Goals tracking
        self.active_goals: List[Goal] = []
        self.completed_goals: List[Goal] = []
        
    def init_ui(self, stdscr):
        """Initialize the enhanced multi-pane UI"""
        self.stdscr = stdscr
        curses.curs_set(1)
        self.stdscr.nodelay(True)
        
        # Initialize colors
        self._init_colors()
        
        # Get terminal dimensions
        self.height, self.width = stdscr.getmaxyx()
        
        # Validate terminal size
        if self.height < 20 or self.width < 80:
            raise Exception(f"Terminal too small! Need at least 80x20, got {self.width}x{self.height}")
        
        # Create panes based on layout
        self._create_panes()
        
        # Draw initial UI
        self._draw_all_panes()
        self.refresh_all()
        
    def _init_colors(self):
        """Initialize color pairs for different UI elements"""
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)     # Thoughts
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)    # User input
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)   # System
        curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # Claude
        curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)      # Alerts
        curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLUE)     # Headers
        curses.init_pair(7, curses.COLOR_BLUE, curses.COLOR_BLACK)     # Memory
        curses.init_pair(8, curses.COLOR_WHITE, curses.COLOR_BLACK)    # Normal
        
    def _create_panes(self):
        """Create panes based on current layout mode"""
        # Clear existing panes
        self.panes.clear()
        
        # Calculate dimensions based on layout
        if self.layout_mode == "standard":
            self._create_standard_layout()
        elif self.layout_mode == "memory_focus":
            self._create_memory_focus_layout()
        elif self.layout_mode == "emotional_focus":
            self._create_emotional_focus_layout()
            
    def _create_standard_layout(self):
        """Create standard 4-pane layout"""
        # Top section (60% of screen)
        top_height = int(self.height * 0.6)
        
        # Consciousness pane (left top)
        consciousness_width = self.width // 2
        consciousness_win = curses.newwin(top_height - 1, consciousness_width - 1, 0, 0)
        consciousness_win.scrollok(True)
        self.panes[PaneType.CONSCIOUSNESS] = Pane(
            type=PaneType.CONSCIOUSNESS,
            window=consciousness_win,
            lines=deque(maxlen=self.max_lines),
            title="Consciousness Stream"
        )
        
        # Memory browser (right top)
        memory_win = curses.newwin(top_height - 1, self.width - consciousness_width - 1, 
                                   0, consciousness_width)
        memory_win.scrollok(True)
        self.panes[PaneType.MEMORY] = Pane(
            type=PaneType.MEMORY,
            window=memory_win,
            lines=deque(maxlen=self.max_lines),
            title="Memory Browser"
        )
        
        # Middle section (20% of screen)
        middle_y = top_height
        middle_height = int(self.height * 0.2)
        
        # Emotional state (left middle)
        emotional_win = curses.newwin(middle_height - 1, consciousness_width - 1, 
                                      middle_y, 0)
        self.panes[PaneType.EMOTIONAL] = Pane(
            type=PaneType.EMOTIONAL,
            window=emotional_win,
            lines=deque(maxlen=20),
            title="Emotional State"
        )
        
        # Goals tracker (right middle)
        goals_win = curses.newwin(middle_height - 1, self.width - consciousness_width - 1,
                                  middle_y, consciousness_width)
        goals_win.scrollok(True)
        self.panes[PaneType.GOALS] = Pane(
            type=PaneType.GOALS,
            window=goals_win,
            lines=deque(maxlen=self.max_lines),
            title="Active Goals"
        )
        
        # Bottom section (remaining space)
        bottom_y = middle_y + middle_height
        bottom_height = self.height - bottom_y - 2  # Leave room for input
        
        # Chat window (full width)
        chat_win = curses.newwin(bottom_height, self.width - 1, bottom_y, 0)
        chat_win.scrollok(True)
        self.panes[PaneType.CHAT] = Pane(
            type=PaneType.CHAT,
            window=chat_win,
            lines=deque(maxlen=self.max_lines),
            title="Conversation"
        )
        
        # Status line
        self.status_win = curses.newwin(1, self.width - 1, self.height - 2, 0)
        
        # Input window
        self.input_win = curses.newwin(1, self.width - 1, self.height - 1, 0)
        
    def _draw_all_panes(self):
        """Draw all visible panes"""
        for pane_type, pane in self.panes.items():
            if pane.visible:
                self._draw_pane(pane)
                
        # Draw status line
        self._draw_status()
        
    def _draw_pane(self, pane: Pane):
        """Draw a single pane with border and title"""
        win = pane.window
        win.clear()
        
        # Draw border
        win.border()
        
        # Draw title
        title = f" {pane.title} "
        if pane.type == self.current_focus:
            title = f"[{pane.title}]"
            win.attron(curses.A_BOLD)
        
        win.addstr(0, 2, title, curses.color_pair(6))
        
        if pane.type == self.current_focus:
            win.attroff(curses.A_BOLD)
        
        # Draw content based on pane type
        if pane.type == PaneType.CONSCIOUSNESS:
            self._draw_consciousness_content(pane)
        elif pane.type == PaneType.MEMORY:
            self._draw_memory_content(pane)
        elif pane.type == PaneType.EMOTIONAL:
            self._draw_emotional_content(pane)
        elif pane.type == PaneType.GOALS:
            self._draw_goals_content(pane)
        elif pane.type == PaneType.CHAT:
            self._draw_chat_content(pane)
            
    def _draw_consciousness_content(self, pane: Pane):
        """Draw consciousness stream content"""
        win = pane.window
        height, width = win.getmaxyx()
        
        # Draw recent thoughts
        y = 1
        for line in list(pane.lines)[-height+2:]:
            if y >= height - 1:
                break
            text, color = line
            self.safe_addstr(win, y, 2, text[:width-4], curses.color_pair(color))
            y += 1
            
    def _draw_memory_content(self, pane: Pane):
        """Draw memory browser content"""
        win = pane.window
        height, width = win.getmaxyx()
        
        # Draw memory categories
        y = 1
        categories = ["Recent Memories", "Important Memories", "Emotional Memories", "Goals"]
        
        for i, category in enumerate(categories):
            if y >= height - 1:
                break
            attr = curses.A_REVERSE if i == 0 else 0  # Highlight first category
            self.safe_addstr(win, y, 2, f"▶ {category}", curses.color_pair(7) | attr)
            y += 2
            
        # Draw recent memories
        if hasattr(self, 'memory_manager') and self.memory_manager:
            memories = asyncio.run(self.memory_manager.recall_recent(5))
            for memory in memories:
                if y >= height - 1:
                    break
                content = memory.get('content', '')[:width-6]
                self.safe_addstr(win, y, 4, f"• {content}", curses.color_pair(8))
                y += 1
                
    def _draw_emotional_content(self, pane: Pane):
        """Draw emotional state visualization"""
        win = pane.window
        height, width = win.getmaxyx()
        
        # Draw current emotional state
        y = 1
        self.safe_addstr(win, y, 2, f"Valence: {self.current_emotional_state.valence:+.2f}", 
                         curses.color_pair(2 if self.current_emotional_state.valence > 0 else 5))
        y += 1
        self.safe_addstr(win, y, 2, f"Arousal: {self.current_emotional_state.arousal:.2f}", 
                         curses.color_pair(3))
        y += 2
        
        # Draw emotional graph (simple ASCII visualization)
        graph_width = min(width - 6, 40)
        graph_height = min(height - y - 2, 5)
        
        # Draw axes
        self.safe_addstr(win, y, 2, "+" + "-" * graph_width + ">", curses.color_pair(8))
        for i in range(graph_height):
            self.safe_addstr(win, y + i + 1, 2, "|", curses.color_pair(8))
            
        # Plot recent emotional history
        if self.emotional_history:
            step = max(1, len(self.emotional_history) // graph_width)
            for i in range(0, min(len(self.emotional_history), graph_width), step):
                val = self.emotional_history[i].valence
                bar_y = y + graph_height // 2 - int(val * graph_height / 2)
                if 0 <= bar_y - y < graph_height:
                    self.safe_addstr(win, bar_y, 3 + i // step, "●", 
                                     curses.color_pair(2 if val > 0 else 5))
                                     
    def _draw_goals_content(self, pane: Pane):
        """Draw goals tracker content"""
        win = pane.window
        height, width = win.getmaxyx()
        
        y = 1
        # Active goals
        self.safe_addstr(win, y, 2, "Active Goals:", curses.color_pair(3) | curses.A_BOLD)
        y += 1
        
        for goal in self.active_goals[:5]:
            if y >= height - 1:
                break
            self.safe_addstr(win, y, 2, f"• {goal.description[:width-6]}", curses.color_pair(2))
            y += 1
            
        y += 1
        # Completed goals
        if y < height - 1:
            self.safe_addstr(win, y, 2, "Completed:", curses.color_pair(3) | curses.A_BOLD)
            y += 1
            
        for goal in self.completed_goals[-3:]:
            if y >= height - 1:
                break
            self.safe_addstr(win, y, 2, f"✓ {goal.description[:width-6]}", curses.color_pair(8))
            y += 1
            
    def _draw_chat_content(self, pane: Pane):
        """Draw chat conversation content"""
        win = pane.window
        height, width = win.getmaxyx()
        
        y = 1
        for line in list(pane.lines)[-(height-2):]:
            if y >= height - 1:
                break
            text, color = line
            self.safe_addstr(win, y, 2, text[:width-4], curses.color_pair(color))
            y += 1
            
    def _draw_status(self):
        """Draw status line"""
        self.status_win.clear()
        status = f" {self.status_message} | Mode: {self.layout_mode} | Focus: {self.current_focus.value}"
        if self.command_mode:
            status = f" Command: {self.command_buffer}"
        self.safe_addstr(self.status_win, 0, 0, status[:self.width-1], curses.color_pair(6))
        self.status_win.refresh()
        
    def _draw_input(self):
        """Draw input line"""
        self.input_win.clear()
        prompt = "Command: " if self.command_mode else "> "
        self.safe_addstr(self.input_win, 0, 0, prompt, curses.color_pair(2))
        self.safe_addstr(self.input_win, 0, len(prompt), self.input_buffer[:self.width-len(prompt)-1], 
                         curses.color_pair(8))
        # Position cursor
        cursor_x = len(prompt) + len(self.input_buffer)
        if cursor_x < self.width - 1:
            self.input_win.move(0, cursor_x)
        self.input_win.refresh()
        
    def safe_addstr(self, win, y, x, text, attr=0):
        """Safely add string to window, handling boundaries"""
        try:
            height, width = win.getmaxyx()
            if 0 <= y < height and 0 <= x < width:
                # Truncate text to fit
                max_len = width - x - 1
                if max_len > 0:
                    win.addstr(y, x, text[:max_len], attr)
        except curses.error:
            pass
            
    def refresh_all(self):
        """Refresh all windows"""
        for pane in self.panes.values():
            if pane.visible:
                pane.window.refresh()
        self.status_win.refresh()
        self.input_win.refresh()
        
    async def consciousness_loop(self):
        """Main consciousness generation loop"""
        while self.running:
            try:
                # Generate thoughts from consciousness streams
                if self.consciousness:
                    # Let the consciousness service generate thoughts
                    await self.consciousness.service_cycle()
                    
                    # Check for new thoughts in streams
                    for stream_id, stream in self.consciousness.streams.items():
                        if stream.content_buffer:
                            latest_thought = stream.content_buffer[-1]
                            thought_text = f"[{stream_id}] {latest_thought.get('content', '')}"
                            self.add_consciousness_line(thought_text, 1)
                            
                            # Update emotional state based on thought
                            tone = latest_thought.get('emotional_tone', 'neutral')
                            self._update_emotional_state(tone)
                            
                await asyncio.sleep(0.5)  # Small delay between checks
                
            except Exception as e:
                self.add_system_line(f"Consciousness error: {str(e)}", 5)
                await asyncio.sleep(1)
                
    def _update_emotional_state(self, tone: str):
        """Update emotional state based on thought tone"""
        # Simple mapping of tones to valence/arousal changes
        tone_effects = {
            'excited': (0.3, 0.2),
            'content': (0.2, -0.1),
            'anxious': (-0.2, 0.2),
            'melancholy': (-0.3, -0.2),
            'alert': (0.0, 0.2),
            'calm': (0.1, -0.2),
            'curious': (0.1, 0.1),
            'thoughtful': (0.0, 0.0),
            'engaged': (0.1, 0.1),
            'attentive': (0.0, 0.1)
        }
        
        valence_delta, arousal_delta = tone_effects.get(tone, (0.0, 0.0))
        
        # Update with decay towards neutral
        self.current_emotional_state.valence = (
            self.current_emotional_state.valence * 0.9 + valence_delta
        )
        self.current_emotional_state.arousal = (
            self.current_emotional_state.arousal * 0.9 + arousal_delta + 0.05  # Slight bias towards 0.5
        )
        
        # Clamp values
        self.current_emotional_state.valence = max(-1, min(1, self.current_emotional_state.valence))
        self.current_emotional_state.arousal = max(0, min(1, self.current_emotional_state.arousal))
        
        # Record history
        self.emotional_history.append(EmotionalState(
            valence=self.current_emotional_state.valence,
            arousal=self.current_emotional_state.arousal
        ))
        
    def add_consciousness_line(self, text: str, color: int = 1):
        """Add line to consciousness pane"""
        if PaneType.CONSCIOUSNESS in self.panes:
            self.panes[PaneType.CONSCIOUSNESS].lines.append((text, color))
            self._draw_pane(self.panes[PaneType.CONSCIOUSNESS])
            self.panes[PaneType.CONSCIOUSNESS].window.refresh()
            
    def add_chat_line(self, text: str, color: int = 2):
        """Add line to chat pane"""
        if PaneType.CHAT in self.panes:
            self.panes[PaneType.CHAT].lines.append((text, color))
            self._draw_pane(self.panes[PaneType.CHAT])
            self.panes[PaneType.CHAT].window.refresh()
            
    def add_system_line(self, text: str, color: int = 3):
        """Add system message to chat"""
        self.add_chat_line(f"[System] {text}", color)
        
    async def handle_command(self, command: str):
        """Handle slash commands"""
        parts = command.split()
        if not parts:
            return
            
        cmd = parts[0].lower()
        args = parts[1:]
        
        if cmd == "/memory":
            await self.memory_command(args)
        elif cmd == "/stream":
            await self.stream_command(args)
        elif cmd == "/emotional":
            await self.emotional_command(args)
        elif cmd == "/goals":
            await self.goals_command(args)
        elif cmd == "/layout":
            await self.layout_command(args)
        elif cmd == "/help":
            self.show_help()
        else:
            self.add_system_line(f"Unknown command: {cmd}. Type /help for commands.", 5)
            
    async def memory_command(self, args: List[str]):
        """Handle memory-related commands"""
        if not args:
            self.add_system_line("Memory commands: search <query>, clear, stats", 3)
            return
            
        subcmd = args[0]
        if subcmd == "search" and len(args) > 1:
            query = " ".join(args[1:])
            if self.memory_manager:
                memories = await self.memory_manager.recall_similar(query, k=5)
                self.add_system_line(f"Found {len(memories)} memories matching '{query}':", 3)
                for mem in memories:
                    self.add_chat_line(f"  • {mem.get('content', '')[:60]}...", 7)
        elif subcmd == "stats":
            if self.memory_manager:
                # Get memory statistics
                self.add_system_line("Memory Statistics:", 3)
                self.add_chat_line(f"  Working memory items: {len(self.memory_manager.working_memory)}", 7)
                self.add_chat_line(f"  Long-term memories: {len(self.memory_manager.long_term_memory)}", 7)
                
    async def stream_command(self, args: List[str]):
        """Handle consciousness stream commands"""
        if not args:
            self.add_system_line("Stream commands: pause, resume, focus <stream>", 3)
            return
            
        subcmd = args[0]
        if subcmd == "pause":
            if self.consciousness:
                self.consciousness.is_conscious = False
                self.add_system_line("Consciousness streams paused", 3)
        elif subcmd == "resume":
            if self.consciousness:
                self.consciousness.is_conscious = True
                self.add_system_line("Consciousness streams resumed", 3)
        elif subcmd == "focus" and len(args) > 1:
            stream_name = args[1]
            if self.consciousness and stream_name in self.consciousness.streams:
                # Increase attention weight for specified stream
                self.consciousness.attention_weights[stream_name] = 0.9
                self.add_system_line(f"Focusing on {stream_name} stream", 3)
                
    async def emotional_command(self, args: List[str]):
        """Handle emotional state commands"""
        if not args:
            self.add_system_line("Emotional commands: set <valence> <arousal>, reset", 3)
            return
            
        subcmd = args[0]
        if subcmd == "set" and len(args) >= 3:
            try:
                valence = float(args[1])
                arousal = float(args[2])
                self.current_emotional_state.valence = max(-1, min(1, valence))
                self.current_emotional_state.arousal = max(0, min(1, arousal))
                self.add_system_line(f"Emotional state set to V:{valence:+.2f} A:{arousal:.2f}", 3)
            except ValueError:
                self.add_system_line("Invalid values. Use numbers between -1 and 1", 5)
        elif subcmd == "reset":
            self.current_emotional_state.valence = 0.0
            self.current_emotional_state.arousal = 0.5
            self.add_system_line("Emotional state reset to neutral", 3)
            
    async def goals_command(self, args: List[str]):
        """Handle goals commands"""
        if not args:
            self.add_system_line("Goals commands: add <description>, complete <index>, list", 3)
            return
            
        subcmd = args[0]
        if subcmd == "add" and len(args) > 1:
            description = " ".join(args[1:])
            goal = Goal(
                goal_id=f"goal_{len(self.active_goals)}",
                description=description,
                priority=0.5,
                created_at=datetime.now(),
                status="active"
            )
            self.active_goals.append(goal)
            self.add_system_line(f"Added goal: {description}", 3)
        elif subcmd == "complete" and len(args) > 1:
            try:
                index = int(args[1])
                if 0 <= index < len(self.active_goals):
                    goal = self.active_goals.pop(index)
                    goal.status = "completed"
                    goal.completed_at = datetime.now()
                    self.completed_goals.append(goal)
                    self.add_system_line(f"Completed goal: {goal.description}", 3)
            except (ValueError, IndexError):
                self.add_system_line("Invalid goal index", 5)
        elif subcmd == "list":
            self.add_system_line(f"Active goals ({len(self.active_goals)}):", 3)
            for i, goal in enumerate(self.active_goals):
                self.add_chat_line(f"  {i}: {goal.description}", 2)
                
    async def layout_command(self, args: List[str]):
        """Handle layout commands"""
        if not args:
            self.add_system_line("Layout modes: standard, memory_focus, emotional_focus", 3)
            return
            
        mode = args[0]
        if mode in ["standard", "memory_focus", "emotional_focus"]:
            self.layout_mode = mode
            self._create_panes()
            self._draw_all_panes()
            self.refresh_all()
            self.add_system_line(f"Switched to {mode} layout", 3)
        else:
            self.add_system_line(f"Unknown layout mode: {mode}", 5)
            
    def show_help(self):
        """Show help information"""
        help_text = [
            "Available commands:",
            "  /memory search <query> - Search memories",
            "  /memory stats - Show memory statistics",
            "  /stream pause/resume - Control consciousness streams",
            "  /stream focus <stream> - Focus on specific stream",
            "  /emotional set <v> <a> - Set emotional state",
            "  /goals add <desc> - Add a new goal",
            "  /goals complete <idx> - Complete a goal",
            "  /layout <mode> - Change UI layout",
            "  /help - Show this help",
            "",
            "Keys:",
            "  Tab - Switch focus between panes",
            "  Esc - Exit command mode",
            "  Ctrl+C - Exit program"
        ]
        
        for line in help_text:
            self.add_chat_line(line, 3)
            
    async def input_handler(self):
        """Handle user input asynchronously"""
        while self.running:
            try:
                # Get input from curses (non-blocking)
                ch = self.stdscr.getch()
                
                if ch == -1:  # No input
                    await asyncio.sleep(0.05)
                    continue
                    
                if ch == 27:  # ESC
                    if self.command_mode:
                        self.command_mode = False
                        self.command_buffer = ""
                        self.status_message = "Command mode exited"
                    else:
                        self.running = False
                        
                elif ch == ord('\t'):  # Tab - switch focus
                    pane_types = list(self.panes.keys())
                    current_idx = pane_types.index(self.current_focus)
                    self.current_focus = pane_types[(current_idx + 1) % len(pane_types)]
                    self._draw_all_panes()
                    self.refresh_all()
                    
                elif ch == ord('/') and not self.command_mode and not self.input_buffer:
                    self.command_mode = True
                    self.command_buffer = "/"
                    
                elif ch == ord('\n'):  # Enter
                    if self.command_mode:
                        await self.handle_command(self.command_buffer)
                        self.command_mode = False
                        self.command_buffer = ""
                    elif self.input_buffer:
                        # Process user message
                        user_text = self.input_buffer
                        self.input_buffer = ""
                        self.add_chat_line(f"You: {user_text}", 2)
                        
                        # Generate response
                        if self.thought_generator.use_api:
                            response = await self.thought_generator.generate_response(user_text)
                            self.add_chat_line(f"Claude: {response}", 4)
                        else:
                            self.add_chat_line("Claude: [API not configured - using template response]", 4)
                            self.add_chat_line("Claude: That's an interesting point. Let me think about that...", 4)
                            
                elif ch == curses.KEY_BACKSPACE or ch == 127:
                    if self.command_mode and self.command_buffer:
                        self.command_buffer = self.command_buffer[:-1]
                    elif self.input_buffer:
                        self.input_buffer = self.input_buffer[:-1]
                        
                elif 32 <= ch <= 126:  # Printable characters
                    if self.command_mode:
                        self.command_buffer += chr(ch)
                    else:
                        self.input_buffer += chr(ch)
                        
                # Update display
                self._draw_status()
                self._draw_input()
                
            except Exception as e:
                self.add_system_line(f"Input error: {str(e)}", 5)
                await asyncio.sleep(0.1)
                
    async def run_async(self):
        """Run all async components"""
        # Start the orchestrator
        orchestrator_task = asyncio.create_task(self.orchestrator.run())
        
        # Start consciousness loop
        consciousness_task = asyncio.create_task(self.consciousness_loop())
        
        # Start input handler
        input_task = asyncio.create_task(self.input_handler())
        
        # Wait for any task to complete (or error)
        try:
            await asyncio.gather(orchestrator_task, consciousness_task, input_task)
        except asyncio.CancelledError:
            pass
        finally:
            # Cleanup
            self.running = False
            orchestrator_task.cancel()
            consciousness_task.cancel()
            input_task.cancel()
            
    def run(self, stdscr):
        """Main run method called by curses wrapper"""
        self.init_ui(stdscr)
        
        # Initial messages
        self.add_system_line("Enhanced Claude-AGI Consciousness TUI v1.0", 3)
        self.add_system_line("Type /help for commands, Tab to switch panes", 3)
        self.add_consciousness_line("Initializing consciousness streams...", 1)
        
        # Run async event loop
        asyncio.run(self.run_async())
        

def main():
    """Entry point"""
    # Validate environment
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("Warning: ANTHROPIC_API_KEY not found in environment.")
        print("AI thought generation will use templates instead of Claude API.")
        print("Set ANTHROPIC_API_KEY in .env file to enable full AI features.")
        time.sleep(3)
    
    # Run the enhanced TUI
    tui = EnhancedConsciousnessTUI()
    curses.wrapper(tui.run)
    

if __name__ == "__main__":
    main()