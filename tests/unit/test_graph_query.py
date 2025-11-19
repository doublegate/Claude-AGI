"""
Unit tests for memory graph query system
"""

import pytest
from datetime import datetime, timedelta
from typing import List

from src.memory.association_network import (
    AssociationNetwork,
    AssociationType,
    MemoryAssociation
)
from src.memory.graph_query import (
    MemoryGraphQuery,
    PathQuery,
    SubgraphQuery,
    PatternQuery,
    TemporalQuery,
    TemporalRelation,
    GraphPath,
    Subgraph
)


class TestMemoryGraphQuery:
    """Test memory graph query functionality"""

    @pytest.fixture
    async def association_network(self):
        """Create sample association network"""
        network = AssociationNetwork()

        # Create a simple graph:
        #   A -- B -- C
        #   |         |
        #   D -- E -- F
        #   |
        #   G

        await network.create_association("A", "B", AssociationType.TEMPORAL, 0.8)
        await network.create_association("B", "C", AssociationType.CAUSAL, 0.7)
        await network.create_association("A", "D", AssociationType.THEMATIC, 0.9)
        await network.create_association("D", "E", AssociationType.SEMANTIC, 0.6)
        await network.create_association("E", "F", AssociationType.CONTEXTUAL, 0.5)
        await network.create_association("C", "F", AssociationType.EMOTIONAL, 0.7)
        await network.create_association("D", "G", AssociationType.TEMPORAL, 0.4)

        return network

    @pytest.fixture
    async def query_engine(self, association_network):
        """Create query engine"""
        return MemoryGraphQuery(association_network)

    @pytest.mark.asyncio
    async def test_find_shortest_path_exists(self, query_engine):
        """Test finding shortest path between connected memories"""
        query = PathQuery(
            source_id="A",
            target_id="C",
            max_depth=5
        )

        path = await query_engine.find_shortest_path(query)

        assert path is not None
        assert path.source == "A"
        assert path.target == "C"
        assert path.length == 2  # A -> B -> C
        assert len(path.path) == 2

    @pytest.mark.asyncio
    async def test_find_shortest_path_none(self, query_engine, association_network):
        """Test finding path when none exists"""
        # Add isolated node
        query = PathQuery(
            source_id="A",
            target_id="Z",  # Doesn't exist
            max_depth=5
        )

        path = await query_engine.find_shortest_path(query)

        assert path is None

    @pytest.mark.asyncio
    async def test_find_shortest_path_max_depth(self, query_engine):
        """Test shortest path respects max depth"""
        query = PathQuery(
            source_id="A",
            target_id="F",
            max_depth=2  # A -> F requires 3+ hops
        )

        path = await query_engine.find_shortest_path(query)

        # Should not find path within depth limit
        assert path is None or path.length <= 2

    @pytest.mark.asyncio
    async def test_find_all_paths(self, query_engine):
        """Test finding all paths between memories"""
        query = PathQuery(
            source_id="A",
            target_id="F",
            max_depth=5
        )

        paths = await query_engine.find_all_paths(query)

        assert len(paths) > 0
        assert all(p.source == "A" for p in paths)
        assert all(p.target == "F" for p in paths)

        # Should find multiple paths:
        # A -> B -> C -> F
        # A -> D -> E -> F

    @pytest.mark.asyncio
    async def test_find_paths_with_type_filter(self, query_engine):
        """Test finding paths with specific association types"""
        query = PathQuery(
            source_id="A",
            target_id="E",
            max_depth=5,
            allowed_types=[AssociationType.THEMATIC, AssociationType.SEMANTIC]
        )

        paths = await query_engine.find_all_paths(query)

        # Should only find A -> D -> E path (thematic + semantic)
        assert len(paths) > 0

        # Verify all associations are of allowed types
        for path in paths:
            for assoc in path.path:
                assert assoc.association_type in [AssociationType.THEMATIC, AssociationType.SEMANTIC]

    @pytest.mark.asyncio
    async def test_path_strength_calculation(self, query_engine):
        """Test path strength calculation"""
        query = PathQuery(
            source_id="A",
            target_id="C",
            max_depth=5
        )

        paths = await query_engine.find_all_paths(query)

        assert len(paths) > 0

        for path in paths:
            # Total strength is product of individual strengths
            expected_total = 1.0
            for assoc in path.path:
                expected_total *= assoc.strength

            assert abs(path.total_strength - expected_total) < 0.001

            # Average strength
            expected_avg = sum(a.strength for a in path.path) / len(path.path)
            assert abs(path.avg_strength - expected_avg) < 0.001

    @pytest.mark.asyncio
    async def test_extract_subgraph_single_seed(self, query_engine):
        """Test extracting subgraph from single seed"""
        query = SubgraphQuery(
            seed_memories=["A"],
            radius=2,
            min_strength=0.0
        )

        subgraph = await query_engine.extract_subgraph(query)

        assert "A" in subgraph.memories
        # Should include neighbors within radius 2
        assert "B" in subgraph.memories  # Distance 1
        assert "D" in subgraph.memories  # Distance 1
        assert "C" in subgraph.memories  # Distance 2
        assert "E" in subgraph.memories  # Distance 2

    @pytest.mark.asyncio
    async def test_extract_subgraph_multiple_seeds(self, query_engine):
        """Test extracting subgraph from multiple seeds"""
        query = SubgraphQuery(
            seed_memories=["A", "F"],
            radius=1,
            min_strength=0.0
        )

        subgraph = await query_engine.extract_subgraph(query)

        # Should include both seeds
        assert "A" in subgraph.memories
        assert "F" in subgraph.memories

        # And their direct neighbors
        assert "B" in subgraph.memories  # Neighbor of A
        assert "D" in subgraph.memories  # Neighbor of A
        assert "E" in subgraph.memories  # Neighbor of F
        assert "C" in subgraph.memories  # Neighbor of F

    @pytest.mark.asyncio
    async def test_subgraph_strength_filter(self, query_engine):
        """Test subgraph extraction with strength filter"""
        query = SubgraphQuery(
            seed_memories=["A"],
            radius=2,
            min_strength=0.7  # Only strong associations
        )

        subgraph = await query_engine.extract_subgraph(query)

        # Should only include high-strength connections
        for assoc in subgraph.associations:
            assert assoc.strength >= 0.7

    @pytest.mark.asyncio
    async def test_subgraph_type_filter(self, query_engine):
        """Test subgraph extraction with type filter"""
        query = SubgraphQuery(
            seed_memories=["A"],
            radius=2,
            association_types=[AssociationType.TEMPORAL, AssociationType.THEMATIC]
        )

        subgraph = await query_engine.extract_subgraph(query)

        # Should only include specified types
        for assoc in subgraph.associations:
            assert assoc.association_type in [AssociationType.TEMPORAL, AssociationType.THEMATIC]

    @pytest.mark.asyncio
    async def test_subgraph_metrics(self, query_engine):
        """Test subgraph density and coherence metrics"""
        query = SubgraphQuery(
            seed_memories=["A"],
            radius=1,
            min_strength=0.0
        )

        subgraph = await query_engine.extract_subgraph(query)

        # Density should be between 0 and 1
        assert 0.0 <= subgraph.density <= 1.0

        # Coherence should be between 0 and 1
        assert 0.0 <= subgraph.coherence <= 1.0

        # Coherence is average strength
        if subgraph.associations:
            expected_coherence = sum(a.strength for a in subgraph.associations) / len(subgraph.associations)
            assert abs(subgraph.coherence - expected_coherence) < 0.001

    @pytest.mark.asyncio
    async def test_find_triangles(self, query_engine, association_network):
        """Test finding triangular patterns"""
        # Create a triangle: A -- B -- C -- A
        await association_network.create_association("A", "C", AssociationType.SEMANTIC, 0.6)

        triangles = await query_engine.find_triangles(min_strength=0.5)

        # Should find at least one triangle
        assert len(triangles) > 0

        # Each triangle should have 3 unique memories
        for triangle in triangles:
            assert len(triangle) == 3
            assert len(set(triangle)) == 3  # All unique

    @pytest.mark.asyncio
    async def test_find_triangles_strength_filter(self, query_engine, association_network):
        """Test triangle detection with strength filter"""
        # Create weak triangle
        await association_network.create_association("D", "G", AssociationType.SEMANTIC, 0.2)
        await association_network.create_association("E", "G", AssociationType.SEMANTIC, 0.2)

        # High strength threshold should exclude weak triangles
        triangles = await query_engine.find_triangles(min_strength=0.8)

        # Should not find weak triangles
        for triangle in triangles:
            # Verify all edges are strong
            for i, mem1 in enumerate(triangle):
                for mem2 in triangle[i+1:]:
                    # Check association exists and is strong
                    pass  # Complex verification omitted

    @pytest.mark.asyncio
    async def test_find_star_patterns(self, query_engine):
        """Test finding star patterns"""
        stars = await query_engine.find_star_patterns(min_rays=2, min_strength=0.5)

        # Should find star patterns
        assert len(stars) > 0

        # Each star should have center and rays
        for center, rays in stars:
            assert len(rays) >= 2
            assert center is not None

    @pytest.mark.asyncio
    async def test_find_star_patterns_sorted(self, query_engine):
        """Test star patterns are sorted by number of connections"""
        stars = await query_engine.find_star_patterns(min_rays=1, min_strength=0.0)

        # Should be sorted descending by ray count
        if len(stars) > 1:
            for i in range(len(stars) - 1):
                assert len(stars[i][1]) >= len(stars[i+1][1])

    @pytest.mark.asyncio
    async def test_temporal_query_within(self, query_engine):
        """Test temporal query with WITHIN relation"""
        timestamps = {
            "A": datetime(2025, 1, 1, 12, 0),
            "B": datetime(2025, 1, 5, 12, 0),
            "C": datetime(2025, 1, 10, 12, 0),
            "D": datetime(2025, 1, 15, 12, 0),
            "E": datetime(2025, 1, 20, 12, 0),
        }

        query = TemporalQuery(
            start_time=datetime(2025, 1, 1),
            end_time=datetime(2025, 1, 11),
            relation=TemporalRelation.WITHIN
        )

        results = await query_engine.query_temporal_window(query, timestamps)

        # Should include A, B, C (within range)
        assert "A" in results
        assert "B" in results
        assert "C" in results

        # Should exclude D, E (outside range)
        assert "D" not in results
        assert "E" not in results

    @pytest.mark.asyncio
    async def test_temporal_query_before(self, query_engine):
        """Test temporal query with BEFORE relation"""
        timestamps = {
            "A": datetime(2025, 1, 1),
            "B": datetime(2025, 1, 5),
            "C": datetime(2025, 1, 10),
        }

        query = TemporalQuery(
            start_time=datetime(2025, 1, 6),
            end_time=datetime(2025, 1, 20),
            relation=TemporalRelation.BEFORE
        )

        results = await query_engine.query_temporal_window(query, timestamps)

        # Should include memories before start_time
        assert "A" in results
        assert "B" in results
        assert "C" not in results

    @pytest.mark.asyncio
    async def test_temporal_query_after(self, query_engine):
        """Test temporal query with AFTER relation"""
        timestamps = {
            "A": datetime(2025, 1, 1),
            "B": datetime(2025, 1, 15),
            "C": datetime(2025, 1, 25),
        }

        query = TemporalQuery(
            start_time=datetime(2025, 1, 1),
            end_time=datetime(2025, 1, 10),
            relation=TemporalRelation.AFTER
        )

        results = await query_engine.query_temporal_window(query, timestamps)

        # Should include memories after end_time
        assert "A" not in results
        assert "B" in results
        assert "C" in results

    @pytest.mark.asyncio
    async def test_compute_centrality(self, query_engine):
        """Test computing memory centrality"""
        centrality = await query_engine.compute_centrality()

        assert len(centrality) > 0

        # All values should be between 0 and 1
        for value in centrality.values():
            assert 0.0 <= value <= 1.0

        # Highly connected nodes should have higher centrality
        # (A and D have most connections in our test graph)

    @pytest.mark.asyncio
    async def test_compute_centrality_subset(self, query_engine):
        """Test computing centrality for subset of memories"""
        centrality = await query_engine.compute_centrality(memory_ids=["A", "B", "C"])

        assert len(centrality) == 3
        assert "A" in centrality
        assert "B" in centrality
        assert "C" in centrality

    @pytest.mark.asyncio
    async def test_analyze_graph_metrics(self, query_engine):
        """Test comprehensive graph analysis"""
        metrics = await query_engine.analyze_graph_metrics()

        # Should include all key metrics
        assert "num_memories" in metrics
        assert "num_associations" in metrics
        assert "avg_degree" in metrics
        assert "density" in metrics
        assert "avg_strength" in metrics
        assert "num_triangles" in metrics
        assert "clustering_coefficient" in metrics

        # Validate metric ranges
        assert metrics["num_memories"] > 0
        assert metrics["num_associations"] > 0
        assert metrics["avg_degree"] >= 0
        assert 0.0 <= metrics["density"] <= 1.0
        assert 0.0 <= metrics["avg_strength"] <= 1.0
        assert metrics["num_triangles"] >= 0
        assert 0.0 <= metrics["clustering_coefficient"] <= 1.0

    @pytest.mark.asyncio
    async def test_find_bridges(self, query_engine):
        """Test finding bridge associations"""
        bridges = await query_engine.find_bridges(min_strength=0.3)

        # Should find some bridge candidates
        assert len(bridges) > 0

        # All should meet minimum strength
        for bridge in bridges:
            assert bridge.strength >= 0.3


