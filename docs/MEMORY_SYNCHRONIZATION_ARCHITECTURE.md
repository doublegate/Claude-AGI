# Memory System Synchronization Architecture

Detailed architecture for synchronizing the three-tier memory system (Redis, PostgreSQL, FAISS) to ensure data consistency and prevent corruption.

## Current Architecture Issues

### Problem Statement
The Claude-AGI memory system uses three different storage backends:
- **Redis**: Fast working memory (volatile)
- **PostgreSQL**: Persistent episodic memory
- **FAISS**: Vector similarity search

Currently, these systems can become inconsistent due to:
- No transaction coordination across stores
- Race conditions during concurrent updates
- FAISS index not persisting between restarts
- No automatic reconciliation mechanism

## Proposed Synchronization Architecture

### Three-Tier Coordination Protocol

```
┌─────────────────────────────────────────────────────────┐
│                   Memory Coordinator                      │
│                  (Transaction Manager)                    │
├─────────────────┬────────────────┬─────────────────────┤
│   Redis Store   │ PostgreSQL Store│    FAISS Index      │
│ (Working Memory)│(Episodic Memory)│ (Semantic Search)   │
└─────────────────┴────────────────┴─────────────────────┘
```

### Implementation Design

#### 1. Transaction Coordinator
```python
from contextlib import asynccontextmanager
from typing import Optional
import asyncio
import uuid

class MemoryTransaction:
    """Distributed transaction across memory stores"""
    
    def __init__(self, transaction_id: str):
        self.id = transaction_id
        self.redis_commands = []
        self.postgres_queries = []
        self.faiss_operations = []
        self.rollback_actions = []
        
    async def commit(self):
        """Two-phase commit protocol"""
        # Phase 1: Prepare
        if not await self._prepare_all():
            await self.rollback()
            raise TransactionError("Prepare phase failed")
            
        # Phase 2: Commit
        try:
            await self._commit_all()
        except Exception as e:
            await self.rollback()
            raise TransactionError(f"Commit failed: {e}")
    
    async def rollback(self):
        """Execute rollback actions in reverse order"""
        for action in reversed(self.rollback_actions):
            try:
                await action()
            except Exception as e:
                logger.error(f"Rollback failed: {e}")

class MemoryCoordinator:
    """Coordinates transactions across all memory stores"""
    
    def __init__(self, redis: Redis, postgres: PostgreSQL, faiss: FAISSIndex):
        self.redis = redis
        self.postgres = postgres
        self.faiss = faiss
        self.lock = asyncio.Lock()
        
    @asynccontextmanager
    async def transaction(self):
        """Create a new distributed transaction"""
        transaction_id = str(uuid.uuid4())
        transaction = MemoryTransaction(transaction_id)
        
        try:
            yield transaction
            await transaction.commit()
        except Exception:
            await transaction.rollback()
            raise
```

#### 2. Consistency Mechanisms

##### Write-Through Cache Pattern
```python
class ConsistentMemoryManager:
    """Ensures consistency across all stores"""
    
    async def store_memory(self, memory: Memory) -> None:
        """Store memory with consistency guarantees"""
        async with self.coordinator.transaction() as txn:
            # 1. Generate embedding
            embedding = await self.generate_embedding(memory.content)
            
            # 2. Prepare all operations
            txn.postgres_queries.append(
                ("INSERT INTO memories VALUES ($1, $2, $3)", 
                 memory.id, memory.content, memory.metadata)
            )
            
            txn.redis_commands.append(
                ("SETEX", f"memory:{memory.id}", 3600, memory.to_json())
            )
            
            txn.faiss_operations.append(
                ("add", memory.id, embedding)
            )
            
            # 3. Add rollback actions
            txn.rollback_actions.extend([
                lambda: self.postgres.execute(
                    "DELETE FROM memories WHERE id = $1", memory.id
                ),
                lambda: self.redis.delete(f"memory:{memory.id}"),
                lambda: self.faiss.remove_ids([memory.id])
            ])
```

