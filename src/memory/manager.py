# memory/manager.py

from typing import Dict, List, Optional, Any
import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
import logging
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

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
from ..database.models import MemoryData, MemoryType, ThoughtData, StreamType, EmotionalState

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manages short-term, long-term, and semantic memory"""
    
    def __init__(self):
        self.db_manager: Optional[DatabaseManager] = None
        self.embedder: Optional[SentenceTransformer] = None
        self.use_database = False  # Flag to enable database integration
        self.message_queue = asyncio.Queue()  # For receiving messages
        
    @classmethod
    async def create(cls):
        """Factory method to create and initialize MemoryManager"""
        instance = cls()
        await instance.initialize()
        return instance
        
    async def initialize(self, use_database: bool = False):
        """Initialize memory stores"""
        logger.info("Initializing memory stores...")
        
        # Check if database components are available
        if not HAS_DATABASE:
            logger.warning("Database dependencies not available, using in-memory storage only")
            use_database = False
        
        self.use_database = use_database
        
        if use_database and HAS_DATABASE:
            # Initialize database connections
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
                
                # Query PostgreSQL for older thoughts
                try:
                    async with self.db_manager.get_connection() as conn:
                        async with conn.cursor() as cursor:
                            await cursor.execute(
                                "SELECT content, metadata FROM thoughts WHERE id = %s", 
                                (thought_id,)
                            )
                            result = await cursor.fetchone()
                            if result:
                                content, metadata = result
                                return {
                                    'id': thought_id,
                                    'content': content,
                                    'metadata': json.loads(metadata) if metadata else {},
                                    'source': 'postgresql'
                                }
                except Exception as db_error:
                    logger.error(f"PostgreSQL query failed: {db_error}")
                    # Continue to in-memory fallback
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
        logger.debug(f"Creating associations for {len(thoughts)} thoughts")
        
        if len(thoughts) < 2:
            return  # Need at least 2 thoughts to create associations
        
        for i, thought_a in enumerate(thoughts):
            for j, thought_b in enumerate(thoughts[i+1:], i+1):
                # Calculate semantic similarity
                similarity = await self._calculate_semantic_similarity(thought_a, thought_b)
                
                if similarity > 0.6:  # High similarity threshold
                    # Create bidirectional association
                    await self._create_bidirectional_link(thought_a, thought_b, similarity)
        
        logger.debug("Association creation completed")
    
    async def _calculate_semantic_similarity(self, thought_a: Dict, thought_b: Dict) -> float:
        """Calculate semantic similarity between two thoughts"""
        content_a = thought_a.get('content', '').lower()
        content_b = thought_b.get('content', '').lower()
        
        if not content_a or not content_b:
            return 0.0
        
        # Simple word overlap similarity (in production, use embeddings)
        words_a = set(content_a.split())
        words_b = set(content_b.split())
        
        intersection = words_a.intersection(words_b)
        union = words_a.union(words_b)
        
        if not union:
            return 0.0
        
        jaccard_similarity = len(intersection) / len(union)
        
        # Boost similarity for similar emotional tones
        tone_a = thought_a.get('emotional_tone', 'neutral')
        tone_b = thought_b.get('emotional_tone', 'neutral')
        
        emotional_boost = 0.1 if tone_a == tone_b else 0.0
        
        # Boost similarity for similar stream types
        stream_a = thought_a.get('stream_type', 'primary')
        stream_b = thought_b.get('stream_type', 'primary')
        
        stream_boost = 0.1 if stream_a == stream_b else 0.0
        
        return jaccard_similarity + emotional_boost + stream_boost
    
    async def _create_bidirectional_link(self, thought_a: Dict, thought_b: Dict, similarity: float):
        """Create bidirectional associative link between thoughts"""
        id_a = thought_a.get('id')
        id_b = thought_b.get('id')
        
        if not id_a or not id_b:
            return
        
        # Add association to thought A
        if 'associations' not in thought_a:
            thought_a['associations'] = []
        
        if id_b not in thought_a['associations']:
            thought_a['associations'].append({
                'thought_id': id_b,
                'similarity': similarity,
                'association_type': 'semantic'
            })
        
        # Add association to thought B
        if 'associations' not in thought_b:
            thought_b['associations'] = []
        
        if id_a not in thought_b['associations']:
            thought_b['associations'].append({
                'thought_id': id_a,
                'similarity': similarity,
                'association_type': 'semantic'
            })
        
        # Store associations in persistent memory if database is available
        if self.db_manager:
            try:
                await self.db_manager.set_working_memory(f"associations:{id_a}", json.dumps(thought_a.get('associations', [])))
                await self.db_manager.set_working_memory(f"associations:{id_b}", json.dumps(thought_b.get('associations', [])))
            except Exception as e:
                logger.error(f"Failed to store associations: {e}")
        
    async def prune_memories(self):
        """Remove redundant or low-value memories"""
        logger.debug("Starting memory pruning process")
        
        # Keep working memory size manageable
        max_working_memory = 1000
        pruned_count = 0
        
        if len(self.working_memory['recent_thoughts']) > max_working_memory:
            # Sort by importance and recency
            sorted_thoughts = sorted(
                self.working_memory['recent_thoughts'], 
                key=lambda t: (
                    t.get('importance', 0.5) * 0.6 +  # Importance weight
                    (time.time() - t.get('timestamp', 0)) / 86400 * 0.4  # Recency weight (days ago)
                ),
                reverse=True
            )
            
            # Keep the most important/recent thoughts
            thoughts_to_keep = sorted_thoughts[:max_working_memory // 2]  # Keep top 50%
            thoughts_to_archive = sorted_thoughts[max_working_memory // 2:]
            
            # Archive low-value thoughts to long-term memory
            for thought in thoughts_to_archive:
                if thought.get('importance', 0.5) > 0.3:  # Don't discard moderately important thoughts
                    await self._archive_to_long_term(thought)
                pruned_count += 1
            
            self.working_memory['recent_thoughts'] = thoughts_to_keep
            
        # Prune short-term memory
        max_short_term = 500
        if len(self.working_memory['short_term']) > max_short_term:
            # Remove oldest entries
            items = list(self.working_memory['short_term'].items())
            items.sort(key=lambda x: x[1].get('timestamp', 0))  # Sort by timestamp
            
            items_to_keep = items[-max_short_term // 2:]  # Keep newest 50%
            items_to_remove = items[:-max_short_term // 2]
            
            # Archive important short-term memories
            for key, item in items_to_remove:
                if item.get('importance', 0.5) > 0.4:
                    await self._archive_to_long_term(item)
                pruned_count += 1
            
            self.working_memory['short_term'] = dict(items_to_keep)
        
        # Remove duplicate or highly similar memories
        await self._remove_duplicate_memories()
        
        # Consolidate related memories
        await self._consolidate_related_memories()
        
        logger.info(f"Memory pruning completed. Pruned {pruned_count} memories")
    
    async def _archive_to_long_term(self, memory: Dict):
        """Archive memory to long-term storage"""
        try:
            memory_id = memory.get('id', f"archived_{int(time.time())}")
            
            # Add archival metadata
            memory['archived_at'] = time.time()
            memory['archive_reason'] = 'working_memory_pruning'
            
            # Store in long-term memory
            if memory_id not in self.working_memory['long_term']:
                self.working_memory['long_term'][memory_id] = memory
                
                # If database is available, persist
                if self.db_manager:
                    await self.db_manager.set_episodic_memory(memory_id, json.dumps(memory))
                    
        except Exception as e:
            logger.error(f"Failed to archive memory: {e}")
    
    async def _remove_duplicate_memories(self):
        """Remove duplicate or highly similar memories"""
        thoughts = self.working_memory['recent_thoughts']
        unique_thoughts = []
        removed_count = 0
        
        for thought in thoughts:
            is_duplicate = False
            
            for unique_thought in unique_thoughts:
                similarity = await self._calculate_semantic_similarity(thought, unique_thought)
                
                if similarity > 0.9:  # Very high similarity - likely duplicate
                    # Keep the one with higher importance or more recent
                    import time as time_module
                    thought_score = (
                        thought.get('importance', 0.5) * 0.7 + 
                        (thought.get('timestamp', 0) / time_module.time()) * 0.3
                    )
                    unique_score = (
                        unique_thought.get('importance', 0.5) * 0.7 + 
                        (unique_thought.get('timestamp', 0) / time_module.time()) * 0.3
                    )
                    
                    if thought_score <= unique_score:
                        is_duplicate = True
                        removed_count += 1
                        break
                    else:
                        # Replace the unique thought with this better one
                        unique_thoughts.remove(unique_thought)
                        break
            
            if not is_duplicate:
                unique_thoughts.append(thought)
        
        self.working_memory['recent_thoughts'] = unique_thoughts
        
        if removed_count > 0:
            logger.debug(f"Removed {removed_count} duplicate memories")
    
    async def _consolidate_related_memories(self):
        """Consolidate related memories to reduce redundancy"""
        thoughts = self.working_memory['recent_thoughts']
        consolidated_groups = []
        processed_indices = set()
        
        for i, thought in enumerate(thoughts):
            if i in processed_indices:
                continue
                
            # Find related thoughts
            related_group = [thought]
            processed_indices.add(i)
            
            for j, other_thought in enumerate(thoughts):
                if j <= i or j in processed_indices:
                    continue
                    
                similarity = await self._calculate_semantic_similarity(thought, other_thought)
                
                if similarity > 0.7:  # High similarity - can be consolidated
                    related_group.append(other_thought)
                    processed_indices.add(j)
            
            if len(related_group) > 1:
                # Consolidate group into single memory
                consolidated = await self._merge_related_thoughts(related_group)
                consolidated_groups.append(consolidated)
            else:
                consolidated_groups.append(thought)
        
        # Only update if we actually consolidated something
        if len(consolidated_groups) < len(thoughts):
            self.working_memory['recent_thoughts'] = consolidated_groups
            consolidated_count = len(thoughts) - len(consolidated_groups)
            logger.debug(f"Consolidated {consolidated_count} related memories")
    
    async def _merge_related_thoughts(self, thoughts: List[Dict]) -> Dict:
        """Merge multiple related thoughts into a consolidated memory"""
        if not thoughts:
            return {}
        
        # Use the most important/recent thought as base
        base_thought = max(thoughts, key=lambda t: (
            t.get('importance', 0.5) * 0.6 + 
            (t.get('timestamp', 0) / time.time()) * 0.4
        ))
        
        # Merge content
        all_content = [t.get('content', '') for t in thoughts if t.get('content')]
        consolidated_content = f"{base_thought.get('content', '')} [Consolidated with: {'; '.join(all_content[1:])}]"
        
        # Average numerical properties
        avg_importance = sum(t.get('importance', 0.5) for t in thoughts) / len(thoughts)
        avg_emotional_valence = sum(t.get('emotional_valence', 0.0) for t in thoughts) / len(thoughts)
        
        # Merge associations
        all_associations = []
        for t in thoughts:
            all_associations.extend(t.get('associations', []))
        
        # Remove duplicates
        unique_associations = []
        seen = set()
        for assoc in all_associations:
            if isinstance(assoc, dict):
                key = assoc.get('thought_id')
            else:
                key = assoc
            if key not in seen:
                unique_associations.append(assoc)
                seen.add(key)
        
        consolidated = base_thought.copy()
        consolidated.update({
            'content': consolidated_content,
            'importance': min(1.0, avg_importance * 1.1),  # Slight boost for consolidated memories
            'emotional_valence': avg_emotional_valence,
            'associations': unique_associations,
            'consolidated_from': [t.get('id') for t in thoughts if t.get('id')],
            'consolidation_timestamp': time.time()
        })
        
        return consolidated
                
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
            
    async def handle_message(self, message):
        """Handle incoming messages from orchestrator"""
        message_type = message.type
        
        if message_type == 'store_thought':
            await self.store_thought(message.content)
        elif message_type == 'recall':
            # Handle memory recall requests
            query = message.content.get('query', '')
            memories = await self.recall_similar(query)
            # Send response back through orchestrator
            # For now, just log it
            logger.info(f"Recalled {len(memories)} memories for query: {query}")
        elif message_type == 'consolidate':
            await self.consolidate_memories()
        else:
            logger.debug(f"Memory manager received unknown message type: {message_type}")
    
    # Alias for orchestrator compatibility
    process_message = handle_message


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