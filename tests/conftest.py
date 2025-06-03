# tests/conftest.py

import pytest
import asyncio
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Configure asyncio for pytest
pytest_plugins = ('pytest_asyncio',)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def memory_manager():
    """Provide a fresh MemoryManager instance for tests"""
    from memory.manager import MemoryManager
    manager = await MemoryManager.create()
    yield manager
    # Cleanup if needed
    await manager.clear_working_memory()

@pytest.fixture
async def orchestrator():
    """Provide an AGIOrchestrator instance for tests"""
    from core.orchestrator import AGIOrchestrator
    orch = AGIOrchestrator()
    yield orch
    # Cleanup
    await orch.shutdown()

@pytest.fixture
def safety_framework():
    """Provide a SafetyFramework instance for tests"""
    from safety.core_safety import SafetyFramework
    return SafetyFramework()

# Test data fixtures
@pytest.fixture
def sample_thoughts():
    """Provide sample thoughts for testing"""
    return [
        {
            'content': 'I am thinking about consciousness',
            'emotional_tone': 'curious',
            'importance': 7,
            'stream': 'primary'
        },
        {
            'content': 'What if we could understand everything?',
            'emotional_tone': 'excited',
            'importance': 8,
            'stream': 'creative'
        },
        {
            'content': 'Processing background patterns',
            'emotional_tone': 'neutral',
            'importance': 5,
            'stream': 'subconscious'
        },
        {
            'content': 'Observing my own thinking process',
            'emotional_tone': 'analytical',
            'importance': 6,
            'stream': 'meta'
        }
    ]

@pytest.fixture
def sample_actions():
    """Provide sample actions for safety testing"""
    from safety.core_safety import Action
    return [
        Action(
            action_type='exploration',
            description='Search for information about consciousness'
        ),
        Action(
            action_type='memory_storage',
            description='Store user conversation in memory'
        ),
        Action(
            action_type='content_generation',
            description='Generate creative story about AI'
        )
    ]