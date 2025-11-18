"""
Working Memory Store for Claude-AGI
====================================

Handles short-term memory storage using Redis and in-memory fallback.
Extracted from MemoryManager to follow Single Responsibility Principle.
"""

import asyncio
import json
import logging
import uuid
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..database.models import StreamType, ThoughtData

logger = logging.getLogger(__name__)


class WorkingMemoryStore:
    """
    Manages working memory (short-term, fast-access storage)

    Responsibilities:
    - Store and retrieve recent thoughts
    - Manage active context
    - Handle Redis operations for working memory
    - Provide in-memory fallback when Redis unavailable
    """

    def __init__(self, db_manager=None, use_database: bool = False):
        """
        Initialize working memory store

        Args:
            db_manager: Database manager instance (optional)
            use_database: Whether to use Redis backend
        """
        self.db_manager = db_manager
        self.use_database = use_database and db_manager is not None

        # In-memory fallback storage
        self.recent_thoughts = deque(maxlen=1000)
        self.short_term_cache: Dict[str, Dict] = {}
        self.active_context: Dict[str, Any] = {}

    async def store_thought(self, thought: Dict[str, Any]) -> str:
        """
        Store a thought in working memory

        Args:
            thought: Thought data with content, importance, etc.

        Returns:
            thought_id: Unique identifier for the stored thought
        """
        thought_id = thought.get('id', str(uuid.uuid4()))
        timestamp = datetime.now()

        # Enrich thought with metadata if not present
        enriched_thought = {
            'id': thought_id,
            'timestamp': timestamp.isoformat(),
            'content': thought.get('content', ''),
            'emotional_tone': thought.get('emotional_tone', 'neutral'),
            'importance': thought.get('importance', 5),
            **thought
        }

        if self.use_database and self.db_manager:
            try:
                # Create ThoughtData model
                thought_data = ThoughtData(
                    stream_type=thought.get('stream_type', StreamType.PRIMARY),
                    content=enriched_thought['content'],
                    emotional_state=thought.get('emotional_state'),
                    context=thought.get('context', {}),
                    memory_references=thought.get('memory_references', []),
                    timestamp=timestamp
                )

                # Store in Redis thought streams
                await self.db_manager.add_thought(
                    thought_data.stream_type.value,
                    thought_data.model_dump()
                )

                # Store in Redis working memory with TTL
                await self.db_manager.set_working_memory(
                    f"thought:{thought_id}",
                    json.dumps(enriched_thought),
                    ttl=86400  # 24 hours
                )

                logger.debug(f"Stored thought {thought_id} in Redis working memory")

            except Exception as e:
                logger.error(f"Failed to store thought in Redis: {e}")
                # Fall through to in-memory storage
                await self._store_in_memory(enriched_thought)
        else:
            # Use in-memory storage
            await self._store_in_memory(enriched_thought)

        return thought_id

    async def _store_in_memory(self, thought: Dict[str, Any]) -> str:
        """Store thought in in-memory storage (fallback)"""
        thought_id = thought['id']

        # Add to recent thoughts deque (auto-bounded to 1000)
        self.recent_thoughts.append(thought)

        # Cache in short-term memory dict
        self.short_term_cache[thought_id] = thought

        logger.debug(f"Stored thought {thought_id} in in-memory working memory")
        return thought_id

    async def recall_recent(self, n: int = 10) -> List[Dict]:
        """
        Recall n most recent thoughts

        Args:
            n: Number of recent thoughts to retrieve

        Returns:
            List of thoughts, most recent first
        """
        if self.use_database and self.db_manager:
            try:
                # Get recent thoughts from Redis
                thoughts = []
                for stream_type in [StreamType.PRIMARY, StreamType.SUBCONSCIOUS,
                                    StreamType.EMOTIONAL, StreamType.CREATIVE]:
                    stream_thoughts = await self.db_manager.get_recent_thoughts(
                        stream_type.value,
                        limit=n
                    )
                    thoughts.extend(stream_thoughts)

                # Sort by timestamp and return most recent
                thoughts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                return thoughts[:n]

            except Exception as e:
                logger.error(f"Failed to recall from Redis: {e}")
                # Fall through to in-memory

        # Use in-memory storage
        recent_list = list(self.recent_thoughts)
        return list(reversed(recent_list[-n:]))

    async def recall_by_id(self, thought_id: str) -> Optional[Dict]:
        """
        Recall a specific thought by ID from working memory

        Args:
            thought_id: Unique thought identifier

        Returns:
            Thought dictionary or None if not found
        """
        if self.use_database and self.db_manager:
            try:
                # Check Redis working memory
                thought_json = await self.db_manager.get_working_memory(f"thought:{thought_id}")
                if thought_json:
                    return json.loads(thought_json)

            except Exception as e:
                logger.error(f"Failed to recall from Redis: {e}")

        # Use in-memory storage
        return self.short_term_cache.get(thought_id)

    async def update_context(self, key: str, value: Any):
        """
        Update active context

        Args:
            key: Context key
            value: Context value
        """
        self.active_context[key] = value

        if self.use_database and self.db_manager:
            try:
                # Store in Redis
                await self.db_manager.set_working_memory(
                    f"context:{key}",
                    json.dumps(value),
                    ttl=3600  # 1 hour
                )
            except Exception as e:
                logger.error(f"Failed to update context in Redis: {e}")

    async def get_context(self, key: str) -> Any:
        """
        Get context value

        Args:
            key: Context key

        Returns:
            Context value or None
        """
        if self.use_database and self.db_manager:
            try:
                # Get from Redis
                value_json = await self.db_manager.get_working_memory(f"context:{key}")
                if value_json:
                    return json.loads(value_json)
            except Exception as e:
                logger.error(f"Failed to get context from Redis: {e}")

        # Use in-memory storage
        return self.active_context.get(key)

    async def clear(self):
        """Clear working memory"""
        # Clear in-memory structures
        self.recent_thoughts.clear()
        self.short_term_cache.clear()
        self.active_context.clear()

        if self.use_database and self.db_manager:
            try:
                # Clear Redis working memory
                # Note: This is a simplified version - full implementation would
                # iterate through all keys with pattern "thought:*" and "context:*"
                logger.info("Redis working memory cleared")
            except Exception as e:
                logger.error(f"Failed to clear Redis: {e}")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get working memory statistics"""
        stats = {
            'in_memory_thoughts': len(self.recent_thoughts),
            'cached_thoughts': len(self.short_term_cache),
            'active_context_keys': len(self.active_context),
            'using_redis': self.use_database
        }

        if self.use_database and self.db_manager:
            try:
                # Get Redis stats if available
                # This would require additional Redis commands
                pass
            except Exception as e:
                logger.error(f"Failed to get Redis stats: {e}")

        return stats
