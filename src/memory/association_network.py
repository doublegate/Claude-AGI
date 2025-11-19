"""
Enhanced Memory Association Network for Claude-AGI
===================================================

Advanced memory association system that creates and manages multiple types
of connections between memories, enabling richer memory retrieval and insights.

Features:
- Multiple association types (temporal, causal, thematic, emotional)
- Association strength tracking and decay
- Network clustering and communities
- Indirect association discovery
- Association pattern learning
"""

import asyncio
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class AssociationType(Enum):
    """Types of associations between memories"""
    TEMPORAL = "temporal"  # Co-occurred in time
    CAUSAL = "causal"  # One led to the other
    THEMATIC = "thematic"  # Similar topics/themes
    EMOTIONAL = "emotional"  # Similar emotional content
    SEMANTIC = "semantic"  # Similar meaning
    CONTEXTUAL = "contextual"  # Same context/situation
    CONTRASTING = "contrasting"  # Opposites/contrasts


@dataclass
class MemoryAssociation:
    """Represents an association between two memories"""
    association_id: str
    memory_a_id: str
    memory_b_id: str
    association_type: AssociationType
    strength: float  # 0.0-1.0
    created_at: datetime = field(default_factory=datetime.now)
    last_activated: datetime = field(default_factory=datetime.now)
    activation_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def activate(self):
        """Activate this association (strengthens it)"""
        self.last_activated = datetime.now()
        self.activation_count += 1
        # Strengthen association (with diminishing returns)
        self.strength = min(1.0, self.strength + 0.1 * (1.0 - self.strength))

    def decay(self, days_since_activation: int, decay_rate: float = 0.01):
        """Apply time-based decay to association strength"""
        self.strength = max(0.0, self.strength - (decay_rate * days_since_activation))


@dataclass
class MemoryCluster:
    """Cluster of related memories"""
    cluster_id: str
    memory_ids: Set[str] = field(default_factory=set)
    centroid_theme: Optional[str] = None
    coherence_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


