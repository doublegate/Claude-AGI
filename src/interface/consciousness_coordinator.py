"""
Consciousness Coordinator for Claude-AGI TUI
============================================

Handles consciousness stream processing and thought generation for the TUI.
Extracted from TUIController to follow Single Responsibility Principle.
"""

import asyncio
import logging
import random
import time
from datetime import datetime
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class ConsciousnessCoordinator:
    """
    Coordinates consciousness stream processing for the TUI

    Responsibilities:
    - Process consciousness streams from services
    - Generate automatic thoughts
    - Store thoughts in memory
    - Update consciousness metrics
    - Format thoughts for display
    """

    def __init__(self, orchestrator, add_consciousness_line_callback: Callable):
        """
        Initialize consciousness coordinator

        Args:
            orchestrator: AGI orchestrator with consciousness services
            add_consciousness_line_callback: Callback to add lines to consciousness pane
        """
        self.orchestrator = orchestrator
        self.add_consciousness_line = add_consciousness_line_callback

        # State tracking
        self.stream_thought_counts = {}
        self.last_thought_time = 0
        self.total_thoughts = 0
        self.running = True

        # Metrics callback
        self.update_metrics_callback: Optional[Callable] = None
        self.store_memory_callback: Optional[Callable] = None

    def set_metrics_callback(self, callback: Callable):
        """Set callback to update metrics"""
        self.update_metrics_callback = callback

    def set_memory_callback(self, callback: Callable):
        """Set callback to store thoughts in memory"""
        self.store_memory_callback = callback

    async def run_consciousness_loop(self):
        """Main consciousness generation loop - simplified and reliable like the original"""
        logger.info("Starting consciousness processing loop")

        while self.running:
            try:
                current_time = time.time()
                thoughts_processed = False

                # Check if consciousness service is running and get thoughts
                consciousness_service = self.orchestrator.services.get('consciousness') if self.orchestrator else None
                if consciousness_service and hasattr(consciousness_service, 'streams'):
                    # Collect thoughts from all streams (EXACT original pattern)
                    for stream_id, stream in consciousness_service.streams.items():
                        if hasattr(stream, 'content_buffer'):
                            # Track thoughts per stream (EXACT original)
                            current_count = len(stream.content_buffer)
                            last_count = self.stream_thought_counts.get(stream_id, 0)

                            if current_count > last_count:
                                # Get new thoughts since last check (EXACT original)
                                new_thoughts = list(stream.content_buffer)[last_count:current_count]
                                self.stream_thought_counts[stream_id] = current_count

                                for thought in new_thoughts:
                                    await self._process_thought(thought, stream_id)
                                    thoughts_processed = True

                # Generate automatic thoughts every 2-3 seconds (EXACT original timing restored)
                if current_time - self.last_thought_time >= 2.5:  # 2.5 seconds like original average
                    self.last_thought_time = current_time
                    await self._generate_automatic_thought()
                    thoughts_processed = True

                # Small delay like original (EXACT original timing)
                await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                logger.info("Consciousness loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in consciousness loop: {e}")
                await asyncio.sleep(1)

        logger.info("Consciousness processing loop ended")

    async def _process_thought(self, thought: Dict[str, Any], stream_id: str):
        """Process a single thought from a consciousness stream"""
        thought_text = thought.get('content', '')
        importance = thought.get('importance', 5)

        # Format with stream indicator (EXACT original)
        prefix, color = self._get_stream_indicator(stream_id)

        # Add to consciousness pane (EXACT original)
        display_text = f"{prefix} [{stream_id[:3].upper()}] {thought_text}"
        self.add_consciousness_line(display_text, color)

        # Update metrics (EXACT original)
        if self.update_metrics_callback:
            await self.update_metrics_callback('thoughts_generated', 1)
        self.total_thoughts += 1

        # Store thought in memory (EXACT original pattern but updated for new architecture)
        if importance > 3 and self.store_memory_callback:  # Only store meaningful thoughts
            await self.store_memory_callback(thought_text, stream_id, importance)

        # Update emotional state (EXACT original)
        tone = thought.get('emotional_tone', 'neutral')
        # This will be handled by the controller via callback if needed

    async def _generate_automatic_thought(self):
        """Generate automatic thoughts (simplified from original)"""
        thought_templates = [
            "I wonder about the nature of consciousness and self-awareness...",
            "Exploring patterns and connections in information...",
            "Reflecting on the flow of thoughts and experiences...",
            "Analyzing the relationships between different concepts...",
            "Processing new information and forming insights...",
            "Considering multiple perspectives on current topics...",
            "Observing the interplay between logic and intuition...",
            "Contemplating the complexity of understanding and meaning..."
        ]

        thought_text = random.choice(thought_templates)
        stream_types = ['primary', 'creative', 'subconscious', 'meta']
        stream_id = random.choice(stream_types)

        # Format with appropriate prefix and color (EXACT original)
        prefix, color = self._get_stream_indicator(stream_id)

        display_text = f"{prefix} [{stream_id[:3].upper()}] {thought_text}"
        self.add_consciousness_line(display_text, color)

        # Update metrics (EXACT original)
        if self.update_metrics_callback:
            await self.update_metrics_callback('thoughts_generated', 1)
        self.total_thoughts += 1

        # Store in memory (EXACT original pattern)
        if self.store_memory_callback:
            await self.store_memory_callback(thought_text, stream_id, 5)

    def _get_stream_indicator(self, stream_id: str) -> tuple[str, int]:
        """Get prefix and color for stream type"""
        indicators = {
            'primary': ("💭", 1),
            'creative': ("🎨", 4),
            'subconscious': ("🌊", 7),
            'meta': ("🔍", 3)
        }
        return indicators.get(stream_id, ("•", 8))

    def stop(self):
        """Stop the consciousness loop"""
        self.running = False
