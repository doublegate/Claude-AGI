"""
Web Content Credibility Checker
=================================

Assesses the credibility and trustworthiness of web sources and content.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Set
from urllib.parse import urlparse
import re

logger = logging.getLogger(__name__)


class CredibilityLevel(Enum):
    """Credibility levels for sources"""
    VERIFIED = 1.0          # Verified authoritative source
    HIGHLY_CREDIBLE = 0.9   # Well-established, peer-reviewed
    CREDIBLE = 0.75         # Generally trustworthy
    MODERATE = 0.5          # Mixed or unknown reliability
    QUESTIONABLE = 0.3      # Red flags present
    UNRELIABLE = 0.1        # Known unreliable source


@dataclass
class CredibilityIndicator:
    """An indicator affecting credibility"""
    indicator_type: str
    description: str
    impact: float  # -1 to +1
    confidence: float  # 0 to 1


@dataclass
class CredibilityAssessment:
    """Assessment of source credibility"""
    url: str
    domain: str
    overall_score: float
    credibility_level: CredibilityLevel
    indicators: List[CredibilityIndicator] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendation: str = ""
    assessed_at: datetime = field(default_factory=datetime.now)


class CredibilityChecker:
    """
    Assesses credibility of web sources using multiple signals.
    """

    def __init__(self):
        # Known trustworthy domains
        self.verified_domains = {
            'wikipedia.org', 'nature.com', 'science.org',
            'arxiv.org', 'ieee.org', 'acm.org',
            'nih.gov', 'nasa.gov', 'edu'
        }

        # Known questionable domains
        self.questionable_domains = {
            'example-fake-news.com'  # Placeholder
        }

        # Credibility history
        self.domain_history: Dict[str, List[float]] = {}
        self.assessment_cache: Dict[str, CredibilityAssessment] = {}

    async def assess_credibility(
        self,
        url: str,
        content: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> CredibilityAssessment:
        """
        Assess credibility of a web source.

        Args:
            url: URL to assess
            content: Optional content for analysis
            metadata: Optional metadata

        Returns:
            Credibility assessment
        """
        # Parse URL
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Check cache
        if url in self.assessment_cache:
            return self.assessment_cache[url]

        indicators = []

        # 1. Domain reputation
        domain_indicators = await self._check_domain_reputation(domain)
        indicators.extend(domain_indicators)

        # 2. HTTPS
        https_indicators = await self._check_https(parsed)
        indicators.extend(https_indicators)

        # 3. Content quality signals
        if content:
            content_indicators = await self._analyze_content_quality(content)
            indicators.extend(content_indicators)

        # 4. Metadata signals
        if metadata:
            metadata_indicators = await self._analyze_metadata(metadata)
            indicators.extend(metadata_indicators)

        # 5. Author credentials
        author_indicators = await self._check_author_credentials(metadata or {})
        indicators.extend(author_indicators)

        # 6. Citation and references
        citation_indicators = await self._check_citations(content or "")
        indicators.extend(citation_indicators)

        # 7. Publication date recency
        recency_indicators = await self._check_recency(metadata or {})
        indicators.extend(recency_indicators)

        # Calculate overall score
        overall_score = await self._calculate_overall_score(indicators)

        # Determine credibility level
        credibility_level = self._score_to_level(overall_score)

        # Identify strengths and weaknesses
        strengths = [
            ind.description for ind in indicators
            if ind.impact > 0.2
        ]

        weaknesses = [
            ind.description for ind in indicators
            if ind.impact < -0.2
        ]

        # Generate recommendation
        recommendation = await self._generate_recommendation(
            overall_score,
            strengths,
            weaknesses
        )

        assessment = CredibilityAssessment(
            url=url,
            domain=domain,
            overall_score=overall_score,
            credibility_level=credibility_level,
            indicators=indicators,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendation=recommendation
        )

        # Cache assessment
        self.assessment_cache[url] = assessment

        # Update domain history
        if domain not in self.domain_history:
            self.domain_history[domain] = []
        self.domain_history[domain].append(overall_score)

        logger.info(
            f"Assessed credibility for {domain}: "
            f"{credibility_level.name} ({overall_score:.2f})"
        )

        return assessment

    async def _check_domain_reputation(
        self,
        domain: str
    ) -> List[CredibilityIndicator]:
        """Check domain reputation"""
        indicators = []

        # Check verified domains
        if any(verified in domain for verified in self.verified_domains):
            indicators.append(CredibilityIndicator(
                indicator_type='domain_reputation',
                description='Verified authoritative domain',
                impact=0.5,
                confidence=1.0
            ))

        # Check .edu domains
        if domain.endswith('.edu'):
            indicators.append(CredibilityIndicator(
                indicator_type='domain_type',
                description='Educational institution domain',
                impact=0.4,
                confidence=0.9
            ))

        # Check .gov domains
        if domain.endswith('.gov'):
            indicators.append(CredibilityIndicator(
                indicator_type='domain_type',
                description='Government domain',
                impact=0.4,
                confidence=1.0
            ))

        # Check questionable domains
        if domain in self.questionable_domains:
            indicators.append(CredibilityIndicator(
                indicator_type='domain_reputation',
                description='Known unreliable source',
                impact=-0.8,
                confidence=1.0
            ))

        # Check domain history
        if domain in self.domain_history and len(self.domain_history[domain]) >= 3:
            avg_score = sum(self.domain_history[domain]) / len(self.domain_history[domain])
            if avg_score > 0.7:
                indicators.append(CredibilityIndicator(
                    indicator_type='domain_history',
                    description='Consistently reliable in past assessments',
                    impact=0.3,
                    confidence=0.8
                ))

        return indicators

    async def _check_https(self, parsed) -> List[CredibilityIndicator]:
        """Check HTTPS usage"""
        indicators = []

        if parsed.scheme == 'https':
            indicators.append(CredibilityIndicator(
                indicator_type='security',
                description='Uses HTTPS encryption',
                impact=0.1,
                confidence=1.0
            ))
        else:
            indicators.append(CredibilityIndicator(
                indicator_type='security',
                description='No HTTPS encryption',
                impact=-0.2,
                confidence=1.0
            ))

        return indicators

    async def _analyze_content_quality(
        self,
        content: str
    ) -> List[CredibilityIndicator]:
        """Analyze content quality signals"""
        indicators = []

        # Check length
        if len(content) > 1000:
            indicators.append(CredibilityIndicator(
                indicator_type='content_quality',
                description='Substantial content length',
                impact=0.1,
                confidence=0.7
            ))

        # Check for sensationalism
        sensational_words = ['shocking', 'unbelievable', 'secret', 'they don\'t want you to know']
        sensational_count = sum(1 for word in sensational_words if word.lower() in content.lower())

        if sensational_count > 3:
            indicators.append(CredibilityIndicator(
                indicator_type='content_quality',
                description='Excessive sensational language',
                impact=-0.3,
                confidence=0.8
            ))

        # Check for claims without evidence
        claim_words = ['studies show', 'research proves', 'experts say']
        claim_count = sum(1 for phrase in claim_words if phrase.lower() in content.lower())

        if claim_count > 0:
            indicators.append(CredibilityIndicator(
                indicator_type='content_quality',
                description='References studies/research',
                impact=0.2,
                confidence=0.6
            ))

        return indicators

    async def _analyze_metadata(
        self,
        metadata: Dict
    ) -> List[CredibilityIndicator]:
        """Analyze metadata signals"""
        indicators = []

        # Check for author
        if metadata.get('author'):
            indicators.append(CredibilityIndicator(
                indicator_type='transparency',
                description='Author identified',
                impact=0.2,
                confidence=0.8
            ))

        # Check for publication date
        if metadata.get('publication_date'):
            indicators.append(CredibilityIndicator(
                indicator_type='transparency',
                description='Publication date provided',
                impact=0.1,
                confidence=0.9
            ))

        return indicators

    async def _check_author_credentials(
        self,
        metadata: Dict
    ) -> List[CredibilityIndicator]:
        """Check author credentials"""
        indicators = []

        author = metadata.get('author', '')

        # Check for credentials in author info
        credentials = ['PhD', 'Dr.', 'Professor', 'MD']
        if any(cred in author for cred in credentials):
            indicators.append(CredibilityIndicator(
                indicator_type='author_credentials',
                description='Author has relevant credentials',
                impact=0.3,
                confidence=0.7
            ))

        return indicators

    async def _check_citations(self, content: str) -> List[CredibilityIndicator]:
        """Check for citations and references"""
        indicators = []

        # Look for reference indicators
        has_references = any(word in content.lower() for word in ['references', 'bibliography', 'citations'])

        if has_references:
            indicators.append(CredibilityIndicator(
                indicator_type='citations',
                description='Includes references/citations',
                impact=0.3,
                confidence=0.8
            ))

        return indicators

    async def _check_recency(self, metadata: Dict) -> List[CredibilityIndicator]:
        """Check publication date recency"""
        indicators = []

        pub_date = metadata.get('publication_date')
        if pub_date and isinstance(pub_date, datetime):
            age_days = (datetime.now() - pub_date).days

            if age_days < 30:
                indicators.append(CredibilityIndicator(
                    indicator_type='recency',
                    description='Recently published (< 1 month)',
                    impact=0.2,
                    confidence=0.9
                ))
            elif age_days > 1825:  # 5 years
                indicators.append(CredibilityIndicator(
                    indicator_type='recency',
                    description='Potentially outdated (> 5 years)',
                    impact=-0.1,
                    confidence=0.6
                ))

        return indicators

    async def _calculate_overall_score(
        self,
        indicators: List[CredibilityIndicator]
    ) -> float:
        """Calculate overall credibility score"""
        if not indicators:
            return 0.5  # Neutral

        # Weighted average by confidence
        total_weighted = sum(ind.impact * ind.confidence for ind in indicators)
        total_confidence = sum(ind.confidence for ind in indicators)

        if total_confidence == 0:
            return 0.5

        score = (total_weighted / total_confidence + 1.0) / 2.0  # Normalize to 0-1

        return max(0.0, min(1.0, score))

    def _score_to_level(self, score: float) -> CredibilityLevel:
        """Convert score to credibility level"""
        if score >= 0.95:
            return CredibilityLevel.VERIFIED
        elif score >= 0.85:
            return CredibilityLevel.HIGHLY_CREDIBLE
        elif score >= 0.7:
            return CredibilityLevel.CREDIBLE
        elif score >= 0.45:
            return CredibilityLevel.MODERATE
        elif score >= 0.25:
            return CredibilityLevel.QUESTIONABLE
        else:
            return CredibilityLevel.UNRELIABLE

    async def _generate_recommendation(
        self,
        score: float,
        strengths: List[str],
        weaknesses: List[str]
    ) -> str:
        """Generate recommendation based on assessment"""
        if score >= 0.85:
            return "Highly credible source. Suitable for knowledge base integration."
        elif score >= 0.7:
            return "Credible source. Recommended for learning with standard verification."
        elif score >= 0.45:
            return "Moderate credibility. Cross-reference with other sources recommended."
        elif score >= 0.25:
            return "Questionable credibility. Use with caution and verify claims."
        else:
            return "Low credibility. Not recommended for knowledge base."

    async def batch_assess(
        self,
        urls: List[str]
    ) -> List[CredibilityAssessment]:
        """Assess multiple URLs"""
        assessments = []

        for url in urls:
            assessment = await self.assess_credibility(url)
            assessments.append(assessment)

        return assessments

    def get_domain_statistics(self) -> Dict[str, any]:
        """Get statistics about assessed domains"""
        total_domains = len(self.domain_history)
        total_assessments = sum(len(scores) for scores in self.domain_history.values())

        avg_score_by_domain = {
            domain: sum(scores) / len(scores)
            for domain, scores in self.domain_history.items()
        }

        return {
            'total_domains_assessed': total_domains,
            'total_assessments': total_assessments,
            'average_scores': avg_score_by_domain,
            'cached_assessments': len(self.assessment_cache)
        }


async def demo():
    """Demo credibility checking"""
    checker = CredibilityChecker()

    # Assess some URLs
    urls = [
        'https://arxiv.org/article',
        'https://example.edu/research',
        'http://sketchy-site.com/article'
    ]

    for url in urls:
        assessment = await checker.assess_credibility(url)

        print(f"\n=== Credibility Assessment: {url} ===")
        print(f"Domain: {assessment.domain}")
        print(f"Overall Score: {assessment.overall_score:.2f}")
        print(f"Level: {assessment.credibility_level.name}")
        print(f"Recommendation: {assessment.recommendation}")

        if assessment.strengths:
            print(f"Strengths:")
            for strength in assessment.strengths[:3]:
                print(f"  + {strength}")

        if assessment.weaknesses:
            print(f"Weaknesses:")
            for weakness in assessment.weaknesses[:3]:
                print(f"  - {weakness}")

    # Statistics
    stats = checker.get_domain_statistics()
    print(f"\n=== Statistics ===")
    print(f"Domains assessed: {stats['total_domains_assessed']}")
    print(f"Total assessments: {stats['total_assessments']}")


if __name__ == "__main__":
    asyncio.run(demo())
