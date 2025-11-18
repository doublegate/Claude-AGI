"""
Transfer Learning System
=========================

Enables knowledge and skill transfer across domains,
facilitating faster learning in new areas based on existing knowledge.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class TransferPattern:
    """Pattern that can be transferred across domains"""
    pattern_id: str
    source_domain: str
    applicable_domains: Set[str]
    pattern_type: str  # structural, procedural, conceptual
    abstraction_level: float  # 0-1, higher = more abstract
    transfer_success_rate: float = 0.0
    transfer_attempts: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TransferInstance:
    """Record of a transfer learning event"""
    source_skill: str
    target_skill: str
    transfer_amount: float
    success: bool
    timestamp: datetime
    performance_gain: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class TransferLearningEngine:
    """
    Manages transfer learning across skills and domains.
    Identifies transferable patterns and applies them to accelerate learning.
    """

    def __init__(self):
        # Transfer patterns
        self.patterns: Dict[str, TransferPattern] = {}
        self.domain_patterns: Dict[str, List[str]] = defaultdict(list)

        # Transfer history
        self.transfer_history: List[TransferInstance] = []

        # Domain similarity matrix
        self.domain_similarity: Dict[Tuple[str, str], float] = {}

        # Performance tracking
        self.transfer_effectiveness: Dict[str, float] = {}

    async def identify_transferable_pattern(
        self,
        source_skill: str,
        source_domain: str,
        pattern_data: Dict[str, Any]
    ) -> TransferPattern:
        """Identify and register a transferable pattern"""
        import uuid

        pattern_id = str(uuid.uuid4())

        # Determine abstraction level
        abstraction = self._calculate_abstraction_level(pattern_data)

        # Identify applicable domains
        applicable = await self._identify_applicable_domains(
            source_domain,
            pattern_data,
            abstraction
        )

        pattern = TransferPattern(
            pattern_id=pattern_id,
            source_domain=source_domain,
            applicable_domains=applicable,
            pattern_type=pattern_data.get('type', 'conceptual'),
            abstraction_level=abstraction,
            metadata={
                'source_skill': source_skill,
                'discovered_at': datetime.now(),
                'pattern_data': pattern_data
            }
        )

        self.patterns[pattern_id] = pattern
        self.domain_patterns[source_domain].append(pattern_id)

        logger.info(f"Identified transferable pattern: {pattern_id} from {source_domain}")
        return pattern

    def _calculate_abstraction_level(self, pattern_data: Dict[str, Any]) -> float:
        """Calculate how abstract/general a pattern is"""
        # Higher abstraction = more transferable
        score = 0.5

        # Structural patterns are more abstract
        if pattern_data.get('type') == 'structural':
            score += 0.2

        # Fewer domain-specific elements = higher abstraction
        domain_specific = pattern_data.get('domain_specific_elements', [])
        if len(domain_specific) < 3:
            score += 0.2

        # General principles are highly abstract
        if pattern_data.get('is_principle', False):
            score += 0.3

        return min(1.0, score)

    async def _identify_applicable_domains(
        self,
        source_domain: str,
        pattern_data: Dict[str, Any],
        abstraction: float
    ) -> Set[str]:
        """Identify domains where pattern can be applied"""
        applicable = {source_domain}  # Always applicable to source

        # Higher abstraction = more domains
        if abstraction > 0.7:
            # Broadly applicable
            applicable.update([
                'cognitive', 'technical', 'creative', 'analytical',
                'problem_solving', 'meta_learning'
            ])
        elif abstraction > 0.5:
            # Related domains
            related = {
                'technical': {'analytical', 'problem_solving'},
                'creative': {'cognitive', 'problem_solving'},
                'analytical': {'technical', 'problem_solving'},
                'cognitive': {'meta_learning', 'creative'},
            }
            applicable.update(related.get(source_domain, set()))
        else:
            # Only very similar domains
            similar = {
                'technical': {'analytical'},
                'creative': {'cognitive'},
            }
            applicable.update(similar.get(source_domain, set()))

        return applicable

    async def attempt_transfer(
        self,
        source_skill: str,
        target_skill: str,
        source_domain: str,
        target_domain: str,
        pattern_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Attempt to transfer learning from source to target skill"""
        # Find applicable patterns
        if pattern_id:
            patterns = [self.patterns[pattern_id]] if pattern_id in self.patterns else []
        else:
            patterns = await self._find_applicable_patterns(source_domain, target_domain)

        if not patterns:
            return {
                'success': False,
                'reason': 'No applicable transfer patterns found'
            }

        # Calculate transfer potential
        transfer_potential = self._calculate_transfer_potential(
            source_domain,
            target_domain,
            patterns
        )

        # Apply transfer
        if transfer_potential > 0.3:
            transfer_amount = transfer_potential * 0.5  # Conservative transfer

            # Record transfer
            transfer_instance = TransferInstance(
                source_skill=source_skill,
                target_skill=target_skill,
                transfer_amount=transfer_amount,
                success=True,
                timestamp=datetime.now(),
                performance_gain=transfer_amount * 0.8,  # Estimated gain
                metadata={
                    'source_domain': source_domain,
                    'target_domain': target_domain,
                    'patterns_used': [p.pattern_id for p in patterns]
                }
            )

            self.transfer_history.append(transfer_instance)

            # Update pattern success rates
            for pattern in patterns:
                pattern.transfer_attempts += 1
                pattern.transfer_success_rate = (
                    (pattern.transfer_success_rate * (pattern.transfer_attempts - 1) + 1.0)
                    / pattern.transfer_attempts
                )

            logger.info(f"Transfer successful: {source_skill} -> {target_skill} ({transfer_amount:.2%})")

            return {
                'success': True,
                'transfer_amount': transfer_amount,
                'performance_gain': transfer_amount * 0.8,
                'patterns_applied': len(patterns)
            }
        else:
            return {
                'success': False,
                'reason': 'Transfer potential too low',
                'potential': transfer_potential
            }

    async def _find_applicable_patterns(
        self,
        source_domain: str,
        target_domain: str
    ) -> List[TransferPattern]:
        """Find patterns that can transfer between domains"""
        applicable = []

        for pattern_id in self.domain_patterns.get(source_domain, []):
            pattern = self.patterns[pattern_id]

            if target_domain in pattern.applicable_domains:
                applicable.append(pattern)

        # Sort by success rate and abstraction
        applicable.sort(
            key=lambda p: (p.transfer_success_rate, p.abstraction_level),
            reverse=True
        )

        return applicable

    def _calculate_transfer_potential(
        self,
        source_domain: str,
        target_domain: str,
        patterns: List[TransferPattern]
    ) -> float:
        """Calculate potential for successful transfer"""
        if not patterns:
            return 0.0

        # Domain similarity
        domain_sim = self.get_domain_similarity(source_domain, target_domain)

        # Pattern quality
        if patterns:
            avg_abstraction = sum(p.abstraction_level for p in patterns) / len(patterns)
            avg_success = sum(p.transfer_success_rate for p in patterns) / len(patterns) if any(p.transfer_attempts > 0 for p in patterns) else 0.5
        else:
            avg_abstraction = 0.0
            avg_success = 0.0

        # Combined potential
        potential = (domain_sim * 0.3 + avg_abstraction * 0.4 + avg_success * 0.3)
        return potential

    def get_domain_similarity(self, domain1: str, domain2: str) -> float:
        """Get similarity between two domains"""
        if domain1 == domain2:
            return 1.0

        # Check cache
        cache_key = tuple(sorted([domain1, domain2]))
        if cache_key in self.domain_similarity:
            return self.domain_similarity[cache_key]

        # Calculate similarity
        similarity = self._calculate_domain_similarity(domain1, domain2)
        self.domain_similarity[cache_key] = similarity

        return similarity

    def _calculate_domain_similarity(self, domain1: str, domain2: str) -> float:
        """Calculate similarity between domains"""
        # Predefined similarity matrix (keys sorted alphabetically)
        similarities = {
            ('analytical', 'technical'): 0.8,
            ('cognitive', 'creative'): 0.7,
            ('analytical', 'problem_solving'): 0.75,
            ('cognitive', 'problem_solving'): 0.7,
            ('cognitive', 'meta_learning'): 0.8,
            ('problem_solving', 'technical'): 0.65,
            ('creative', 'problem_solving'): 0.6,
        }

        key = tuple(sorted([domain1, domain2]))
        return similarities.get(key, 0.3)  # Default low similarity

    async def get_transfer_recommendations(
        self,
        target_skill: str,
        target_domain: str,
        available_skills: List[Tuple[str, str, float]]  # (name, domain, proficiency)
    ) -> List[Dict[str, Any]]:
        """Get recommendations for which skills to leverage for transfer"""
        recommendations = []

        for source_skill, source_domain, proficiency in available_skills:
            if proficiency < 0.5:  # Need decent proficiency to transfer
                continue

            # Calculate transfer potential
            patterns = await self._find_applicable_patterns(source_domain, target_domain)
            potential = self._calculate_transfer_potential(source_domain, target_domain, patterns)

            if potential > 0.2:
                recommendations.append({
                    'source_skill': source_skill,
                    'source_domain': source_domain,
                    'source_proficiency': proficiency,
                    'transfer_potential': potential,
                    'estimated_benefit': potential * proficiency * 0.3,
                    'applicable_patterns': len(patterns)
                })

        # Sort by estimated benefit
        recommendations.sort(key=lambda x: x['estimated_benefit'], reverse=True)
        return recommendations

    async def analyze_transfer_effectiveness(self) -> Dict[str, Any]:
        """Analyze effectiveness of transfer learning"""
        if not self.transfer_history:
            return {'message': 'No transfer learning history yet'}

        successful = [t for t in self.transfer_history if t.success]
        total_attempts = len(self.transfer_history)

        # Performance gains
        avg_gain = sum(t.performance_gain for t in successful) / len(successful) if successful else 0.0
        total_gain = sum(t.performance_gain for t in successful)

        # Pattern effectiveness
        pattern_usage = defaultdict(int)
        for transfer in successful:
            for pattern_id in transfer.metadata.get('patterns_used', []):
                pattern_usage[pattern_id] += 1

        most_used_patterns = sorted(
            pattern_usage.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            'total_transfers': total_attempts,
            'successful_transfers': len(successful),
            'success_rate': len(successful) / total_attempts if total_attempts > 0 else 0.0,
            'average_performance_gain': avg_gain,
            'total_performance_gain': total_gain,
            'total_patterns': len(self.patterns),
            'most_effective_patterns': [
                {
                    'pattern_id': pid,
                    'usage_count': count,
                    'success_rate': self.patterns[pid].transfer_success_rate
                }
                for pid, count in most_used_patterns if pid in self.patterns
            ]
        }

    async def meta_learn_from_transfers(self):
        """Meta-learn by analyzing transfer patterns"""
        # Analyze which types of transfers work best
        if len(self.transfer_history) < 10:
            return

        # Find successful domain pairs
        domain_pair_success = defaultdict(lambda: {'successes': 0, 'total': 0})

        for transfer in self.transfer_history:
            source_domain = transfer.metadata.get('source_domain')
            target_domain = transfer.metadata.get('target_domain')

            if source_domain and target_domain:
                key = (source_domain, target_domain)
                domain_pair_success[key]['total'] += 1
                if transfer.success:
                    domain_pair_success[key]['successes'] += 1

        # Update domain similarities based on transfer success
        for (source, target), stats in domain_pair_success.items():
            if stats['total'] >= 3:  # Minimum sample size
                success_rate = stats['successes'] / stats['total']

                # Update similarity matrix
                cache_key = tuple(sorted([source, target]))
                current_sim = self.domain_similarity.get(cache_key, 0.5)

                # Blend with observed success rate
                new_sim = (current_sim * 0.7 + success_rate * 0.3)
                self.domain_similarity[cache_key] = new_sim

        logger.info("Meta-learned from transfer patterns - updated domain similarities")