class AssociationNetwork:
    """
    Manages a network of associations between memories.

    Provides advanced memory linking capabilities beyond simple similarity,
    enabling context-aware retrieval and insight generation.
    """

    def __init__(self, decay_enabled: bool = True, decay_interval_hours: int = 24):
        """
        Initialize association network

        Args:
            decay_enabled: Whether to apply time-based decay
            decay_interval_hours: Hours between decay application
        """
        # Association storage
        self.associations: Dict[str, MemoryAssociation] = {}

        # Adjacency lists for efficient traversal
        self.adjacency: Dict[str, List[MemoryAssociation]] = defaultdict(list)

        # Type-specific indices
        self.by_type: Dict[AssociationType, List[MemoryAssociation]] = defaultdict(list)

        # Memory clusters
        self.clusters: Dict[str, MemoryCluster] = {}
        self.memory_to_cluster: Dict[str, str] = {}

        # Decay settings
        self.decay_enabled = decay_enabled
        self.decay_interval = timedelta(hours=decay_interval_hours)
        self.last_decay = datetime.now()

        # Statistics
        self.stats = {
            'total_associations': 0,
            'associations_by_type': defaultdict(int),
            'total_activations': 0
        }

    async def create_association(
        self,
        memory_a_id: str,
        memory_b_id: str,
        association_type: AssociationType,
        strength: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryAssociation:
        """
        Create an association between two memories

        Args:
            memory_a_id: First memory ID
            memory_b_id: Second memory ID
            association_type: Type of association
            strength: Initial strength (0.0-1.0)
            metadata: Additional metadata

        Returns:
            Created MemoryAssociation
        """
        # Ensure consistent ordering (smaller ID first)
        if memory_a_id > memory_b_id:
            memory_a_id, memory_b_id = memory_b_id, memory_a_id

        # Generate association ID
        import uuid
        association_id = f"{memory_a_id}_{memory_b_id}_{association_type.value}"

        # Check if association already exists
        if association_id in self.associations:
            # Strengthen existing association
            existing = self.associations[association_id]
            existing.activate()
            logger.debug(f"Strengthened existing association: {association_id}")
            return existing

        # Create new association
        association = MemoryAssociation(
            association_id=association_id,
            memory_a_id=memory_a_id,
            memory_b_id=memory_b_id,
            association_type=association_type,
            strength=max(0.0, min(1.0, strength)),
            metadata=metadata or {}
        )

        # Store association
        self.associations[association_id] = association

        # Update adjacency lists (bidirectional)
        self.adjacency[memory_a_id].append(association)
        self.adjacency[memory_b_id].append(association)

        # Update type index
        self.by_type[association_type].append(association)

        # Update statistics
        self.stats['total_associations'] += 1
        self.stats['associations_by_type'][association_type.value] += 1

        logger.info(f"Created {association_type.value} association: {memory_a_id} <-> {memory_b_id}")

        return association

    async def get_associated_memories(
        self,
        memory_id: str,
        association_types: Optional[List[AssociationType]] = None,
        min_strength: float = 0.0,
        limit: int = 10
    ) -> List[Tuple[str, MemoryAssociation]]:
        """
        Get memories associated with a given memory

        Args:
            memory_id: Memory to find associations for
            association_types: Filter by types (None = all types)
            min_strength: Minimum association strength
            limit: Maximum number of results

        Returns:
            List of (associated_memory_id, association) tuples
        """
        # Apply decay if needed
        await self._apply_decay_if_needed()

        # Get all associations for this memory
        associations = self.adjacency.get(memory_id, [])

        # Filter by type if specified
        if association_types:
            associations = [a for a in associations if a.association_type in association_types]

        # Filter by strength
        associations = [a for a in associations if a.strength >= min_strength]

        # Sort by strength (descending)
        associations.sort(key=lambda a: a.strength, reverse=True)

        # Extract associated memory IDs
        results = []
        for association in associations[:limit]:
            # Determine which memory is the associated one
            other_id = (
                association.memory_b_id
                if association.memory_a_id == memory_id
                else association.memory_a_id
            )
            results.append((other_id, association))

            # Activate association (strengthen through use)
            association.activate()
            self.stats['total_activations'] += 1

        return results

    async def find_indirect_associations(
        self,
        memory_id: str,
        max_depth: int = 2,
        min_path_strength: float = 0.3
    ) -> List[Tuple[str, List[MemoryAssociation]]]:
        """
        Find indirect associations (e.g., memories connected through intermediaries)

        Args:
            memory_id: Starting memory
            max_depth: Maximum path length to explore
            min_path_strength: Minimum cumulative strength for path

        Returns:
            List of (target_memory_id, path) tuples
        """
        # BFS to find paths
        visited = {memory_id}
        queue = deque([(memory_id, [], 1.0)])  # (current_id, path, cumulative_strength)
        indirect_associations = []

        while queue:
            current_id, path, cumulative_strength = queue.popleft()

            # Stop if path too long
            if len(path) >= max_depth:
                continue

            # Get direct associations
            for other_id, association in await self.get_associated_memories(current_id, limit=50):
                # Calculate new cumulative strength
                new_strength = cumulative_strength * association.strength

                # Skip if path too weak
                if new_strength < min_path_strength:
                    continue

                # Build new path
                new_path = path + [association]

                # If this is a new memory (not visited), add as indirect association
                if other_id not in visited:
                    visited.add(other_id)

                    # Only add if path length > 1 (indirect)
                    if len(new_path) > 1:
                        indirect_associations.append((other_id, new_path))

                    # Continue exploration
                    queue.append((other_id, new_path, new_strength))

        # Sort by path strength (product of association strengths)
        indirect_associations.sort(
            key=lambda x: self._calculate_path_strength(x[1]),
            reverse=True
        )

        return indirect_associations

    def _calculate_path_strength(self, path: List[MemoryAssociation]) -> float:
        """Calculate cumulative strength of association path"""
        if not path:
            return 0.0
        strength = 1.0
        for association in path:
            strength *= association.strength
        return strength

    async def create_temporal_associations(
        self,
        memory_ids: List[str],
        time_window_seconds: int = 60,
        strength: float = 0.6
    ) -> int:
        """
        Create temporal associations between memories that occurred close in time

        Args:
            memory_ids: List of memory IDs (ordered by time)
            time_window_seconds: Time window for association
            strength: Association strength

        Returns:
            Number of associations created
        """
        count = 0

        # Create associations between adjacent memories in time window
        for i in range(len(memory_ids)):
            for j in range(i + 1, len(memory_ids)):
                # Stop if outside time window (assuming ordered list)
                if j - i > time_window_seconds:
                    break

                await self.create_association(
                    memory_ids[i],
                    memory_ids[j],
                    AssociationType.TEMPORAL,
                    strength=strength
                )
                count += 1

        logger.info(f"Created {count} temporal associations")
        return count

    async def cluster_memories(
        self,
        memory_ids: List[str],
        min_cluster_size: int = 3,
        coherence_threshold: float = 0.5
    ) -> List[MemoryCluster]:
        """
        Cluster memories based on their associations

        Args:
            memory_ids: Memories to cluster
            min_cluster_size: Minimum cluster size
            coherence_threshold: Minimum coherence for cluster

        Returns:
            List of clusters
        """
        # Simple clustering based on association density
        # In production, would use more sophisticated methods (community detection, etc.)

        visited = set()
        clusters = []

        for memory_id in memory_ids:
            if memory_id in visited:
                continue

            # Start new cluster
            cluster_memories = {memory_id}
            queue = deque([memory_id])
            visited.add(memory_id)

            # Expand cluster using BFS
            while queue:
                current_id = queue.popleft()

                # Get strongly associated memories
                associated = await self.get_associated_memories(
                    current_id,
                    min_strength=coherence_threshold,
                    limit=20
                )

                for other_id, _ in associated:
                    if other_id not in visited and other_id in memory_ids:
                        cluster_memories.add(other_id)
                        queue.append(other_id)
                        visited.add(other_id)

            # Create cluster if large enough
            if len(cluster_memories) >= min_cluster_size:
                import uuid
                cluster = MemoryCluster(
                    cluster_id=str(uuid.uuid4()),
                    memory_ids=cluster_memories,
                    coherence_score=self._calculate_cluster_coherence(cluster_memories)
                )

                clusters.append(cluster)
                self.clusters[cluster.cluster_id] = cluster

                # Update memory -> cluster mapping
                for mem_id in cluster_memories:
                    self.memory_to_cluster[mem_id] = cluster.cluster_id

        logger.info(f"Created {len(clusters)} memory clusters")
        return clusters

    def _calculate_cluster_coherence(self, memory_ids: Set[str]) -> float:
        """Calculate coherence score for a cluster"""
        if len(memory_ids) < 2:
            return 0.0

        # Calculate average association strength within cluster
        total_strength = 0.0
        count = 0

        memory_list = list(memory_ids)
        for i in range(len(memory_list)):
            for j in range(i + 1, len(memory_list)):
                # Check if association exists
                for association in self.adjacency.get(memory_list[i], []):
                    if (association.memory_a_id == memory_list[j] or
                        association.memory_b_id == memory_list[j]):
                        total_strength += association.strength
                        count += 1

        return total_strength / count if count > 0 else 0.0

    async def suggest_associations(
        self,
        memory_id: str,
        candidate_memory_ids: List[str],
        limit: int = 5
    ) -> List[Tuple[str, AssociationType, float]]:
        """
        Suggest potential associations based on patterns

        Args:
            memory_id: Memory to find associations for
            candidate_memory_ids: Potential memories to associate
            limit: Maximum suggestions

        Returns:
            List of (candidate_id, suggested_type, confidence) tuples
        """
        suggestions = []

        # Get existing associations to learn patterns
        existing_associations = self.adjacency.get(memory_id, [])

        # Count association types
        type_counts = defaultdict(int)
        for association in existing_associations:
            type_counts[association.association_type] += 1

        # For each candidate, estimate likelihood of different association types
        for candidate_id in candidate_memory_ids[:limit]:
            # Skip if already associated
            if any(a.memory_a_id == candidate_id or a.memory_b_id == candidate_id
                   for a in existing_associations):
                continue

            # Find indirect associations
            indirect = await self.find_indirect_associations(memory_id, max_depth=2)

            # Check if candidate is indirectly connected
            for target_id, path in indirect:
                if target_id == candidate_id and path:
                    # Suggest same type as most common in path
                    path_types = [a.association_type for a in path]
                    most_common_type = max(set(path_types), key=path_types.count)

                    # Confidence based on path strength
                    confidence = self._calculate_path_strength(path)

                    suggestions.append((candidate_id, most_common_type, confidence))
                    break

        # Sort by confidence
        suggestions.sort(key=lambda x: x[2], reverse=True)

        return suggestions[:limit]

    async def _apply_decay_if_needed(self):
        """Apply time-based decay to associations if interval has passed"""
        if not self.decay_enabled:
            return

        now = datetime.now()
        if now - self.last_decay < self.decay_interval:
            return

        # Apply decay to all associations
        days_since_decay = (now - self.last_decay).total_seconds() / 86400

        for association in self.associations.values():
            days_since_activation = (now - association.last_activated).total_seconds() / 86400
            association.decay(int(days_since_activation))

        self.last_decay = now
        logger.debug(f"Applied association decay ({days_since_decay:.1f} days)")

    async def prune_weak_associations(self, min_strength: float = 0.1) -> int:
        """
        Remove associations that have decayed below threshold

        Args:
            min_strength: Minimum strength to keep

        Returns:
            Number of associations removed
        """
        to_remove = []

        for association_id, association in self.associations.items():
            if association.strength < min_strength:
                to_remove.append(association_id)

        # Remove associations
        for association_id in to_remove:
            association = self.associations[association_id]

            # Remove from adjacency lists
            self.adjacency[association.memory_a_id].remove(association)
            self.adjacency[association.memory_b_id].remove(association)

            # Remove from type index
            self.by_type[association.association_type].remove(association)

            # Remove from main storage
            del self.associations[association_id]

            # Update statistics
            self.stats['total_associations'] -= 1
            self.stats['associations_by_type'][association.association_type.value] -= 1

        logger.info(f"Pruned {len(to_remove)} weak associations")
        return len(to_remove)

    async def get_statistics(self) -> Dict[str, Any]:
        """Get network statistics"""
        # Apply decay first
        await self._apply_decay_if_needed()

        # Calculate average strength by type
        avg_strength_by_type = {}
        for assoc_type, associations in self.by_type.items():
            if associations:
                avg_strength = sum(a.strength for a in associations) / len(associations)
                avg_strength_by_type[assoc_type.value] = round(avg_strength, 3)

        return {
            'total_associations': self.stats['total_associations'],
            'associations_by_type': dict(self.stats['associations_by_type']),
            'total_activations': self.stats['total_activations'],
            'avg_strength_by_type': avg_strength_by_type,
            'total_clusters': len(self.clusters),
            'memories_in_clusters': len(self.memory_to_cluster),
            'decay_enabled': self.decay_enabled,
            'last_decay': self.last_decay.isoformat()
        }
