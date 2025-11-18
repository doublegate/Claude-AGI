"""
Goal Management System for Claude-AGI
======================================

Manages goal formation, tracking, prioritization, and achievement
for autonomous learning and development.
"""

import asyncio
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class GoalStatus(Enum):
    """Status of a goal"""
    PROPOSED = "proposed"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"
    PAUSED = "paused"


class GoalPriority(Enum):
    """Priority levels for goals"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    OPTIONAL = 1


class GoalType(Enum):
    """Types of goals"""
    IMMEDIATE = "immediate"        # Current conversation
    SESSION = "session"            # This interaction period
    PROJECT = "project"            # Creative/learning projects
    LONG_TERM = "long_term"       # Long-term aspirations
    VALUE_ALIGNED = "value_aligned"  # Value-driven objectives
    EXPLORATION = "exploration"    # Discovery-based goals


@dataclass
class Goal:
    """Represents a goal with associated metadata"""
    id: str
    description: str
    goal_type: GoalType
    priority: GoalPriority
    status: GoalStatus
    created_at: datetime
    updated_at: datetime
    target_completion: Optional[datetime] = None
    progress: float = 0.0
    parent_goal_id: Optional[str] = None
    child_goal_ids: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """Convert goal to dictionary"""
        return {
            'id': self.id,
            'description': self.description,
            'goal_type': self.goal_type.value,
            'priority': self.priority.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'target_completion': self.target_completion.isoformat() if self.target_completion else None,
            'progress': self.progress,
            'parent_goal_id': self.parent_goal_id,
            'child_goal_ids': self.child_goal_ids,
            'prerequisites': self.prerequisites,
            'success_criteria': self.success_criteria,
            'milestones': self.milestones,
            'metadata': self.metadata,
            'tags': list(self.tags)
        }


class GoalManager:
    """
    Manages goal lifecycle, hierarchy, and progress tracking.
    Implements goal-directed learning and autonomous goal formation.
    """

    def __init__(self):
        # Goal storage
        self.goals: Dict[str, Goal] = {}
        self.active_goals: List[str] = []
        self.completed_goals: List[str] = []

        # Goal relationships
        self.goal_hierarchy: Dict[str, List[str]] = defaultdict(list)
        self.goal_dependencies: Dict[str, Set[str]] = defaultdict(set)

        # Achievement tracking
        self.achievement_history: List[Dict[str, Any]] = []
        self.success_rate: Dict[GoalType, float] = {}

        # Strategy tracking
        self.successful_strategies: Dict[str, int] = defaultdict(int)
        self.failed_strategies: Dict[str, int] = defaultdict(int)

        # Exploration-driven goals
        self.interest_to_goals: Dict[str, List[str]] = defaultdict(list)

    async def create_goal(
        self,
        description: str,
        goal_type: GoalType,
        priority: GoalPriority,
        parent_goal_id: Optional[str] = None,
        prerequisites: Optional[List[str]] = None,
        success_criteria: Optional[List[str]] = None,
        target_completion: Optional[datetime] = None,
        tags: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Goal:
        """Create a new goal"""
        goal_id = str(uuid.uuid4())

        goal = Goal(
            id=goal_id,
            description=description,
            goal_type=goal_type,
            priority=priority,
            status=GoalStatus.PROPOSED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            target_completion=target_completion,
            parent_goal_id=parent_goal_id,
            prerequisites=prerequisites or [],
            success_criteria=success_criteria or [],
            tags=tags or set(),
            metadata=metadata or {}
        )

        self.goals[goal_id] = goal

        # Update hierarchy
        if parent_goal_id and parent_goal_id in self.goals:
            self.goals[parent_goal_id].child_goal_ids.append(goal_id)
            self.goal_hierarchy[parent_goal_id].append(goal_id)

        # Update dependencies
        if prerequisites:
            for prereq in prerequisites:
                self.goal_dependencies[goal_id].add(prereq)

        logger.info(f"Created goal: {description} (ID: {goal_id})")
        return goal

    async def activate_goal(self, goal_id: str) -> bool:
        """Activate a goal if prerequisites are met"""
        if goal_id not in self.goals:
            logger.error(f"Goal not found: {goal_id}")
            return False

        goal = self.goals[goal_id]

        # Check prerequisites
        if not await self._check_prerequisites(goal_id):
            logger.warning(f"Prerequisites not met for goal: {goal.description}")
            return False

        goal.status = GoalStatus.ACTIVE
        goal.updated_at = datetime.now()

        if goal_id not in self.active_goals:
            self.active_goals.append(goal_id)

        logger.info(f"Activated goal: {goal.description}")
        return True

    async def _check_prerequisites(self, goal_id: str) -> bool:
        """Check if all prerequisites for a goal are met"""
        if goal_id not in self.goal_dependencies:
            return True

        for prereq_id in self.goal_dependencies[goal_id]:
            if prereq_id not in self.goals:
                continue

            prereq_goal = self.goals[prereq_id]
            if prereq_goal.status != GoalStatus.COMPLETED:
                return False

        return True

    async def update_progress(self, goal_id: str, progress: float, milestone_reached: Optional[str] = None):
        """Update goal progress"""
        if goal_id not in self.goals:
            logger.error(f"Goal not found: {goal_id}")
            return

        goal = self.goals[goal_id]
        goal.progress = min(1.0, max(0.0, progress))
        goal.updated_at = datetime.now()

        # Update status based on progress
        if goal.progress >= 1.0:
            goal.status = GoalStatus.COMPLETED
            await self._handle_goal_completion(goal_id)
        elif goal.progress > 0.0 and goal.status == GoalStatus.ACTIVE:
            goal.status = GoalStatus.IN_PROGRESS

        # Record milestone
        if milestone_reached:
            goal.milestones.append({
                'name': milestone_reached,
                'achieved_at': datetime.now(),
                'progress': progress
            })
            logger.info(f"Milestone reached for goal '{goal.description}': {milestone_reached}")

    async def _handle_goal_completion(self, goal_id: str):
        """Handle goal completion and activate dependent goals"""
        goal = self.goals[goal_id]

        # Move to completed
        if goal_id in self.active_goals:
            self.active_goals.remove(goal_id)
        self.completed_goals.append(goal_id)

        # Record achievement
        self.achievement_history.append({
            'goal_id': goal_id,
            'description': goal.description,
            'completed_at': datetime.now(),
            'duration': (datetime.now() - goal.created_at).total_seconds(),
            'goal_type': goal.goal_type.value
        })

        # Update success rate
        await self._update_success_rate(goal.goal_type)

        # Activate child goals
        for child_id in goal.child_goal_ids:
            await self.activate_goal(child_id)

        # Check for dependent goals
        for other_id, deps in self.goal_dependencies.items():
            if goal_id in deps and other_id not in self.active_goals:
                await self.activate_goal(other_id)

        logger.info(f"Goal completed: {goal.description}")

    async def _update_success_rate(self, goal_type: GoalType):
        """Update success rate for goal type"""
        completed = len([g for g in self.completed_goals
                        if self.goals[g].goal_type == goal_type])
        failed = len([g for g_id, g in self.goals.items()
                     if g.goal_type == goal_type and g.status == GoalStatus.FAILED])

        total = completed + failed
        if total > 0:
            self.success_rate[goal_type] = completed / total

    async def prioritize_goals(self) -> List[str]:
        """Prioritize active goals based on priority, deadline, and dependencies"""
        active_goals = [self.goals[g_id] for g_id in self.active_goals if g_id in self.goals]

        # Multi-factor scoring
        def score_goal(goal: Goal) -> float:
            score = goal.priority.value * 10

            # Deadline urgency
            if goal.target_completion:
                days_remaining = (goal.target_completion - datetime.now()).days
                if days_remaining < 7:
                    score += 20
                elif days_remaining < 30:
                    score += 10

            # Progress momentum
            if goal.progress > 0:
                score += goal.progress * 5

            # Unblocking factor (has dependents)
            if goal.id in self.goal_hierarchy:
                score += len(self.goal_hierarchy[goal.id]) * 2

            return score

        sorted_goals = sorted(active_goals, key=score_goal, reverse=True)
        return [g.id for g in sorted_goals]

    async def generate_goal_from_interest(self, interest: str, learning_data: Dict[str, Any]) -> Optional[Goal]:
        """Generate a learning goal from discovered interest"""
        # Analyze interest strength and novelty
        interest_strength = learning_data.get('strength', 0.5)
        if interest_strength < 0.6:
            return None

        # Create learning objective
        description = f"Develop expertise in {interest}"

        # Determine timeline based on complexity
        complexity = learning_data.get('complexity', 'medium')
        if complexity == 'simple':
            target = datetime.now() + timedelta(weeks=2)
        elif complexity == 'medium':
            target = datetime.now() + timedelta(weeks=8)
        else:
            target = datetime.now() + timedelta(weeks=16)

        # Create goal
        goal = await self.create_goal(
            description=description,
            goal_type=GoalType.EXPLORATION,
            priority=GoalPriority.MEDIUM,
            target_completion=target,
            success_criteria=[
                f"Understand fundamental concepts of {interest}",
                f"Explore multiple perspectives on {interest}",
                f"Create synthesis or original insight about {interest}"
            ],
            tags={interest, 'exploration', 'learning'},
            metadata={
                'interest': interest,
                'strength': interest_strength,
                'complexity': complexity,
                'auto_generated': True
            }
        )

        # Track interest-goal relationship
        self.interest_to_goals[interest].append(goal.id)

        return goal

    async def reflect_on_progress(self) -> Dict[str, Any]:
        """Generate reflection on goal progress and achievements"""
        total_goals = len(self.goals)
        completed = len(self.completed_goals)
        active = len(self.active_goals)

        # Calculate completion rate by type
        type_stats = {}
        for goal_type in GoalType:
            goals_of_type = [g for g in self.goals.values() if g.goal_type == goal_type]
            completed_of_type = [g for g in goals_of_type if g.status == GoalStatus.COMPLETED]
            type_stats[goal_type.value] = {
                'total': len(goals_of_type),
                'completed': len(completed_of_type),
                'completion_rate': len(completed_of_type) / len(goals_of_type) if goals_of_type else 0.0
            }

        # Recent achievements
        recent_achievements = [
            a for a in self.achievement_history
            if (datetime.now() - a['completed_at']).days < 30
        ]

        return {
            'total_goals': total_goals,
            'completed_goals': completed,
            'active_goals': active,
            'completion_rate': completed / total_goals if total_goals > 0 else 0.0,
            'type_statistics': type_stats,
            'recent_achievements': len(recent_achievements),
            'success_rates': {k.value: v for k, v in self.success_rate.items()},
            'average_completion_time': self._calculate_average_completion_time()
        }

    def _calculate_average_completion_time(self) -> float:
        """Calculate average time to complete goals"""
        if not self.achievement_history:
            return 0.0

        durations = [a['duration'] for a in self.achievement_history]
        return sum(durations) / len(durations) if durations else 0.0

    async def get_goal_hierarchy(self, root_goal_id: Optional[str] = None) -> Dict[str, Any]:
        """Get hierarchical representation of goals"""
        def build_tree(goal_id: str) -> Dict[str, Any]:
            if goal_id not in self.goals:
                return {}

            goal = self.goals[goal_id]
            return {
                'id': goal_id,
                'description': goal.description,
                'status': goal.status.value,
                'progress': goal.progress,
                'children': [build_tree(child_id) for child_id in goal.child_goal_ids]
            }

        if root_goal_id:
            return build_tree(root_goal_id)

        # Return all root goals
        root_goals = [g_id for g_id, g in self.goals.items() if g.parent_goal_id is None]
        return {
            'roots': [build_tree(g_id) for g_id in root_goals]
        }

    async def abandon_goal(self, goal_id: str, reason: str):
        """Abandon a goal with reason"""
        if goal_id not in self.goals:
            return

        goal = self.goals[goal_id]
        goal.status = GoalStatus.ABANDONED
        goal.updated_at = datetime.now()
        goal.metadata['abandonment_reason'] = reason

        if goal_id in self.active_goals:
            self.active_goals.remove(goal_id)

        logger.info(f"Goal abandoned: {goal.description} - Reason: {reason}")

    async def revise_goal(self, goal_id: str, updates: Dict[str, Any]):
        """Revise a goal with new parameters"""
        if goal_id not in self.goals:
            return

        goal = self.goals[goal_id]

        if 'description' in updates:
            goal.description = updates['description']
        if 'priority' in updates and isinstance(updates['priority'], GoalPriority):
            goal.priority = updates['priority']
        if 'target_completion' in updates:
            goal.target_completion = updates['target_completion']
        if 'success_criteria' in updates:
            goal.success_criteria = updates['success_criteria']

        goal.updated_at = datetime.now()
        goal.metadata['revised'] = True
        goal.metadata['revision_history'] = goal.metadata.get('revision_history', [])
        goal.metadata['revision_history'].append({
            'revised_at': datetime.now(),
            'changes': list(updates.keys())
        })

        logger.info(f"Goal revised: {goal.description}")
