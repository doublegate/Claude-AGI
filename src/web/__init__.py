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
from .news_integration import (
    NewsIntegration,
    NewsArticle,
    NewsCategory,
    NewsSentiment
)
from .weather_integration import (
    WeatherIntegration,
    WeatherData,
    WeatherForecast,
    WeatherCondition
)
from .arxiv_integration import (
    ArxivIntegration,
    ArxivPaper,
    ArxivCategory,
    Author
)

__all__ = [
    'WebExplorer', 'WebService',
    'FactVerificationSystem', 'FactStatus', 'CredibilityLevel',
    'WebContentProcessor', 'InformationSynthesizer', 'ContentType',
    'WikipediaIntegration', 'WikipediaArticle', 'WikiSearchResult',
    'WikipediaKnowledgeExtractor', 'ContentFormat',
    'WikidataIntegration', 'WikidataEntity', 'WikidataProperty',
    'WikidataTriple', 'WikidataKnowledgeGraph', 'PropertyType',
    'UnifiedKnowledgeAPI', 'UnifiedKnowledgeResult', 'QueryType',
    'NewsIntegration', 'NewsArticle', 'NewsCategory', 'NewsSentiment',
    'WeatherIntegration', 'WeatherData', 'WeatherForecast', 'WeatherCondition',
    'ArxivIntegration', 'ArxivPaper', 'ArxivCategory', 'Author'
]