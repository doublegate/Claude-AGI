# Architectural Improvements Guide

Based on analyses identifying architectural anti-patterns that need resolution before Phase 2.

## Identified Anti-Patterns and Solutions

### 1. God Objects

**Problem**: Classes handling too many responsibilities, violating Single Responsibility Principle.

**Identified God Objects**:
- `AGIOrchestrator`: Managing state, services, events, AND cognitive processing
- `MemoryManager`: Handling Redis, PostgreSQL, FAISS, AND thought generation
- `ClaudeAGI` (TUI): UI rendering, event handling, AND business logic

**Solutions**:

#### Orchestrator Refactoring
```python
# Before: Single monolithic orchestrator
class AGIOrchestrator:
    def __init__(self):
        self.services = {}
        self.state = SystemState.IDLE
        self.event_queue = Queue()
        self.memory = MemoryManager()
        self.consciousness = ConsciousnessStream()
        # ... 20+ other responsibilities

# After: Separated concerns
class ServiceRegistry:
    """Manages service lifecycle"""
    def register_service(self, name: str, service: ServiceBase): ...
    def get_service(self, name: str) -> ServiceBase: ...

class StateManager:
    """Manages system state transitions"""
    def transition_to(self, new_state: SystemState): ...
    def validate_transition(self, from_state, to_state): ...

class EventBus:
    """Handles inter-service communication"""
    def publish(self, event: Event): ...
    def subscribe(self, event_type: str, handler: Callable): ...

class AGIOrchestrator:
    """Coordinates high-level system behavior"""
    def __init__(self, registry: ServiceRegistry, 
                 state_mgr: StateManager, 
                 event_bus: EventBus):
        self.registry = registry
        self.state_manager = state_mgr
        self.event_bus = event_bus
```

#### Memory Manager Refactoring
```python
# After: Separated storage concerns
class WorkingMemoryStore:
    """Redis-specific operations"""
    async def store(self, key: str, value: Any): ...
    async def retrieve(self, key: str) -> Any: ...

class EpisodicMemoryStore:
    """PostgreSQL-specific operations"""
    async def save_episode(self, episode: Episode): ...
    async def query_episodes(self, criteria: QueryCriteria): ...

class SemanticIndex:
    """FAISS-specific operations"""
    async def add_embedding(self, id: str, embedding: np.ndarray): ...
    async def search_similar(self, query_embedding: np.ndarray): ...

class MemoryCoordinator:
    """Coordinates across memory stores"""
    def __init__(self, working: WorkingMemoryStore,
                 episodic: EpisodicMemoryStore,
                 semantic: SemanticIndex):
        self.working = working
        self.episodic = episodic
        self.semantic = semantic
```

### 2. Circular Dependencies

**Problem**: Modules depending on each other in cycles, making testing and maintenance difficult.

**Identified Cycles**:
- Orchestrator ↔ ConsciousnessStream ↔ MemoryManager ↔ Orchestrator
- SafetyFramework ↔ Orchestrator ↔ Services ↔ SafetyFramework

**Solution**: Dependency Inversion

```python
# Define interfaces/protocols
from typing import Protocol

class IMemoryService(Protocol):
    """Memory service interface"""
    async def store(self, content: str, metadata: dict): ...
    async def retrieve(self, query: str) -> List[Memory]: ...

class IConsciousnessService(Protocol):
    """Consciousness service interface"""
    async def generate_thought(self) -> Thought: ...
    async def process_input(self, input: str): ...

class ISafetyService(Protocol):
    """Safety validation interface"""
    async def validate_content(self, content: str) -> bool: ...
    async def validate_action(self, action: Action) -> bool: ...

# Inject dependencies through interfaces
class ConsciousnessStream:
    def __init__(self, memory: IMemoryService, safety: ISafetyService):
        self.memory = memory  # No direct dependency on MemoryManager
        self.safety = safety  # No direct dependency on SafetyFramework
```

### 3. Event Loop Blocking

**Problem**: Synchronous operations blocking the async event loop.

**Solutions**:

```python
# Bad: Blocking I/O in async context
async def process_thought(self):
    thought = self.generate_thought()  # CPU-intensive
    time.sleep(1)  # Blocks event loop
    with open('log.txt', 'a') as f:  # Blocking I/O
        f.write(thought)
    
# Good: Non-blocking alternatives
async def process_thought(self):
    # Run CPU-intensive work in thread pool
    thought = await asyncio.get_event_loop().run_in_executor(
        None, self.generate_thought
    )
    
    # Use async sleep
    await asyncio.sleep(1)
    
    # Use async file I/O
    async with aiofiles.open('log.txt', 'a') as f:
        await f.write(thought)
```

### 4. Missing Abstraction Layers

**Problem**: Direct coupling between high-level and low-level components.

**Solution**: Introduce proper layering

