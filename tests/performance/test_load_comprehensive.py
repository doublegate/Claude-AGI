"""
Comprehensive Load Testing Suite for Claude-AGI
================================================

Validates performance under load for all major subsystems:
- Knowledge graph operations
- Problem solving throughput
- Memory system performance
- Emotional processing speed
- Theory of mind inference rate
- Multi-user concurrency
- Dream simulation throughput
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any

import pytest

from src.learning.knowledge_graph import KnowledgeGraph
from src.reasoning.problem_solving import ProblemSolvingFramework, Problem, ProblemType
from src.memory.working_memory import WorkingMemory
from src.emotional.emotional_model import AdvancedEmotionalModel
from src.social.theory_of_mind import TheoryOfMind
from src.social.multi_user_manager import MultiUserManager
from src.creative.dream_simulation import DreamSimulator


class LoadTester:
    """Comprehensive load testing framework"""

    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}

    async def test_knowledge_graph_load(self, operations: int = 10000) -> Dict[str, Any]:
        """Test knowledge graph performance under load"""
        kg = KnowledgeGraph()

        start = time.time()

        # Warm-up
        for i in range(100):
            await kg.add_concept(f"warmup_{i}", "test", "warmup concept")

        # Actual test
        start = time.time()
        for i in range(operations):
            await kg.add_concept(f"concept_{i}", "technology", f"Test concept {i}")

        duration = time.time() - start
        ops_per_sec = operations / duration

        result = {
            'operations': operations,
            'duration_seconds': round(duration, 2),
            'ops_per_second': round(ops_per_sec, 2),
            'target': 16403,
            'meets_target': ops_per_sec >= 16403 * 0.8  # Allow 20% variance
        }

        self.results['knowledge_graph'] = result
        return result

    async def test_problem_solving_load(self, problems: int = 1000) -> Dict[str, Any]:
        """Test problem solving throughput"""
        framework = ProblemSolvingFramework()

        start = time.time()

        # Create and solve problems concurrently
        tasks = []
        for i in range(problems):
            problem = await framework.analyze_problem(f"Solve problem {i}")
            tasks.append(framework.solve_problem(problem, max_iterations=1))

        # Execute in batches to avoid overwhelming system
        batch_size = 100
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            await asyncio.gather(*batch)

        duration = time.time() - start
        problems_per_sec = problems / duration

        result = {
            'problems': problems,
            'duration_seconds': round(duration, 2),
            'problems_per_second': round(problems_per_sec, 2),
            'target': 2500,
            'meets_target': problems_per_sec >= 2500 * 0.8
        }

        self.results['problem_solving'] = result
        return result

    async def test_emotional_processing_load(self, stimuli: int = 10000) -> Dict[str, Any]:
        """Test emotional processing speed"""
        model = AdvancedEmotionalModel()

        stimulus_types = ['discovery', 'achievement', 'learning', 'success', 'excitement']

        start = time.time()

        for i in range(stimuli):
            stimulus = stimulus_types[i % len(stimulus_types)]
            await model.process_emotional_stimulus(stimulus, intensity=0.5)

        duration = time.time() - start
        stimuli_per_sec = stimuli / duration

        result = {
            'stimuli': stimuli,
            'duration_seconds': round(duration, 2),
            'stimuli_per_second': round(stimuli_per_sec, 2),
            'target': 34765,
            'meets_target': stimuli_per_sec >= 34765 * 0.8
        }

        self.results['emotional_processing'] = result
        return result

    async def test_theory_of_mind_load(self, inferences: int = 10000) -> Dict[str, Any]:
        """Test theory of mind inference rate"""
        tom = TheoryOfMind()

        statements = [
            "I believe this is interesting",
            "I think this might work",
            "I feel excited about this",
            "I want to learn more",
            "This seems important"
        ]

        start = time.time()

        for i in range(inferences):
            statement = statements[i % len(statements)]
            await tom.infer_belief(f"user_{i % 10}", statement)

        duration = time.time() - start
        inferences_per_sec = inferences / duration

        result = {
            'inferences': inferences,
            'duration_seconds': round(duration, 2),
            'inferences_per_second': round(inferences_per_sec, 2),
            'target': 29926,
            'meets_target': inferences_per_sec >= 29926 * 0.8
        }

        self.results['theory_of_mind'] = result
        return result

    async def test_multi_user_concurrency(self, users: int = 100, ops_per_user: int = 50) -> Dict[str, Any]:
        """Test multi-user system under concurrent load"""
        manager = MultiUserManager()

        start = time.time()

        # Create users and sessions concurrently
        user_tasks = []
        for i in range(users):
            user_id = f"load_test_user_{i}"
            user_tasks.append(manager.create_user(user_id))

        await asyncio.gather(*user_tasks)

        # Perform operations concurrently
        operation_tasks = []
        for i in range(users):
            user_id = f"load_test_user_{i}"
            for j in range(ops_per_user):
                operation_tasks.append(
                    manager.store_user_data(f"key_{j}", f"value_{j}", user_id=user_id)
                )

        await asyncio.gather(*operation_tasks)

        duration = time.time() - start
        total_ops = users * ops_per_user
        ops_per_sec = total_ops / duration

        result = {
            'users': users,
            'ops_per_user': ops_per_user,
            'total_operations': total_ops,
            'duration_seconds': round(duration, 2),
            'ops_per_second': round(ops_per_sec, 2),
            'concurrent_users_supported': users
        }

        self.results['multi_user_concurrency'] = result
        return result

    async def test_dream_simulation_throughput(self, sessions: int = 50) -> Dict[str, Any]:
        """Test dream simulation throughput"""
        simulator = DreamSimulator()

        # Add memories
        for i in range(100):
            await simulator.add_memory_to_pool(f"memory_{i}", is_recent=True)

        start = time.time()

        # Run dream sessions concurrently
        tasks = []
        for i in range(sessions):
            tasks.append(
                simulator.start_dream_session(duration_minutes=1)
            )

        results = await asyncio.gather(*tasks)

        duration = time.time() - start
        sessions_per_sec = sessions / duration
        total_elements = sum(len(r.elements) for r in results)
        elements_per_sec = total_elements / duration

        result = {
            'sessions': sessions,
            'total_elements_generated': total_elements,
            'duration_seconds': round(duration, 2),
            'sessions_per_second': round(sessions_per_sec, 2),
            'elements_per_second': round(elements_per_sec, 2)
        }

        self.results['dream_simulation'] = result
        return result

    async def test_memory_stress(self, operations: int = 5000) -> Dict[str, Any]:
        """Stress test memory system"""
        memory = WorkingMemory()

        start = time.time()

        # Mixed operations
        for i in range(operations):
            if i % 3 == 0:
                await memory.add_item(f"key_{i}", f"value_{i}")
            elif i % 3 == 1:
                await memory.get_item(f"key_{i - 1}")
            else:
                await memory.get_recent_items(limit=10)

        duration = time.time() - start
        ops_per_sec = operations / duration

        result = {
            'operations': operations,
            'duration_seconds': round(duration, 2),
            'ops_per_second': round(ops_per_sec, 2)
        }

        self.results['memory_stress'] = result
        return result

    def generate_report(self) -> str:
        """Generate comprehensive load test report"""
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE LOAD TEST REPORT")
        report.append("=" * 80)
        report.append("")

        all_passed = True

        for test_name, result in self.results.items():
            report.append(f"\n{test_name.replace('_', ' ').upper()}")
            report.append("-" * 80)

            for key, value in result.items():
                if key == 'meets_target':
                    status = "✅ PASS" if value else "❌ FAIL"
                    report.append(f"  Status: {status}")
                    if not value:
                        all_passed = False
                else:
                    report.append(f"  {key}: {value}")

        report.append("\n" + "=" * 80)
        report.append(f"OVERALL RESULT: {'✅ ALL TESTS PASSED' if all_passed else '⚠️  SOME TESTS FAILED'}")
        report.append("=" * 80)

        return "\n".join(report)


@pytest.mark.asyncio
@pytest.mark.performance
async def test_comprehensive_load():
    """Run comprehensive load test suite"""
    tester = LoadTester()

    print("\n🚀 Starting Comprehensive Load Testing...")
    print("=" * 80)

    # Run all load tests
    tests = [
        ("Knowledge Graph Operations", tester.test_knowledge_graph_load(1000)),
        ("Problem Solving Throughput", tester.test_problem_solving_load(100)),
        ("Emotional Processing Speed", tester.test_emotional_processing_load(5000)),
        ("Theory of Mind Inference", tester.test_theory_of_mind_load(5000)),
        ("Multi-User Concurrency", tester.test_multi_user_concurrency(50, 20)),
        ("Dream Simulation Throughput", tester.test_dream_simulation_throughput(20)),
        ("Memory System Stress", tester.test_memory_stress(2000))
    ]

    for test_name, test_coro in tests:
        print(f"\n⚡ Running: {test_name}...")
        result = await test_coro
        print(f"  ✓ Completed in {result.get('duration_seconds', 'N/A')}s")

    # Generate and print report
    report = tester.generate_report()
    print("\n" + report)

    # All targets should be met
    all_passed = all(
        r.get('meets_target', True)
        for r in tester.results.values()
    )

    assert all_passed, "Some load tests did not meet performance targets"


if __name__ == "__main__":
    asyncio.run(test_comprehensive_load())
