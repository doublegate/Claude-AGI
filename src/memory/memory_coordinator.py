"""
Memory Coordinator

Coordinates between different memory stores and provides a unified interface.
Replaces the god object MemoryManager with a clean, single-responsibility design.
"""

import asyncio
import uuid
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from enum import Enum

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    SentenceTransformer = None

from ..core.service_registry import ServiceRegistry
from ..core.event_bus import EventBus
from ..database.models import MemoryType, StreamType, EmotionalState
from .stores.working_memory_store import WorkingMemoryStore
from .stores.episodic_memory_store import EpisodicMemoryStore
from .stores.semantic_index import SemanticIndex
from .synchronizer import MemorySynchronizer
from .connection_pool import ConnectionPoolManager


class MemoryOperation(Enum):
    """Types of memory operations"""
    STORE = "store"
    RECALL = "recall"
    CONSOLIDATE = "consolidate"
    SEARCH = "search"
    UPDATE_CONTEXT = "update_context"


class MemoryCoordinator:
    """
    Coordinates memory operations across different stores.
    
    This replaces the monolithic MemoryManager with a cleaner design:
    - WorkingMemoryStore: Short-term, fast access (Redis)
    - EpisodicMemoryStore: Long-term storage (PostgreSQL)
    - SemanticIndex: Similarity search (FAISS)
    - MemorySynchronizer: Ensures consistency across stores
    """
    
    def __init__(
        self,
        service_registry: Optional[ServiceRegistry] = None,
        event_bus: Optional[EventBus] = None,
        postgres_dsn: Optional[str] = None,
        redis_url: Optional[str] = None,
        use_embeddings: bool = True,
        embedding_model: str = 'all-MiniLM-L6-v2'
    ):
        self.service_registry = service_registry
        self.event_bus = event_bus
        self.use_embeddings = use_embeddings
        self.embedding_model = embedding_model
        
        self.logger = logging.getLogger(__name__)
        
        # Components
        self.connection_pool: Optional[ConnectionPoolManager] = None
        self.working_memory: Optional[WorkingMemoryStore] = None
        self.episodic_memory: Optional[EpisodicMemoryStore] = None
        self.semantic_index: Optional[SemanticIndex] = None
        self.synchronizer: Optional[MemorySynchronizer] = None
        self.embedder: Optional[SentenceTransformer] = None
        
        # Configuration
        self.postgres_dsn = postgres_dsn
        self.redis_url = redis_url
        
        # Metrics
        self._operation_count = {op: 0 for op in MemoryOperation}
        self._consolidation_count = 0
        
        # Monitoring hooks (optional)
        self.monitoring_hooks = None
        
    async def initialize(self):
        """Initialize all memory components"""
        self.logger.info("Initializing Memory Coordinator")
        
        # Initialize connection pool if database URLs provided
        if self.postgres_dsn or self.redis_url:
            self.connection_pool = ConnectionPoolManager(
                postgres_dsn=self.postgres_dsn,
                redis_url=self.redis_url,
                service_registry=self.service_registry,
                event_bus=self.event_bus
            )
            await self.connection_pool.initialize()
        
        # Initialize working memory store
        self.working_memory = WorkingMemoryStore(
            connection_pool=self.connection_pool,
            service_registry=self.service_registry
        )
        await self.working_memory.initialize()
        
        # Initialize episodic memory store
        self.episodic_memory = EpisodicMemoryStore(
            connection_pool=self.connection_pool,
            service_registry=self.service_registry
        )
        await self.episodic_memory.initialize()
        
        # Initialize embedder if requested
        if self.use_embeddings and HAS_SENTENCE_TRANSFORMERS:
            try:
                self.embedder = SentenceTransformer(self.embedding_model)
                embedding_dim = self.embedder.get_sentence_embedding_dimension()
                
                # Initialize semantic index
                self.semantic_index = SemanticIndex(
                    dimension=embedding_dim,
                    service_registry=self.service_registry
                )
                await self.semantic_index.initialize()
                
                self.logger.info(f"Initialized embedder with dimension {embedding_dim}")
            except Exception as e:
                self.logger.error(f"Failed to initialize embedder: {e}")
                self.use_embeddings = False
        
        # Initialize synchronizer if we have database connections
        if self.connection_pool:
            redis_client = None
            postgres_pool = None
            
            try:
                redis_client = self.connection_pool.get_redis_client()
            except:
                pass
                
            if self.connection_pool._postgres_pool:
                postgres_pool = self.connection_pool._postgres_pool
            
            self.synchronizer = MemorySynchronizer(
                redis_client=redis_client,
                postgres_pool=postgres_pool,
                faiss_index=self.semantic_index.index if self.semantic_index else None,
                service_registry=self.service_registry,
                event_bus=self.event_bus
            )
            await self.synchronizer.initialize()
        
        # Register with service registry
        if self.service_registry:
            await self.service_registry.register_service(
                "memory_coordinator",
                self,
                {
                    "has_database": self.connection_pool is not None,
                    "use_embeddings": self.use_embeddings,
                    "embedding_model": self.embedding_model
                }
            )
        
        self.logger.info("Memory Coordinator initialized")
    
    async def shutdown(self):
        """Shutdown all memory components gracefully"""
        self.logger.info("Shutting down Memory Coordinator")
        
        # Shutdown components in reverse order
        if self.synchronizer:
            await self.synchronizer.shutdown()
        
        if self.semantic_index:
            await self.semantic_index.shutdown()
        
        if self.episodic_memory:
            await self.episodic_memory.shutdown()
        
        if self.working_memory:
            await self.working_memory.shutdown()
        
        if self.connection_pool:
            await self.connection_pool.shutdown()
        
        # Unregister from service registry
        if self.service_registry:
            await self.service_registry.unregister_service("memory_coordinator")
    
    def set_monitoring_hooks(self, monitoring_hooks):
        """Set monitoring hooks for instrumentation"""
        self.monitoring_hooks = monitoring_hooks
        
        # Pass to sub-components
        if self.working_memory and hasattr(self.working_memory, 'set_monitoring_hooks'):
            self.working_memory.set_monitoring_hooks(monitoring_hooks)
        if self.episodic_memory and hasattr(self.episodic_memory, 'set_monitoring_hooks'):
            self.episodic_memory.set_monitoring_hooks(monitoring_hooks)
        if self.synchronizer and hasattr(self.synchronizer, 'set_monitoring_hooks'):
            self.synchronizer.set_monitoring_hooks(monitoring_hooks)
        if self.connection_pool and hasattr(self.connection_pool, 'set_monitoring_hooks'):
            self.connection_pool.set_monitoring_hooks(monitoring_hooks)
    
    async def store_thought(self, thought: Dict[str, Any]) -> str:
        """
        Store a thought across appropriate memory systems.
        
        Args:
            thought: Thought data containing content, importance, etc.
            
        Returns:
            Thought ID
        """
        self._operation_count[MemoryOperation.STORE] += 1
        
        # Track with monitoring if available
        if self.monitoring_hooks:
            self.monitoring_hooks.increment_counter(
                "memory_operations_total",
                labels={"operation": "store", "type": "thought"}
            )
        
        # Generate ID and enrich thought
        thought_id = thought.get('id', str(uuid.uuid4()))
        timestamp = datetime.now(timezone.utc)
        
        enriched_thought = {
            'id': thought_id,
            'memory_id': thought_id,  # For compatibility
            'timestamp': timestamp.isoformat(),
            'content': thought.get('content', ''),
            'emotional_tone': thought.get('emotional_tone', 'neutral'),
            'importance': thought.get('importance', 5) / 10.0,  # Normalize to 0-1
            'stream_type': thought.get('stream_type', StreamType.PRIMARY).value,
            **thought
        }
        
        # Generate embedding if available
        embedding = None
        if self.use_embeddings and self.embedder and enriched_thought['content']:
            try:
                embedding = self.embedder.encode(enriched_thought['content']).tolist()
                enriched_thought['embedding'] = embedding
            except Exception as e:
                self.logger.error(f"Failed to generate embedding: {e}")
        
        # Store in working memory
        await self.working_memory.store_thought(thought_id, enriched_thought)
        
        # Store in episodic memory if important enough
        if enriched_thought['importance'] >= 0.7:
            await self.episodic_memory.store_memory(
                memory_id=thought_id,
                content=enriched_thought['content'],
                memory_type=MemoryType.EPISODIC,
                importance=enriched_thought['importance'],
                emotional_valence=self._calculate_emotional_valence(enriched_thought),
                metadata=enriched_thought,
                embedding=embedding
            )
        
        # Add to semantic index if we have an embedding
        if embedding and self.semantic_index:
            await self.semantic_index.add_vector(
                thought_id,
                embedding,
                {
                    'content': enriched_thought['content'],
                    'importance': enriched_thought['importance'],
                    'timestamp': enriched_thought['timestamp']
                }
            )
        
        # Sync if synchronizer is available
        if self.synchronizer:
            asyncio.create_task(
                self.synchronizer.sync_memory(thought_id, enriched_thought)
            )
        
        # Publish event
        if self.event_bus:
            await self.event_bus.publish(
                "memory.thought_stored",
                {
                    "thought_id": thought_id,
                    "stream_type": enriched_thought['stream_type'],
                    "importance": enriched_thought['importance']
                }
            )
        
        return thought_id
    
    async def recall_recent(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Recall n most recent thoughts.
        
        Args:
            n: Number of thoughts to recall
            
        Returns:
            List of recent thoughts
        """
        self._operation_count[MemoryOperation.RECALL] += 1
        
        # Track with monitoring if available
        if self.monitoring_hooks:
            self.monitoring_hooks.increment_counter(
                "memory_operations_total",
                labels={"operation": "recall", "type": "recent"}
            )
        
        # Get from working memory first
        recent = await self.working_memory.get_recent_thoughts(n)
        
        # If not enough, supplement from episodic memory
        if len(recent) < n:
            episodic = await self.episodic_memory.get_recent_memories(
                limit=n - len(recent)
            )
            recent.extend(episodic)
        
        return recent
    
    async def recall_by_id(self, thought_id: str) -> Optional[Dict[str, Any]]:
        """
        Recall a specific thought by ID.
        
        Args:
            thought_id: Thought/memory ID
            
        Returns:
            Thought data if found
        """
        self._operation_count[MemoryOperation.RECALL] += 1
        
        # Check working memory first
        thought = await self.working_memory.get_thought(thought_id)
        if thought:
            return thought
        
        # Check episodic memory
        memory = await self.episodic_memory.get_memory(thought_id)
        if memory:
            return memory
        
        return None
    
    async def search_similar(
        self,
        query: str,
        k: int = 5,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for memories similar to query.
        
        Args:
            query: Search query
            k: Number of results
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of similar memories
        """
        self._operation_count[MemoryOperation.SEARCH] += 1
        
        # Track with monitoring if available
        if self.monitoring_hooks:
            self.monitoring_hooks.increment_counter(
                "memory_operations_total",
                labels={"operation": "search", "type": "semantic"}
            )
        
        if self.semantic_index and self.embedder:
            try:
                # Generate query embedding
                query_embedding = self.embedder.encode(query).tolist()
                
                # Search in semantic index
                results = await self.semantic_index.search_by_similarity(
                    query_embedding,
                    k=k,
                    min_similarity=min_similarity
                )
                
                # Retrieve full memory data
                memories = []
                for memory_id, similarity, metadata in results:
                    # Try to get full data
                    memory = await self.recall_by_id(memory_id)
                    if memory:
                        memory['similarity_score'] = similarity
                        memories.append(memory)
                    else:
                        # Use metadata if full data not available
                        metadata['memory_id'] = memory_id
                        metadata['similarity_score'] = similarity
                        memories.append(metadata)
                
                return memories
                
            except Exception as e:
                self.logger.error(f"Semantic search failed: {e}")
        
        # Fallback to keyword search
        return await self._keyword_search(query, k)
    
    async def consolidate_memories(self):
        """
        Consolidate memories - identify important patterns and create associations.
        """
        self._operation_count[MemoryOperation.CONSOLIDATE] += 1
        self._consolidation_count += 1
        
        self.logger.info("Starting memory consolidation")
        
        # Get recent thoughts from working memory
        recent_thoughts = await self.working_memory.get_recent_thoughts(100)
        
        # Identify important memories
        important_memories = self._identify_important_memories(recent_thoughts)
        
        # Store important memories in episodic storage
        for memory in important_memories:
            # Generate embedding if needed
            embedding = None
            if self.use_embeddings and self.embedder and memory.get('content'):
                try:
                    embedding = self.embedder.encode(memory['content']).tolist()
                except Exception as e:
                    self.logger.error(f"Failed to generate embedding: {e}")
            
            # Store in episodic memory
            await self.episodic_memory.store_memory(
                memory_id=memory.get('id', str(uuid.uuid4())),
                content=memory.get('content', ''),
                importance=memory.get('importance', 0.5),
                emotional_valence=self._calculate_emotional_valence(memory),
                metadata=memory,
                embedding=embedding
            )
        
        # Create associations between related memories
        await self._create_associations(recent_thoughts)
        
        # Apply decay to old memories
        if self.episodic_memory:
            decayed = await self.episodic_memory.apply_decay()
            self.logger.info(f"Applied decay to {decayed} memories")
        
        # Prune low-importance memories
        if self.episodic_memory:
            pruned = await self.episodic_memory.prune_memories()
            self.logger.info(f"Pruned {pruned} memories")
        
        # Run consistency check if synchronizer available
        if self.synchronizer:
            inconsistencies = await self.synchronizer.check_consistency()
            if inconsistencies:
                self.logger.warning(
                    f"Found {len(inconsistencies)} memory inconsistencies"
                )
                await self.synchronizer.repair_inconsistencies(inconsistencies)
        
        self.logger.info("Memory consolidation complete")
    
    async def update_context(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Update active context.
        
        Args:
            key: Context key
            value: Context value
            ttl: Optional TTL in seconds
        """
        self._operation_count[MemoryOperation.UPDATE_CONTEXT] += 1
        
        await self.working_memory.update_context(key, value, ttl)
        
        # Publish event
        if self.event_bus:
            await self.event_bus.publish(
                "memory.context_updated",
                {"key": key, "has_value": value is not None}
            )
    
    async def get_context(self, key: str) -> Any:
        """
        Get value from active context.
        
        Args:
            key: Context key
            
        Returns:
            Context value if found
        """
        return await self.working_memory.get_context(key)
    
    async def get_all_context(self) -> Dict[str, Any]:
        """
        Get all active context.
        
        Returns:
            Dict of all context
        """
        return await self.working_memory.get_all_context()
    
    async def clear_working_memory(self):
        """Clear working memory (useful for resets)"""
        await self.working_memory.clear_all()
        
        self.logger.info("Working memory cleared")
    
    async def handle_message(self, message):
        """
        Handle incoming messages from orchestrator.
        
        Args:
            message: Message object with type and content
        """
        message_type = message.type
        
        if message_type == 'store_thought':
            await self.store_thought(message.content)
            
        elif message_type == 'recall':
            query = message.content.get('query', '')
            memories = await self.search_similar(query)
            
            # Could send response back through event bus
            if self.event_bus:
                await self.event_bus.publish(
                    "memory.recall_complete",
                    {
                        "query": query,
                        "count": len(memories),
                        "memories": memories[:5]  # First 5 for preview
                    }
                )
            
        elif message_type == 'consolidate':
            await self.consolidate_memories()
            
        else:
            self.logger.debug(f"Memory coordinator received unknown message type: {message_type}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive memory system statistics.
        
        Returns:
            Dict of statistics from all components
        """
        stats = {
            "coordinator": {
                "operations": dict(self._operation_count),
                "consolidations": self._consolidation_count
            }
        }
        
        # Get stats from each component
        if self.working_memory:
            stats["working_memory"] = self.working_memory.get_stats()
        
        if self.episodic_memory:
            stats["episodic_memory"] = self.episodic_memory.get_stats()
        
        if self.semantic_index:
            stats["semantic_index"] = self.semantic_index.get_stats()
        
        if self.connection_pool:
            stats["connections"] = self.connection_pool.get_health_status()
        
        return stats
    
    # Private helper methods
    
    def _identify_important_memories(
        self,
        thoughts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify which memories are important to keep"""
        important = []
        
        for thought in thoughts:
            # Already normalized importance
            importance = thought.get('importance', 0.5)
            
            # Emotional intensity
            emotional_intensity = abs(self._calculate_emotional_valence(thought))
            
            # Combined score
            score = (importance + emotional_intensity) / 2
            
            if score >= 0.6:  # Threshold for importance
                important.append(thought)
        
        return important
    
    def _calculate_emotional_valence(self, thought: Dict[str, Any]) -> float:
        """Calculate emotional valence (-1 to 1) of a thought"""
        emotional_tone = thought.get('emotional_tone', 'neutral')
        
        valence_map = {
            'joy': 0.8, 'excitement': 0.7, 'love': 0.9,
            'calm': 0.3, 'neutral': 0.0,
            'fear': -0.6, 'anger': -0.7, 'sadness': -0.8,
            'surprise': 0.1, 'disgust': -0.6
        }
        
        return valence_map.get(emotional_tone, 0.0)
    
    async def _create_associations(self, thoughts: List[Dict[str, Any]]):
        """Create associations between related memories"""
        if not self.semantic_index or not self.embedder:
            return
        
        # For each thought, find similar ones
        for thought in thoughts[-20:]:  # Last 20 thoughts
            if thought.get('content') and thought.get('id'):
                similar = await self.search_similar(
                    thought['content'],
                    k=3,
                    min_similarity=0.7
                )
                
                # Create associations
                for similar_memory in similar:
                    if similar_memory.get('memory_id') != thought['id']:
                        await self.episodic_memory.create_association(
                            thought['id'],
                            similar_memory['memory_id'],
                            strength=similar_memory.get('similarity_score', 0.5)
                        )
    
    async def _keyword_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Fallback keyword-based search"""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Search in working memory
        recent = await self.working_memory.get_recent_thoughts(100)
        
        # Search in episodic memory
        episodic = await self.episodic_memory.get_recent_memories(100)
        
        # Combine and score
        all_memories = recent + episodic
        scored_memories = []
        
        for memory in all_memories:
            content = memory.get('content', '').lower()
            content_words = set(content.split())
            
            # Calculate Jaccard similarity
            intersection = len(query_words & content_words)
            union = len(query_words | content_words)
            
            if union > 0:
                score = intersection / union
                if score > 0:
                    memory['similarity_score'] = score
                    scored_memories.append(memory)
        
        # Sort by score and return top k
        scored_memories.sort(key=lambda x: x['similarity_score'], reverse=True)
        return scored_memories[:k]