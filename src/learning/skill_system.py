"""
Skill Acquisition and Management System
========================================

Advanced skill learning, proficiency tracking, and transfer learning
for continuous capability development.
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class SkillDomain(Enum):
    """Domains of skills"""
    COGNITIVE = "cognitive"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    SOCIAL = "social"
    ANALYTICAL = "analytical"
    LINGUISTIC = "linguistic"
    PROBLEM_SOLVING = "problem_solving"
    META_LEARNING = "meta_learning"


class ProficiencyLevel(Enum):
    """Levels of skill proficiency"""
    NOVICE = (0.0, 0.2, "Novice")
    BEGINNER = (0.2, 0.4, "Beginner")
    INTERMEDIATE = (0.4, 0.6, "Intermediate")
    ADVANCED = (0.6, 0.8, "Advanced")
    EXPERT = (0.8, 1.0, "Expert")

    def __init__(self, min_val, max_val, label):
        self.min_val = min_val
        self.max_val = max_val
        self.label = label

    @classmethod
    def from_proficiency(cls, proficiency: float):
        """Get proficiency level from numeric value"""
        for level in cls:
            if level.min_val <= proficiency < level.max_val:
                return level
        return cls.EXPERT  # For proficiency >= 0.8


@dataclass
class SkillComponent:
    """Individual component of a skill"""
    name: str
    description: str
    proficiency: float = 0.0
    practice_count: int = 0
    last_practiced: Optional[datetime] = None


@dataclass
class Skill:
    """Comprehensive skill representation"""
    skill_id: str
    name: str
    domain: SkillDomain
    description: str
    proficiency: float = 0.0
    components: List[SkillComponent] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    enables: List[str] = field(default_factory=list)
    practice_sessions: int = 0
    total_practice_time: float = 0.0
    success_rate: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    last_practiced: datetime = field(default_factory=datetime.now)
    mastery_criteria: Dict[str, Any] = field(default_factory=dict)
    learning_trajectory: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_proficiency_level(self) -> ProficiencyLevel:
        """Get current proficiency level"""
        return ProficiencyLevel.from_proficiency(self.proficiency)

    def record_practice(self, duration: float, success: bool, performance: float):
        """Record a practice session"""
        self.practice_sessions += 1
        self.total_practice_time += duration
        self.last_practiced = datetime.now()

        # Update success rate
        total_attempts = len(self.learning_trajectory)
        if total_attempts > 0:
            successes = sum(1 for entry in self.learning_trajectory if entry.get('success', False))
            self.success_rate = (successes + (1 if success else 0)) / (total_attempts + 1)
        else:
            self.success_rate = 1.0 if success else 0.0

        # Record trajectory
        self.learning_trajectory.append({
            'timestamp': datetime.now(),
            'proficiency': self.proficiency,
            'performance': performance,
            'success': success,
            'duration': duration
        })


class SkillSystem:
    """
    Advanced skill acquisition and management system.
    Tracks skill proficiency, manages learning paths, and enables
    transfer learning across related skills.
    """

    def __init__(self):
        # Skill storage
        self.skills: Dict[str, Skill] = {}
        self.skill_graph: Dict[str, Set[str]] = defaultdict(set)  # Skill relationships

        # Learning parameters
        self.learning_rate = 0.05
        self.decay_rate = 0.02
        self.transfer_coefficient = 0.3

        # Practice tracking
        self.practice_history: List[Dict[str, Any]] = []
        self.skill_synergies: Dict[Tuple[str, str], float] = {}

        # Performance analytics
        self.domain_proficiency: Dict[SkillDomain, float] = {}

    async def create_skill(
        self,
        name: str,
        domain: SkillDomain,
        description: str,
        components: Optional[List[SkillComponent]] = None,
        prerequisites: Optional[List[str]] = None,
        mastery_criteria: Optional[Dict[str, Any]] = None
    ) -> Skill:
        """Create a new skill"""
        import uuid

        skill = Skill(
            skill_id=str(uuid.uuid4()),
            name=name,
            domain=domain,
            description=description,
            components=components or [],
            prerequisites=prerequisites or [],
            mastery_criteria=mastery_criteria or {
                'min_proficiency': 0.8,
                'min_sessions': 10,
                'min_success_rate': 0.7
            }
        )

        self.skills[skill.skill_id] = skill

        # Build skill graph relationships
        if prerequisites:
            for prereq_name in prerequisites:
                prereq_skill = self._find_skill_by_name(prereq_name)
                if prereq_skill:
                    prereq_skill.enables.append(skill.skill_id)
                    self.skill_graph[prereq_skill.skill_id].add(skill.skill_id)

        logger.info(f"Created skill: {name} in domain {domain.value}")
        return skill

    def _find_skill_by_name(self, name: str) -> Optional[Skill]:
        """Find skill by name"""
        for skill in self.skills.values():
            if skill.name.lower() == name.lower():
                return skill
        return None

    async def practice_skill(
        self,
        skill_id: str,
        duration: float,
        performance: float,
        success: bool,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Record skill practice and update proficiency"""
        if skill_id not in self.skills:
            return {'error': 'Skill not found'}

        skill = self.skills[skill_id]

        # Calculate proficiency gain
        proficiency_gain = self._calculate_proficiency_gain(
            skill, performance, success, duration
        )

        # Update skill proficiency
        old_proficiency = skill.proficiency
        skill.proficiency = min(1.0, skill.proficiency + proficiency_gain)

        # Record practice
        skill.record_practice(duration, success, performance)

        # Apply transfer learning to related skills
        await self._apply_transfer_learning(skill_id, proficiency_gain)

        # Record in history
        self.practice_history.append({
            'skill_id': skill_id,
            'skill_name': skill.name,
            'timestamp': datetime.now(),
            'duration': duration,
            'performance': performance,
            'success': success,
            'proficiency_gain': proficiency_gain,
            'new_proficiency': skill.proficiency,
            'context': context or {}
        })

        # Update domain proficiency
        await self._update_domain_proficiency(skill.domain)

        return {
            'skill_name': skill.name,
            'old_proficiency': old_proficiency,
            'new_proficiency': skill.proficiency,
            'proficiency_gain': proficiency_gain,
            'level': skill.get_proficiency_level().label,
            'sessions': skill.practice_sessions,
            'success_rate': skill.success_rate
        }

    def _calculate_proficiency_gain(
        self,
        skill: Skill,
        performance: float,
        success: bool,
        duration: float
    ) -> float:
        """Calculate how much proficiency increases from practice"""
        # Base gain from performance
        base_gain = self.learning_rate * performance

        # Success bonus
        if success:
            base_gain *= 1.2

        # Diminishing returns at higher proficiency
        difficulty_multiplier = 1.0 - (skill.proficiency * 0.5)
        base_gain *= difficulty_multiplier

        # Duration factor (longer focused practice is better)
        duration_factor = min(1.5, duration / 60)  # Normalize to hours
        base_gain *= duration_factor

        # Practice spacing (avoid cramming)
        if skill.last_practiced:
            hours_since_practice = (datetime.now() - skill.last_practiced).total_seconds() / 3600
            if hours_since_practice < 1:
                base_gain *= 0.5  # Cramming penalty
            elif 12 <= hours_since_practice <= 48:
                base_gain *= 1.2  # Optimal spacing bonus

        return base_gain

    async def _apply_transfer_learning(self, skill_id: str, proficiency_gain: float):
        """Apply transfer learning to related skills"""
        if skill_id not in self.skills:
            return

        skill = self.skills[skill_id]

        # Find related skills
        related_skills = await self._find_related_skills(skill_id)

        for related_id, similarity in related_skills:
            if related_id == skill_id:
                continue

            related_skill = self.skills[related_id]

            # Transfer a portion of the learning
            transfer_amount = proficiency_gain * self.transfer_coefficient * similarity

            # Only transfer if beneficial (not if already at higher proficiency)
            if related_skill.proficiency < skill.proficiency:
                related_skill.proficiency = min(1.0, related_skill.proficiency + transfer_amount)

                logger.debug(f"Transfer learning: {skill.name} -> {related_skill.name} (+{transfer_amount:.4f})")

    async def _find_related_skills(self, skill_id: str) -> List[Tuple[str, float]]:
        """Find skills related to the given skill"""
        if skill_id not in self.skills:
            return []

        skill = self.skills[skill_id]
        related = []

        for other_id, other_skill in self.skills.items():
            if other_id == skill_id:
                continue

            # Calculate similarity
            similarity = 0.0

            # Same domain
            if other_skill.domain == skill.domain:
                similarity += 0.5

            # Prerequisite relationship
            if other_id in self.skill_graph.get(skill_id, set()):
                similarity += 0.3
            if skill_id in self.skill_graph.get(other_id, set()):
                similarity += 0.3

            # Shared components
            if skill.components and other_skill.components:
                shared_components = set(c.name for c in skill.components) & set(c.name for c in other_skill.components)
                if shared_components:
                    similarity += 0.2 * (len(shared_components) / max(len(skill.components), len(other_skill.components)))

            if similarity > 0.1:
                related.append((other_id, similarity))

        return sorted(related, key=lambda x: x[1], reverse=True)

    async def _update_domain_proficiency(self, domain: SkillDomain):
        """Update overall proficiency for a domain"""
        domain_skills = [s for s in self.skills.values() if s.domain == domain]

        if domain_skills:
            avg_proficiency = sum(s.proficiency for s in domain_skills) / len(domain_skills)
            self.domain_proficiency[domain] = avg_proficiency

    async def apply_skill_decay(self):
        """Apply decay to skills not practiced recently"""
        current_time = datetime.now()

        for skill in self.skills.values():
            if not skill.last_practiced:
                continue

            days_since_practice = (current_time - skill.last_practiced).days

            if days_since_practice > 7:
                # Decay factor increases with time
                decay_amount = self.decay_rate * (days_since_practice / 30)

                # Higher proficiency decays slower (muscle memory)
                decay_resistance = skill.proficiency * 0.5
                effective_decay = decay_amount * (1 - decay_resistance)

                skill.proficiency = max(0.0, skill.proficiency - effective_decay)

    async def get_learning_path(self, target_skill: str) -> List[Dict[str, Any]]:
        """Get recommended learning path to achieve target skill"""
        target = self._find_skill_by_name(target_skill)
        if not target:
            return []

        # Build learning path using topological sort
        path = []
        visited = set()

        def build_path(skill: Skill):
            if skill.skill_id in visited:
                return

            visited.add(skill.skill_id)

            # Add prerequisites first
            for prereq_name in skill.prerequisites:
                prereq = self._find_skill_by_name(prereq_name)
                if prereq and prereq.proficiency < 0.6:  # Only if not already proficient
                    build_path(prereq)

            # Add current skill
            path.append({
                'skill_id': skill.skill_id,
                'name': skill.name,
                'current_proficiency': skill.proficiency,
                'target_proficiency': 0.7,
                'estimated_practice_time': self._estimate_practice_time(skill, 0.7),
                'level': skill.get_proficiency_level().label
            })

        build_path(target)
        return path

    def _estimate_practice_time(self, skill: Skill, target_proficiency: float) -> float:
        """Estimate hours of practice needed to reach target proficiency"""
        if skill.proficiency >= target_proficiency:
            return 0.0

        proficiency_gap = target_proficiency - skill.proficiency

        # Base estimate: 10 hours per 0.1 proficiency
        base_hours = proficiency_gap * 100

        # Adjust for current level (harder at higher levels)
        difficulty_multiplier = 1 + skill.proficiency

        return base_hours * difficulty_multiplier

    async def identify_skill_gaps(self, domain: Optional[SkillDomain] = None) -> List[Dict[str, Any]]:
        """Identify skills that need development"""
        gaps = []

        skills_to_check = self.skills.values()
        if domain:
            skills_to_check = [s for s in skills_to_check if s.domain == domain]

        for skill in skills_to_check:
            # Check if below intermediate level
            if skill.proficiency < 0.5:
                gaps.append({
                    'skill_name': skill.name,
                    'domain': skill.domain.value,
                    'current_proficiency': skill.proficiency,
                    'level': skill.get_proficiency_level().label,
                    'last_practiced': skill.last_practiced.isoformat() if skill.last_practiced else None,
                    'priority': self._calculate_skill_priority(skill)
                })

        # Sort by priority
        gaps.sort(key=lambda x: x['priority'], reverse=True)
        return gaps

    def _calculate_skill_priority(self, skill: Skill) -> float:
        """Calculate priority for developing a skill"""
        priority = 0.0

        # Number of skills it enables
        priority += len(skill.enables) * 10

        # Inverse of last practice (more urgent if not practiced)
        if skill.last_practiced:
            days_since = (datetime.now() - skill.last_practiced).days
            priority += min(days_since, 90)  # Cap at 90 days

        # Domain importance (could be configured)
        if skill.domain in [SkillDomain.META_LEARNING, SkillDomain.PROBLEM_SOLVING]:
            priority += 20

        return priority

    async def get_skill_insights(self) -> Dict[str, Any]:
        """Generate insights about skill development"""
        if not self.skills:
            return {'message': 'No skills tracked yet'}

        total_skills = len(self.skills)
        mastered_skills = len([s for s in self.skills.values() if s.proficiency >= 0.8])

        # Practice statistics
        recent_practice = [
            p for p in self.practice_history
            if (datetime.now() - p['timestamp']).days < 30
        ]

        avg_proficiency = sum(s.proficiency for s in self.skills.values()) / total_skills

        return {
            'total_skills': total_skills,
            'mastered_skills': mastered_skills,
            'mastery_rate': mastered_skills / total_skills,
            'average_proficiency': avg_proficiency,
            'recent_practice_sessions': len(recent_practice),
            'domain_proficiency': {d.value: p for d, p in self.domain_proficiency.items()},
            'most_practiced': self._get_most_practiced_skill(),
            'fastest_learner': self._get_fastest_learning_skill(),
            'needs_attention': await self.identify_skill_gaps()
        }

    def _get_most_practiced_skill(self) -> Optional[Dict[str, Any]]:
        """Get skill with most practice sessions"""
        if not self.skills:
            return None

        most_practiced = max(self.skills.values(), key=lambda s: s.practice_sessions)
        return {
            'name': most_practiced.name,
            'sessions': most_practiced.practice_sessions,
            'total_time': most_practiced.total_practice_time,
            'proficiency': most_practiced.proficiency
        }

    def _get_fastest_learning_skill(self) -> Optional[Dict[str, Any]]:
        """Get skill with fastest proficiency growth"""
        if not self.skills:
            return None

        # Calculate growth rate (proficiency per hour)
        fastest = None
        max_rate = 0

        for skill in self.skills.values():
            if skill.total_practice_time > 0:
                rate = skill.proficiency / skill.total_practice_time
                if rate > max_rate:
                    max_rate = rate
                    fastest = skill

        if fastest:
            return {
                'name': fastest.name,
                'proficiency': fastest.proficiency,
                'practice_time': fastest.total_practice_time,
                'learning_rate': max_rate
            }

        return None
