# memory/manager.py

from typing import Dict, List, Optional, Any
import asyncio
import json
import uuid
from datetime import datetime, timedelta
import logging
import numpy as np
from sentence_transformers import SentenceTransformer

from ..database.connections import get_db_manager, DatabaseManager
from ..database.models import MemoryData, MemoryType, ThoughtData, StreamType, EmotionalState

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manages short-term, long-term, and semantic memory"""
    
    def __init__(self):
        self.db_manager: Optional[DatabaseManager] = None
        self.embedder: Optional[SentenceTransformer] = None
        self.use_database = False  # Flag to enable database integration
        
    @classmethod
    async def create(cls):
        """Factory method to create and initialize MemoryManager"""
        instance = cls()
        await instance.initialize()
        return instance
        
    async def initialize(self, use_database: bool = False):
        """Initialize memory stores"""
        logger.info("Initializing memory stores...")
        
        self.use_database = use_database
        
        if use_database:
            # Initialize database connections
            try:
                self.db_manager = await get_db_manager()
                logger.info("Database connections established")
                
                # Initialize sentence transformer for embeddings
                self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Sentence transformer initialized")
            except Exception as e:
                logger.error(f"Failed to initialize database connections: {e}")
                logger.info("Falling back to in-memory storage")
                self.use_database = False
        
        if not self.use_database:
            # Fallback to in-memory storage
            self.working_memory = {
                'recent_thoughts': [],
                'active_context': {},
                'short_term': {}
            }
            self.long_term_memory = []
            self.vector_store = SimpleVectorStore()
            await self.vector_store.initialize()
        
        logger.info("Memory stores initialized")
        
    async def store_thought(self, thought: Dict[str, Any]) -> str:
        """Store a thought in appropriate memory systems"""
        thought_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        # Enrich thought with metadata
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
                
                # Store in Redis and PostgreSQL
                await self.db_manager.add_thought(
                    thought_data.stream_type.value,
                    thought_data.model_dump()
                )
                
                # Store in working memory (Redis)
                await self.db_manager.set_working_memory(
                    f"thought:{thought_id}",
                    json.dumps(enriched_thought),
                    ttl=86400  # 24 hours
                )
                
                # If high importance, also store as long-term memory
                if enriched_thought['importance'] >= 7:
                    # Generate embedding if we have content
                    embedding = None
                    if self.embedder and enriched_thought['content']:
                        embedding = self.embedder.encode(enriched_thought['content']).tolist()
                    
                    memory_data = {
                        'memory_type': MemoryType.EPISODIC.value,
                        'content': enriched_thought['content'],
                        'embedding': embedding,
                        'emotional_valence': self._get_emotional_valence(enriched_thought),
                        'importance': enriched_thought['importance'] / 10.0,  # Normalize to 0-1
                        'context': enriched_thought,
                        'associations': []
                    }
                    
                    await self.db_manager.store_memory(memory_data)
                
            except Exception as e:
                logger.error(f"Failed to store thought in database: {e}")
                # Fall back to in-memory storage
                return await self._store_thought_in_memory(enriched_thought)
        else:
            # Use in-memory storage
            return await self._store_thought_in_memory(enriched_thought)
            
        logger.debug(f"Stored thought {thought_id}")
        return thought_id
    
    async def _store_thought_in_memory(self, enriched_thought: Dict[str, Any]) -> str:
        """Store thought in in-memory storage (fallback)"""
        thought_id = enriched_thought['id']
        
        # Working memory - recent thoughts
        self.working_memory['recent_thoughts'].append(enriched_thought)
        # Keep only last 1000 thoughts
        if len(self.working_memory['recent_thoughts']) > 1000:
            self.working_memory['recent_thoughts'] = self.working_memory['recent_thoughts'][-1000:]
            
        # Short-term memory cache
        self.working_memory['short_term'][thought_id] = enriched_thought
        
        # Long-term memory (simulated)
        if enriched_thought['importance'] >= 7:
            self.long_term_memory.append(enriched_thought)
            
        # Semantic memory - store with embedding if available
        if 'embedding' in enriched_thought:
            await self.vector_store.add(
                thought_id,
                enriched_thought['embedding'],
                enriched_thought
            )
            
        return thought_id
        
    async def recall_recent(self, n: int = 10) -> List[Dict]:
        """Recall n most recent thoughts"""
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
                logger.error(f"Failed to recall from database: {e}")
                # Fall back to in-memory
        
        # Use in-memory storage
        recent = self.working_memory['recent_thoughts'][-n:]
        return list(reversed(recent))
        
    async def recall_by_id(self, thought_id: str) -> Optional[Dict]:
        """Recall a specific thought by ID"""
        if self.use_database and self.db_manager:
            try:
                # Check Redis working memory first
                thought_json = await self.db_manager.get_working_memory(f"thought:{thought_id}")
                if thought_json:
                    return json.loads(thought_json)
                
                # TODO: Query PostgreSQL for older thoughts
                # This would require adding a method to db_manager to query thoughts by ID
            except Exception as e:
                logger.error(f"Failed to recall from database: {e}")
        
        # Use in-memory storage
        if thought_id in self.working_memory['short_term']:
            return self.working_memory['short_term'][thought_id]
            
        # Check long-term memory
        for thought in self.long_term_memory:
            if thought['id'] == thought_id:
                return thought
                
        return None
        
    async def recall_similar(self, query: str, k: int = 5) -> List[Dict]:
        """Recall memories similar to query"""
        if self.use_database and self.db_manager and self.embedder:
            try:
                # Generate embedding for query
                query_embedding = self.embedder.encode(query).tolist()
                
                # Search in FAISS index
                similar_memories = await self.db_manager.search_similar_memories(
                    query_embedding, 
                    k=k
                )
                
                return similar_memories
            except Exception as e:
                logger.error(f"Failed to search similar memories: {e}")
        
        # Fallback to keyword matching
        query_lower = query.lower()
        scored_memories = []
        
        # Search in all memories
        all_memories = (
            self.working_memory.get('recent_thoughts', []) + 
            self.long_term_memory
        )
        
        for memory in all_memories:
            content = memory.get('content', '').lower()
            # Simple scoring based on keyword presence
            score = sum(1 for word in query_lower.split() if word in content)
            if score > 0:
                scored_memories.append((score, memory))
                
        # Sort by score and return top k
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [memory for score, memory in scored_memories[:k]]
        
    async def consolidate_memories(self):
        """Memory consolidation during 'sleep' cycles"""
        logger.info("Starting memory consolidation...")
        
        # Get recent thoughts
        if self.use_database and self.db_manager:
            recent_thoughts = []
            for stream_type in [StreamType.PRIMARY, StreamType.SUBCONSCIOUS]:
                thoughts = await self.db_manager.get_recent_thoughts(stream_type.value, 100)
                recent_thoughts.extend(thoughts)
        else:
            recent_thoughts = self.working_memory['recent_thoughts'][-100:]
        
        # Identify important memories based on various factors
        important_memories = await self.identify_important_memories(recent_thoughts)
        
        # Store important memories in long-term storage
        if self.use_database and self.db_manager and self.embedder:
            for memory in important_memories:
                # Generate embedding
                embedding = None
                if memory.get('content'):
                    embedding = self.embedder.encode(memory['content']).tolist()
                
                memory_data = {
                    'memory_type': MemoryType.EPISODIC.value,
                    'content': memory.get('content', ''),
                    'embedding': embedding,
                    'emotional_valence': self._get_emotional_valence(memory),
                    'importance': memory.get('importance', 5) / 10.0,
                    'context': memory,
                    'associations': []
                }
                
                await self.db_manager.store_memory(memory_data)
        else:
            # In-memory storage
            for memory in important_memories:
                if memory not in self.long_term_memory:
                    self.long_term_memory.append(memory)
                
        # Create associations between related memories
        await self.create_associations(recent_thoughts)
        
        # Prune redundant memories
        await self.prune_memories()
        
        logger.info("Memory consolidation complete")
        
    async def identify_important_memories(self, thoughts: List[Dict]) -> List[Dict]:
        """Identify which memories are important to keep"""
        important = []
        
        for thought in thoughts:
            # Criteria for importance:
            # 1. High emotional intensity
            # 2. High explicit importance rating
            # 3. Frequently accessed
            # 4. Novel or unique content
            
            importance_score = thought.get('importance', 5)
            emotional_intensity = self._get_emotional_intensity(thought)
            
            if importance_score >= 7 or emotional_intensity >= 0.7:
                important.append(thought)
                
        return important
        
    def _get_emotional_intensity(self, thought: Dict) -> float:
        """Calculate emotional intensity of a thought"""
        emotional_tone = thought.get('emotional_tone', 'neutral')
        
        # Simple mapping of emotions to intensity
        intensity_map = {
            'joy': 0.8, 'excitement': 0.9, 'love': 0.9,
            'fear': 0.8, 'anger': 0.8, 'sadness': 0.7,
            'surprise': 0.7, 'disgust': 0.6,
            'neutral': 0.3, 'calm': 0.2
        }
        
        return intensity_map.get(emotional_tone, 0.5)
    
    def _get_emotional_valence(self, thought: Dict) -> float:
        """Calculate emotional valence (-1 to 1) of a thought"""
        emotional_tone = thought.get('emotional_tone', 'neutral')
        
        # Mapping of emotions to valence
        valence_map = {
            'joy': 0.8, 'excitement': 0.7, 'love': 0.9,
            'calm': 0.3, 'neutral': 0.0,
            'fear': -0.6, 'anger': -0.7, 'sadness': -0.8,
            'surprise': 0.1, 'disgust': -0.6
        }
        
        return valence_map.get(emotional_tone, 0.0)
        
    async def create_associations(self, thoughts: List[Dict]):
        """Create associative links between related memories"""
        # TODO: Implement association creation logic
        # This would involve finding semantic similarities and creating links
        pass
        
    async def prune_memories(self):
        """Remove redundant or low-value memories"""
        # TODO: Implement memory pruning logic
        # Keep working memory size manageable
        max_working_memory = 1000
        if len(self.working_memory['recent_thoughts']) > max_working_memory:
            # Keep only the most recent
            self.working_memory['recent_thoughts'] = \
                self.working_memory['recent_thoughts'][-max_working_memory:]
                
    async def update_context(self, key: str, value: Any):
        """Update active context"""
        if self.use_database and self.db_manager:
            try:
                # Store in Redis with context prefix
                await self.db_manager.set_working_memory(
                    f"context:{key}",
                    json.dumps(value) if not isinstance(value, str) else value,
                    ttl=86400  # 24 hours
                )
            except Exception as e:
                logger.error(f"Failed to update context in database: {e}")
        else:
            # Use in-memory storage
            self.working_memory['active_context'][key] = value
        
    async def get_context(self, key: str) -> Any:
        """Get value from active context"""
        if self.use_database and self.db_manager:
            try:
                # Get from Redis
                value = await self.db_manager.get_working_memory(f"context:{key}")
                if value:
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
            except Exception as e:
                logger.error(f"Failed to get context from database: {e}")
        
        # Use in-memory storage
        return self.working_memory.get('active_context', {}).get(key)
        
    async def clear_working_memory(self):
        """Clear working memory (useful for resets)"""
        if self.use_database and self.db_manager:
            try:
                # Clear Redis keys with our prefixes
                # Note: This is a simplified version - in production you'd want
                # to use SCAN to avoid blocking
                logger.warning("Database working memory clearing not fully implemented")
            except Exception as e:
                logger.error(f"Failed to clear database working memory: {e}")
        else:
            # Clear in-memory storage
            self.working_memory['recent_thoughts'] = []
            self.working_memory['short_term'] = {}
        
        logger.info("Working memory cleared")
    
    async def close(self):
        """Close database connections gracefully"""
        if self.use_database and self.db_manager:
            await self.db_manager.close()


class SimpleVectorStore:
    """Simple vector store for semantic similarity search"""
    
    def __init__(self):
        self.vectors = {}
        self.metadata = {}
        
    async def initialize(self):
        """Initialize the vector store"""
        logger.info("Vector store initialized")
        
    async def add(self, id: str, vector: List[float], metadata: Dict):
        """Add a vector with metadata"""
        self.vectors[id] = np.array(vector)
        self.metadata[id] = metadata
        
    async def search(self, query_vector: List[float], k: int = 5) -> List[str]:
        """Search for k most similar vectors"""
        if not self.vectors:
            return []
            
        query_vec = np.array(query_vector)
        similarities = []
        
        for id, vector in self.vectors.items():
            # Cosine similarity
            similarity = np.dot(query_vec, vector) / (
                np.linalg.norm(query_vec) * np.linalg.norm(vector)
            )
            similarities.append((similarity, id))
            
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [id for _, id in similarities[:k]]