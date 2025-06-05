# Memory Synchronization Implementation

## Overview

The Memory Synchronization system ensures data consistency across three different storage backends:
- **Redis**: Fast working memory for real-time access
- **PostgreSQL**: Persistent episodic memory storage
- **FAISS**: Vector index for semantic similarity search

## Architecture

### Components

1. **MemorySynchronizer** (`src/memory/synchronizer.py`)
   - Handles synchronization logic between stores
   - Manages version tracking and conflict resolution
   - Provides transaction support with rollback capabilities
   - Runs background tasks for periodic sync and consistency checks

2. **ConnectionPoolManager** (`src/memory/connection_pool.py`)
   - Manages database connection pools
   - Provides health monitoring and auto-reconnection
   - Tracks connection statistics and performance metrics
   - Implements connection recycling and timeout handling

3. **Database Schema** (`database/migrations/memory_versioning.sql`)
   - Version tracking tables for synchronization state
   - Transaction logs for audit trails
   - Conflict resolution history
   - Sync queue for pending operations

## Features

### 1. Version Tracking
- Each memory has a version number that increments on updates
- Store-specific versions track sync state per backend
- Checksums ensure data integrity

```python
class MemoryVersion(BaseModel):
    memory_id: str
    version: int = 1
    checksum: str
    last_modified: datetime
    store_versions: Dict[str, int]  # {"redis": 1, "postgres": 1, "faiss": 1}
```

### 2. Conflict Resolution
Multiple strategies available:
- **LATEST_WINS**: Most recent update takes precedence (default)
- **MERGE**: Combine data from conflicting stores
- **VERSION_VECTOR**: Use vector clocks for ordering
- **MANUAL**: Flag for manual resolution

### 3. Transaction Support
- All sync operations are wrapped in transactions
- Rollback data is prepared before any updates
- Failed syncs automatically trigger rollback
- Transaction history is maintained for debugging

### 4. Consistency Checking
- Periodic background checks for inconsistencies
- Detects missing memories across stores
- Identifies version mismatches
- Automatic repair with configurable strategies

### 5. Connection Management
- Connection pooling for both Redis and PostgreSQL
- Automatic reconnection on failure
- Health monitoring with degradation states
- Performance metrics tracking

## Usage

### Basic Synchronization

```python
# Initialize synchronizer
synchronizer = MemorySynchronizer(
    redis_client=redis_client,
    postgres_pool=postgres_pool,
    faiss_index=faiss_index
)
await synchronizer.initialize()

# Sync a single memory
memory_data = {
    "memory_id": "mem_123",
    "content": "Important memory",
    "memory_type": "episodic",
    "importance": 0.8,
    "embedding": [0.1, 0.2, 0.3, ...]
}
success = await synchronizer.sync_memory("mem_123", memory_data)

# Sync multiple memories
memories = [memory1, memory2, memory3]
results = await synchronizer.sync_batch(memories)
```

### Consistency Management

```python
# Check for inconsistencies
inconsistencies = await synchronizer.check_consistency()
# Returns: {"mem_1": ["redis"], "mem_2": ["faiss", "postgres"]}

# Repair inconsistencies
repair_results = await synchronizer.repair_inconsistencies(inconsistencies)
# Returns: {"mem_1": True, "mem_2": True}
```

### Connection Pool Usage

```python
# Initialize connection pool manager
pool_manager = ConnectionPoolManager(
    postgres_dsn="postgresql://user:pass@localhost/claudeagi",
    redis_url="redis://localhost:6379/0"
)
await pool_manager.initialize()

# Use PostgreSQL connection
async with pool_manager.get_postgres_connection() as conn:
    result = await conn.fetch("SELECT * FROM episodic_memory")

# Use Redis client
redis_client = pool_manager.get_redis_client()
await redis_client.set("key", "value")

# Check health status
health = pool_manager.get_health_status()
# Returns detailed health metrics for each connection type
```

## Configuration

### Synchronizer Settings
```python
# In MemorySynchronizer.__init__
self.batch_size = 100              # Memories per batch
self.sync_interval = 5.0           # Seconds between sync checks
self.max_retries = 3               # Retry attempts for failed syncs
self.consistency_check_interval = 60.0  # Seconds between consistency checks
```

### Connection Pool Settings
```python
config = PoolConfig(
    # PostgreSQL
    postgres_min_size=10,
    postgres_max_size=20,
    postgres_command_timeout=60.0,
    
    # Redis
    redis_max_connections=50,
    redis_health_check_interval=30,
    
    # General
    reconnect_interval=5.0,
    health_check_interval=30.0
)
```

## Database Schema

### Key Tables

1. **memory_versions**: Tracks version info for each memory
2. **sync_transactions**: Logs all sync operations
3. **conflict_resolutions**: Records how conflicts were resolved
4. **sync_queue**: Pending sync operations

### Monitoring Views

- `v_memory_sync_status`: Real-time sync status for all memories
- `get_sync_statistics()`: Function returning sync performance metrics
- `check_memory_consistency()`: Function to check specific memory consistency

## Performance Considerations

1. **Batching**: Sync operations are batched to reduce overhead
2. **Async Operations**: All I/O is asynchronous for better concurrency
3. **Connection Pooling**: Reuses connections to minimize overhead
4. **Background Processing**: Sync and consistency checks run in background
5. **Caching**: Version information is cached in memory

## Error Handling

1. **Automatic Retries**: Failed syncs are retried with exponential backoff
2. **Rollback Support**: Failed transactions are automatically rolled back
3. **Health Monitoring**: Unhealthy connections are detected and reconnected
4. **Graceful Degradation**: System continues with available stores

## Monitoring and Metrics

### Available Metrics
- Sync success/failure rates
- Average sync time
- Connection pool utilization
- Health check success rates
- Conflict resolution frequency

### Integration with Prometheus
```python
# Metrics are exposed via service registry
metrics = {
    "sync_total": sync_counter,
    "sync_duration_seconds": sync_histogram,
    "consistency_errors": error_counter,
    "connection_pool_size": pool_gauge
}
```

## Testing

Comprehensive test suite available in `tests/unit/test_memory_synchronizer.py`:
- Unit tests for all synchronization operations
- Mock implementations for all backends
- Concurrent operation testing
- Failure and rollback scenarios
- Performance benchmarks

## Future Enhancements

1. **Multi-Region Support**: Sync across geographic regions
2. **Compression**: Compress data for network efficiency
3. **Encryption**: End-to-end encryption for sensitive memories
4. **Sharding**: Distribute memories across multiple instances
5. **Real-time Sync**: WebSocket-based instant synchronization