##### Read Consistency
```python
async def retrieve_memory(self, memory_id: str) -> Optional[Memory]:
    """Retrieve with consistency check"""
    # Try Redis first (fastest)
    cached = await self.redis.get(f"memory:{memory_id}")
    if cached:
        memory = Memory.from_json(cached)
        # Verify consistency
        if await self._verify_consistency(memory):
            return memory
    
    # Fall back to PostgreSQL (source of truth)
    row = await self.postgres.fetchone(
        "SELECT * FROM memories WHERE id = $1", memory_id
    )
    if row:
        memory = Memory.from_row(row)
        # Update cache
        await self.redis.setex(
            f"memory:{memory_id}", 3600, memory.to_json()
        )
        return memory
    
    return None

async def _verify_consistency(self, memory: Memory) -> bool:
    """Verify memory exists in all stores"""
    # Check PostgreSQL
    exists_pg = await self.postgres.fetchval(
        "SELECT EXISTS(SELECT 1 FROM memories WHERE id = $1)", 
        memory.id
    )
    
    # Check FAISS
    exists_faiss = memory.id in self.faiss.get_ids()
    
    return exists_pg and exists_faiss
```

#### 3. FAISS Index Persistence

```python
class PersistentFAISSIndex:
    """FAISS index with automatic persistence"""
    
    def __init__(self, index_path: str, embedding_dim: int):
        self.index_path = index_path
        self.embedding_dim = embedding_dim
        self.index = None
        self.id_map = {}  # Map internal FAISS ids to memory ids
        self._load_or_create()
        
    def _load_or_create(self):
        """Load existing index or create new one"""
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            # Load ID mapping
            with open(f"{self.index_path}.ids", "rb") as f:
                self.id_map = pickle.load(f)
        else:
            # Create new IVF index for scalability
            quantizer = faiss.IndexFlatL2(self.embedding_dim)
            self.index = faiss.IndexIVFFlat(
                quantizer, self.embedding_dim, 100
            )
            
    async def add(self, memory_id: str, embedding: np.ndarray):
        """Add embedding with automatic persistence"""
        faiss_id = self.index.ntotal
        self.index.add(np.array([embedding]))
        self.id_map[faiss_id] = memory_id
        
        # Persist immediately (can be optimized with batching)
        await self._persist()
        
    async def _persist(self):
        """Save index and mappings to disk"""
        faiss.write_index(self.index, self.index_path)
        with open(f"{self.index_path}.ids", "wb") as f:
            pickle.dump(self.id_map, f)
```

#### 4. Reconciliation Service

```python
class MemoryReconciliationService:
    """Periodic reconciliation to fix inconsistencies"""
    
    def __init__(self, coordinator: MemoryCoordinator):
        self.coordinator = coordinator
        self.running = False
        
    async def start(self):
        """Start periodic reconciliation"""
        self.running = True
        while self.running:
            try:
                await self.reconcile()
                await asyncio.sleep(300)  # Every 5 minutes
            except Exception as e:
                logger.error(f"Reconciliation error: {e}")
                
    async def reconcile(self):
        """Detect and fix inconsistencies"""
        # 1. Find orphaned Redis entries
        redis_keys = await self.coordinator.redis.keys("memory:*")
        for key in redis_keys:
            memory_id = key.split(":")[-1]
            if not await self._exists_in_postgres(memory_id):
                logger.warning(f"Orphaned Redis entry: {memory_id}")
                await self.coordinator.redis.delete(key)
                
        # 2. Rebuild FAISS index if needed
        pg_count = await self.coordinator.postgres.fetchval(
            "SELECT COUNT(*) FROM memories"
        )
        faiss_count = self.coordinator.faiss.index.ntotal
        
        if abs(pg_count - faiss_count) > 10:  # Threshold
            logger.warning("FAISS index out of sync, rebuilding...")
            await self._rebuild_faiss_index()
            
    async def _rebuild_faiss_index(self):
        """Rebuild FAISS index from PostgreSQL"""
        # Stream memories from PostgreSQL
        async for memory in self._stream_memories():
            embedding = await self.generate_embedding(memory.content)
            await self.coordinator.faiss.add(memory.id, embedding)
```

