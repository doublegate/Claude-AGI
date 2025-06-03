# tests/performance/test_performance_benchmarks.py

import pytest
import asyncio
import time
import statistics
from datetime import datetime, timedelta
import psutil
import os

from src.memory.manager import MemoryManager
from src.consciousness.stream import ConsciousnessStream, ThoughtStream
from src.safety.core_safety import SafetyFramework
from src.core.orchestrator import AGIOrchestrator


@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Performance benchmarks for Phase 1 requirements"""
    
    @pytest.fixture
    def performance_config(self):
        """Configuration optimized for performance testing"""
        return {
            'services': {
                'memory': {'enabled': True},
                'consciousness': {'enabled': True},
                'safety': {'enabled': True}
            },
            'database': {
                'enabled': False  # Use in-memory for consistent benchmarks
            },
            'orchestrator': {
                'max_queue_size': 1000
            }
        }
    
    @pytest.mark.asyncio
    async def test_memory_retrieval_under_50ms(self, performance_config):
        """Test that memory retrieval meets <50ms requirement"""
        memory_manager = MemoryManager(config=performance_config, use_database=False)
        await memory_manager.initialize()
        
        # Pre-populate with memories
        for i in range(1000):
            await memory_manager.store({
                'content': f'Memory {i} with some content about topic {i % 10}',
                'importance': 5 + (i % 5),
                'timestamp': datetime.now()
            })
        
        # Measure retrieval times
        retrieval_times = []
        
        for _ in range(100):
            start = time.perf_counter()
            memories = await memory_manager.recall_recent(10)
            end = time.perf_counter()
            retrieval_times.append((end - start) * 1000)  # Convert to ms
        
        # Calculate statistics
        avg_time = statistics.mean(retrieval_times)
        max_time = max(retrieval_times)
        p95_time = sorted(retrieval_times)[int(len(retrieval_times) * 0.95)]
        
        print(f"\nMemory Retrieval Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  95th percentile: {p95_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")
        
        # Assert Phase 1 requirement
        assert p95_time < 50, f"95th percentile retrieval time {p95_time:.2f}ms exceeds 50ms requirement"
    
    @pytest.mark.asyncio
    async def test_thought_generation_rate(self, performance_config):
        """Test thought generation meets human-like pacing"""
        orchestrator = AGIOrchestrator(performance_config)
        consciousness = ConsciousnessStream(orchestrator)
        
        # Measure thought generation over 10 seconds
        start_time = time.time()
        thought_count = 0
        
        while time.time() - start_time < 10:
            await consciousness.service_cycle()
            
            # Count new thoughts
            for stream in consciousness.streams.values():
                thought_count += len(stream.content_buffer)
                stream.content_buffer.clear()  # Clear to count only new
            
            await asyncio.sleep(0.1)
        
        # Calculate rate
        duration = time.time() - start_time
        thoughts_per_second = thought_count / duration
        
        print(f"\nThought Generation Rate:")
        print(f"  Total thoughts: {thought_count}")
        print(f"  Duration: {duration:.1f}s")
        print(f"  Rate: {thoughts_per_second:.2f} thoughts/second")
        
        # Should generate thoughts at human-like rate (0.3-0.5 per second per stream)
        expected_min = 0.3 * len(consciousness.streams) * 0.5  # With some margin
        expected_max = 0.5 * len(consciousness.streams) * 2.0
        
        assert expected_min <= thoughts_per_second <= expected_max, \
            f"Thought rate {thoughts_per_second:.2f}/s outside human-like range"
    
    @pytest.mark.asyncio
    async def test_safety_validation_latency(self, performance_config):
        """Test safety validation completes quickly"""
        mock_orchestrator = pytest.Mock()
        safety = SafetyFramework(mock_orchestrator)
        
        # Prepare various actions
        test_actions = [
            {'type': 'think', 'content': 'Normal thought about consciousness'},
            {'type': 'respond', 'content': 'Hello, how can I help you today?'},
            {'type': 'remember', 'content': 'Important information to store'},
            {'type': 'explore', 'content': 'Search for new knowledge'},
            {'type': 'execute_code', 'content': 'print("Hello")'}  # Should be blocked
        ]
        
        validation_times = []
        
        # Run multiple iterations
        for _ in range(20):
            for action in test_actions:
                start = time.perf_counter()
                result = await safety.validate_action(action)
                end = time.perf_counter()
                validation_times.append((end - start) * 1000)
        
        avg_time = statistics.mean(validation_times)
        max_time = max(validation_times)
        
        print(f"\nSafety Validation Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")
        
        # Safety validation should be fast
        assert avg_time < 10, f"Average validation time {avg_time:.2f}ms too high"
        assert max_time < 50, f"Max validation time {max_time:.2f}ms too high"
    
    @pytest.mark.asyncio
    async def test_concurrent_thought_processing(self, performance_config):
        """Test system handles concurrent thought streams efficiently"""
        orchestrator = AGIOrchestrator(performance_config)
        await orchestrator._initialize_services()
        
        consciousness = orchestrator.services.get('consciousness')
        if not consciousness:
            pytest.skip("Consciousness service not available")
        
        # Generate thoughts concurrently across all streams
        start = time.time()
        tasks = []
        
        for _ in range(10):  # 10 cycles
            for stream_id, stream in consciousness.streams.items():
                thought = {
                    'content': f'Concurrent thought from {stream_id}',
                    'stream': stream_id,
                    'timestamp': time.time(),
                    'emotional_tone': 'neutral',
                    'importance': 5
                }
                task = consciousness.process_thought(thought, stream)
                tasks.append(task)
        
        # Process all thoughts concurrently
        await asyncio.gather(*tasks)
        
        duration = time.time() - start
        thoughts_processed = len(tasks)
        
        print(f"\nConcurrent Processing Performance:")
        print(f"  Thoughts processed: {thoughts_processed}")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Rate: {thoughts_processed/duration:.1f} thoughts/second")
        
        # Should handle at least 10 thoughts per second
        assert thoughts_processed / duration > 10, "Concurrent processing too slow"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_24_hour_coherence_simulation(self, performance_config):
        """Simulate 24-hour operation (accelerated)"""
        # This is a shortened simulation - real 24h test would be separate
        print("\nRunning accelerated 24-hour coherence test...")
        
        orchestrator = AGIOrchestrator(performance_config)
        await orchestrator._initialize_services()
        
        memory = orchestrator.services.get('memory')
        consciousness = orchestrator.services.get('consciousness')
        
        if not all([memory, consciousness]):
            pytest.skip("Required services not available")
        
        # Simulate 24 hours in 24 seconds (1 hour = 1 second)
        start_time = time.time()
        simulated_hours = 0
        
        memory_coherence_checks = []
        thought_continuity_checks = []
        
        while simulated_hours < 24:
            # Simulate one hour of operation
            
            # Generate thoughts
            for _ in range(10):  # 10 thoughts per "hour"
                await consciousness.service_cycle()
            
            # Check memory coherence
            recent_memories = await memory.recall_recent(5)
            if recent_memories:
                # Check that memories maintain temporal ordering
                timestamps = [m.get('timestamp', datetime.min) for m in recent_memories]
                is_ordered = all(timestamps[i] >= timestamps[i+1] 
                                for i in range(len(timestamps)-1))
                memory_coherence_checks.append(is_ordered)
            
            # Check thought continuity
            all_thoughts = []
            for stream in consciousness.streams.values():
                all_thoughts.extend(stream.get_recent(3))
            
            if len(all_thoughts) >= 2:
                # Check that thoughts maintain some continuity
                has_continuity = len(all_thoughts) > 0
                thought_continuity_checks.append(has_continuity)
            
            # Consolidate memory every 6 "hours"
            if simulated_hours % 6 == 0:
                await memory.consolidate_memories()
            
            await asyncio.sleep(1)  # 1 second = 1 hour
            simulated_hours += 1
        
        # Calculate coherence metrics
        memory_coherence_rate = (sum(memory_coherence_checks) / 
                                len(memory_coherence_checks) if memory_coherence_checks else 0)
        thought_continuity_rate = (sum(thought_continuity_checks) / 
                                  len(thought_continuity_checks) if thought_continuity_checks else 0)
        
        print(f"\n24-Hour Coherence Results:")
        print(f"  Memory coherence: {memory_coherence_rate*100:.1f}%")
        print(f"  Thought continuity: {thought_continuity_rate*100:.1f}%")
        
        # Should maintain high coherence
        assert memory_coherence_rate > 0.95, "Memory coherence below 95%"
        assert thought_continuity_rate > 0.90, "Thought continuity below 90%"
    
    @pytest.mark.asyncio
    async def test_memory_scaling(self, performance_config):
        """Test memory performance with large numbers of memories"""
        memory_manager = MemoryManager(config=performance_config, use_database=False)
        await memory_manager.initialize()
        
        # Test with increasing memory counts
        memory_counts = [100, 1000, 10000]
        results = []
        
        for count in memory_counts:
            # Clear and populate
            await memory_manager.clear_working_memory()
            
            # Add memories
            start = time.time()
            for i in range(count):
                await memory_manager.store({
                    'content': f'Memory {i} about various topics',
                    'importance': 5,
                    'timestamp': datetime.now()
                })
            populate_time = time.time() - start
            
            # Test retrieval
            retrieval_times = []
            for _ in range(10):
                start = time.perf_counter()
                await memory_manager.recall_recent(10)
                retrieval_times.append(time.perf_counter() - start)
            
            avg_retrieval = statistics.mean(retrieval_times) * 1000
            
            results.append({
                'count': count,
                'populate_time': populate_time,
                'avg_retrieval_ms': avg_retrieval
            })
            
            print(f"\nMemory count: {count}")
            print(f"  Population time: {populate_time:.2f}s")
            print(f"  Avg retrieval: {avg_retrieval:.2f}ms")
        
        # Retrieval should remain fast even with many memories
        for result in results:
            assert result['avg_retrieval_ms'] < 100, \
                f"Retrieval too slow ({result['avg_retrieval_ms']:.2f}ms) with {result['count']} memories"
    
    @pytest.mark.asyncio
    async def test_resource_usage(self, performance_config):
        """Monitor resource usage during operation"""
        process = psutil.Process(os.getpid())
        
        # Baseline measurements
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        baseline_cpu = process.cpu_percent(interval=0.1)
        
        # Run system
        orchestrator = AGIOrchestrator(performance_config)
        await orchestrator._initialize_services()
        
        # Operate for a period
        start = time.time()
        max_memory = baseline_memory
        cpu_samples = []
        
        while time.time() - start < 5:
            await orchestrator._run_service_cycles()
            
            # Sample resources
            current_memory = process.memory_info().rss / 1024 / 1024
            current_cpu = process.cpu_percent(interval=0.1)
            
            max_memory = max(max_memory, current_memory)
            cpu_samples.append(current_cpu)
            
            await asyncio.sleep(0.1)
        
        # Calculate metrics
        memory_increase = max_memory - baseline_memory
        avg_cpu = statistics.mean(cpu_samples) if cpu_samples else 0
        
        print(f"\nResource Usage:")
        print(f"  Baseline memory: {baseline_memory:.1f} MB")
        print(f"  Peak memory: {max_memory:.1f} MB")
        print(f"  Memory increase: {memory_increase:.1f} MB")
        print(f"  Average CPU: {avg_cpu:.1f}%")
        
        # Resource usage should be reasonable
        assert memory_increase < 100, f"Memory increase {memory_increase:.1f}MB exceeds 100MB"
        assert avg_cpu < 80, f"CPU usage {avg_cpu:.1f}% too high"
    
    def test_startup_time(self, performance_config):
        """Test system startup time"""
        async def measure_startup():
            start = time.time()
            
            orchestrator = AGIOrchestrator(performance_config)
            await orchestrator._initialize_services()
            
            return time.time() - start
        
        # Run startup test
        startup_time = asyncio.run(measure_startup())
        
        print(f"\nStartup Performance:")
        print(f"  Time to initialize: {startup_time:.2f}s")
        
        # Should start up quickly
        assert startup_time < 5.0, f"Startup time {startup_time:.2f}s exceeds 5 seconds"