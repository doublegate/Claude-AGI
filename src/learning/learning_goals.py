"""
Learning Goal Formation and Management
======================================

Creates and manages learning goals based on knowledge gaps,
curiosity, and strategic learning priorities.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Set
import uuid

logger = logging.getLogger(__name__)


class GoalType(Enum):
    """Types of learning goals"""
    EPISTEMIC = "epistemic"  # Understanding deeper concepts
    SKILL = "skill"           # Acquiring practical skills
    EXPLORATION = "exploration"  # Exploring new domains
    MASTERY = "mastery"       # Achieving mastery in a topic
    INTEGRATION = "integration"  # Connecting disparate knowledge


class GoalStatus(Enum):
    """Status of a learning goal"""
    CREATED = "created"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class LearningGoal:
    """Represents a learning goal"""
    goal_id: str
    title: str
    description: str
    goal_type: GoalType
    status: GoalStatus
    priority: float  # 0-1
    difficulty: float  # 0-1
    estimated_effort: int  # In hours
    actual_effort: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    prerequisites: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    progress: float = 0.0  # 0-1
    sub_goals: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    milestones: List[Dict] = field(default_factory=list)
    notes: str = ""


@dataclass
class LearningPath:
    """A structured path to achieve a learning goal"""
    path_id: str
    goal_id: str
    steps: List[Dict]  # List of learning steps
    current_step: int = 0
    estimated_duration: int = 0  # In hours
    created_at: datetime = field(default_factory=datetime.now)


class LearningGoalManager:
    """
    Manages learning goals, creates learning paths, and tracks progress.
    """

    def __init__(self, knowledge_graph=None, curiosity_engine=None):
        self.knowledge_graph = knowledge_graph
        self.curiosity_engine = curiosity_engine

        self.goals: Dict[str, LearningGoal] = {}
        self.learning_paths: Dict[str, LearningPath] = {}
        self.goal_history: List[Dict] = []

        # Goal formation parameters
        self.max_concurrent_goals = 5
        self.min_priority_threshold = 0.3

    async def create_goal(
        self,
        title: str,
        description: str,
        goal_type: GoalType,
        priority: float = 0.5,
        difficulty: float = 0.5,
        prerequisites: List[str] = None,
        related_concepts: List[str] = None
    ) -> LearningGoal:
        """
        Create a new learning goal.

        Args:
            title: Goal title
            description: Detailed description
            goal_type: Type of goal
            priority: Priority (0-1)
            difficulty: Estimated difficulty (0-1)
            prerequisites: Prerequisite goals
            related_concepts: Related concept names

        Returns:
            Created learning goal
        """
        goal_id = str(uuid.uuid4())

        # Estimate effort based on difficulty and type
        base_effort = {
            GoalType.EPISTEMIC: 10,
            GoalType.SKILL: 20,
            GoalType.EXPLORATION: 5,
            GoalType.MASTERY: 50,
            GoalType.INTEGRATION: 15
        }
        estimated_effort = int(base_effort[goal_type] * (1 + difficulty))

        goal = LearningGoal(
            goal_id=goal_id,
            title=title,
            description=description,
            goal_type=goal_type,
            status=GoalStatus.CREATED,
            priority=priority,
            difficulty=difficulty,
            estimated_effort=estimated_effort,
            prerequisites=prerequisites or [],
            related_concepts=related_concepts or []
        )

        self.goals[goal_id] = goal

        logger.info(f"Created learning goal: {title} ({goal_type.value})")

        return goal

    async def create_goal_from_knowledge_gap(
        self,
        gap: 'KnowledgeGap'
    ) -> LearningGoal:
        """
        Create a learning goal to fill a knowledge gap.

        Args:
            gap: Knowledge gap to address

        Returns:
            Created learning goal
        """
        # Determine goal type based on gap type
        goal_type_mapping = {
            'missing_concept': GoalType.EPISTEMIC,
            'weak_understanding': GoalType.MASTERY,
            'contradiction': GoalType.INTEGRATION
        }

        goal_type = goal_type_mapping.get(gap.gap_type, GoalType.EPISTEMIC)

        title = f"Understand {gap.topic}"
        description = f"Fill knowledge gap: {gap.evidence}"

        goal = await self.create_goal(
            title=title,
            description=description,
            goal_type=goal_type,
            priority=gap.importance,
            difficulty=0.5,
            related_concepts=gap.related_concepts
        )

        return goal

    async def create_goal_from_curiosity(
        self,
        question: 'CuriosityQuestion'
    ) -> LearningGoal:
        """
        Create a learning goal from a curiosity question.

        Args:
            question: Curiosity question

        Returns:
            Created learning goal
        """
        # Map curiosity type to goal type
        goal_type_mapping = {
            'epistemic': GoalType.EPISTEMIC,
            'perceptual': GoalType.EXPLORATION,
            'specific': GoalType.SKILL,
            'diversive': GoalType.EXPLORATION
        }

        goal_type = goal_type_mapping.get(
            question.curiosity_type.value,
            GoalType.EXPLORATION
        )

        title = f"Answer: {question.question}"
        description = f"Explore question driven by {question.curiosity_type.value} curiosity"

        goal = await self.create_goal(
            title=title,
            description=description,
            goal_type=goal_type,
            priority=question.priority,
            difficulty=0.3,
            related_concepts=question.related_concepts
        )

        return goal

    async def generate_learning_path(
        self,
        goal_id: str
    ) -> Optional[LearningPath]:
        """
        Generate a structured learning path for a goal.

        Args:
            goal_id: ID of the learning goal

        Returns:
            Generated learning path
        """
        goal = self.goals.get(goal_id)
        if not goal:
            return None

        # Generate steps based on goal type and related concepts
        steps = []

        if goal.goal_type == GoalType.EPISTEMIC:
            # Understanding-focused path
            steps = [
                {
                    'step_number': 1,
                    'title': f'Research fundamentals of {goal.related_concepts[0] if goal.related_concepts else goal.title}',
                    'description': 'Gather basic information and definitions',
                    'estimated_duration': 2,
                    'resources': [],
                    'completed': False
                },
                {
                    'step_number': 2,
                    'title': 'Understand core mechanisms',
                    'description': 'Learn how the concepts work',
                    'estimated_duration': 4,
                    'resources': [],
                    'completed': False
                },
                {
                    'step_number': 3,
                    'title': 'Explore connections',
                    'description': 'Understand how this relates to other knowledge',
                    'estimated_duration': 3,
                    'resources': [],
                    'completed': False
                },
                {
                    'step_number': 4,
                    'title': 'Synthesize understanding',
                    'description': 'Create comprehensive mental model',
                    'estimated_duration': 2,
                    'resources': [],
                    'completed': False
                }
            ]

        elif goal.goal_type == GoalType.SKILL:
            # Skill acquisition path
            steps = [
                {
                    'step_number': 1,
                    'title': 'Learn theory',
                    'description': 'Understand theoretical foundations',
                    'estimated_duration': 3,
                    'resources': [],
                    'completed': False
                },
                {
                    'step_number': 2,
                    'title': 'Practice basics',
                    'description': 'Apply basic techniques',
                    'estimated_duration': 5,
                    'resources': [],
                    'completed': False
                },
                {
                    'step_number': 3,
                    'title': 'Advanced practice',
                    'description': 'Work on complex applications',
                    'estimated_duration': 8,
                    'resources': [],
                    'completed': False
                },
                {
                    'step_number': 4,
                    'title': 'Build project',
                    'description': 'Create practical demonstration',
                    'estimated_duration': 10,
                    'resources': [],
                    'completed': False
                }
            ]

        elif goal.goal_type == GoalType.EXPLORATION:
            # Exploratory path
            steps = [
                {
                    'step_number': 1,
                    'title': 'Survey landscape',
                    'description': 'Get broad overview of domain',
                    'estimated_duration': 2,
                    'resources': [],
                    'completed': False
                },
                {
                    'step_number': 2,
                    'title': 'Identify interesting areas',
                    'description': 'Find topics worth deeper investigation',
                    'estimated_duration': 3,
                    'resources': [],
                    'completed': False
                },
                {
                    'step_number': 3,
                    'title': 'Deep dive',
                    'description': 'Explore selected topics in detail',
                    'estimated_duration': 5,
                    'resources': [],
                    'completed': False
                }
            ]

        else:
            # Generic learning path
            steps = [
                {
                    'step_number': 1,
                    'title': 'Initial research',
                    'description': 'Gather information',
                    'estimated_duration': 3,
                    'resources': [],
                    'completed': False
                },
                {
                    'step_number': 2,
                    'title': 'Deep study',
                    'description': 'Comprehensive learning',
                    'estimated_duration': 8,
                    'resources': [],
                    'completed': False
                },
                {
                    'step_number': 3,
                    'title': 'Application',
                    'description': 'Apply knowledge',
                    'estimated_duration': 5,
                    'resources': [],
                    'completed': False
                }
            ]

        path = LearningPath(
            path_id=str(uuid.uuid4()),
            goal_id=goal_id,
            steps=steps,
            estimated_duration=sum(s['estimated_duration'] for s in steps)
        )

        self.learning_paths[path.path_id] = path

        logger.info(f"Generated learning path for goal: {goal.title} ({len(steps)} steps)")

        return path

    async def update_goal_progress(
        self,
        goal_id: str,
        progress_delta: float,
        effort_hours: int = 0
    ) -> Optional[LearningGoal]:
        """
        Update progress on a learning goal.

        Args:
            goal_id: Goal ID
            progress_delta: Change in progress (0-1)
            effort_hours: Hours of effort invested

        Returns:
            Updated goal
        """
        goal = self.goals.get(goal_id)
        if not goal:
            return None

        # Update progress
        goal.progress = min(1.0, goal.progress + progress_delta)
        goal.actual_effort += effort_hours

        # Update status based on progress
        if goal.progress >= 1.0:
            goal.status = GoalStatus.COMPLETED
            logger.info(f"Goal completed: {goal.title}")
        elif goal.progress > 0:
            goal.status = GoalStatus.IN_PROGRESS

        # Record in history
        self.goal_history.append({
            'timestamp': datetime.now(),
            'goal_id': goal_id,
            'progress': goal.progress,
            'effort': goal.actual_effort,
            'status': goal.status.value
        })

        return goal

    async def prioritize_goals(self) -> List[LearningGoal]:
        """
        Prioritize active goals based on multiple factors.

        Returns:
            List of goals sorted by priority
        """
        active_goals = [
            g for g in self.goals.values()
            if g.status in [GoalStatus.ACTIVE, GoalStatus.IN_PROGRESS]
        ]

        # Calculate effective priority
        for goal in active_goals:
            # Base priority
            effective_priority = goal.priority

            # Boost if prerequisites are met
            prereq_met = all(
                self.goals.get(pid, {}).get('status') == GoalStatus.COMPLETED
                for pid in goal.prerequisites
            )
            if prereq_met:
                effective_priority *= 1.2

            # Boost if approaching deadline
            if goal.deadline:
                days_remaining = (goal.deadline - datetime.now()).days
                if days_remaining < 7:
                    effective_priority *= 1.5
                elif days_remaining < 30:
                    effective_priority *= 1.2

            # Penalize if stalled
            if goal.status == GoalStatus.PAUSED:
                effective_priority *= 0.5

            goal.priority = min(1.0, effective_priority)

        # Sort by priority
        sorted_goals = sorted(active_goals, key=lambda g: g.priority, reverse=True)

        return sorted_goals

    async def suggest_next_actions(
        self,
        max_suggestions: int = 5
    ) -> List[Dict]:
        """
        Suggest next learning actions to take.

        Args:
            max_suggestions: Maximum suggestions

        Returns:
            List of suggested actions
        """
        suggestions = []

        # Get prioritized goals
        prioritized = await self.prioritize_goals()

        for goal in prioritized[:max_suggestions]:
            # Get learning path
            path = None
            for p in self.learning_paths.values():
                if p.goal_id == goal.goal_id:
                    path = p
                    break

            if path and path.current_step < len(path.steps):
                # Suggest next step in path
                next_step = path.steps[path.current_step]
                suggestions.append({
                    'action_type': 'continue_path',
                    'goal': goal.title,
                    'step': next_step['title'],
                    'description': next_step['description'],
                    'estimated_duration': next_step['estimated_duration'],
                    'priority': goal.priority
                })
            else:
                # Suggest starting the goal
                suggestions.append({
                    'action_type': 'start_goal',
                    'goal': goal.title,
                    'description': goal.description,
                    'estimated_effort': goal.estimated_effort,
                    'priority': goal.priority
                })

        return suggestions

    def get_goal_statistics(self) -> Dict[str, any]:
        """Get statistics about learning goals"""
        total = len(self.goals)
        by_status = {}
        by_type = {}

        for goal in self.goals.values():
            by_status[goal.status.value] = by_status.get(goal.status.value, 0) + 1
            by_type[goal.goal_type.value] = by_type.get(goal.goal_type.value, 0) + 1

        completed = by_status.get('completed', 0)
        avg_progress = sum(g.progress for g in self.goals.values()) / total if total > 0 else 0

        return {
            'total_goals': total,
            'by_status': by_status,
            'by_type': by_type,
            'completion_rate': completed / total if total > 0 else 0,
            'average_progress': avg_progress,
            'total_paths': len(self.learning_paths),
            'total_effort': sum(g.actual_effort for g in self.goals.values())
        }


async def demo():
    """Demo learning goal management"""
    manager = LearningGoalManager()

    # Create some goals
    goal1 = await manager.create_goal(
        title="Master Python Programming",
        description="Achieve proficiency in Python",
        goal_type=GoalType.SKILL,
        priority=0.9,
        difficulty=0.6
    )

    goal2 = await manager.create_goal(
        title="Understand Quantum Computing",
        description="Learn quantum computing principles",
        goal_type=GoalType.EPISTEMIC,
        priority=0.7,
        difficulty=0.8
    )

    # Generate learning path
    path = await manager.generate_learning_path(goal1.goal_id)

    print(f"\nLearning Path for: {goal1.title}")
    print(f"  Total steps: {len(path.steps)}")
    print(f"  Estimated duration: {path.estimated_duration} hours")
    for step in path.steps:
        print(f"    {step['step_number']}. {step['title']} ({step['estimated_duration']}h)")

    # Get suggestions
    suggestions = await manager.suggest_next_actions()
    print(f"\nSuggested Next Actions:")
    for suggestion in suggestions:
        print(f"  - {suggestion['action_type']}: {suggestion['goal']}")

    # Stats
    stats = manager.get_goal_statistics()
    print(f"\nGoal Statistics:")
    print(f"  Total goals: {stats['total_goals']}")
    print(f"  By type: {stats['by_type']}")


if __name__ == "__main__":
    asyncio.run(demo())