```
┌─────────────────────────────────────┐
│         Presentation Layer          │ (TUI, API endpoints)
├─────────────────────────────────────┤
│         Application Layer           │ (Use cases, workflows)
├─────────────────────────────────────┤
│          Domain Layer               │ (Core business logic)
├─────────────────────────────────────┤
│       Infrastructure Layer          │ (Databases, external APIs)
└─────────────────────────────────────┘
```

**Implementation**:
```python
# Domain layer (pure business logic)
class ConsciousnessModel:
    def generate_thought(self, context: Context) -> Thought:
        # Pure logic, no I/O
        return Thought(content="...", importance=5)

# Application layer (orchestrates domain objects)
class GenerateThoughtUseCase:
    def __init__(self, consciousness: ConsciousnessModel,
                 memory_repo: IMemoryRepository,
                 safety_validator: ISafetyValidator):
        self.consciousness = consciousness
        self.memory_repo = memory_repo
        self.safety_validator = safety_validator
    
    async def execute(self, context: Context) -> Thought:
        # Orchestrate the workflow
        thought = self.consciousness.generate_thought(context)
        if await self.safety_validator.is_safe(thought):
            await self.memory_repo.save(thought)
            return thought
        raise UnsafeContentError()

# Infrastructure layer (concrete implementations)
class PostgresMemoryRepository(IMemoryRepository):
    async def save(self, thought: Thought):
        # Actual database operations
        async with self.get_connection() as conn:
            await conn.execute(...)
```

## Dependency Injection Framework

**Recommendation**: Implement a DI container to manage dependencies.

```python
# Using python-injector or similar
from injector import Module, provider, Injector, inject

class AppModule(Module):
    @provider
    def provide_memory_service(self) -> IMemoryService:
        return MemoryManager()
    
    @provider
    def provide_consciousness_service(self,
                                    memory: IMemoryService) -> IConsciousnessService:
        return ConsciousnessStream(memory)

# Usage
injector = Injector([AppModule()])
orchestrator = injector.get(AGIOrchestrator)
```

## Interface-Based Design

**Define clear contracts between components**:

```python
# src/interfaces/services.py
from abc import ABC, abstractmethod

class CognitiveService(ABC):
    """Base interface for all cognitive services"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Gracefully shutdown the service"""
        pass
    
    @abstractmethod
    async def health_check(self) -> dict:
        """Return service health status"""
        pass

class ThoughtProcessor(CognitiveService):
    """Interface for thought generation services"""
    
    @abstractmethod
    async def generate_thought(self, context: dict) -> Thought:
        """Generate a thought based on context"""
        pass
```

## Async Best Practices

### 1. Proper Task Management
```python
class ServiceManager:
    def __init__(self):
        self._tasks: List[asyncio.Task] = []
    
    async def start_service(self, service: CognitiveService):
        await service.initialize()
        task = asyncio.create_task(service.run())
        self._tasks.append(task)
    
    async def shutdown_all(self):
        # Cancel all tasks gracefully
        for task in self._tasks:
            task.cancel()
        
        # Wait for cancellation with timeout
        await asyncio.gather(*self._tasks, return_exceptions=True)
```

### 2. Backpressure Handling
```python
class ThoughtQueue:
    def __init__(self, max_size: int = 1000):
        self.queue = asyncio.Queue(maxsize=max_size)
        self.dropped_count = 0
    
    async def put_nowait_safe(self, thought: Thought):
        try:
            self.queue.put_nowait(thought)
        except asyncio.QueueFull:
            self.dropped_count += 1
            logger.warning(f"Thought queue full, dropped {self.dropped_count} thoughts")
```

## Migration Strategy

### Phase 1 Completion (Immediate)
1. **Extract interfaces** from existing classes
2. **Create adapter classes** for backward compatibility
3. **Add dependency injection** incrementally

### Phase 2 Preparation
1. **Refactor god objects** into smaller services
2. **Implement event bus** for decoupled communication
3. **Add abstraction layers** between components

### Implementation Order
1. **Week 1**: Define all interfaces
2. **Week 2**: Implement DI framework
3. **Week 3**: Refactor orchestrator
4. **Week 4**: Refactor memory system
5. **Month 2**: Complete remaining refactoring

## Success Metrics

- **Coupling**: Reduce inter-module dependencies by 50%
- **Cohesion**: Each class has single responsibility
- **Testability**: 100% of classes can be unit tested in isolation
- **Maintainability**: New features require changes to <3 files
- **Performance**: No degradation from refactoring

## Architecture Documentation

### Component Diagrams
Create visual documentation for:
- Service interaction flows
- Data flow between layers
- Event propagation paths
- Dependency graphs

### Decision Records
Document architectural decisions:
- Why certain patterns were chosen
- Trade-offs considered
- Future migration paths

## Next Steps

1. **Create interface definitions** for all services
2. **Set up DI framework** with initial bindings
3. **Refactor one service** as proof of concept
4. **Update tests** to use interfaces
5. **Document patterns** for team reference