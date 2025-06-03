"""
Database connection managers for Claude-AGI
==========================================

Provides connection management for:
- PostgreSQL: Long-term episodic memory storage
- Redis: Working memory and short-term cache
- FAISS: Vector similarity search for semantic memory
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import asyncpg
import redis.asyncio as redis
import numpy as np
import faiss
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, JSON, Index
from datetime import datetime
import json

logger = logging.getLogger(__name__)

Base = declarative_base()


class DatabaseConfig:
    """Database configuration from environment variables"""
    
    def __init__(self):
        self.postgres_url = os.getenv(
            'POSTGRES_URL',
            'postgresql+asyncpg://claude_agi:password@localhost:5432/claude_consciousness'
        )
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.faiss_index_path = os.getenv('FAISS_INDEX_PATH', './data/faiss_index.bin')
        self.faiss_dimension = int(os.getenv('FAISS_DIMENSION', '768'))  # For sentence-transformers


class Memory(Base):
    """SQLAlchemy model for episodic memories"""
    __tablename__ = 'memories'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    memory_type = Column(String(50), nullable=False)  # episodic, semantic, procedural
    content = Column(Text, nullable=False)
    embedding = Column(JSON)  # Store as JSON array for simplicity
    emotional_valence = Column(Float, default=0.0)  # -1 to 1
    importance = Column(Float, default=0.5)  # 0 to 1
    context = Column(JSON)  # Additional metadata
    associations = Column(JSON)  # Links to other memory IDs
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_timestamp', 'timestamp'),
        Index('idx_memory_type', 'memory_type'),
        Index('idx_importance', 'importance'),
    )


class Thought(Base):
    """SQLAlchemy model for consciousness stream thoughts"""
    __tablename__ = 'thoughts'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    stream_type = Column(String(50), nullable=False)  # primary, subconscious, etc.
    content = Column(Text, nullable=False)
    emotional_state = Column(JSON)  # Complex emotional state
    context = Column(JSON)  # Environmental and cognitive context
    memory_references = Column(JSON)  # IDs of related memories
    
    __table_args__ = (
        Index('idx_thought_timestamp', 'timestamp'),
        Index('idx_stream_type', 'stream_type'),
    )


class DatabaseManager:
    """Manages all database connections for Claude-AGI"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self.engine = None
        self.async_session = None
        self.redis_client = None
        self.faiss_index = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize all database connections"""
        if self._initialized:
            return
            
        try:
            # PostgreSQL setup
            self.engine = create_async_engine(
                self.config.postgres_url,
                echo=False,
                pool_size=20,
                max_overflow=40,
                pool_pre_ping=True
            )
            
            # Create tables if they don't exist
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            # Create session factory
            self.async_session = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Redis setup
            self.redis_client = await redis.from_url(
                self.config.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50
            )
            
            # Test Redis connection
            await self.redis_client.ping()
            
            # FAISS setup
            self._initialize_faiss()
            
            self._initialized = True
            logger.info("All database connections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            raise
    
    def _initialize_faiss(self):
        """Initialize or load FAISS index"""
        index_path = self.config.faiss_index_path
        
        if os.path.exists(index_path):
            # Load existing index
            self.faiss_index = faiss.read_index(index_path)
            logger.info(f"Loaded FAISS index from {index_path}")
        else:
            # Create new index
            # Using IndexFlatIP for inner product (cosine similarity with normalized vectors)
            self.faiss_index = faiss.IndexFlatIP(self.config.faiss_dimension)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(index_path), exist_ok=True)
            logger.info(f"Created new FAISS index with dimension {self.config.faiss_dimension}")
    
    async def close(self):
        """Close all database connections"""
        if self.engine:
            await self.engine.dispose()
        
        if self.redis_client:
            await self.redis_client.close()
        
        # Save FAISS index
        if self.faiss_index and self.faiss_index.ntotal > 0:
            faiss.write_index(self.faiss_index, self.config.faiss_index_path)
            logger.info(f"Saved FAISS index with {self.faiss_index.ntotal} vectors")
        
        self._initialized = False
    
    @asynccontextmanager
    async def get_session(self):
        """Get PostgreSQL session context manager"""
        if not self._initialized:
            await self.initialize()
            
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def store_memory(self, memory_data: Dict[str, Any]) -> int:
        """Store a memory in PostgreSQL and optionally index in FAISS"""
        async with self.get_session() as session:
            memory = Memory(
                memory_type=memory_data['memory_type'],
                content=memory_data['content'],
                embedding=memory_data.get('embedding'),
                emotional_valence=memory_data.get('emotional_valence', 0.0),
                importance=memory_data.get('importance', 0.5),
                context=memory_data.get('context', {}),
                associations=memory_data.get('associations', [])
            )
            session.add(memory)
            await session.flush()
            memory_id = memory.id
            
            # Index in FAISS if embedding provided
            if memory_data.get('embedding'):
                embedding_array = np.array(memory_data['embedding'], dtype=np.float32)
                embedding_array = embedding_array.reshape(1, -1)
                
                # Normalize for cosine similarity
                faiss.normalize_L2(embedding_array)
                
                # Add to index with ID
                self.faiss_index.add_with_ids(embedding_array, np.array([memory_id]))
            
            return memory_id
    
    async def search_similar_memories(self, embedding: List[float], k: int = 5) -> List[Dict]:
        """Search for similar memories using FAISS"""
        if self.faiss_index.ntotal == 0:
            return []
        
        # Prepare query embedding
        query_embedding = np.array(embedding, dtype=np.float32).reshape(1, -1)
        faiss.normalize_L2(query_embedding)
        
        # Search
        distances, indices = self.faiss_index.search(query_embedding, min(k, self.faiss_index.ntotal))
        
        # Fetch memory details from PostgreSQL
        memory_ids = [int(idx) for idx in indices[0] if idx != -1]
        if not memory_ids:
            return []
        
        async with self.get_session() as session:
            result = await session.execute(
                "SELECT * FROM memories WHERE id = ANY(:ids)",
                {"ids": memory_ids}
            )
            memories = result.fetchall()
            
            # Convert to dicts with similarity scores
            memory_dicts = []
            for memory, distance in zip(memories, distances[0]):
                if memory:
                    memory_dict = dict(memory._mapping)
                    memory_dict['similarity_score'] = float(distance)
                    memory_dicts.append(memory_dict)
            
            return memory_dicts
    
    async def get_working_memory(self, key: str) -> Optional[str]:
        """Get value from Redis working memory"""
        return await self.redis_client.get(f"working_memory:{key}")
    
    async def set_working_memory(self, key: str, value: str, ttl: int = 86400):
        """Set value in Redis working memory with TTL (default 24 hours)"""
        await self.redis_client.setex(f"working_memory:{key}", ttl, value)
    
    async def get_recent_thoughts(self, stream_type: str, limit: int = 10) -> List[Dict]:
        """Get recent thoughts from Redis cache"""
        thoughts = await self.redis_client.lrange(f"thoughts:{stream_type}", 0, limit - 1)
        return [json.loads(thought) for thought in thoughts]
    
    async def add_thought(self, stream_type: str, thought_data: Dict[str, Any]):
        """Add thought to Redis and PostgreSQL"""
        # Add to Redis for quick access
        await self.redis_client.lpush(
            f"thoughts:{stream_type}",
            json.dumps(thought_data)
        )
        
        # Trim to keep only recent thoughts in Redis
        await self.redis_client.ltrim(f"thoughts:{stream_type}", 0, 99)
        
        # Store in PostgreSQL for persistence
        async with self.get_session() as session:
            thought = Thought(
                stream_type=stream_type,
                content=thought_data['content'],
                emotional_state=thought_data.get('emotional_state'),
                context=thought_data.get('context'),
                memory_references=thought_data.get('memory_references', [])
            )
            session.add(thought)


# Singleton instance
_db_manager: Optional[DatabaseManager] = None


async def get_db_manager() -> DatabaseManager:
    """Get or create the database manager singleton"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        await _db_manager.initialize()
    return _db_manager