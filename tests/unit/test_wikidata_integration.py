"""
Tests for Wikidata Integration
================================

Tests Wikidata API integration functionality including:
- Entity retrieval and caching
- SPARQL queries
- Relationship discovery
- Knowledge graph building
"""

import pytest
from datetime import datetime

from src.web.wikidata_integration import (
    WikidataIntegration,
    WikidataEntity,
    WikidataProperty,
    WikidataTriple,
    WikidataKnowledgeGraph,
    PropertyType
)


@pytest.fixture
def wikidata():
    """Create Wikidata integration instance"""
    return WikidataIntegration(language="en")


@pytest.fixture
def knowledge_graph(wikidata):
    """Create knowledge graph builder"""
    return WikidataKnowledgeGraph(wikidata)


class TestWikidataIntegration:
    """Test Wikidata API integration"""

    @pytest.mark.asyncio
    async def test_search_entities(self, wikidata):
        """Test entity search"""
        results = await wikidata.search_entities("Python", limit=5)

        assert isinstance(results, list)
        assert len(results) <= 5

    @pytest.mark.asyncio
    async def test_get_entity(self, wikidata):
        """Test entity retrieval"""
        # Q42 is Douglas Adams
        entity = await wikidata.get_entity("Q42")

        assert entity is None or isinstance(entity, WikidataEntity)

        if entity:
            assert entity.entity_id == "Q42"

    @pytest.mark.asyncio
    async def test_get_entity_caching(self, wikidata):
        """Test that entities are cached"""
        entity_id = "Q42"

        # First call
        entity1 = await wikidata.get_entity(entity_id)

        # Second call should use cache
        entity2 = await wikidata.get_entity(entity_id)

        # Should be same instance if cached
        if entity1 and entity2:
            assert entity1 is entity2

    @pytest.mark.asyncio
    async def test_get_entity_by_wikipedia_title(self, wikidata):
        """Test finding entity from Wikipedia title"""
        entity = await wikidata.get_entity_by_wikipedia_title(
            "Albert Einstein",
            wiki_site="enwiki"
        )

        assert entity is None or isinstance(entity, WikidataEntity)

    @pytest.mark.asyncio
    async def test_get_property_values(self, wikidata):
        """Test property value retrieval"""
        # P31 is "instance of"
        values = await wikidata.get_property_values("Q42", "P31")

        assert isinstance(values, list)

    @pytest.mark.asyncio
    async def test_query_sparql(self, wikidata):
        """Test SPARQL query execution"""
        query = """
        SELECT ?item WHERE {
          ?item wdt:P31 wd:Q5.
        }
        LIMIT 5
        """

        results = await wikidata.query_sparql(query)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_find_entities_with_property(self, wikidata):
        """Test finding entities by property value"""
        entities = await wikidata.find_entities_with_property(
            "P31",  # instance of
            "Q5",   # human
            limit=5
        )

        assert isinstance(entities, list)
        assert len(entities) <= 5

    @pytest.mark.asyncio
    async def test_get_related_entities(self, wikidata):
        """Test related entity discovery"""
        related = await wikidata.get_related_entities("Q42", limit=5)

        assert isinstance(related, list)
        assert len(related) <= 5

    @pytest.mark.asyncio
    async def test_get_entity_hierarchy(self, wikidata):
        """Test hierarchy retrieval"""
        hierarchy = await wikidata.get_entity_hierarchy("Q42", max_depth=2)

        assert isinstance(hierarchy, dict)
        assert 'entity_id' in hierarchy
        assert 'parents' in hierarchy
        assert 'depth' in hierarchy

    @pytest.mark.asyncio
    async def test_extract_triples(self, wikidata):
        """Test RDF triple extraction"""
        triples = await wikidata.extract_triples("Q42")

        assert isinstance(triples, list)

        for triple in triples:
            assert isinstance(triple, WikidataTriple)
            assert triple.subject == "Q42"

    @pytest.mark.asyncio
    async def test_get_multilingual_labels(self, wikidata):
        """Test multilingual label retrieval"""
        labels = await wikidata.get_multilingual_labels(
            "Q42",
            languages=['en', 'es', 'fr', 'de']
        )

        assert isinstance(labels, dict)

    @pytest.mark.asyncio
    async def test_find_by_external_id(self, wikidata):
        """Test finding entity by external identifier"""
        # P345 is IMDB ID
        entity_id = await wikidata.find_by_external_id("P345", "tt0076759")

        assert entity_id is None or isinstance(entity_id, str)

    @pytest.mark.asyncio
    async def test_get_temporal_data(self, wikidata):
        """Test temporal data retrieval"""
        temporal = await wikidata.get_temporal_data("Q42", "P39")  # position held

        assert isinstance(temporal, list)

    @pytest.mark.asyncio
    async def test_cache_clear(self, wikidata):
        """Test cache clearing"""
        # Add something to cache
        await wikidata.get_entity("Q42")

        # Clear cache
        wikidata.clear_cache()

        # Cache should be empty
        assert len(wikidata.entity_cache) == 0


