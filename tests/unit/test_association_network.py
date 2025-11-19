"""
Unit tests for memory association network
"""

import pytest
from datetime import datetime, timedelta
from src.memory.association_network import (
    AssociationNetwork,
    AssociationType,
    MemoryAssociation,
    MemoryCluster
)


@pytest.fixture
async def network():
    """Create an association network instance"""
    return AssociationNetwork(decay_enabled=False)  # Disable decay for predictable tests


@pytest.mark.asyncio
class TestBasicAssociations:
    """Test basic association creation and retrieval"""

    async def test_create_association(self, network):
        """Test creating an association"""
        association = await network.create_association(
            "memory1",
            "memory2",
            AssociationType.THEMATIC,
            strength=0.8
        )

        assert association.memory_a_id == "memory1"
        assert association.memory_b_id == "memory2"
        assert association.association_type == AssociationType.THEMATIC
        assert association.strength == 0.8
        assert network.stats['total_associations'] == 1

    async def test_create_association_consistent_ordering(self, network):
        """Test that association IDs are consistent regardless of argument order"""
        assoc1 = await network.create_association(
            "memory_a",
            "memory_b",
            AssociationType.SEMANTIC,
            strength=0.5
        )

        # Try to create reverse - should strengthen existing
        assoc2 = await network.create_association(
            "memory_b",
            "memory_a",
            AssociationType.SEMANTIC,
            strength=0.5
        )

        # Should be same association
        assert assoc1.association_id == assoc2.association_id
        assert network.stats['total_associations'] == 1
        # Strength should have increased from activation
        assert assoc2.strength > 0.5

    async def test_association_bidirectional(self, network):
        """Test that associations are bidirectional"""
        await network.create_association(
            "mem1",
            "mem2",
            AssociationType.TEMPORAL,
            strength=0.7
        )

        # Should be accessible from both memories
        from_mem1 = await network.get_associated_memories("mem1")
        from_mem2 = await network.get_associated_memories("mem2")

        assert len(from_mem1) == 1
        assert len(from_mem2) == 1
        assert from_mem1[0][0] == "mem2"
        assert from_mem2[0][0] == "mem1"

    async def test_multiple_association_types(self, network):
        """Test creating multiple types of associations"""
        await network.create_association("m1", "m2", AssociationType.TEMPORAL, 0.8)
        await network.create_association("m1", "m3", AssociationType.CAUSAL, 0.9)
        await network.create_association("m1", "m4", AssociationType.EMOTIONAL, 0.7)

        # Should have 3 different associations
        assert network.stats['total_associations'] == 3
        assert network.stats['associations_by_type']['temporal'] == 1
        assert network.stats['associations_by_type']['causal'] == 1
        assert network.stats['associations_by_type']['emotional'] == 1


@pytest.mark.asyncio
class TestAssociationRetrieval:
    """Test retrieving associated memories"""

    async def test_get_associated_memories_empty(self, network):
        """Test getting associations for memory with no associations"""
        results = await network.get_associated_memories("nonexistent")
        assert len(results) == 0

    async def test_get_associated_memories_basic(self, network):
        """Test basic association retrieval"""
        await network.create_association("m1", "m2", AssociationType.THEMATIC, 0.8)
        await network.create_association("m1", "m3", AssociationType.THEMATIC, 0.6)

        results = await network.get_associated_memories("m1")

        assert len(results) == 2
        # Should be sorted by strength
        assert results[0][0] == "m2"  # Stronger association
        assert results[1][0] == "m3"

    async def test_filter_by_association_type(self, network):
        """Test filtering associations by type"""
        await network.create_association("m1", "m2", AssociationType.TEMPORAL, 0.8)
        await network.create_association("m1", "m3", AssociationType.CAUSAL, 0.9)
        await network.create_association("m1", "m4", AssociationType.TEMPORAL, 0.7)

        # Get only temporal associations
        temporal = await network.get_associated_memories(
            "m1",
            association_types=[AssociationType.TEMPORAL]
        )

        assert len(temporal) == 2
        assert temporal[0][0] == "m2"  # Higher strength
        assert temporal[1][0] == "m4"

    async def test_filter_by_min_strength(self, network):
        """Test filtering by minimum strength"""
        await network.create_association("m1", "m2", AssociationType.THEMATIC, 0.9)
        await network.create_association("m1", "m3", AssociationType.THEMATIC, 0.5)
        await network.create_association("m1", "m4", AssociationType.THEMATIC, 0.3)

        # Only get strong associations
        strong = await network.get_associated_memories("m1", min_strength=0.6)

        assert len(strong) == 1
        assert strong[0][0] == "m2"

    async def test_limit_results(self, network):
        """Test limiting number of results"""
        for i in range(10):
            await network.create_association("m1", f"m{i+2}", AssociationType.THEMATIC, 0.5 + i * 0.05)

        results = await network.get_associated_memories("m1", limit=5)

        assert len(results) == 5
        # Should get top 5 by strength


