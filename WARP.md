# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Claude-AGI (Project Prometheus) is an advanced self-consciousness platform implementing continuous consciousness, autonomous learning, and meta-cognitive capabilities for Claude AI. This is a sophisticated multi-tier system featuring consciousness streams, persistent memory, safety frameworks, and a production-ready TUI interface.

## Development Commands

### Environment Setup
```bash
# Environment setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-test.txt  # For testing
```

### Core Application Commands
```bash
# Run the main AGI system (enhanced TUI)
python claude-agi.py

# Run with specific configuration
python claude-agi.py --config configs/development.yaml

# Run the original consciousness demo
python scripts/claude-consciousness-tui.py

# Run with Docker Compose (full stack)
docker-compose -f deployment/docker/docker-compose.yml up -d
```

### Testing Commands
```bash
# Local CI/CD testing (matches cloud pipeline exactly)
python scripts/ci-local.py            # Run all tests
python scripts/ci-local.py unit       # Unit tests only
python scripts/ci-local.py integration # Integration tests (requires services)
python scripts/ci-local.py safety     # Safety tests
python scripts/ci-local.py performance # Performance benchmarks
python scripts/ci-local.py coverage   # Comprehensive coverage

# Individual pytest commands
pytest tests/unit -v --cov=src        # Unit tests with coverage
pytest tests/integration -v           # Integration tests
pytest tests/safety -v --safety-critical # Safety-critical tests
pytest tests/performance -v           # Performance benchmarks
```

### Build and Deployment
```bash
# Build cross-platform executables
python scripts/build-executable.py

# Deploy monitoring stack
cd monitoring && ./deploy.sh

# Deploy to Kubernetes
./deployment/scripts/initial_deploy.sh
kubectl apply -f deployment/kubernetes/
```

### Database Setup
```bash
# Start required services (Redis & PostgreSQL)
docker-compose -f deployment/docker/docker-compose.yml up -d postgres redis

# Initialize databases (optional but recommended)
python scripts/setup/setup_databases.py
```

## High-Level Architecture

### Core Architecture Pattern
Claude-AGI follows an event-driven, service-oriented architecture with these key patterns:

- **Multi-Stream Consciousness**: Parallel cognitive processing (primary, subconscious, creative, meta streams)
- **Three-Tier Memory System**: Working memory (Redis), episodic memory (PostgreSQL), semantic search (FAISS)
- **Safety-First Design**: Multi-layered validation with hard constraints preventing harmful actions
- **Async Event-Driven**: Real-time responsiveness using asyncio and message passing

### Key Architectural Components

1. **AGI Orchestrator (`src/core/orchestrator.py`)**
   - Central coordinator managing system state (IDLE, THINKING, EXPLORING)
   - Message routing between services
   - Service lifecycle management

2. **Multi-Stream Consciousness (`src/consciousness/stream.py`)**
   - Primary: Main conscious thoughts
   - Subconscious: Background processing
   - Creative: Ideation and creativity
   - Meta: Self-observation and reflection

3. **Memory Architecture (`src/memory/manager.py`)**
   - Working Memory: Short-term storage (Redis/in-memory)
   - Episodic Memory: Long-term experiences (PostgreSQL)
   - Semantic Memory: Knowledge concepts (Vector store)
   - Memory consolidation during idle cycles

4. **Safety Framework (`src/safety/core_safety.py`)**
   - Hard Constraints: Prohibited actions
   - Ethical Evaluation: Principle-based scoring
   - Consequence Prediction: Impact assessment
   - Welfare Monitoring: Well-being checks

5. **Enhanced TUI (`src/interface/`)**
   - Multi-pane interface with consciousness, chat, memory, emotional state, and goals
   - Real-time updates with ultra-responsive input (0.1ms polling)
   - Professional-grade polish with scrolling and active pane indicators

## Critical Development Practices

