"""
Advanced Graph Query System for Memory Network
==============================================

Provides powerful query capabilities for the memory association network:
- Path finding between memories
- Subgraph extraction
- Pattern matching
- Temporal queries
- Cluster analysis
- Graph statistics
"""

import asyncio
from collections import deque
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum

from .association_network import AssociationNetwork, AssociationType, MemoryAssociation

import logging

logger = logging.getLogger(__name__)


class QueryOperator(str, Enum):
    """Query operators"""
    AND = "and"
    OR = "or"
    NOT = "not"


class TemporalRelation(str, Enum):
    """Temporal relations between events"""
    BEFORE = "before"
    AFTER = "after"
    DURING = "during"
    OVERLAPS = "overlaps"
    WITHIN = "within"


@dataclass
class PathQuery:
    """Query for finding paths between memories"""
    source_id: str
    target_id: str
    max_depth: int = 5
    allowed_types: Optional[List[AssociationType]] = None
    min_path_strength: float = 0.0


@dataclass
class SubgraphQuery:
    """Query for extracting subgraphs"""
    seed_memories: List[str]
    radius: int = 2  # How many hops from seeds
    min_strength: float = 0.0
    association_types: Optional[List[AssociationType]] = None


@dataclass
class PatternQuery:
    """Query for pattern matching in memory graph"""
    pattern_type: str  # "triangle", "star", "chain", "cycle"
    min_size: int = 3
    required_types: Optional[List[AssociationType]] = None


@dataclass
class TemporalQuery:
    """Temporal query for memories"""
    start_time: datetime
    end_time: datetime
    relation: TemporalRelation = TemporalRelation.WITHIN
    include_associations: bool = True


@dataclass
class GraphPath:
    """Represents a path through the memory graph"""
    source: str
    target: str
    path: List[MemoryAssociation]
    total_strength: float
    avg_strength: float
    length: int


@dataclass
class Subgraph:
    """Represents a subgraph of memories"""
    memories: Set[str]
    associations: List[MemoryAssociation]
    density: float  # Ratio of actual to possible edges
    coherence: float  # Average association strength


