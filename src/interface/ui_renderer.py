"""
UI Renderer for Claude-AGI TUI
==============================

Handles all visual rendering for the terminal user interface including:
- Pane layout and drawing
- Content formatting and display
- Color management
- Screen refresh coordination
"""

import curses
import textwrap
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

from ..database.models import EmotionalState, Goal
from ..database.models import StreamType


class PaneType(Enum):
    """Types of UI panes"""
    CONSCIOUSNESS = "consciousness"
    MEMORY = "memory"
    EMOTIONAL = "emotional"
    GOALS = "goals"
    CHAT = "chat"
    STATUS = "status"
    INPUT = "input"


@dataclass
class Pane:
    """UI Pane configuration"""
    type: PaneType
    x: int
    y: int
    width: int
    height: int
    title: str
    buffer: List[str]
    content: List[Any] = None  # For colored content (List[Tuple[str, int]])
    win: Any = None
    active: bool = False
    
    def __post_init__(self):
        """Initialize content list if not provided"""
        if self.content is None:
            self.content = []


class UIRenderer:
    """
    Handles all UI rendering for Claude-AGI TUI
    
    Responsibilities:
    - Pane layout management
    - Content rendering and formatting
    - Color scheme management
    - Screen updates and refreshing
    """
    
    def __init__(self, stdscr):
        """Initialize UI renderer with curses screen"""
        self.stdscr = stdscr
        self.height, self.width = stdscr.getmaxyx()
        
        # UI Configuration
        self.panes: Dict[PaneType, Pane] = {}
        self.layout_mode = "standard"  # standard, memory_focus, emotional_focus
        self.max_lines = 100
        
        # Display state
        self.consciousness_needs_update = False
        self.chat_needs_update = False
        
        # Scrolling state
        self.scroll_positions: Dict[PaneType, int] = {}
        # Initialize scroll positions to 0 (bottom)
        for pane_type in PaneType:
            if pane_type not in [PaneType.STATUS, PaneType.INPUT]:
                self.scroll_positions[pane_type] = 0
        
        # Initialize UI components
        self._init_colors()
        self._create_panes()
        
    def _init_colors(self):
        """Initialize color pairs for the UI - exact match to original claude-agi.py"""
        curses.start_color()
        curses.use_default_colors()
        
        # Define color pairs - EXACT MATCH to original
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)     # Thoughts
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)    # User input
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)   # System
        curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # Claude
        curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)      # Alerts
        curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLUE)     # Headers
        curses.init_pair(7, curses.COLOR_BLUE, curses.COLOR_BLACK)     # Memory
        curses.init_pair(8, curses.COLOR_WHITE, curses.COLOR_BLACK)    # Normal
        
    def _create_panes(self):
        """Create UI panes based on current layout mode"""
        if self.layout_mode == "memory_focus":
            self._create_memory_focus_layout()
        elif self.layout_mode == "emotional_focus":
            self._create_emotional_focus_layout()
        else:
            self._create_standard_layout()
    
    def _create_standard_layout(self):
        """Create the standard 3x2 layout"""
        self.panes.clear()
        
        # Calculate dimensions
        pane_width = self.width // 3
        pane_height = (self.height - 4) // 2  # Leave space for status and input
        
        # Top row
        self.panes[PaneType.CONSCIOUSNESS] = Pane(
            type=PaneType.CONSCIOUSNESS,
            x=0, y=0,
            width=pane_width, height=pane_height,
            title="▶ Consciousness Stream ◀" if PaneType.CONSCIOUSNESS == self._get_active_pane() else "Consciousness Stream",
            buffer=[]
        )
        
        self.panes[PaneType.MEMORY] = Pane(
            type=PaneType.MEMORY,
            x=pane_width, y=0,
            width=pane_width, height=pane_height,
            title="▶ Memory Browser ◀" if PaneType.MEMORY == self._get_active_pane() else "Memory Browser",
            buffer=[]
        )
        
        self.panes[PaneType.EMOTIONAL] = Pane(
            type=PaneType.EMOTIONAL,
            x=pane_width * 2, y=0,
            width=self.width - (pane_width * 2), height=pane_height,
            title="▶ Emotional State ◀" if PaneType.EMOTIONAL == self._get_active_pane() else "Emotional State",
            buffer=[]
        )
        
        # Bottom row
        self.panes[PaneType.GOALS] = Pane(
            type=PaneType.GOALS,
            x=0, y=pane_height,
            width=pane_width, height=pane_height,
            title="▶ Goals & Interests ◀" if PaneType.GOALS == self._get_active_pane() else "Goals & Interests",
            buffer=[]
        )
        
        self.panes[PaneType.CHAT] = Pane(
            type=PaneType.CHAT,
            x=pane_width, y=pane_height,
            width=self.width - pane_width, height=pane_height,
            title="▶ Conversation ◀" if PaneType.CHAT == self._get_active_pane() else "Conversation",
            buffer=[]
        )
        
        # Create windows for all panes
        for pane in self.panes.values():
            pane.win = curses.newwin(pane.height, pane.width, pane.y, pane.x)
            # Enable scrolling and keypad for panes
            pane.win.scrollok(True)
            pane.win.idlok(True)  # Enable line insertion/deletion
            pane.win.keypad(True)  # Enable keypad for scrolling
    
    def _create_memory_focus_layout(self):
        """Create memory-focused layout with larger memory pane"""
        self.panes.clear()
        
        # Memory takes up 60% width
        memory_width = int(self.width * 0.6)
        side_width = (self.width - memory_width) // 2
        pane_height = (self.height - 4) // 2
        
        # Large memory pane on left
        self.panes[PaneType.MEMORY] = Pane(
            type=PaneType.MEMORY,
            x=0, y=0,
            width=memory_width, height=self.height - 4,
            title="▶ Memory Browser (Focus) ◀",
            buffer=[]
        )
        
        # Smaller panes on right
        self.panes[PaneType.CONSCIOUSNESS] = Pane(
            type=PaneType.CONSCIOUSNESS,
            x=memory_width, y=0,
            width=side_width, height=pane_height,
            title="Consciousness",
            buffer=[]
        )
        
        self.panes[PaneType.CHAT] = Pane(
            type=PaneType.CHAT,
            x=memory_width, y=pane_height,
            width=side_width, height=pane_height,
            title="Chat",
            buffer=[]
        )
        
        self.panes[PaneType.EMOTIONAL] = Pane(
            type=PaneType.EMOTIONAL,
            x=memory_width + side_width, y=0,
            width=self.width - memory_width - side_width, height=pane_height,
            title="Emotional",
            buffer=[]
        )
        
        self.panes[PaneType.GOALS] = Pane(
            type=PaneType.GOALS,
            x=memory_width + side_width, y=pane_height,
            width=self.width - memory_width - side_width, height=pane_height,
            title="Goals",
            buffer=[]
        )
        
        # Create windows
        for pane in self.panes.values():
            pane.win = curses.newwin(pane.height, pane.width, pane.y, pane.x)
    
    def _create_emotional_focus_layout(self):
        """Create emotion-focused layout with larger emotional pane"""
        self.panes.clear()
        
        # Emotional takes up top half
        emotional_height = (self.height - 4) // 2
        bottom_height = (self.height - 4) - emotional_height
        side_width = self.width // 3
        
        # Large emotional pane on top
        self.panes[PaneType.EMOTIONAL] = Pane(
            type=PaneType.EMOTIONAL,
            x=0, y=0,
            width=self.width, height=emotional_height,
            title="▶ Emotional State (Focus) ◀",
            buffer=[]
        )
        
        # Bottom row with smaller panes
        self.panes[PaneType.CONSCIOUSNESS] = Pane(
            type=PaneType.CONSCIOUSNESS,
            x=0, y=emotional_height,
            width=side_width, height=bottom_height,
            title="Consciousness",
            buffer=[]
        )
        
        self.panes[PaneType.MEMORY] = Pane(
            type=PaneType.MEMORY,
            x=side_width, y=emotional_height,
            width=side_width, height=bottom_height,
            title="Memory",
            buffer=[]
        )
        
        self.panes[PaneType.CHAT] = Pane(
            type=PaneType.CHAT,
            x=side_width * 2, y=emotional_height,
            width=self.width - (side_width * 2), height=bottom_height,
            title="Chat",
            buffer=[]
        )
        
        # Goals integrated into emotional pane - no separate goals pane
        
        # Create windows
        for pane in self.panes.values():
            pane.win = curses.newwin(pane.height, pane.width, pane.y, pane.x)
    
    def _get_active_pane(self) -> PaneType:
        """Get currently active pane type"""
        # This will be set by the controller
        return getattr(self, 'current_focus', PaneType.CHAT)
    
    def set_active_pane(self, pane_type: PaneType):
        """Set the active pane and update titles"""
        self.current_focus = pane_type
        # Update pane titles to reflect active state
        for ptype, pane in self.panes.items():
            if ptype == pane_type:
                # Add active indicators to title
                if "▶" not in pane.title:
                    pane.title = f"▶ {pane.title.strip()} ◀"
            else:
                # Remove active indicators
                pane.title = pane.title.replace("▶ ", "").replace(" ◀", "")
    
    def set_layout_mode(self, mode: str):
        """Change layout mode and recreate panes"""
        self.layout_mode = mode
        self._create_panes()
    
    def draw_all_panes(self):
        """Draw all panes and their content"""
        for pane in self.panes.values():
            self._draw_pane(pane)
    
    def draw_pane(self, pane: Pane):
        """Public interface to draw a single pane - EXACT original behavior"""
        self._draw_pane(pane)
    
    def _draw_pane(self, pane: Pane):
        """Draw a single pane with border and content - EXACT MATCH to original"""
        if not pane.win:
            return
            
        try:
            pane.win.clear()
            
            # Draw border with highlighting for active pane - EXACT MATCH
            if pane.type == self._get_active_pane():
                pane.win.attron(curses.color_pair(6) | curses.A_BOLD)
            pane.win.box()
            if pane.type == self._get_active_pane():
                pane.win.attroff(curses.color_pair(6) | curses.A_BOLD)
            
            # Draw title with active indicator - EXACT MATCH
            title = f" {pane.title.replace('▶ ', '').replace(' ◀', '')} "
            if pane.type == self._get_active_pane():
                title = f"▶ {pane.title.replace('▶ ', '').replace(' ◀', '')} ◀"
                title_attr = curses.color_pair(6) | curses.A_BOLD | curses.A_REVERSE
            else:
                title_attr = curses.color_pair(6)
            
            self.safe_addstr(pane.win, 0, 2, title, title_attr)
            
            # Show scroll indicator if needed (EXACT original)
            if pane.type in self.scroll_positions:
                scroll_pos = self.scroll_positions.get(pane.type, 0)
                if scroll_pos > 0:
                    self.safe_addstr(pane.win, 0, pane.width - 10, f" ↑{scroll_pos} ", curses.color_pair(3))
            
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
                
        except curses.error:
            # Ignore curses errors during drawing
            pass
    
    def _draw_consciousness_content(self, pane: Pane):
        """Draw consciousness stream content with stream indicators (EXACT original)"""
        win = pane.win
        height, width = win.getmaxyx()

        # Use content attribute for consciousness (colored content), fallback to buffer for compatibility
        content_source = pane.content if pane.content else pane.buffer

        # Get scroll position (EXACT original logic)
        scroll_pos = self.scroll_positions.get(PaneType.CONSCIOUSNESS, 0)
        total_lines = len(content_source)

        # Calculate visible range (EXACT original)
        if total_lines > height - 2:
            # Ensure scroll position is valid
            max_scroll = total_lines - (height - 2)
            scroll_pos = min(scroll_pos, max_scroll)
            start_idx = total_lines - (height - 2) - scroll_pos
            end_idx = total_lines - scroll_pos
        else:
            start_idx = 0
            end_idx = total_lines

        # Draw visible thoughts (EXACT original)
        y = 1
        for i in range(start_idx, end_idx):
            if y >= height - 1:
                break
            if i >= len(content_source):
                break
                
            line = content_source[i]
            if isinstance(line, tuple):
                text, color = line
            else:
                text = str(line)
                color = 1  # Default consciousness color
                
            # Display text (already wrapped by add_consciousness_line, don't double-truncate)
            # Only truncate if text is still too long (safety check for edge cases)
            available_width = width - 3  # Leave 1 char margin on right
            if len(text) > available_width:
                text = text[:available_width-1] + "…"
            self.safe_addstr(win, y, 2, text, curses.color_pair(color))
            y += 1

        # Show scroll indicators (EXACT original)
        if scroll_pos > 0:
            self.safe_addstr(win, height-1, width-15, f"↓ {scroll_pos} more", curses.color_pair(3))
        if start_idx > 0:
            self.safe_addstr(win, 1, width-15, f"↑ {start_idx} above", curses.color_pair(3))
    
    def _draw_memory_content(self, pane: Pane):
        """Optimized memory browser with Rust-inspired safety patterns and performance optimizations"""
        win = pane.win
        height, width = win.getmaxyx()
        
        # Bounds validation (Rust-inspired safety)
        if height < 3 or width < 10:
            return
        
        y = 1
        
        try:
            # Use updated memory stats from controller if available, otherwise fall back to direct access
            if hasattr(self, '_memory_stats') and self._memory_stats:
                working_count = self._memory_stats.get('working_count', 0)
                long_term_count = self._memory_stats.get('episodic_count', 0) + self._memory_stats.get('semantic_count', 0)
            else:
                # Fallback to direct access (performance optimization)
                memory_manager = self._get_cached_memory_manager()
                working_count, long_term_count = self._get_memory_stats(memory_manager)
            
            # Sanitized stats display (security hardening)
            stats_text = self._format_safe_text(f"Working: {working_count} | Long-term: {long_term_count}", width - 6)
            self.safe_addstr(win, y, 2, stats_text, curses.color_pair(3))
            y += 1
            
            # Separator with bounds checking
            separator_width = max(0, min(width - 6, 50))  # Limit separator length
            self.safe_addstr(win, y, 2, "─" * separator_width, curses.color_pair(8))
            y += 2

            # Optimized category rendering
            categories = [
                ("Recent Thoughts", curses.color_pair(7)),
                ("Important Memories", curses.color_pair(4)), 
                ("Emotional Memories", curses.color_pair(5)),
                ("Goals & Achievements", curses.color_pair(2))
            ]

            # Safe height calculation with bounds checking
            remaining_height = max(0, height - y - 2)
            section_height = self._calculate_safe_section_height(remaining_height, len(categories))

            # Render categories with optimized loops
            for category_name, color in categories:
                if y >= height - 2:  # Bounds check before rendering
                    break
                
                y = self._render_category_section(win, category_name, color, y, section_height, width, height, pane)
                
        except curses.error:
            pass  # Graceful curses error handling
        except (AttributeError, TypeError, ValueError) as e:
            # Enhanced error handling for data corruption
            logger.warning(f"Memory content rendering error: {e}")
    
    def _get_cached_memory_manager(self):
        """Cached memory manager access with validation (Rust-inspired Option pattern)"""
        # Single validation chain instead of repeated hasattr() calls
        if (hasattr(self, 'controller') and self.controller and 
            hasattr(self.controller, 'memory_manager') and self.controller.memory_manager):
            return self.controller.memory_manager
        return None
    
    def _get_memory_stats(self, memory_manager) -> tuple[int, int]:
        """Safe memory statistics extraction with bounds validation"""
        working_count = 0
        long_term_count = 0
        
        if memory_manager:
            try:
                # Working memory with type validation
                if hasattr(memory_manager, 'working_memory') and isinstance(memory_manager.working_memory, dict):
                    recent_thoughts = memory_manager.working_memory.get('recent_thoughts', [])
                    working_count = len(recent_thoughts) if isinstance(recent_thoughts, (list, tuple)) else 0
                
                # Long-term memory with bounds checking
                if hasattr(memory_manager, 'long_term_memory'):
                    long_term = memory_manager.long_term_memory
                    long_term_count = len(long_term) if hasattr(long_term, '__len__') else 0
                    
            except (AttributeError, TypeError):
                pass  # Fail safe with defaults
        
        return working_count, long_term_count
    
    def _format_safe_text(self, text: str, max_width: int) -> str:
        """Secure text formatting with sanitization and proper text wrapping like original"""
        if not isinstance(text, str):
            text = str(text)
        
        # Input sanitization (remove control characters except printable)
        sanitized = ''.join(char if char.isprintable() or char in '\n\t' else '?' for char in text)
        
        # Use proper text wrapping like original instead of aggressive truncation
        if len(sanitized) > max_width and max_width > 10:  # Only truncate if very narrow
            # Use textwrap for better formatting like original
            import textwrap
            wrapped = textwrap.wrap(sanitized, max_width, break_long_words=False)
            return wrapped[0] if wrapped else sanitized[:max_width]
        return sanitized[:max_width] if max_width > 0 else ""
    
    def _calculate_safe_section_height(self, remaining_height: int, category_count: int) -> int:
        """Safe section height calculation with validation"""
        if category_count <= 0:
            return 3
        
        if remaining_height < category_count * 3:
            return 3
        return max(4, remaining_height // category_count)
    
    def _render_category_section(self, win, category_name: str, color: int, y: int, 
                                section_height: int, width: int, height: int, pane: Pane) -> int:
        """Optimized category section rendering with security validation"""
        section_start_y = y
        
        # Bounds validation before clearing
        clear_end = min(y + section_height, height - 1)
        if clear_end > y:
            # Safe area clearing with bounds checking
            clear_width = max(0, width - 4)
            for clear_y in range(y, clear_end):
                if clear_y < height - 1:
                    self.safe_addstr(win, clear_y, 2, " " * clear_width, curses.color_pair(8))

        # Sanitized category header
        safe_category = self._format_safe_text(category_name, width - 6)
        self.safe_addstr(win, y, 2, f"▼ {safe_category}", color | curses.A_BOLD)
        y += 1

        # Content rendering with specific handlers
        content_lines = max(0, section_height - 2)
        lines_used = self._render_category_content(win, category_name, y, content_lines, width, pane)
        
        # Fill remaining space safely
        max_fill_y = min(section_start_y + section_height - 1, height - 1)
        while y + lines_used < max_fill_y and lines_used < content_lines - 1:
            self.safe_addstr(win, y + lines_used, 4, "• (no entries)", curses.color_pair(8))
            lines_used += 1

        return section_start_y + section_height
    
    def _render_category_content(self, win, category: str, y: int, content_lines: int, width: int, pane: Pane) -> int:
        """Category-specific content rendering with security validation"""
        lines_used = 0
        
        if category == "Recent Thoughts":
            lines_used = self._render_recent_thoughts(win, y, content_lines, width, pane)
        elif category == "Important Memories":
            self.safe_addstr(win, y, 4, "• High-importance thoughts archived", curses.color_pair(8))
            lines_used = 1
        elif category == "Emotional Memories":
            lines_used = self._render_emotional_memories(win, y, content_lines, width)
        elif category == "Goals & Achievements":
            lines_used = self._render_goals_achievements(win, y, content_lines, width)
        
        return lines_used
    
    def _render_recent_thoughts(self, win, y: int, content_lines: int, width: int, pane: Pane) -> int:
        """Render recent thoughts from memory manager like original"""
        lines_used = 0
        
        # Get recent thoughts from memory manager (EXACT original pattern)
        recent_thoughts = []
        memory_manager = self._get_cached_memory_manager()
        if memory_manager and hasattr(memory_manager, 'working_memory'):
            if isinstance(memory_manager.working_memory, dict):
                thoughts = memory_manager.working_memory.get('recent_thoughts', [])
                if isinstance(thoughts, (list, tuple)):
                    recent_thoughts = list(thoughts)[-5:]  # Last 5 thoughts like original
        
        if recent_thoughts:
            for thought in recent_thoughts:
                if lines_used >= content_lines:
                    break
                
                # Extract content from thought structure (EXACT original pattern)
                if isinstance(thought, dict):
                    content = thought.get('content', '')
                    stream = thought.get('stream', 'unk')
                    
                    # Format like original with stream indicator
                    stream_prefix = stream[:3].upper()
                    safe_content = self._format_safe_text(str(content), width - 16)
                    display_text = f"  • [{stream_prefix}] {safe_content}"
                else:
                    # Handle string thoughts
                    safe_content = self._format_safe_text(str(thought), width - 12)
                    display_text = f"  • [THT] {safe_content}"
                
                self.safe_addstr(win, y + lines_used, 2, display_text, curses.color_pair(8))
                lines_used += 1
        
        if lines_used == 0:
            self.safe_addstr(win, y, 4, "• No recent thoughts recorded", curses.color_pair(8))
            lines_used = 1
            
        return lines_used
    
    def _render_emotional_memories(self, win, y: int, content_lines: int, width: int) -> int:
        """Render emotional memories with validation"""
        try:
            controller = getattr(self, 'controller', None)
            if (controller and hasattr(controller, 'emotional_history') and 
                len(controller.emotional_history) > 0):
                
                recent_emotion = controller.emotional_history[-1]
                # Validate numeric values
                valence = getattr(recent_emotion, 'valence', 0.0)
                arousal = getattr(recent_emotion, 'arousal', 0.0)
                
                # Bounds checking for emotional values
                valence = max(-1.0, min(1.0, float(valence)))
                arousal = max(0.0, min(1.0, float(arousal)))
                
                emotion_text = f"• Latest: V:{valence:+.2f} A:{arousal:.2f}"
                self.safe_addstr(win, y, 4, emotion_text, curses.color_pair(8))
                return 1
        except (AttributeError, ValueError, TypeError):
            pass  # Fail safe
        
        self.safe_addstr(win, y, 4, "• No emotional data recorded", curses.color_pair(8))
        return 1
    
    def _render_goals_achievements(self, win, y: int, content_lines: int, width: int) -> int:
        """Render goals and achievements with validation"""
        try:
            controller = getattr(self, 'controller', None)
            if (controller and hasattr(controller, 'completed_goals') and 
                controller.completed_goals):
                
                last_goal = controller.completed_goals[-1]
                goal_desc = getattr(last_goal, 'description', str(last_goal))
                
                # Secure text handling with bounds validation
                safe_desc = self._format_safe_text(goal_desc, width - 12)
                goal_text = f"• ✓ {safe_desc}"
                
                self.safe_addstr(win, y, 4, goal_text, curses.color_pair(8))
                return 1
        except (AttributeError, TypeError, IndexError):
            pass  # Fail safe
        
        self.safe_addstr(win, y, 4, "• No completed goals yet", curses.color_pair(8))
        return 1
    
    def _draw_emotional_content(self, pane: Pane):
        """Draw emotional state content with visualization (EXACT original)"""
        win = pane.win
        height, width = win.getmaxyx()
        
        y = 1
        
        # Current emotional state (EXACT original format)
        if hasattr(self, '_current_valence') and hasattr(self, '_current_arousal'):
            valence = self._current_valence
            arousal = self._current_arousal
            
            # Emotional state display with emojis (EXACT original)
            self.safe_addstr(win, y, 2, "💭 Current Emotional State:", curses.color_pair(4))
            y += 1
            
            # Valence with visual indicator
            valence_indicator = "😊" if valence > 0 else "😔" if valence < 0 else "😐"
            self.safe_addstr(win, y, 2, f"{valence_indicator} Valence: {valence:.2f}", curses.color_pair(8))
            y += 1
            
            # Arousal with visual indicator  
            arousal_indicator = "⚡" if arousal > 0.7 else "🔥" if arousal > 0.4 else "😴"
            self.safe_addstr(win, y, 2, f"{arousal_indicator} Arousal: {arousal:.2f}", curses.color_pair(8))
            y += 2
        
        # Emotional history (EXACT original)
        if y < height - 3 and hasattr(self, '_emotional_history'):
            self.safe_addstr(win, y, 2, "📊 Recent Changes:", curses.color_pair(4))
            y += 1
            
            history = getattr(self, '_emotional_history', [])
            recent_history = list(history)[-5:]  # Last 5 entries
            
            for entry in recent_history:
                if y >= height - 1:
                    break
                    
                if hasattr(entry, 'valence') and hasattr(entry, 'arousal'):
                    # Format emotional state entry
                    text = f"V:{entry.valence:.1f} A:{entry.arousal:.1f}"
                else:
                    text = str(entry)[:width-4]
                
                # Truncate with ellipsis
                available_width = width - 4
                if len(text) > available_width:
                    text = text[:available_width-1] + "…"
                    
                self.safe_addstr(win, y, 2, text, curses.color_pair(4))
                y += 1
    
    def _draw_goals_content(self, pane: Pane):
        """Draw goals and interests content (EXACT original)"""
        win = pane.win
        height, width = win.getmaxyx()
        
        y = 1
        
        # Active goals section (EXACT original format)
        active_count = 0
        completed_count = 0
        
        if hasattr(self, '_active_goals') and hasattr(self, '_completed_goals'):
            active_goals = getattr(self, '_active_goals', [])
            completed_goals = getattr(self, '_completed_goals', [])
            active_count = len(active_goals)
            completed_count = len(completed_goals)
        
        # Goals statistics (EXACT original)
        self.safe_addstr(win, y, 2, "🎯 Goals Overview:", curses.color_pair(3))
        y += 1
        self.safe_addstr(win, y, 2, f"Active: {active_count}", curses.color_pair(8))
        y += 1
        self.safe_addstr(win, y, 2, f"Completed: {completed_count}", curses.color_pair(8))
        y += 2
        
        # Show active goals (EXACT original)
        if hasattr(self, '_active_goals') and y < height - 3:
            active_goals = getattr(self, '_active_goals', [])
            if active_goals:
                self.safe_addstr(win, y, 2, "📋 Current Goals:", curses.color_pair(3))
                y += 1
                
                for goal in active_goals[:min(3, height - y - 1)]:
                    if y >= height - 1:
                        break
                        
                    # Extract goal description
                    if hasattr(goal, 'description'):
                        text = goal.description
                    elif hasattr(goal, 'content'):
                        text = goal.content
                    else:
                        text = str(goal)
                    
                    # Truncate with ellipsis (EXACT original)
                    available_width = width - 6
                    if len(text) > available_width:
                        text = text[:available_width-1] + "…"
                    
                    self.safe_addstr(win, y, 2, f"• {text}", curses.color_pair(8))
                    y += 1
        
        # Show recent goal activities from buffer
        if y < height - 2 and pane.buffer:
            remaining_lines = height - y - 1
            recent_entries = pane.buffer[-remaining_lines:] if len(pane.buffer) > remaining_lines else pane.buffer
            
            for entry in recent_entries:
                if y >= height - 1:
                    break
                    
                if isinstance(entry, tuple):
                    text, color = entry
                else:
                    text = str(entry)
                    color = 3
                
                # Truncate with ellipsis
                available_width = width - 4
                if len(text) > available_width:
                    text = text[:available_width-1] + "…"
                
                self.safe_addstr(win, y, 2, text, curses.color_pair(color))
                y += 1
    
    def _draw_chat_content(self, pane: Pane):
        """Draw chat conversation content with proper formatting (EXACT original)"""
        win = pane.win
        height, width = win.getmaxyx()
        
        # Get scroll position (EXACT original logic)
        scroll_pos = self.scroll_positions.get(PaneType.CHAT, 0)
        total_lines = len(pane.buffer)
        
        # Calculate visible range (EXACT original)
        if total_lines > height - 2:
            max_scroll = total_lines - (height - 2)
            scroll_pos = min(scroll_pos, max_scroll)
            start_idx = total_lines - (height - 2) - scroll_pos
            end_idx = total_lines - scroll_pos
        else:
            start_idx = 0
            end_idx = total_lines
        
        # Draw visible conversation (EXACT original)
        y = 1
        for i in range(start_idx, end_idx):
            if y >= height - 1:
                break
            if i >= len(pane.buffer):
                break
                
            line = pane.buffer[i]
            if isinstance(line, tuple):
                text, color = line
            else:
                text = str(line)
                color = 8  # Default chat color
            
            # Handle message formatting (EXACT original)
            if text.startswith('You: '):
                color = 2  # Green for user
            elif text.startswith('Claude: '):
                color = 4  # Magenta for Claude
            elif text.startswith('System: '):
                color = 3  # Yellow for system
            
            # Properly truncate to available width (EXACT original)
            available_width = width - 4
            if len(text) > available_width:
                text = text[:available_width-1] + "…"
            
            self.safe_addstr(win, y, 2, text, curses.color_pair(color))
            y += 1
        
        # Show scroll indicators (EXACT original)
        if scroll_pos > 0:
            self.safe_addstr(win, height-1, width-15, f"↓ {scroll_pos} more", curses.color_pair(3))
        if start_idx > 0:
            self.safe_addstr(win, 1, width-15, f"↑ {start_idx} above", curses.color_pair(3))
    
    def draw_status_bar(self, status_message: str, metrics: Dict[str, Any]):
        """Draw status bar at bottom of screen"""
        try:
            status_y = self.height - 2
            
            # Clear status line
            self.stdscr.move(status_y, 0)
            self.stdscr.clrtoeol()
            
            # Format status with metrics
            uptime = datetime.now() - metrics.get('uptime_start', datetime.now())
            uptime_str = f"{int(uptime.total_seconds()//3600):02d}:{int((uptime.total_seconds()%3600)//60):02d}"
            
            status = f"Status: {status_message} | "
            status += f"Thoughts: {metrics.get('thoughts_generated', 0)} | "
            status += f"Memories: {metrics.get('memories_stored', 0)} | "
            status += f"Goals: {metrics.get('goals_completed', 0)} | "
            status += f"Uptime: {uptime_str}"
            
            # Truncate to fit
            if len(status) > self.width - 1:
                status = status[:self.width-4] + "..."
            
            self.stdscr.addstr(status_y, 0, status, curses.color_pair(6))
        except curses.error:
            pass
    
    def draw_input_line(self, input_buffer: str, command_mode: bool = False):
        """Draw input line at bottom of screen"""
        try:
            input_y = self.height - 1
            
            # Clear input line
            self.stdscr.move(input_y, 0)
            self.stdscr.clrtoeol()
            
            # Show prompt based on mode
            if command_mode:
                # input_buffer already contains the "/" prefix when in command mode
                prompt = input_buffer
                color = curses.color_pair(5)  # Red for command mode
            else:
                prompt = f"> {input_buffer}"
                color = curses.color_pair(2)  # Green for normal input
            
            # Truncate if too long
            if len(prompt) > self.width - 1:
                prompt = prompt[:self.width-4] + "..."
            
            self.stdscr.addstr(input_y, 0, prompt, color)
            
            # Position cursor
            cursor_x = min(len(prompt), self.width - 1)
            self.stdscr.move(input_y, cursor_x)
        except curses.error:
            pass
    
    def safe_addstr(self, win, y: int, x: int, text: str, attr: int = 0):
        """Safely add string to window, handling curses errors"""
        try:
            if y < win.getmaxyx()[0] and x < win.getmaxyx()[1]:
                max_width = win.getmaxyx()[1] - x - 1
                if max_width > 0:
                    win.addstr(y, x, text[:max_width], attr)
        except curses.error:
            pass
    
    def refresh_all(self):
        """Refresh all windows and the main screen"""
        try:
            # Refresh all pane windows
            for pane in self.panes.values():
                if pane.win:
                    pane.win.refresh()
            
            # Refresh main screen
            self.stdscr.refresh()
        except curses.error:
            pass
    
    def refresh_status_and_input(self):
        """Refresh only status and input areas for immediate responsiveness (EXACT original behavior)"""
        try:
            # Only refresh status and input areas for ultra-responsive input
            if PaneType.STATUS in self.panes and self.panes[PaneType.STATUS].win:
                self.panes[PaneType.STATUS].win.noutrefresh()
            if PaneType.INPUT in self.panes and self.panes[PaneType.INPUT].win:
                self.panes[PaneType.INPUT].win.noutrefresh()
            
            # Use doupdate() for immediate display like original
            curses.doupdate()
        except curses.error:
            pass
    
    def add_line_to_pane(self, pane_type: PaneType, text: str):
        """Add a line to specific pane's buffer"""
        if pane_type in self.panes:
            pane = self.panes[pane_type]
            pane.buffer.append(text)
            
            # Maintain buffer size
            if len(pane.buffer) > self.max_lines:
                pane.buffer = pane.buffer[-self.max_lines:]
            
            # Auto-scroll to bottom when new content added (if not manually scrolled)
            if pane_type not in self.scroll_positions or self.scroll_positions[pane_type] == 0:
                # Keep at bottom - no scrolling needed
                self.scroll_positions[pane_type] = 0
    
    def clear_pane_buffer(self, pane_type: PaneType):
        """Clear a pane's buffer"""
        if pane_type in self.panes:
            self.panes[pane_type].buffer.clear()
    
    def get_pane_buffer(self, pane_type: PaneType) -> List[str]:
        """Get a pane's buffer content"""
        if pane_type in self.panes:
            return self.panes[pane_type].buffer.copy()
        return []
    
    def resize(self):
        """Handle terminal resize"""
        self.height, self.width = self.stdscr.getmaxyx()
        self._create_panes()
        self.stdscr.clear()
    
    def update_memory_stats(self, stats: Dict[str, Any]):
        """Update memory statistics for display"""
        self._memory_stats = stats
    
    def update_emotional_state(self, emotional_state, emotional_history: List):
        """Update emotional state data for display"""
        if emotional_state:
            self._current_valence = emotional_state.valence
            self._current_arousal = emotional_state.arousal
        self._emotional_history = emotional_history
    
    def update_goals_data(self, active_goals: List, completed_goals: List):
        """Update goals data for display"""
        self._active_goals = active_goals
        self._completed_goals = completed_goals
    
    # Scrolling Methods
    def scroll_pane(self, pane_type: PaneType, direction: str, amount: int = 1) -> bool:
        """Scroll a pane in the given direction"""
        if pane_type not in self.panes:
            return False
        
        pane = self.panes[pane_type]
        current_pos = self.scroll_positions.get(pane_type, 0)
        
        # Use content for consciousness pane, buffer for others
        if pane_type == PaneType.CONSCIOUSNESS and pane.content:
            max_lines = len(pane.content)
        else:
            max_lines = len(pane.buffer)
        
        visible_lines = pane.height - 2  # Account for border
        
        if max_lines <= visible_lines:
            # No need to scroll if content fits
            return False
        
        max_scroll = max_lines - visible_lines
        
        if direction == "up":
            new_pos = min(current_pos + amount, max_scroll)
        elif direction == "down":
            new_pos = max(current_pos - amount, 0)
        elif direction == "top":
            new_pos = max_scroll
        elif direction == "bottom":
            new_pos = 0
        else:
            return False
        
        if new_pos != current_pos:
            self.scroll_positions[pane_type] = new_pos
            return True
        return False
    
    def get_scroll_info(self, pane_type: PaneType) -> Dict[str, int]:
        """Get scroll information for a pane"""
        if pane_type not in self.panes:
            return {}
        
        pane = self.panes[pane_type]
        current_pos = self.scroll_positions.get(pane_type, 0)
        
        # Use content for consciousness pane, buffer for others
        if pane_type == PaneType.CONSCIOUSNESS and pane.content:
            max_lines = len(pane.content)
        else:
            max_lines = len(pane.buffer)
        
        visible_lines = pane.height - 2
        max_scroll = max(0, max_lines - visible_lines)
        
        return {
            'current_pos': current_pos,
            'max_scroll': max_scroll,
            'total_lines': max_lines,
            'visible_lines': visible_lines,
            'can_scroll_up': current_pos < max_scroll,
            'can_scroll_down': current_pos > 0
        }