## Connection Management

### Connection Pooling
```python
class ConnectionManager:
    """Manages connection pools for all stores"""
    
    def __init__(self, config: dict):
        self.config = config
        self.redis_pool = None
        self.postgres_pool = None
        
    async def initialize(self):
        # Redis connection pool
        self.redis_pool = await aioredis.create_redis_pool(
            self.config['redis_url'],
            minsize=5,
            maxsize=20
        )
        
        # PostgreSQL connection pool
        self.postgres_pool = await asyncpg.create_pool(
            self.config['postgres_url'],
            min_size=10,
            max_size=30,
            max_queries=50000,
            max_inactive_connection_lifetime=300
        )
        
    async def get_redis(self) -> Redis:
        return Redis(self.redis_pool)
        
    async def get_postgres(self) -> PostgreSQL:
        async with self.postgres_pool.acquire() as conn:
            return PostgreSQLConnection(conn)
```

### Automatic Reconnection
```python
class ResilientConnection:
    """Connection with automatic retry and reconnection"""
    
    def __init__(self, connection_factory, max_retries=3):
        self.connection_factory = connection_factory
        self.max_retries = max_retries
        self.connection = None
        
    async def execute(self, operation, *args, **kwargs):
        """Execute operation with automatic retry"""
        for attempt in range(self.max_retries):
            try:
                if not self.connection:
                    self.connection = await self.connection_factory()
                    
                return await operation(self.connection, *args, **kwargs)
                
            except (ConnectionError, TimeoutError) as e:
                logger.warning(f"Connection error (attempt {attempt + 1}): {e}")
                self.connection = None
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Monitoring and Alerting

### Consistency Metrics
```python
# Prometheus metrics
memory_consistency_errors = Counter(
    'memory_consistency_errors_total',
    'Number of consistency errors detected',
    ['error_type']
)

memory_sync_latency = Histogram(
    'memory_sync_latency_seconds',
    'Time to sync memory across stores'
)

faiss_index_size = Gauge(
    'faiss_index_size',
    'Number of vectors in FAISS index'
)
```

### Health Checks
```python
async def health_check() -> dict:
    """Comprehensive health check for memory system"""
    health = {
        'status': 'healthy',
        'checks': {}
    }
    
    # Check Redis
    try:
        await redis.ping()
        health['checks']['redis'] = 'ok'
    except Exception as e:
        health['status'] = 'unhealthy'
        health['checks']['redis'] = str(e)
    
    # Check PostgreSQL
    try:
        await postgres.fetchval("SELECT 1")
        health['checks']['postgres'] = 'ok'
    except Exception as e:
        health['status'] = 'unhealthy'
        health['checks']['postgres'] = str(e)
    
    # Check FAISS
    try:
        count = faiss_index.ntotal
        health['checks']['faiss'] = f"ok ({count} vectors)"
    except Exception as e:
        health['status'] = 'unhealthy'
        health['checks']['faiss'] = str(e)
    
    # Check consistency
    consistency = await check_consistency()
    health['checks']['consistency'] = consistency
    
    return health
```

## Migration Plan

### Phase 1: Current State → Basic Synchronization
1. Implement transaction coordinator
2. Add consistency checks to read operations
3. Set up reconciliation service
4. Add monitoring metrics

### Phase 2: Advanced Features
1. Implement distributed locking
2. Add event sourcing for audit trail
3. Implement conflict resolution strategies
4. Add real-time synchronization

### Phase 3: Scale Optimization
1. Implement sharding for PostgreSQL
2. Use Redis Cluster for distribution
3. Distribute FAISS index across nodes
4. Add caching layers

## Success Criteria

- Zero data loss during normal operations
- <1% inconsistency rate during reconciliation
- <10ms overhead for consistency checks
- 99.9% uptime for all memory operations
- Automatic recovery from single-store failures