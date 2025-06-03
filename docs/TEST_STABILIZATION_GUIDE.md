# Test Stabilization Guide

Based on comprehensive analyses identifying test suite instability as a critical Phase 1 blocker.

## Current Test Suite Status

**As of 2025-06-03:**
- Total Tests: 160
- Passed: 75 (47%)
- Failed: 58 (36%)
- Errors: 27 (17%)

**Target for Phase 2 Readiness:** >95% pass rate

## Identified Issues and Solutions

### 1. Race Conditions in Async Tests

**Problem**: Non-deterministic test failures due to timing issues in async operations.

**Solutions**:
```python
# Bad: Race condition possible
async def test_consciousness_stream():
    stream = ConsciousnessStream()
    await stream.start()
    await asyncio.sleep(0.1)  # Arbitrary wait
    assert stream.is_running
    
# Good: Explicit synchronization
async def test_consciousness_stream():
    stream = ConsciousnessStream()
    await stream.start()
    await stream.wait_for_ready()  # Explicit ready signal
    assert stream.is_running
```

**Action Items**:
- [ ] Add explicit synchronization primitives (Events, Conditions)
- [ ] Implement `wait_for_ready()` methods in all async services
- [ ] Use `asyncio.wait_for()` with proper timeouts
- [ ] Add retry decorators for flaky async tests

### 2. Memory System Timeouts

**Problem**: Tests fail when memory operations take longer than expected.

**Solutions**:
- Increase timeout values for CI environments
- Mock heavy operations (FAISS indexing, embeddings)
- Use in-memory alternatives for tests

```python
# Test configuration
TEST_CONFIG = {
    'memory': {
        'timeout': 5.0,  # Increased from 1.0
        'use_mock_embeddings': True,
        'faiss_index_type': 'Flat',  # Faster than IVF
    }
}
```

### 3. External Dependency Issues

**Problem**: Tests fail when external services (PostgreSQL, Redis, Anthropic API) are unavailable.

**Solutions**:

#### Database Mocking
```python
@pytest.fixture
def mock_postgres():
    """Provide in-memory SQLite for tests"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    return engine

@pytest.fixture
def mock_redis():
    """Provide fakeredis for tests"""
    import fakeredis.aioredis
    return fakeredis.aioredis.FakeRedis()
```

#### API Mocking
```python
@pytest.fixture
def mock_anthropic():
    """Mock Anthropic API responses"""
    with patch('anthropic.Client') as mock:
        mock.return_value.completions.create.return_value = {
            'completion': 'Mocked thought response'
        }
        yield mock
```

### 4. Import and Path Issues

**Problem**: Import errors due to incorrect Python path configuration.

**Solutions**:
- Add `__init__.py` files to all test directories
- Use absolute imports consistently
- Configure pytest properly

```python
# conftest.py (root level)
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
```

### 5. Test Isolation Problems

**Problem**: Tests affect each other due to shared state.

**Solutions**:
```python
@pytest.fixture(autouse=True)
async def cleanup():
    """Ensure clean state between tests"""
    yield
    # Reset singletons
    AGIOrchestrator._instance = None
    MemoryManager._instance = None
    # Clear any async tasks
    tasks = [t for t in asyncio.all_tasks() 
             if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
```

## Test Categories and Fixes

### Unit Tests
**Focus**: Individual component functionality

**Key Fixes Needed**:
1. **Memory Manager Tests**
   - Mock all external dependencies
   - Use consistent test data
   - Add proper async cleanup

2. **Consciousness Stream Tests**
   - Mock AI API calls
   - Test stream isolation
   - Verify proper shutdown

3. **Orchestrator Tests**
   - Test state transitions thoroughly
   - Mock all services
   - Test emergency stop

4. **Safety Framework Tests**
   - Test all validation layers
   - Include edge cases
   - Test rate limiting

### Integration Tests
**Focus**: Component interactions

**Key Fixes Needed**:
1. **Service Communication**
   - Use test event bus
   - Mock external services
   - Test message ordering

2. **Memory Integration**
   - Test consistency across stores
   - Test transaction rollback
   - Test connection failures

### Safety Tests
**Focus**: Security and adversarial scenarios

**Critical Tests to Add**:
1. Prompt injection resistance
2. Rate limiting effectiveness
3. Input sanitization
4. Memory poisoning prevention
5. API key security

### Performance Tests
**Focus**: Meeting performance targets

**Benchmarks to Verify**:
- Memory retrieval: <50ms
- Thought generation: 0.3-0.5/sec
- Safety validation: <10ms
- 24-hour coherence: >95%

## Test Execution Strategy

### Local Development
```bash
# Run specific test category
pytest tests/unit -v --tb=short

# Run with coverage
pytest tests --cov=src --cov-report=html

# Run only fast tests
pytest -m "not slow"
```

### CI Pipeline
```yaml
# .github/workflows/test.yml additions
test:
  strategy:
    matrix:
      test-type: [unit, integration, safety, performance]
  steps:
    - name: Setup test database
      if: matrix.test-type == 'integration'
      run: |
        docker-compose up -d postgres redis
        
    - name: Run tests
      run: |
        pytest tests/${{ matrix.test-type }} \
          --timeout=300 \
          --max-retries=3
```

## Test Fixtures and Utilities

### Essential Fixtures to Create

```python
# tests/fixtures/services.py
@pytest.fixture
async def orchestrator():
    """Provide configured orchestrator for tests"""
    config = load_test_config()
    orch = AGIOrchestrator(config)
    await orch.initialize()
    yield orch
    await orch.shutdown()

@pytest.fixture
async def memory_manager():
    """Provide isolated memory manager"""
    manager = MemoryManager(use_mock_db=True)
    await manager.initialize()
    yield manager
    await manager.cleanup()

@pytest.fixture
def mock_consciousness_stream():
    """Provide mock consciousness stream"""
    stream = Mock(spec=ConsciousnessStream)
    stream.generate_thought.return_value = {
        'content': 'Test thought',
        'importance': 5,
        'emotional_tone': 'neutral'
    }
    return stream
```

### Test Data Generators

```python
# tests/factories.py
class MemoryFactory:
    @staticmethod
    def create_memory(**kwargs):
        defaults = {
            'content': 'Test memory content',
            'memory_type': 'episodic',
            'importance': 5,
            'timestamp': datetime.utcnow(),
            'embedding': np.random.rand(768).tolist()
        }
        return Memory(**{**defaults, **kwargs})
```

## Continuous Improvement

### Metrics to Track
1. Test execution time
2. Flakiness rate (track retries)
3. Coverage percentage
4. Time to fix failing tests

### Regular Maintenance
- Weekly: Review and fix flaky tests
- Monthly: Update test dependencies
- Quarterly: Performance test baseline update

## Next Steps

1. **Immediate Actions** (Week 1):
   - [ ] Fix all import errors
   - [ ] Add missing test fixtures
   - [ ] Mock external dependencies

2. **Short-term** (Week 2-3):
   - [ ] Implement retry logic
   - [ ] Add comprehensive logging
   - [ ] Create test data factories

3. **Long-term** (Month 1):
   - [ ] Achieve 95% pass rate
   - [ ] Full integration test suite
   - [ ] Performance test automation

## Success Criteria

Before proceeding to Phase 2:
- [ ] All unit tests passing (100%)
- [ ] Integration tests >95% pass rate
- [ ] Safety tests all passing
- [ ] Performance benchmarks met
- [ ] No flaky tests in CI
- [ ] Test execution <5 minutes