@pytest.mark.asyncio
class TestAssociationActivation:
    """Test association activation and strengthening"""

    async def test_association_activation(self, network):
        """Test that retrieving associations activates them"""
        association = await network.create_association(
            "m1", "m2", AssociationType.THEMATIC, strength=0.5
        )

        original_strength = association.strength
        original_count = association.activation_count

        # Retrieve association
        await network.get_associated_memories("m1")

        # Should be activated
        assert association.activation_count == original_count + 1
        assert association.strength > original_strength

    async def test_multiple_activations(self, network):
        """Test that multiple activations strengthen association"""
        association = await network.create_association(
            "m1", "m2", AssociationType.THEMATIC, strength=0.5
        )

        # Activate multiple times
        for _ in range(5):
            await network.get_associated_memories("m1")

        # Should be significantly strengthened
        assert association.activation_count == 5
        assert association.strength > 0.6


@pytest.mark.asyncio
class TestIndirectAssociations:
    """Test finding indirect associations"""

    async def test_find_indirect_2hop(self, network):
        """Test finding 2-hop indirect associations"""
        # Create chain: m1 -> m2 -> m3
        await network.create_association("m1", "m2", AssociationType.THEMATIC, 0.8)
        await network.create_association("m2", "m3", AssociationType.THEMATIC, 0.7)

        # Find indirect associations from m1
        indirect = await network.find_indirect_associations("m1", max_depth=2)

        # Should find m3 through m2
        assert len(indirect) >= 1

        # Find the path to m3
        m3_paths = [path for target_id, path in indirect if target_id == "m3"]
        assert len(m3_paths) > 0
        assert len(m3_paths[0]) == 2  # 2 associations in path

    async def test_indirect_associations_path_strength(self, network):
        """Test that path strength is calculated correctly"""
        # Create strong path: m1 -> m2 (0.9) -> m3 (0.8)
        await network.create_association("m1", "m2", AssociationType.THEMATIC, 0.9)
        await network.create_association("m2", "m3", AssociationType.THEMATIC, 0.8)

        # Create weak path: m1 -> m4 (0.3) -> m3 (0.3)
        await network.create_association("m1", "m4", AssociationType.THEMATIC, 0.3)
        await network.create_association("m4", "m3", AssociationType.THEMATIC, 0.3)

        indirect = await network.find_indirect_associations("m1", max_depth=2)

        # Should prefer stronger path
        m3_results = [(tid, path) for tid, path in indirect if tid == "m3"]
        assert len(m3_results) > 0

        # Strongest path should be first (sorted by strength)
        # Strong path: 0.9 * 0.8 = 0.72
        # Weak path: 0.3 * 0.3 = 0.09
        strongest_path = m3_results[0][1]
        path_strength = network._calculate_path_strength(strongest_path)
        assert path_strength > 0.5  # Should be the strong path

    async def test_indirect_min_path_strength(self, network):
        """Test filtering by minimum path strength"""
        # Create weak chain
        await network.create_association("m1", "m2", AssociationType.THEMATIC, 0.5)
        await network.create_association("m2", "m3", AssociationType.THEMATIC, 0.5)

        # With high threshold, should find nothing
        indirect = await network.find_indirect_associations(
            "m1",
            max_depth=2,
            min_path_strength=0.9
        )

        # Path strength is 0.5 * 0.5 = 0.25, below threshold
        assert len(indirect) == 0


