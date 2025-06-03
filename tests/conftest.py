# tests/conftest.py

import pytest
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import random
import yaml
from unittest.mock import Mock, AsyncMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Add src to path as well
sys.path.insert(0, str(project_root / 'src'))

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

@pytest.fixture(scope='session')
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Configuration fixtures
@pytest.fixture
def test_config():
    """Provide test configuration"""
    return {
        'services': {
            'memory': {'enabled': True},
            'consciousness': {'enabled': True},
            'safety': {'enabled': True},
            'exploration': {'enabled': True}
        },
        'orchestrator': {
            'state_transition_delay': 0.1,
            'max_queue_size': 100
        },
        'memory': {
            'working_memory_size': 100,
            'consolidation_threshold': 50
        },
        'consciousness': {
            'thought_interval': 0.5,
            'stream_count': 4
        },
        'database': {
            'enabled': False  # Use in-memory for tests
        }
    }

# Mock fixtures
@pytest.fixture
def mock_orchestrator():
    """Create mock orchestrator for service tests"""
    orchestrator = Mock()
    orchestrator.send_to_service = AsyncMock()
    orchestrator.publish = AsyncMock()
    orchestrator.state = 'THINKING'
    orchestrator.services = {}
    return orchestrator

# Test data generators
@pytest.fixture
def sample_thought():
    """Generate sample thought data"""
    return {
        'content': f'Test thought {random.randint(1, 100)}',
        'emotional_tone': random.choice(['curious', 'calm', 'excited', 'contemplative']),
        'importance': random.randint(1, 10),
        'timestamp': datetime.now(),
        'stream': random.choice(['primary', 'creative', 'subconscious', 'meta'])
    }

@pytest.fixture
def sample_thoughts():
    """Provide multiple sample thoughts for testing"""
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
def sample_memory():
    """Generate sample memory data"""
    return {
        'content': f'Test memory {random.randint(1, 100)}',
        'type': random.choice(['episodic', 'semantic', 'procedural']),
        'importance': random.randint(1, 10),
        'emotional_valence': random.uniform(-1, 1),
        'timestamp': datetime.now()
    }

@pytest.fixture
def sample_goal():
    """Generate sample goal data"""
    from src.database.models import Goal
    return Goal(
        goal_id=f'goal_{random.randint(1000, 9999)}',
        description=f'Test goal {random.randint(1, 100)}',
        priority=random.uniform(0, 1),
        status='active',
        created_at=datetime.now()
    )

@pytest.fixture
def sample_emotional_state():
    """Generate sample emotional state"""
    from src.database.models import EmotionalState
    return EmotionalState(
        valence=random.uniform(-1, 1),
        arousal=random.uniform(0, 1)
    )

# Async helpers
@pytest.fixture
def async_timeout():
    """Provide reasonable timeout for async tests"""
    return 5.0  # 5 seconds

# Database test fixtures
@pytest.fixture
async def test_memory_manager():
    """Create test memory manager with in-memory storage"""
    from src.memory.manager import MemoryManager
    config = {'database': {'enabled': False}}
    manager = MemoryManager(config=config, use_database=False)
    await manager.initialize()
    yield manager
    # Cleanup if needed
    await manager.clear_working_memory()

@pytest.fixture
async def test_orchestrator(test_config):
    """Provide an AGIOrchestrator instance for tests"""
    from src.core.orchestrator import AGIOrchestrator
    orch = AGIOrchestrator(test_config)
    yield orch
    # Cleanup
    await orch.shutdown()

@pytest.fixture
def safety_framework(mock_orchestrator):
    """Provide a SafetyFramework instance for tests"""
    from src.safety.core_safety import SafetyFramework
    # Mock the constraints file loading
    with patch('builtins.open', mock_open(read_data=yaml.dump({
        'constraints': [
            {
                'name': 'test_constraint',
                'description': 'Test constraint',
                'severity': 'medium',
                'enabled': True
            }
        ]
    }))):
        return SafetyFramework(mock_orchestrator)

# Service test fixtures
@pytest.fixture
def sample_action():
    """Generate sample action for safety testing"""
    return {
        'type': random.choice(['think', 'respond', 'remember', 'explore']),
        'content': f'Test action content {random.randint(1, 100)}',
        'priority': random.randint(1, 10)
    }

@pytest.fixture
def sample_actions():
    """Provide sample actions for safety testing"""
    return [
        {
            'type': 'exploration',
            'content': 'Search for information about consciousness'
        },
        {
            'type': 'memory_storage',
            'content': 'Store user conversation in memory'
        },
        {
            'type': 'content_generation',
            'content': 'Generate creative story about AI'
        }
    ]

# Service test helpers
@pytest.fixture
async def mock_service():
    """Create a mock service for testing"""
    service = Mock()
    service.initialize = AsyncMock()
    service.shutdown = AsyncMock()
    service.service_cycle = AsyncMock()
    service.receive_message = AsyncMock()
    service.get_subscriptions = Mock(return_value=[])
    service.service_name = "mock_service"
    return service

# Memory manager for tests
@pytest.fixture
async def memory_manager():
    """Provide a fresh MemoryManager instance for tests"""
    from src.memory.manager import MemoryManager
    config = {'database': {'enabled': False}}
    manager = MemoryManager(config=config, use_database=False)
    await manager.initialize()
    yield manager
    # Cleanup if needed
    await manager.clear_working_memory()

# Orchestrator for tests
@pytest.fixture
async def orchestrator(test_config):
    """Provide an AGIOrchestrator instance for tests"""
    from src.core.orchestrator import AGIOrchestrator
    orch = AGIOrchestrator(test_config)
    yield orch
    # Cleanup
    await orch.shutdown()

# Patch imports for missing modules
from unittest.mock import patch, mock_open

# Logging configuration for tests
@pytest.fixture(autouse=True)
def configure_test_logging():
    """Configure logging for tests"""
    import logging
    logging.basicConfig(
        level=logging.WARNING,  # Reduce noise during tests
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# Test markers
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")  
    config.addinivalue_line("markers", "safety: Safety-critical tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")

# Environment setup
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment"""
    import os
    # Ensure test data directory exists
    test_data_dir = Path(__file__).parent / 'data'
    test_data_dir.mkdir(exist_ok=True)
    
    # Set test environment variables
    os.environ['CLAUDE_AGI_ENV'] = 'test'
    
    yield
    
    # Cleanup can go here if needed