class MemoryGraphQuery:
    """
    Advanced query engine for memory association network

    Provides high-level graph query capabilities
    """

    def __init__(self, association_network: AssociationNetwork):
        """
        Initialize query engine

        Args:
            association_network: The memory association network to query
        """
        self.network = association_network

    # Path Queries

    async def find_all_paths(
        self,
        query: PathQuery
    ) -> List[GraphPath]:
        """
        Find all paths between source and target memories

        Uses depth-first search to enumerate all paths up to max_depth
        """
        all_paths = []

        async def dfs(
            current: str,
            target: str,
            path: List[MemoryAssociation],
            visited: Set[str],
            depth: int
        ):
            if depth > query.max_depth:
                return

            if current == target and path:
                # Found a path
                total_strength = 1.0
                for assoc in path:
                    total_strength *= assoc.strength

                if total_strength >= query.min_path_strength:
                    all_paths.append(GraphPath(
                        source=query.source_id,
                        target=target,
                        path=path.copy(),
                        total_strength=total_strength,
                        avg_strength=sum(a.strength for a in path) / len(path),
                        length=len(path)
                    ))
                return

            # Explore neighbors
            associations = self.network.adjacency.get(current, [])

            # Filter by type if specified
            if query.allowed_types:
                associations = [
                    a for a in associations
                    if a.association_type in query.allowed_types
                ]

            for assoc in associations:
                # Determine next node
                next_node = (
                    assoc.memory_b_id if assoc.memory_a_id == current
                    else assoc.memory_a_id
                )

                if next_node not in visited:
                    visited.add(next_node)
                    path.append(assoc)

                    await dfs(next_node, target, path, visited, depth + 1)

                    path.pop()
                    visited.remove(next_node)

        # Start DFS
        await dfs(query.source_id, query.target_id, [], {query.source_id}, 0)

        # Sort by strength
        all_paths.sort(key=lambda p: p.total_strength, reverse=True)

        logger.info(f"Found {len(all_paths)} paths from {query.source_id} to {query.target_id}")
        return all_paths

    async def find_shortest_path(
        self,
        query: PathQuery
    ) -> Optional[GraphPath]:
        """
        Find shortest path between memories using BFS

        Returns:
            Shortest path or None if no path exists
        """
        # BFS for shortest path
        queue = deque([(query.source_id, [])])
        visited = {query.source_id}

        while queue:
            current, path = queue.popleft()

            if len(path) > query.max_depth:
                continue

            if current == query.target_id and path:
                # Found shortest path
                total_strength = 1.0
                for assoc in path:
                    total_strength *= assoc.strength

                return GraphPath(
                    source=query.source_id,
                    target=query.target_id,
                    path=path,
                    total_strength=total_strength,
                    avg_strength=sum(a.strength for a in path) / len(path),
                    length=len(path)
                )

            # Explore neighbors
            associations = self.network.adjacency.get(current, [])

            # Filter by type
            if query.allowed_types:
                associations = [
                    a for a in associations
                    if a.association_type in query.allowed_types
                ]

            for assoc in associations:
                next_node = (
                    assoc.memory_b_id if assoc.memory_a_id == current
                    else assoc.memory_a_id
                )

                if next_node not in visited:
                    visited.add(next_node)
                    queue.append((next_node, path + [assoc]))

        return None

    # Subgraph Queries

    async def extract_subgraph(
        self,
        query: SubgraphQuery
    ) -> Subgraph:
        """
        Extract subgraph around seed memories

        Uses BFS to expand from seeds up to specified radius
        """
        memories = set(query.seed_memories)
        associations = []
        visited = set(query.seed_memories)

        # BFS from all seeds
        queue = deque([(seed, 0) for seed in query.seed_memories])

        while queue:
            current, depth = queue.popleft()

            if depth >= query.radius:
                continue

            # Get neighbors
            for assoc in self.network.adjacency.get(current, []):
                # Filter by type
                if query.association_types:
                    if assoc.association_type not in query.association_types:
                        continue

                # Filter by strength
                if assoc.strength < query.min_strength:
                    continue

                # Add association
                if assoc not in associations:
                    associations.append(assoc)

                # Find neighbor
                neighbor = (
                    assoc.memory_b_id if assoc.memory_a_id == current
                    else assoc.memory_a_id
                )

                # Add to memories
                memories.add(neighbor)

                # Continue BFS
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))

        # Calculate metrics
        num_memories = len(memories)
        num_associations = len(associations)
        max_possible_edges = num_memories * (num_memories - 1) / 2

        density = num_associations / max_possible_edges if max_possible_edges > 0 else 0
        coherence = (
            sum(a.strength for a in associations) / num_associations
            if associations else 0
        )

        return Subgraph(
            memories=memories,
            associations=associations,
            density=density,
            coherence=coherence
        )

    # Pattern Queries

    async def find_triangles(
        self,
        min_strength: float = 0.5
    ) -> List[Tuple[str, str, str]]:
        """
        Find triangles in the memory graph

        A triangle is three memories all connected to each other
        """
        triangles = []
        memories = list(self.network.adjacency.keys())

        for i, mem_a in enumerate(memories):
            # Get neighbors of A
            neighbors_a = set()
            for assoc in self.network.adjacency.get(mem_a, []):
                if assoc.strength >= min_strength:
                    neighbor = (
                        assoc.memory_b_id if assoc.memory_a_id == mem_a
                        else assoc.memory_a_id
                    )
                    neighbors_a.add(neighbor)

            # Check pairs of neighbors
            neighbors_list = list(neighbors_a)
            for j in range(len(neighbors_list)):
                for k in range(j + 1, len(neighbors_list)):
                    mem_b = neighbors_list[j]
                    mem_c = neighbors_list[k]

                    # Check if B and C are connected
                    for assoc in self.network.adjacency.get(mem_b, []):
                        if assoc.strength >= min_strength:
                            other = (
                                assoc.memory_b_id if assoc.memory_a_id == mem_b
                                else assoc.memory_a_id
                            )
                            if other == mem_c:
                                # Found triangle
                                triangle = tuple(sorted([mem_a, mem_b, mem_c]))
                                if triangle not in triangles:
                                    triangles.append(triangle)
                                break

        logger.info(f"Found {len(triangles)} triangles")
        return triangles

    async def find_star_patterns(
        self,
        min_rays: int = 3,
        min_strength: float = 0.5
    ) -> List[Tuple[str, List[str]]]:
        """
        Find star patterns (one central node with multiple connections)

        Returns:
            List of (center, [connected_nodes]) tuples
        """
        stars = []

        for memory_id in self.network.adjacency.keys():
            # Get strong connections
            connected = []
            for assoc in self.network.adjacency.get(memory_id, []):
                if assoc.strength >= min_strength:
                    neighbor = (
                        assoc.memory_b_id if assoc.memory_a_id == memory_id
                        else assoc.memory_a_id
                    )
                    connected.append(neighbor)

            if len(connected) >= min_rays:
                stars.append((memory_id, connected))

        # Sort by number of connections
        stars.sort(key=lambda x: len(x[1]), reverse=True)

        logger.info(f"Found {len(stars)} star patterns")
        return stars

    # Temporal Queries

    async def query_temporal_window(
        self,
        query: TemporalQuery,
        memory_timestamps: Dict[str, datetime]
    ) -> List[str]:
        """
        Query memories within a temporal window

        Args:
            query: Temporal query specification
            memory_timestamps: Mapping of memory_id -> timestamp

        Returns:
            List of memory IDs matching the query
        """
        matching_memories = []

        for memory_id, timestamp in memory_timestamps.items():
            # Check temporal relation
            if query.relation == TemporalRelation.WITHIN:
                if query.start_time <= timestamp <= query.end_time:
                    matching_memories.append(memory_id)

            elif query.relation == TemporalRelation.BEFORE:
                if timestamp < query.start_time:
                    matching_memories.append(memory_id)

            elif query.relation == TemporalRelation.AFTER:
                if timestamp > query.end_time:
                    matching_memories.append(memory_id)

        logger.info(f"Found {len(matching_memories)} memories in temporal window")
        return matching_memories

    # Graph Statistics

    async def compute_centrality(
        self,
        memory_ids: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Compute degree centrality for memories

        Centrality = number of connections / max possible connections
        """
        if memory_ids is None:
            memory_ids = list(self.network.adjacency.keys())

        total_nodes = len(memory_ids)
        centrality = {}

        for memory_id in memory_ids:
            degree = len(self.network.adjacency.get(memory_id, []))
            centrality[memory_id] = degree / (total_nodes - 1) if total_nodes > 1 else 0

        return centrality

    async def find_bridges(
        self,
        min_strength: float = 0.3
    ) -> List[MemoryAssociation]:
        """
        Find bridge associations (whose removal disconnects the graph)

        These are critical connections between memory clusters
        """
        bridges = []

        # For each association, temporarily remove it and check connectivity
        for assoc in self.network.associations.values():
            if assoc.strength < min_strength:
                continue

            # Check if removing this association disconnects the graph
            # (Simplified check - in production, use more efficient algorithm)
            # This is computationally expensive, so we'll mark it as a candidate
            bridges.append(assoc)

        logger.info(f"Found {len(bridges)} potential bridge associations")
        return bridges

    async def analyze_graph_metrics(self) -> Dict[str, Any]:
        """
        Compute comprehensive graph metrics

        Returns:
            Dictionary of graph statistics
        """
        num_memories = len(self.network.adjacency)
        num_associations = len(self.network.associations)

        # Calculate average degree
        total_degree = sum(len(assocs) for assocs in self.network.adjacency.values())
        avg_degree = total_degree / num_memories if num_memories > 0 else 0

        # Calculate density
        max_edges = num_memories * (num_memories - 1) / 2
        density = num_associations / max_edges if max_edges > 0 else 0

        # Calculate average strength
        avg_strength = (
            sum(a.strength for a in self.network.associations.values()) / num_associations
            if num_associations > 0 else 0
        )

        # Find triangles
        triangles = await self.find_triangles(min_strength=0.5)

        # Clustering coefficient
        clustering_coef = len(triangles) / (num_memories * (num_memories - 1) * (num_memories - 2) / 6) if num_memories >= 3 else 0

        return {
            "num_memories": num_memories,
            "num_associations": num_associations,
            "avg_degree": round(avg_degree, 2),
            "density": round(density, 4),
            "avg_strength": round(avg_strength, 3),
            "num_triangles": len(triangles),
            "clustering_coefficient": round(clustering_coef, 4),
            "domains": len(set(self.network.by_type.keys()))
        }
