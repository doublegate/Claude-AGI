"""
Memory System Synchronization

This module provides synchronization between Redis (working memory),
PostgreSQL (episodic memory), and FAISS (semantic index) to ensure
data consistency across all memory stores.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import asyncpg
import redis.asyncio as redis
import numpy as np
from pydantic import BaseModel, Field

from ..core.service_registry import ServiceRegistry
from ..core.event_bus import EventBus


class SyncStatus(Enum):
    """Synchronization status states"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"


class MemoryVersion(BaseModel):
    """Version information for a memory entry"""
    memory_id: str
    version: int = 1
    checksum: str
    last_modified: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    store_versions: Dict[str, int] = Field(default_factory=dict)


class SyncTransaction(BaseModel):
    """Represents a synchronization transaction"""
    transaction_id: str
    memories: List[str] = Field(default_factory=list)
    status: SyncStatus = SyncStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    rollback_data: Dict[str, Any] = Field(default_factory=dict)


class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    LATEST_WINS = "latest_wins"
    MERGE = "merge"
    MANUAL = "manual"
    VERSION_VECTOR = "version_vector"


class MemorySynchronizer:
    """
    Handles synchronization between different memory stores.
    
    Ensures consistency between:
    - Redis (working memory) - fast access
    - PostgreSQL (episodic memory) - persistent storage
    - FAISS (semantic index) - similarity search
    """
    
    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        postgres_pool: Optional[asyncpg.Pool] = None,
        faiss_index: Optional[Any] = None,
        service_registry: Optional[ServiceRegistry] = None,
        event_bus: Optional[EventBus] = None
    ):
        self.redis_client = redis_client
        self.postgres_pool = postgres_pool
        self.faiss_index = faiss_index
        self.service_registry = service_registry
        self.event_bus = event_bus
        
        self.logger = logging.getLogger(__name__)
        self._versions: Dict[str, MemoryVersion] = {}
        self._active_transactions: Dict[str, SyncTransaction] = {}
        self._lock_manager = asyncio.Lock()
        self._conflict_resolution = ConflictResolution.LATEST_WINS
        
        # Sync configuration
        self.batch_size = 100
        self.sync_interval = 5.0  # seconds
        self.max_retries = 3
        self.consistency_check_interval = 60.0  # seconds
        
        # Background tasks
        self._sync_task: Optional[asyncio.Task] = None
        self._consistency_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Initialize the synchronizer and start background tasks"""
        self.logger.info("Initializing Memory Synchronizer")
        
        # Initialize version tracking
        await self._load_versions()
        
        # Start background tasks
        self._sync_task = asyncio.create_task(self._sync_loop())
        self._consistency_task = asyncio.create_task(self._consistency_check_loop())
        
        # Register with service registry if available
        if self.service_registry:
            await self.service_registry.register_service(
                "memory_synchronizer",
                self,
                {"sync_interval": self.sync_interval}
            )
    
    async def shutdown(self):
        """Shutdown the synchronizer gracefully"""
        self.logger.info("Shutting down Memory Synchronizer")
        
        # Cancel background tasks
        if self._sync_task:
            self._sync_task.cancel()
        if self._consistency_task:
            self._consistency_task.cancel()
        
        # Wait for active transactions to complete
        await self._wait_for_transactions()
        
        # Unregister from service registry
        if self.service_registry:
            await self.service_registry.unregister_service("memory_synchronizer")
    
    async def sync_memory(self, memory_id: str, memory_data: Dict[str, Any]) -> bool:
        """
        Synchronize a single memory across all stores.
        
        Args:
            memory_id: The memory identifier
            memory_data: The memory data to synchronize
            
        Returns:
            bool: True if synchronization successful
        """
        transaction_id = f"sync_{memory_id}_{datetime.now().timestamp()}"
        transaction = SyncTransaction(
            transaction_id=transaction_id,
            memories=[memory_id]
        )
        
        try:
            async with self._lock_manager:
                self._active_transactions[transaction_id] = transaction
                transaction.status = SyncStatus.IN_PROGRESS
                transaction.started_at = datetime.now(timezone.utc)
            
            # Calculate checksum
            checksum = self._calculate_checksum(memory_data)
            
            # Get or create version info
            version = self._versions.get(memory_id, MemoryVersion(
                memory_id=memory_id,
                checksum=checksum
            ))
            
            # Check for conflicts
            conflicts = await self._check_conflicts(memory_id, checksum)
            if conflicts:
                transaction.status = SyncStatus.CONFLICT
                resolved_data = await self._resolve_conflicts(
                    memory_id,
                    memory_data,
                    conflicts
                )
                if resolved_data:
                    memory_data = resolved_data
                else:
                    raise Exception("Conflict resolution failed")
            
            # Store rollback data
            transaction.rollback_data = await self._prepare_rollback(memory_id)
            
            # Sync to each store
            success = True
            
            # Update Redis
            if self.redis_client:
                success &= await self._sync_to_redis(memory_id, memory_data)
                version.store_versions["redis"] = version.version
            
            # Update PostgreSQL
            if self.postgres_pool:
                success &= await self._sync_to_postgres(memory_id, memory_data)
                version.store_versions["postgres"] = version.version
            
            # Update FAISS
            if self.faiss_index and "embedding" in memory_data:
                success &= await self._sync_to_faiss(memory_id, memory_data)
                version.store_versions["faiss"] = version.version
            
            if success:
                # Update version info
                version.version += 1
                version.checksum = checksum
                version.last_modified = datetime.now(timezone.utc)
                self._versions[memory_id] = version
                
                transaction.status = SyncStatus.COMPLETED
                transaction.completed_at = datetime.now(timezone.utc)
                
                # Publish sync event
                if self.event_bus:
                    await self.event_bus.publish(
                        "memory.synchronized",
                        {
                            "memory_id": memory_id,
                            "version": version.version,
                            "stores": list(version.store_versions.keys())
                        }
                    )
            else:
                raise Exception("Synchronization failed")
                
        except Exception as e:
            self.logger.error(f"Sync failed for memory {memory_id}: {e}")
            transaction.status = SyncStatus.FAILED
            transaction.error = str(e)
            
            # Attempt rollback
            await self._rollback_transaction(transaction)
            return False
            
        finally:
            async with self._lock_manager:
                self._active_transactions.pop(transaction_id, None)
        
        return True
    
    async def sync_batch(self, memories: List[Dict[str, Any]]) -> Dict[str, bool]:
        """
        Synchronize a batch of memories.
        
        Args:
            memories: List of memory data dictionaries
            
        Returns:
            Dict mapping memory_id to success status
        """
        results = {}
        
        # Process in batches
        for i in range(0, len(memories), self.batch_size):
            batch = memories[i:i + self.batch_size]
            
            # Sync each memory in the batch concurrently
            tasks = []
            for memory_data in batch:
                memory_id = memory_data.get("memory_id", "")
                if memory_id:
                    tasks.append(self.sync_memory(memory_id, memory_data))
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            for j, result in enumerate(batch_results):
                memory_id = batch[j].get("memory_id", "")
                results[memory_id] = result is True
        
        return results
    
    async def check_consistency(self) -> Dict[str, List[str]]:
        """
        Check consistency across all memory stores.
        
        Returns:
            Dict mapping memory_id to list of inconsistent stores
        """
        inconsistencies = {}
        
        # Get all memory IDs from each store
        redis_ids = await self._get_redis_memory_ids() if self.redis_client else set()
        postgres_ids = await self._get_postgres_memory_ids() if self.postgres_pool else set()
        faiss_ids = await self._get_faiss_memory_ids() if self.faiss_index else set()
        
        all_ids = redis_ids | postgres_ids | faiss_ids
        
        for memory_id in all_ids:
            inconsistent_stores = []
            
            # Check which stores have this memory
            stores_with_memory = []
            if memory_id in redis_ids:
                stores_with_memory.append("redis")
            if memory_id in postgres_ids:
                stores_with_memory.append("postgres")
            if memory_id in faiss_ids:
                stores_with_memory.append("faiss")
            
            # If not in all stores, it's inconsistent
            if len(stores_with_memory) != 3:
                missing_stores = []
                if memory_id not in redis_ids and self.redis_client:
                    missing_stores.append("redis")
                if memory_id not in postgres_ids and self.postgres_pool:
                    missing_stores.append("postgres")
                if memory_id not in faiss_ids and self.faiss_index:
                    missing_stores.append("faiss")
                
                if missing_stores:
                    inconsistencies[memory_id] = missing_stores
            else:
                # Check version consistency
                version = self._versions.get(memory_id)
                if version:
                    for store, store_version in version.store_versions.items():
                        if store_version != version.version:
                            inconsistent_stores.append(store)
                
                if inconsistent_stores:
                    inconsistencies[memory_id] = inconsistent_stores
        
        return inconsistencies
    
    async def repair_inconsistencies(
        self,
        inconsistencies: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, bool]:
        """
        Repair detected inconsistencies.
        
        Args:
            inconsistencies: Dict of memory_id to inconsistent stores,
                           or None to detect automatically
            
        Returns:
            Dict mapping memory_id to repair success status
        """
        if inconsistencies is None:
            inconsistencies = await self.check_consistency()
        
        repair_results = {}
        
        for memory_id, inconsistent_stores in inconsistencies.items():
            try:
                # Get the most recent version from available stores
                memory_data = await self._get_latest_memory_version(memory_id)
                
                if memory_data:
                    # Sync to inconsistent stores
                    success = await self.sync_memory(memory_id, memory_data)
                    repair_results[memory_id] = success
                else:
                    self.logger.warning(f"Could not find memory {memory_id} in any store")
                    repair_results[memory_id] = False
                    
            except Exception as e:
                self.logger.error(f"Failed to repair memory {memory_id}: {e}")
                repair_results[memory_id] = False
        
        return repair_results
    
    # Private helper methods
    
    async def _sync_loop(self):
        """Background task for periodic synchronization"""
        while True:
            try:
                await asyncio.sleep(self.sync_interval)
                
                # Get pending sync operations
                pending_memories = await self._get_pending_syncs()
                
                if pending_memories:
                    await self.sync_batch(pending_memories)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Sync loop error: {e}")
    
    async def _consistency_check_loop(self):
        """Background task for periodic consistency checks"""
        while True:
            try:
                await asyncio.sleep(self.consistency_check_interval)
                
                inconsistencies = await self.check_consistency()
                
                if inconsistencies:
                    self.logger.warning(
                        f"Found {len(inconsistencies)} inconsistent memories"
                    )
                    
                    # Auto-repair if enabled
                    await self.repair_inconsistencies(inconsistencies)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Consistency check error: {e}")
    
    async def _sync_to_redis(self, memory_id: str, memory_data: Dict[str, Any]) -> bool:
        """Sync memory to Redis"""
        try:
            # Store in working memory hash
            await self.redis_client.hset(
                "working_memory",
                memory_id,
                json.dumps(memory_data)
            )
            
            # Update index sets
            memory_type = memory_data.get("memory_type", "general")
            await self.redis_client.sadd(f"memory_type:{memory_type}", memory_id)
            
            # Set TTL if specified
            ttl = memory_data.get("ttl")
            if ttl:
                await self.redis_client.expire(f"memory:{memory_id}", ttl)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Redis sync failed: {e}")
            return False
    
    async def _sync_to_postgres(self, memory_id: str, memory_data: Dict[str, Any]) -> bool:
        """Sync memory to PostgreSQL"""
        try:
            async with self.postgres_pool.acquire() as conn:
                # Upsert memory
                await conn.execute("""
                    INSERT INTO episodic_memory (
                        memory_id, content, memory_type, importance,
                        emotional_valence, metadata, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (memory_id) DO UPDATE SET
                        content = EXCLUDED.content,
                        memory_type = EXCLUDED.memory_type,
                        importance = EXCLUDED.importance,
                        emotional_valence = EXCLUDED.emotional_valence,
                        metadata = EXCLUDED.metadata,
                        updated_at = EXCLUDED.updated_at
                """,
                    memory_id,
                    memory_data.get("content", ""),
                    memory_data.get("memory_type", "general"),
                    memory_data.get("importance", 0.5),
                    memory_data.get("emotional_valence", 0.0),
                    json.dumps(memory_data.get("metadata", {})),
                    memory_data.get("timestamp", datetime.now(timezone.utc)),
                    datetime.now(timezone.utc)
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"PostgreSQL sync failed: {e}")
            return False
    
    async def _sync_to_faiss(self, memory_id: str, memory_data: Dict[str, Any]) -> bool:
        """Sync memory to FAISS index"""
        try:
            embedding = memory_data.get("embedding")
            if not embedding:
                return True  # Skip if no embedding
            
            # Convert to numpy array
            embedding_array = np.array(embedding, dtype=np.float32)
            
            # Add to index
            # Note: This is simplified - real implementation would handle
            # index management more carefully
            self.faiss_index.add(embedding_array.reshape(1, -1))
            
            return True
            
        except Exception as e:
            self.logger.error(f"FAISS sync failed: {e}")
            return False
    
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate checksum for memory data"""
        # Sort keys for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True)
        return hashlib.sha256(sorted_data.encode()).hexdigest()
    
    async def _check_conflicts(self, memory_id: str, checksum: str) -> List[str]:
        """Check for conflicts across stores"""
        conflicts = []
        
        # Check each store's checksum
        if self.redis_client:
            redis_data = await self.redis_client.hget("working_memory", memory_id)
            if redis_data:
                redis_checksum = self._calculate_checksum(json.loads(redis_data))
                if redis_checksum != checksum:
                    conflicts.append("redis")
        
        # Similar checks for PostgreSQL and FAISS
        
        return conflicts
    
    async def _resolve_conflicts(
        self,
        memory_id: str,
        memory_data: Dict[str, Any],
        conflicts: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Resolve conflicts based on configured strategy"""
        if self._conflict_resolution == ConflictResolution.LATEST_WINS:
            # Use the provided memory_data as the latest version
            return memory_data
            
        elif self._conflict_resolution == ConflictResolution.MERGE:
            # Merge data from all stores
            merged_data = memory_data.copy()
            
            # Get data from each conflicting store and merge
            # Implementation depends on merge strategy
            
            return merged_data
            
        else:
            # Manual or other strategies
            return None
    
    async def _prepare_rollback(self, memory_id: str) -> Dict[str, Any]:
        """Prepare rollback data for a memory"""
        rollback_data = {}
        
        # Save current state from each store
        if self.redis_client:
            redis_data = await self.redis_client.hget("working_memory", memory_id)
            if redis_data:
                rollback_data["redis"] = json.loads(redis_data)
        
        # Similar for other stores
        
        return rollback_data
    
    async def _rollback_transaction(self, transaction: SyncTransaction):
        """Rollback a failed transaction"""
        for memory_id in transaction.memories:
            rollback_data = transaction.rollback_data.get(memory_id, {})
            
            # Restore each store
            if "redis" in rollback_data and self.redis_client:
                await self.redis_client.hset(
                    "working_memory",
                    memory_id,
                    json.dumps(rollback_data["redis"])
                )
    
    async def _wait_for_transactions(self):
        """Wait for all active transactions to complete"""
        max_wait = 30  # seconds
        start_time = datetime.now()
        
        while self._active_transactions:
            if (datetime.now() - start_time).total_seconds() > max_wait:
                self.logger.warning("Timeout waiting for transactions to complete")
                break
            
            await asyncio.sleep(0.1)
    
    async def _load_versions(self):
        """Load version information from persistent storage"""
        # Load from PostgreSQL if available
        if self.postgres_pool:
            async with self.postgres_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT memory_id, version, checksum, last_modified
                    FROM memory_versions
                """)
                
                for row in rows:
                    self._versions[row["memory_id"]] = MemoryVersion(
                        memory_id=row["memory_id"],
                        version=row["version"],
                        checksum=row["checksum"],
                        last_modified=row["last_modified"]
                    )
    
    async def _get_redis_memory_ids(self) -> Set[str]:
        """Get all memory IDs from Redis"""
        keys = await self.redis_client.hkeys("working_memory")
        return set(keys)
    
    async def _get_postgres_memory_ids(self) -> Set[str]:
        """Get all memory IDs from PostgreSQL"""
        async with self.postgres_pool.acquire() as conn:
            rows = await conn.fetch("SELECT memory_id FROM episodic_memory")
            return {row["memory_id"] for row in rows}
    
    async def _get_faiss_memory_ids(self) -> Set[str]:
        """Get all memory IDs from FAISS"""
        # This would require maintaining a separate mapping
        # of FAISS indices to memory IDs
        return set()
    
    async def _get_latest_memory_version(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest version of a memory from any store"""
        # Try each store in order of preference
        
        # Try PostgreSQL first (most reliable)
        if self.postgres_pool:
            async with self.postgres_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM episodic_memory WHERE memory_id = $1",
                    memory_id
                )
                if row:
                    return dict(row)
        
        # Try Redis
        if self.redis_client:
            redis_data = await self.redis_client.hget("working_memory", memory_id)
            if redis_data:
                return json.loads(redis_data)
        
        return None
    
    async def _get_pending_syncs(self) -> List[Dict[str, Any]]:
        """Get memories that need synchronization"""
        pending = []
        
        # Check for memories marked for sync in Redis
        if self.redis_client:
            pending_ids = await self.redis_client.smembers("pending_sync")
            
            for memory_id in pending_ids:
                memory_data = await self.redis_client.hget("working_memory", memory_id)
                if memory_data:
                    data = json.loads(memory_data)
                    data["memory_id"] = memory_id
                    pending.append(data)
        
        return pending