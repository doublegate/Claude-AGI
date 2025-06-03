#!/usr/bin/env python3
"""
Setup script for Phase 1 of Claude AGI

This script sets up the foundational components:
- Database initialization
- Core services setup
- Basic consciousness streams
- TUI interface preparation
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from core.orchestrator import AGIOrchestrator
from memory.manager import MemoryManager
from consciousness.stream import ConsciousnessStream

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_prerequisites():
    """Check that required services are available"""
    logger.info("Checking prerequisites...")
    
    # Check for environment variables
    required_env = ['ANTHROPIC_API_KEY']
    missing = []
    
    for env_var in required_env:
        if not os.getenv(env_var):
            missing.append(env_var)
            
    if missing:
        logger.error(f"Missing required environment variables: {missing}")
        logger.info("Please set them in your .env file or environment")
        return False
        
    # Check Python version
    if sys.version_info < (3, 11):
        logger.error("Python 3.11+ is required")
        return False
        
    logger.info("Prerequisites check passed")
    return True


async def setup_databases():
    """Initialize database connections"""
    logger.info("Setting up databases...")
    
    # For Phase 1, we're using in-memory stores
    # In production, this would initialize PostgreSQL and Redis
    
    logger.info("Using in-memory stores for Phase 1 development")
    
    # Future implementation would include:
    # - PostgreSQL schema creation
    # - Redis configuration
    # - Initial data loading
    
    return True


async def initialize_core_services():
    """Initialize core AGI services"""
    logger.info("Initializing core services...")
    
    try:
        # Create orchestrator
        orchestrator = AGIOrchestrator()
        logger.info("✓ Orchestrator created")
        
        # Initialize orchestrator (this will create all services)
        await orchestrator.initialize()
        logger.info("✓ All services initialized")
        
        # Verify services
        service_count = len(orchestrator.services)
        logger.info(f"✓ {service_count} services ready")
        
        return orchestrator
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        return None


async def verify_consciousness_streams(orchestrator):
    """Verify consciousness streams are working"""
    logger.info("Verifying consciousness streams...")
    
    consciousness = orchestrator.services.get('consciousness')
    if not consciousness:
        logger.error("Consciousness service not found")
        return False
        
    # Check streams
    streams = consciousness.streams
    logger.info(f"✓ {len(streams)} consciousness streams configured")
    
    for stream_id, stream in streams.items():
        logger.info(f"  - {stream_id}: priority={stream.priority}, interval={stream.thought_interval}s")
        
    return True


async def test_memory_system(orchestrator):
    """Test memory system functionality"""
    logger.info("Testing memory system...")
    
    memory = orchestrator.services.get('memory')
    if not memory:
        logger.error("Memory service not found")
        return False
        
    try:
        # Test storing a thought
        test_thought = {
            'content': 'Phase 1 setup test thought',
            'emotional_tone': 'optimistic',
            'importance': 7
        }
        
        thought_id = await memory.store_thought(test_thought)
        logger.info(f"✓ Stored test thought: {thought_id}")
        
        # Test retrieval
        retrieved = await memory.recall_by_id(thought_id)
        if retrieved:
            logger.info("✓ Successfully retrieved test thought")
        else:
            logger.error("Failed to retrieve test thought")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Memory test failed: {e}")
        return False


async def prepare_tui_interface():
    """Prepare the TUI interface configuration"""
    logger.info("Preparing TUI interface...")
    
    # Check if the existing TUI script is available
    tui_path = Path(__file__).parent.parent / 'claude-consciousness-tui.py'
    
    if tui_path.exists():
        logger.info(f"✓ TUI script found at: {tui_path}")
        logger.info("  You can run it with: python scripts/claude-consciousness-tui.py")
    else:
        logger.warning("TUI script not found at expected location")
        
    return True


async def create_initial_config():
    """Create initial configuration files if needed"""
    logger.info("Checking configuration...")
    
    config_dir = Path(__file__).parent.parent.parent / 'configs'
    env_file = Path(__file__).parent.parent.parent / '.env'
    
    if not env_file.exists():
        logger.warning(".env file not found - creating from template")
        template = Path(__file__).parent.parent.parent / '.env.example'
        if template.exists():
            import shutil
            shutil.copy(template, env_file)
            logger.info("✓ Created .env from template - please update with your API keys")
        else:
            logger.error(".env.example not found")
            
    return True


async def setup_phase1():
    """Main setup function for Phase 1"""
    logger.info("=== Claude AGI Phase 1 Setup ===")
    logger.info("Setting up foundational components...")
    
    # Check prerequisites
    if not await check_prerequisites():
        logger.error("Prerequisites check failed")
        return False
        
    # Create initial config
    await create_initial_config()
    
    # Setup databases
    if not await setup_databases():
        logger.error("Database setup failed")
        return False
        
    # Initialize core services
    orchestrator = await initialize_core_services()
    if not orchestrator:
        logger.error("Service initialization failed")
        return False
        
    # Verify components
    if not await verify_consciousness_streams(orchestrator):
        logger.error("Consciousness verification failed")
        return False
        
    if not await test_memory_system(orchestrator):
        logger.error("Memory system test failed")
        return False
        
    # Prepare TUI
    await prepare_tui_interface()
    
    # Shutdown orchestrator (it will be started fresh when running main.py)
    await orchestrator.shutdown()
    
    logger.info("\n=== Phase 1 Setup Complete! ===")
    logger.info("\nNext steps:")
    logger.info("1. Update .env file with your ANTHROPIC_API_KEY")
    logger.info("2. Run the consciousness TUI: python scripts/claude-consciousness-tui.py")
    logger.info("3. Or start the full system: python src/main.py")
    
    return True


if __name__ == "__main__":
    # Run setup
    success = asyncio.run(setup_phase1())
    sys.exit(0 if success else 1)