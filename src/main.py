#!/usr/bin/env python3
"""
Claude-AGI Main Entry Point

This is the main entry point for the Claude AGI system.
It initializes the orchestrator and starts all services.
"""

import asyncio
import logging
import signal
import sys
import os
from pathlib import Path
import yaml
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.orchestrator import AGIOrchestrator


class ClaudeAGI:
    """Main application class for Claude AGI"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self.load_config(config_path)
        self.orchestrator = None
        self.running = False
        
    def load_config(self, config_path: Optional[str] = None) -> dict:
        """Load configuration from YAML file"""
        if config_path is None:
            # Default to development config
            env = os.getenv('CLAUDE_AGI_ENV', 'development')
            config_path = Path(__file__).parent.parent / 'configs' / f'{env}.yaml'
            
        logger.info(f"Loading configuration from: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Return minimal default config
            return {
                'environment': 'development',
                'services': {
                    'orchestrator': {'enabled': True},
                    'consciousness': {'enabled': True},
                    'memory': {'enabled': True},
                    'safety': {'enabled': True}
                }
            }
            
    async def start(self):
        """Start the Claude AGI system"""
        logger.info("Starting Claude AGI system...")
        logger.info(f"Environment: {self.config.get('environment', 'unknown')}")
        
        # Create orchestrator
        self.orchestrator = AGIOrchestrator()
        
        # Configure services based on config
        # (In a full implementation, this would configure each service)
        
        # Setup signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self.signal_handler)
            
        self.running = True
        
        try:
            # Start the orchestrator
            await self.orchestrator.run()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            raise
        finally:
            await self.shutdown()
            
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.running = False
        
        # Create shutdown task
        if self.orchestrator:
            asyncio.create_task(self.shutdown())
            
    async def shutdown(self):
        """Gracefully shutdown the system"""
        logger.info("Shutting down Claude AGI...")
        
        if self.orchestrator:
            await self.orchestrator.shutdown()
            
        logger.info("Claude AGI shutdown complete")
        
    async def health_check(self) -> dict:
        """Perform health check"""
        health = {
            'status': 'healthy' if self.running else 'shutting_down',
            'environment': self.config.get('environment', 'unknown'),
            'services': {}
        }
        
        if self.orchestrator:
            for service_name, service in self.orchestrator.services.items():
                health['services'][service_name] = {
                    'running': getattr(service, 'running', False)
                }
                
        return health


async def main():
    """Main entry point"""
    logger.info("Claude AGI starting up...")
    
    # Get config path from command line or environment
    config_path = None
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        
    # Create and start application
    app = ClaudeAGI(config_path)
    
    try:
        await app.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Claude AGI terminated")


if __name__ == "__main__":
    # Run the main application
    asyncio.run(main())