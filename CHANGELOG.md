# Changelog

All notable changes to the Claude-AGI Project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Initial Implementation (2025-01-06)
- Complete project directory structure with all modules and subdirectories
- Core system implementations extracted from documentation:
  - `src/core/orchestrator.py` - Main AGI orchestrator with event loop
  - `src/core/communication.py` - Service base class and messaging
  - `src/memory/manager.py` - Memory management system
  - `src/consciousness/stream.py` - Multi-stream consciousness implementation
  - `src/safety/core_safety.py` - Multi-layer safety framework
  - `src/safety/hard_constraints.yaml` - Safety rules configuration
  - `src/exploration/engine.py` - Web exploration and curiosity system
  - `src/main.py` - Main application entry point
- Phase-specific requirement files:
  - `requirements/requirements_phase1.txt` through `requirements_advanced.txt`
- Configuration system:
  - `configs/development.yaml` - Development environment settings
  - `configs/production.yaml` - Production environment settings
- Deployment infrastructure:
  - `deployment/docker/Dockerfile` - Container definition
  - `deployment/docker/docker-compose.yml` - Local development setup
- Testing framework:
  - `tests/unit/test_memory_manager.py` - Memory system unit tests
  - `tests/conftest.py` - Pytest fixtures and configuration
- Setup automation:
  - `scripts/setup/setup_phase1.py` - Phase 1 initialization script
- Project configuration:
  - `pyproject.toml` - Python project metadata and tool configuration
  - `.env.example` - Environment variable template
- Documentation improvements:
  - Reorganized docs into `ref_docs/` for reference materials
  - Created new `docs/` for active project documentation
  - Added `ref_info/` for transient reference materials
  - Created `PROJECT_STRUCTURE.md` documenting directory layout
  - Created `IMPLEMENTATION_STATUS.md` tracking code implementation

#### Deployment and Testing Infrastructure (2025-01-06 Evening)
- Database migrations:
  - `database/migrations/phase2_tables.sql` - Phase 2 database schema
- Deployment scripts:
  - `deployment/scripts/initial_deploy.sh` - Automated deployment script
  - `deployment/scripts/disaster_recovery.sh` - Recovery procedures
- Kubernetes manifests:
  - `deployment/kubernetes/claude-agi-deployment.yaml` - Main deployment
  - `deployment/kubernetes/services.yaml` - Service definitions
  - `deployment/kubernetes/prometheus-rules.yaml` - Monitoring alerts
  - `deployment/kubernetes/rbac.yaml` - Role-based access control
  - `deployment/kubernetes/horizontal-pod-autoscaler.yaml` - Auto-scaling
  - `deployment/kubernetes/configmap.yaml` - Configuration management
  - `deployment/kubernetes/secrets.yaml` - Secret management template
  - `deployment/kubernetes/pvc.yaml` - Persistent volume claims
- CI/CD pipeline:
  - `.github/workflows/agi-tests.yml` - GitHub Actions test workflow
- Additional requirements:
  - `requirements/requirements_phase2.txt` - Phase 2 dependencies
  - `requirements-test.txt` - Testing dependencies
  - `deployment/requirements.yaml` - Hardware specifications
- TUI improvements:
  - Added `.env` file support to `scripts/claude-consciousness-tui.py`
  - Created `scripts/run_tui.py` - Python wrapper with environment setup
  - Created `start_tui.sh` - Bash launcher with dependency checking
  - Integrated `python-dotenv` for secure API key management

### Changed
- Renamed original `docs/` to `ref_docs/` for historical reference
- Updated all documentation references to use correct paths
- Enhanced `.gitignore` with `ref_info/` directory exclusion
- Updated GitHub username from placeholder to 'doublegate' throughout
- Modified `configs/development.yaml` to include Phase 2 learning settings
- Updated `src/main.py` to load environment variables from `.env`
- Moved `run_tui.py` to `scripts/` directory for better organization

### Security
- Implemented `.env` file support for API key management
- Removed hardcoded API keys from all scripts
- Added environment validation to TUI launchers

### Infrastructure
- Complete Python package structure with `__init__.py` files
- Modular architecture supporting phased development
- Async/await pattern throughout for scalability
- Safety-first design with multiple validation layers
- Production-ready Kubernetes deployment configuration
- Comprehensive CI/CD pipeline with multiple test stages

## [0.1.0] - 2025-01-06

### Added
- Initial repository creation
- Basic project structure
- Documentation framework
- Proof-of-concept consciousness TUI

[Unreleased]: https://github.com/doublegate/Claude-AGI/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/doublegate/Claude-AGI/releases/tag/v0.1.0