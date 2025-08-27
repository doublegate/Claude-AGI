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
    win: Any = None
    active: bool = False


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
        
        # Initialize UI components
        self._init_colors()
        self._create_panes()
        
    def _init_colors(self):
        """Initialize color pairs for the UI"""
        curses.start_color()
        curses.use_default_colors()
        
        # Define color pairs
        curses.init_pair(1, curses.COLOR_CYAN, -1)    # Consciousness
        curses.init_pair(2, curses.COLOR_GREEN, -1)   # Chat/User
        curses.init_pair(3, curses.COLOR_YELLOW, -1)  # System
        curses.init_pair(4, curses.COLOR_WHITE, -1)   # Memory
        curses.init_pair(5, curses.COLOR_RED, -1)     # Errors
        curses.init_pair(6, curses.COLOR_MAGENTA, -1) # Dreams/Insights
        curses.init_pair(7, curses.COLOR_BLUE, -1)    # Emotional
        
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
    
    def _draw_pane(self, pane: Pane):
        """Draw a single pane with border and content"""
        if not pane.win:
            return
            
        try:
            pane.win.clear()
            
            # Draw border
            if pane.type == self._get_active_pane():
                pane.win.attron(curses.A_BOLD)
                pane.win.box()
                pane.win.attroff(curses.A_BOLD)
            else:
                pane.win.box()
            
            # Draw title
            if len(pane.title) < pane.width - 4:
                title_x = max(2, (pane.width - len(pane.title)) // 2)
                pane.win.addstr(0, title_x, pane.title)
            
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
        """Draw consciousness stream content"""
        content_height = pane.height - 2
        content_width = pane.width - 2
        
        # Get recent consciousness lines
        lines_to_show = pane.buffer[-content_height:] if pane.buffer else []
        
        for i, line in enumerate(lines_to_show):
            if i >= content_height:
                break
                
            # Wrap and truncate line to fit
            wrapped = textwrap.fill(line, content_width)
            wrapped_lines = wrapped.split('\n')
            
            for j, wrapped_line in enumerate(wrapped_lines[:1]):  # Only first line
                try:
                    y_pos = i + 1
                    if y_pos < pane.height - 1:
                        self.safe_addstr(pane.win, y_pos, 1, wrapped_line[:content_width], 
                                       curses.color_pair(1))
                except curses.error:
                    continue
    
    def _draw_memory_content(self, pane: Pane):
        """Draw memory browser content"""
        content_height = pane.height - 2
        content_width = pane.width - 2
        
        # Get memory content from buffer
        lines_to_show = pane.buffer[-content_height:] if pane.buffer else []
        
        for i, line in enumerate(lines_to_show):
            if i >= content_height:
                break
                
            try:
                y_pos = i + 1
                if y_pos < pane.height - 1:
                    display_line = line[:content_width]
                    self.safe_addstr(pane.win, y_pos, 1, display_line, 
                                   curses.color_pair(4))
            except curses.error:
                continue
    
    def _draw_emotional_content(self, pane: Pane):
        """Draw emotional state content"""
        content_height = pane.height - 2
        content_width = pane.width - 2
        
        # Get emotional content from buffer
        lines_to_show = pane.buffer[-content_height:] if pane.buffer else []
        
        for i, line in enumerate(lines_to_show):
            if i >= content_height:
                break
                
            try:
                y_pos = i + 1
                if y_pos < pane.height - 1:
                    display_line = line[:content_width]
                    self.safe_addstr(pane.win, y_pos, 1, display_line, 
                                   curses.color_pair(7))
            except curses.error:
                continue
    
    def _draw_goals_content(self, pane: Pane):
        """Draw goals and interests content"""
        content_height = pane.height - 2
        content_width = pane.width - 2
        
        # Get goals content from buffer
        lines_to_show = pane.buffer[-content_height:] if pane.buffer else []
        
        for i, line in enumerate(lines_to_show):
            if i >= content_height:
                break
                
            try:
                y_pos = i + 1
                if y_pos < pane.height - 1:
                    display_line = line[:content_width]
                    color = curses.color_pair(3) if line.startswith("✓") else curses.color_pair(2)
                    self.safe_addstr(pane.win, y_pos, 1, display_line, color)
            except curses.error:
                continue
    
    def _draw_chat_content(self, pane: Pane):
        """Draw conversation content"""
        content_height = pane.height - 2
        content_width = pane.width - 2
        
        # Get chat lines from buffer
        lines_to_show = pane.buffer[-content_height:] if pane.buffer else []
        
        for i, line in enumerate(lines_to_show):
            if i >= content_height:
                break
                
            try:
                y_pos = i + 1
                if y_pos < pane.height - 1:
                    display_line = line[:content_width]
                    # Color coding for different message types
                    if line.startswith("You:"):
                        color = curses.color_pair(2)
                    elif line.startswith("Claude:"):
                        color = curses.color_pair(1)
                    else:
                        color = curses.color_pair(4)
                    
                    self.safe_addstr(pane.win, y_pos, 1, display_line, color)
            except curses.error:
                continue
    
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
            
            self.stdscr.addstr(status_y, 0, status, curses.color_pair(3))
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
                prompt = f"/{input_buffer}"
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
    
    def add_line_to_pane(self, pane_type: PaneType, text: str):
        """Add a line to specific pane's buffer"""
        if pane_type in self.panes:
            pane = self.panes[pane_type]
            pane.buffer.append(text)
            
            # Maintain buffer size
            if len(pane.buffer) > self.max_lines:
                pane.buffer = pane.buffer[-self.max_lines:]
    
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