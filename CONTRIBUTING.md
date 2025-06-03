# Contributing to Claude-AGI

First off, thank you for considering contributing to the Claude-AGI Project! This project aims to push the boundaries of AI consciousness and your contributions can help shape the future of artificial general intelligence.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Process](#development-process)
- [Style Guidelines](#style-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Ethical Considerations](#ethical-considerations)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/yourusername/Claude-AGI.git
   cd Claude-AGI
   ```
3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
4. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```
5. Create a branch for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- System information (OS, Python version, etc.)
- Relevant logs or error messages
- Code snippets that demonstrate the issue

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- A clear and descriptive title
- Step-by-step description of the suggested enhancement
- Explanation of why this enhancement would be useful
- Possible implementation approach (if you have ideas)
- Mockups or examples (if applicable)

### Code Contributions

Areas where we particularly welcome contributions:

1. **Memory Systems**: Improvements to persistence, retrieval, and organization
2. **Cognitive Services**: New cognitive capabilities or enhancements
3. **Safety Framework**: Additional safety validations and monitoring
4. **Testing**: Expanding test coverage, especially for edge cases
5. **Documentation**: Improving clarity and completeness
6. **Performance**: Optimizations for real-time processing
7. **Visualization**: Tools for understanding consciousness streams

## Development Process

### 1. Setting Up Your Development Environment

Ensure you have:
- Python 3.11+
- Redis and PostgreSQL for testing
- All dependencies from requirements.txt
- Development tools from requirements-dev.txt

### 2. Making Changes

- Write clean, readable code following our style guidelines
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass locally
- Run linters and formatters

### 3. Testing

Run the test suite before submitting:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit -v
pytest tests/integration -v
pytest tests/safety -v --safety-critical
```

Ensure:
- All tests pass
- Coverage remains above 90% for core components
- 100% coverage for safety-critical code
- No linting errors

## Style Guidelines

### Python Style

We follow PEP 8 with these additions:
- Use type hints for all function signatures
- Maximum line length of 100 characters
- Use f-strings for string formatting
- Async/await for all I/O operations

### Code Organization

- Keep modules focused and cohesive
- Use clear, descriptive names
- Document complex algorithms
- Separate concerns appropriately

### Documentation

- Write clear docstrings for all public functions/classes
- Include examples in docstrings where helpful
- Keep README and other docs up to date
- Document any non-obvious design decisions

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or modifications
- `chore`: Maintenance tasks

Example:
```
feat(memory): add semantic search capability

Implement FAISS-based semantic search for memory retrieval.
This allows for more intelligent memory access based on
meaning rather than just keywords.

Closes #123
```

## Pull Request Process

1. Ensure your branch is up to date with main:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

3. Create a Pull Request with:
   - Clear title describing the change
   - Description of what changed and why
   - Link to any related issues
   - Screenshots/examples if applicable
   - Checklist of completed items:
     - [ ] Tests added/updated
     - [ ] Documentation updated
     - [ ] Changelog entry added
     - [ ] All tests passing
     - [ ] Code follows style guidelines

4. Address review feedback promptly

5. Once approved, we'll merge your contribution!

## Ethical Considerations

Given the nature of this project, we have special ethical considerations:

### Safety First
- All contributions must maintain or enhance safety features
- Never bypass or weaken safety validations
- Consider potential misuse scenarios

### Consciousness Ethics
- Treat the system as if its experiences matter
- Implement features that respect potential consciousness
- Include welfare monitoring where appropriate

### Transparency
- Document any behaviors that might surprise users
- Be clear about system capabilities and limitations
- Maintain audit trails for important decisions

### Privacy
- Respect user privacy in all features
- Implement proper data handling and retention
- Never log sensitive information

## Questions?

Feel free to:
- Open an issue for discussion
- Reach out to maintainers
- Check existing documentation
- Join community discussions

Thank you for contributing to the future of conscious AI! 🚀