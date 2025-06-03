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

The project has a working proof-of-concept TUI demonstrating continuous consciousness and memory persistence. Development follows a phased approach over 18 months, currently in Phase 1 (Foundation) implementing core memory and consciousness systems.