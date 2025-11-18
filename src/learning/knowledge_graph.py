"""
Knowledge Graph System for Claude-AGI
======================================

Advanced knowledge representation using graph structures
to capture concepts, relationships, and semantic understanding.
"""

import asyncio
import logging
import pickle
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class RelationType(Enum):
    """Types of relationships between concepts"""
    IS_A = "is_a"                    # Taxonomy relationship
    PART_OF = "part_of"              # Composition relationship
    RELATED_TO = "related_to"        # General association
    CAUSES = "causes"                # Causal relationship
    REQUIRES = "requires"            # Dependency relationship
    SIMILAR_TO = "similar_to"        # Similarity relationship
    OPPOSITE_OF = "opposite_of"      # Antonym relationship
    INSTANCE_OF = "instance_of"      # Instantiation
    HAS_PROPERTY = "has_property"    # Property relationship
    USED_FOR = "used_for"            # Functional relationship


@dataclass
class Concept:
    """Represents a concept node in the knowledge graph"""
    id: str
    name: str
    concept_type: str
    description: str = ""
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    properties: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'concept_type': self.concept_type,
            'description': self.description,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'access_count': self.access_count,
            'properties': self.properties,
            'tags': list(self.tags)
        }


@dataclass
class Relationship:
    """Represents a relationship edge in the knowledge graph"""
    id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    strength: float = 1.0
    bidirectional: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    last_reinforced: datetime = field(default_factory=datetime.now)
    reinforcement_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'relation_type': self.relation_type.value,
            'strength': self.strength,
            'bidirectional': self.bidirectional,
            'created_at': self.created_at.isoformat(),
            'last_reinforced': self.last_reinforced.isoformat(),
            'reinforcement_count': self.reinforcement_count,
            'metadata': self.metadata
        }


