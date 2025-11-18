"""
NLP Integration for Enhanced Knowledge Extraction
=================================================

Provides optional spaCy and Transformers integration for advanced
natural language processing capabilities.

Installation:
    pip install spacy transformers sentence-transformers
    python -m spacy download en_core_web_sm

Usage:
    from src.learning.nlp_integration import NLPEnhancedExtractor

    extractor = NLPEnhancedExtractor()
    concepts = await extractor.extract_concepts(text)
"""

import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try to import NLP libraries
try:
    import spacy
    from spacy.tokens import Doc
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available - using pattern-based extraction only")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available - embeddings disabled")


@dataclass
class NLPConcept:
    """Enhanced concept with NLP features"""
    text: str
    lemma: str
    pos_tag: str
    dep_tag: str
    named_entity_type: str
    embedding: Optional[List[float]] = None
    confidence: float = 0.8
    context: str = ""
    related_concepts: List[str] = None

    def __post_init__(self):
        if self.related_concepts is None:
            self.related_concepts = []


@dataclass
class NLPRelationship:
    """Enhanced relationship with NLP features"""
    subject: str
    predicate: str
    object: str
    relation_type: str
    confidence: float
    context: str
    dependency_path: List[str] = None

    def __post_init__(self):
        if self.dependency_path is None:
            self.dependency_path = []


