"""
Performance Benchmarks for Refactored Architecture
==================================================

Compares performance of refactored components against requirements:
- Memory operations throughput
- Component initialization time
- Coordinator delegation overhead
- Resource usage
"""

import asyncio
import pytest
import time
import tracemalloc
from datetime import datetime
from typing import List

from src.memory.manager_refactored import MemoryManager
from src.interface.consciousness_coordinator import ConsciousnessCoordinator
from src.interface.conversation_coordinator import ConversationCoordinator
from src.interface.command_registry import CommandRegistry
from unittest.mock import AsyncMock


class TestMemoryPerformanceBenchmarks:
    """Performance benchmarks for refactored memory system"""

    @pytest.fixture
    async def memory_manager(self):
        """Create memory manager for benchmarking"""
        manager = MemoryManager()
        await manager.initialize(use_database=False)
        yield manager
        # Cleanup - manager_refactored doesn't need explicit close for in-memory mode
        try:
            if hasattr(manager, 'close'):
                await manager.close()
        except AttributeError:
            pass  # No cleanup needed for in-memory mode

    @pytest.mark.asyncio
    async def test_memory_store_throughput(self, memory_manager):
        """Benchmark: Memory storage throughput (operations per second)"""

        # Store 100 thoughts and measure time
        start_time = time.perf_counter()
        for i in range(100):
            await memory_manager.store_thought({
                'content': f'Benchmark thought {i}',
                'stream': 'primary',
                'timestamp': datetime.now().isoformat(),
                'importance': 5
            })
        end_time = time.perf_counter()

        duration = end_time - start_time
        throughput = 100 / duration

        # Requirement: >100 ops/sec for memory storage
        assert throughput > 100, f"Memory storage throughput {throughput:.2f} ops/s < 100 ops/s"

        print(f"\n✓ Memory Store Throughput: {throughput:.2f} ops/s (target: >100 ops/s)")
        print(f"  Time for 100 operations: {duration:.3f}s")

    @pytest.mark.asyncio
    async def test_memory_recall_performance(self, memory_manager):
        """Benchmark: Memory recall latency"""

        # Store 100 thoughts first
        thought_ids = []
        for i in range(100):
            thought_id = await memory_manager.store_thought({
                'content': f'Recall test {i}',
                'timestamp': datetime.now().isoformat()
            })
            thought_ids.append(thought_id)

        # Measure recall time
        start_time = time.perf_counter()
        for thought_id in thought_ids[:10]:  # Recall 10 thoughts
            await memory_manager.recall_by_id(thought_id)
        end_time = time.perf_counter()

        avg_recall_time = (end_time - start_time) / 10

        # Requirement: <10ms average recall time
        assert avg_recall_time < 0.01, f"Recall time {avg_recall_time*1000:.2f}ms > 10ms"

        print(f"\nAverage Recall Time: {avg_recall_time*1000:.2f}ms")

    @pytest.mark.asyncio
    async def test_memory_recall_recent_performance(self, memory_manager):
        """Benchmark: Recall recent thoughts performance"""

        # Store 1000 thoughts
        for i in range(1000):
            await memory_manager.store_thought({
                'content': f'Recent test {i}',
                'timestamp': datetime.now().isoformat()
            })

        # Measure recall recent time
        start_time = time.perf_counter()
        recent = await memory_manager.recall_recent(n=50)
        end_time = time.perf_counter()

        recall_time = end_time - start_time

        # Requirement: <50ms for recalling 50 recent thoughts
        assert recall_time < 0.05, f"Recall recent time {recall_time*1000:.2f}ms > 50ms"
        assert len(recent) == 50

        print(f"\nRecall Recent Time (50 thoughts): {recall_time*1000:.2f}ms")

    @pytest.mark.asyncio
    async def test_memory_consolidation_performance(self, memory_manager):
        """Benchmark: Memory consolidation performance"""

        # Store 100 thoughts with varying importance
        for i in range(100):
            await memory_manager.store_thought({
                'content': f'Consolidation test {i}',
                'timestamp': datetime.now().isoformat(),
                'importance': 3 + (i % 7)  # Varying importance
            })

        # Measure consolidation time
        start_time = time.perf_counter()
        await memory_manager.consolidate_memories()
        end_time = time.perf_counter()

        consolidation_time = end_time - start_time

        # Requirement: <500ms for consolidating 100 thoughts
        assert consolidation_time < 0.5, f"Consolidation time {consolidation_time*1000:.2f}ms > 500ms"

        print(f"\nConsolidation Time (100 thoughts): {consolidation_time*1000:.2f}ms")

    @pytest.mark.asyncio
    async def test_memory_concurrent_operations(self, memory_manager):
        """Benchmark: Concurrent memory operations"""

        async def concurrent_stores():
            """Store thoughts concurrently"""
            tasks = []
            for i in range(50):
                task = memory_manager.store_thought({
                    'content': f'Concurrent {i}',
                    'timestamp': datetime.now().isoformat()
                })
                tasks.append(task)
            await asyncio.gather(*tasks)

        # Measure concurrent operation time
        start_time = time.perf_counter()
        await concurrent_stores()
        end_time = time.perf_counter()

        concurrent_time = end_time - start_time
        throughput = 50 / concurrent_time

        # Requirement: >100 ops/s even with concurrency
        assert throughput > 100, f"Concurrent throughput {throughput:.2f} ops/s < 100 ops/s"

        print(f"\nConcurrent Store Throughput: {throughput:.2f} ops/s")


