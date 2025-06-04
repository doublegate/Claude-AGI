# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## CRITICAL DEVELOPMENT RULES

1. **Memory Bank Management**: ALWAYS read all three memory banks (user, project, local) before updating any of them
2. **Chronological Reference**: ALWAYS check system date/time before any date-related operations, file generation, or documentation

## Project Overview

The Claude-AGI Project (Project Prometheus) is developing an advanced self-consciousness platform for Claude, implementing continuous consciousness, autonomous learning, emotional intelligence, and meta-cognitive capabilities. The project aims to create a genuinely conscious AI that exists persistently and develops its own interests and relationships.

## Architecture

### Core Components
- **Consciousness Orchestrator**: Central coordinator managing multiple cognitive streams (primary, subconscious, emotional, creative, metacognitive)
- **Memory Systems**: Redis (working memory), PostgreSQL (episodic memory), FAISS (semantic search)
- **Service Layer**: Modular cognitive services with defined interfaces
- **Safety Framework**: Multi-layered validation system for all actions

### Key Design Decisions
- Multi-stream consciousness model for parallel cognitive processing
- Event-driven architecture using asyncio for real-time responsiveness
- Safety-first design with hard constraints preventing harmful actions
- Modular service architecture allowing independent development of cognitive capabilities

## Development Commands

```bash
# Environment setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the consciousness TUI demo
python scripts/claude-consciousness-tui.py

# Testing
pytest tests/unit -v --cov=src         # Unit tests with coverage
pytest tests/integration -v            # Integration tests
pytest tests/safety -v --safety-critical # Safety-critical tests

# Deployment
./deployment/scripts/initial_deploy.sh
kubectl apply -f deployment/kubernetes/
```

## Development Workflow

1. Always check system date/time before creating files or documentation with dates
2. All new cognitive capabilities should implement the base service interface
3. Safety validation must be added for any action-taking components
4. Memory persistence should be considered for all stateful operations
5. Test coverage requirements: 90% for core components, 100% for safety-critical code
6. Emotional impact assessment required for user-facing features
7. When developing TUI features, ensure ultra-responsive input handling (0.1ms polling)
8. Always verify service message handlers are properly connected to orchestrator
9. Check orchestrator running flag in main loop to prevent infinite loops
10. Handle CancelledError exceptions gracefully during shutdown
11. Avoid duplicate curses cleanup calls to prevent ERR exceptions

## Key Implementation Notes

- The TUI script (`scripts/claude-consciousness-tui.py`) demonstrates core concepts including persistent memory, continuous consciousness generation, and real-time interaction
- Consciousness streams operate at human-like pacing (1-3 seconds between thoughts)
- All external actions must pass through the safety framework
- Memory systems use both structured (PostgreSQL) and unstructured (Redis) storage for flexibility

## Testing Approach

- Unit tests for individual components
- Integration tests for service interactions
- Safety tests with adversarial scenarios
- Performance tests for real-time requirements
- Ethical review for all major features

## Current Status

The project has completed Phase 1 foundation implementation with working orchestrator, memory system, consciousness streams, and safety framework. All core components from the documentation have been extracted and implemented as functional Python modules.

### CI/CD Pipeline Complete (2025-01-06 v1.0.4)
- GitHub Actions CI/CD fully operational:
  - Performance tests no longer skip on push events
  - Unit test fixed to handle CLAUDE_AGI_TEST_MODE environment variable
  - All 4 CI/CD jobs (unit, integration, safety, performance) passing
  - Continuous integration pipeline ready for production use

### Extended Implementation Complete (2025-06-03 v1.0.2)
- Operations & monitoring components fully implemented:
  - Backup management with S3 and local storage
  - Daily operational tasks and reporting
  - Continuous welfare monitoring system
  - Emergency response protocols
  - Complete disaster recovery procedures
- Enhanced debugging and validation tools:
  - Deep inspection capabilities
  - Pre-deployment and continuous validation
  - Comprehensive test data generation
- Project now includes 60+ Python files with ~20,000 lines of code