class NLPEnhancedExtractor:
    """
    Enhanced knowledge extractor using spaCy and Transformers.
    Falls back to pattern-based extraction if NLP libraries unavailable.
    """

    def __init__(self, use_embeddings: bool = True):
        """
        Initialize NLP enhanced extractor.

        Args:
            use_embeddings: Whether to compute embeddings (requires sentence-transformers)
        """
        self.use_embeddings = use_embeddings and SENTENCE_TRANSFORMERS_AVAILABLE

        # Load spaCy model if available
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("Loaded spaCy model: en_core_web_sm")
            except OSError:
                logger.warning("spaCy model not found - run: python -m spacy download en_core_web_sm")
                SPACY_AVAILABLE = False

        # Load sentence transformer if available
        self.embedder = None
        if self.use_embeddings:
            try:
                self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded sentence transformer: all-MiniLM-L6-v2")
            except Exception as e:
                logger.warning(f"Failed to load sentence transformer: {e}")
                self.use_embeddings = False

    async def extract_concepts(self, text: str) -> List[NLPConcept]:
        """
        Extract concepts using NLP if available, otherwise pattern-based.

        Args:
            text: Text to analyze

        Returns:
            List of extracted NLP concepts
        """
        if not self.nlp:
            logger.warning("spaCy not available - using pattern-based extraction")
            return self._pattern_based_extraction(text)

        doc = self.nlp(text)
        concepts = []

        # Extract named entities
        for ent in doc.ents:
            concepts.append(NLPConcept(
                text=ent.text,
                lemma=ent.lemma_,
                pos_tag="ENTITY",
                dep_tag="ROOT",
                named_entity_type=ent.label_,
                confidence=0.9,
                context=ent.sent.text
            ))

        # Extract noun chunks as concepts
        for chunk in doc.noun_chunks:
            # Skip if already in entities
            if any(ent.text == chunk.text for ent in doc.ents):
                continue

            concepts.append(NLPConcept(
                text=chunk.text,
                lemma=chunk.lemma_,
                pos_tag=chunk.root.pos_,
                dep_tag=chunk.root.dep_,
                named_entity_type="",
                confidence=0.7,
                context=chunk.sent.text
            ))

        # Extract key verbs as action concepts
        for token in doc:
            if token.pos_ == "VERB" and token.dep_ in ["ROOT", "ccomp", "xcomp"]:
                concepts.append(NLPConcept(
                    text=token.text,
                    lemma=token.lemma_,
                    pos_tag=token.pos_,
                    dep_tag=token.dep_,
                    named_entity_type="",
                    confidence=0.6,
                    context=token.sent.text
                ))

        # Compute embeddings if enabled
        if self.use_embeddings and self.embedder:
            concept_texts = [c.text for c in concepts]
            if concept_texts:
                embeddings = self.embedder.encode(concept_texts)
                for concept, embedding in zip(concepts, embeddings):
                    concept.embedding = embedding.tolist()

        # Deduplicate by text
        seen = set()
        unique_concepts = []
        for concept in concepts:
            if concept.text.lower() not in seen:
                seen.add(concept.text.lower())
                unique_concepts.append(concept)

        return unique_concepts

    async def extract_relationships(self, text: str, known_concepts: Optional[Set[str]] = None) -> List[NLPRelationship]:
        """
        Extract relationships using dependency parsing.

        Args:
            text: Text to analyze
            known_concepts: Set of known concept names to filter by

        Returns:
            List of extracted relationships
        """
        if not self.nlp:
            logger.warning("spaCy not available - using pattern-based extraction")
            return []

        doc = self.nlp(text)
        relationships = []

        for sent in doc.sents:
            # Find subject-verb-object triples
            for token in sent:
                if token.dep_ in ["nsubj", "nsubjpass"]:
                    subject = token.text
                    verb = token.head

                    # Find object
                    for child in verb.children:
                        if child.dep_ in ["dobj", "attr", "prep"]:
                            obj = child.text

                            # Determine relationship type
                            rel_type = self._classify_relationship(verb.lemma_, verb.dep_)

                            # Create relationship
                            relationships.append(NLPRelationship(
                                subject=subject,
                                predicate=verb.text,
                                object=obj,
                                relation_type=rel_type,
                                confidence=0.8,
                                context=sent.text,
                                dependency_path=[token.dep_, verb.dep_, child.dep_]
                            ))

        return relationships

    def _classify_relationship(self, verb_lemma: str, dep: str) -> str:
        """Classify relationship type based on verb"""
        # Causal verbs
        if verb_lemma in ["cause", "lead", "result", "create", "produce"]:
            return "causes"
        # Requirement verbs
        elif verb_lemma in ["require", "need", "depend"]:
            return "requires"
        # Composition verbs
        elif verb_lemma in ["contain", "include", "comprise"]:
            return "part_of"
        # Similarity verbs
        elif verb_lemma in ["resemble", "like", "similar"]:
            return "similar_to"
        # Default
        else:
            return "related_to"

    def _pattern_based_extraction(self, text: str) -> List[NLPConcept]:
        """Fallback pattern-based extraction"""
        import re

        concepts = []

        # Extract capitalized noun phrases (likely named entities)
        pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        matches = re.finditer(pattern, text)

        for match in matches:
            concepts.append(NLPConcept(
                text=match.group(),
                lemma=match.group().lower(),
                pos_tag="NOUN",
                dep_tag="ROOT",
                named_entity_type="UNKNOWN",
                confidence=0.5,
                context=text[max(0, match.start()-50):min(len(text), match.end()+50)]
            ))

        return concepts

    async def compute_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Compute semantic similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        if not self.use_embeddings or not self.embedder:
            logger.warning("Embeddings not available - using simple overlap")
            # Fallback to word overlap
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            if not words1 or not words2:
                return 0.0
            return len(words1 & words2) / len(words1 | words2)

        # Compute embeddings
        embeddings = self.embedder.encode([text1, text2])

        # Compute cosine similarity
        from numpy import dot
        from numpy.linalg import norm

        similarity = dot(embeddings[0], embeddings[1]) / (norm(embeddings[0]) * norm(embeddings[1]))
        return float(similarity)

    def get_capabilities(self) -> Dict[str, bool]:
        """Get available NLP capabilities"""
        return {
            "spacy": SPACY_AVAILABLE and self.nlp is not None,
            "embeddings": self.use_embeddings and self.embedder is not None,
            "named_entity_recognition": SPACY_AVAILABLE and self.nlp is not None,
            "dependency_parsing": SPACY_AVAILABLE and self.nlp is not None,
            "semantic_similarity": self.use_embeddings and self.embedder is not None,
        }


async def demo():
    """Demo NLP integration capabilities"""
    print("NLP Integration Demo")
    print("=" * 70)

    extractor = NLPEnhancedExtractor()

    # Show capabilities
    capabilities = extractor.get_capabilities()
    print("\nAvailable Capabilities:")
    for capability, available in capabilities.items():
        status = "✅" if available else "❌"
        print(f"  {status} {capability}")

    # Test extraction
    text = """
    Machine learning is a subset of artificial intelligence. Neural networks
    enable deep learning. Python is the most popular language for AI development.
    TensorFlow and PyTorch are widely used frameworks.
    """

    print("\nExtracting concepts from text...")
    concepts = await extractor.extract_concepts(text)

    print(f"\nExtracted {len(concepts)} concepts:")
    for concept in concepts[:10]:  # Show first 10
        print(f"  - {concept.text} ({concept.named_entity_type or concept.pos_tag})")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo())
