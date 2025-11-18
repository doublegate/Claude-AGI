"""
Semantic Index for Claude-AGI
==============================

Handles semantic search and vector similarity using FAISS and embeddings.
Extracted from MemoryManager to follow Single Responsibility Principle.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

logger = logging.getLogger(__name__)


class SemanticIndex:
    """
    Manages semantic search using vector embeddings

    Responsibilities:
    - Generate embeddings for content
    - Perform similarity search
    - Manage FAISS index (if available)
    - Provide fallback simple vector store
    """

    def __init__(self, embedder=None, use_faiss: bool = False):
        """
        Initialize semantic index

        Args:
            embedder: Sentence transformer for generating embeddings
            use_faiss: Whether to use FAISS for efficient similarity search
        """
        self.embedder = embedder
        self.use_faiss = use_faiss and HAS_NUMPY

        # Simple vector store (fallback)
        self.simple_store = SimpleVectorStore()

        # FAISS index (if available)
        self.faiss_index = None
        self.faiss_id_map: Dict[int, str] = {}  # Maps FAISS index to memory IDs

        if self.use_faiss:
            try:
                import faiss
                self.faiss = faiss
                logger.info("FAISS available for semantic search")
            except ImportError:
                logger.warning("FAISS not available, using simple vector store")
                self.use_faiss = False

    async def initialize(self):
        """Initialize the semantic index"""
        await self.simple_store.initialize()

        if self.use_faiss and self.embedder:
            # Initialize FAISS index with appropriate dimensionality
            # For all-MiniLM-L6-v2, dimensionality is 384
            dimension = 384
            self.faiss_index = self.faiss.IndexFlatL2(dimension)
            logger.info(f"Initialized FAISS index with dimension {dimension}")

    async def add(self, memory_id: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """
        Add content to semantic index

        Args:
            memory_id: Unique identifier for this memory
            content: Text content to index
            metadata: Additional metadata to store

        Returns:
            True if successfully added
        """
        if not content:
            return False

        # Generate embedding
        embedding = await self._generate_embedding(content)
        if embedding is None:
            return False

        # Add to FAISS index
        if self.use_faiss and self.faiss_index is not None:
            try:
                # Convert to numpy array and add to index
                vector = np.array([embedding], dtype=np.float32)
                idx = self.faiss_index.ntotal
                self.faiss_index.add(vector)
                self.faiss_id_map[idx] = memory_id

                logger.debug(f"Added memory {memory_id} to FAISS index")
                return True

            except Exception as e:
                logger.error(f"Failed to add to FAISS index: {e}")
                # Fall through to simple store

        # Add to simple vector store
        await self.simple_store.add(memory_id, embedding, metadata or {})
        return True

    async def search(self, query: str, k: int = 5, threshold: float = 0.0) -> List[Tuple[str, float]]:
        """
        Search for similar content

        Args:
            query: Query text
            k: Number of results to return
            threshold: Minimum similarity threshold (0.0-1.0)

        Returns:
            List of (memory_id, similarity_score) tuples
        """
        # Generate query embedding
        query_embedding = await self._generate_embedding(query)
        if query_embedding is None:
            return []

        # Search FAISS index
        if self.use_faiss and self.faiss_index is not None and self.faiss_index.ntotal > 0:
            try:
                query_vector = np.array([query_embedding], dtype=np.float32)
                distances, indices = self.faiss_index.search(query_vector, k)

                # Convert distances to similarity scores (cosine similarity approximation)
                # FAISS L2 distance to similarity: similarity = 1 / (1 + distance)
                results = []
                for dist, idx in zip(distances[0], indices[0]):
                    if idx != -1 and idx in self.faiss_id_map:
                        similarity = 1.0 / (1.0 + float(dist))
                        if similarity >= threshold:
                            results.append((self.faiss_id_map[idx], similarity))

                logger.debug(f"FAISS search returned {len(results)} results")
                return results

            except Exception as e:
                logger.error(f"FAISS search failed: {e}")
                # Fall through to simple store

        # Use simple vector store
        memory_ids = await self.simple_store.search(query_embedding, k)

        # Calculate similarities for simple store results
        results = []
        for memory_id in memory_ids:
            # For simple store, we don't have pre-calculated similarities
            # Return with a default similarity score
            results.append((memory_id, 0.5))  # Placeholder similarity

        return results

    async def calculate_similarity(self, content_a: str, content_b: str) -> float:
        """
        Calculate semantic similarity between two pieces of content

        Args:
            content_a: First content
            content_b: Second content

        Returns:
            Similarity score (0.0-1.0)
        """
        if not content_a or not content_b:
            return 0.0

        # Generate embeddings
        embedding_a = await self._generate_embedding(content_a)
        embedding_b = await self._generate_embedding(content_b)

        if embedding_a is None or embedding_b is None:
            return 0.0

        # Calculate cosine similarity
        if HAS_NUMPY:
            vec_a = np.array(embedding_a)
            vec_b = np.array(embedding_b)

            # Cosine similarity
            dot_product = np.dot(vec_a, vec_b)
            norm_a = np.linalg.norm(vec_a)
            norm_b = np.linalg.norm(vec_b)

            if norm_a == 0 or norm_b == 0:
                return 0.0

            similarity = dot_product / (norm_a * norm_b)
            return float(max(0.0, min(1.0, similarity)))  # Clamp to [0, 1]
        else:
            # Fallback without numpy
            return 0.5  # Placeholder

    async def _generate_embedding(self, content: str) -> Optional[List[float]]:
        """
        Generate embedding for content

        Args:
            content: Text content

        Returns:
            Embedding vector or None if failed
        """
        if not self.embedder or not content:
            return None

        try:
            embedding = self.embedder.encode(content)
            return embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None

    async def remove(self, memory_id: str) -> bool:
        """
        Remove a memory from the index

        Args:
            memory_id: Memory identifier to remove

        Returns:
            True if successfully removed
        """
        # FAISS doesn't support efficient removal, so we'd need to rebuild the index
        # For now, just remove from simple store
        # In production, this would require index rebuilding or using a different structure

        # Remove from simple store
        if memory_id in self.simple_store.vectors:
            del self.simple_store.vectors[memory_id]
            del self.simple_store.metadata[memory_id]
            return True

        return False

    async def get_statistics(self) -> Dict[str, Any]:
        """Get semantic index statistics"""
        stats = {
            'has_embedder': self.embedder is not None,
            'using_faiss': self.use_faiss,
            'simple_store_size': len(self.simple_store.vectors) if hasattr(self.simple_store, 'vectors') else 0
        }

        if self.use_faiss and self.faiss_index is not None:
            stats['faiss_index_size'] = self.faiss_index.ntotal

        return stats


class SimpleVectorStore:
    """
    Simple in-memory vector store (fallback when FAISS unavailable)

    This is a basic implementation for development and testing.
    Production use should prefer FAISS for efficiency.
    """

    def __init__(self):
        """Initialize simple vector store"""
        self.vectors: Dict[str, List[float]] = {}
        self.metadata: Dict[str, Dict] = {}

    async def initialize(self):
        """Initialize the store"""
        pass  # No initialization needed for simple store

    async def add(self, id: str, vector: List[float], metadata: Dict):
        """
        Add a vector to the store

        Args:
            id: Unique identifier
            vector: Embedding vector
            metadata: Associated metadata
        """
        self.vectors[id] = vector
        self.metadata[id] = metadata

    async def search(self, query_vector: List[float], k: int = 5) -> List[str]:
        """
        Search for similar vectors

        Args:
            query_vector: Query embedding
            k: Number of results

        Returns:
            List of memory IDs
        """
        if not self.vectors:
            return []

        # Calculate similarity scores (simple dot product)
        scores = []
        for memory_id, vector in self.vectors.items():
            # Simple dot product similarity
            if len(vector) == len(query_vector):
                score = sum(a * b for a, b in zip(query_vector, vector))
                scores.append((memory_id, score))

        # Sort by score (descending)
        scores.sort(key=lambda x: x[1], reverse=True)

        # Return top k IDs
        return [memory_id for memory_id, _ in scores[:k]]
