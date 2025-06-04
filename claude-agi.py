#!/usr/bin/env python3
"""
Claude-AGI: Advanced General Intelligence System
===============================================

Main entry point for the Claude-AGI consciousness system.
This script provides an interactive terminal interface for:
- Multi-stream consciousness processing
- Persistent memory management
- Emotional state tracking
- Goal-oriented behavior
- Real-time user interaction

Usage:
    python claude-agi.py [--config CONFIG_PATH]
    
Options:
    --config    Path to configuration file (default: configs/development.yaml)
    --help      Show this help message
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

import asyncio
import curses
import threading
import queue
import time
import json
import argparse
import textwrap
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, asdict
from collections import deque

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import AGI components
from src.core.orchestrator import AGIOrchestrator, SystemState, Message
from src.memory.manager import MemoryManager
from src.consciousness.stream import ConsciousnessStream
from src.database.models import EmotionalState, Goal, Interest, StreamType
from src.core.ai_integration import ThoughtGenerator
from src.safety.core_safety import SafetyFramework

# Load environment
from dotenv import load_dotenv
load_dotenv()

import yaml
import logging

# Configure logging - disable console output when using TUI
# StreamHandler interferes with curses
# Ensure logs directory exists
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'claude-agi.log')
        # Removed StreamHandler to prevent curses interference
    ]
)
logger = logging.getLogger(__name__)


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


class ClaudeAGI:
    """
    Main Claude-AGI Interface
    
    Integrates all AGI components into a unified consciousness system
    with real-time interaction capabilities.
    """
    
    def __init__(self, config_path: str = "configs/development.yaml"):
        """Initialize Claude-AGI with configuration"""
        logger.info(f"Initializing Claude-AGI with config: {config_path}")
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize AGI components
        self.orchestrator = AGIOrchestrator(self.config)
        self.memory_manager = None  # Will be set after initialization
        self.consciousness = None  # Will be set after initialization
        self.safety = None  # Will be set after initialization
        self.thought_generator = ThoughtGenerator()
        self.thought_queue = asyncio.Queue()  # Queue for receiving thoughts
        self.total_thoughts = 0
        
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
        self.status_message = "Claude-AGI System Initialized"
        
        # Command history
        self.command_history = deque(maxlen=50)
        self.history_index = -1
        
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
        
        # Update flags
        self.consciousness_needs_update = False
        self.chat_needs_update = False
        
        logger.info("Claude-AGI initialization complete")
        
    def init_ui(self, stdscr):
        """Initialize the multi-pane UI"""
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
        if curses.has_colors():
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
        consciousness_win.idlok(True)  # Enable line insertion/deletion
        consciousness_win.keypad(True)  # Enable keypad for scrolling
        self.panes[PaneType.CONSCIOUSNESS] = Pane(
            type=PaneType.CONSCIOUSNESS,
            window=consciousness_win,
            lines=deque(maxlen=self.max_lines * 3),  # More history
            title="Consciousness Stream"
        )
        
        # Initialize scroll positions
        if not hasattr(self, 'scroll_positions'):
            self.scroll_positions = {}
        
        # Memory browser (right top)
        memory_width = self.width - consciousness_width
        memory_win = curses.newwin(top_height - 1, memory_width, 
                                   0, consciousness_width)
        memory_win.scrollok(True)
        memory_win.idlok(True)
        memory_win.keypad(True)
        self.panes[PaneType.MEMORY] = Pane(
            type=PaneType.MEMORY,
            window=memory_win,
            lines=deque(maxlen=self.max_lines * 2),  # More memory history
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
        goals_win = curses.newwin(middle_height - 1, memory_width,
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
        chat_win.idlok(True)
        chat_win.keypad(True)
        self.panes[PaneType.CHAT] = Pane(
            type=PaneType.CHAT,
            window=chat_win,
            lines=deque(maxlen=self.max_lines * 2),  # More chat history
            title="Conversation"
        )
        
        # Status line
        self.status_win = curses.newwin(1, self.width - 1, self.height - 2, 0)
        
        # Input window
        self.input_win = curses.newwin(1, self.width - 1, self.height - 1, 0)
        
    def _create_memory_focus_layout(self):
        """Create layout with larger memory pane"""
        # Memory takes 70% of top area
        memory_height = int(self.height * 0.7)
        
        # Large memory pane
        memory_win = curses.newwin(memory_height - 1, self.width - 1, 0, 0)
        memory_win.scrollok(True)
        self.panes[PaneType.MEMORY] = Pane(
            type=PaneType.MEMORY,
            window=memory_win,
            lines=deque(maxlen=self.max_lines * 2),
            title="Memory Browser (Focused)"
        )
        
        # Remaining panes in bottom 30%
        bottom_y = memory_height
        remaining_height = self.height - bottom_y - 2
        
        # Small consciousness stream
        consciousness_height = remaining_height // 2
        consciousness_win = curses.newwin(consciousness_height, self.width // 2 - 1, 
                                          bottom_y, 0)
        consciousness_win.scrollok(True)
        self.panes[PaneType.CONSCIOUSNESS] = Pane(
            type=PaneType.CONSCIOUSNESS,
            window=consciousness_win,
            lines=deque(maxlen=50),
            title="Consciousness"
        )
        
        # Chat on right
        chat_win = curses.newwin(consciousness_height, self.width - self.width // 2 - 1,
                                 bottom_y, self.width // 2)
        chat_win.scrollok(True)
        self.panes[PaneType.CHAT] = Pane(
            type=PaneType.CHAT,
            window=chat_win,
            lines=deque(maxlen=50),
            title="Chat"
        )
        
        # Status and input
        self.status_win = curses.newwin(1, self.width - 1, self.height - 2, 0)
        self.input_win = curses.newwin(1, self.width - 1, self.height - 1, 0)
        
    def _create_emotional_focus_layout(self):
        """Create layout focused on emotional visualization"""
        # Large emotional state pane
        emotional_height = int(self.height * 0.5)
        emotional_win = curses.newwin(emotional_height - 1, self.width - 1, 0, 0)
        self.panes[PaneType.EMOTIONAL] = Pane(
            type=PaneType.EMOTIONAL,
            window=emotional_win,
            lines=deque(maxlen=200),
            title="Emotional State Analysis"
        )
        
        # Bottom section for other panes
        bottom_y = emotional_height
        remaining_height = self.height - bottom_y - 2
        
        # Consciousness and chat side by side
        consciousness_win = curses.newwin(remaining_height, self.width // 2 - 1, 
                                          bottom_y, 0)
        consciousness_win.scrollok(True)
        self.panes[PaneType.CONSCIOUSNESS] = Pane(
            type=PaneType.CONSCIOUSNESS,
            window=consciousness_win,
            lines=deque(maxlen=50),
            title="Thoughts"
        )
        
        chat_win = curses.newwin(remaining_height, self.width - self.width // 2 - 1,
                                 bottom_y, self.width // 2)
        chat_win.scrollok(True)
        self.panes[PaneType.CHAT] = Pane(
            type=PaneType.CHAT,
            window=chat_win,
            lines=deque(maxlen=50),
            title="Interaction"
        )
        
        # Status and input
        self.status_win = curses.newwin(1, self.width - 1, self.height - 2, 0)
        self.input_win = curses.newwin(1, self.width - 1, self.height - 1, 0)
        
    def _draw_all_panes(self):
        """Draw all visible panes"""
        for pane_type, pane in self.panes.items():
            if pane.visible:
                self._draw_pane(pane)
                pane.window.noutrefresh()  # Queue for update
                
        # Draw status line
        self._draw_status()
        self.status_win.noutrefresh()
        self._draw_input()
        self.input_win.noutrefresh()
        
        # Update physical screen once
        curses.doupdate()
        
    def _draw_pane(self, pane: Pane):
        """Draw a single pane with border and title"""
        win = pane.window
        win.clear()
        
        # Draw border with highlighting for active pane
        try:
            if pane.type == self.current_focus:
                win.attron(curses.color_pair(6) | curses.A_BOLD)
            win.border()
            if pane.type == self.current_focus:
                win.attroff(curses.color_pair(6) | curses.A_BOLD)
        except curses.error:
            pass
        
        # Draw title with active indicator
        title = f" {pane.title} "
        if pane.type == self.current_focus:
            title = f"▶ {pane.title} ◀"
            title_attr = curses.color_pair(6) | curses.A_BOLD | curses.A_REVERSE
        else:
            title_attr = curses.color_pair(6)
        
        self.safe_addstr(win, 0, 2, title, title_attr)
        
        # Show scroll indicator if needed
        if pane.type in self.scroll_positions:
            scroll_pos = self.scroll_positions.get(pane.type, 0)
            if scroll_pos > 0:
                self.safe_addstr(win, 0, win.getmaxyx()[1] - 10, f" ↑{scroll_pos} ", curses.color_pair(3))
        
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
        """Draw consciousness stream content with stream indicators"""
        win = pane.window
        height, width = win.getmaxyx()
        
        # Get scroll position
        scroll_pos = self.scroll_positions.get(PaneType.CONSCIOUSNESS, 0)
        total_lines = len(pane.lines)
        
        # Calculate visible range
        if total_lines > height - 2:
            # Ensure scroll position is valid
            max_scroll = total_lines - (height - 2)
            scroll_pos = min(scroll_pos, max_scroll)
            start_idx = total_lines - (height - 2) - scroll_pos
            end_idx = total_lines - scroll_pos
        else:
            start_idx = 0
            end_idx = total_lines
        
        # Draw visible thoughts
        y = 1
        for line in list(pane.lines)[start_idx:end_idx]:
            if y >= height - 1:
                break
            text, color = line
            # Properly truncate to available width
            available_width = width - 4
            if len(text) > available_width:
                text = text[:available_width-1] + "…"
            self.safe_addstr(win, y, 2, text, curses.color_pair(color))
            y += 1
        
        # Show scroll indicators
        if scroll_pos > 0:
            self.safe_addstr(win, height-1, width-15, f"↓ {scroll_pos} more", curses.color_pair(3))
        if start_idx > 0:
            self.safe_addstr(win, 1, width-15, f"↑ {start_idx} above", curses.color_pair(3))
            
    def _draw_memory_content(self, pane: Pane):
        """Draw enhanced memory browser with categories and search"""
        win = pane.window
        height, width = win.getmaxyx()
        
        y = 1
        
        # Memory statistics
        if self.memory_manager:
            working_count = 0
            long_term_count = 0
            
            # Get counts based on memory structure
            if hasattr(self.memory_manager, 'working_memory') and isinstance(self.memory_manager.working_memory, dict):
                working_count = len(self.memory_manager.working_memory.get('recent_thoughts', []))
            if hasattr(self.memory_manager, 'long_term_memory'):
                long_term_count = len(self.memory_manager.long_term_memory)
                
            stats_text = f"Working: {working_count} | Long-term: {long_term_count}"
            self.safe_addstr(win, y, 2, stats_text, curses.color_pair(3))
            y += 1
            # Add separator line
            self.safe_addstr(win, y, 2, "─" * (width - 6), curses.color_pair(8))
            y += 2
        
        # Categories with proper spacing
        categories = [
            ("Recent Thoughts", curses.color_pair(7)),
            ("Important Memories", curses.color_pair(4)),
            ("Emotional Memories", curses.color_pair(5)),
            ("Goals & Achievements", curses.color_pair(2))
        ]
        
        # Calculate space for each section dynamically
        remaining_height = height - y - 2  # Account for border
        # Make sure we have enough space
        if remaining_height < len(categories) * 3:
            # Not enough space, just show what we can
            section_height = 3
        else:
            section_height = max(4, remaining_height // len(categories))  # At least 4 lines per section
        
        for category, color in categories:
            if y >= height - 2:
                break
            
            section_start_y = y
            
            # Clear section area first to prevent overlap
            for clear_y in range(y, min(y + section_height, height - 1)):
                self.safe_addstr(win, clear_y, 2, " " * (width - 4), curses.color_pair(8))
            
            # Category header with expansion indicator
            self.safe_addstr(win, y, 2, f"▼ {category}", color | curses.A_BOLD)
            y += 1
            
            # Reserve at least one line for content
            content_lines = section_height - 2  # Header + spacing
            lines_used = 0
            
            # Show items under each category
            if category == "Recent Thoughts" and hasattr(self, 'memory_manager') and self.memory_manager:
                try:
                    if hasattr(self.memory_manager, 'working_memory'):
                        recent_thoughts = self.memory_manager.working_memory.get('recent_thoughts', [])
                        # Show last 3 thoughts with proper formatting
                        for mem in recent_thoughts[-3:]:
                            if lines_used >= content_lines or y >= section_start_y + section_height - 1:
                                break
                            content = mem.get('content', '')
                            stream = mem.get('stream', 'unknown')
                            
                            # Calculate available width for content
                            prefix = f"  • [{stream[:3].upper()}] "
                            available_width = width - len(prefix) - 4
                            
                            # Word wrap with proper truncation
                            if len(content) > available_width:
                                # Wrap text properly
                                wrapped = textwrap.wrap(content, available_width, break_long_words=False)
                                for i, line in enumerate(wrapped[:2]):  # Max 2 lines per thought
                                    if lines_used >= content_lines or y >= section_start_y + section_height - 1:
                                        break
                                    if i == 0:
                                        self.safe_addstr(win, y, 2, prefix + line, curses.color_pair(8))
                                    else:
                                        self.safe_addstr(win, y, 2, " " * len(prefix) + line, curses.color_pair(8))
                                    y += 1
                                    lines_used += 1
                            else:
                                self.safe_addstr(win, y, 2, prefix + content, curses.color_pair(8))
                                y += 1
                                lines_used += 1
                except Exception as e:
                    logger.error(f"Error displaying memories: {e}")
                    self.safe_addstr(win, y, 4, "• Error loading memories", curses.color_pair(5))
                    y += 1
                    lines_used += 1
                    
                # Fill empty space if no thoughts
                if lines_used == 0:
                    self.safe_addstr(win, y, 4, "• No recent thoughts recorded", curses.color_pair(8))
                    y += 1
                    lines_used += 1
            
            elif category == "Important Memories" and hasattr(self, 'memory_manager') and self.memory_manager:
                # Show a placeholder or actual important memories
                self.safe_addstr(win, y, 4, "• No important memories flagged yet", curses.color_pair(8))
                y += 1
                lines_used += 1
            
            elif category == "Emotional Memories":
                # Show emotional context
                if len(self.emotional_history) > 0:
                    recent_emotion = self.emotional_history[-1]
                    emotion_text = f"• Latest: V:{recent_emotion.valence:+.2f} A:{recent_emotion.arousal:.2f}"
                    self.safe_addstr(win, y, 4, emotion_text, curses.color_pair(8))
                    y += 1
                    lines_used += 1
                else:
                    self.safe_addstr(win, y, 4, "• No emotional data recorded", curses.color_pair(8))
                    y += 1
                    lines_used += 1
            
            elif category == "Goals & Achievements":
                if self.completed_goals:
                    last_goal = self.completed_goals[-1]
                    # Properly truncate goal text
                    max_goal_width = width - 12
                    goal_desc = last_goal.description
                    if len(goal_desc) > max_goal_width:
                        goal_desc = goal_desc[:max_goal_width-3] + "..."
                    goal_text = f"• ✓ {goal_desc}"
                    self.safe_addstr(win, y, 4, goal_text, curses.color_pair(8))
                    y += 1
                    lines_used += 1
                else:
                    self.safe_addstr(win, y, 4, "• No completed goals yet", curses.color_pair(8))
                    y += 1
                    lines_used += 1
            
            # Move to next section position
            y = section_start_y + section_height
                
    def _draw_emotional_content(self, pane: Pane):
        """Draw enhanced emotional state visualization"""
        win = pane.window
        height, width = win.getmaxyx()
        
        y = 1
        
        # Current state with descriptive labels
        valence = self.current_emotional_state.valence
        arousal = self.current_emotional_state.arousal
        
        # Determine emotional label
        if valence > 0.3 and arousal > 0.6:
            emotion = "Excited"
            color = curses.color_pair(2)
        elif valence > 0.3 and arousal <= 0.6:
            emotion = "Content"
            color = curses.color_pair(2)
        elif valence < -0.3 and arousal > 0.6:
            emotion = "Anxious"
            color = curses.color_pair(5)
        elif valence < -0.3 and arousal <= 0.6:
            emotion = "Melancholy"
            color = curses.color_pair(5)
        else:
            emotion = "Neutral"
            color = curses.color_pair(8)
            
        self.safe_addstr(win, y, 2, f"Current: {emotion}", color | curses.A_BOLD)
        y += 1
        
        self.safe_addstr(win, y, 2, f"Valence: {valence:+.2f}", 
                         curses.color_pair(2 if valence > 0 else 5))
        y += 1
        self.safe_addstr(win, y, 2, f"Arousal: {arousal:.2f}", 
                         curses.color_pair(3))
        y += 2
        
        # ASCII visualization
        graph_width = min(width - 6, 50)
        graph_height = min(height - y - 2, 7)
        
        if graph_height >= 3:
            # Draw coordinate system
            mid_y = y + graph_height // 2
            
            # Y-axis (arousal)
            for i in range(graph_height):
                self.safe_addstr(win, y + i, 2, "│", curses.color_pair(8))
                
            # X-axis (valence)
            self.safe_addstr(win, mid_y, 2, "├" + "─" * graph_width + "→", curses.color_pair(8))
            
            # Labels
            self.safe_addstr(win, y - 1, 2, "↑A", curses.color_pair(8))
            self.safe_addstr(win, mid_y, graph_width + 3, "V→", curses.color_pair(8))
            
            # Plot history
            if len(self.emotional_history) > 1:
                # Sample points from history
                step = max(1, len(self.emotional_history) // graph_width)
                for i in range(0, min(len(self.emotional_history), graph_width * step), step):
                    if i < len(self.emotional_history):
                        state = self.emotional_history[i]
                        x = 3 + int((state.valence + 1) * graph_width / 2)
                        y_pos = mid_y - int(state.arousal * graph_height / 2)
                        
                        if 3 <= x < graph_width + 3 and y <= y_pos < y + graph_height:
                            # Fade older points
                            age_ratio = i / len(self.emotional_history)
                            char = "●" if age_ratio > 0.8 else "○"
                            self.safe_addstr(win, y_pos, x, char, 
                                             curses.color_pair(2 if state.valence > 0 else 5))
                            
            # Current position
            curr_x = 3 + int((valence + 1) * graph_width / 2)
            curr_y = mid_y - int(arousal * graph_height / 2)
            if 3 <= curr_x < graph_width + 3 and y <= curr_y < y + graph_height:
                self.safe_addstr(win, curr_y, curr_x, "◉", color | curses.A_BOLD)
                
    def _draw_goals_content(self, pane: Pane):
        """Draw enhanced goals tracker with progress"""
        win = pane.window
        height, width = win.getmaxyx()
        
        y = 1
        
        # Summary
        active_count = len(self.active_goals)
        completed_count = len(self.completed_goals)
        self.safe_addstr(win, y, 2, f"Active: {active_count} | Completed: {completed_count}", 
                         curses.color_pair(3))
        y += 2
        
        # Active goals with priority indicators
        if self.active_goals:
            self.safe_addstr(win, y, 2, "Active Goals:", curses.color_pair(3) | curses.A_BOLD)
            y += 1
            
            for i, goal in enumerate(self.active_goals[:5]):
                if y >= height - 1:
                    break
                    
                # Priority indicator
                priority_char = "!" if goal.priority > 0.7 else "•"
                priority_color = curses.color_pair(5) if goal.priority > 0.7 else curses.color_pair(2)
                
                self.safe_addstr(win, y, 2, priority_char, priority_color)
                self.safe_addstr(win, y, 4, f"{i}: {goal.description[:width-8]}", curses.color_pair(2))
                y += 1
                
        else:
            self.safe_addstr(win, y, 2, "No active goals", curses.color_pair(8))
            y += 1
            
        y += 1
        
        # Recent completions
        if y < height - 1 and self.completed_goals:
            self.safe_addstr(win, y, 2, "Recently Completed:", curses.color_pair(3) | curses.A_BOLD)
            y += 1
            
            for goal in reversed(self.completed_goals[-3:]):
                if y >= height - 1:
                    break
                self.safe_addstr(win, y, 2, f"✓ {goal.description[:width-6]}", curses.color_pair(8))
                y += 1
                
    def _draw_chat_content(self, pane: Pane):
        """Draw chat conversation with speaker indicators"""
        win = pane.window
        height, width = win.getmaxyx()
        
        # Get scroll position
        scroll_pos = self.scroll_positions.get(PaneType.CHAT, 0)
        total_lines = len(pane.lines)
        
        # Calculate visible range
        if total_lines > height - 2:
            max_scroll = total_lines - (height - 2)
            scroll_pos = min(scroll_pos, max_scroll)
            start_idx = total_lines - (height - 2) - scroll_pos
            end_idx = total_lines - scroll_pos
        else:
            start_idx = 0
            end_idx = total_lines
        
        # Draw visible chat lines
        y = 1
        for line in list(pane.lines)[start_idx:end_idx]:
            if y >= height - 1:
                break
            text, color = line
            
            # Ensure proper line width without overlap
            available_width = width - 4
            if len(text) > available_width:
                text = text[:available_width-1] + "…"
            
            self.safe_addstr(win, y, 2, text, curses.color_pair(color))
            y += 1
        
        # Show scroll indicators
        if scroll_pos > 0:
            self.safe_addstr(win, height-1, width-15, f"↓ {scroll_pos} more", curses.color_pair(3))
        if start_idx > 0:
            self.safe_addstr(win, 1, width-15, f"↑ {start_idx} above", curses.color_pair(3))
            
    def _draw_status(self):
        """Draw enhanced status line with metrics"""
        self.status_win.clear()
        
        # Calculate uptime
        uptime = datetime.now() - self.metrics['uptime_start']
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)
        
        # Build status message with proper spacing
        if self.command_mode:
            status = f" Command: {self.command_buffer}"
        else:
            # Left side: status message
            left_status = f" {self.status_message}"
            
            # Right side: metrics
            right_status = f"T:{self.metrics['thoughts_generated']} M:{self.metrics['memories_stored']} Up:{hours}h{minutes}m [{self.layout_mode}] "
            
            # Calculate padding
            padding_len = self.width - len(left_status) - len(right_status)
            if padding_len > 0:
                status = left_status + " " * padding_len + right_status
            else:
                # Truncate if too long
                available = self.width - len(right_status) - 3
                status = left_status[:available] + "..." + right_status
            
        self.safe_addstr(self.status_win, 0, 0, status[:self.width], curses.color_pair(6))
        
    def _draw_input(self):
        """Draw input line with mode indicator"""
        self.input_win.clear()
        
        if self.command_mode:
            prompt = "Command: "
            prompt_color = curses.color_pair(3)
        elif self.in_conversation:
            prompt = "You: "
            prompt_color = curses.color_pair(2)
        else:
            prompt = "> "
            prompt_color = curses.color_pair(8)
            
        self.safe_addstr(self.input_win, 0, 0, prompt, prompt_color)
        self.safe_addstr(self.input_win, 0, len(prompt), 
                         self.input_buffer[:self.width-len(prompt)-1], curses.color_pair(8))
        
        # Position cursor
        cursor_x = len(prompt) + len(self.input_buffer)
        if cursor_x < self.width - 1:
            self.input_win.move(0, cursor_x)
        
    def safe_addstr(self, win, y, x, text, attr=0):
        """Safely add string to window, handling boundaries"""
        try:
            height, width = win.getmaxyx()
            if 0 <= y < height and 0 <= x < width:
                # Ensure text is a string
                text = str(text)
                # Truncate text to fit
                max_len = width - x - 1
                if max_len > 0:
                    win.addstr(y, x, text[:max_len], attr)
        except curses.error:
            # Ignore curses errors (typically from writing to screen edges)
            pass
            
    def refresh_all(self):
        """Refresh all windows using double buffering"""
        for pane in self.panes.values():
            if pane.visible:
                try:
                    pane.window.noutrefresh()
                except curses.error:
                    pass
        self.status_win.noutrefresh()
        self.input_win.noutrefresh()
        # Single update to physical screen
        curses.doupdate()
        
    async def ui_refresh_loop(self):
        """Periodic UI refresh for dynamic content only"""
        last_uptime = None
        last_thought_count = 0
        last_memory_count = 0
        last_goals_count = 0
        last_input_buffer = ""
        needs_full_redraw = True  # Initial full draw
        
        while self.running:
            try:
                updates_made = False
                
                # Perform full redraw if needed
                if needs_full_redraw:
                    self._draw_all_panes()
                    needs_full_redraw = False
                    updates_made = True
                
                # Update specific panes if needed - with error handling
                try:
                    if self.consciousness_needs_update and PaneType.CONSCIOUSNESS in self.panes:
                        self._draw_pane(self.panes[PaneType.CONSCIOUSNESS])
                        self.panes[PaneType.CONSCIOUSNESS].window.noutrefresh()
                        self.consciousness_needs_update = False
                        updates_made = True
                    
                    if self.chat_needs_update and PaneType.CHAT in self.panes:
                        self._draw_pane(self.panes[PaneType.CHAT])
                        self.panes[PaneType.CHAT].window.noutrefresh()
                        self.chat_needs_update = False
                        updates_made = True
                        
                    # Check if memory count changed
                    current_memory_count = self.metrics['memories_stored']
                    if current_memory_count != last_memory_count:
                        last_memory_count = current_memory_count
                        if PaneType.MEMORY in self.panes:
                            self._draw_pane(self.panes[PaneType.MEMORY])
                            self.panes[PaneType.MEMORY].window.noutrefresh()
                            updates_made = True
                    
                    # Check if goals changed
                    current_goals_count = len(self.active_goals) + len(self.completed_goals)
                    if current_goals_count != last_goals_count:
                        last_goals_count = current_goals_count
                        if PaneType.GOALS in self.panes:
                            self._draw_pane(self.panes[PaneType.GOALS])
                            self.panes[PaneType.GOALS].window.noutrefresh()
                            updates_made = True
                            
                except Exception as e:
                    logger.error(f"Error updating panes: {e}")
                    needs_full_redraw = True
                
                # Only update status bar if time has changed
                current_uptime = datetime.now() - self.metrics['uptime_start']
                current_minutes = int(current_uptime.total_seconds() // 60)
                
                if last_uptime is None or current_minutes != last_uptime:
                    last_uptime = current_minutes
                    self._draw_status()
                    self.status_win.noutrefresh()
                    updates_made = True
                
                # Only update metrics if thoughts changed
                if self.total_thoughts != last_thought_count:
                    last_thought_count = self.total_thoughts
                    # Status bar includes thought count
                    self._draw_status()
                    self.status_win.noutrefresh()
                    updates_made = True
                
                # Only update input line if it changed
                current_input = self.input_buffer if not self.command_mode else self.command_buffer
                if current_input != last_input_buffer:
                    last_input_buffer = current_input
                    self._draw_input()
                    self.input_win.noutrefresh()
                    updates_made = True
                
                # Single screen update only if needed
                if updates_made:
                    curses.doupdate()
                
                # Slower refresh rate to reduce flickering
                await asyncio.sleep(1.0)  # Increased to 1 second to reduce flicker
            except Exception as e:
                logger.error(f"UI refresh error: {e}")
                needs_full_redraw = True  # Redraw everything on error
                await asyncio.sleep(1)
    
    async def consciousness_loop(self):
        """Main consciousness generation loop"""
        stream_thought_counts = {}
        
        while self.running:
            try:
                # Check if consciousness service is running and get thoughts
                if self.consciousness and hasattr(self.consciousness, 'streams'):
                    # Collect thoughts from all streams
                    for stream_id, stream in self.consciousness.streams.items():
                        if hasattr(stream, 'content_buffer'):
                            # Track thoughts per stream
                            current_count = len(stream.content_buffer)
                            last_count = stream_thought_counts.get(stream_id, 0)
                            
                            if current_count > last_count:
                                # Get new thoughts since last check
                                new_thoughts = list(stream.content_buffer)[last_count:current_count]
                                stream_thought_counts[stream_id] = current_count
                                
                                for thought in new_thoughts:
                                    thought_text = thought.get('content', '')
                                    importance = thought.get('importance', 5)
                                    
                                    # Format with stream indicator
                                    if stream_id == 'primary':
                                        prefix = "💭"
                                        color = 1
                                    elif stream_id == 'creative':
                                        prefix = "🎨"
                                        color = 4
                                    elif stream_id == 'subconscious':
                                        prefix = "🌊"
                                        color = 7
                                    elif stream_id == 'meta':
                                        prefix = "🔍"
                                        color = 3
                                    else:
                                        prefix = "•"
                                        color = 8
                                        
                                    # Add to consciousness pane
                                    display_text = f"{prefix} [{stream_id[:3].upper()}] {thought_text}"
                                    self.add_consciousness_line(display_text, color)
                                    
                                    # Update metrics
                                    self.metrics['thoughts_generated'] += 1
                                    self.total_thoughts += 1
                                    
                                    # Store thought in memory via orchestrator message system
                                    if self.memory_manager and importance > 3:  # Only store meaningful thoughts
                                        message = Message(
                                            source='consciousness',
                                            target='memory',
                                            type='store_thought',
                                            content={
                                                'type': 'thought',
                                                'content': thought_text,
                                                'stream': stream_id,
                                                'timestamp': datetime.now().isoformat(),
                                                'importance': importance,
                                                'emotional_tone': thought.get('emotional_tone', 'neutral'),
                                                'stream_type': stream_id
                                            }
                                        )
                                        await self.orchestrator.send_message(message)
                                        self.metrics['memories_stored'] += 1
                                        
                                        # Also store directly in working memory for immediate access
                                        if hasattr(self.memory_manager, 'working_memory'):
                                            self.memory_manager.working_memory['recent_thoughts'].append({
                                                'content': thought_text,
                                                'stream': stream_id,
                                                'timestamp': datetime.now().isoformat(),
                                                'importance': importance
                                            })
                                    
                                    # Update emotional state
                                    tone = thought.get('emotional_tone', 'neutral')
                                    self._update_emotional_state(tone)
                                
                        # Process any cross-stream insights
                        await self._process_insights()
                        
                await asyncio.sleep(0.1)  # Small delay
                
            except Exception as e:
                logger.error(f"Consciousness loop error: {e}")
                self.add_system_line(f"Consciousness error: {str(e)}", 5)
                await asyncio.sleep(1)
                
    async def _process_insights(self):
        """Process cross-stream insights and emergent patterns"""
        # This would analyze patterns across streams
        # For now, just a placeholder
        pass
        
    def _update_emotional_state(self, tone: str):
        """Update emotional state based on thought tone"""
        # Mapping of tones to valence/arousal changes
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
            'attentive': (0.0, 0.1),
            'inspired': (0.3, 0.1),
            'playful': (0.2, 0.2),
            'contemplative': (0.0, -0.1),
            'analytical': (-0.1, 0.0),
            'observant': (0.0, 0.0),
            'reflective': (0.1, -0.1)
        }
        
        valence_delta, arousal_delta = tone_effects.get(tone, (0.0, 0.0))
        
        # Update with momentum and decay
        momentum = 0.85  # How much previous state influences new state
        self.current_emotional_state.valence = (
            self.current_emotional_state.valence * momentum + valence_delta * (1 - momentum)
        )
        self.current_emotional_state.arousal = (
            self.current_emotional_state.arousal * momentum + 
            arousal_delta * (1 - momentum) + 0.01  # Slight bias towards middle arousal
        )
        
        # Clamp values
        self.current_emotional_state.valence = max(-1, min(1, self.current_emotional_state.valence))
        self.current_emotional_state.arousal = max(0, min(1, self.current_emotional_state.arousal))
        
        # Record history
        self.emotional_history.append(EmotionalState(
            valence=self.current_emotional_state.valence,
            arousal=self.current_emotional_state.arousal
        ))
        
        # Update displays only if visible
        if PaneType.EMOTIONAL in self.panes and self.panes[PaneType.EMOTIONAL].visible:
            self._draw_pane(self.panes[PaneType.EMOTIONAL])
            self.panes[PaneType.EMOTIONAL].window.noutrefresh()
            curses.doupdate()
            
    def add_consciousness_line(self, text: str, color: int = 1):
        """Add line to consciousness pane"""
        if PaneType.CONSCIOUSNESS in self.panes:
            # Word wrap long lines
            max_width = self.panes[PaneType.CONSCIOUSNESS].window.getmaxyx()[1] - 4
            if len(text) > max_width:
                # Keep the prefix intact for wrapped lines
                if text.startswith(('💭', '🎨', '🌊', '🔍', '•')):
                    # Find the first space after the prefix and tag
                    parts = text.split(' ', 2)  # Split into at most 3 parts
                    if len(parts) >= 3 and parts[1].startswith('[') and parts[1].endswith(']'):
                        # We have emoji, tag, and content
                        prefix = f"{parts[0]} {parts[1]}"
                        rest = parts[2]
                    elif len(parts) >= 2:
                        # Just emoji and content
                        prefix = parts[0]
                        rest = ' '.join(parts[1:])
                    else:
                        # Just the emoji
                        prefix = text
                        rest = ""
                    
                    if rest:
                        # Calculate available width for text after prefix
                        prefix_len = len(prefix) + 1  # +1 for space
                        available_width = max_width - prefix_len
                        if available_width > 10:  # Only wrap if we have reasonable space
                            lines = textwrap.wrap(rest, available_width, break_long_words=False)
                            if lines:
                                # First line with prefix
                                self.panes[PaneType.CONSCIOUSNESS].lines.append((f"{prefix} {lines[0]}", color))
                                # Subsequent lines with indent (matching prefix length)
                                indent = ' ' * prefix_len
                                for line in lines[1:]:
                                    self.panes[PaneType.CONSCIOUSNESS].lines.append((f"{indent}{line}", color))
                        else:
                            # Not enough space, truncate
                            self.panes[PaneType.CONSCIOUSNESS].lines.append((text[:max_width-3] + "...", color))
                    else:
                        self.panes[PaneType.CONSCIOUSNESS].lines.append((prefix, color))
                else:
                    # No special prefix, normal wrap
                    lines = textwrap.wrap(text, max_width, break_long_words=False)
                    for line in lines:
                        self.panes[PaneType.CONSCIOUSNESS].lines.append((line, color))
            else:
                self.panes[PaneType.CONSCIOUSNESS].lines.append((text, color))
            
            # Mark that consciousness pane needs update
            self.consciousness_needs_update = True
            
            # Auto-scroll to bottom when new content added (if not manually scrolled)
            if PaneType.CONSCIOUSNESS not in self.scroll_positions or self.scroll_positions[PaneType.CONSCIOUSNESS] == 0:
                # Reset scroll to show latest
                self.scroll_positions[PaneType.CONSCIOUSNESS] = 0
            
    def add_chat_line(self, text: str, color: int = 2):
        """Add line to chat pane"""
        if PaneType.CHAT in self.panes:
            # Word wrap long lines
            max_width = self.panes[PaneType.CHAT].window.getmaxyx()[1] - 4
            if len(text) > max_width:
                # Check if this is a speaker line
                if text.startswith(("You: ", "Claude: ", "[System] ")):
                    # Find speaker prefix
                    if text.startswith("You: "):
                        prefix = "You: "
                        rest = text[5:]
                    elif text.startswith("Claude: "):
                        prefix = "Claude: "
                        rest = text[8:]
                    elif text.startswith("[System] "):
                        prefix = "[System] "
                        rest = text[9:]
                    else:
                        prefix = ""
                        rest = text
                    
                    if prefix and rest:
                        # Wrap with continuation indent
                        indent = "  "  # Indent continuation lines
                        available_width = max_width - len(indent)
                        lines = textwrap.wrap(rest, available_width, break_long_words=False)
                        if lines:
                            # First line with speaker
                            self.panes[PaneType.CHAT].lines.append((prefix + lines[0], color))
                            # Continuation lines with indent
                            for line in lines[1:]:
                                self.panes[PaneType.CHAT].lines.append((indent + line, color))
                    else:
                        self.panes[PaneType.CHAT].lines.append((text[:max_width], color))
                else:
                    # Regular text wrap
                    lines = textwrap.wrap(text, max_width, break_long_words=False)
                    for line in lines:
                        self.panes[PaneType.CHAT].lines.append((line, color))
            else:
                self.panes[PaneType.CHAT].lines.append((text, color))
            
            # Mark that chat pane needs update
            self.chat_needs_update = True
            
            # Auto-scroll to bottom for chat
            if PaneType.CHAT not in self.scroll_positions or self.scroll_positions[PaneType.CHAT] == 0:
                self.scroll_positions[PaneType.CHAT] = 0
            
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
        
        commands = {
            "/memory": self.memory_command,
            "/stream": self.stream_command,
            "/emotional": self.emotional_command,
            "/goals": self.goals_command,
            "/layout": self.layout_command,
            "/state": self.state_command,
            "/metrics": self.metrics_command,
            "/safety": self.safety_command,
            "/help": self.show_help,
            "/quit": self.quit_command
        }
        
        if cmd in commands:
            await commands[cmd](args)
        else:
            self.add_system_line(f"Unknown command: {cmd}. Type /help for commands.", 5)
            
    async def memory_command(self, args: List[str]):
        """Handle memory-related commands"""
        if not args:
            self.add_system_line("Memory commands: search <query>, stats, clear, consolidate", 3)
            return
            
        subcmd = args[0]
        
        if subcmd == "search" and len(args) > 1:
            query = " ".join(args[1:])
            if self.memory_manager:
                memories = await self.memory_manager.recall_similar(query, k=5)
                self.add_system_line(f"Found {len(memories)} memories matching '{query}':", 3)
                for i, mem in enumerate(memories):
                    content = mem.get('content', '')[:80]
                    self.add_chat_line(f"  {i+1}. {content}...", 7)
                    
        elif subcmd == "stats":
            if self.memory_manager:
                self.add_system_line("Memory Statistics:", 3)
                
                # Get working memory count
                working_count = 0
                if hasattr(self.memory_manager, 'working_memory') and isinstance(self.memory_manager.working_memory, dict):
                    working_count = len(self.memory_manager.working_memory.get('recent_thoughts', []))
                
                # Get long-term memory count
                long_term_count = len(getattr(self.memory_manager, 'long_term_memory', []))
                
                self.add_chat_line(f"  Working memory: {working_count} items", 7)
                self.add_chat_line(f"  Long-term memory: {long_term_count} items", 7)
                
                if hasattr(self.memory_manager, 'vector_store') and hasattr(self.memory_manager.vector_store, 'vectors'):
                    self.add_chat_line(f"  Semantic index: {len(self.memory_manager.vector_store.vectors)} vectors", 7)
                    
                # Show last few memories
                if working_count > 0:
                    recent = self.memory_manager.working_memory.get('recent_thoughts', [])[-3:]
                    self.add_chat_line("  Recent thoughts:", 7)
                    for mem in recent:
                        content = mem.get('content', '')[:60]
                        self.add_chat_line(f"    - {content}...", 8)
                    
                self.metrics['memories_stored'] = working_count + long_term_count
                
                # Force immediate update of memory pane
                if PaneType.MEMORY in self.panes:
                    self._draw_pane(self.panes[PaneType.MEMORY])
                    self.panes[PaneType.MEMORY].window.noutrefresh()
                    curses.doupdate()
                
        elif subcmd == "consolidate":
            if self.memory_manager:
                self.add_system_line("Starting memory consolidation...", 3)
                await self.memory_manager.consolidate_memories()
                self.add_system_line("Memory consolidation complete", 3)
                
        elif subcmd == "clear":
            self.add_system_line("Memory clearing requires confirmation. Use: /memory clear confirm", 5)
            if len(args) > 1 and args[1] == "confirm":
                # Clear working memory only (preserve long-term)
                if hasattr(self.memory_manager, 'working_memory'):
                    self.memory_manager.working_memory.clear()
                self.add_system_line("Working memory cleared", 3)
                
    async def stream_command(self, args: List[str]):
        """Handle consciousness stream commands"""
        if not args:
            self.add_system_line("Stream commands: pause, resume, focus <stream>, list", 3)
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
                # Adjust attention weights
                for stream in self.consciousness.attention_weights:
                    self.consciousness.attention_weights[stream] = 0.2
                self.consciousness.attention_weights[stream_name] = 0.9
                self.add_system_line(f"Focusing on {stream_name} stream", 3)
            else:
                self.add_system_line(f"Unknown stream: {stream_name}", 5)
                
        elif subcmd == "list":
            if self.consciousness:
                self.add_system_line("Active consciousness streams:", 3)
                for stream_id, weight in self.consciousness.attention_weights.items():
                    status = "●" if weight > 0.5 else "○"
                    self.add_chat_line(f"  {status} {stream_id}: attention={weight:.2f}", 7)
                    
    async def emotional_command(self, args: List[str]):
        """Handle emotional state commands"""
        if not args:
            self.add_system_line("Emotional commands: set <valence> <arousal>, reset, history", 3)
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
                self.add_system_line("Invalid values. Use numbers: valence (-1 to 1), arousal (0 to 1)", 5)
                
        elif subcmd == "reset":
            self.current_emotional_state.valence = 0.0
            self.current_emotional_state.arousal = 0.5
            self.emotional_history.clear()
            self.add_system_line("Emotional state reset to neutral", 3)
            
        elif subcmd == "history":
            if self.emotional_history:
                recent = list(self.emotional_history)[-5:]
                self.add_system_line("Recent emotional states:", 3)
                for i, state in enumerate(recent):
                    self.add_chat_line(f"  {i+1}. V:{state.valence:+.2f} A:{state.arousal:.2f}", 7)
            else:
                self.add_system_line("No emotional history recorded", 3)
                
    async def goals_command(self, args: List[str]):
        """Handle goals commands"""
        if not args:
            self.add_system_line("Goals commands: add <desc>, complete <idx>, priority <idx> <0-1>, list", 3)
            return
            
        subcmd = args[0]
        
        if subcmd == "add" and len(args) > 1:
            description = " ".join(args[1:])
            goal = Goal(
                id=f"goal_{datetime.now().timestamp()}",
                description=description,
                priority=0.5,
                created_at=datetime.now(),
                status="active"
            )
            self.active_goals.append(goal)
            self.add_system_line(f"Added goal: {description}", 3)
            
            # Force immediate update of goals pane
            if PaneType.GOALS in self.panes:
                self._draw_pane(self.panes[PaneType.GOALS])
                self.panes[PaneType.GOALS].window.noutrefresh()
                curses.doupdate()
            
        elif subcmd == "complete" and len(args) > 1:
            try:
                index = int(args[1])
                if 0 <= index < len(self.active_goals):
                    goal = self.active_goals.pop(index)
                    goal.status = "completed"
                    goal.updated_at = datetime.now()
                    self.completed_goals.append(goal)
                    self.metrics['goals_completed'] += 1
                    self.add_system_line(f"Completed goal: {goal.description}", 3)
                    
                    # Generate achievement thought
                    if self.consciousness:
                        achievement_thought = {
                            'content': f"I've completed a goal: {goal.description}. This gives me a sense of accomplishment.",
                            'stream': 'primary',
                            'timestamp': time.time(),
                            'emotional_tone': 'content',
                            'importance': 7
                        }
                        await self.consciousness.process_thought(
                            achievement_thought, 
                            self.consciousness.streams['primary']
                        )
                else:
                    self.add_system_line(f"Invalid goal index: {index}", 5)
            except ValueError:
                self.add_system_line("Invalid index. Use goal number from list.", 5)
                
        elif subcmd == "priority" and len(args) >= 3:
            try:
                index = int(args[1])
                priority = float(args[2])
                if 0 <= index < len(self.active_goals) and 0 <= priority <= 1:
                    self.active_goals[index].priority = priority
                    self.add_system_line(f"Updated goal priority to {priority}", 3)
                    # Resort by priority
                    self.active_goals.sort(key=lambda g: g.priority, reverse=True)
            except (ValueError, IndexError):
                self.add_system_line("Invalid arguments. Use: priority <index> <0-1>", 5)
                
        elif subcmd == "list":
            self.add_system_line(f"Active goals ({len(self.active_goals)}):", 3)
            for i, goal in enumerate(self.active_goals):
                priority_indicator = "!" if goal.priority > 0.7 else "•"
                self.add_chat_line(f"  {i}: [{priority_indicator}] {goal.description}", 2)
                
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
            
    async def state_command(self, args: List[str]):
        """Handle system state commands"""
        if not args:
            current = self.orchestrator.state if self.orchestrator else "unknown"
            self.add_system_line(f"Current state: {current}", 3)
            self.add_system_line("Available states: thinking, exploring, creating, reflecting, sleeping", 3)
            return
            
        new_state = args[0].upper()
        try:
            state_enum = SystemState[new_state]
            if self.orchestrator:
                await self.orchestrator.transition_to(state_enum)
                self.add_system_line(f"Transitioned to {new_state} state", 3)
        except KeyError:
            self.add_system_line(f"Unknown state: {new_state}", 5)
            
    async def metrics_command(self, args: List[str]):
        """Display system metrics"""
        uptime = datetime.now() - self.metrics['uptime_start']
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)
        
        self.add_system_line("System Metrics:", 3)
        self.add_chat_line(f"  Uptime: {hours} hours, {minutes} minutes", 7)
        self.add_chat_line(f"  Thoughts generated: {self.metrics['thoughts_generated']}", 7)
        self.add_chat_line(f"  Memories stored: {self.metrics['memories_stored']}", 7)
        self.add_chat_line(f"  Goals completed: {self.metrics['goals_completed']}", 7)
        
        if self.consciousness:
            self.add_chat_line(f"  Consciousness active: {'Yes' if self.consciousness.is_conscious else 'No'}", 7)
            self.add_chat_line(f"  Total thoughts: {self.consciousness.total_thoughts}", 7)
            
    async def safety_command(self, args: List[str]):
        """Handle safety framework commands"""
        if not args:
            self.add_system_line("Safety commands: status, test <action>, report", 3)
            return
            
        subcmd = args[0]
        
        if subcmd == "status":
            if self.safety:
                self.add_system_line("Safety Framework Status:", 3)
                self.add_chat_line("  Framework: Active", 2)
                self.add_chat_line("  Validation layers: 4", 7)
                self.add_chat_line("  Constraints loaded: Yes", 7)
            else:
                self.add_system_line("Safety framework not initialized", 5)
                
        elif subcmd == "test" and len(args) > 1:
            test_action = " ".join(args[1:])
            if self.safety:
                result = await self.safety.validate_action({
                    'type': 'test',
                    'content': test_action
                })
                if result.is_safe:
                    self.add_system_line(f"Action '{test_action}' passed safety validation", 2)
                else:
                    self.add_system_line(f"Action '{test_action}' failed: {result.reason}", 5)
                    
        elif subcmd == "report":
            self.add_system_line("Safety report generated in logs/safety_report.json", 3)
            
    async def quit_command(self, args: List[str]):
        """Handle quit command"""
        self.add_system_line("Shutting down Claude-AGI...", 3)
        self.running = False
        
        # Cancel all running tasks to ensure clean shutdown
        try:
            # Cancel UI refresh task
            if hasattr(self, 'ui_refresh_task') and self.ui_refresh_task:
                self.ui_refresh_task.cancel()
            
            # Cancel all consciousness tasks
            for task in self.consciousness_tasks.values():
                if task and not task.done():
                    task.cancel()
            
            # Clear task references
            self.consciousness_tasks.clear()
            
            # Give tasks a moment to cancel
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.debug(f"Error during quit cleanup: {e}")
        
    async def show_help(self, args: List[str] = None):
        """Show help information"""
        help_sections = {
            "commands": [
                "Basic Commands:",
                "  /memory search <query> - Search memories",
                "  /memory stats - Show memory statistics", 
                "  /memory consolidate - Consolidate memories",
                "  /stream pause/resume - Control consciousness",
                "  /stream focus <name> - Focus on stream",
                "  /stream list - List all streams",
                "  /emotional set <v> <a> - Set emotional state",
                "  /emotional history - Show emotional history",
                "  /goals add <desc> - Add a new goal",
                "  /goals complete <idx> - Complete a goal",
                "  /goals priority <idx> <p> - Set priority",
                "  /layout <mode> - Change UI layout",
                "  /state [<state>] - View/change system state",
                "  /metrics - Show system metrics",
                "  /safety status - Safety framework status",
                "  /help [topic] - Show help",
                "  /quit - Exit Claude-AGI"
            ],
            "keys": [
                "Keyboard Shortcuts:",
                "  Tab - Switch focus between panes (active pane highlighted)",
                "  / - Enter command mode",
                "  Esc - Exit command mode / Exit program",
                "  Arrow Keys:",
                "    Up/Down - Scroll current pane (when not typing)",
                "    Up/Down - Navigate command history (when typing)",
                "    PgUp/PgDn - Scroll by page",
                "    Home/End - Go to top/bottom",
                "  Ctrl+L - Clear current pane",
                "  Ctrl+C - Emergency exit"
            ],
            "states": [
                "System States:",
                "  THINKING - General cognitive processing",
                "  EXPLORING - Active learning and discovery",
                "  CREATING - Creative generation mode",
                "  REFLECTING - Meta-cognitive analysis",
                "  SLEEPING - Low-power memory consolidation"
            ],
            "layouts": [
                "Layout Modes:",
                "  standard - Balanced view of all systems",
                "  memory_focus - Expanded memory browser",
                "  emotional_focus - Detailed emotional analysis"
            ]
        }
        
        topic = args[0] if args else "commands"
        
        if topic in help_sections:
            for line in help_sections[topic]:
                self.add_chat_line(line, 3)
        else:
            self.add_chat_line("Help topics: commands, keys, states, layouts", 3)
            self.add_chat_line("Use: /help <topic> for specific help", 3)
            
    async def handle_user_message(self, message: str):
        """Process user conversation message"""
        self.in_conversation = True
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now()
        })
        
        # Store in memory via orchestrator
        if self.memory_manager:
            message_obj = Message(
                source='chat',
                target='memory',
                type='store_thought',
                content={
                    'type': 'conversation',
                    'content': f"User said: {message}",
                    'timestamp': datetime.now().isoformat(),
                    'importance': 6,
                    'stream_type': 'conversation'
                }
            )
            await self.orchestrator.send_message(message_obj)
        
        # Notify consciousness of user input
        if self.consciousness:
            await self.consciousness.handle_user_input({'message': message})
        
        # Generate response
        response = await self._generate_response(message)
        
        # Display response
        # Add response with proper formatting to prevent overlap
        self.add_chat_line(f"Claude: {response}", 4)
        
        # Force immediate update to prevent overlap
        if PaneType.CHAT in self.panes:
            self._draw_pane(self.panes[PaneType.CHAT])
            self.panes[PaneType.CHAT].window.noutrefresh()
            curses.doupdate()
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "assistant", 
            "content": response,
            "timestamp": datetime.now()
        })
        
        # Store response in memory via orchestrator
        if self.memory_manager:
            message_obj = Message(
                source='chat',
                target='memory',
                type='store_thought',
                content={
                    'type': 'conversation',
                    'content': f"I responded: {response}",
                    'timestamp': datetime.now().isoformat(),
                    'importance': 5,
                    'stream_type': 'conversation'
                }
            )
            await self.orchestrator.send_message(message_obj)
        
        self.in_conversation = False
        
    async def _generate_response(self, user_input: str) -> str:
        """Generate response using thought generator"""
        if self.thought_generator.use_api:
            try:
                # Convert conversation history for API
                history = []
                for msg in list(self.conversation_history)[-10:]:  # Last 10 messages
                    history.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                
                response = await self.thought_generator.generate_response(
                    user_input,
                    conversation_history=history,
                    emotional_state=self.current_emotional_state
                )
                return response
            except Exception as e:
                logger.error(f"Response generation error: {e}")
                return "I'm having trouble formulating a response right now. Let me gather my thoughts..."
        else:
            # Fallback response
            return "I'm reflecting on what you said. My thought generation capabilities are currently limited, but I'm still processing and learning from our interaction."
            
    async def input_handler(self):
        """Handle user input asynchronously"""
        while self.running:
            try:
                # Get input from curses (non-blocking)
                ch = self.stdscr.getch()
                
                if ch == -1:  # No input
                    await asyncio.sleep(0.01)  # Short delay but not too aggressive
                    continue
                    
                # Handle special keys
                if ch == 27:  # ESC
                    if self.command_mode:
                        self.command_mode = False
                        self.command_buffer = ""
                        self.status_message = "Command mode exited"
                    else:
                        # Confirm exit
                        self.add_system_line("Press ESC again to exit, or any other key to continue", 5)
                        confirm_ch = self.stdscr.getch()
                        if confirm_ch == 27:
                            self.running = False
                            
                elif ch == ord('\t'):  # Tab - switch focus
                    pane_types = list(self.panes.keys())
                    current_idx = pane_types.index(self.current_focus)
                    self.current_focus = pane_types[(current_idx + 1) % len(pane_types)]
                    self._draw_all_panes()
                    self.refresh_all()
                    
                elif ch == curses.KEY_UP and not self.command_mode and not self.input_buffer:
                    # Scroll up in current pane
                    if self.current_focus in self.scroll_positions:
                        current_pos = self.scroll_positions[self.current_focus]
                        pane = self.panes[self.current_focus]
                        max_scroll = len(pane.lines) - (pane.window.getmaxyx()[0] - 2)
                        if current_pos < max_scroll:
                            self.scroll_positions[self.current_focus] = current_pos + 1
                            self._draw_pane(pane)
                            pane.window.noutrefresh()
                            curses.doupdate()
                    elif self.current_focus not in self.scroll_positions and self.current_focus in self.panes:
                        self.scroll_positions[self.current_focus] = 1
                        pane = self.panes[self.current_focus]
                        self._draw_pane(pane)
                        pane.window.noutrefresh()
                        curses.doupdate()
                        
                elif ch == curses.KEY_DOWN and not self.command_mode and not self.input_buffer:
                    # Scroll down in current pane
                    if self.current_focus in self.scroll_positions:
                        current_pos = self.scroll_positions[self.current_focus]
                        if current_pos > 0:
                            self.scroll_positions[self.current_focus] = current_pos - 1
                            pane = self.panes[self.current_focus]
                            self._draw_pane(pane)
                            pane.window.noutrefresh()
                            curses.doupdate()
                            
                elif ch == curses.KEY_PPAGE:  # Page Up
                    if self.current_focus in self.panes:
                        pane = self.panes[self.current_focus]
                        page_size = pane.window.getmaxyx()[0] - 3
                        current_pos = self.scroll_positions.get(self.current_focus, 0)
                        max_scroll = len(pane.lines) - (pane.window.getmaxyx()[0] - 2)
                        new_pos = min(current_pos + page_size, max_scroll)
                        if new_pos > current_pos:
                            self.scroll_positions[self.current_focus] = new_pos
                            self._draw_pane(pane)
                            pane.window.noutrefresh()
                            curses.doupdate()
                            
                elif ch == curses.KEY_NPAGE:  # Page Down
                    if self.current_focus in self.scroll_positions:
                        pane = self.panes[self.current_focus]
                        page_size = pane.window.getmaxyx()[0] - 3
                        current_pos = self.scroll_positions[self.current_focus]
                        new_pos = max(current_pos - page_size, 0)
                        if new_pos < current_pos:
                            self.scroll_positions[self.current_focus] = new_pos
                            self._draw_pane(pane)
                            pane.window.noutrefresh()
                            curses.doupdate()
                            
                elif ch == curses.KEY_HOME:  # Home - go to top
                    if self.current_focus in self.panes:
                        pane = self.panes[self.current_focus]
                        max_scroll = len(pane.lines) - (pane.window.getmaxyx()[0] - 2)
                        if max_scroll > 0:
                            self.scroll_positions[self.current_focus] = max_scroll
                            self._draw_pane(pane)
                            pane.window.noutrefresh()
                            curses.doupdate()
                            
                elif ch == curses.KEY_END:  # End - go to bottom
                    if self.current_focus in self.scroll_positions:
                        self.scroll_positions[self.current_focus] = 0
                        pane = self.panes[self.current_focus]
                        self._draw_pane(pane)
                        pane.window.noutrefresh()
                        curses.doupdate()
                    
                elif ch == ord('/') and not self.command_mode and not self.input_buffer:
                    self.command_mode = True
                    self.command_buffer = "/"
                    # Immediate update for slash commands
                    self._draw_status()
                    self._draw_input()
                    self.status_win.noutrefresh()
                    self.input_win.noutrefresh()
                    curses.doupdate()
                    
                elif ch == curses.KEY_UP and (self.command_mode or self.input_buffer):  # Command history
                    if self.command_history and self.history_index < len(self.command_history) - 1:
                        self.history_index += 1
                        if self.command_mode:
                            self.command_buffer = self.command_history[-(self.history_index + 1)]
                        else:
                            self.input_buffer = self.command_history[-(self.history_index + 1)]
                            
                elif ch == curses.KEY_DOWN and (self.command_mode or self.input_buffer):  # Command history
                    if self.history_index > -1:
                        self.history_index -= 1
                        if self.history_index >= 0:
                            if self.command_mode:
                                self.command_buffer = self.command_history[-(self.history_index + 1)]
                            else:
                                self.input_buffer = self.command_history[-(self.history_index + 1)]
                        else:
                            self.command_buffer = "/" if self.command_mode else ""
                            self.input_buffer = ""
                            
                elif ch == curses.KEY_RESIZE:  # Terminal resized
                    # Get new dimensions
                    self.height, self.width = self.stdscr.getmaxyx()
                    # Recreate panes with new dimensions
                    self._create_panes()
                    self._draw_all_panes()
                    self.refresh_all()
                    
                elif ch == 12:  # Ctrl+L - Clear current pane
                    if self.current_focus in self.panes:
                        self.panes[self.current_focus].lines.clear()
                        self._draw_pane(self.panes[self.current_focus])
                        self.panes[self.current_focus].window.noutrefresh()
                        curses.doupdate()
                        
                elif ch == ord('\n'):  # Enter
                    if self.command_mode and self.command_buffer:
                        # Execute command
                        self.command_history.append(self.command_buffer)
                        self.history_index = -1
                        await self.handle_command(self.command_buffer)
                        self.command_mode = False
                        self.command_buffer = ""
                    elif self.input_buffer:
                        # Process user message
                        user_text = self.input_buffer
                        self.input_buffer = ""
                        self.history_index = -1
                        self.add_chat_line(f"You: {user_text}", 2)
                        
                        # Handle message asynchronously
                        asyncio.create_task(self.handle_user_message(user_text))
                        
                        # Force immediate update of input area
                        self._draw_input()
                        self.input_win.noutrefresh()
                        curses.doupdate()
                        
                elif ch == curses.KEY_BACKSPACE or ch == 127:
                    if self.command_mode and len(self.command_buffer) > 1:
                        self.command_buffer = self.command_buffer[:-1]
                    elif not self.command_mode and self.input_buffer:
                        self.input_buffer = self.input_buffer[:-1]
                        
                elif 32 <= ch <= 126:  # Printable characters
                    if self.command_mode:
                        self.command_buffer += chr(ch)
                    else:
                        self.input_buffer += chr(ch)
                        
                # Only update display if we actually processed input
                if ch != -1:
                    self._draw_status()
                    self._draw_input()
                    self.status_win.noutrefresh()
                    self.input_win.noutrefresh()
                    curses.doupdate()
                
            except Exception as e:
                logger.error(f"Input handler error: {e}", exc_info=True)
                await asyncio.sleep(0.1)
                
    async def run_async(self):
        """Run all async components"""
        try:
            # Start the orchestrator
            logger.info("Starting AGI orchestrator...")
            orchestrator_task = asyncio.create_task(self.orchestrator.run())
            
            # Wait for services to initialize
            await asyncio.sleep(1)
            
            # Get service references after initialization
            self.memory_manager = self.orchestrator.services.get('memory')
            self.consciousness = self.orchestrator.services.get('consciousness')
            self.safety = self.orchestrator.services.get('safety')
            
            # Log service connections
            if self.memory_manager:
                logger.info("Memory manager connected successfully")
                # Ensure memory manager can receive messages from orchestrator
                if hasattr(self.memory_manager, 'handle_message'):
                    logger.info("Memory manager message handler confirmed")
            else:
                logger.warning("Memory manager not found in services")
                
            if self.consciousness:
                logger.info("Consciousness service connected successfully")
            else:
                logger.warning("Consciousness service not found")
            
            # Start consciousness loop
            logger.info("Starting consciousness loop...")
            consciousness_task = asyncio.create_task(self.consciousness_loop())
            
            # Start input handler
            logger.info("Starting input handler...")
            input_task = asyncio.create_task(self.input_handler())
            
            # Start UI refresh loop
            logger.info("Starting UI refresh loop...")
            ui_refresh_task = asyncio.create_task(self.ui_refresh_loop())
            
            # Initial system messages
            self.add_system_line("Claude-AGI System v1.0 Initialized", 3)
            self.add_system_line("Type /help for commands, Tab to switch panes", 3)
            self.add_consciousness_line("💭 [PRI] Consciousness streams activating...", 1)
            
            # Show safety status
            if self.safety:
                self.add_system_line("Safety framework initialized with constraints", 2)
            else:
                self.add_system_line("Safety framework initializing...", 3)
            
            # Store tasks for cleanup
            self.tasks = [orchestrator_task, consciousness_task, input_task, ui_refresh_task]
            
            # Run until stopped
            try:
                await asyncio.gather(*self.tasks, return_exceptions=True)
            except asyncio.CancelledError:
                logger.info("Main tasks cancelled")
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
            
        except asyncio.CancelledError:
            logger.info("Async tasks cancelled")
        except Exception as e:
            logger.error(f"Runtime error: {e}")
            self.add_system_line(f"Critical error: {str(e)}", 5)
        finally:
            # Cleanup
            logger.info("Shutting down Claude-AGI...")
            self.running = False
                
    def run(self, stdscr):
        """Main run method called by curses wrapper"""
        loop = None
        try:
            self.init_ui(stdscr)
            
            # Create and run event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.run_async())
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
        finally:
            # Cancel all tasks
            if hasattr(self, 'tasks'):
                for task in self.tasks:
                    if not task.done():
                        task.cancel()
            
            # Shutdown orchestrator and other services properly
            if hasattr(self, 'orchestrator') and self.orchestrator:
                try:
                    # Create a new loop for cleanup if current is closed
                    if loop and loop.is_closed():
                        cleanup_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(cleanup_loop)
                        cleanup_loop.run_until_complete(self.orchestrator.shutdown())
                        # Also close thought generator
                        if hasattr(self, 'thought_generator') and self.thought_generator:
                            cleanup_loop.run_until_complete(self.thought_generator.close())
                        cleanup_loop.close()
                    elif loop:
                        loop.run_until_complete(self.orchestrator.shutdown())
                        # Also close thought generator
                        if hasattr(self, 'thought_generator') and self.thought_generator:
                            loop.run_until_complete(self.thought_generator.close())
                except Exception as e:
                    logger.error(f"Error during orchestrator shutdown: {e}")
            
            # Clean up curses properly
            try:
                # Reset terminal state only if stdscr is valid
                if hasattr(self, 'stdscr') and self.stdscr:
                    try:
                        self.stdscr.keypad(False)
                    except:
                        pass
                    
                # Reset terminal modes
                try:
                    curses.echo()
                    curses.nocbreak()
                except:
                    pass
                
                # Finally call endwin() - but only if not already ended
                try:
                    if not curses.isendwin():
                        curses.endwin()
                except:
                    # Force reset if normal endwin fails
                    pass  # Let curses.wrapper handle final cleanup
                
                # Clear any remaining curses state
                try:
                    import os
                    os.system('reset')  # Reset terminal as last resort
                except:
                    pass
            except Exception as e:
                # Ignore errors during cleanup
                logger.debug(f"Curses cleanup error (expected): {e}")
                
            # Close event loop properly
            if loop and not loop.is_closed():
                try:
                    # Stop the loop first to prevent new tasks
                    loop.stop()
                    
                    # Get all pending tasks
                    pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
                    for task in pending:
                        task.cancel()
                    
                    # Run once more to handle cancellations
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                except:
                    pass
                finally:
                    # Close all async generators
                    try:
                        loop.run_until_complete(loop.shutdown_asyncgens())
                    except:
                        pass
                    loop.close()
            

def main():
    """Entry point for Claude-AGI"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Claude-AGI: Advanced General Intelligence System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--config',
        default='configs/development.yaml',
        help='Path to configuration file (default: configs/development.yaml)'
    )
    parser.add_argument(
        '--setup-db',
        action='store_true',
        help='Run database setup before starting'
    )
    
    args = parser.parse_args()
    
    # Create necessary directories
    for directory in ['logs', 'data', 'archive']:
        Path(directory).mkdir(exist_ok=True)
    
    # Check environment
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("\n" + "="*60)
        print("WARNING: ANTHROPIC_API_KEY not found in environment")
        print("="*60)
        print("\nThe system will operate with limited capabilities:")
        print("- Thought generation will use templates instead of Claude AI")
        print("- Conversations will have basic responses")
        print("\nTo enable full AI capabilities:")
        print("1. Get an API key from https://console.anthropic.com/")
        print("2. Add to .env file: ANTHROPIC_API_KEY=your-key-here")
        print("\nPress Enter to continue with limited mode, or Ctrl+C to exit...")
        try:
            input()
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)
    
    # Run database setup if requested
    if args.setup_db:
        print("Running database setup...")
        setup_script = Path("scripts/setup/setup_databases.py")
        if setup_script.exists():
            import subprocess
            result = subprocess.run([sys.executable, str(setup_script)], capture_output=True, text=True)
            if result.returncode == 0:
                print("Database setup completed successfully")
            else:
                print(f"Database setup failed: {result.stderr}")
                sys.exit(1)
        else:
            print("Database setup script not found")
    
    # Validate configuration file
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Configuration file not found: {config_path}")
        print("Please ensure the configuration file exists or use --config to specify a different path")
        sys.exit(1)
    
    try:
        # Initialize and run Claude-AGI
        logger.info(f"Starting Claude-AGI with config: {args.config}")
        agi = ClaudeAGI(str(config_path))
        
        # Run with curses wrapper for terminal UI
        curses.wrapper(agi.run)
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        print("\nShutting down...")
    except curses.error as e:
        error_str = str(e)
        # Ignore common curses cleanup errors
        if not any(x in error_str for x in ['cbreak()', 'nocbreak()', 'endwin()', 'ERR']):
            logger.error(f"Curses error: {e}")
            print(f"\nDisplay error: {e}")
    except Exception as e:
        error_str = str(e)
        # Check if it's a curses-related error wrapped in another exception
        if 'curses' in error_str and any(x in error_str for x in ['cbreak()', 'nocbreak()', 'endwin()']):
            # Silently ignore curses cleanup errors
            pass
        else:
            logger.error(f"Failed to start Claude-AGI: {e}", exc_info=True)
            print(f"\nError: {e}")
            print("\nCheck logs/claude-agi.log for details")
            sys.exit(1)
    finally:
        # Clean shutdown procedures
        try:
            if 'agi' in locals():
                # Shutdown orchestrator
                if hasattr(agi, 'orchestrator') and agi.orchestrator:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(agi.orchestrator.shutdown())
                    loop.close()
                
                # Close thought generator to prevent auth warnings
                if hasattr(agi, 'thought_generator') and agi.thought_generator:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(agi.thought_generator.close())
                    loop.close()
        except:
            pass
        
        # Force terminal reset to clean state
        try:
            # Use stty sane which is more reliable than reset
            os.system('stty sane 2>/dev/null')
            # Clear the screen
            os.system('clear 2>/dev/null')
        except:
            pass
        
        # Only print shutdown message if we didn't exit due to an error
        if 'e' not in locals() or 'curses' in str(locals().get('e', '')):
            print("\nClaude-AGI shutdown complete")
        

if __name__ == "__main__":
    main()