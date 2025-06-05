"""
Working Memory Store

Handles short-term, rapidly accessible memory storage.
Typically backed by Redis for fast access.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import deque

from ...core.service_registry import ServiceRegistry
from ..connection_pool import ConnectionPoolManager


class WorkingMemoryStore:
    """
    Manages working memory (short-term storage) for recent thoughts and active context.
    
    Features:
    - Fast access to recent thoughts
    - Active context management
    - TTL-based expiration
    - Circular buffer for memory limits
    """
    
    def __init__(
        self,
        connection_pool: Optional[ConnectionPoolManager] = None,
        service_registry: Optional[ServiceRegistry] = None,
        max_thoughts: int = 1000,
        default_ttl: int = 86400  # 24 hours
    ):
        self.connection_pool = connection_pool
        self.service_registry = service_registry
        self.max_thoughts = max_thoughts
        self.default_ttl = default_ttl
        
        self.logger = logging.getLogger(__name__)
        
        # In-memory fallback storage
        self._recent_thoughts = deque(maxlen=max_thoughts)
        self._short_term_cache: Dict[str, Dict[str, Any]] = {}
        self._active_context: Dict[str, Any] = {}
        
        # Metrics
        self._store_count = 0
        self._retrieve_count = 0
        self._hit_rate = 0.0
        
    async def initialize(self):
        """Initialize the working memory store"""
        self.logger.info("Initializing Working Memory Store")
        
        # Register with service registry
        if self.service_registry:
            await self.service_registry.register_service(
                "working_memory_store",
                self,
                {
                    "max_thoughts": self.max_thoughts,
                    "default_ttl": self.default_ttl
                }
            )
    
    async def shutdown(self):
        """Shutdown the store gracefully"""
        self.logger.info("Shutting down Working Memory Store")
        
        # Unregister from service registry
        if self.service_registry:
            await self.service_registry.unregister_service("working_memory_store")
    
    async def store_thought(self, thought_id: str, thought_data: Dict[str, Any]) -> bool:
        """
        Store a thought in working memory.
        
        Args:
            thought_id: Unique identifier for the thought
            thought_data: Thought data to store
            
        Returns:
            bool: Success status
        """
        try:
            self._store_count += 1
            
            # Try Redis first
            if self.connection_pool:
                redis_client = self.connection_pool.get_redis_client()
                
                # Store in Redis hash
                await redis_client.hset(
                    "working_memory:thoughts",
                    thought_id,
                    json.dumps(thought_data)
                )
                
                # Add to recent thoughts list
                await redis_client.lpush("working_memory:recent", thought_id)
                await redis_client.ltrim("working_memory:recent", 0, self.max_thoughts - 1)
                
                # Set TTL on the thought
                ttl = thought_data.get('ttl', self.default_ttl)
                if ttl:
                    await redis_client.expire(f"thought:{thought_id}", ttl)
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to store thought in Redis: {e}")
        
        # Fallback to in-memory storage
        self._recent_thoughts.append(thought_id)
        self._short_term_cache[thought_id] = thought_data
        
        # Cleanup old entries if cache is too large
        if len(self._short_term_cache) > self.max_thoughts * 2:
            self._cleanup_cache()
        
        return True
    
    async def get_thought(self, thought_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific thought by ID.
        
        Args:
            thought_id: Thought identifier
            
        Returns:
            Thought data if found, None otherwise
        """
        self._retrieve_count += 1
        
        try:
            # Try Redis first
            if self.connection_pool:
                redis_client = self.connection_pool.get_redis_client()
                
                thought_data = await redis_client.hget("working_memory:thoughts", thought_id)
                if thought_data:
                    self._update_hit_rate(True)
                    return json.loads(thought_data)
                    
        except Exception as e:
            self.logger.error(f"Failed to retrieve thought from Redis: {e}")
        
        # Fallback to in-memory storage
        thought = self._short_term_cache.get(thought_id)
        if thought:
            self._update_hit_rate(True)
            return thought
        
        self._update_hit_rate(False)
        return None
    
    async def get_recent_thoughts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent thoughts.
        
        Args:
            limit: Maximum number of thoughts to return
            
        Returns:
            List of recent thoughts
        """
        thoughts = []
        
        try:
            # Try Redis first
            if self.connection_pool:
                redis_client = self.connection_pool.get_redis_client()
                
                # Get recent thought IDs
                thought_ids = await redis_client.lrange("working_memory:recent", 0, limit - 1)
                
                if thought_ids:
                    # Get thought data for each ID
                    for thought_id in thought_ids:
                        thought_data = await redis_client.hget(
                            "working_memory:thoughts",
                            thought_id.decode() if isinstance(thought_id, bytes) else thought_id
                        )
                        if thought_data:
                            thoughts.append(json.loads(thought_data))
                    
                    return thoughts
                    
        except Exception as e:
            self.logger.error(f"Failed to get recent thoughts from Redis: {e}")
        
        # Fallback to in-memory storage
        recent_ids = list(self._recent_thoughts)[-limit:]
        for thought_id in reversed(recent_ids):
            thought = self._short_term_cache.get(thought_id)
            if thought:
                thoughts.append(thought)
        
        return thoughts
    
    async def update_context(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Update active context.
        
        Args:
            key: Context key
            value: Context value
            ttl: Optional TTL in seconds
            
        Returns:
            bool: Success status
        """
        try:
            # Try Redis first
            if self.connection_pool:
                redis_client = self.connection_pool.get_redis_client()
                
                # Store in Redis with context prefix
                redis_key = f"working_memory:context:{key}"
                
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value)
                else:
                    value_str = str(value)
                
                await redis_client.set(redis_key, value_str)
                
                if ttl:
                    await redis_client.expire(redis_key, ttl)
                elif ttl is None:
                    # Use default TTL
                    await redis_client.expire(redis_key, self.default_ttl)
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update context in Redis: {e}")
        
        # Fallback to in-memory storage
        self._active_context[key] = value
        return True
    
    async def get_context(self, key: str) -> Any:
        """
        Get value from active context.
        
        Args:
            key: Context key
            
        Returns:
            Context value if found, None otherwise
        """
        try:
            # Try Redis first
            if self.connection_pool:
                redis_client = self.connection_pool.get_redis_client()
                
                value = await redis_client.get(f"working_memory:context:{key}")
                if value:
                    # Try to parse as JSON
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value.decode() if isinstance(value, bytes) else value
                        
        except Exception as e:
            self.logger.error(f"Failed to get context from Redis: {e}")
        
        # Fallback to in-memory storage
        return self._active_context.get(key)
    
    async def get_all_context(self) -> Dict[str, Any]:
        """
        Get all active context.
        
        Returns:
            Dict of all context key-value pairs
        """
        context = {}
        
        try:
            # Try Redis first
            if self.connection_pool:
                redis_client = self.connection_pool.get_redis_client()
                
                # Get all context keys
                keys = await redis_client.keys("working_memory:context:*")
                
                for key in keys:
                    # Extract the actual key name
                    key_str = key.decode() if isinstance(key, bytes) else key
                    context_key = key_str.replace("working_memory:context:", "")
                    
                    value = await redis_client.get(key)
                    if value:
                        try:
                            context[context_key] = json.loads(value)
                        except json.JSONDecodeError:
                            context[context_key] = value.decode() if isinstance(value, bytes) else value
                            
                return context
                
        except Exception as e:
            self.logger.error(f"Failed to get all context from Redis: {e}")
        
        # Fallback to in-memory storage
        return self._active_context.copy()
    
    async def clear_context(self) -> bool:
        """
        Clear all active context.
        
        Returns:
            bool: Success status
        """
        try:
            # Try Redis first
            if self.connection_pool:
                redis_client = self.connection_pool.get_redis_client()
                
                # Get all context keys and delete them
                keys = await redis_client.keys("working_memory:context:*")
                if keys:
                    await redis_client.delete(*keys)
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to clear context in Redis: {e}")
        
        # Clear in-memory storage
        self._active_context.clear()
        return True
    
    async def clear_all(self) -> bool:
        """
        Clear all working memory.
        
        Returns:
            bool: Success status
        """
        try:
            # Try Redis first
            if self.connection_pool:
                redis_client = self.connection_pool.get_redis_client()
                
                # Clear thoughts
                await redis_client.delete("working_memory:thoughts")
                await redis_client.delete("working_memory:recent")
                
                # Clear context
                await self.clear_context()
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to clear working memory in Redis: {e}")
        
        # Clear in-memory storage
        self._recent_thoughts.clear()
        self._short_term_cache.clear()
        self._active_context.clear()
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get working memory statistics.
        
        Returns:
            Dict of statistics
        """
        return {
            "store_count": self._store_count,
            "retrieve_count": self._retrieve_count,
            "hit_rate": round(self._hit_rate, 2),
            "thoughts_in_memory": len(self._short_term_cache),
            "context_keys": len(self._active_context),
            "max_thoughts": self.max_thoughts
        }
    
    # Private helper methods
    
    def _cleanup_cache(self):
        """Clean up old entries from in-memory cache"""
        # Keep only thoughts that are in recent_thoughts
        valid_ids = set(self._recent_thoughts)
        self._short_term_cache = {
            k: v for k, v in self._short_term_cache.items()
            if k in valid_ids
        }
    
    def _update_hit_rate(self, hit: bool):
        """Update cache hit rate"""
        if self._retrieve_count == 1:
            self._hit_rate = 1.0 if hit else 0.0
        else:
            # Running average
            self._hit_rate = (
                (self._hit_rate * (self._retrieve_count - 1) + (1.0 if hit else 0.0)) /
                self._retrieve_count
            )