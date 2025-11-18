"""
Performance Profiling for Phase 2-6 AGI Modules
================================================

Profiles CPU, memory, and execution time for critical AGI operations.
"""

import asyncio
import cProfile
import pstats
import time
import tracemalloc
from typing import Dict, Any, List
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.learning.knowledge_extraction import KnowledgeExtractor, LearningPathGenerator
from src.learning.curiosity_engine import CuriosityEngine
from src.learning.knowledge_graph import KnowledgeGraph, RelationType
from src.web.content_processor import WebContentProcessor, InformationSynthesizer
from src.emotional.emotional_model import AdvancedEmotionalModel
from src.social.theory_of_mind import TheoryOfMind
from src.metacognitive.enhanced_self_model import EnhancedSelfModel
from src.reasoning.problem_solving import ProblemSolvingFramework


class PerformanceProfiler:
    """Profile performance of AGI modules"""

    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}

    async def profile_knowledge_extraction(self):
        """Profile knowledge extraction performance"""
        print("\n=== Profiling Knowledge Extraction ===")

        extractor = KnowledgeExtractor()

        # Large document for testing
        text = """
        Artificial intelligence is transforming technology. Machine learning enables pattern recognition.
        Deep learning uses neural networks. Natural language processing analyzes text.
        Computer vision processes images. Robotics combines AI with physical systems.
        Expert systems encode human knowledge. Reinforcement learning optimizes decisions.
        """ * 50  # Repeat for larger dataset

        # Time concept extraction
        start = time.time()
        tracemalloc.start()

        concepts = await extractor.extract_concepts(text, use_ai=False)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed = time.time() - start

        self.results['knowledge_extraction'] = {
            'concepts_extracted': len(concepts),
            'time': elapsed,
            'memory_current_mb': current / 1024 / 1024,
            'memory_peak_mb': peak / 1024 / 1024,
            'throughput_concepts_per_sec': len(concepts) / elapsed if elapsed > 0 else 0
        }

        print(f"  Concepts extracted: {len(concepts)}")
        print(f"  Time: {elapsed:.3f}s")
        print(f"  Memory (current/peak): {current/1024/1024:.2f} / {peak/1024/1024:.2f} MB")

    async def profile_curiosity_engine(self):
        """Profile curiosity engine performance"""
        print("\n=== Profiling Curiosity Engine ===")

        kg = KnowledgeGraph()
        # Add test concepts
        for i in range(100):
            await kg.add_concept(f"Concept_{i}", "test", f"Description {i}")

        curiosity = CuriosityEngine(kg)

        # Time question generation
        start = time.time()
        tracemalloc.start()

        for _ in range(10):
            questions = await curiosity.generate_questions(context="AI research", max_questions=5)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed = time.time() - start

        self.results['curiosity_engine'] = {
            'iterations': 10,
            'time': elapsed,
            'memory_current_mb': current / 1024 / 1024,
            'memory_peak_mb': peak / 1024 / 1024,
            'avg_time_per_gen': elapsed / 10
        }

        print(f"  Iterations: 10")
        print(f"  Total time: {elapsed:.3f}s")
        print(f"  Avg per iteration: {elapsed/10:.3f}s")
        print(f"  Memory (current/peak): {current/1024/1024:.2f} / {peak/1024/1024:.2f} MB")

    async def profile_web_content_processor(self):
        """Profile web content processing"""
        print("\n=== Profiling Web Content Processor ===")

        processor = WebContentProcessor()

        html = """
        <html>
        <head><title>AI Research Article</title></head>
        <body>
            <h1>Machine Learning Advances</h1>
            <p>Recent developments in machine learning have shown significant progress.</p>
            <p>Neural networks are becoming more efficient and accurate.</p>
        </body>
        </html>
        """ * 20  # Larger content

        start = time.time()
        tracemalloc.start()

        for _ in range(50):
            content = await processor.process_url(
                "https://example.com",
                html,
                use_ai=False
            )

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed = time.time() - start

        self.results['web_content_processor'] = {
            'documents_processed': 50,
            'time': elapsed,
            'memory_current_mb': current / 1024 / 1024,
            'memory_peak_mb': peak / 1024 / 1024,
            'throughput_docs_per_sec': 50 / elapsed if elapsed > 0 else 0
        }

        print(f"  Documents processed: 50")
        print(f"  Total time: {elapsed:.3f}s")
        print(f"  Throughput: {50/elapsed:.2f} docs/sec")
        print(f"  Memory (current/peak): {current/1024/1024:.2f} / {peak/1024/1024:.2f} MB")

    async def profile_emotional_model(self):
        """Profile emotional processing"""
        print("\n=== Profiling Emotional Model ===")

        model = AdvancedEmotionalModel()

        start = time.time()
        tracemalloc.start()

        for _ in range(1000):
            await model.process_emotional_stimulus('joy', intensity=0.7)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed = time.time() - start

        self.results['emotional_model'] = {
            'stimuli_processed': 1000,
            'time': elapsed,
            'memory_current_mb': current / 1024 / 1024,
            'memory_peak_mb': peak / 1024 / 1024,
            'throughput_stimuli_per_sec': 1000 / elapsed if elapsed > 0 else 0
        }

        print(f"  Stimuli processed: 1000")
        print(f"  Total time: {elapsed:.3f}s")
        print(f"  Throughput: {1000/elapsed:.2f} stimuli/sec")
        print(f"  Memory (current/peak): {current/1024/1024:.2f} / {peak/1024/1024:.2f} MB")

    async def profile_theory_of_mind(self):
        """Profile theory of mind operations"""
        print("\n=== Profiling Theory of Mind ===")

        tom = TheoryOfMind()

        start = time.time()
        tracemalloc.start()

        for i in range(100):
            await tom.infer_belief(
                f"user_{i % 10}",
                "I think AI is fascinating",
                context="Technology discussion"
            )
            await tom.infer_emotional_state(f"user_{i % 10}", "This is amazing!")

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed = time.time() - start

        self.results['theory_of_mind'] = {
            'inferences': 200,
            'time': elapsed,
            'memory_current_mb': current / 1024 / 1024,
            'memory_peak_mb': peak / 1024 / 1024,
            'throughput_inferences_per_sec': 200 / elapsed if elapsed > 0 else 0
        }

        print(f"  Inferences: 200")
        print(f"  Total time: {elapsed:.3f}s")
        print(f"  Throughput: {200/elapsed:.2f} inferences/sec")
        print(f"  Memory (current/peak): {current/1024/1024:.2f} / {peak/1024/1024:.2f} MB")

    async def profile_problem_solving(self):
        """Profile problem-solving framework"""
        print("\n=== Profiling Problem Solving ===")

        framework = ProblemSolvingFramework()

        start = time.time()
        tracemalloc.start()

        for i in range(20):
            problem = await framework.analyze_problem(
                f"Optimize system performance issue {i}"
            )
            solution = await framework.solve_problem(problem, max_iterations=2)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed = time.time() - start

        self.results['problem_solving'] = {
            'problems_solved': 20,
            'time': elapsed,
            'memory_current_mb': current / 1024 / 1024,
            'memory_peak_mb': peak / 1024 / 1024,
            'avg_time_per_problem': elapsed / 20
        }

        print(f"  Problems solved: 20")
        print(f"  Total time: {elapsed:.3f}s")
        print(f"  Avg per problem: {elapsed/20:.3f}s")
        print(f"  Memory (current/peak): {current/1024/1024:.2f} / {peak/1024/1024:.2f} MB")

    async def profile_knowledge_graph(self):
        """Profile knowledge graph operations"""
        print("\n=== Profiling Knowledge Graph ===")

        kg = KnowledgeGraph()

        start = time.time()
        tracemalloc.start()

        # Add concepts
        concept_ids = []
        for i in range(500):
            concept = await kg.add_concept(f"Concept_{i}", "test", f"Description {i}")
            concept_ids.append(concept.id)

        # Add relationships
        for i in range(0, len(concept_ids) - 1, 2):
            await kg.add_relationship(
                f"Concept_{i}",
                f"Concept_{i+1}",
                RelationType.RELATED_TO
            )

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed = time.time() - start

        self.results['knowledge_graph'] = {
            'concepts_added': 500,
            'relationships_added': 250,
            'time': elapsed,
            'memory_current_mb': current / 1024 / 1024,
            'memory_peak_mb': peak / 1024 / 1024,
            'throughput_ops_per_sec': 750 / elapsed if elapsed > 0 else 0
        }

        print(f"  Concepts added: 500")
        print(f"  Relationships added: 250")
        print(f"  Total time: {elapsed:.3f}s")
        print(f"  Throughput: {750/elapsed:.2f} ops/sec")
        print(f"  Memory (current/peak): {current/1024/1024:.2f} / {peak/1024/1024:.2f} MB")

    def print_summary(self):
        """Print performance summary"""
        print("\n" + "=" * 70)
        print("PERFORMANCE SUMMARY")
        print("=" * 70)

        for module, metrics in self.results.items():
            print(f"\n{module.replace('_', ' ').title()}:")
            for key, value in metrics.items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.4f}")
                else:
                    print(f"  {key}: {value}")

        # Overall statistics
        total_time = sum(m.get('time', 0) for m in self.results.values())
        total_memory_peak = sum(m.get('memory_peak_mb', 0) for m in self.results.values())

        print("\nOverall:")
        print(f"  Total profiling time: {total_time:.3f}s")
        print(f"  Total peak memory: {total_memory_peak:.2f} MB")

    async def run_all_profiles(self):
        """Run all performance profiles"""
        print("Starting Performance Profiling...")
        print("=" * 70)

        await self.profile_knowledge_extraction()
        await self.profile_curiosity_engine()
        await self.profile_web_content_processor()
        await self.profile_emotional_model()
        await self.profile_theory_of_mind()
        await self.profile_problem_solving()
        await self.profile_knowledge_graph()

        self.print_summary()


async def main():
    """Main profiling entry point"""
    profiler = PerformanceProfiler()
    await profiler.run_all_profiles()


if __name__ == "__main__":
    asyncio.run(main())
