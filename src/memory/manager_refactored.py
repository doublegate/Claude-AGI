"""
Refactored Memory Manager for Claude-AGI
=========================================

Thin coordinator that delegates to specialized memory components.
Maintains backwards compatibility with original MemoryManager API.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    SentenceTransformer = None

try:
    from ..database.connections import get_db_manager, DatabaseManager
    HAS_DATABASE = True
except ImportError:
    HAS_DATABASE = False
    get_db_manager = None
    DatabaseManager = None

from .episodic_memory_store import EpisodicMemoryStore
from .semantic_index import SemanticIndex
from .working_memory_store import WorkingMemoryStore

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Refactored Memory Manager (Thin Coordinator)

    Delegates to specialized components:
    - WorkingMemoryStore: Redis and short-term storage
    - EpisodicMemoryStore: PostgreSQL and long-term storage
    - SemanticIndex: FAISS and similarity search

    Maintains backwards compatibility with original MemoryManager API.
    """

    def __init__(self):
        """Initialize memory manager with components"""
        self.db_manager: Optional[DatabaseManager] = None
        self.embedder: Optional[SentenceTransformer] = None
        self.use_database = False

        # Specialized components (initialized in initialize())
        self.working_memory: Optional[WorkingMemoryStore] = None
        self.episodic_memory: Optional[EpisodicMemoryStore] = None
        self.semantic_index: Optional[SemanticIndex] = None

        # Message queue for service integration (backwards compatibility)
        self.message_queue = asyncio.Queue()

    @classmethod
    async def create(cls):
        """Factory method to create and initialize MemoryManager"""
        instance = cls()
        await instance.initialize()
        return instance

    async def initialize(self, use_database: bool = False):
        """Initialize memory stores and components"""
        logger.info("Initializing refactored memory manager with specialized components...")

        # Check database availability
        if not HAS_DATABASE:
            logger.warning("Database dependencies not available, using in-memory storage only")
            use_database = False

        self.use_database = use_database

        # Initialize database and embedder if requested
        if use_database and HAS_DATABASE:
            try:
                self.db_manager = await get_db_manager()
                logger.info("Database connections established")

                # Initialize sentence transformer for embeddings
                if HAS_SENTENCE_TRANSFORMERS:
                    self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
                    logger.info("Sentence transformer initialized")
                else:
                    logger.warning("Sentence transformers not available, semantic search will be limited")

            except Exception as e:
                logger.error(f"Failed to initialize database connections: {e}")
                logger.info("Falling back to in-memory storage")
                self.use_database = False

        # Initialize specialized components
        self.working_memory = WorkingMemoryStore(self.db_manager, self.use_database)
        self.episodic_memory = EpisodicMemoryStore(self.db_manager, self.embedder, self.use_database)
        self.semantic_index = SemanticIndex(self.embedder, use_faiss=self.use_database)

        # Initialize semantic index
        await self.semantic_index.initialize()

        logger.info("Refactored memory manager initialized successfully")
        logger.info(f"  - Working memory: {'Redis' if self.use_database else 'In-memory'}")
        logger.info(f"  - Episodic memory: {'PostgreSQL' if self.use_database else 'In-memory'}")
        logger.info(f"  - Semantic index: {'FAISS' if self.use_database else 'Simple vector store'}")

    # ==========================
    # Public API (Backwards Compatible)
    # ==========================

    async def store_thought(self, thought: Dict[str, Any]) -> str:
        """Store a thought (delegates to working memory)"""
        if not self.working_memory:
            raise RuntimeError("MemoryManager not initialized")
        return await self.working_memory.store_thought(thought)

    async def recall_recent(self, n: int = 10) -> List[Dict]:
        """Recall recent thoughts (delegates to working memory)"""
        if not self.working_memory:
            raise RuntimeError("MemoryManager not initialized")
        return await self.working_memory.recall_recent(n)

    async def recall_by_id(self, thought_id: str) -> Optional[Dict]:
        """Recall specific thought by ID (delegates to working memory)"""
        if not self.working_memory:
            raise RuntimeError("MemoryManager not initialized")
        return await self.working_memory.recall_by_id(thought_id)

    async def recall_similar(self, query: str, k: int = 5) -> List[Dict]:
        """Recall similar memories (delegates to semantic index)"""
        if not self.semantic_index:
            raise RuntimeError("MemoryManager not initialized")
        results = await self.semantic_index.search(query, k)
        # Convert results to memory format
        memories = []
        for thought_id, score in results:
            memory = await self.working_memory.recall_by_id(thought_id)
            if memory:
                memory['similarity_score'] = score
                memories.append(memory)
        return memories

    async def consolidate_memories(self, min_importance: float = 0.5):
        """Consolidate working memory to episodic (basic implementation)"""
        if not self.working_memory or not self.episodic_memory:
            raise RuntimeError("MemoryManager not initialized")

        # Get recent thoughts
        recent = await self.working_memory.recall_recent(n=100)

        # Move important thoughts to episodic memory
        for thought in recent:
            importance = thought.get('importance', 0)
            if importance >= min_importance * 10:  # Scale to 0-10
                await self.episodic_memory.store_memory(thought)

    async def create_associations(self, thoughts: List[Dict]):
        """Create associations between thoughts (placeholder)"""
        # Future implementation could use semantic index to link related thoughts
        logger.info(f"Creating associations for {len(thoughts)} thoughts")

    async def prune_memories(self, days_old: int = 90, min_importance: float = 0.3):
        """Prune old memories (delegates to episodic memory)"""
        if not self.episodic_memory:
            raise RuntimeError("MemoryManager not initialized")
        await self.episodic_memory.prune_old_memories(days_old, min_importance)

    async def update_context(self, key: str, value: Any):
        """Update context (delegates to working memory)"""
        if not self.working_memory:
            raise RuntimeError("MemoryManager not initialized")
        await self.working_memory.update_context(key, value)

    async def get_context(self, key: str) -> Any:
        """Get context value (delegates to working memory)"""
        if not self.working_memory:
            raise RuntimeError("MemoryManager not initialized")
        return await self.working_memory.get_context(key)

    async def clear_working_memory(self):
        """Clear working memory (delegates to working memory store)"""
        if not self.working_memory:
            raise RuntimeError("MemoryManager not initialized")
        await self.working_memory.clear()

    async def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics (aggregates from all stores)"""
        stats = {}

        if self.working_memory:
            recent = await self.working_memory.recall_recent(n=10000)
            stats['working_memory'] = {
                'thought_count': len(recent),
                'storage_type': 'Redis' if self.use_database else 'In-memory'
            }

        if self.episodic_memory:
            episodic_recent = await self.episodic_memory.recall_recent(n=10000)
            stats['episodic_memory'] = {
                'memory_count': len(episodic_recent),
                'storage_type': 'PostgreSQL' if self.use_database else 'In-memory'
            }

        if self.semantic_index:
            index_stats = await self.semantic_index.get_statistics()
            stats['semantic_index'] = index_stats

        stats['total_thoughts'] = stats.get('working_memory', {}).get('thought_count', 0)

        return stats

    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle service message (backwards compatibility)"""
        # Basic message handling - store thoughts from messages
        if message.get('type') == 'store_thought':
            thought_id = await self.store_thought(message.get('thought', {}))
            return {'status': 'success', 'thought_id': thought_id}

        return {'status': 'unknown_message_type'}

    async def close(self):
        """Clean up resources"""
        # No cleanup needed for in-memory stores
        # Database connections are managed externally
        logger.info("Memory manager closed")

    # ==========================
    # Component Access (for testing and advanced usage)
    # ==========================

    def get_working_memory(self) -> Optional[WorkingMemoryStore]:
        """Get working memory store"""
        return self.working_memory

    def get_episodic_memory(self) -> Optional[EpisodicMemoryStore]:
        """Get episodic memory store"""
        return self.episodic_memory

    def get_semantic_index(self) -> Optional[SemanticIndex]:
        """Get semantic index"""
        return self.semantic_index

    def get_coordinator(self):
        """Get coordinator (returns self for backwards compatibility)"""
        return self

    # ==========================
    # Helper Methods (backwards compatibility)
    # ==========================

    def _get_emotional_valence(self, thought: Dict) -> float:
        """Get emotional valence of thought (placeholder)"""
        return thought.get('emotional_valence', 0.0)

    # ==========================
    # Service Interface (MessageHandler compatibility)
    # ==========================

    async def send_message(self, message: Dict[str, Any]):
        """Send message (service interface)"""
        await self.message_queue.put(message)

    async def receive_message(self) -> Dict[str, Any]:
        """Receive message (service interface)"""
        return await self.message_queue.get()