class TestMemoryMemoryUsageBenchmarks:
    """Memory usage benchmarks for refactored components"""

    @pytest.mark.asyncio
    async def test_memory_manager_memory_usage(self):
        """Benchmark: Memory manager memory footprint"""

        # Start memory tracking
        tracemalloc.start()
        baseline = tracemalloc.get_traced_memory()[0]

        # Create and initialize memory manager
        manager = MemoryManager()
        await manager.initialize(use_database=False)

        # Store 1000 thoughts
        for i in range(1000):
            await manager.store_thought({
                'content': f'Memory test {i}' * 10,  # Larger content
                'timestamp': datetime.now().isoformat()
            })

        current, peak = tracemalloc.get_traced_memory()
        memory_used = (current - baseline) / 1024 / 1024  # MB

        tracemalloc.stop()

        # Requirement: <50MB for 1000 thoughts
        assert memory_used < 50, f"Memory usage {memory_used:.2f}MB > 50MB"

        print(f"\nMemory Usage (1000 thoughts): {memory_used:.2f}MB")

        await manager.close()


class TestTUIPerformanceBenchmarks:
    """Performance benchmarks for refactored TUI components"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator"""
        orchestrator = AsyncMock()
        orchestrator.get_service = AsyncMock(return_value=None)
        orchestrator.publish = AsyncMock()
        return orchestrator

    @pytest.fixture
    def mock_thought_generator(self):
        """Create mock thought generator"""
        generator = AsyncMock()
        generator.generate_response = AsyncMock(return_value="Response")
        return generator

    @pytest.mark.asyncio
    async def test_consciousness_coordinator_initialization_time(self, mock_orchestrator):
        """Benchmark: ConsciousnessCoordinator initialization time"""

        lines = []

        start_time = time.perf_counter()
        coordinator = ConsciousnessCoordinator(
            orchestrator=mock_orchestrator,
            add_consciousness_line_callback=lambda line: lines.append(line)
        )
        end_time = time.perf_counter()

        init_time = end_time - start_time

        # Requirement: <10ms initialization
        assert init_time < 0.01, f"Initialization time {init_time*1000:.2f}ms > 10ms"

        print(f"\nConsciousnessCoordinator Init Time: {init_time*1000:.2f}ms")

    @pytest.mark.asyncio
    async def test_conversation_coordinator_response_time(
        self, mock_thought_generator, mock_orchestrator
    ):
        """Benchmark: ConversationCoordinator message handling time"""

        lines = []
        coordinator = ConversationCoordinator(
            thought_generator=mock_thought_generator,
            orchestrator=mock_orchestrator,
            add_chat_line_callback=lambda line: lines.append(line)
        )

        # Measure message handling time
        start_time = time.perf_counter()
        await coordinator.handle_user_message("Hello, Claude!")
        end_time = time.perf_counter()

        handling_time = end_time - start_time

        # Requirement: <100ms for message handling (excluding AI response generation)
        # Since we mock the AI response, this tests coordinator overhead only
        assert handling_time < 0.1, f"Message handling time {handling_time*1000:.2f}ms > 100ms"

        print(f"\nConversation Message Handling Time: {handling_time*1000:.2f}ms")

    @pytest.mark.asyncio
    async def test_command_registry_routing_performance(self):
        """Benchmark: CommandRegistry command routing performance"""

        chat_lines = []
        system_lines = []

        registry = CommandRegistry(
            add_chat_line_callback=lambda line: chat_lines.append(line),
            add_system_line_callback=lambda line: system_lines.append(line)
        )

        # Measure command routing time
        start_time = time.perf_counter()
        for _ in range(100):
            await registry.route_command('help', [])
        end_time = time.perf_counter()

        avg_routing_time = (end_time - start_time) / 100

        # Requirement: <1ms average routing time
        assert avg_routing_time < 0.001, f"Command routing time {avg_routing_time*1000:.2f}ms > 1ms"

        print(f"\nAverage Command Routing Time: {avg_routing_time*1000:.2f}ms")

    @pytest.mark.asyncio
    async def test_consciousness_loop_performance(self, mock_orchestrator):
        """Benchmark: Consciousness loop iteration time"""

        lines = []
        coordinator = ConsciousnessCoordinator(
            orchestrator=mock_orchestrator,
            add_consciousness_line_callback=lambda line: lines.append(line)
        )

        # Run consciousness loop for 5 iterations
        coordinator.running = True
        start_time = time.perf_counter()

        task = asyncio.create_task(coordinator.run_consciousness_loop())
        await asyncio.sleep(1.0)  # Let it run for 1 second

        coordinator.running = False
        try:
            await asyncio.wait_for(task, timeout=2.0)
        except asyncio.TimeoutError:
            task.cancel()

        end_time = time.perf_counter()

        # Should have some output within 1 second
        assert len(lines) > 0, "Consciousness loop produced no output"

        print(f"\nConsciousness loop ran for {end_time - start_time:.2f}s, produced {len(lines)} lines")


