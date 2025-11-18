"""
Episodic Memory Store for Claude-AGI
====================================

Handles long-term memory storage using PostgreSQL and in-memory fallback.
Extracted from MemoryManager to follow Single Responsibility Principle.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..database.models import MemoryType

logger = logging.getLogger(__name__)


class EpisodicMemoryStore:
    """
    Manages episodic memory (long-term, persistent storage)

    Responsibilities:
    - Store and retrieve long-term memories
    - Handle PostgreSQL operations
    - Manage memory consolidation
    - Provide in-memory fallback when PostgreSQL unavailable
    """

    def __init__(self, db_manager=None, embedder=None, use_database: bool = False):
        """
        Initialize episodic memory store

        Args:
            db_manager: Database manager instance (optional)
            embedder: Sentence transformer for embeddings (optional)
            use_database: Whether to use PostgreSQL backend
        """
        self.db_manager = db_manager
        self.embedder = embedder
        self.use_database = use_database and db_manager is not None

        # In-memory fallback storage
        self.long_term_memories: List[Dict] = []

    async def store_memory(self, memory_data: Dict[str, Any]) -> str:
        """
        Store a memory in long-term storage

        Args:
            memory_data: Memory data including content, importance, context

        Returns:
            memory_id: Unique identifier for the stored memory
        """
        if self.use_database and self.db_manager:
            try:
                # Generate embedding if we have content and embedder
                embedding = memory_data.get('embedding')
                if not embedding and self.embedder and memory_data.get('content'):
                    embedding = self.embedder.encode(memory_data['content']).tolist()
                    memory_data['embedding'] = embedding

                # Store in PostgreSQL
                await self.db_manager.store_memory(memory_data)

                logger.debug(f"Stored memory in PostgreSQL: {memory_data.get('content', '')[:50]}...")
                return str(memory_data.get('id', 'unknown'))

            except Exception as e:
                logger.error(f"Failed to store memory in PostgreSQL: {e}")
                # Fall through to in-memory storage
                return await self._store_in_memory(memory_data)
        else:
            # Use in-memory storage
            return await self._store_in_memory(memory_data)

    async def _store_in_memory(self, memory_data: Dict[str, Any]) -> str:
        """Store memory in in-memory storage (fallback)"""
        memory_id = memory_data.get('id', f"mem_{len(self.long_term_memories)}")
        memory_data['id'] = memory_id
        memory_data['stored_at'] = datetime.now().isoformat()

        self.long_term_memories.append(memory_data)

        logger.debug(f"Stored memory {memory_id} in in-memory long-term storage")
        return str(memory_id)

    async def recall_by_id(self, memory_id: str) -> Optional[Dict]:
        """
        Recall a specific memory by ID

        Args:
            memory_id: Unique memory identifier

        Returns:
            Memory dictionary or None if not found
        """
        if self.use_database and self.db_manager:
            try:
                # Query PostgreSQL
                async with self.db_manager.get_connection() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute(
                            """
                            SELECT id, memory_type, content, embedding, emotional_valence,
                                   importance, context, associations, created_at, accessed_at
                            FROM memories
                            WHERE id = %s
                            """,
                            (memory_id,)
                        )
                        result = await cursor.fetchone()

                        if result:
                            # Update access timestamp
                            await cursor.execute(
                                "UPDATE memories SET accessed_at = %s WHERE id = %s",
                                (datetime.now(), memory_id)
                            )
                            await conn.commit()

                            return {
                                'id': result[0],
                                'memory_type': result[1],
                                'content': result[2],
                                'embedding': result[3],
                                'emotional_valence': result[4],
                                'importance': result[5],
                                'context': result[6],
                                'associations': result[7],
                                'created_at': result[8],
                                'accessed_at': result[9],
                                'source': 'postgresql'
                            }

            except Exception as e:
                logger.error(f"Failed to recall from PostgreSQL: {e}")

        # Use in-memory storage
        for memory in self.long_term_memories:
            if str(memory.get('id')) == str(memory_id):
                return memory

        return None

    async def recall_recent(self, n: int = 10, memory_type: Optional[str] = None) -> List[Dict]:
        """
        Recall n most recent memories

        Args:
            n: Number of memories to retrieve
            memory_type: Optional filter by memory type

        Returns:
            List of memories, most recent first
        """
        if self.use_database and self.db_manager:
            try:
                # Query PostgreSQL
                async with self.db_manager.get_connection() as conn:
                    async with conn.cursor() as cursor:
                        if memory_type:
                            await cursor.execute(
                                """
                                SELECT id, memory_type, content, importance, created_at
                                FROM memories
                                WHERE memory_type = %s
                                ORDER BY created_at DESC
                                LIMIT %s
                                """,
                                (memory_type, n)
                            )
                        else:
                            await cursor.execute(
                                """
                                SELECT id, memory_type, content, importance, created_at
                                FROM memories
                                ORDER BY created_at DESC
                                LIMIT %s
                                """,
                                (n,)
                            )

                        results = await cursor.fetchall()
                        return [
                            {
                                'id': row[0],
                                'memory_type': row[1],
                                'content': row[2],
                                'importance': row[3],
                                'created_at': row[4],
                                'source': 'postgresql'
                            }
                            for row in results
                        ]

            except Exception as e:
                logger.error(f"Failed to recall from PostgreSQL: {e}")

        # Use in-memory storage
        filtered = self.long_term_memories
        if memory_type:
            filtered = [m for m in filtered if m.get('memory_type') == memory_type]

        # Sort by creation time (most recent first)
        sorted_memories = sorted(
            filtered,
            key=lambda m: m.get('stored_at', m.get('created_at', '')),
            reverse=True
        )
        return sorted_memories[:n]

    async def recall_important(self, threshold: float = 0.7, limit: int = 20) -> List[Dict]:
        """
        Recall important memories above a certain threshold

        Args:
            threshold: Minimum importance (0.0-1.0)
            limit: Maximum number of memories to return

        Returns:
            List of important memories
        """
        if self.use_database and self.db_manager:
            try:
                # Query PostgreSQL
                async with self.db_manager.get_connection() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute(
                            """
                            SELECT id, memory_type, content, importance, created_at
                            FROM memories
                            WHERE importance >= %s
                            ORDER BY importance DESC, created_at DESC
                            LIMIT %s
                            """,
                            (threshold, limit)
                        )

                        results = await cursor.fetchall()
                        return [
                            {
                                'id': row[0],
                                'memory_type': row[1],
                                'content': row[2],
                                'importance': row[3],
                                'created_at': row[4],
                                'source': 'postgresql'
                            }
                            for row in results
                        ]

            except Exception as e:
                logger.error(f"Failed to recall important memories from PostgreSQL: {e}")

        # Use in-memory storage
        important = [
            m for m in self.long_term_memories
            if m.get('importance', 0) >= threshold
        ]
        important.sort(key=lambda m: m.get('importance', 0), reverse=True)
        return important[:limit]

    async def prune_old_memories(self, days_old: int = 90, min_importance: float = 0.5):
        """
        Prune old, low-importance memories

        Args:
            days_old: Age threshold in days
            min_importance: Importance threshold (0.0-1.0)
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)

        if self.use_database and self.db_manager:
            try:
                # Delete from PostgreSQL
                async with self.db_manager.get_connection() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute(
                            """
                            DELETE FROM memories
                            WHERE created_at < %s
                              AND importance < %s
                            """,
                            (cutoff_date, min_importance)
                        )
                        deleted_count = cursor.rowcount
                        await conn.commit()

                        logger.info(f"Pruned {deleted_count} old memories from PostgreSQL")

            except Exception as e:
                logger.error(f"Failed to prune PostgreSQL memories: {e}")

        # Prune in-memory storage
        original_count = len(self.long_term_memories)
        self.long_term_memories = [
            m for m in self.long_term_memories
            if not (
                datetime.fromisoformat(m.get('stored_at', m.get('created_at', datetime.now().isoformat()))) < cutoff_date
                and m.get('importance', 1.0) < min_importance
            )
        ]
        pruned_count = original_count - len(self.long_term_memories)
        if pruned_count > 0:
            logger.info(f"Pruned {pruned_count} old memories from in-memory storage")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get episodic memory statistics"""
        stats = {
            'in_memory_memories': len(self.long_term_memories),
            'using_postgresql': self.use_database,
            'has_embedder': self.embedder is not None
        }

        if self.use_database and self.db_manager:
            try:
                # Get PostgreSQL stats
                async with self.db_manager.get_connection() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute("SELECT COUNT(*) FROM memories")
                        result = await cursor.fetchone()
                        stats['postgresql_memories'] = result[0] if result else 0

                        await cursor.execute(
                            "SELECT AVG(importance) FROM memories WHERE importance IS NOT NULL"
                        )
                        result = await cursor.fetchone()
                        stats['average_importance'] = float(result[0]) if result and result[0] else 0.0

            except Exception as e:
                logger.error(f"Failed to get PostgreSQL stats: {e}")

        return stats
