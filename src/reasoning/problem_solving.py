"""
Adaptive Problem Solving Framework for Claude-AGI
==================================================

General problem-solving system that decomposes problems, selects strategies,
and learns from outcomes.
"""

import asyncio
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class ProblemType(Enum):
    """Types of problems"""
    ANALYTICAL = "analytical"          # Logical analysis required
    CREATIVE = "creative"              # Novel solution needed
    OPTIMIZATION = "optimization"      # Find best solution
    DIAGNOSIS = "diagnosis"            # Identify root cause
    PLANNING = "planning"              # Sequence of actions
    LEARNING = "learning"              # Acquire new knowledge
    SOCIAL = "social"                  # Interpersonal problem


class StrategyType(Enum):
    """Problem-solving strategies"""
    DECOMPOSITION = "decomposition"    # Break into subproblems
    ANALOGY = "analogy"                # Use similar past problem
    BRAINSTORMING = "brainstorming"    # Generate many solutions
    SYSTEMATIC = "systematic"          # Methodical exploration
    HEURISTIC = "heuristic"            # Use rules of thumb
    TRIAL_ERROR = "trial_error"        # Try and learn
    CONSTRAINT = "constraint"          # Satisfy constraints
    OPTIMIZATION = "optimization"      # Maximize/minimize objective


@dataclass
class Problem:
    """Represents a problem to solve"""
    problem_id: str
    description: str
    problem_type: ProblemType
    constraints: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    resources_available: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    priority: float = 0.5
    deadline: Optional[datetime] = None


@dataclass
class Subproblem:
    """A component of a larger problem"""
    subproblem_id: str
    parent_problem_id: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"  # 'pending', 'in_progress', 'solved', 'failed'
    solution: Optional[str] = None


@dataclass
class Solution:
    """A proposed or implemented solution"""
    solution_id: str
    problem_id: str
    description: str
    strategy_used: StrategyType
    confidence: float
    estimated_effort: float
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    implementation_steps: List[str] = field(default_factory=list)
    outcome: Optional[str] = None
    effectiveness: Optional[float] = None


@dataclass
class ProblemSolvingSession:
    """A problem-solving session"""
    session_id: str
    problem: Problem
    strategies_attempted: List[StrategyType] = field(default_factory=list)
    solutions_generated: List[Solution] = field(default_factory=list)
    selected_solution: Optional[Solution] = None
    outcome: Optional[str] = None
    lessons_learned: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None