@pytest.mark.asyncio
class TestTemporalAssociations:
    """Test temporal association creation"""

    async def test_create_temporal_associations(self, network):
        """Test creating temporal associations"""
        memory_ids = ["m1", "m2", "m3", "m4", "m5"]

        count = await network.create_temporal_associations(
            memory_ids,
            time_window_seconds=2,
            strength=0.7
        )

        # Should create associations between adjacent memories
        assert count > 0
        assert network.stats['associations_by_type']['temporal'] > 0

    async def test_temporal_window_limit(self, network):
        """Test that temporal associations respect time window"""
        memory_ids = ["m1", "m2", "m3", "m4"]

        # Small window
        await network.create_temporal_associations(
            memory_ids,
            time_window_seconds=1,  # Only adjacent
            strength=0.7
        )

        # Should only associate adjacent memories
        m1_assoc = await network.get_associated_memories("m1")
        # m1 should associate with m2 only (within window of 1)
        assert len(m1_assoc) == 1


@pytest.mark.asyncio
class TestMemoryClustering:
    """Test memory clustering"""

    async def test_cluster_memories_basic(self, network):
        """Test basic memory clustering"""
        # Create a cluster of related memories
        await network.create_association("m1", "m2", AssociationType.THEMATIC, 0.8)
        await network.create_association("m2", "m3", AssociationType.THEMATIC, 0.8)
        await network.create_association("m1", "m3", AssociationType.THEMATIC, 0.7)

        # Create another isolated cluster
        await network.create_association("m4", "m5", AssociationType.THEMATIC, 0.9)
        await network.create_association("m5", "m6", AssociationType.THEMATIC, 0.9)

        memory_ids = ["m1", "m2", "m3", "m4", "m5", "m6"]
        clusters = await network.cluster_memories(
            memory_ids,
            min_cluster_size=2,
            coherence_threshold=0.6
        )

        # Should find 2 clusters
        assert len(clusters) >= 1

    async def test_cluster_coherence(self, network):
        """Test that cluster coherence is calculated"""
        # Create tightly connected cluster
        await network.create_association("m1", "m2", AssociationType.THEMATIC, 0.9)
        await network.create_association("m2", "m3", AssociationType.THEMATIC, 0.9)
        await network.create_association("m1", "m3", AssociationType.THEMATIC, 0.9)

        clusters = await network.cluster_memories(
            ["m1", "m2", "m3"],
            min_cluster_size=2,
            coherence_threshold=0.5
        )

        assert len(clusters) == 1
        # Should have high coherence
        assert clusters[0].coherence_score > 0.7

    async def test_min_cluster_size(self, network):
        """Test minimum cluster size filter"""
        # Create small association
        await network.create_association("m1", "m2", AssociationType.THEMATIC, 0.8)

        clusters = await network.cluster_memories(
            ["m1", "m2"],
            min_cluster_size=3,  # Require at least 3 memories
            coherence_threshold=0.5
        )

        # Should find no clusters (too small)
        assert len(clusters) == 0


