"""
Integration tests for graph query system (Option D)
Tests memory association network with graph query engine
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from src.memory.association_network import (
    AssociationNetwork,
    AssociationType,
    MemoryAssociation
)
from src.memory.graph_query import (
    MemoryGraphQuery,
    PathQuery,
    SubgraphQuery,
    TemporalQuery,
    TemporalRelation
)


class TestGraphQueryIntegration:
    """Test complete graph query workflows"""

    @pytest.fixture
    async def complex_network(self):
        """Create a complex test network"""
        network = AssociationNetwork()

        # Create a network with multiple clusters
        # Cluster 1: Science (A-E)
        await network.create_association("physics_A", "physics_B", AssociationType.THEMATIC, 0.9)
        await network.create_association("physics_B", "physics_C", AssociationType.CAUSAL, 0.8)
        await network.create_association("physics_C", "physics_D", AssociationType.SEMANTIC, 0.7)
        await network.create_association("physics_D", "physics_E", AssociationType.TEMPORAL, 0.6)

        # Cluster 2: Art (F-J)
        await network.create_association("art_F", "art_G", AssociationType.EMOTIONAL, 0.85)
        await network.create_association("art_G", "art_H", AssociationType.THEMATIC, 0.75)
        await network.create_association("art_H", "art_I", AssociationType.CONTEXTUAL, 0.65)
        await network.create_association("art_I", "art_J", AssociationType.SEMANTIC, 0.55)

        # Bridge between clusters
        await network.create_association("physics_C", "art_G", AssociationType.CONTRASTING, 0.5)

        # Create some triangles
        await network.create_association("physics_A", "physics_C", AssociationType.SEMANTIC, 0.7)
        await network.create_association("art_F", "art_H", AssociationType.SEMANTIC, 0.6)

        return network

    @pytest.fixture
    async def query_engine(self, complex_network):
        return MemoryGraphQuery(complex_network)

    @pytest.mark.asyncio
    async def test_cross_cluster_path_finding(self, query_engine):
        """Test finding paths between different clusters"""
        query = PathQuery(
            source_id="physics_A",
            target_id="art_J",
            max_depth=10
        )

        paths = await query_engine.find_all_paths(query)

        # Should find path through the bridge
        assert len(paths) > 0

        # Verify path goes through both clusters
        for path in paths:
            memory_ids = [path.source]
            for assoc in path.path:
                next_id = assoc.memory_b_id if assoc.memory_a_id == memory_ids[-1] else assoc.memory_a_id
                memory_ids.append(next_id)

            # Should have physics and art memories
            has_physics = any("physics" in mid for mid in memory_ids)
            has_art = any("art" in mid for mid in memory_ids)
            assert has_physics and has_art

    @pytest.mark.asyncio
    async def test_cluster_subgraph_extraction(self, query_engine):
        """Test extracting cohesive cluster"""
        query = SubgraphQuery(
            seed_memories=["physics_A", "physics_B"],
            radius=3,
            min_strength=0.5
        )

        subgraph = await query_engine.extract_subgraph(query)

        # Should include most of physics cluster
        assert "physics_A" in subgraph.memories
        assert "physics_B" in subgraph.memories
        assert "physics_C" in subgraph.memories
        assert "physics_D" in subgraph.memories

        # Check coherence
        assert subgraph.coherence > 0.6  # Should be high for cluster

    @pytest.mark.asyncio
    async def test_triangle_detection_in_network(self, query_engine):
        """Test detecting triangular patterns"""
        triangles = await query_engine.find_triangles(min_strength=0.5)

        # Should find at least the physics triangle
        assert len(triangles) > 0

        # Verify triangle contains expected memories
        physics_triangle = [t for t in triangles if all("physics" in m for m in t)]
        assert len(physics_triangle) > 0

    @pytest.mark.asyncio
    async def test_centrality_identifies_hubs(self, query_engine):
        """Test centrality computation identifies hub nodes"""
        centrality = await query_engine.compute_centrality()

        # physics_C and art_G should have high centrality (they're hubs)
        assert centrality["physics_C"] > centrality.get("physics_E", 0)
        assert centrality["art_G"] > centrality.get("art_J", 0)

    @pytest.mark.asyncio
    async def test_bridge_detection(self, query_engine):
        """Test detecting bridge between clusters"""
        bridges = await query_engine.find_bridges(min_strength=0.3)

        # Should find the physics_C <-> art_G bridge
        bridge_ids = {(b.memory_a_id, b.memory_b_id) for b in bridges}

        # Look for the bridge in either direction
        has_bridge = (
            ("physics_C", "art_G") in bridge_ids or
            ("art_G", "physics_C") in bridge_ids
        )
        assert has_bridge

    @pytest.mark.asyncio
    async def test_comprehensive_metrics(self, query_engine):
        """Test comprehensive graph analysis"""
        metrics = await query_engine.analyze_graph_metrics()

        assert metrics["num_memories"] >= 10  # We created 10+ memories
        assert metrics["num_associations"] >= 12  # We created 12+ associations
        assert 0 < metrics["density"] < 1
        assert 0 < metrics["avg_strength"] <= 1
        assert metrics["num_triangles"] >= 0


class TestTemporalGraphQueries:
    """Test temporal queries on memory graph"""

    @pytest.fixture
    async def temporal_network(self):
        """Create network with temporal data"""
        network = AssociationNetwork()

        # Create memories with implied temporal ordering
        await network.create_association("event_1", "event_2", AssociationType.TEMPORAL, 0.8)
        await network.create_association("event_2", "event_3", AssociationType.TEMPORAL, 0.7)
        await network.create_association("event_3", "event_4", AssociationType.TEMPORAL, 0.6)
        await network.create_association("event_1", "event_3", AssociationType.CAUSAL, 0.5)

        return network

    @pytest.fixture
    async def query_engine(self, temporal_network):
        return MemoryGraphQuery(temporal_network)

    @pytest.mark.asyncio
    async def test_temporal_window_query(self, query_engine):
        """Test querying memories within time window"""
        # Create timestamp mapping
        base_time = datetime(2025, 1, 1, 12, 0)
        timestamps = {
            "event_1": base_time,
            "event_2": base_time + timedelta(hours=1),
            "event_3": base_time + timedelta(hours=2),
            "event_4": base_time + timedelta(hours=3),
        }

        query = TemporalQuery(
            start_time=base_time,
            end_time=base_time + timedelta(hours=2, minutes=30),
            relation=TemporalRelation.WITHIN
        )

        results = await query_engine.query_temporal_window(query, timestamps)

        # Should include events 1, 2, 3 but not 4
        assert "event_1" in results
        assert "event_2" in results
        assert "event_3" in results
        assert "event_4" not in results

    @pytest.mark.asyncio
    async def test_temporal_path_strength(self, query_engine):
        """Test temporal path strength calculation"""
        query = PathQuery(
            source_id="event_1",
            target_id="event_4",
            max_depth=5,
            allowed_types=[AssociationType.TEMPORAL]
        )

        paths = await query_engine.find_all_paths(query)

        # Should find temporal path
        assert len(paths) > 0

        # Path strength should be product of individual strengths
        for path in paths:
            expected_strength = 1.0
            for assoc in path.path:
                expected_strength *= assoc.strength

            assert abs(path.total_strength - expected_strength) < 0.001


class TestGraphQueryPerformance:
    """Test performance characteristics of graph queries"""

    @pytest.fixture
    async def large_network(self):
        """Create larger network for performance testing"""
        network = AssociationNetwork()

        # Create 50 memories in chain
        for i in range(49):
            await network.create_association(
                f"mem_{i}",
                f"mem_{i+1}",
                AssociationType.TEMPORAL,
                0.8 - (i * 0.01)  # Varying strength
            )

        # Create some cross-connections
        for i in range(0, 49, 5):
            if i + 10 < 50:
                await network.create_association(
                    f"mem_{i}",
                    f"mem_{i+10}",
                    AssociationType.SEMANTIC,
                    0.6
                )

        return network

    @pytest.fixture
    async def query_engine(self, large_network):
        return MemoryGraphQuery(large_network)

    @pytest.mark.asyncio
    async def test_shortest_path_performance(self, query_engine):
        """Test shortest path is reasonably fast"""
        import time

        query = PathQuery(
            source_id="mem_0",
            target_id="mem_40",
            max_depth=50
        )

        start = time.time()
        path = await query_engine.find_shortest_path(query)
        elapsed = time.time() - start

        assert path is not None
        assert elapsed < 0.1  # Should complete in < 100ms

    @pytest.mark.asyncio
    async def test_subgraph_extraction_performance(self, query_engine):
        """Test subgraph extraction is reasonably fast"""
        import time

        query = SubgraphQuery(
            seed_memories=["mem_20", "mem_21"],
            radius=5,
            min_strength=0.5
        )

        start = time.time()
        subgraph = await query_engine.extract_subgraph(query)
        elapsed = time.time() - start

        assert len(subgraph.memories) > 0
        assert elapsed < 0.1  # Should complete in < 100ms

    @pytest.mark.asyncio
    async def test_graph_metrics_performance(self, query_engine):
        """Test graph metrics computation is reasonable"""
        import time

        start = time.time()
        metrics = await query_engine.analyze_graph_metrics()
        elapsed = time.time() - start

        assert metrics["num_memories"] > 0
        assert elapsed < 0.5  # Should complete in < 500ms


class TestRealWorldScenarios:
    """Test realistic usage scenarios"""

    @pytest.fixture
    async def knowledge_network(self):
        """Create network representing knowledge domain"""
        network = AssociationNetwork()

        # Programming concepts
        await network.create_association("python", "functions", AssociationType.SEMANTIC, 0.9)
        await network.create_association("functions", "recursion", AssociationType.THEMATIC, 0.8)
        await network.create_association("recursion", "algorithms", AssociationType.SEMANTIC, 0.7)

        # Web development
        await network.create_association("html", "css", AssociationType.CONTEXTUAL, 0.9)
        await network.create_association("css", "javascript", AssociationType.CONTEXTUAL, 0.85)
        await network.create_association("javascript", "react", AssociationType.SEMANTIC, 0.8)

        # Connections between domains
        await network.create_association("python", "javascript", AssociationType.CONTRASTING, 0.6)
        await network.create_association("algorithms", "react", AssociationType.THEMATIC, 0.5)

        return network

    @pytest.fixture
    async def query_engine(self, knowledge_network):
        return MemoryGraphQuery(knowledge_network)

    @pytest.mark.asyncio
    async def test_find_learning_path(self, query_engine):
        """Test finding learning path between concepts"""
        query = PathQuery(
            source_id="html",
            target_id="algorithms",
            max_depth=8
        )

        paths = await query_engine.find_all_paths(query)

        # Should find path connecting web dev to algorithms
        assert len(paths) > 0

        # Shortest path should be reasonable
        shortest = await query_engine.find_shortest_path(query)
        assert shortest is not None
        assert shortest.length <= 5  # Not too long

    @pytest.mark.asyncio
    async def test_extract_topic_cluster(self, query_engine):
        """Test extracting related topic cluster"""
        query = SubgraphQuery(
            seed_memories=["html", "css"],
            radius=2,
            min_strength=0.7
        )

        subgraph = await query_engine.extract_subgraph(query)

        # Should include web dev cluster
        assert "html" in subgraph.memories
        assert "css" in subgraph.memories
        assert "javascript" in subgraph.memories

        # High coherence for focused topic
        assert subgraph.coherence >= 0.7

    @pytest.mark.asyncio
    async def test_find_concept_connections(self, query_engine):
        """Test finding how concepts relate"""
        query = PathQuery(
            source_id="python",
            target_id="react",
            max_depth=6
        )

        paths = await query_engine.find_all_paths(query)

        # Should find multiple connection paths
        assert len(paths) >= 2  # Direct and indirect paths

        # Paths should show different relationship types
        all_types = set()
        for path in paths:
            for assoc in path.path:
                all_types.add(assoc.association_type)

        assert len(all_types) >= 2  # Multiple relationship types