class TestCoordinatorOverheadBenchmarks:
    """Benchmark delegation overhead of refactored coordinators"""

    @pytest.mark.asyncio
    async def test_memory_coordinator_delegation_overhead(self):
        """Benchmark: Delegation overhead in MemoryCoordinator"""

        # Create manager with all components
        manager = MemoryManager()
        await manager.initialize(use_database=False)

        # Measure direct store vs coordinated store
        thought = {
            'content': 'Overhead test',
            'timestamp': datetime.now().isoformat()
        }

        # Coordinated store (through manager)
        start_time = time.perf_counter()
        for _ in range(100):
            await manager.store_thought(thought)
        end_time = time.perf_counter()

        coordinated_time = (end_time - start_time) / 100

        # Direct store (through working memory)
        start_time = time.perf_counter()
        for _ in range(100):
            await manager.working_memory.store_thought(thought)
        end_time = time.perf_counter()

        direct_time = (end_time - start_time) / 100

        overhead = coordinated_time - direct_time
        overhead_percent = (overhead / direct_time) * 100

        # Requirement: <20% overhead from coordination
        assert overhead_percent < 20, f"Coordination overhead {overhead_percent:.1f}% > 20%"

        print(f"\nDelegation Overhead:")
        print(f"  Direct: {direct_time*1000:.2f}ms")
        print(f"  Coordinated: {coordinated_time*1000:.2f}ms")
        print(f"  Overhead: {overhead_percent:.1f}%")

        await manager.close()

    @pytest.mark.asyncio
    async def test_conversation_coordinator_delegation_overhead(self):
        """Benchmark: Delegation overhead in ConversationCoordinator"""

        mock_thought_generator = AsyncMock()
        mock_thought_generator.generate_response = AsyncMock(return_value="Response")
        mock_orchestrator = AsyncMock()
        lines = []

        coordinator = ConversationCoordinator(
            thought_generator=mock_thought_generator,
            orchestrator=mock_orchestrator,
            add_chat_line_callback=lambda line: lines.append(line)
        )

        # Measure coordinator overhead
        start_time = time.perf_counter()
        await coordinator.handle_user_message("Test message")
        end_time = time.perf_counter()

        total_time = end_time - start_time

        # Direct AI call time
        start_time = time.perf_counter()
        await mock_thought_generator.generate_response("Test message")
        end_time = time.perf_counter()

        ai_call_time = end_time - start_time
        overhead = total_time - ai_call_time

        # Requirement: <10ms overhead for message processing
        assert overhead < 0.01, f"Message processing overhead {overhead*1000:.2f}ms > 10ms"

        print(f"\nConversation Coordinator Overhead: {overhead*1000:.2f}ms")


