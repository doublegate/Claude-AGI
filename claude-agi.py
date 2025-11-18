#!/usr/bin/env python3
"""Claude-AGI: Advanced General Intelligence System (Refactored)
================================================================

Main entry point for the Claude-AGI consciousness system with refactored architecture.
This script provides an interactive terminal interface using modular components:
- UIRenderer: Handles all visual rendering
- EventHandler: Processes user input and events
- TUIController: Coordinates components and manages state

Usage:
    python claude-agi.py [--config CONFIG_PATH]

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
from src.memory.manager_refactored import MemoryManager  # Using refactored MemoryManager
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
        self.orchestrator_task = None

        logger.info("Claude-AGI initialization complete")

    async def initialize_components(self):
        """Initialize AGI components after orchestrator is ready"""
        logger.info("Initializing AGI components")

        try:
            # Initialize orchestrator services first
            await self.orchestrator.initialize()
            
            # Verify orchestrator is ready before starting background task
            if not self.orchestrator.services:
                logger.error("Orchestrator services not initialized")
                return
            
            # Start the orchestrator as a background task with better error handling
            self.orchestrator_task = asyncio.create_task(self.orchestrator.run())
            self.orchestrator_task.add_done_callback(self._handle_orchestrator_exception)
            
            # Wait longer for services to be fully initialized and start their cycles
            await asyncio.sleep(2)

            # Get components from orchestrator services using correct pattern
            self.memory_manager = self.orchestrator.services.get('memory')
            self.consciousness = self.orchestrator.services.get('consciousness')
            self.safety = self.orchestrator.services.get('safety')
            self.exploration_engine = self.orchestrator.services.get('explorer')

            # Set components in controller
            if self.memory_manager:
                self.controller.set_memory_manager(self.memory_manager)

            if self.consciousness:
                self.controller.set_consciousness_stream(self.consciousness)

            if self.safety:
                self.controller.set_safety_framework(self.safety)
                
            if self.exploration_engine:
                self.controller.set_exploration_engine(self.exploration_engine)

            logger.info("AGI components initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing AGI components: {e}")
            # Continue with basic functionality even if some components fail

    def run(self, stdscr):
        """Main application entry point with curses"""
        try:
            logger.info("Starting TUI initialization")
            
            # Initialize TUI components
            self.controller.initialize_ui(stdscr)
            logger.info("TUI controller initialized")

            # Configure curses
            curses.curs_set(0)  # Hide cursor
            stdscr.clear()
            stdscr.refresh()
            logger.info("Curses configured, starting async main loop")

            # Run the application
            asyncio.run(self._run_async())

        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"Application error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    async def _run_async(self):
        """Async main loop with proper task coordination like the original"""
        try:
            logger.info("Starting AGI components initialization")
            # Initialize AGI components
            await self.initialize_components()
            logger.info("AGI components initialized, starting coordinated tasks")

            # Create all tasks (EXACT original pattern)
            tasks = []
            
            # Orchestrator task (already started in initialize_components)
            if self.orchestrator_task:
                tasks.append(self.orchestrator_task)
            
            # Controller task
            controller_task = asyncio.create_task(self.controller.run())
            tasks.append(controller_task)
            
            logger.info(f"Starting {len(tasks)} coordinated tasks")
            
            # Run all tasks together like the original (EXACT pattern)
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except asyncio.CancelledError:
                logger.info("Main tasks cancelled")
            except Exception as e:
                logger.error(f"Error in task coordination: {e}")

        except Exception as e:
            logger.error(f"Error in async main loop: {e}")
            import traceback
            logger.error(f"Async main loop traceback: {traceback.format_exc()}")
        finally:
            # Cleanup
            await self._cleanup()


    async def _cleanup(self):
        """Clean up application resources"""
        logger.info("Cleaning up application resources")

        try:
            # Cancel orchestrator background task first
            if self.orchestrator_task and not self.orchestrator_task.done():
                self.orchestrator_task.cancel()
                try:
                    await self.orchestrator_task
                except asyncio.CancelledError:
                    pass
            
            # Shutdown orchestrator
            if self.orchestrator:
                await self.orchestrator.shutdown()

            logger.info("Application cleanup complete")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def _handle_orchestrator_exception(self, task: asyncio.Task):
        """Handle exceptions from orchestrator background task"""
        if task.exception():
            logger.error(f"Orchestrator task error: {task.exception()}")


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
            logger.error(f"Fatal error: {e}")
            print(f"Fatal error: {e}")
            sys.exit(1)
    finally:
        # Force terminal reset to clean state
        try:
            # Use stty sane which is more reliable than reset
            os.system('stty sane 2>/dev/null')
            # Clear the screen
            os.system('clear 2>/dev/null')
        except:
            pass


if __name__ == "__main__":
    main()