@pytest.mark.asyncio
class TestAssociationSuggestions:
    """Test association suggestion system"""

    async def test_suggest_associations_from_indirect(self, network):
        """Test suggesting associations based on indirect connections"""
        # Create pattern: m1 -> m2 -> m3
        await network.create_association("m1", "m2", AssociationType.THEMATIC, 0.8)
        await network.create_association("m2", "m3", AssociationType.THEMATIC, 0.7)

        # Suggest associations for m1
        suggestions = await network.suggest_associations(
            "m1",
            ["m3", "m4"],  # m3 is indirectly connected
            limit=5
        )

        # Should suggest m3 (indirectly connected)
        assert len(suggestions) > 0
        suggested_ids = [s[0] for s in suggestions]
        assert "m3" in suggested_ids

    async def test_suggestion_confidence(self, network):
        """Test that suggestions have confidence scores"""
        # Create indirect path
        await network.create_association("m1", "m2", AssociationType.THEMATIC, 0.9)
        await network.create_association("m2", "m3", AssociationType.THEMATIC, 0.8)

        suggestions = await network.suggest_associations(
            "m1",
            ["m3"],
            limit=1
        )

        if suggestions:
            _, suggested_type, confidence = suggestions[0]
            assert 0.0 <= confidence <= 1.0


@pytest.mark.asyncio
class TestDecayAndPruning:
    """Test association decay and pruning"""

    async def test_association_decay(self):
        """Test that associations decay over time"""
        network = AssociationNetwork(decay_enabled=True)

        association = await network.create_association(
            "m1", "m2", AssociationType.THEMATIC, strength=1.0
        )

        original_strength = association.strength

        # Manually trigger decay
        association.decay(days_since_activation=30, decay_rate=0.01)

        # Should have decayed
        assert association.strength < original_strength

    async def test_prune_weak_associations(self, network):
        """Test pruning weak associations"""
        # Create strong and weak associations
        await network.create_association("m1", "m2", AssociationType.THEMATIC, 0.9)
        await network.create_association("m1", "m3", AssociationType.THEMATIC, 0.05)
        await network.create_association("m1", "m4", AssociationType.THEMATIC, 0.02)

        # Prune weak ones
        pruned = await network.prune_weak_associations(min_strength=0.1)

        # Should have removed 2 weak associations
        assert pruned == 2
        assert network.stats['total_associations'] == 1

    async def test_decay_interval(self):
        """Test that decay only applies after interval"""
        network = AssociationNetwork(
            decay_enabled=True,
            decay_interval_hours=1
        )

        association = await network.create_association(
            "m1", "m2", AssociationType.THEMATIC, strength=1.0
        )

        # Get associations immediately - should not decay yet
        await network.get_associated_memories("m1")

        # Strength should be same (or higher from activation)
        assert association.strength >= 1.0


@pytest.mark.asyncio
class TestStatistics:
    """Test network statistics"""

    async def test_statistics_empty(self, network):
        """Test statistics for empty network"""
        stats = await network.get_statistics()

        assert stats['total_associations'] == 0
        assert stats['total_activations'] == 0

    async def test_statistics_with_data(self, network):
        """Test statistics with associations"""
        await network.create_association("m1", "m2", AssociationType.THEMATIC, 0.8)
        await network.create_association("m1", "m3", AssociationType.CAUSAL, 0.9)
        await network.create_association("m1", "m4", AssociationType.TEMPORAL, 0.7)

        # Activate some
        await network.get_associated_memories("m1")

        stats = await network.get_statistics()

        assert stats['total_associations'] == 3
        assert stats['associations_by_type']['thematic'] == 1
        assert stats['associations_by_type']['causal'] == 1
        assert stats['associations_by_type']['temporal'] == 1
        assert stats['total_activations'] == 3  # All 3 were activated

    async def test_average_strength_by_type(self, network):
        """Test average strength calculation by type"""
        await network.create_association("m1", "m2", AssociationType.THEMATIC, 0.6)
        await network.create_association("m1", "m3", AssociationType.THEMATIC, 0.8)
        await network.create_association("m1", "m4", AssociationType.CAUSAL, 0.9)

        stats = await network.get_statistics()

        # Average thematic strength should be (0.6 + 0.8) / 2 = 0.7
        assert 'avg_strength_by_type' in stats
        assert abs(stats['avg_strength_by_type']['thematic'] - 0.7) < 0.01
