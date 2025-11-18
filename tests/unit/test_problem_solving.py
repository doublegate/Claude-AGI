"""
Unit Tests for Problem Solving Framework
=========================================

Tests for adaptive problem-solving and strategy selection.
"""

import pytest
from src.reasoning.problem_solving import (
    ProblemSolvingFramework,
    Problem,
    Subproblem,
    Solution,
    ProblemType,
    StrategyType,
    ProblemSolvingSession
)


class TestProblemSolvingFramework:
    """Test the ProblemSolvingFramework class"""

    @pytest.fixture
    def framework(self):
        """Create a problem-solving framework"""
        return ProblemSolvingFramework()

    @pytest.mark.asyncio
    async def test_analyze_problem_analytical(self, framework):
        """Test analyzing an analytical problem"""
        problem = await framework.analyze_problem(
            "Analyze the performance bottlenecks in this system"
        )

        assert isinstance(problem, Problem)
        assert problem.problem_type == ProblemType.ANALYTICAL
        assert len(problem.problem_id) > 0

    @pytest.mark.asyncio
    async def test_analyze_problem_creative(self, framework):
        """Test analyzing a creative problem"""
        problem = await framework.analyze_problem(
            "Design an innovative solution for user engagement"
        )

        assert problem.problem_type == ProblemType.CREATIVE

    @pytest.mark.asyncio
    async def test_analyze_problem_optimization(self, framework):
        """Test analyzing an optimization problem"""
        problem = await framework.analyze_problem(
            "Find the best way to minimize latency"
        )

        assert problem.problem_type == ProblemType.OPTIMIZATION

    @pytest.mark.asyncio
    async def test_analyze_problem_diagnosis(self, framework):
        """Test analyzing a diagnostic problem"""
        problem = await framework.analyze_problem(
            "Diagnose the root cause of the system crash"
        )

        assert problem.problem_type == ProblemType.DIAGNOSIS

    @pytest.mark.asyncio
    async def test_extract_constraints(self, framework):
        """Test constraint extraction"""
        description = "Solve this problem. Must complete within budget. Cannot exceed 100MB memory."

        problem = await framework.analyze_problem(description)

        # Should extract constraint sentences
        assert len(problem.constraints) > 0
        assert any("must" in c.lower() or "cannot" in c.lower() for c in problem.constraints)

    @pytest.mark.asyncio
    async def test_extract_success_criteria(self, framework):
        """Test success criteria extraction"""
        description = "The goal is to improve performance. Need to achieve 99% uptime."

        problem = await framework.analyze_problem(description)

        assert len(problem.success_criteria) > 0

    @pytest.mark.asyncio
    async def test_decompose_problem_large(self, framework):
        """Test decomposing a large problem"""
        description = "Build a complete web application with user authentication, " \
                     "database integration, API endpoints, and real-time features. " \
                     "It should be scalable, secure, and performant."

        problem = await framework.analyze_problem(description)
        subproblems = await framework.decompose_problem(problem)

        # Large problem should be decomposed
        assert len(subproblems) > 0
        assert all(isinstance(sp, Subproblem) for sp in subproblems)

    @pytest.mark.asyncio
    async def test_decompose_problem_dependencies(self, framework):
        """Test that subproblems have dependencies"""
        description = "A" * 250  # Create a long problem

        problem = await framework.analyze_problem(description)
        subproblems = await framework.decompose_problem(problem)

        if len(subproblems) > 1:
            # Later subproblems should have dependencies on earlier ones
            last_subproblem = subproblems[-1]
            assert len(last_subproblem.dependencies) > 0

    @pytest.mark.asyncio
    async def test_select_strategy_analytical(self, framework):
        """Test strategy selection for analytical problems"""
        problem = Problem(
            problem_id="test_1",
            description="Analyze data patterns",
            problem_type=ProblemType.ANALYTICAL,
            constraints=[],
            success_criteria=[]
        )

        strategy = await framework.select_strategy(problem)

        assert strategy in [StrategyType.SYSTEMATIC, StrategyType.DECOMPOSITION]

    @pytest.mark.asyncio
    async def test_select_strategy_creative(self, framework):
        """Test strategy selection for creative problems"""
        problem = Problem(
            problem_id="test_2",
            description="Create innovative design",
            problem_type=ProblemType.CREATIVE,
            constraints=[],
            success_criteria=[]
        )

        strategy = await framework.select_strategy(problem)

        assert strategy in [StrategyType.BRAINSTORMING, StrategyType.ANALOGY]

    @pytest.mark.asyncio
    async def test_select_strategy_optimization(self, framework):
        """Test strategy selection for optimization problems"""
        problem = Problem(
            problem_id="test_3",
            description="Optimize performance",
            problem_type=ProblemType.OPTIMIZATION,
            constraints=[],
            success_criteria=[]
        )

        strategy = await framework.select_strategy(problem)

        assert strategy in [StrategyType.OPTIMIZATION, StrategyType.HEURISTIC]

    @pytest.mark.asyncio
    async def test_generate_solution_decomposition(self, framework):
        """Test solution generation with decomposition strategy"""
        problem = Problem(
            problem_id="test_4",
            description="Complex problem",
            problem_type=ProblemType.ANALYTICAL,
            constraints=[],
            success_criteria=[]
        )

        solution = await framework.generate_solution(problem, StrategyType.DECOMPOSITION)

        assert isinstance(solution, Solution)
        assert solution.strategy_used == StrategyType.DECOMPOSITION
        assert len(solution.implementation_steps) > 0
        assert len(solution.pros) > 0
        assert len(solution.cons) > 0

    @pytest.mark.asyncio
    async def test_generate_solution_brainstorming(self, framework):
        """Test solution generation with brainstorming strategy"""
        problem = Problem(
            problem_id="test_5",
            description="Creative problem",
            problem_type=ProblemType.CREATIVE,
            constraints=[],
            success_criteria=[]
        )

        solution = await framework.generate_solution(problem, StrategyType.BRAINSTORMING)

        assert solution.strategy_used == StrategyType.BRAINSTORMING
        assert len(solution.implementation_steps) > 0

    @pytest.mark.asyncio
    async def test_evaluate_solution(self, framework):
        """Test solution evaluation"""
        problem = Problem(
            problem_id="test_6",
            description="Test problem",
            problem_type=ProblemType.ANALYTICAL,
            constraints=[],
            success_criteria=[]
        )

        solution = Solution(
            solution_id="sol_1",
            problem_id=problem.problem_id,
            description="Test solution",
            strategy_used=StrategyType.SYSTEMATIC,
            confidence=0.7,
            estimated_effort=0.5,
            pros=["Pro 1", "Pro 2"],
            cons=["Con 1"]
        )

        score = await framework.evaluate_solution(solution, problem)

        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_start_problem_solving_session(self, framework):
        """Test starting a problem-solving session"""
        problem = await framework.analyze_problem("Test problem")

        session = await framework.start_problem_solving_session(problem)

        assert isinstance(session, ProblemSolvingSession)
        assert session.problem == problem
        assert len(session.session_id) > 0
        assert session.session_id in framework.active_sessions

    @pytest.mark.asyncio
    async def test_solve_problem_basic(self, framework):
        """Test basic problem solving"""
        problem = await framework.analyze_problem(
            "How can we improve code quality?"
        )

        solution = await framework.solve_problem(problem, max_iterations=3)

        assert solution is not None
        assert isinstance(solution, Solution)
        assert solution.problem_id == problem.problem_id

    @pytest.mark.asyncio
    async def test_solve_problem_multiple_iterations(self, framework):
        """Test problem solving with multiple iterations"""
        problem = await framework.analyze_problem("Optimize database queries")

        solution = await framework.solve_problem(problem, max_iterations=5)

        # Should have tried multiple strategies
        assert solution is not None

    @pytest.mark.asyncio
    async def test_solve_problem_early_stop(self, framework):
        """Test that solving stops early with good solution"""
        problem = await framework.analyze_problem("Simple problem")

        # Manually add a high-performing strategy
        key = (problem.problem_type, StrategyType.SYSTEMATIC)
        framework.strategy_performance[key] = [0.9, 0.95, 0.92]

        solution = await framework.solve_problem(problem, max_iterations=10)

        # Should find good solution and stop early
        assert solution is not None

    @pytest.mark.asyncio
    async def test_record_outcome_updates_performance(self, framework):
        """Test that recording outcome updates strategy performance"""
        problem = await framework.analyze_problem("Test problem")
        solution = await framework.generate_solution(problem, StrategyType.SYSTEMATIC)

        key = (problem.problem_type, solution.strategy_used)
        initial_count = len(framework.strategy_performance[key])

        await framework.record_outcome(
            solution=solution,
            problem=problem,
            effectiveness=0.85,
            lessons_learned=["Lesson 1", "Lesson 2"]
        )

        # Should add to performance tracking
        assert len(framework.strategy_performance[key]) == initial_count + 1
        assert 0.85 in framework.strategy_performance[key]

    @pytest.mark.asyncio
    async def test_record_outcome_creates_success_pattern(self, framework):
        """Test that high effectiveness creates success pattern"""
        problem = await framework.analyze_problem("Test problem")
        solution = await framework.generate_solution(problem, StrategyType.ANALOGY)

        initial_patterns = len(framework.success_patterns)

        await framework.record_outcome(
            solution=solution,
            problem=problem,
            effectiveness=0.85  # High effectiveness
        )

        # Should create success pattern
        assert len(framework.success_patterns) > initial_patterns

    @pytest.mark.asyncio
    async def test_get_problem_solving_statistics(self, framework):
        """Test getting problem-solving statistics"""
        # Solve a problem to generate data
        problem = await framework.analyze_problem("Test problem")
        await framework.solve_problem(problem)

        stats = await framework.get_problem_solving_statistics()

        assert 'total_sessions' in stats
        assert 'active_sessions' in stats
        assert 'problem_types_solved' in stats

    @pytest.mark.asyncio
    async def test_statistics_with_multiple_sessions(self, framework):
        """Test statistics with multiple sessions"""
        # Solve multiple problems
        for i in range(3):
            problem = await framework.analyze_problem(f"Problem {i}")
            await framework.solve_problem(problem, max_iterations=2)

        stats = await framework.get_problem_solving_statistics()

        assert stats['total_sessions'] >= 3

    @pytest.mark.asyncio
    async def test_session_moves_to_completed(self, framework):
        """Test that session moves to completed after solving"""
        problem = await framework.analyze_problem("Test")

        session = await framework.start_problem_solving_session(problem)
        session_id = session.session_id

        # Manually end by solving
        await framework.solve_problem(problem)

        # Session should be in completed, not active
        assert session_id not in framework.active_sessions
        assert len(framework.completed_sessions) > 0

    def test_detect_problem_type_keywords(self, framework):
        """Test problem type detection with various keywords"""
        test_cases = [
            ("Analyze the system performance", ProblemType.ANALYTICAL),
            ("Create a novel design", ProblemType.CREATIVE),
            ("Find the best approach", ProblemType.OPTIMIZATION),
            ("Diagnose the bug", ProblemType.DIAGNOSIS),
            ("Plan the project timeline", ProblemType.PLANNING),
            ("Learn about machine learning", ProblemType.LEARNING),
        ]

        for description, expected_type in test_cases:
            detected_type = framework._detect_problem_type(description)
            assert detected_type == expected_type

    def test_extract_constraints_various_phrases(self, framework):
        """Test constraint extraction with various phrases"""
        descriptions = [
            "Must complete by Friday",
            "Cannot exceed 100 requests",
            "Limited to 5GB storage",
            "Required to use Python",
        ]

        for desc in descriptions:
            constraints = framework._extract_constraints(desc)
            assert len(constraints) > 0

    def test_extract_success_criteria_various_phrases(self, framework):
        """Test success criteria extraction"""
        descriptions = [
            "Goal is to improve speed",
            "Should achieve 99% accuracy",
            "Need to reduce costs",
            "Want to increase engagement",
        ]

        for desc in descriptions:
            criteria = framework._extract_success_criteria(desc)
            assert len(criteria) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
