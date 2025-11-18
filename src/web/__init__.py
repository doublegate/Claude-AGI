# web module

from .explorer import WebExplorer
from .web_service import WebService
from .fact_verification import FactVerificationSystem, FactStatus, CredibilityLevel
from .content_processor import WebContentProcessor, InformationSynthesizer, ContentType
from .wikipedia_integration import (
    WikipediaIntegration,
    WikipediaArticle,
    WikiSearchResult,
    WikipediaKnowledgeExtractor,
    ContentFormat
)
from .wikidata_integration import (
    WikidataIntegration,
    WikidataEntity,
    WikidataProperty,
    WikidataTriple,
    WikidataKnowledgeGraph,
    PropertyType
)
from .unified_knowledge_api import (
    UnifiedKnowledgeAPI,
    UnifiedKnowledgeResult,
    QueryType
)

__all__ = [
    'WebExplorer', 'WebService',
    'FactVerificationSystem', 'FactStatus', 'CredibilityLevel',
    'WebContentProcessor', 'InformationSynthesizer', 'ContentType',
    'WikipediaIntegration', 'WikipediaArticle', 'WikiSearchResult',
    'WikipediaKnowledgeExtractor', 'ContentFormat',
    'WikidataIntegration', 'WikidataEntity', 'WikidataProperty',
    'WikidataTriple', 'WikidataKnowledgeGraph', 'PropertyType',
    'UnifiedKnowledgeAPI', 'UnifiedKnowledgeResult', 'QueryType'
]