class ProblemSolvingFramework:
    """
    Adaptive problem-solving system that selects and applies strategies
    based on problem characteristics and past experience.
    """

    def __init__(self):
        # Problem tracking
        self.active_problems: Dict[str, Problem] = {}
        self.problem_history: deque = deque(maxlen=500)

        # Strategy performance tracking
        self.strategy_performance: Dict[Tuple[ProblemType, StrategyType], List[float]] = defaultdict(list)

        # Solution library
        self.solution_library: Dict[str, List[Solution]] = defaultdict(list)

        # Session tracking
        self.active_sessions: Dict[str, ProblemSolvingSession] = {}
        self.completed_sessions: deque = deque(maxlen=200)

        # Learning from outcomes
        self.success_patterns: List[Dict[str, Any]] = []

    async def analyze_problem(self, problem_description: str) -> Problem:
        """
        Analyze a problem to determine type and characteristics.

        Args:
            problem_description: Description of the problem

        Returns:
            Structured Problem object
        """
        # Detect problem type (simplified - would use NLP in production)
        problem_type = self._detect_problem_type(problem_description)

        # Extract constraints and criteria
        constraints = self._extract_constraints(problem_description)
        success_criteria = self._extract_success_criteria(problem_description)

        # Generate unique ID
        import uuid
        problem_id = str(uuid.uuid4())

        problem = Problem(
            problem_id=problem_id,
            description=problem_description,
            problem_type=problem_type,
            constraints=constraints,
            success_criteria=success_criteria
        )

        self.active_problems[problem_id] = problem

        logger.info(f"Analyzed problem: {problem_type.value} - {problem_description[:50]}...")

        return problem

    def _detect_problem_type(self, description: str) -> ProblemType:
        """Detect problem type from description"""
        desc_lower = description.lower()

        # Keywords for each problem type
        type_keywords = {
            ProblemType.ANALYTICAL: ['analyze', 'understand', 'explain', 'logic', 'reason'],
            ProblemType.CREATIVE: ['create', 'design', 'invent', 'novel', 'innovative'],
            ProblemType.OPTIMIZATION: ['best', 'optimize', 'improve', 'maximize', 'minimize'],
            ProblemType.DIAGNOSIS: ['diagnose', 'troubleshoot', 'debug', 'find cause', 'identify issue'],
            ProblemType.PLANNING: ['plan', 'schedule', 'organize', 'sequence', 'coordinate'],
            ProblemType.LEARNING: ['learn', 'understand', 'master', 'acquire', 'study'],
            ProblemType.SOCIAL: ['relationship', 'communication', 'social', 'interpersonal', 'conflict'],
        }

        # Count matches for each type
        type_scores = {}
        for ptype, keywords in type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in desc_lower)
            if score > 0:
                type_scores[ptype] = score

        # Return type with highest score, or ANALYTICAL as default
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        return ProblemType.ANALYTICAL

    def _extract_constraints(self, description: str) -> List[str]:
        """Extract constraints from problem description"""
        constraints = []

        # Look for constraint indicators
        constraint_phrases = [
            'must', 'cannot', 'limited to', 'restricted', 'required',
            'within', 'no more than', 'at least', 'constraint'
        ]

        import re
        sentences = re.split(r'[.!?]', description)

        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(phrase in sentence_lower for phrase in constraint_phrases):
                constraints.append(sentence.strip())

        return constraints

    def _extract_success_criteria(self, description: str) -> List[str]:
        """Extract success criteria from problem description"""
        criteria = []

        # Look for success indicators
        success_phrases = [
            'goal', 'objective', 'should', 'need to', 'want to',
            'achieve', 'accomplish', 'result in', 'success'
        ]

        import re
        sentences = re.split(r'[.!?]', description)

        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(phrase in sentence_lower for phrase in success_phrases):
                criteria.append(sentence.strip())

        return criteria

    async def decompose_problem(self, problem: Problem) -> List[Subproblem]:
        """
        Decompose a problem into manageable subproblems.

        Args:
            problem: The problem to decompose

        Returns:
            List of subproblems
        """
        subproblems = []

        # Simple decomposition heuristics
        if len(problem.description) > 200:
            # Large problem - break into phases
            subproblems.append(Subproblem(
                subproblem_id=f"{problem.problem_id}_analyze",
                parent_problem_id=problem.problem_id,
                description=f"Analyze and understand: {problem.description[:100]}..."
            ))
            subproblems.append(Subproblem(
                subproblem_id=f"{problem.problem_id}_plan",
                parent_problem_id=problem.problem_id,
                description="Plan solution approach",
                dependencies=[f"{problem.problem_id}_analyze"]
            ))
            subproblems.append(Subproblem(
                subproblem_id=f"{problem.problem_id}_execute",
                parent_problem_id=problem.problem_id,
                description="Execute solution",
                dependencies=[f"{problem.problem_id}_plan"]
            ))
            subproblems.append(Subproblem(
                subproblem_id=f"{problem.problem_id}_verify",
                parent_problem_id=problem.problem_id,
                description="Verify solution meets criteria",
                dependencies=[f"{problem.problem_id}_execute"]
            ))

        logger.info(f"Decomposed problem into {len(subproblems)} subproblems")

        return subproblems

    async def select_strategy(
        self,
        problem: Problem,
        context: Optional[Dict[str, Any]] = None
    ) -> StrategyType:
        """
        Select the most appropriate strategy for a problem.

        Args:
            problem: The problem to solve
            context: Optional context information

        Returns:
            Selected strategy
        """
        # Strategy selection based on problem type and past performance
        strategies_for_type = {
            ProblemType.ANALYTICAL: [StrategyType.SYSTEMATIC, StrategyType.DECOMPOSITION],
            ProblemType.CREATIVE: [StrategyType.BRAINSTORMING, StrategyType.ANALOGY],
            ProblemType.OPTIMIZATION: [StrategyType.OPTIMIZATION, StrategyType.HEURISTIC],
            ProblemType.DIAGNOSIS: [StrategyType.SYSTEMATIC, StrategyType.CONSTRAINT],
            ProblemType.PLANNING: [StrategyType.DECOMPOSITION, StrategyType.SYSTEMATIC],
            ProblemType.LEARNING: [StrategyType.SYSTEMATIC, StrategyType.TRIAL_ERROR],
            ProblemType.SOCIAL: [StrategyType.ANALOGY, StrategyType.BRAINSTORMING],
        }

        candidate_strategies = strategies_for_type.get(
            problem.problem_type,
            [StrategyType.SYSTEMATIC]
        )

        # If we have performance data, choose best-performing strategy
        best_strategy = candidate_strategies[0]
        best_performance = 0.0

        for strategy in candidate_strategies:
            key = (problem.problem_type, strategy)
            if key in self.strategy_performance:
                performances = self.strategy_performance[key]
                if performances:
                    avg_performance = sum(performances) / len(performances)
                    if avg_performance > best_performance:
                        best_performance = avg_performance
                        best_strategy = strategy

        logger.info(f"Selected strategy: {best_strategy.value} for {problem.problem_type.value} problem")

        return best_strategy

    async def generate_solution(
        self,
        problem: Problem,
        strategy: StrategyType
    ) -> Solution:
        """
        Generate a solution using the specified strategy.

        Args:
            problem: The problem to solve
            strategy: Strategy to use

        Returns:
            Generated solution
        """
        import uuid

        solution = Solution(
            solution_id=str(uuid.uuid4()),
            problem_id=problem.problem_id,
            description=f"Solution using {strategy.value} approach",
            strategy_used=strategy,
            confidence=0.7,  # Base confidence
            estimated_effort=0.5
        )

        # Strategy-specific solution generation
        if strategy == StrategyType.DECOMPOSITION:
            subproblems = await self.decompose_problem(problem)
            solution.implementation_steps = [
                f"Solve: {sp.description}" for sp in subproblems
            ]
            solution.pros = ["Manageable chunks", "Clear progress tracking"]
            solution.cons = ["May miss holistic insights", "Overhead of coordination"]

        elif strategy == StrategyType.BRAINSTORMING:
            solution.description = "Generate multiple creative approaches and select best"
            solution.implementation_steps = [
                "Generate diverse ideas (5+ approaches)",
                "Evaluate each against criteria",
                "Select most promising",
                "Refine selected approach"
            ]
            solution.pros = ["Explores solution space", "May find novel approach"]
            solution.cons = ["Time-consuming", "May generate impractical ideas"]

        elif strategy == StrategyType.SYSTEMATIC:
            solution.description = "Methodically explore solution space"
            solution.implementation_steps = [
                "Identify all relevant factors",
                "Systematically test combinations",
                "Eliminate infeasible options",
                "Optimize remaining candidates"
            ]
            solution.pros = ["Thorough", "Less likely to miss solutions"]
            solution.cons = ["Time-intensive", "May be overkill for simple problems"]

        elif strategy == StrategyType.ANALOGY:
            solution.description = "Apply solution from similar past problem"
            solution.implementation_steps = [
                "Find similar past problem",
                "Extract relevant patterns",
                "Adapt to current context",
                "Verify applicability"
            ]
            solution.pros = ["Leverages experience", "Faster than from scratch"]
            solution.cons = ["May miss important differences", "Requires good analogies"]

        # Add to solution library
        self.solution_library[problem.problem_type.value].append(solution)

        return solution

    async def evaluate_solution(
        self,
        solution: Solution,
        problem: Problem
    ) -> float:
        """
        Evaluate a solution's likelihood of success.

        Args:
            solution: Solution to evaluate
            problem: The problem it solves

        Returns:
            Evaluation score (0-1)
        """
        score = solution.confidence

        # Adjust based on pros/cons
        score += len(solution.pros) * 0.05
        score -= len(solution.cons) * 0.05

        # Adjust based on past strategy performance
        key = (problem.problem_type, solution.strategy_used)
        if key in self.strategy_performance:
            performances = self.strategy_performance[key]
            if performances:
                avg_performance = sum(performances) / len(performances)
                score = (score + avg_performance) / 2

        # Clamp to 0-1
        return max(0.0, min(1.0, score))

    async def start_problem_solving_session(
        self,
        problem: Problem
    ) -> ProblemSolvingSession:
        """
        Start a problem-solving session.

        Args:
            problem: Problem to solve

        Returns:
            Problem-solving session
        """
        import uuid

        session = ProblemSolvingSession(
            session_id=str(uuid.uuid4()),
            problem=problem
        )

        self.active_sessions[session.session_id] = session

        logger.info(f"Started problem-solving session for: {problem.description[:50]}...")

        return session

    async def solve_problem(
        self,
        problem: Problem,
        max_iterations: int = 5
    ) -> Optional[Solution]:
        """
        Solve a problem using adaptive strategy selection.

        Args:
            problem: Problem to solve
            max_iterations: Maximum solution attempts

        Returns:
            Selected solution or None
        """
        session = await self.start_problem_solving_session(problem)

        best_solution = None
        best_score = 0.0

        for i in range(max_iterations):
            # Select strategy
            strategy = await self.select_strategy(problem)
            session.strategies_attempted.append(strategy)

            # Generate solution
            solution = await self.generate_solution(problem, strategy)
            session.solutions_generated.append(solution)

            # Evaluate solution
            score = await self.evaluate_solution(solution, problem)

            if score > best_score:
                best_score = score
                best_solution = solution

            # If we found a very good solution, stop early
            if best_score > 0.85:
                break

        session.selected_solution = best_solution
        session.end_time = datetime.now()

        # Move to completed sessions
        self.completed_sessions.append(session)
        if session.session_id in self.active_sessions:
            del self.active_sessions[session.session_id]

        logger.info(f"Solved problem with {best_solution.strategy_used.value if best_solution else 'no'} solution (score: {best_score:.2f})")

        return best_solution

    async def record_outcome(
        self,
        solution: Solution,
        problem: Problem,
        effectiveness: float,
        lessons_learned: Optional[List[str]] = None
    ):
        """
        Record the outcome of applying a solution.

        Args:
            solution: The solution that was applied
            problem: The problem it was applied to
            effectiveness: How effective it was (0-1)
            lessons_learned: Optional lessons learned
        """
        solution.effectiveness = effectiveness

        # Update strategy performance
        key = (problem.problem_type, solution.strategy_used)
        self.strategy_performance[key].append(effectiveness)

        # Record success patterns if effective
        if effectiveness > 0.7:
            pattern = {
                'problem_type': problem.problem_type.value,
                'strategy': solution.strategy_used.value,
                'effectiveness': effectiveness,
                'constraints': problem.constraints,
                'timestamp': datetime.now()
            }
            self.success_patterns.append(pattern)

        # Store lessons learned
        if lessons_learned:
            for session in self.completed_sessions:
                if session.selected_solution and session.selected_solution.solution_id == solution.solution_id:
                    session.lessons_learned.extend(lessons_learned)
                    break

        logger.info(f"Recorded outcome: {effectiveness:.2f} effectiveness for {solution.strategy_used.value}")

    async def get_problem_solving_statistics(self) -> Dict[str, Any]:
        """Get statistics about problem-solving performance"""
        total_sessions = len(self.completed_sessions)

        if total_sessions == 0:
            return {}

        # Calculate strategy success rates
        strategy_stats = {}
        for (ptype, strategy), performances in self.strategy_performance.items():
            if performances:
                strategy_stats[f"{ptype.value}_{strategy.value}"] = {
                    'attempts': len(performances),
                    'avg_effectiveness': sum(performances) / len(performances)
                }

        # Count problem types solved
        problem_types = defaultdict(int)
        for session in self.completed_sessions:
            problem_types[session.problem.problem_type.value] += 1

        return {
            'total_sessions': total_sessions,
            'active_sessions': len(self.active_sessions),
            'problem_types_solved': dict(problem_types),
            'strategy_performance': strategy_stats,
            'success_patterns_learned': len(self.success_patterns),
            'solution_library_size': sum(len(sols) for sols in self.solution_library.values())
        }
