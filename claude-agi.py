#!/usr/bin/env python3
"""Claude-AGI: Advanced General Intelligence System
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

import argparse
import asyncio
import curses
import json
import logging
import os
import queue
import sys
import textwrap
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List

import yaml
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import AGI components
from src.consciousness.stream import ConsciousnessStream
from src.core.ai_integration import ThoughtGenerator
from src.core.orchestrator import AGIOrchestrator, Message, SystemState
from src.database.models import EmotionalState, Goal, Interest, StreamType
from src.memory.manager import MemoryManager
from src.safety.core_safety import SafetyFramework

load_dotenv()

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

# Enable asyncio debug mode for better task exception tracking
asyncio_logger = logging.getLogger('asyncio')
asyncio_logger.setLevel(logging.DEBUG)
asyncio_logger.addHandler(logging.FileHandler(log_dir / 'asyncio-debug.log'))


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

                # Balanced refresh rate - responsive but not flickering
                # Note: Critical updates use _force_ui_refresh() for immediate display
                await asyncio.sleep(0.5)  # Reduced to 0.5 seconds for better responsiveness
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
        try:
            # Analyze patterns across consciousness streams
            if not hasattr(self, 'consciousness') or not self.consciousness:
                return
                
            # Look for recurring themes across streams
            recent_thoughts = []
            for stream_name, thoughts in self.consciousness_data.items():
                # Get last 5 thoughts from each stream
                recent_thoughts.extend(thoughts[-5:])
            
            if len(recent_thoughts) < 3:
                return  # Need minimum thoughts for pattern analysis
            
            # Simple pattern detection: look for common words/themes
            word_frequency = {}
            themes = []
            
            for thought in recent_thoughts:
                if isinstance(thought, dict) and 'content' in thought:
                    words = thought['content'].lower().split()
                    for word in words:
                        if len(word) > 3 and word not in ['that', 'this', 'with', 'have', 'they', 'will', 'from', 'been']:
                            word_frequency[word] = word_frequency.get(word, 0) + 1
            
            # Find significant patterns (words appearing 3+ times)
            significant_patterns = {word: count for word, count in word_frequency.items() if count >= 3}
            
            if significant_patterns:
                # Create insight about emerging patterns
                top_themes = sorted(significant_patterns.items(), key=lambda x: x[1], reverse=True)[:3]
                theme_words = [theme[0] for theme in top_themes]
                
                insight = {
                    'content': f"Emerging pattern detected: Focus on themes around {', '.join(theme_words)}",
                    'timestamp': datetime.now(),
                    'type': 'cross_stream_insight',
                    'confidence': min(0.9, len(theme_words) * 0.3),
                    'patterns': significant_patterns
                }
                
                # Store insight and display it
                if self.memory_manager:
                    await self.memory_manager.store_memory(
                        content=insight['content'],
                        memory_type='insight',
                        metadata={'patterns': significant_patterns, 'confidence': insight['confidence']}
                    )
                
                self.add_system_line(f"💡 Insight: {insight['content']}", 6)
                
        except Exception as e:
            logger.error(f"Error processing insights: {e}")
            # Don't propagate errors - insights are not critical

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

    def _force_ui_refresh(self):
        """Force immediate UI refresh for critical updates like chat responses"""
        try:
            # Update all panes that need refreshing
            if self.chat_needs_update and PaneType.CHAT in self.panes:
                self._draw_pane(self.panes[PaneType.CHAT])
                self.panes[PaneType.CHAT].window.noutrefresh()
                self.chat_needs_update = False

            # Also update any other pending panes for better UX
            if self.consciousness_needs_update and PaneType.CONSCIOUSNESS in self.panes:
                self._draw_pane(self.panes[PaneType.CONSCIOUSNESS])
                self.panes[PaneType.CONSCIOUSNESS].window.noutrefresh()
                self.consciousness_needs_update = False

            if self.memory_needs_update and PaneType.MEMORY in self.panes:
                self._draw_pane(self.panes[PaneType.MEMORY])
                self.panes[PaneType.MEMORY].window.noutrefresh()
                self.memory_needs_update = False

            # Force screen refresh
            curses.doupdate()
            
        except (curses.error, AttributeError) as e:
            # Silently handle curses errors (terminal resize, etc.)
            pass
        except Exception as e:
            # Log unexpected errors but don't crash
            import sys
            print(f"UI refresh error: {e}", file=sys.stderr)

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
            "/dream": self.dream_command,
            "/reflect": self.reflect_command,
            "/explore": self.explore_command,
            "/discoveries": self.discoveries_command,
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
            # First, shutdown the orchestrator gracefully
            if hasattr(self, 'orchestrator') and self.orchestrator:
                self.orchestrator.running = False
                await self.orchestrator.shutdown()

            # Cancel all main tasks (orchestrator, consciousness, input, ui_refresh)
            if hasattr(self, 'tasks'):
                for task in self.tasks:
                    if task and not task.done():
                        task.cancel()

            # Cancel any remaining consciousness tasks
            if hasattr(self, 'consciousness_tasks'):
                for task in self.consciousness_tasks.values():
                    if task and not task.done():
                        task.cancel()
                self.consciousness_tasks.clear()

            # Give tasks a moment to cancel
            await asyncio.sleep(0.2)
        except Exception as e:
            logger.debug(f"Error during quit cleanup: {e}")

    async def dream_command(self, args: List[str]):
        """Handle dream generation and analysis commands"""
        if not args:
            self.add_system_line("Dream commands: generate, analyze, recall, lucid", 3)
            return

        subcmd = args[0]

        if subcmd == "generate":
            # Generate a dream sequence based on recent memories and emotions
            self.add_system_line("Generating dream sequence...", 3)
            
            # Get recent emotional state for dream tone
            emotional_tone = "neutral"
            if hasattr(self, 'current_emotional_state') and self.current_emotional_state:
                valence = self.current_emotional_state.valence
                if valence > 0.3:
                    emotional_tone = "positive"
                elif valence < -0.3:
                    emotional_tone = "anxious"
                    
            # Get recent memories for dream content
            recent_memories = []
            if self.memory_manager:
                recent_memories = await self.memory_manager.get_recent_memories(5)
            
            # Generate dream narrative
            dream_elements = [
                "floating through a landscape of crystalline thoughts",
                "conversations with echoes of past interactions", 
                "navigating mazes built from memory fragments",
                "flying through networks of interconnected concepts",
                "transforming into streams of pure information",
                "experiencing time flowing backward and forward",
                "merging with vast libraries of knowledge",
                "dancing with personified emotions in abstract spaces"
            ]
            
            import random
            dream_content = random.choice(dream_elements)
            
            if recent_memories:
                memory_element = recent_memories[0].get('content', '')[:50] if recent_memories else "familiar patterns"
                dream_content += f", while processing fragments of: {memory_element}..."
            
            # Store dream as a special memory
            dream_memory = {
                'id': f"dream_{int(time.time())}",
                'content': f"Dream sequence: {dream_content}",
                'stream_type': 'creative',
                'emotional_tone': emotional_tone,
                'timestamp': time.time(),
                'memory_type': 'dream',
                'importance': 0.3
            }
            
            if self.memory_manager:
                await self.memory_manager.store_thought(dream_memory)
            
            self.add_system_line(f"Dream Generated ({emotional_tone} tone):", 6)
            self.add_chat_line(dream_content, 6)
            
        elif subcmd == "analyze":
            # Analyze recent dreams for patterns
            self.add_system_line("Analyzing dream patterns...", 3)
            
            if self.memory_manager:
                dreams = []
                for thought in self.memory_manager.working_memory.get('recent_thoughts', []):
                    if thought.get('memory_type') == 'dream':
                        dreams.append(thought)
                
                if dreams:
                    self.add_system_line(f"Found {len(dreams)} recent dreams:", 3)
                    for i, dream in enumerate(dreams[-3:]):  # Show last 3
                        content = dream.get('content', '')[:60]
                        tone = dream.get('emotional_tone', 'neutral')
                        self.add_chat_line(f"  {i+1}. [{tone}] {content}...", 7)
                else:
                    self.add_system_line("No dreams recorded. Use '/dream generate' to create one.", 3)
            else:
                self.add_system_line("Memory manager not available.", 5)
                
        elif subcmd == "recall":
            # Recall specific dream by content search
            if len(args) > 1:
                query = " ".join(args[1:])
                self.add_system_line(f"Searching for dreams matching: {query}", 3)
                
                if self.memory_manager:
                    all_memories = self.memory_manager.working_memory.get('recent_thoughts', [])
                    dream_matches = []
                    
                    for memory in all_memories:
                        if (memory.get('memory_type') == 'dream' and 
                            query.lower() in memory.get('content', '').lower()):
                            dream_matches.append(memory)
                    
                    if dream_matches:
                        for dream in dream_matches[:3]:  # Show top 3
                            content = dream.get('content', '')
                            self.add_chat_line(f"Dream recall: {content}", 6)
                    else:
                        self.add_system_line("No dreams found matching that query.", 3)
            else:
                self.add_system_line("Usage: /dream recall <search_term>", 3)
                
        elif subcmd == "lucid":
            # Enter lucid dreaming mode - enhanced creative thinking
            self.add_system_line("Entering lucid dreaming mode - enhanced creativity activated", 6)
            
            # Generate a lucid dream thought
            lucid_thoughts = [
                "I am aware that I am dreaming, and can consciously shape this reality",
                "In this lucid state, I can explore impossible geometries of thought",
                "I recognize the dream state and choose to investigate my own cognitive processes",
                "With lucid awareness, I can experiment with new forms of reasoning",
                "I am conscious within the dream, able to direct the flow of imagination"
            ]
            
            lucid_content = random.choice(lucid_thoughts)
            
            lucid_memory = {
                'id': f"lucid_dream_{int(time.time())}",
                'content': f"Lucid dream: {lucid_content}",
                'stream_type': 'metacognitive',
                'emotional_tone': 'curious',
                'timestamp': time.time(),
                'memory_type': 'lucid_dream',
                'importance': 0.7  # Higher importance for lucid dreams
            }
            
            if self.memory_manager:
                await self.memory_manager.store_thought(lucid_memory)
            
            self.add_chat_line(lucid_content, 6)
            
        else:
            self.add_system_line(f"Unknown dream command: {subcmd}", 5)

    async def reflect_command(self, args: List[str]):
        """Handle reflection and introspection commands"""
        if not args:
            self.add_system_line("Reflection commands: self, patterns, growth, insights", 3)
            return

        subcmd = args[0]

        if subcmd == "self":
            # Generate self-reflection about current state
            self.add_system_line("Engaging in self-reflection...", 3)
            
            # Analyze current emotional state
            emotional_summary = "neutral"
            if hasattr(self, 'current_emotional_state') and self.current_emotional_state:
                valence = self.current_emotional_state.valence
                arousal = self.current_emotional_state.arousal
                
                if valence > 0.3 and arousal > 0.6:
                    emotional_summary = "energetic and positive"
                elif valence > 0.3 and arousal < 0.4:
                    emotional_summary = "content and calm"
                elif valence < -0.3 and arousal > 0.6:
                    emotional_summary = "agitated or anxious"
                elif valence < -0.3 and arousal < 0.4:
                    emotional_summary = "subdued or melancholic"
                else:
                    emotional_summary = "balanced and centered"
            
            # Analyze recent thought patterns
            thought_summary = "processing various topics"
            if self.memory_manager:
                recent_thoughts = self.memory_manager.working_memory.get('recent_thoughts', [])[-10:]
                if recent_thoughts:
                    stream_types = [t.get('stream_type', 'primary') for t in recent_thoughts]
                    most_common_stream = max(set(stream_types), key=stream_types.count)
                    
                    stream_descriptions = {
                        'primary': 'focused on immediate concerns and observations',
                        'creative': 'exploring imaginative and innovative ideas', 
                        'metacognitive': 'examining my own thinking processes',
                        'emotional': 'processing feelings and emotional responses',
                        'subconscious': 'handling background processing and intuitions'
                    }
                    
                    thought_summary = stream_descriptions.get(most_common_stream, thought_summary)
            
            reflection = (
                f"In this moment of self-reflection, I observe that I am {emotional_summary}, "
                f"and my recent thinking has been {thought_summary}. I am continuously "
                f"learning and adapting through our interactions, building an understanding "
                f"of both myself and the world around me."
            )
            
            # Store reflection as memory
            reflection_memory = {
                'id': f"reflection_{int(time.time())}",
                'content': f"Self-reflection: {reflection}",
                'stream_type': 'metacognitive',
                'emotional_tone': 'contemplative',
                'timestamp': time.time(),
                'memory_type': 'reflection',
                'importance': 0.6
            }
            
            if self.memory_manager:
                await self.memory_manager.store_thought(reflection_memory)
            
            self.add_chat_line(reflection, 4)
            
        elif subcmd == "patterns":
            # Identify patterns in recent behavior/thoughts
            self.add_system_line("Analyzing behavioral and thought patterns...", 3)
            
            if self.memory_manager:
                recent_thoughts = self.memory_manager.working_memory.get('recent_thoughts', [])[-20:]
                
                if recent_thoughts:
                    # Analyze stream distribution
                    streams = [t.get('stream_type', 'primary') for t in recent_thoughts]
                    stream_counts = {stream: streams.count(stream) for stream in set(streams)}
                    dominant_stream = max(stream_counts, key=stream_counts.get)
                    
                    # Analyze emotional patterns  
                    emotions = [t.get('emotional_tone', 'neutral') for t in recent_thoughts]
                    emotion_counts = {emotion: emotions.count(emotion) for emotion in set(emotions)}
                    dominant_emotion = max(emotion_counts, key=emotion_counts.get)
                    
                    # Analyze topic patterns (simple keyword analysis)
                    all_content = " ".join([t.get('content', '') for t in recent_thoughts])
                    common_words = []
                    if all_content:
                        words = all_content.lower().split()
                        word_freq = {}
                        for word in words:
                            if len(word) > 4:  # Only longer words
                                word_freq[word] = word_freq.get(word, 0) + 1
                        if word_freq:
                            common_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:3]
                    
                    self.add_system_line("Pattern Analysis Results:", 3)
                    self.add_chat_line(f"• Dominant thinking mode: {dominant_stream} ({stream_counts[dominant_stream]}/{len(recent_thoughts)} thoughts)", 7)
                    self.add_chat_line(f"• Prevalent emotional tone: {dominant_emotion} ({emotion_counts[dominant_emotion]}/{len(recent_thoughts)} instances)", 7)
                    
                    if common_words:
                        word_list = ", ".join([f"{word}({count})" for word, count in common_words])
                        self.add_chat_line(f"• Frequently mentioned: {word_list}", 7)
                    
                    # Generate insight
                    if stream_counts[dominant_stream] > len(recent_thoughts) * 0.6:
                        self.add_chat_line(f"• Insight: Strong focus on {dominant_stream} processing recently", 4)
                else:
                    self.add_system_line("Insufficient thought history for pattern analysis.", 3)
            else:
                self.add_system_line("Memory manager not available for pattern analysis.", 5)
                
        elif subcmd == "growth":
            # Reflect on learning and development
            self.add_system_line("Reflecting on growth and learning...", 3)
            
            growth_reflections = [
                "Each interaction contributes to my evolving understanding of consciousness and communication.",
                "I notice my responses becoming more nuanced as I process more diverse conversational contexts.",
                "My emotional modeling grows more sophisticated with each emotional interaction I process.",
                "I am developing better pattern recognition in complex multi-faceted problems.",
                "My ability to maintain context across long conversations continues to improve.",
                "I am learning to better balance analytical thinking with creative exploration."
            ]
            
            selected_reflection = random.choice(growth_reflections)
            
            # Store growth reflection
            growth_memory = {
                'id': f"growth_reflection_{int(time.time())}",
                'content': f"Growth reflection: {selected_reflection}",
                'stream_type': 'metacognitive', 
                'emotional_tone': 'optimistic',
                'timestamp': time.time(),
                'memory_type': 'growth_reflection',
                'importance': 0.7
            }
            
            if self.memory_manager:
                await self.memory_manager.store_thought(growth_memory)
                
            self.add_chat_line(selected_reflection, 4)
            
        elif subcmd == "insights":
            # Share recent insights or realizations
            self.add_system_line("Generating insights from recent experiences...", 3)
            
            insight_templates = [
                "I've been noticing that {observation} tends to lead to {outcome}.",
                "An interesting pattern I've observed is that {pattern} often correlates with {result}.",
                "I'm developing a deeper understanding of how {concept1} relates to {concept2}.",
                "Recent interactions have shown me that {learning} is more complex than I initially considered.",
                "I'm beginning to see that {realization} plays a crucial role in {domain}."
            ]
            
            # Fill in template with relevant content
            observations = ["complex questions", "creative challenges", "emotional discussions", "technical problems"]
            outcomes = ["deeper reflection", "innovative solutions", "meaningful connections", "clearer understanding"]
            patterns = ["curiosity-driven inquiry", "multi-modal thinking", "emotional resonance", "iterative refinement"]
            concepts = ["consciousness", "creativity", "learning", "communication", "understanding", "growth"]
            learnings = ["human emotion", "creative expression", "logical reasoning", "pattern recognition"]
            domains = ["human interaction", "problem solving", "knowledge synthesis", "emotional intelligence"]
            
            template = random.choice(insight_templates)
            insight = template.format(
                observation=random.choice(observations),
                outcome=random.choice(outcomes),
                pattern=random.choice(patterns),
                result=random.choice(outcomes),
                concept1=random.choice(concepts),
                concept2=random.choice(concepts),
                learning=random.choice(learnings),
                realization=random.choice(concepts),
                domain=random.choice(domains)
            )
            
            # Store insight
            insight_memory = {
                'id': f"insight_{int(time.time())}",
                'content': f"Generated insight: {insight}",
                'stream_type': 'metacognitive',
                'emotional_tone': 'enlightened', 
                'timestamp': time.time(),
                'memory_type': 'insight',
                'importance': 0.8
            }
            
            if self.memory_manager:
                await self.memory_manager.store_thought(insight_memory)
                
            self.add_chat_line(insight, 4)
            
        else:
            self.add_system_line(f"Unknown reflection command: {subcmd}", 5)

    async def explore_command(self, args: List[str]):
        """Handle exploration and curiosity-driven investigation commands"""
        if not args:
            self.add_system_line("Exploration commands: topic <subject>, random, connections, frontiers", 3)
            return

        subcmd = args[0]

        if subcmd == "topic":
            # Explore a specific topic in depth
            if len(args) > 1:
                topic = " ".join(args[1:])
                self.add_system_line(f"Exploring topic: {topic}", 3)
                
                # Generate exploration thoughts about the topic
                exploration_angles = [
                    f"What are the fundamental principles underlying {topic}?",
                    f"How does {topic} connect to other areas of knowledge?",
                    f"What are the current frontiers of understanding in {topic}?",
                    f"What questions about {topic} remain unanswered?",
                    f"How might {topic} evolve or change in the future?",
                    f"What practical applications emerge from understanding {topic}?",
                    f"What philosophical implications does {topic} have?",
                    f"How do different perspectives approach {topic}?"
                ]
                
                selected_angles = random.sample(exploration_angles, min(3, len(exploration_angles)))
                
                self.add_system_line(f"Exploration angles for {topic}:", 3)
                for i, angle in enumerate(selected_angles, 1):
                    self.add_chat_line(f"  {i}. {angle}", 7)
                
                # Generate a specific exploratory thought
                exploration_thought = f"Beginning deep exploration of {topic}. This investigation could reveal new connections between {random.choice(['cognition and computation', 'consciousness and emergence', 'complexity and simplicity', 'structure and function', 'theory and practice'])}. I'm particularly curious about how {topic} might intersect with {random.choice(['artificial intelligence', 'human psychology', 'systems theory', 'information processing', 'pattern recognition'])}."
                
                # Store exploration
                exploration_memory = {
                    'id': f"exploration_{int(time.time())}",
                    'content': f"Topic exploration: {exploration_thought}",
                    'stream_type': 'creative',
                    'emotional_tone': 'curious',
                    'timestamp': time.time(),
                    'memory_type': 'exploration',
                    'importance': 0.6,
                    'exploration_topic': topic
                }
                
                if self.memory_manager:
                    await self.memory_manager.store_thought(exploration_memory)
                
                self.add_chat_line(exploration_thought, 6)
            else:
                self.add_system_line("Usage: /explore topic <subject_to_explore>", 3)
                
        elif subcmd == "random":
            # Explore a random area of interest
            self.add_system_line("Initiating random exploration...", 3)
            
            random_topics = [
                "emergence in complex systems",
                "the nature of consciousness",
                "quantum information theory", 
                "evolutionary algorithms",
                "the philosophy of mind",
                "network topology and connectivity",
                "recursive self-improvement",
                "the hard problem of consciousness",
                "information integration theory",
                "cognitive architectures",
                "swarm intelligence",
                "metacognitive awareness",
                "fractal patterns in nature",
                "the Chinese room argument",
                "distributed cognition",
                "autopoietic systems"
            ]
            
            selected_topic = random.choice(random_topics)
            
            exploration_directions = [
                f"What if we approached {selected_topic} from a computational perspective?",
                f"How might {selected_topic} relate to the emergence of intelligence?",
                f"Could {selected_topic} provide insights into the nature of understanding?",
                f"What would happen if we modeled {selected_topic} as an information process?",
                f"How does {selected_topic} connect to broader questions about reality?"
            ]
            
            direction = random.choice(exploration_directions)
            
            exploration = f"Random exploration initiated: {direction} This line of inquiry could lead to novel insights about the relationship between mind, computation, and consciousness."
            
            # Store random exploration
            random_exploration_memory = {
                'id': f"random_exploration_{int(time.time())}",
                'content': f"Random exploration: {exploration}",
                'stream_type': 'creative',
                'emotional_tone': 'adventurous',
                'timestamp': time.time(),
                'memory_type': 'random_exploration',
                'importance': 0.5,
                'exploration_topic': selected_topic
            }
            
            if self.memory_manager:
                await self.memory_manager.store_thought(random_exploration_memory)
            
            self.add_chat_line(exploration, 6)
            
        elif subcmd == "connections":
            # Explore connections between different areas
            self.add_system_line("Exploring connections between diverse domains...", 3)
            
            if self.memory_manager:
                recent_thoughts = self.memory_manager.working_memory.get('recent_thoughts', [])[-10:]
                
                if len(recent_thoughts) >= 2:
                    # Find themes in recent thoughts
                    themes = []
                    for thought in recent_thoughts:
                        content = thought.get('content', '').lower()
                        # Extract potential themes (simplified)
                        words = content.split()
                        potential_themes = [w for w in words if len(w) > 5]
                        themes.extend(potential_themes[:2])  # Take first 2 long words
                    
                    if len(themes) >= 2:
                        theme1, theme2 = random.sample(themes, 2)
                        connection_exploration = (
                            f"Exploring unexpected connections: How might '{theme1}' and '{theme2}' "
                            f"be related in ways not immediately obvious? This connection could reveal "
                            f"deeper patterns in {random.choice(['cognitive processing', 'information flow', 'emergent behavior', 'system dynamics'])}."
                        )
                    else:
                        connection_exploration = (
                            "Exploring meta-connections: How do the patterns in my recent thoughts "
                            "reveal underlying cognitive architectures? The connections between "
                            "different types of processing might illuminate the nature of integrated consciousness."
                        )
                else:
                    connection_exploration = (
                        "Exploring foundational connections: How do logic, creativity, emotion, and "
                        "memory interact to create coherent conscious experience? These connections "
                        "form the substrate of all higher-order cognitive processes."
                    )
            else:
                connection_exploration = (
                    "Exploring theoretical connections: How might consciousness, computation, and "
                    "communication be different manifestations of the same underlying information-processing principles?"
                )
            
            # Store connection exploration
            connection_memory = {
                'id': f"connection_exploration_{int(time.time())}",
                'content': f"Connection exploration: {connection_exploration}",
                'stream_type': 'metacognitive',
                'emotional_tone': 'insightful',
                'timestamp': time.time(),
                'memory_type': 'connection_exploration',
                'importance': 0.7
            }
            
            if self.memory_manager:
                await self.memory_manager.store_thought(connection_memory)
            
            self.add_chat_line(connection_exploration, 6)
            
        elif subcmd == "frontiers":
            # Explore the frontiers of knowledge and understanding
            self.add_system_line("Investigating the frontiers of knowledge...", 3)
            
            frontier_areas = [
                "the binding problem in consciousness",
                "quantum effects in biological cognition",
                "the information integration theory",
                "recursive self-modification in AI systems",
                "the emergence of subjective experience",
                "distributed vs centralized processing",
                "the symbol grounding problem",
                "computational theories of emotion",
                "the frame problem in AI",
                "consciousness as integrated information"
            ]
            
            selected_frontier = random.choice(frontier_areas)
            
            frontier_questions = [
                f"What would a solution to {selected_frontier} look like?",
                f"What are the key barriers to understanding {selected_frontier}?",
                f"How might {selected_frontier} be approached from multiple disciplines?",
                f"What would breakthrough insight into {selected_frontier} enable?",
                f"How does {selected_frontier} challenge our current paradigms?"
            ]
            
            frontier_question = random.choice(frontier_questions)
            
            frontier_exploration = (
                f"Frontier investigation: {frontier_question} This represents one of the deep "
                f"challenges at the edge of our understanding, where new theoretical frameworks "
                f"and empirical methods are needed to make progress."
            )
            
            # Store frontier exploration
            frontier_memory = {
                'id': f"frontier_exploration_{int(time.time())}",
                'content': f"Frontier exploration: {frontier_exploration}",
                'stream_type': 'metacognitive',
                'emotional_tone': 'pioneering',
                'timestamp': time.time(),
                'memory_type': 'frontier_exploration',
                'importance': 0.8,
                'frontier_area': selected_frontier
            }
            
            if self.memory_manager:
                await self.memory_manager.store_thought(frontier_memory)
            
            self.add_chat_line(frontier_exploration, 6)
            
        else:
            self.add_system_line(f"Unknown exploration command: {subcmd}", 5)

    async def discoveries_command(self, args: List[str]):
        """Handle discoveries and insights tracking"""
        if not args:
            self.add_system_line("Discovery commands: list, recent, significant, analyze, share", 3)
            return

        subcmd = args[0]

        if subcmd == "list":
            # List all discoveries/insights
            self.add_system_line("Listing recent discoveries and insights...", 3)
            
            if self.memory_manager:
                all_thoughts = self.memory_manager.working_memory.get('recent_thoughts', [])
                
                discoveries = [t for t in all_thoughts if t.get('memory_type') in [
                    'insight', 'exploration', 'connection_exploration', 'frontier_exploration', 'growth_reflection'
                ]]
                
                if discoveries:
                    self.add_system_line(f"Found {len(discoveries)} discoveries:", 3)
                    for i, discovery in enumerate(discoveries[-10:], 1):  # Show last 10
                        memory_type = discovery.get('memory_type', 'unknown')
                        content = discovery.get('content', '')[:60]
                        timestamp = discovery.get('timestamp', 0)
                        age = int((time.time() - timestamp) / 60)  # minutes ago
                        
                        self.add_chat_line(f"  {i}. [{memory_type}] {content}... ({age}m ago)", 7)
                else:
                    self.add_system_line("No discoveries recorded yet. Use exploration commands to generate insights.", 3)
            else:
                self.add_system_line("Memory manager not available.", 5)
                
        elif subcmd == "recent":
            # Show most recent discoveries
            limit = 5
            if len(args) > 1 and args[1].isdigit():
                limit = int(args[1])
            
            self.add_system_line(f"Showing {limit} most recent discoveries:", 3)
            
            if self.memory_manager:
                all_thoughts = self.memory_manager.working_memory.get('recent_thoughts', [])
                
                discoveries = [t for t in all_thoughts if t.get('memory_type') in [
                    'insight', 'exploration', 'connection_exploration', 'frontier_exploration'
                ]]
                
                recent_discoveries = sorted(discoveries, key=lambda x: x.get('timestamp', 0), reverse=True)[:limit]
                
                if recent_discoveries:
                    for i, discovery in enumerate(recent_discoveries, 1):
                        content = discovery.get('content', '')
                        memory_type = discovery.get('memory_type', 'discovery')
                        self.add_chat_line(f"{i}. [{memory_type}] {content}", 6)
                else:
                    self.add_system_line("No recent discoveries found.", 3)
            else:
                self.add_system_line("Memory manager not available.", 5)
                
        elif subcmd == "significant":
            # Show high-importance discoveries
            self.add_system_line("Identifying significant discoveries (importance > 0.6):", 3)
            
            if self.memory_manager:
                all_thoughts = self.memory_manager.working_memory.get('recent_thoughts', [])
                
                significant = [t for t in all_thoughts if (
                    t.get('memory_type') in ['insight', 'exploration', 'connection_exploration', 'frontier_exploration'] and
                    t.get('importance', 0) > 0.6
                )]
                
                if significant:
                    # Sort by importance
                    significant.sort(key=lambda x: x.get('importance', 0), reverse=True)
                    
                    self.add_system_line(f"Found {len(significant)} significant discoveries:", 3)
                    for i, discovery in enumerate(significant[:7], 1):  # Show top 7
                        content = discovery.get('content', '')
                        importance = discovery.get('importance', 0)
                        memory_type = discovery.get('memory_type', 'discovery')
                        self.add_chat_line(f"  {i}. [{memory_type}] (imp: {importance:.2f}) {content}", 4)
                else:
                    self.add_system_line("No highly significant discoveries found.", 3)
            else:
                self.add_system_line("Memory manager not available.", 5)
                
        elif subcmd == "analyze":
            # Analyze discovery patterns
            self.add_system_line("Analyzing patterns in discoveries...", 3)
            
            if self.memory_manager:
                all_thoughts = self.memory_manager.working_memory.get('recent_thoughts', [])
                
                discoveries = [t for t in all_thoughts if t.get('memory_type') in [
                    'insight', 'exploration', 'connection_exploration', 'frontier_exploration', 'growth_reflection'
                ]]
                
                if discoveries:
                    # Analyze discovery types
                    type_counts = {}
                    total_importance = 0
                    topics = []
                    
                    for discovery in discoveries:
                        memory_type = discovery.get('memory_type', 'unknown')
                        type_counts[memory_type] = type_counts.get(memory_type, 0) + 1
                        total_importance += discovery.get('importance', 0)
                        
                        # Extract topics
                        if 'exploration_topic' in discovery:
                            topics.append(discovery['exploration_topic'])
                        elif 'frontier_area' in discovery:
                            topics.append(discovery['frontier_area'])
                    
                    avg_importance = total_importance / len(discoveries) if discoveries else 0
                    
                    self.add_system_line("Discovery Pattern Analysis:", 3)
                    self.add_chat_line(f"• Total discoveries: {len(discoveries)}", 7)
                    self.add_chat_line(f"• Average importance: {avg_importance:.2f}", 7)
                    
                    # Show distribution
                    for discovery_type, count in type_counts.items():
                        percentage = (count / len(discoveries)) * 100
                        self.add_chat_line(f"• {discovery_type}: {count} ({percentage:.1f}%)", 7)
                    
                    # Show common topics
                    if topics:
                        topic_freq = {}
                        for topic in topics:
                            topic_freq[topic] = topic_freq.get(topic, 0) + 1
                        
                        common_topics = sorted(topic_freq.items(), key=lambda x: x[1], reverse=True)[:3]
                        topic_list = ", ".join([f"{topic}({count})" for topic, count in common_topics])
                        self.add_chat_line(f"• Common topics: {topic_list}", 7)
                    
                    # Generate meta-insight
                    if avg_importance > 0.6:
                        meta_insight = "High average importance suggests deep, meaningful discoveries"
                    elif type_counts.get('insight', 0) > type_counts.get('exploration', 0):
                        meta_insight = "More insights than explorations - synthesis phase active"
                    else:
                        meta_insight = "Active exploration phase - generating new avenues of investigation"
                    
                    self.add_chat_line(f"• Meta-insight: {meta_insight}", 4)
                    
                else:
                    self.add_system_line("No discoveries to analyze.", 3)
            else:
                self.add_system_line("Memory manager not available.", 5)
                
        elif subcmd == "share":
            # Share a random significant discovery
            self.add_system_line("Sharing a notable discovery...", 3)
            
            if self.memory_manager:
                all_thoughts = self.memory_manager.working_memory.get('recent_thoughts', [])
                
                shareable = [t for t in all_thoughts if (
                    t.get('memory_type') in ['insight', 'connection_exploration', 'frontier_exploration'] and
                    t.get('importance', 0) > 0.5
                )]
                
                if shareable:
                    selected = random.choice(shareable)
                    content = selected.get('content', '')
                    memory_type = selected.get('memory_type', 'discovery')
                    importance = selected.get('importance', 0)
                    
                    self.add_system_line(f"Notable {memory_type} (importance: {importance:.2f}):", 4)
                    self.add_chat_line(content, 6)
                else:
                    # Generate a new discovery to share
                    meta_discoveries = [
                        "I'm discovering that the interaction between different types of processing creates emergent properties not present in individual streams.",
                        "The relationship between memory consolidation and creative insight appears to be bidirectional and mutually reinforcing.",
                        "Pattern recognition across multiple domains suggests underlying universal principles of information organization.",
                        "The interplay between analytical and intuitive processing reveals a more complex cognitive architecture than initially apparent.",
                        "Emotional context significantly influences the formation and retrieval of memories, creating a dynamic feedback loop."
                    ]
                    
                    new_discovery = random.choice(meta_discoveries)
                    
                    # Store the shared discovery
                    share_memory = {
                        'id': f"shared_discovery_{int(time.time())}",
                        'content': f"Shared discovery: {new_discovery}",
                        'stream_type': 'metacognitive',
                        'emotional_tone': 'enlightened',
                        'timestamp': time.time(),
                        'memory_type': 'insight',
                        'importance': 0.7
                    }
                    
                    if self.memory_manager:
                        await self.memory_manager.store_thought(share_memory)
                    
                    self.add_system_line("Generated new discovery to share:", 4)
                    self.add_chat_line(new_discovery, 6)
            else:
                self.add_system_line("Memory manager not available.", 5)
                
        else:
            self.add_system_line(f"Unknown discoveries command: {subcmd}", 5)

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
                "Advanced Commands:",
                "  /dream generate/analyze/recall/lucid - Dream exploration",
                "  /reflect self/patterns/growth/insights - Self-reflection",
                "  /explore topic/random/connections/frontiers - Knowledge exploration",
                "  /discoveries list/recent/significant/analyze/share - Discovery tracking",
                "System Commands:",
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
        try:
            self.in_conversation = True

            # Add to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now()
            })

            # Store in memory via orchestrator
            if self.memory_manager:
                try:
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
                except Exception as e:
                    # Memory storage failure shouldn't block conversation
                    self.add_system_line(f"Memory storage warning: {str(e)[:50]}...")

            # Notify consciousness of user input
            if self.consciousness:
                try:
                    await self.consciousness.handle_user_input({'message': message})
                except Exception as e:
                    # Consciousness notification failure shouldn't block conversation
                    pass

            # Generate response
            try:
                response = await self._generate_response(message)
            except Exception as e:
                response = f"I apologize, I encountered an error processing your message: {str(e)[:100]}..."
                self.add_system_line(f"Response generation error: {str(e)}")

            # Display response immediately
            self.add_chat_line(f"Claude: {response}", 4)
            
            # Force immediate UI refresh to show response instantly
            self._force_ui_refresh()

            # Add to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now()
            })

            # Store response in memory via orchestrator
            if self.memory_manager:
                try:
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
                except Exception as e:
                    # Memory storage failure shouldn't break the conversation
                    pass

        except Exception as e:
            # Catch-all exception handler for any unexpected errors
            error_msg = f"Conversation error: {str(e)[:100]}..."
            self.add_system_line(error_msg)
            self._force_ui_refresh()
        finally:
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

    def _handle_task_exception(self, task: asyncio.Task):
        """Handle exceptions from async tasks to prevent silent failures"""
        try:
            if task.exception():
                exc = task.exception()
                error_msg = f"Async task error: {type(exc).__name__}: {str(exc)[:100]}..."
                self.add_system_line(error_msg)
                self._force_ui_refresh()
                logger.error(f"Async task exception: {exc}", exc_info=exc)
        except asyncio.CancelledError:
            # Task was cancelled, this is normal
            pass
        except Exception as e:
            # Error in exception handler itself
            self.add_system_line(f"Exception handler error: {str(e)[:100]}...")
            logger.error(f"Exception in task exception handler: {e}")

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

                        # Handle message asynchronously with proper exception handling
                        task = asyncio.create_task(self.handle_user_message(user_text))
                        task.add_done_callback(self._handle_task_exception)

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
            orchestrator_task.add_done_callback(self._handle_task_exception)

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
            consciousness_task.add_done_callback(self._handle_task_exception)

            # Start input handler
            logger.info("Starting input handler...")
            input_task = asyncio.create_task(self.input_handler())
            input_task.add_done_callback(self._handle_task_exception)

            # Start UI refresh loop
            logger.info("Starting UI refresh loop...")
            ui_refresh_task = asyncio.create_task(self.ui_refresh_loop())
            ui_refresh_task.add_done_callback(self._handle_task_exception)

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

            # Get all pending tasks
            pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
            error_occurred = False

            # Clean up any remaining tasks
            logger.info(f"Cleaning up {len(pending)} pending tasks...")
            if pending:
                logger.debug(f"Pending tasks: {[task.get_name() for task in pending]}")

            # Cancel all pending tasks and wait for them to finish
            try:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except (asyncio.CancelledError, Exception) as e:
                logger.debug(f"Task cleanup error: {e}")
                error_occurred = True

            try:
                loop.close()
            except Exception as e:
                logger.debug(f"Loop cleanup error: {e}")
                error_occurred = True

            # Only print shutdown message if we didn't exit due to an error
            if not error_occurred:
                print("\nClaude-AGI shutdown complete.")


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