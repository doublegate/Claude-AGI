# Claude-AGI Project Structure

This document describes the complete directory structure of the Claude-AGI project.

## Directory Overview

```
Claude-AGI/
├── src/                    # Main source code
├── tests/                  # Test suites
├── deployment/             # Deployment configurations
├── operations/             # Operational tools
├── monitoring/             # Monitoring setup
├── docs/                   # Documentation
├── ref_docs/               # Reference documentation (original planning docs)
├── ref_info/               # Reference information (transient)
├── data/                   # Data storage
├── logs/                   # Log files
└── ...                     # Other directories
```

## Source Code Structure (`src/`)

- **core/**: Core system components (orchestrator, communication, state management)
- **consciousness/**: Consciousness implementation (streams, thought generation, attention)
- **memory/**: Memory systems (episodic, semantic, procedural, working memory)
- **learning/**: Learning engine (curiosity, knowledge acquisition, skill development)
- **exploration/**: Web exploration system (interest tracking, search strategies)
- **emotional/**: Emotional framework (emotion models, welfare monitoring, empathy)
- **creative/**: Creative engine (project management, dream simulation, aesthetics)
- **social/**: Social intelligence (relationship management, user modeling)
- **meta/**: Meta-cognitive systems (self-model, goal management, reflection)
- **safety/**: Safety and ethics framework (ethical evaluation, content filtering)
- **welfare/**: Welfare monitoring (distress mitigation, intervention)
- **api/**: API interfaces (Anthropic wrapper, external integrations)
- **interface/**: User interfaces (TUI, Web UI, REST API, CLI)
- **database/**: Database layer (models, migrations, connections)
- **optimization/**: Performance optimization (monitoring, caching, profiling)
- **diagnostics/**: System diagnostics (health checks, coherence testing)

## Test Structure (`tests/`)

- **unit/**: Unit tests for individual components
- **integration/**: Integration tests for service interactions
- **behavioral/**: Behavioral tests for emergent properties
- **safety/**: Safety mechanism tests
- **performance/**: Performance and load tests
- **welfare/**: Welfare monitoring tests
- **data/**: Test data and fixtures

## Deployment (`deployment/`)

- **kubernetes/**: Kubernetes manifests
- **docker/**: Docker configurations
- **scripts/**: Deployment automation scripts
- **helm/**: Helm charts for Kubernetes

## Operations & Monitoring

- **operations/**: Backup, daily tasks, incident response
- **monitoring/**: Prometheus rules, Grafana dashboards
- **security/**: RBAC, audit logging, certificates
- **compliance/**: Compliance reporting and policies
- **audit/**: Ethical auditing and reports
- **emergency/**: Emergency protocols and runbooks

## Data & Logs

- **data/**: Memories, knowledge base, creative works, backups
- **logs/**: System, consciousness, safety, and audit logs

## Development Support

- **configs/**: System and environment configurations
- **requirements/**: Phase-specific Python dependencies
- **scripts/**: Setup and utility scripts
- **debug/**: Debugging tools and scenarios
- **metrics/**: KPI definitions and reports
- **training/**: Training simulations and materials
- **validation/**: Pre-deployment and continuous validation
- **archive/**: Historical data (memories, experiments, reports)

## Project Files

- **pyproject.toml**: Python project configuration
- **setup.py**: Package setup script
- **justfile**: Task automation commands
- **requirements.txt**: Main Python dependencies
- **.env.example**: Environment variable template
- **CLAUDE.md**: AI assistant guidance
- **CLAUDE.local.md**: Local project memory (not in git)

All Python packages include `__init__.py` files to make them proper Python modules.