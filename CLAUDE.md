# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

1. All new cognitive capabilities should implement the base service interface
2. Safety validation must be added for any action-taking components
3. Memory persistence should be considered for all stateful operations
4. Test coverage requirements: 90% for core components, 100% for safety-critical code
5. Emotional impact assessment required for user-facing features

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

### Implementation Complete (2025-01-06)
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

### Deployment Infrastructure Complete (2025-01-06 Evening)
- Full Kubernetes deployment stack (8 manifests)
- Automated deployment and disaster recovery scripts
- GitHub Actions CI/CD pipeline
- Database migration schemas for Phase 2
- Secure API key management with .env support
- Multiple TUI launch methods

### Ready for Integration
- Anthropic API connection for actual thought generation
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