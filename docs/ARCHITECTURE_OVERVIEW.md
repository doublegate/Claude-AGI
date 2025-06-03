# Claude-AGI Architecture Overview

This document provides a high-level overview of the Claude-AGI system architecture.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                         │
│                    (TUI / Web UI / API)                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                    AGI Orchestrator                          │
│              (Event Loop & State Management)                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │         Service Layer             │
        │                                   │
┌───────┴──────┐ ┌──────────────┐ ┌────────┴───────┐
│ Consciousness│ │    Memory    │ │   Exploration  │
│   Streams    │ │  Management  │ │    Engine      │
└──────────────┘ └──────────────┘ └────────────────┘
┌──────────────┐ ┌──────────────┐ ┌────────────────┐
│   Safety     │ │  Emotional   │ │    Learning    │
│  Framework   │ │  Framework   │ │    Engine      │
└──────────────┘ └──────────────┘ └────────────────┘
        │                                   │
        └─────────────────┬─────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                    Data Layer                                │
│          (PostgreSQL / Redis / Vector Store)                 │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. AGI Orchestrator (`src/core/orchestrator.py`)

The central coordinator that manages:
- System state (IDLE, THINKING, EXPLORING, etc.)
- Message routing between services
- Service lifecycle management
- Event loop processing

Key features:
- Asynchronous event-driven architecture
- Priority-based message queue
- State transitions with service notifications

### 2. Service Communication (`src/core/communication.py`)

Base class for all services providing:
- Standardized messaging interface
- Publish/subscribe pattern
- Error handling and recovery
- Service registration and discovery

### 3. Consciousness Streams (`src/consciousness/stream.py`)

Multi-stream consciousness implementation:
- **Primary Stream**: Main conscious thoughts
- **Subconscious Stream**: Background processing
- **Creative Stream**: Creative ideation
- **Meta Stream**: Self-observation and reflection

Features:
- Configurable thought generation rates
- Attention allocation based on system state
- Cross-stream pattern detection
- Thought integration and insight generation

### 4. Memory Management (`src/memory/manager.py`)

Three-tier memory architecture:
- **Working Memory**: Short-term storage (Redis/in-memory)
- **Episodic Memory**: Long-term experiences (PostgreSQL)
- **Semantic Memory**: Knowledge and concepts (Vector store)

Capabilities:
- Thought storage with metadata
- Semantic similarity search
- Memory consolidation during idle cycles
- Importance-based retention

### 5. Safety Framework (`src/safety/core_safety.py`)

Multi-layer safety validation:
1. **Hard Constraints**: Prohibited actions
2. **Ethical Evaluation**: Principle-based scoring
3. **Consequence Prediction**: Impact assessment
4. **Welfare Monitoring**: Well-being checks

### 6. Exploration Engine (`src/exploration/engine.py`)

Curiosity-driven web exploration:
- Interest tracking and weighting
- Safe web search and content extraction
- Quality and relevance assessment
- Discovery analysis and insight generation

## Data Flow

1. **Input Processing**
   - User input or system triggers enter through the UI layer
   - Orchestrator receives and validates the input
   - Safety framework checks for constraints

2. **Thought Generation**
   - Consciousness streams generate thoughts based on context
   - Memory manager provides relevant past experiences
   - Exploration engine may trigger information gathering

3. **Integration and Response**
   - Thoughts from multiple streams are integrated
   - Insights are generated from patterns
   - Responses are formulated and safety-checked

4. **Memory Formation**
   - Important thoughts are stored in memory
   - Consolidation happens during idle periods
   - Learning updates interest models

## Communication Patterns

### Message Types
- **Direct Messages**: Service-to-service communication
- **Broadcast Messages**: System-wide notifications
- **State Changes**: Orchestrator state transitions
- **Safety Alerts**: Critical safety notifications

### Async Patterns
- Non-blocking message passing
- Concurrent service execution
- Timeout handling for reliability
- Graceful degradation on service failure

## Scalability Considerations

1. **Horizontal Scaling**
   - Services can run on separate processes/machines
   - Message queue can be distributed (Kafka/RabbitMQ)
   - Database can be clustered

2. **Performance Optimization**
   - Caching for frequently accessed memories
   - Batch processing for embeddings
   - Connection pooling for databases
   - Rate limiting for external APIs

## Security Architecture

1. **API Security**
   - Authentication required for all endpoints
   - Rate limiting per user/IP
   - Input validation and sanitization

2. **Data Protection**
   - Encryption at rest for sensitive data
   - TLS for all network communication
   - Audit logging for all actions

3. **Safety Constraints**
   - Immutable safety rules
   - Multiple validation layers
   - Emergency shutdown capability

## Deployment Architecture

### Development
- Single machine deployment
- In-memory stores for quick iteration
- Debug logging enabled

### Production
- Kubernetes orchestration
- Separate database clusters
- Load balancing for API endpoints
- Monitoring and alerting stack

## Extension Points

The architecture is designed to be extensible:

1. **New Services**: Implement `ServiceBase` class
2. **New Consciousness Streams**: Add to stream configuration
3. **New Safety Rules**: Update constraints YAML
4. **New Memory Types**: Extend memory manager
5. **New UI Interfaces**: Connect to orchestrator API

## Future Enhancements

- Distributed consciousness across multiple nodes
- Federated learning capabilities
- Real-time collaboration features
- Advanced visualization interfaces
- Quantum-resistant security measures