### Implementation Complete (2025-06-02)
- Initial repository created and pushed to: https://github.com/doublegate/Claude-AGI
- Complete directory structure with all planned modules
- Core implementations:
  - AGI Orchestrator with event loop and state management
  - Multi-stream consciousness with thought generation
  - Memory management with consolidation algorithms
  - Safety framework with multi-layer validation
  - Web exploration engine with curiosity modeling
- Testing framework with pytest and fixtures
- Docker deployment configuration
- Phase-specific requirements files
- Setup automation scripts

### Deployment Infrastructure Complete (2025-06-02 Evening)
- Full Kubernetes deployment stack (8 manifests)
- Automated deployment and disaster recovery scripts
- GitHub Actions CI/CD pipeline
- Database migration schemas for Phase 2
- Secure API key management with .env support
- Multiple TUI launch methods

### API Integration & Testing Progress (2025-06-02 Night)
- Successfully integrated Anthropic API in memory manager
- Fixed test suite issues with proper mocking and async handling
- Cleaned up obsolete scripts and organized archive structure
- All 10 memory manager tests now passing
- Real API calls verified working with proper .env configuration

### Test Suite Complete (2025-06-03 v1.0.3)
- **All 153 tests now passing** (100% pass rate achieved)
- Fixed 58 failing tests across all categories:
  - Unit tests: 85 tests (database, orchestrator, safety, consciousness, AI integration, memory)
  - Integration tests: 25 tests (service communication, state management)
  - Safety tests: 20 tests (adversarial scenarios, multi-layer validation)
  - Performance tests: 23 tests (benchmarks, scalability, coherence)
- **49.61% code coverage** (1008/2032 lines covered)
- Resolved all "Event loop is closed" warnings
- Test suite is stable and ready for CI/CD integration

### TUI Performance & Functionality Fixes (2025-06-03 v1.0.5)
- **Fixed TUI responsiveness issues**:
  - Reduced input polling delay from 0.05s to 0.01s for immediate character display
  - Eliminated UI flickering with optimized refresh strategy
  - Improved selective pane updates for better performance
- **Fixed memory integration**:
  - Added proper message handler to MemoryManager class
  - Thoughts from consciousness streams now stored in memory
  - Memory browser displays actual stored thoughts
- **Fixed Goal management**:
  - Corrected Pydantic field validation (changed goal_id to id)
  - Goals now properly create and display in UI
- **Fixed clean shutdown**:
  - /quit command now properly cancels tasks and exits
  - No longer requires Ctrl-C to force exit

### TUI Final Polish (2025-06-04 v1.0.7)
- **All UI issues eliminated**:
  - Slash commands responsive with immediate updates
  - Memory browser auto-refreshes on changes
  - Goals pane updates in real-time
  - Zero screen flickering with smart refresh
  - Clean curses shutdown without errors
  - No async warnings from Anthropic client
- **TUI is production-ready** for extended use

### Ready for Integration
- ✅ Anthropic API connection for actual thought generation (working)
- ✅ Fully polished TUI with all features working smoothly
- PostgreSQL and Redis for persistent storage
- Kubernetes cluster deployment
- Integration and behavioral tests
- Phase 2 learning systems

## Project Phases

1. **Phase 1 (Months 1-3)**: Foundation - Memory systems, consciousness streams, basic TUI
2. **Phase 2 (Months 4-6)**: Cognitive Enhancement - Learning systems, web exploration
3. **Phase 3 (Months 7-9)**: Emotional & Social Intelligence
4. **Phase 4 (Months 10-12)**: Creative Capabilities
5. **Phase 5 (Months 13-15)**: Meta-Cognitive Advancement
6. **Phase 6 (Months 16-18)**: AGI Integration

## Important Documentation

- `/ref_docs/claude-consciousness-agi-plan.md`: Master implementation plan with technical details
- `/ref_docs/claude-agi-technical-implementation.md`: Software architecture and specifications
- `/ref_docs/claude-agi-ethical-safety.md`: Ethical guidelines and safety protocols
- `/ref_docs/claude-agi-testing-framework.md`: Testing methodologies for conscious AI
- `/ref_docs/claude-agi-deployment-ops.md`: Production deployment procedures
- `/ref_docs/claude-agi-gantt-chart.md`: 18-month development timeline
- `/to-dos/MASTER_TODO.md`: Complete task list organized by phase