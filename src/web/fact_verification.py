"""
Fact Verification System
=========================

Verifies facts from web sources using multi-source validation,
credibility assessment, and consistency checking.
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class CredibilityLevel(Enum):
    """Source credibility levels"""
    VERIFIED = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    UNKNOWN = 1


class FactStatus(Enum):
    """Verification status of a fact"""
    VERIFIED = "verified"
    LIKELY_TRUE = "likely_true"
    UNCERTAIN = "uncertain"
    LIKELY_FALSE = "likely_false"
    DEBUNKED = "debunked"


@dataclass
class Source:
    """Information source"""
    url: str
    domain: str
    credibility: CredibilityLevel
    bias_score: float = 0.0  # -1 to 1
    specialty_areas: Set[str] = field(default_factory=set)
    verification_history: List[bool] = field(default_factory=list)


@dataclass
class Claim:
    """A factual claim to verify"""
    claim_id: str
    text: str
    domain: str
    status: FactStatus
    confidence: float
    sources_supporting: List[str] = field(default_factory=list)
    sources_contradicting: List[str] = field(default_factory=list)
    verified_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class FactVerificationSystem:
    """
    Multi-source fact verification system with credibility assessment
    and consistency checking.
    """

    def __init__(self):
        # Source tracking
        self.sources: Dict[str, Source] = {}
        self.domain_experts: Dict[str, List[str]] = defaultdict(list)

        # Claim tracking
        self.claims: Dict[str, Claim] = {}
        self.verification_history: List[Dict[str, Any]] = []

        # Credibility patterns
        self.credible_domains = {
            'edu', 'gov', 'org'  # Educational, government, non-profit
        }
        self.known_reliable_domains = set()
        self.known_unreliable_domains = set()

    async def verify_fact(
        self,
        claim_text: str,
        domain: str,
        sources: List[Dict[str, Any]]
    ) -> Claim:
        """Verify a factual claim using multiple sources"""
        import uuid

        claim_id = str(uuid.uuid4())

        # Assess source credibility
        credible_sources = []
        for source_data in sources:
            source = await self._assess_source(source_data)
            if source.credibility.value >= 3:  # MEDIUM or higher
                credible_sources.append(source)

        # Cross-reference sources
        supporting = []
        contradicting = []

        for source in credible_sources:
            # Check if source supports the claim
            supports = await self._source_supports_claim(source, claim_text, sources)

            if supports is True:
                supporting.append(source.url)
            elif supports is False:
                contradicting.append(source.url)

        # Determine verification status
        status, confidence = self._determine_status(
            len(supporting),
            len(contradicting),
            credible_sources
        )

        claim = Claim(
            claim_id=claim_id,
            text=claim_text,
            domain=domain,
            status=status,
            confidence=confidence,
            sources_supporting=supporting,
            sources_contradicting=contradicting,
            verified_at=datetime.now(),
            metadata={
                'total_sources_checked': len(sources),
                'credible_sources': len(credible_sources)
            }
        )

        self.claims[claim_id] = claim

        # Record verification
        self.verification_history.append({
            'claim_id': claim_id,
            'timestamp': datetime.now(),
            'status': status.value,
            'confidence': confidence,
            'sources_count': len(sources)
        })

        logger.info(f"Fact verified: {status.value} (confidence: {confidence:.2f})")
        return claim

    async def _assess_source(self, source_data: Dict[str, Any]) -> Source:
        """Assess credibility of a source"""
        url = source_data.get('url', '')
        domain = self._extract_domain(url)

        # Check if source already tracked
        if url in self.sources:
            return self.sources[url]

        # Assess credibility
        credibility = await self._calculate_credibility(domain, source_data)

        # Extract bias
        bias = source_data.get('bias_score', 0.0)

        source = Source(
            url=url,
            domain=domain,
            credibility=credibility,
            bias_score=bias,
            specialty_areas=set(source_data.get('topics', []))
        )

        self.sources[url] = source

        # Track domain experts
        for topic in source.specialty_areas:
            self.domain_experts[topic].append(url)

        return source

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove www.
        if domain.startswith('www.'):
            domain = domain[4:]

        return domain

    async def _calculate_credibility(
        self,
        domain: str,
        source_data: Dict[str, Any]
    ) -> CredibilityLevel:
        """Calculate source credibility level"""
        score = 3  # Start with MEDIUM

        # Check known lists
        if domain in self.known_reliable_domains:
            score += 2
        elif domain in self.known_unreliable_domains:
            score -= 2

        # Domain type
        tld = domain.split('.')[-1]
        if tld in self.credible_domains:
            score += 1

        # Peer review status
        if source_data.get('peer_reviewed', False):
            score += 1

        # Primary source
        if source_data.get('primary_source', False):
            score += 1

        # Author credentials
        if source_data.get('author_credentials'):
            score += 1

        # Clamp score
        score = max(1, min(5, score))

        return CredibilityLevel(score)

    async def _source_supports_claim(
        self,
        source: Source,
        claim: str,
        all_sources: List[Dict[str, Any]]
    ) -> Optional[bool]:
        """Check if source supports the claim"""
        # Find the source data
        source_content = None
        for s in all_sources:
            if s.get('url') == source.url:
                source_content = s.get('content', '')
                break

        if not source_content:
            return None

        # Simple keyword matching (in real implementation, use NLP)
        claim_keywords = set(claim.lower().split())
        content_keywords = set(source_content.lower().split())

        # Calculate overlap
        overlap = len(claim_keywords & content_keywords)
        overlap_ratio = overlap / len(claim_keywords) if claim_keywords else 0

        if overlap_ratio > 0.5:
            # Check for negation words
            negation_words = {'not', 'no', 'false', 'incorrect', 'wrong', 'debunked'}
            if any(word in content_keywords for word in negation_words):
                return False
            return True

        return None

    def _determine_status(
        self,
        supporting_count: int,
        contradicting_count: int,
        credible_sources: List[Source]
    ) -> tuple[FactStatus, float]:
        """Determine verification status and confidence"""
        total = supporting_count + contradicting_count

        if total == 0:
            return FactStatus.UNCERTAIN, 0.0

        support_ratio = supporting_count / total

        # Calculate confidence based on source count and credibility
        base_confidence = min(1.0, total / 5)  # More sources = more confident

        # Adjust for credibility
        avg_credibility = sum(s.credibility.value for s in credible_sources) / len(credible_sources) if credible_sources else 3
        credibility_factor = avg_credibility / 5.0

        confidence = base_confidence * credibility_factor

        # Determine status
        if support_ratio >= 0.8 and supporting_count >= 3:
            return FactStatus.VERIFIED, confidence
        elif support_ratio >= 0.6:
            return FactStatus.LIKELY_TRUE, confidence * 0.8
        elif support_ratio <= 0.2 and contradicting_count >= 3:
            return FactStatus.DEBUNKED, confidence
        elif support_ratio <= 0.4:
            return FactStatus.LIKELY_FALSE, confidence * 0.7
        else:
            return FactStatus.UNCERTAIN, confidence * 0.5

    async def check_consistency(
        self,
        claims: List[str],
        domain: str
    ) -> Dict[str, Any]:
        """Check consistency across multiple claims"""
        # Verify each claim
        verified_claims = []
        for claim_text in claims:
            # In real implementation, would fetch sources
            claim = await self.verify_fact(claim_text, domain, [])
            verified_claims.append(claim)

        # Check for contradictions
        contradictions = []
        for i, claim1 in enumerate(verified_claims):
            for claim2 in verified_claims[i+1:]:
                if self._claims_contradict(claim1, claim2):
                    contradictions.append((claim1.claim_id, claim2.claim_id))

        consistency_score = 1.0 - (len(contradictions) / max(len(claims), 1))

        return {
            'consistency_score': consistency_score,
            'verified_claims': len([c for c in verified_claims if c.status == FactStatus.VERIFIED]),
            'uncertain_claims': len([c for c in verified_claims if c.status == FactStatus.UNCERTAIN]),
            'contradictions_found': len(contradictions),
            'overall_confidence': sum(c.confidence for c in verified_claims) / len(verified_claims) if verified_claims else 0.0
        }

    def _claims_contradict(self, claim1: Claim, claim2: Claim) -> bool:
        """Check if two claims contradict each other"""
        # Simplified contradiction detection
        # In real implementation, use semantic analysis

        # Check status opposition
        if claim1.status == FactStatus.VERIFIED and claim2.status == FactStatus.DEBUNKED:
            return True
        if claim1.status == FactStatus.DEBUNKED and claim2.status == FactStatus.VERIFIED:
            return True

        # Check for opposing keywords
        opposing_pairs = [
            ('increase', 'decrease'),
            ('true', 'false'),
            ('correct', 'incorrect'),
            ('valid', 'invalid')
        ]

        words1 = set(claim1.text.lower().split())
        words2 = set(claim2.text.lower().split())

        for word_a, word_b in opposing_pairs:
            if word_a in words1 and word_b in words2:
                return True
            if word_b in words1 and word_a in words2:
                return True

        return False

    async def update_source_credibility(self, url: str, verification_outcome: bool):
        """Update source credibility based on verification outcomes"""
        if url not in self.sources:
            return

        source = self.sources[url]
        source.verification_history.append(verification_outcome)

        # Recalculate credibility
        if len(source.verification_history) >= 5:
            accuracy = sum(source.verification_history) / len(source.verification_history)

            if accuracy >= 0.8:
                source.credibility = CredibilityLevel.HIGH
                self.known_reliable_domains.add(source.domain)
            elif accuracy <= 0.4:
                source.credibility = CredibilityLevel.LOW
                self.known_unreliable_domains.add(source.domain)

    async def get_verification_insights(self) -> Dict[str, Any]:
        """Get insights about fact verification"""
        if not self.verification_history:
            return {'message': 'No verification history'}

        recent = [v for v in self.verification_history
                 if (datetime.now() - v['timestamp']).days < 30]

        verified_count = len([v for v in recent if v['status'] == 'verified'])
        debunked_count = len([v for v in recent if v['status'] == 'debunked'])

        return {
            'total_verifications': len(self.verification_history),
            'recent_verifications': len(recent),
            'verified_facts': verified_count,
            'debunked_facts': debunked_count,
            'average_confidence': sum(v['confidence'] for v in recent) / len(recent) if recent else 0.0,
            'total_sources_tracked': len(self.sources),
            'reliable_domains': len(self.known_reliable_domains),
            'unreliable_domains': len(self.known_unreliable_domains)
        }
