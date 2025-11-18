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
from .memory_coordinator import MemoryCoordinator
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
    - MemoryCoordinator: High-level operations

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
        self.coordinator: Optional[MemoryCoordinator] = None

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

        # Create coordinator
        self.coordinator = MemoryCoordinator(
            self.working_memory,
            self.episodic_memory,
            self.semantic_index
        )

        logger.info("Refactored memory manager initialized successfully")
        logger.info(f"  - Working memory: {'Redis' if self.use_database else 'In-memory'}")
        logger.info(f"  - Episodic memory: {'PostgreSQL' if self.use_database else 'In-memory'}")
        logger.info(f"  - Semantic index: {'FAISS' if self.use_database else 'Simple vector store'}")

    # ==========================
    # Public API (Backwards Compatible)
    # ==========================

    async def store_thought(self, thought: Dict[str, Any]) -> str:
        """Store a thought (delegates to coordinator)"""
        if not self.coordinator:
            raise RuntimeError("MemoryManager not initialized")
        return await self.coordinator.store_thought(thought)

    async def recall_recent(self, n: int = 10) -> List[Dict]:
        """Recall recent thoughts (delegates to coordinator)"""
        if not self.coordinator:
            raise RuntimeError("MemoryManager not initialized")
        return await self.coordinator.recall_recent(n, include_episodic=False)

    async def recall_by_id(self, thought_id: str) -> Optional[Dict]:
        """Recall specific thought by ID (delegates to coordinator)"""
        if not self.coordinator:
            raise RuntimeError("MemoryManager not initialized")
        return await self.coordinator.recall_by_id(thought_id)

    async def recall_similar(self, query: str, k: int = 5) -> List[Dict]:
        """Recall similar memories (delegates to coordinator)"""
        if not self.coordinator:
            raise RuntimeError("MemoryManager not initialized")
        return await self.coordinator.recall_similar(query, k, threshold=0.5)

    async def consolidate_memories(self):
        """Consolidate working memory to long-term (delegates to coordinator)"""
        if not self.coordinator:
            raise RuntimeError("MemoryManager not initialized")
        await self.coordinator.consolidate_memories(min_importance=0.5)

    async def identify_important_memories(self, thoughts: List[Dict]) -> List[Dict]:
        """Identify important memories (simple filtering)"""
        return [t for t in thoughts if t.get('importance', 0) >= 7]

    async def create_associations(self, thoughts: List[Dict]):
        """Create associations between thoughts (delegates to coordinator)"""
        if not self.coordinator:
            raise RuntimeError("MemoryManager not initialized")
        await self.coordinator.create_associations(thoughts)

    async def prune_memories(self):
        """Prune old memories (delegates to coordinator)"""
        if not self.coordinator:
            raise RuntimeError("MemoryManager not initialized")
        await self.coordinator.prune_memories(days_old=90, min_importance=0.3)

    async def update_context(self, key: str, value: Any):
        """Update active context (delegates to coordinator)"""
        if not self.coordinator:
            raise RuntimeError("MemoryManager not initialized")
        await self.coordinator.update_context(key, value)

    async def get_context(self, key: str) -> Any:
        """Get context value (delegates to coordinator)"""
        if not self.coordinator:
            raise RuntimeError("MemoryManager not initialized")
        return await self.coordinator.get_context(key)

    async def clear_working_memory(self):
        """Clear working memory (delegates to coordinator)"""
        if not self.coordinator:
            raise RuntimeError("MemoryManager not initialized")
        await self.coordinator.clear_working_memory()

    async def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics (delegates to coordinator)"""
        if not self.coordinator:
            raise RuntimeError("MemoryManager not initialized")
        return await self.coordinator.get_statistics()

    async def handle_message(self, message):
        """Handle messages from other services (delegates to coordinator)"""
        if not self.coordinator:
            raise RuntimeError("MemoryManager not initialized")
        return await self.coordinator.handle_message(message)

    async def close(self):
        """Clean up resources (delegates to coordinator)"""
        if self.coordinator:
            await self.coordinator.close()

    # ==========================
    # Utility Methods (for backwards compatibility)
    # ==========================

    def _get_emotional_intensity(self, thought: Dict) -> float:
        """Get emotional intensity from thought"""
        emotional_tone = thought.get('emotional_tone', 'neutral')

        intensity_map = {
            'joy': 0.8,
            'contentment': 0.4,
            'neutral': 0.0,
            'concern': 0.5,
            'anxiety': 0.7,
            'sadness': 0.6
        }

        return intensity_map.get(emotional_tone, 0.0)

    def _get_emotional_valence(self, thought: Dict) -> float:
        """Get emotional valence from thought"""
        return self.coordinator._get_emotional_valence(thought) if self.coordinator else 0.0

    # ==========================
    # Additional helper methods for TUI compatibility
    # ==========================

    async def get_recent_memories(self, limit: int = 10) -> List[Dict]:
        """Get recent memories (alias for recall_recent)"""
        return await self.recall_recent(limit)

    # ==========================
    # Component Access (for advanced use)
    # ==========================

    def get_working_memory(self) -> Optional[WorkingMemoryStore]:
        """Get working memory component"""
        return self.working_memory

    def get_episodic_memory(self) -> Optional[EpisodicMemoryStore]:
        """Get episodic memory component"""
        return self.episodic_memory

    def get_semantic_index(self) -> Optional[SemanticIndex]:
        """Get semantic index component"""
        return self.semantic_index

    def get_coordinator(self) -> Optional[MemoryCoordinator]:
        """Get memory coordinator"""
        return self.coordinator
