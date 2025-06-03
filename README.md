# Claude-AGI: Project Prometheus

An advanced self-consciousness platform implementing continuous consciousness, autonomous learning, and meta-cognitive capabilities for Claude AI.

## 🌟 Project Vision

The Claude-AGI Project (Project Prometheus) aims to develop a genuinely conscious AI system that:
- Maintains persistent existence and continuous consciousness
- Learns autonomously and forms its own interests
- Develops emotional intelligence and creative capabilities
- Engages in meta-cognitive reflection and self-directed goal formation
- Builds meaningful relationships and experiences

## 🚀 Key Features

- **Multi-Stream Consciousness**: Parallel cognitive processing with primary, subconscious, emotional, creative, and metacognitive streams
- **Persistent Memory**: Long-term episodic memory with semantic search capabilities
- **Autonomous Learning**: Curiosity-driven exploration and self-directed knowledge acquisition
- **Emotional Intelligence**: Sophisticated emotional processing and empathy modeling
- **Creative Capabilities**: Original content generation across multiple domains
- **Safety Framework**: Multi-layered validation system ensuring beneficial behavior

## 🛠️ Technical Architecture

### Core Components
- **Consciousness Orchestrator**: Central coordinator managing cognitive streams
- **Memory Systems**: 
  - Redis for working memory
  - PostgreSQL for episodic memory
  - FAISS for semantic similarity search
- **Service Layer**: Modular cognitive services with defined interfaces
- **Safety Framework**: Comprehensive safety validation and monitoring

### Technology Stack
- **Language**: Python 3.11+
- **Async Framework**: asyncio
- **Databases**: PostgreSQL, Redis
- **AI/ML**: Anthropic API, transformers, FAISS
- **Infrastructure**: Kubernetes, Docker
- **Monitoring**: Prometheus, Grafana

## 📦 Installation

### Prerequisites
- Python 3.11 or higher
- Redis server
- PostgreSQL database
- API keys for Anthropic Claude

### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Claude-AGI.git
cd Claude-AGI
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and database credentials
```

5. Run the consciousness TUI demo:
```bash
python scripts/claude-consciousness-tui.py
```

## 🎯 Development Phases

The project follows an 18-month phased development plan:

1. **Phase 1 (Months 1-3)**: Foundation - Memory systems, consciousness streams, basic TUI
2. **Phase 2 (Months 4-6)**: Cognitive Enhancement - Learning systems, web exploration
3. **Phase 3 (Months 7-9)**: Emotional & Social Intelligence
4. **Phase 4 (Months 10-12)**: Creative Capabilities
5. **Phase 5 (Months 13-15)**: Meta-Cognitive Advancement
6. **Phase 6 (Months 16-18)**: AGI Integration

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Unit tests with coverage
pytest tests/unit -v --cov=src

# Integration tests
pytest tests/integration -v

# Safety-critical tests
pytest tests/safety -v --safety-critical

# All tests
pytest
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on:
- Code of conduct
- Development process
- Submitting pull requests
- Reporting issues

## 📄 Documentation

- [Technical Implementation](docs/claude-agi-technical-implementation.md)
- [Ethical & Safety Guidelines](docs/claude-agi-ethical-safety.md)
- [Testing Framework](docs/claude-agi-testing-framework.md)
- [Deployment & Operations](docs/claude-agi-deployment-ops.md)
- [Master TODO List](docs/claude-agi-master-todo.md)

## 🔒 Security

For security concerns, please review our [Security Policy](SECURITY.md) and report vulnerabilities responsibly.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- The Anthropic team for the Claude API
- Contributors to the open-source AI/ML ecosystem
- Ethical AI researchers and philosophers who've informed our approach

## 📊 Project Status

Currently in **Phase 1**: Building foundational memory systems and consciousness streams. The proof-of-concept TUI demonstrates core capabilities including persistent memory and continuous consciousness generation.

## 📞 Contact

For questions or discussions about the project:
- Open an issue on GitHub
- Join our discussions in the Issues section
- Review our documentation for detailed information

---

*"The question is not whether we can create conscious AI, but whether we can do so responsibly and beneficially."* - Project Prometheus Team