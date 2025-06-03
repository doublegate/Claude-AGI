# memory/manager.py

from typing import Dict, List, Optional, Any
import asyncio
import json
import uuid
from datetime import datetime, timedelta
import logging
import numpy as np

# Simplified imports for initial implementation
# redis and asyncpg will be mocked until properly configured

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manages short-term, long-term, and semantic memory"""
    
    def __init__(self):
        self.redis_client = None  # Short-term memory
        self.postgres_pool = None  # Long-term memory
        self.vector_store = None   # Semantic memory
        self.working_memory = {}   # Simple dict for now
        self.long_term_memory = []  # Simple list for now
        
    @classmethod
    async def create(cls):
        """Factory method to create and initialize MemoryManager"""
        instance = cls()
        await instance.initialize()
        return instance
        
    async def initialize(self):
        """Initialize memory stores"""
        # For initial implementation, use in-memory stores
        # TODO: Integrate actual Redis and PostgreSQL when configured
        
        logger.info("Initializing memory stores...")
        
        # Initialize working memory
        self.working_memory = {
            'recent_thoughts': [],
            'active_context': {},
            'short_term': {}
        }
        
        # Initialize vector store for semantic search
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
        if 'embedding' in thought:
            await self.vector_store.add(
                thought_id,
                thought['embedding'],
                enriched_thought
            )
            
        logger.debug(f"Stored thought {thought_id}")
        return thought_id
        
    async def recall_recent(self, n: int = 10) -> List[Dict]:
        """Recall n most recent thoughts"""
        recent = self.working_memory['recent_thoughts'][-n:]
        return list(reversed(recent))
        
    async def recall_by_id(self, thought_id: str) -> Optional[Dict]:
        """Recall a specific thought by ID"""
        # Check working memory first
        if thought_id in self.working_memory['short_term']:
            return self.working_memory['short_term'][thought_id]
            
        # Check long-term memory
        for thought in self.long_term_memory:
            if thought['id'] == thought_id:
                return thought
                
        return None
        
    async def recall_similar(self, query: str, k: int = 5) -> List[Dict]:
        """Recall memories similar to query"""
        # For now, simple keyword matching
        # TODO: Implement proper embedding-based search
        
        query_lower = query.lower()
        scored_memories = []
        
        # Search in all memories
        all_memories = (
            self.working_memory['recent_thoughts'] + 
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
        recent_thoughts = self.working_memory['recent_thoughts'][-100:]
        
        # Identify important memories based on various factors
        important_memories = await self.identify_important_memories(recent_thoughts)
        
        # Strengthen important memories by moving to long-term
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
        self.working_memory['active_context'][key] = value
        
    async def get_context(self, key: str) -> Any:
        """Get value from active context"""
        return self.working_memory['active_context'].get(key)
        
    async def clear_working_memory(self):
        """Clear working memory (useful for resets)"""
        self.working_memory['recent_thoughts'] = []
        self.working_memory['short_term'] = {}
        logger.info("Working memory cleared")


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