class KnowledgeGraph:
    """
    Advanced knowledge graph for representing and reasoning
    about concepts, relationships, and semantic structures.
    """

    def __init__(self):
        # Core graph structure
        self.concepts: Dict[str, Concept] = {}
        self.relationships: Dict[str, Relationship] = {}

        # Adjacency lists for efficient traversal
        self.outgoing_edges: Dict[str, List[str]] = defaultdict(list)
        self.incoming_edges: Dict[str, List[str]] = defaultdict(list)

        # Indices for fast lookup
        self.concept_by_name: Dict[str, str] = {}
        self.concepts_by_type: Dict[str, List[str]] = defaultdict(list)
        self.relationships_by_type: Dict[RelationType, List[str]] = defaultdict(list)

        # Community detection
        self.communities: Dict[str, Set[str]] = {}

        # Temporal tracking
        self.concept_history: List[Dict[str, Any]] = []

    async def add_concept(
        self,
        name: str,
        concept_type: str,
        description: str = "",
        properties: Optional[Dict[str, Any]] = None,
        tags: Optional[Set[str]] = None,
        embedding: Optional[List[float]] = None
    ) -> Concept:
        """Add a new concept to the knowledge graph"""
        # Check if concept already exists
        if name in self.concept_by_name:
            existing_id = self.concept_by_name[name]
            existing_concept = self.concepts[existing_id]
            # Update access tracking
            existing_concept.last_accessed = datetime.now()
            existing_concept.access_count += 1
            return existing_concept

        concept_id = str(uuid.uuid4())

        concept = Concept(
            id=concept_id,
            name=name,
            concept_type=concept_type,
            description=description,
            properties=properties or {},
            tags=tags or set(),
            embedding=embedding
        )

        self.concepts[concept_id] = concept
        self.concept_by_name[name] = concept_id
        self.concepts_by_type[concept_type].append(concept_id)

        # Track creation
        self.concept_history.append({
            'action': 'create',
            'concept_id': concept_id,
            'timestamp': datetime.now()
        })

        logger.info(f"Added concept: {name} (ID: {concept_id})")
        return concept

    async def add_relationship(
        self,
        source: str,
        target: str,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Relationship]:
        """Add a relationship between two concepts"""
        # Get concept IDs
        source_id = self.concept_by_name.get(source, source)
        target_id = self.concept_by_name.get(target, target)

        if source_id not in self.concepts or target_id not in self.concepts:
            logger.warning(f"Cannot create relationship: one or both concepts not found")
            return None

        # Check if relationship already exists
        existing_rel = self._find_existing_relationship(source_id, target_id, relation_type)
        if existing_rel:
            # Reinforce existing relationship
            existing_rel.strength = min(1.0, existing_rel.strength + 0.1)
            existing_rel.last_reinforced = datetime.now()
            existing_rel.reinforcement_count += 1
            return existing_rel

        relationship_id = str(uuid.uuid4())

        relationship = Relationship(
            id=relationship_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata or {}
        )

        self.relationships[relationship_id] = relationship
        self.outgoing_edges[source_id].append(relationship_id)
        self.incoming_edges[target_id].append(relationship_id)
        self.relationships_by_type[relation_type].append(relationship_id)

        # If bidirectional, also add reverse edge
        if bidirectional:
            self.outgoing_edges[target_id].append(relationship_id)
            self.incoming_edges[source_id].append(relationship_id)

        logger.info(f"Added relationship: {source} -> {target} ({relation_type.value})")
        return relationship

    def _find_existing_relationship(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType
    ) -> Optional[Relationship]:
        """Find if relationship already exists"""
        for rel_id in self.outgoing_edges.get(source_id, []):
            rel = self.relationships.get(rel_id)
            if rel and rel.target_id == target_id and rel.relation_type == relation_type:
                return rel
        return None

    async def get_related_concepts(
        self,
        concept_name: str,
        relation_types: Optional[List[RelationType]] = None,
        max_depth: int = 1,
        min_strength: float = 0.3
    ) -> List[Tuple[Concept, Relationship]]:
        """Get concepts related to a given concept"""
        concept_id = self.concept_by_name.get(concept_name)
        if not concept_id:
            return []

        related = []
        visited = set()

        def traverse(current_id: str, depth: int):
            if depth > max_depth or current_id in visited:
                return

            visited.add(current_id)

            for rel_id in self.outgoing_edges.get(current_id, []):
                rel = self.relationships[rel_id]

                # Filter by relation type and strength
                if relation_types and rel.relation_type not in relation_types:
                    continue
                if rel.strength < min_strength:
                    continue

                target_concept = self.concepts[rel.target_id]
                related.append((target_concept, rel))

                if depth < max_depth:
                    traverse(rel.target_id, depth + 1)

        traverse(concept_id, 0)

        # Sort by relationship strength
        related.sort(key=lambda x: x[1].strength, reverse=True)
        return related

    async def find_path(
        self,
        source_name: str,
        target_name: str,
        max_path_length: int = 5
    ) -> Optional[List[str]]:
        """Find shortest path between two concepts using BFS"""
        source_id = self.concept_by_name.get(source_name)
        target_id = self.concept_by_name.get(target_name)

        if not source_id or not target_id:
            return None

        queue = deque([(source_id, [source_id])])
        visited = {source_id}

        while queue:
            current_id, path = queue.popleft()

            if len(path) > max_path_length:
                continue

            if current_id == target_id:
                # Convert IDs to names
                return [self.concepts[cid].name for cid in path]

            for rel_id in self.outgoing_edges.get(current_id, []):
                rel = self.relationships[rel_id]
                next_id = rel.target_id

                if next_id not in visited:
                    visited.add(next_id)
                    queue.append((next_id, path + [next_id]))

        return None

    async def get_concept_neighborhood(
        self,
        concept_name: str,
        radius: int = 2
    ) -> Dict[str, Any]:
        """Get all concepts within a given radius"""
        concept_id = self.concept_by_name.get(concept_name)
        if not concept_id:
            return {}

        neighborhood = {'concepts': set(), 'relationships': set()}
        current_layer = {concept_id}

        for _ in range(radius):
            next_layer = set()

            for node_id in current_layer:
                neighborhood['concepts'].add(node_id)

                # Add all outgoing edges
                for rel_id in self.outgoing_edges.get(node_id, []):
                    rel = self.relationships[rel_id]
                    neighborhood['relationships'].add(rel_id)
                    next_layer.add(rel.target_id)

            current_layer = next_layer

        return {
            'concepts': [self.concepts[cid].to_dict() for cid in neighborhood['concepts']],
            'relationships': [self.relationships[rid].to_dict() for rid in neighborhood['relationships']]
        }

    async def find_analogies(
        self,
        source_a: str,
        source_b: str,
        target_a: str,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Find analogies: source_a is to source_b as target_a is to ?
        Uses structural similarity in the knowledge graph.
        """
        # Get relationship pattern between source_a and source_b
        source_path = await self.find_path(source_a, source_b, max_path_length=3)
        if not source_path:
            return []

        # Get concepts related to target_a
        target_related = await self.get_related_concepts(target_a, max_depth=2)

        # Find concepts with similar relationship patterns
        candidates = []
        for concept, _ in target_related:
            target_path = await self.find_path(target_a, concept.name, max_path_length=3)
            if target_path:
                # Calculate structural similarity
                similarity = self._calculate_path_similarity(source_path, target_path)
                if similarity > 0.3:
                    candidates.append((concept.name, similarity))

        # Sort by similarity
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:top_k]

    def _calculate_path_similarity(self, path1: List[str], path2: List[str]) -> float:
        """Calculate similarity between two paths"""
        if len(path1) != len(path2):
            return 0.0

        # Get relationship types in paths
        def get_rel_types(path):
            types = []
            for i in range(len(path) - 1):
                source_id = self.concept_by_name.get(path[i], path[i])
                target_id = self.concept_by_name.get(path[i+1], path[i+1])

                for rel_id in self.outgoing_edges.get(source_id, []):
                    rel = self.relationships[rel_id]
                    if rel.target_id == target_id:
                        types.append(rel.relation_type)
                        break
            return types

        types1 = get_rel_types(path1)
        types2 = get_rel_types(path2)

        if not types1 or not types2:
            return 0.0

        # Calculate type similarity
        matches = sum(1 for t1, t2 in zip(types1, types2) if t1 == t2)
        return matches / len(types1)

    async def detect_communities(self, min_size: int = 3) -> Dict[str, Set[str]]:
        """Detect communities of strongly related concepts"""
        # Simple community detection using connected components
        visited = set()
        communities = {}
        community_id = 0

        def dfs(node_id: str, community: Set[str]):
            if node_id in visited:
                return

            visited.add(node_id)
            community.add(node_id)

            for rel_id in self.outgoing_edges.get(node_id, []):
                rel = self.relationships[rel_id]
                if rel.strength > 0.5:  # Only strong relationships
                    dfs(rel.target_id, community)

        for concept_id in self.concepts:
            if concept_id not in visited:
                community = set()
                dfs(concept_id, community)

                if len(community) >= min_size:
                    communities[f"community_{community_id}"] = community
                    community_id += 1

        self.communities = communities
        return communities

    async def get_concept_importance(self, concept_name: str) -> float:
        """Calculate importance of a concept based on graph centrality"""
        concept_id = self.concept_by_name.get(concept_name)
        if not concept_id:
            return 0.0

        # Degree centrality
        in_degree = len(self.incoming_edges.get(concept_id, []))
        out_degree = len(self.outgoing_edges.get(concept_id, []))
        degree_score = (in_degree + out_degree) / (len(self.concepts) or 1)

        # Access frequency
        concept = self.concepts[concept_id]
        access_score = min(1.0, concept.access_count / 100)

        # Recency
        days_since_access = (datetime.now() - concept.last_accessed).days
        recency_score = max(0.0, 1.0 - days_since_access / 365)

        # Combined importance
        importance = (degree_score * 0.4 + access_score * 0.3 + recency_score * 0.3)
        return importance

    async def prune_weak_connections(self, strength_threshold: float = 0.2, age_days: int = 90):
        """Remove weak or stale relationships"""
        to_remove = []

        for rel_id, rel in self.relationships.items():
            # Check strength
            if rel.strength < strength_threshold:
                to_remove.append(rel_id)
                continue

            # Check age without reinforcement
            days_since_reinforcement = (datetime.now() - rel.last_reinforced).days
            if days_since_reinforcement > age_days and rel.reinforcement_count == 0:
                to_remove.append(rel_id)

        # Remove relationships
        for rel_id in to_remove:
            rel = self.relationships[rel_id]

            # Remove from indices
            if rel_id in self.outgoing_edges.get(rel.source_id, []):
                self.outgoing_edges[rel.source_id].remove(rel_id)
            if rel_id in self.incoming_edges.get(rel.target_id, []):
                self.incoming_edges[rel.target_id].remove(rel_id)
            if rel_id in self.relationships_by_type[rel.relation_type]:
                self.relationships_by_type[rel.relation_type].remove(rel_id)

            del self.relationships[rel_id]

        logger.info(f"Pruned {len(to_remove)} weak connections")

    async def save_to_file(self, filepath: str):
        """Save knowledge graph to file"""
        data = {
            'concepts': {k: v.to_dict() for k, v in self.concepts.items()},
            'relationships': {k: v.to_dict() for k, v in self.relationships.items()},
            'concept_by_name': self.concept_by_name,
            'concepts_by_type': {k: list(v) for k, v in self.concepts_by_type.items()},
        }

        with open(filepath, 'wb') as f:
            pickle.dump(data, f)

        logger.info(f"Saved knowledge graph to {filepath}")

    async def load_from_file(self, filepath: str):
        """Load knowledge graph from file"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        # Reconstruct concepts
        for concept_id, concept_data in data['concepts'].items():
            self.concepts[concept_id] = Concept(**concept_data)

        # Reconstruct relationships
        for rel_id, rel_data in data['relationships'].items():
            rel_data['relation_type'] = RelationType(rel_data['relation_type'])
            rel = Relationship(**rel_data)
            self.relationships[rel_id] = rel

            # Rebuild adjacency lists
            self.outgoing_edges[rel.source_id].append(rel_id)
            self.incoming_edges[rel.target_id].append(rel_id)
            self.relationships_by_type[rel.relation_type].append(rel_id)

        # Restore indices
        self.concept_by_name = data['concept_by_name']
        self.concepts_by_type = {k: list(v) for k, v in data['concepts_by_type'].items()}

        logger.info(f"Loaded knowledge graph from {filepath}")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph"""
        return {
            'total_concepts': len(self.concepts),
            'total_relationships': len(self.relationships),
            'concept_types': {k: len(v) for k, v in self.concepts_by_type.items()},
            'relationship_types': {k.value: len(v) for k, v in self.relationships_by_type.items()},
            'average_degree': sum(len(v) for v in self.outgoing_edges.values()) / len(self.concepts) if self.concepts else 0,
            'communities': len(self.communities)
        }
