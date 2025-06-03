# Test Suite Fixes TODO

## Current Status (2025-06-02 Continued Session)

### Test Results
- **Total Tests**: 160
- **Passed**: 75 ✅
- **Failed**: 58 ❌
- **Errors**: 27 ⚠️

### Fixed Issues ✅
1. **Safety Framework Classes**
   - Added ViolationType enum
   - Added ContentFilter class
   - Added SafetyValidator base class
   - Added ActionValidator class
   - Added RateLimiter class
   - Added EmergencyStop class
   - Added SafetyMonitor class

2. **Orchestrator Classes & Methods**
   - Added StateTransition dataclass
   - Added _initialize_services method
   - Added publish/subscribe methods
   - Added emergency_stop method
   - Added send_to_service method
   - Added process_events_queue method
   - Added get_system_status method
   - Added register_service method
   - Added transition_to method with validation

3. **Import Path Fixes**
   - Fixed memory.manager -> src.memory.manager
   - Fixed relative imports in orchestrator

4. **AI Integration**
   - Added retry decorator to _generate_with_api
   - Fixed datetime.utcnow() deprecation

### Remaining Issues to Fix 🔧

#### 1. Test Expectation Mismatches
- [ ] Update test mocks to use AsyncMock for async methods
- [ ] Fix Message class test expectations
- [ ] Update orchestrator tests for new method signatures
- [ ] Fix consciousness stream test expectations

#### 2. Database Connection Tests
- [ ] Mock database connections for tests
- [ ] Add test fixtures for PostgreSQL/Redis
- [ ] Fix FAISS index initialization in tests

#### 3. Service Integration Tests
- [ ] Update service initialization expectations
- [ ] Fix service communication test mocks
- [ ] Add missing service stubs for tests

#### 4. Safety Framework Tests
- [ ] Update validator test expectations
- [ ] Fix rate limiter timing tests
- [ ] Update emergency stop test scenarios

#### 5. Performance Tests
- [ ] Fix benchmark test setup
- [ ] Update performance metric assertions
- [ ] Fix timing-dependent tests

### Next Steps
1. Run tests individually to identify specific failures
2. Update test mocks and expectations
3. Add missing test fixtures
4. Fix timing and async issues
5. Ensure all tests can run without external dependencies

### Commands for Testing
```bash
# Run specific test file
python -m pytest tests/unit/test_orchestrator.py -xvs

# Run specific test
python -m pytest tests/unit/test_orchestrator.py::TestOrchestrator::test_name -xvs

# Run with debugging
python -m pytest tests/unit/test_orchestrator.py -xvs --pdb

# Show test output
python -m pytest tests/unit/test_orchestrator.py -xvs --capture=no
```

### Priority Order
1. Fix orchestrator tests (core functionality)
2. Fix safety framework tests (critical for operation)
3. Fix AI integration tests (needed for thought generation)
4. Fix consciousness stream tests (main feature)
5. Fix database connection tests (can mock for now)
6. Fix integration tests (depends on unit tests)
7. Fix performance tests (can be last)