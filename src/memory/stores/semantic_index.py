"""
Semantic Index

Handles vector-based semantic similarity search using FAISS or simple numpy operations.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from datetime import datetime

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    faiss = None

from ...core.service_registry import ServiceRegistry


class SemanticIndex:
    """
    Manages semantic similarity search using vector embeddings.
    
    Features:
    - Vector indexing with FAISS (when available)
    - Fallback numpy-based similarity search
    - Metadata storage alongside vectors
    - Incremental index updates
    - Index persistence and recovery
    """
    
    def __init__(
        self,
        dimension: int = 384,  # Default for all-MiniLM-L6-v2
        index_type: str = "IVF",  # IVF, Flat, HNSW
        nlist: int = 100,  # Number of clusters for IVF
        service_registry: Optional[ServiceRegistry] = None
    ):
        self.dimension = dimension
        self.index_type = index_type
        self.nlist = nlist
        self.service_registry = service_registry
        
        self.logger = logging.getLogger(__name__)
        
        # FAISS index
        self.index = None
        self.use_faiss = HAS_FAISS
        
        # Metadata storage
        self.id_to_idx: Dict[str, int] = {}  # Map memory_id to index position
        self.idx_to_id: Dict[int, str] = {}  # Map index position to memory_id
        self.metadata: Dict[str, Dict[str, Any]] = {}  # Store metadata by memory_id
        
        # Numpy fallback storage
        self.vectors: Dict[str, np.ndarray] = {}
        
        # Metrics
        self._add_count = 0
        self._search_count = 0
        self._index_size = 0
        
    async def initialize(self):
        """Initialize the semantic index"""
        self.logger.info(f"Initializing Semantic Index (dimension={self.dimension})")
        
        if self.use_faiss:
            try:
                # Create FAISS index based on type
                if self.index_type == "Flat":
                    self.index = faiss.IndexFlatL2(self.dimension)
                    
                elif self.index_type == "IVF":
                    # IVF requires training, start with Flat quantizer
                    quantizer = faiss.IndexFlatL2(self.dimension)
                    self.index = faiss.IndexIVFFlat(
                        quantizer,
                        self.dimension,
                        self.nlist
                    )
                    
                elif self.index_type == "HNSW":
                    self.index = faiss.IndexHNSWFlat(self.dimension, 32)
                    
                else:
                    self.logger.warning(f"Unknown index type {self.index_type}, using Flat")
                    self.index = faiss.IndexFlatL2(self.dimension)
                    
                self.logger.info(f"Created FAISS {self.index_type} index")
                
            except Exception as e:
                self.logger.error(f"Failed to create FAISS index: {e}")
                self.use_faiss = False
        
        if not self.use_faiss:
            self.logger.info("Using numpy-based similarity search")
        
        # Register with service registry
        if self.service_registry:
            await self.service_registry.register_service(
                "semantic_index",
                self,
                {
                    "dimension": self.dimension,
                    "index_type": self.index_type,
                    "use_faiss": self.use_faiss
                }
            )
    
    async def shutdown(self):
        """Shutdown the index gracefully"""
        self.logger.info("Shutting down Semantic Index")
        
        # Save index to disk if needed
        # await self.save_index()
        
        # Unregister from service registry
        if self.service_registry:
            await self.service_registry.unregister_service("semantic_index")
    
    async def add_vector(
        self,
        memory_id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a vector to the index.
        
        Args:
            memory_id: Unique identifier for the memory
            vector: Embedding vector
            metadata: Optional metadata to store
            
        Returns:
            bool: Success status
        """
        self._add_count += 1
        
        # Validate vector dimension
        if len(vector) != self.dimension:
            self.logger.error(
                f"Vector dimension mismatch: expected {self.dimension}, got {len(vector)}"
            )
            return False
        
        # Convert to numpy array
        vec_array = np.array(vector, dtype=np.float32)
        
        if self.use_faiss and self.index is not None:
            try:
                # Check if IVF index needs training
                if (self.index_type == "IVF" and 
                    not self.index.is_trained and 
                    self._index_size >= self.nlist):
                    await self._train_ivf_index()
                
                # Add to FAISS index
                idx = self._index_size
                self.index.add(vec_array.reshape(1, -1))
                
                # Update mappings
                self.id_to_idx[memory_id] = idx
                self.idx_to_id[idx] = memory_id
                self._index_size += 1
                
            except Exception as e:
                self.logger.error(f"Failed to add vector to FAISS: {e}")
                self.use_faiss = False
        
        # Always store in numpy fallback (for redundancy or if FAISS fails)
        self.vectors[memory_id] = vec_array
        
        # Store metadata
        if metadata:
            self.metadata[memory_id] = metadata
        
        self.logger.debug(f"Added vector for memory {memory_id}")
        return True
    
    async def add_batch(
        self,
        vectors: List[Tuple[str, List[float], Optional[Dict[str, Any]]]]
    ) -> Dict[str, bool]:
        """
        Add multiple vectors in batch.
        
        Args:
            vectors: List of (memory_id, vector, metadata) tuples
            
        Returns:
            Dict mapping memory_id to success status
        """
        results = {}
        
        # Prepare batch data
        valid_vectors = []
        for memory_id, vector, metadata in vectors:
            if len(vector) == self.dimension:
                valid_vectors.append((memory_id, vector, metadata))
                results[memory_id] = True
            else:
                results[memory_id] = False
                self.logger.warning(f"Skipping {memory_id}: dimension mismatch")
        
        if not valid_vectors:
            return results
        
        # Convert to numpy array for batch processing
        vec_matrix = np.array(
            [vec for _, vec, _ in valid_vectors],
            dtype=np.float32
        )
        
        if self.use_faiss and self.index is not None:
            try:
                # Check if IVF index needs training
                if (self.index_type == "IVF" and 
                    not self.index.is_trained and 
                    self._index_size + len(valid_vectors) >= self.nlist):
                    await self._train_ivf_index()
                
                # Add batch to FAISS
                start_idx = self._index_size
                self.index.add(vec_matrix)
                
                # Update mappings
                for i, (memory_id, _, metadata) in enumerate(valid_vectors):
                    idx = start_idx + i
                    self.id_to_idx[memory_id] = idx
                    self.idx_to_id[idx] = memory_id
                    
                    if metadata:
                        self.metadata[memory_id] = metadata
                
                self._index_size += len(valid_vectors)
                self._add_count += len(valid_vectors)
                
            except Exception as e:
                self.logger.error(f"Failed to add batch to FAISS: {e}")
                # Mark all as failed
                for memory_id, _, _ in valid_vectors:
                    results[memory_id] = False
        
        # Store in numpy fallback
        for memory_id, vector, metadata in valid_vectors:
            self.vectors[memory_id] = np.array(vector, dtype=np.float32)
            if metadata:
                self.metadata[memory_id] = metadata
        
        return results
    
    async def search(
        self,
        query_vector: List[float],
        k: int = 5,
        threshold: Optional[float] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query embedding vector
            k: Number of results to return
            threshold: Optional similarity threshold
            
        Returns:
            List of (memory_id, distance, metadata) tuples
        """
        self._search_count += 1
        
        # Validate query dimension
        if len(query_vector) != self.dimension:
            self.logger.error(
                f"Query dimension mismatch: expected {self.dimension}, got {len(query_vector)}"
            )
            return []
        
        # Convert to numpy array
        query_array = np.array(query_vector, dtype=np.float32)
        
        results = []
        
        if self.use_faiss and self.index is not None and self.index.ntotal > 0:
            try:
                # For IVF index, ensure it's trained
                if self.index_type == "IVF" and not self.index.is_trained:
                    self.logger.warning("IVF index not trained, falling back to numpy")
                else:
                    # Search in FAISS
                    distances, indices = self.index.search(
                        query_array.reshape(1, -1),
                        min(k, self.index.ntotal)
                    )
                    
                    # Convert results
                    for i in range(len(indices[0])):
                        idx = indices[0][i]
                        if idx >= 0:  # Valid index
                            memory_id = self.idx_to_id.get(idx)
                            if memory_id:
                                distance = float(distances[0][i])
                                
                                # Apply threshold if specified
                                if threshold is None or distance <= threshold:
                                    metadata = self.metadata.get(memory_id, {})
                                    results.append((memory_id, distance, metadata))
                    
                    return results
                    
            except Exception as e:
                self.logger.error(f"FAISS search failed: {e}")
        
        # Fallback to numpy search
        if self.vectors:
            similarities = []
            
            for memory_id, vector in self.vectors.items():
                # Compute L2 distance
                distance = np.linalg.norm(query_array - vector)
                
                # Apply threshold if specified
                if threshold is None or distance <= threshold:
                    metadata = self.metadata.get(memory_id, {})
                    similarities.append((memory_id, distance, metadata))
            
            # Sort by distance (ascending) and return top k
            similarities.sort(key=lambda x: x[1])
            results = similarities[:k]
        
        return results
    
    async def search_by_similarity(
        self,
        query_vector: List[float],
        k: int = 5,
        min_similarity: float = 0.0
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search using cosine similarity instead of L2 distance.
        
        Args:
            query_vector: Query embedding vector
            k: Number of results to return
            min_similarity: Minimum cosine similarity (0-1)
            
        Returns:
            List of (memory_id, similarity, metadata) tuples
        """
        # Convert to numpy array and normalize
        query_array = np.array(query_vector, dtype=np.float32)
        query_norm = query_array / (np.linalg.norm(query_array) + 1e-8)
        
        results = []
        
        # Always use numpy for cosine similarity
        if self.vectors:
            similarities = []
            
            for memory_id, vector in self.vectors.items():
                # Normalize stored vector
                vec_norm = vector / (np.linalg.norm(vector) + 1e-8)
                
                # Compute cosine similarity
                similarity = float(np.dot(query_norm, vec_norm))
                
                # Apply threshold
                if similarity >= min_similarity:
                    metadata = self.metadata.get(memory_id, {})
                    similarities.append((memory_id, similarity, metadata))
            
            # Sort by similarity (descending) and return top k
            similarities.sort(key=lambda x: x[1], reverse=True)
            results = similarities[:k]
        
        return results
    
    async def remove_vector(self, memory_id: str) -> bool:
        """
        Remove a vector from the index.
        
        Note: FAISS doesn't support removal, so we track deleted IDs.
        
        Args:
            memory_id: Memory ID to remove
            
        Returns:
            bool: Success status
        """
        # Remove from numpy storage
        if memory_id in self.vectors:
            del self.vectors[memory_id]
        
        # Remove metadata
        if memory_id in self.metadata:
            del self.metadata[memory_id]
        
        # Mark as deleted in FAISS mappings (can't actually remove from index)
        if memory_id in self.id_to_idx:
            idx = self.id_to_idx[memory_id]
            del self.id_to_idx[memory_id]
            del self.idx_to_id[idx]
        
        return True
    
    async def update_vector(
        self,
        memory_id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a vector (remove and re-add).
        
        Args:
            memory_id: Memory ID to update
            vector: New embedding vector
            metadata: Optional new metadata
            
        Returns:
            bool: Success status
        """
        # Remove old vector
        await self.remove_vector(memory_id)
        
        # Add new vector
        return await self.add_vector(memory_id, vector, metadata)
    
    async def save_index(self, path: str) -> bool:
        """
        Save index to disk.
        
        Args:
            path: File path to save to
            
        Returns:
            bool: Success status
        """
        try:
            # Save FAISS index if available
            if self.use_faiss and self.index is not None:
                faiss.write_index(self.index, f"{path}.faiss")
            
            # Save mappings and metadata
            save_data = {
                "dimension": self.dimension,
                "index_type": self.index_type,
                "id_to_idx": self.id_to_idx,
                "idx_to_id": {str(k): v for k, v in self.idx_to_id.items()},
                "metadata": self.metadata,
                "vectors": {k: v.tolist() for k, v in self.vectors.items()},
                "index_size": self._index_size
            }
            
            with open(f"{path}.json", "w") as f:
                json.dump(save_data, f)
            
            self.logger.info(f"Saved index to {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save index: {e}")
            return False
    
    async def load_index(self, path: str) -> bool:
        """
        Load index from disk.
        
        Args:
            path: File path to load from
            
        Returns:
            bool: Success status
        """
        try:
            # Load mappings and metadata
            with open(f"{path}.json", "r") as f:
                save_data = json.load(f)
            
            self.dimension = save_data["dimension"]
            self.index_type = save_data["index_type"]
            self.id_to_idx = save_data["id_to_idx"]
            self.idx_to_id = {int(k): v for k, v in save_data["idx_to_id"].items()}
            self.metadata = save_data["metadata"]
            self.vectors = {
                k: np.array(v, dtype=np.float32)
                for k, v in save_data["vectors"].items()
            }
            self._index_size = save_data["index_size"]
            
            # Load FAISS index if available
            if self.use_faiss:
                try:
                    self.index = faiss.read_index(f"{path}.faiss")
                    self.logger.info(f"Loaded FAISS index from {path}")
                except Exception as e:
                    self.logger.warning(f"Could not load FAISS index: {e}")
                    self.use_faiss = False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load index: {e}")
            return False
    
    async def rebuild_index(self) -> bool:
        """
        Rebuild FAISS index from numpy vectors.
        
        Returns:
            bool: Success status
        """
        if not self.use_faiss or not self.vectors:
            return False
        
        try:
            # Reinitialize index
            await self.initialize()
            
            # Re-add all vectors
            vectors_list = [
                (memory_id, vector.tolist(), self.metadata.get(memory_id))
                for memory_id, vector in self.vectors.items()
            ]
            
            await self.add_batch(vectors_list)
            
            self.logger.info("Rebuilt FAISS index")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rebuild index: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get index statistics.
        
        Returns:
            Dict of statistics
        """
        stats = {
            "add_count": self._add_count,
            "search_count": self._search_count,
            "index_size": self._index_size,
            "numpy_vectors": len(self.vectors),
            "dimension": self.dimension,
            "index_type": self.index_type,
            "use_faiss": self.use_faiss
        }
        
        if self.use_faiss and self.index is not None:
            stats["faiss_total"] = self.index.ntotal
            stats["faiss_trained"] = getattr(self.index, "is_trained", True)
        
        return stats
    
    # Private helper methods
    
    async def _train_ivf_index(self):
        """Train IVF index with current vectors"""
        if not self.vectors or len(self.vectors) < self.nlist:
            return
        
        try:
            # Get training vectors
            training_vectors = np.array(
                list(self.vectors.values())[:self.nlist * 10],
                dtype=np.float32
            )
            
            # Train the index
            self.index.train(training_vectors)
            self.logger.info(f"Trained IVF index with {len(training_vectors)} vectors")
            
        except Exception as e:
            self.logger.error(f"Failed to train IVF index: {e}")