class TestScalabilityBenchmarks:
    """Scalability benchmarks for refactored architecture"""

    @pytest.mark.asyncio
    async def test_memory_scalability_with_thought_count(self):
        """Benchmark: Performance scaling with number of stored thoughts"""

        manager = MemoryManager()
        await manager.initialize(use_database=False)

        results = []

        for count in [100, 500, 1000, 5000]:
            # Store thoughts
            start_time = time.perf_counter()
            for i in range(count):
                await manager.store_thought({
                    'content': f'Scalability test {i}',
                    'timestamp': datetime.now().isoformat()
                })
            store_time = time.perf_counter() - start_time

            # Recall recent
            start_time = time.perf_counter()
            await manager.recall_recent(n=10)
            recall_time = time.perf_counter() - start_time

            results.append({
                'count': count,
                'store_time': store_time,
                'recall_time': recall_time,
                'store_throughput': count / store_time
            })

            # Clear for next iteration
            await manager.clear_working_memory()

        # Verify scalability
        for i in range(len(results) - 1):
            current = results[i]
            next_result = results[i + 1]

            # Recall time should remain relatively constant (not grow linearly)
            # Allow 2x increase for 5x data increase
            assert next_result['recall_time'] < current['recall_time'] * 2, \
                f"Recall time scaled poorly: {current['count']} thoughts: {current['recall_time']:.3f}s, " \
                f"{next_result['count']} thoughts: {next_result['recall_time']:.3f}s"

        print("\nScalability Results:")
        for result in results:
            print(f"  {result['count']} thoughts: "
                  f"Store {result['store_time']:.3f}s ({result['store_throughput']:.1f} ops/s), "
                  f"Recall {result['recall_time']*1000:.2f}ms")

        await manager.close()

    @pytest.mark.asyncio
    async def test_concurrent_coordinator_scalability(self):
        """Benchmark: Multiple coordinators operating concurrently"""

        # Create multiple memory managers simulating multiple users
        managers = []
        for _ in range(5):
            manager = MemoryManager()
            await manager.initialize(use_database=False)
            managers.append(manager)

        # Concurrent operations across all managers
        start_time = time.perf_counter()

        tasks = []
        for manager in managers:
            for i in range(20):
                task = manager.store_thought({
                    'content': f'Concurrent test {i}',
                    'timestamp': datetime.now().isoformat()
                })
                tasks.append(task)

        await asyncio.gather(*tasks)

        end_time = time.perf_counter()

        concurrent_time = end_time - start_time
        throughput = (5 * 20) / concurrent_time

        # Requirement: >100 ops/s even with multiple concurrent coordinators
        assert throughput > 100, f"Concurrent coordinator throughput {throughput:.2f} ops/s < 100 ops/s"

        print(f"\nConcurrent Coordinators Throughput (5 managers): {throughput:.2f} ops/s")

        # Cleanup
        for manager in managers:
            await manager.close()


class TestRefactoredVsOriginalComparison:
    """Compare refactored components against baseline requirements"""

    @pytest.mark.asyncio
    async def test_refactored_meets_performance_requirements(self):
        """Verify refactored architecture meets all performance requirements"""

        manager = MemoryManager()
        await manager.initialize(use_database=False)

        # Test 1: Storage throughput
        start = time.perf_counter()
        for i in range(100):
            await manager.store_thought({
                'content': f'Test {i}',
                'timestamp': datetime.now().isoformat()
            })
        store_throughput = 100 / (time.perf_counter() - start)

        # Test 2: Recall latency
        thought_id = await manager.store_thought({'content': 'Test', 'timestamp': datetime.now().isoformat()})
        start = time.perf_counter()
        await manager.recall_by_id(thought_id)
        recall_latency = time.perf_counter() - start

        # Test 3: Recent recall performance
        start = time.perf_counter()
        await manager.recall_recent(n=10)
        recent_recall_time = time.perf_counter() - start

        # Requirements
        assert store_throughput > 100, f"Storage throughput {store_throughput:.2f} ops/s < 100 ops/s"
        assert recall_latency < 0.01, f"Recall latency {recall_latency*1000:.2f}ms > 10ms"
        assert recent_recall_time < 0.05, f"Recent recall time {recent_recall_time*1000:.2f}ms > 50ms"

        print("\n=== Performance Summary ===")
        print(f"✓ Storage Throughput: {store_throughput:.2f} ops/s (req: >100 ops/s)")
        print(f"✓ Recall Latency: {recall_latency*1000:.2f}ms (req: <10ms)")
        print(f"✓ Recent Recall Time: {recent_recall_time*1000:.2f}ms (req: <50ms)")
        print("=== All Requirements Met ===")

        await manager.close()
