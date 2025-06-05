"""
Episodic Memory Store

Handles long-term episodic memory storage with PostgreSQL backend.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
import uuid

from ...core.service_registry import ServiceRegistry
from ..connection_pool import ConnectionPoolManager
from ...database.models import MemoryType, EmotionalState


class EpisodicMemoryStore:
    """
    Manages episodic (long-term) memory storage.
    
    Features:
    - Persistent storage in PostgreSQL
    - Importance-based retention
    - Emotional tagging
    - Association tracking
    - Time-based decay
    """
    
    def __init__(
        self,
        connection_pool: Optional[ConnectionPoolManager] = None,
        service_registry: Optional[ServiceRegistry] = None,
        importance_threshold: float = 0.7,
        decay_rate: float = 0.01
    ):
        self.connection_pool = connection_pool
        self.service_registry = service_registry
        self.importance_threshold = importance_threshold
        self.decay_rate = decay_rate
        
        self.logger = logging.getLogger(__name__)
        
        # In-memory fallback storage
        self._memories: Dict[str, Dict[str, Any]] = {}
        self._associations: Dict[str, List[str]] = {}
        
        # Metrics
        self._store_count = 0
        self._retrieve_count = 0
        self._association_count = 0
        
    async def initialize(self):
        """Initialize the episodic memory store"""
        self.logger.info("Initializing Episodic Memory Store")
        
        # Verify database connection if available
        if self.connection_pool:
            try:
                async with self.connection_pool.get_postgres_connection() as conn:
                    # Verify table exists
                    exists = await conn.fetchval("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'episodic_memory'
                        )
                    """)
                    
                    if not exists:
                        self.logger.warning("Episodic memory table does not exist")
                        self.connection_pool = None
                        
            except Exception as e:
                self.logger.error(f"Failed to verify database: {e}")
                self.connection_pool = None
        
        # Register with service registry
        if self.service_registry:
            await self.service_registry.register_service(
                "episodic_memory_store",
                self,
                {
                    "importance_threshold": self.importance_threshold,
                    "decay_rate": self.decay_rate,
                    "has_database": self.connection_pool is not None
                }
            )
    
    async def shutdown(self):
        """Shutdown the store gracefully"""
        self.logger.info("Shutting down Episodic Memory Store")
        
        # Unregister from service registry
        if self.service_registry:
            await self.service_registry.unregister_service("episodic_memory_store")
    
    async def store_memory(
        self,
        memory_id: str,
        content: str,
        memory_type: MemoryType = MemoryType.EPISODIC,
        importance: float = 0.5,
        emotional_valence: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> bool:
        """
        Store an episodic memory.
        
        Args:
            memory_id: Unique identifier for the memory
            content: Memory content
            memory_type: Type of memory
            importance: Importance score (0-1)
            emotional_valence: Emotional valence (-1 to 1)
            metadata: Additional metadata
            embedding: Vector embedding for the memory
            
        Returns:
            bool: Success status
        """
        self._store_count += 1
        
        # Check importance threshold
        if importance < self.importance_threshold:
            self.logger.debug(f"Memory {memory_id} below importance threshold")
            return False
        
        timestamp = datetime.now(timezone.utc)
        
        try:
            # Try PostgreSQL first
            if self.connection_pool:
                async with self.connection_pool.get_postgres_connection() as conn:
                    await conn.execute("""
                        INSERT INTO episodic_memory (
                            memory_id, content, memory_type, importance,
                            emotional_valence, metadata, embedding, created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (memory_id) DO UPDATE SET
                            content = EXCLUDED.content,
                            importance = EXCLUDED.importance,
                            emotional_valence = EXCLUDED.emotional_valence,
                            metadata = EXCLUDED.metadata,
                            embedding = EXCLUDED.embedding,
                            updated_at = EXCLUDED.updated_at,
                            access_count = episodic_memory.access_count + 1
                    """,
                        memory_id,
                        content,
                        memory_type.value,
                        importance,
                        emotional_valence,
                        json.dumps(metadata or {}),
                        embedding,
                        timestamp,
                        timestamp
                    )
                    
                    self.logger.debug(f"Stored episodic memory {memory_id}")
                    return True
                    
        except Exception as e:
            self.logger.error(f"Failed to store memory in PostgreSQL: {e}")
        
        # Fallback to in-memory storage
        self._memories[memory_id] = {
            "memory_id": memory_id,
            "content": content,
            "memory_type": memory_type.value,
            "importance": importance,
            "emotional_valence": emotional_valence,
            "metadata": metadata or {},
            "embedding": embedding,
            "created_at": timestamp.isoformat(),
            "updated_at": timestamp.isoformat(),
            "access_count": 0
        }
        
        return True
    
    async def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific memory by ID.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Memory data if found, None otherwise
        """
        self._retrieve_count += 1
        
        try:
            # Try PostgreSQL first
            if self.connection_pool:
                async with self.connection_pool.get_postgres_connection() as conn:
                    # Update access count and last accessed
                    row = await conn.fetchrow("""
                        UPDATE episodic_memory 
                        SET access_count = access_count + 1,
                            last_accessed = CURRENT_TIMESTAMP
                        WHERE memory_id = $1
                        RETURNING *
                    """, memory_id)
                    
                    if row:
                        return dict(row)
                        
        except Exception as e:
            self.logger.error(f"Failed to retrieve memory from PostgreSQL: {e}")
        
        # Fallback to in-memory storage
        memory = self._memories.get(memory_id)
        if memory:
            memory["access_count"] += 1
            memory["last_accessed"] = datetime.now(timezone.utc).isoformat()
            return memory
        
        return None
    
    async def get_recent_memories(
        self,
        limit: int = 10,
        memory_type: Optional[MemoryType] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent memories, optionally filtered by type.
        
        Args:
            limit: Maximum number of memories to return
            memory_type: Optional memory type filter
            
        Returns:
            List of recent memories
        """
        try:
            # Try PostgreSQL first
            if self.connection_pool:
                async with self.connection_pool.get_postgres_connection() as conn:
                    if memory_type:
                        rows = await conn.fetch("""
                            SELECT * FROM episodic_memory
                            WHERE memory_type = $1
                            ORDER BY created_at DESC
                            LIMIT $2
                        """, memory_type.value, limit)
                    else:
                        rows = await conn.fetch("""
                            SELECT * FROM episodic_memory
                            ORDER BY created_at DESC
                            LIMIT $1
                        """, limit)
                    
                    return [dict(row) for row in rows]
                    
        except Exception as e:
            self.logger.error(f"Failed to get recent memories from PostgreSQL: {e}")
        
        # Fallback to in-memory storage
        memories = list(self._memories.values())
        
        # Filter by type if specified
        if memory_type:
            memories = [m for m in memories if m["memory_type"] == memory_type.value]
        
        # Sort by created_at descending
        memories.sort(key=lambda x: x["created_at"], reverse=True)
        
        return memories[:limit]
    
    async def get_important_memories(
        self,
        min_importance: float = 0.8,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get memories above a certain importance threshold.
        
        Args:
            min_importance: Minimum importance score
            limit: Maximum number of memories to return
            
        Returns:
            List of important memories
        """
        try:
            # Try PostgreSQL first
            if self.connection_pool:
                async with self.connection_pool.get_postgres_connection() as conn:
                    rows = await conn.fetch("""
                        SELECT * FROM episodic_memory
                        WHERE importance >= $1
                        ORDER BY importance DESC, created_at DESC
                        LIMIT $2
                    """, min_importance, limit)
                    
                    return [dict(row) for row in rows]
                    
        except Exception as e:
            self.logger.error(f"Failed to get important memories from PostgreSQL: {e}")
        
        # Fallback to in-memory storage
        memories = [
            m for m in self._memories.values()
            if m["importance"] >= min_importance
        ]
        
        # Sort by importance descending, then by created_at
        memories.sort(
            key=lambda x: (x["importance"], x["created_at"]),
            reverse=True
        )
        
        return memories[:limit]
    
    async def get_emotional_memories(
        self,
        valence_range: Tuple[float, float] = (-1.0, 1.0),
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get memories within a certain emotional valence range.
        
        Args:
            valence_range: Tuple of (min_valence, max_valence)
            limit: Maximum number of memories to return
            
        Returns:
            List of memories within the valence range
        """
        min_valence, max_valence = valence_range
        
        try:
            # Try PostgreSQL first
            if self.connection_pool:
                async with self.connection_pool.get_postgres_connection() as conn:
                    rows = await conn.fetch("""
                        SELECT * FROM episodic_memory
                        WHERE emotional_valence BETWEEN $1 AND $2
                        ORDER BY ABS(emotional_valence) DESC
                        LIMIT $3
                    """, min_valence, max_valence, limit)
                    
                    return [dict(row) for row in rows]
                    
        except Exception as e:
            self.logger.error(f"Failed to get emotional memories from PostgreSQL: {e}")
        
        # Fallback to in-memory storage
        memories = [
            m for m in self._memories.values()
            if min_valence <= m["emotional_valence"] <= max_valence
        ]
        
        # Sort by absolute emotional valence
        memories.sort(
            key=lambda x: abs(x["emotional_valence"]),
            reverse=True
        )
        
        return memories[:limit]
    
    async def create_association(
        self,
        memory_id1: str,
        memory_id2: str,
        strength: float = 0.5
    ) -> bool:
        """
        Create an association between two memories.
        
        Args:
            memory_id1: First memory ID
            memory_id2: Second memory ID
            strength: Association strength (0-1)
            
        Returns:
            bool: Success status
        """
        self._association_count += 1
        
        try:
            # Try PostgreSQL first
            if self.connection_pool:
                async with self.connection_pool.get_postgres_connection() as conn:
                    # Insert association (bidirectional)
                    await conn.execute("""
                        INSERT INTO memory_associations (
                            memory_id_1, memory_id_2, strength, created_at
                        ) VALUES 
                            ($1, $2, $3, CURRENT_TIMESTAMP),
                            ($2, $1, $3, CURRENT_TIMESTAMP)
                        ON CONFLICT (memory_id_1, memory_id_2) DO UPDATE
                        SET strength = GREATEST(
                            memory_associations.strength,
                            EXCLUDED.strength
                        )
                    """, memory_id1, memory_id2, strength)
                    
                    return True
                    
        except Exception as e:
            self.logger.error(f"Failed to create association in PostgreSQL: {e}")
        
        # Fallback to in-memory storage
        if memory_id1 not in self._associations:
            self._associations[memory_id1] = []
        if memory_id2 not in self._associations:
            self._associations[memory_id2] = []
            
        if memory_id2 not in self._associations[memory_id1]:
            self._associations[memory_id1].append(memory_id2)
        if memory_id1 not in self._associations[memory_id2]:
            self._associations[memory_id2].append(memory_id1)
        
        return True
    
    async def get_associated_memories(
        self,
        memory_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get memories associated with a given memory.
        
        Args:
            memory_id: Memory ID to find associations for
            limit: Maximum number of associations to return
            
        Returns:
            List of associated memories
        """
        try:
            # Try PostgreSQL first
            if self.connection_pool:
                async with self.connection_pool.get_postgres_connection() as conn:
                    # Get associated memory IDs
                    rows = await conn.fetch("""
                        SELECT em.*, ma.strength
                        FROM episodic_memory em
                        JOIN memory_associations ma ON em.memory_id = ma.memory_id_2
                        WHERE ma.memory_id_1 = $1
                        ORDER BY ma.strength DESC, em.importance DESC
                        LIMIT $2
                    """, memory_id, limit)
                    
                    return [dict(row) for row in rows]
                    
        except Exception as e:
            self.logger.error(f"Failed to get associations from PostgreSQL: {e}")
        
        # Fallback to in-memory storage
        associated_ids = self._associations.get(memory_id, [])[:limit]
        memories = []
        
        for assoc_id in associated_ids:
            memory = self._memories.get(assoc_id)
            if memory:
                memories.append(memory)
        
        return memories
    
    async def apply_decay(self) -> int:
        """
        Apply time-based decay to memory importance.
        
        Returns:
            Number of memories affected
        """
        affected = 0
        
        try:
            # Try PostgreSQL first
            if self.connection_pool:
                async with self.connection_pool.get_postgres_connection() as conn:
                    # Apply decay based on time since last access
                    result = await conn.execute("""
                        UPDATE episodic_memory
                        SET importance = GREATEST(
                            0.1,  -- Minimum importance
                            importance - (
                                $1 * EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - last_accessed)) / 86400
                            )
                        )
                        WHERE last_accessed < CURRENT_TIMESTAMP - INTERVAL '1 day'
                    """, self.decay_rate)
                    
                    affected = int(result.split()[-1])
                    return affected
                    
        except Exception as e:
            self.logger.error(f"Failed to apply decay in PostgreSQL: {e}")
        
        # Fallback to in-memory storage
        current_time = datetime.now(timezone.utc)
        
        for memory in self._memories.values():
            last_accessed = datetime.fromisoformat(
                memory.get("last_accessed", memory["created_at"])
            )
            
            # Calculate days since last access
            days_inactive = (current_time - last_accessed).days
            
            if days_inactive > 0:
                # Apply decay
                old_importance = memory["importance"]
                memory["importance"] = max(
                    0.1,  # Minimum importance
                    old_importance - (self.decay_rate * days_inactive)
                )
                
                if memory["importance"] < old_importance:
                    affected += 1
        
        return affected
    
    async def prune_memories(
        self,
        max_memories: int = 10000,
        min_importance: float = 0.1
    ) -> int:
        """
        Prune low-importance memories to maintain size limits.
        
        Args:
            max_memories: Maximum number of memories to keep
            min_importance: Minimum importance to retain
            
        Returns:
            Number of memories pruned
        """
        pruned = 0
        
        try:
            # Try PostgreSQL first
            if self.connection_pool:
                async with self.connection_pool.get_postgres_connection() as conn:
                    # First, delete memories below minimum importance
                    result = await conn.execute("""
                        DELETE FROM episodic_memory
                        WHERE importance < $1
                    """, min_importance)
                    
                    pruned = int(result.split()[-1])
                    
                    # Then check if we still have too many
                    count = await conn.fetchval(
                        "SELECT COUNT(*) FROM episodic_memory"
                    )
                    
                    if count > max_memories:
                        # Delete oldest, least important memories
                        result = await conn.execute("""
                            DELETE FROM episodic_memory
                            WHERE memory_id IN (
                                SELECT memory_id FROM episodic_memory
                                ORDER BY importance ASC, last_accessed ASC
                                LIMIT $1
                            )
                        """, count - max_memories)
                        
                        pruned += int(result.split()[-1])
                    
                    return pruned
                    
        except Exception as e:
            self.logger.error(f"Failed to prune memories in PostgreSQL: {e}")
        
        # Fallback to in-memory storage
        # Remove memories below minimum importance
        to_remove = [
            memory_id for memory_id, memory in self._memories.items()
            if memory["importance"] < min_importance
        ]
        
        for memory_id in to_remove:
            del self._memories[memory_id]
            pruned += 1
        
        # Check if still too many
        if len(self._memories) > max_memories:
            # Sort by importance and last accessed
            sorted_memories = sorted(
                self._memories.items(),
                key=lambda x: (x[1]["importance"], x[1].get("last_accessed", x[1]["created_at"]))
            )
            
            # Remove excess memories
            excess = len(self._memories) - max_memories
            for memory_id, _ in sorted_memories[:excess]:
                del self._memories[memory_id]
                pruned += 1
        
        return pruned
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get episodic memory statistics.
        
        Returns:
            Dict of statistics
        """
        total_memories = len(self._memories)
        total_associations = sum(len(assocs) for assocs in self._associations.values()) // 2
        
        avg_importance = 0.0
        avg_valence = 0.0
        
        if total_memories > 0:
            avg_importance = sum(m["importance"] for m in self._memories.values()) / total_memories
            avg_valence = sum(m["emotional_valence"] for m in self._memories.values()) / total_memories
        
        return {
            "store_count": self._store_count,
            "retrieve_count": self._retrieve_count,
            "association_count": self._association_count,
            "total_memories": total_memories,
            "total_associations": total_associations,
            "avg_importance": round(avg_importance, 2),
            "avg_emotional_valence": round(avg_valence, 2),
            "importance_threshold": self.importance_threshold,
            "decay_rate": self.decay_rate
        }