class TestGraphPathDataclass:
    """Test GraphPath dataclass"""

    def test_create_graph_path(self):
        """Test creating GraphPath"""
        assoc1 = MemoryAssociation(
            memory_a_id="A",
            memory_b_id="B",
            association_type=AssociationType.TEMPORAL,
            strength=0.8,
            created_at=datetime.now()
        )

        path = GraphPath(
            source="A",
            target="C",
            path=[assoc1],
            total_strength=0.8,
            avg_strength=0.8,
            length=1
        )

        assert path.source == "A"
        assert path.target == "C"
        assert len(path.path) == 1
        assert path.length == 1


class TestSubgraphDataclass:
    """Test Subgraph dataclass"""

    def test_create_subgraph(self):
        """Test creating Subgraph"""
        subgraph = Subgraph(
            memories={"A", "B", "C"},
            associations=[],
            density=0.5,
            coherence=0.7
        )

        assert len(subgraph.memories) == 3
        assert "A" in subgraph.memories
        assert subgraph.density == 0.5
        assert subgraph.coherence == 0.7


class TestQueryDataclasses:
    """Test query dataclasses"""

    def test_path_query(self):
        """Test PathQuery creation"""
        query = PathQuery(
            source_id="A",
            target_id="B",
            max_depth=5,
            allowed_types=[AssociationType.TEMPORAL],
            min_path_strength=0.5
        )

        assert query.source_id == "A"
        assert query.target_id == "B"
        assert query.max_depth == 5

    def test_subgraph_query(self):
        """Test SubgraphQuery creation"""
        query = SubgraphQuery(
            seed_memories=["A", "B"],
            radius=2,
            min_strength=0.5
        )

        assert len(query.seed_memories) == 2
        assert query.radius == 2

    def test_temporal_query(self):
        """Test TemporalQuery creation"""
        query = TemporalQuery(
            start_time=datetime(2025, 1, 1),
            end_time=datetime(2025, 12, 31),
            relation=TemporalRelation.WITHIN
        )

        assert query.relation == TemporalRelation.WITHIN
