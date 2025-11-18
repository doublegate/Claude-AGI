"""
Novelty Detection System
=========================

Detects and evaluates novelty in creative works and ideas.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class CreativeWork:
    """A creative work for novelty analysis"""
    work_id: str
    content: str
    work_type: str  # poem, story, code, idea, etc.
    novelty_score: float = 0.0
    originality_factors: Dict[str, float] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.originality_factors is None:
            self.originality_factors = {}
        if self.created_at is None:
            self.created_at = datetime.now()


class NoveltyDetector:
    """
    Evaluates novelty and originality of creative works
    by comparing with existing works and detecting unique patterns.
    """

    def __init__(self):
        self.existing_works: Dict[str, CreativeWork] = {}
        self.pattern_library: Dict[str, int] = defaultdict(int)
        self.novelty_threshold = 0.6

    async def evaluate_novelty(
        self,
        work: CreativeWork
    ) -> Dict[str, Any]:
        """Evaluate novelty of a creative work"""
        # Extract patterns
        patterns = self._extract_patterns(work.content, work.work_type)

        # Calculate novelty factors
        uniqueness = await self._calculate_uniqueness(patterns)
        originality = await self._calculate_originality(work, patterns)
        surprise = await self._calculate_surprise(patterns)

        # Combined novelty score
        novelty_score = (uniqueness * 0.4 + originality * 0.4 + surprise * 0.2)

        work.novelty_score = novelty_score
        work.originality_factors = {
            'uniqueness': uniqueness,
            'originality': originality,
            'surprise': surprise
        }

        # Store work
        self.existing_works[work.work_id] = work

        # Update pattern library
        for pattern in patterns:
            self.pattern_library[pattern] += 1

        return {
            'novelty_score': novelty_score,
            'is_novel': novelty_score >= self.novelty_threshold,
            'factors': work.originality_factors,
            'unique_patterns': len([p for p in patterns if self.pattern_library[p] == 1])
        }

    def _extract_patterns(self, content: str, work_type: str) -> List[str]:
        """Extract patterns from creative work"""
        patterns = []

        # Word patterns
        words = content.lower().split()
        for i in range(len(words) - 2):
            pattern = f"trigram:{words[i]}_{words[i+1]}_{words[i+2]}"
            patterns.append(pattern)

        # Structural patterns
        if work_type == 'poem':
            lines = content.split('\n')
            patterns.append(f"line_count:{len(lines)}")
            patterns.append(f"avg_line_length:{sum(len(l) for l in lines) // max(len(lines), 1)}")

        return patterns

    async def _calculate_uniqueness(self, patterns: List[str]) -> float:
        """Calculate uniqueness based on pattern rarity"""
        if not patterns:
            return 0.0

        unique_count = sum(1 for p in patterns if self.pattern_library.get(p, 0) == 0)
        return unique_count / len(patterns)

    async def _calculate_originality(
        self,
        work: CreativeWork,
        patterns: List[str]
    ) -> float:
        """Calculate originality by comparing with existing works"""
        if not self.existing_works:
            return 0.8  # First work is original

        # Find most similar work
        max_similarity = 0.0
        for existing in self.existing_works.values():
            if existing.work_id == work.work_id:
                continue

            similarity = self._calculate_similarity(work.content, existing.content)
            max_similarity = max(max_similarity, similarity)

        # Originality is inverse of similarity
        return 1.0 - max_similarity

    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two works"""
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    async def _calculate_surprise(self, patterns: List[str]) -> float:
        """Calculate surprise factor based on unexpected patterns"""
        if not patterns:
            return 0.0

        rare_patterns = sum(1 for p in patterns if self.pattern_library.get(p, 0) < 2)
        return min(1.0, rare_patterns / (len(patterns) * 0.3))
