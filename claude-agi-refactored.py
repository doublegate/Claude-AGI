#!/usr/bin/env python3
"""Claude-AGI: Advanced General Intelligence System (Refactored)
================================================================

Main entry point for the Claude-AGI consciousness system with refactored architecture.
This script provides an interactive terminal interface using modular components:
- UIRenderer: Handles all visual rendering
- EventHandler: Processes user input and events
- TUIController: Coordinates components and manages state

Usage:
    python claude-agi-refactored.py [--config CONFIG_PATH]

Options:
    --config    Path to configuration file (default: configs/development.yaml)
    --help      Show this help message
"""

import argparse
import asyncio
import curses
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import AGI components
from src.consciousness.stream import ConsciousnessStream
from src.core.ai_integration import ThoughtGenerator
from src.core.orchestrator import AGIOrchestrator
from src.interface.tui_controller import TUIController
from src.memory.manager import MemoryManager
from src.safety.core_safety import SafetyFramework

load_dotenv()

# Configure logging - disable console output when using TUI
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

# Configure file-only logging to avoid interfering with curses
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/claude-agi.log'),
    ]
)

# Suppress some verbose loggers
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('anthropic').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class ClaudeAGIApp:
    """
    Main Claude-AGI Application (Refactored)

    Uses modular architecture with separated concerns:
    - TUIController: Coordinates UI and AGI components
    - UIRenderer: Handles visual display
    - EventHandler: Processes user input
    """

    def __init__(self, config_path: str = "configs/development.yaml"):
        """Initialize Claude-AGI with configuration"""
        logger.info(f"Initializing Claude-AGI with config: {config_path}")

        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Initialize core AGI orchestrator
        self.orchestrator = AGIOrchestrator(self.config)

        # Initialize TUI controller
        self.controller = TUIController(self.config, self.orchestrator)

        # AGI components (will be initialized after orchestrator setup)
        self.memory_manager = None
        self.consciousness = None
        self.safety = None

        logger.info("Claude-AGI initialization complete")

    async def initialize_components(self):
        """Initialize AGI components after orchestrator is ready"""
        logger.info("Initializing AGI components")

        try:
            # Start the orchestrator
            await self.orchestrator.start()

            # Get components from orchestrator
            self.memory_manager = getattr(self.orchestrator, 'memory_manager', None)
            self.consciousness = getattr(self.orchestrator, 'consciousness_streams', {}).get('primary')
            self.safety = getattr(self.orchestrator, 'safety_framework', None)

            # Set components in controller
            if self.memory_manager:
                self.controller.set_memory_manager(self.memory_manager)

            if self.consciousness:
                self.controller.set_consciousness_stream(self.consciousness)

            if self.safety:
                self.controller.set_safety_framework(self.safety)

            logger.info("AGI components initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing AGI components: {e}")
            # Continue with basic functionality even if some components fail

    def run(self, stdscr):
        """Main application entry point with curses"""
        try:
            # Initialize TUI components
            self.controller.initialize_ui(stdscr)

            # Configure curses
            curses.curs_set(0)  # Hide cursor
            stdscr.clear()
            stdscr.refresh()

            # Run the application
            asyncio.run(self._run_async())

        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            self._cleanup_curses()

    async def _run_async(self):
        """Async main loop"""
        try:
            # Initialize AGI components
            await self.initialize_components()

            # Start the controller
            await self.controller.run()

        except Exception as e:
            logger.error(f"Error in async main loop: {e}")
        finally:
            # Cleanup
            await self._cleanup()

    def _cleanup_curses(self):
        """Clean up curses state"""
        try:
            curses.nocbreak()
            curses.echo()
            curses.endwin()
        except:
            # Ignore cleanup errors
            pass

    async def _cleanup(self):
        """Clean up application resources"""
        logger.info("Cleaning up application resources")

        try:
            # Stop orchestrator
            if self.orchestrator:
                await self.orchestrator.stop()

            logger.info("Application cleanup complete")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Claude-AGI: Advanced General Intelligence System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--config', 
        default='configs/development.yaml',
        help='Path to configuration file (default: configs/development.yaml)'
    )

    args = parser.parse_args()

    # Check if config file exists
    if not os.path.exists(args.config):
        print(f"Error: Configuration file '{args.config}' not found")
        print("Available configs:")
        config_dir = Path('configs')
        if config_dir.exists():
            for config_file in config_dir.glob('*.yaml'):
                print(f"  {config_file}")
        else:
            print("  No configs directory found")
        sys.exit(1)

    # Create and run application
    app = ClaudeAGIApp(args.config)

    try:
        # Run with curses wrapper for proper cleanup
        curses.wrapper(app.run)
    except Exception as e:
        print(f"Fatal error: {e}")
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()