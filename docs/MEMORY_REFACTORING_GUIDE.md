# Memory System Refactoring Guide

## Overview

The monolithic `MemoryManager` has been refactored into a clean, modular architecture with clear separation of concerns. This guide helps you migrate from the old system to the new one.

## Architecture Changes

### Old Architecture (God Object)
```
MemoryManager
├── Working Memory Management
├── Episodic Memory Management  
├── Semantic Search
├── Database Connections
├── Embeddings
├── Consolidation
└── Context Management
```

### New Architecture (Single Responsibility)
```
MemoryCoordinator (Thin coordinator)
├── WorkingMemoryStore (Redis-backed short-term storage)
├── EpisodicMemoryStore (PostgreSQL-backed long-term storage)
├── SemanticIndex (FAISS/numpy similarity search)
├── MemorySynchronizer (Cross-store consistency)
└── ConnectionPoolManager (Database connection handling)
```

## Component Responsibilities

### 1. MemoryCoordinator
- Coordinates operations across stores
- Handles message routing
- Manages embeddings generation
- Provides unified interface

### 2. WorkingMemoryStore
- Short-term memory storage
- Active context management
- Recent thoughts tracking
- Redis-backed with in-memory fallback

### 3. EpisodicMemoryStore
- Long-term memory persistence
- Importance-based retention
- Emotional tagging
- Association tracking
- PostgreSQL-backed

### 4. SemanticIndex
- Vector similarity search
- FAISS index management
- Numpy fallback for compatibility
- Metadata storage

### 5. MemorySynchronizer
- Ensures consistency across stores
- Version tracking
- Conflict resolution
- Transaction support

### 6. ConnectionPoolManager
- Database connection pooling
- Health monitoring
- Auto-reconnection
- Performance metrics

## Migration Steps

### Step 1: Update Imports

Old:
```python
from src.memory.manager import MemoryManager
```

New:
```python
from src.memory.memory_coordinator import MemoryCoordinator
```

### Step 2: Update Initialization

Old:
```python
memory_manager = MemoryManager()
await memory_manager.initialize(use_database=True)
```

New:
```python
memory_coordinator = MemoryCoordinator(
    service_registry=service_registry,
    event_bus=event_bus,
    postgres_dsn="postgresql://...",
    redis_url="redis://...",
    use_embeddings=True
)
await memory_coordinator.initialize()
```

### Step 3: Update Method Calls

Most method signatures remain the same, but some have been enhanced:

| Old Method | New Method | Notes |
|------------|------------|-------|
| `store_thought(thought)` | `store_thought(thought)` | Same signature |
| `recall_recent(n)` | `recall_recent(n)` | Same signature |
| `recall_by_id(id)` | `recall_by_id(id)` | Same signature |
| `recall_similar(query, k)` | `search_similar(query, k, min_similarity)` | Added similarity threshold |
| `consolidate_memories()` | `consolidate_memories()` | Same signature |
| `update_context(key, value)` | `update_context(key, value, ttl)` | Added TTL support |
| `get_context(key)` | `get_context(key)` | Same signature |
| `clear_working_memory()` | `clear_working_memory()` | Same signature |

### Step 4: Update Message Handling

The message handling remains the same:

```python
# In orchestrator or message router
await memory_coordinator.handle_message(message)
```

### Step 5: Access Specific Stores (Optional)

If you need direct access to specific stores:

```python
# Access working memory directly
recent = await memory_coordinator.working_memory.get_recent_thoughts(20)

# Access episodic memory directly
important = await memory_coordinator.episodic_memory.get_important_memories(
    min_importance=0.8
)

# Access semantic index directly
similar = await memory_coordinator.semantic_index.search(
    query_vector,
    k=10
)
```

### Step 6: Update Configuration

The new system uses connection pools and requires proper configuration:

```yaml
# development.yaml or production.yaml
memory:
  postgres_dsn: "postgresql://user:pass@localhost/claudeagi"
  redis_url: "redis://localhost:6379/0"
  embedding_model: "all-MiniLM-L6-v2"
  working_memory:
    max_thoughts: 1000
    default_ttl: 86400
  episodic_memory:
    importance_threshold: 0.7
    decay_rate: 0.01
  semantic_index:
    index_type: "IVF"
    nlist: 100
```

### Step 7: Update Tests

Update test imports and mocks:

```python
# Old test
async def test_memory_manager():
    memory_manager = MemoryManager()
    await memory_manager.initialize()
    
    thought_id = await memory_manager.store_thought({
        'content': 'Test thought'
    })

# New test
async def test_memory_coordinator():
    memory_coordinator = MemoryCoordinator()
    await memory_coordinator.initialize()
    
    thought_id = await memory_coordinator.store_thought({
        'content': 'Test thought'
    })
```

## Benefits of the New Architecture

1. **Separation of Concerns**: Each component has a single, clear responsibility
2. **Better Testability**: Components can be tested in isolation
3. **Improved Performance**: Connection pooling and optimized queries
4. **Enhanced Reliability**: Auto-reconnection and health monitoring
5. **Easier Maintenance**: Cleaner code structure
6. **Better Scalability**: Can scale individual components
7. **Consistency Guarantees**: Synchronizer ensures data consistency

## Common Issues and Solutions

### Issue 1: Database Connection Errors
```python
# Ensure connection pool is initialized
if memory_coordinator.connection_pool:
    health = memory_coordinator.connection_pool.get_health_status()
    print(f"PostgreSQL: {health['postgres']['health']}")
    print(f"Redis: {health['redis']['health']}")
```

### Issue 2: Missing Embeddings
```python
# Check if embeddings are enabled
stats = memory_coordinator.get_stats()
if not stats['coordinator'].get('use_embeddings'):
    print("Embeddings disabled - install sentence-transformers")
```

### Issue 3: Memory Not Persisting
```python
# Check synchronizer status
if memory_coordinator.synchronizer:
    inconsistencies = await memory_coordinator.synchronizer.check_consistency()
    if inconsistencies:
        await memory_coordinator.synchronizer.repair_inconsistencies()
```

## Performance Considerations

1. **Batch Operations**: Use batch methods when storing multiple memories
2. **Connection Pooling**: Properly configure pool sizes for your workload
3. **Index Training**: For FAISS IVF index, ensure enough vectors for training
4. **Memory Limits**: Configure appropriate limits for working memory
5. **Decay and Pruning**: Schedule consolidation during low-activity periods

## Monitoring

The new system provides comprehensive statistics:

```python
stats = memory_coordinator.get_stats()

# Coordinator stats
print(f"Store operations: {stats['coordinator']['operations']['store']}")
print(f"Recall operations: {stats['coordinator']['operations']['recall']}")

# Working memory stats
print(f"Hit rate: {stats['working_memory']['hit_rate']}")

# Episodic memory stats
print(f"Total memories: {stats['episodic_memory']['total_memories']}")

# Connection health
print(f"PostgreSQL health: {stats['connections']['postgres']['health']}")
print(f"Redis health: {stats['connections']['redis']['health']}")
```

## Future Enhancements

The modular architecture makes it easy to add new features:

1. **New Memory Stores**: Add specialized stores (e.g., ProceduralMemoryStore)
2. **Alternative Backends**: Swap Redis for Memcached, PostgreSQL for MongoDB
3. **Advanced Indexing**: Add specialized indexes for different query types
4. **Compression**: Add memory compression for storage efficiency
5. **Encryption**: Add end-to-end encryption for sensitive memories