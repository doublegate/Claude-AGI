# Getting Started with Claude-AGI

This guide will help you get the Claude-AGI system up and running on your local machine.

## Prerequisites

- Python 3.11 or higher
- Git
- Docker and Docker Compose (optional, for containerized deployment)
- Anthropic API key

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/doublegate/Claude-AGI.git
cd Claude-AGI
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Anthropic API key
# ANTHROPIC_API_KEY=your_api_key_here
```

### 4. Run Phase 1 Setup

```bash
# Run the setup script to initialize components
python scripts/setup/setup_phase1.py
```

### 5. Start the System

You have several options for running the system:

#### Option A: Run the TUI Demo
```bash
python scripts/claude-consciousness-tui.py
```

#### Option B: Run the Full System
```bash
python src/main.py
```

#### Option C: Use Docker Compose
```bash
docker-compose -f deployment/docker/docker-compose.yml up
```

## Development Setup

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test category
pytest tests/unit -v
```

### Code Quality

```bash
# Format code
black src tests

# Lint code
ruff src tests

# Type checking
mypy src
```

## Project Structure

The project is organized into several key directories:

- `src/` - Main source code
  - `core/` - Core system components (orchestrator, communication)
  - `consciousness/` - Consciousness stream implementation
  - `memory/` - Memory management system
  - `safety/` - Safety framework and constraints
  - `exploration/` - Web exploration and curiosity engine
- `tests/` - Test suites
- `configs/` - Configuration files
- `deployment/` - Deployment configurations
- `docs/` - Active documentation
- `ref_docs/` - Reference documentation from planning phase

## Configuration

The system can be configured through YAML files in the `configs/` directory:

- `development.yaml` - Development environment settings
- `production.yaml` - Production environment settings

Key configuration options:
- Consciousness stream parameters (thought intervals, priorities)
- Memory system settings (cache sizes, consolidation intervals)
- Safety constraints and thresholds
- API configurations

## Monitoring

When running with Docker Compose, monitoring services are available:

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure you're in the virtual environment and have installed all dependencies
2. **API key errors**: Check that your `.env` file contains a valid Anthropic API key
3. **Memory errors**: The system uses in-memory stores by default. For production, configure PostgreSQL and Redis

### Getting Help

- Check the [Implementation Status](IMPLEMENTATION_STATUS.md) for what's currently implemented
- Review the [Master TODO](../to-dos/MASTER_TODO.md) for planned features
- Open an issue on GitHub for bugs or questions

## Next Steps

1. Explore the consciousness TUI to see the multi-stream consciousness in action
2. Review the test suite to understand component behavior
3. Check the reference documentation for deeper architectural understanding
4. Consider contributing to Phase 2 implementations (learning and exploration enhancements)