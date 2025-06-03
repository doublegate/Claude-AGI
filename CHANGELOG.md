# Changelog

All notable changes to the Claude-AGI Project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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

### Changed
- Renamed original `docs/` to `ref_docs/` for historical reference
- Updated all documentation references to use correct paths
- Enhanced `.gitignore` with `ref_info/` directory exclusion
- Updated GitHub username from placeholder to 'doublegate' throughout

### Infrastructure
- Complete Python package structure with `__init__.py` files
- Modular architecture supporting phased development
- Async/await pattern throughout for scalability
- Safety-first design with multiple validation layers

## [0.1.0] - 2025-01-06

### Added
- Initial repository creation
- Basic project structure
- Documentation framework
- Proof-of-concept consciousness TUI

[Unreleased]: https://github.com/doublegate/Claude-AGI/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/doublegate/Claude-AGI/releases/tag/v0.1.0