### Memory Bank Management
- **ALWAYS** read all three memory banks (user, project, local) before updating any of them
- **ALWAYS** check system date/time before any date-related operations or file generation

### TUI Development Guidelines
- Input polling at 0.1ms for ultra-responsive typing
- 1-second refresh interval for main UI updates
- Service message handlers must be properly connected to orchestrator
- Use `id` not `goal_id` for Pydantic validation
- Handle CancelledError exceptions gracefully during shutdown
- Avoid duplicate curses cleanup calls to prevent ERR exceptions

### Testing Standards
- Unit tests for individual components (90% coverage required for core)
- Integration tests for service interactions (requires Redis/PostgreSQL)
- Safety tests with adversarial scenarios (100% coverage for safety-critical code)
- Performance tests for real-time requirements
- Use `CLAUDE_AGI_TEST_MODE=true` environment variable for CI behavior

### Architecture Refactoring Principles
- **God Object Elimination**: Breaking large classes into focused components
- **Service Registry Pattern**: Central lifecycle management with health tracking  
- **Event Bus Pattern**: Type-safe channels with request-response support
- **Memory Store Pattern**: Separate storage concerns with coordinators
- **Connection Pooling**: Always use pools with health monitoring

## Configuration Management

### Environment Files
- `.env.example`: Template for environment variables
- `.env`: Local configuration (ANTHROPIC_API_KEY required)
- `configs/development.yaml`: Development environment settings
- `configs/production.yaml`: Production environment settings

### Required Environment Variables
- `ANTHROPIC_API_KEY`: Required for thought generation (from Anthropic API)
- `PROMETHEUS_METRICS_PORT=8001`: For monitoring
- `METRICS_ENABLED=true`: Enable metrics collection
- `CLAUDE_AGI_TEST_MODE=true`: For test environments

## Safety and Security Notes

### Security Framework Features
- Prompt injection protection with pattern-based threat detection
- Secure key management with Fernet encryption and audit logging
- Memory validation with anomaly detection and quarantine system
- Enhanced safety framework integrating all security components

### Development Safety Rules
- All external actions must pass through the safety framework
- Safety validation required for any action-taking components
- Emotional impact assessment required for user-facing features
- Test coverage requirements: 90% for core, 100% for safety-critical code

## Production Deployment

### Infrastructure Requirements
- **Development**: 16 cores, 64GB RAM, 500GB+ NVMe SSD
- **Production**: 64 cores, 256GB RAM, 2TB+ NVMe SSD RAID
- **Kubernetes**: 3 control nodes + 5 worker nodes with GPU support
- **Dependencies**: PostgreSQL 15+, Redis 7+, Prometheus/Grafana for monitoring

### Monitoring Stack
- Prometheus metrics collection on `:9090`
- Grafana dashboards on `:3000` (admin/admin)
- Node Exporter system metrics on `:9100`
- Application metrics endpoint on `:8001/metrics`

### Release Process
- Automatic builds triggered on version tags (e.g., `v1.0.10`)
- Cross-platform executables (Linux, Windows, macOS) via PyInstaller
- GitHub Actions CI/CD with comprehensive test coverage
- Portable executables include all dependencies

## Current Status

**Phase 1**: ✅ **100% COMPLETE** (v1.5.1)
- All core features fully implemented and tested
- 423+ tests passing with comprehensive coverage
- Production monitoring deployed and operational
- Complete RBAC implementation with JWT auth
- TUI fully refactored with all commands
- Cross-platform executable builds available

The system is production-ready with continuous consciousness, persistent memory, safety frameworks, and professional-grade interfaces.

## External Dependencies

Key external services that may be referenced:
- **Anthropic API**: For thought generation and consciousness streams
- **OpenAI API**: Alternative thought generation (fallback)
- **PostgreSQL**: Persistent episodic memory storage
- **Redis**: Working memory and caching
- **Prometheus/Grafana**: Production monitoring and observability