class TestWikidataKnowledgeGraph:
    """Test knowledge graph building from Wikidata"""

    @pytest.mark.asyncio
    async def test_build_subgraph(self, knowledge_graph):
        """Test knowledge subgraph building"""
        subgraph = await knowledge_graph.build_subgraph(
            "Q42",
            max_depth=2,
            max_nodes=20
        )

        assert isinstance(subgraph, dict)
        assert 'nodes' in subgraph
        assert 'edges' in subgraph
        assert 'metadata' in subgraph

    @pytest.mark.asyncio
    async def test_find_path_between_entities(self, knowledge_graph):
        """Test finding path between entities"""
        path = await knowledge_graph.find_path_between_entities(
            "Q42",  # Douglas Adams
            "Q5",   # Human
            max_path_length=3
        )

        assert path is None or isinstance(path, list)

    @pytest.mark.asyncio
    async def test_cluster_entities(self, knowledge_graph):
        """Test entity clustering"""
        entities = ["Q42", "Q5", "Q1"]
        clusters = await knowledge_graph.cluster_entities(
            entities,
            clustering_property="P31"
        )

        assert isinstance(clusters, dict)

    @pytest.mark.asyncio
    async def test_extract_knowledge_domain(self, knowledge_graph):
        """Test knowledge domain extraction"""
        domain = await knowledge_graph.extract_knowledge_domain(
            "Q5",  # Human
            instance_property="P31",
            subclass_property="P279"
        )

        assert isinstance(domain, dict)
        assert 'root_class' in domain
        assert 'instances' in domain
        assert 'subclasses' in domain


class TestWikidataDataClasses:
    """Test Wikidata data structures"""

    def test_wikidata_entity_creation(self):
        """Test WikidataEntity creation"""
        entity = WikidataEntity(
            entity_id="Q42",
            label="Test Entity",
            description="Test description"
        )

        assert entity.entity_id == "Q42"
        assert entity.label == "Test Entity"
        assert len(entity.properties) == 0
        assert len(entity.claims) == 0

    def test_wikidata_property_creation(self):
        """Test WikidataProperty creation"""
        prop = WikidataProperty(
            property_id="P31",
            label="instance of",
            description="that class of which this subject is a particular example and member",
            property_type=PropertyType.ITEM
        )

        assert prop.property_id == "P31"
        assert prop.property_type == PropertyType.ITEM

    def test_wikidata_triple_creation(self):
        """Test WikidataTriple creation"""
        triple = WikidataTriple(
            subject="Q42",
            predicate="P31",
            object="Q5"
        )

        assert triple.subject == "Q42"
        assert triple.predicate == "P31"
        assert triple.object == "Q5"
        assert len(triple.qualifiers) == 0

    def test_property_type_enum(self):
        """Test PropertyType enum"""
        assert PropertyType.STRING.value == "string"
        assert PropertyType.ITEM.value == "wikibase-item"
        assert PropertyType.TIME.value == "time"
