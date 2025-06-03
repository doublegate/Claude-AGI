"""
Debug inspector for Claude AGI consciousness system.

Provides deep inspection and debugging capabilities for consciousness processes.
"""

import asyncio
import json
import time
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
from contextlib import contextmanager
from collections import defaultdict


logger = logging.getLogger(__name__)


class TraceData:
    """Container for trace data"""
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.duration = 0
        self.memory_calls = []
        self.api_calls = []
        self.branches = []
        self.errors = []
        self.logs = []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'memory_calls': len(self.memory_calls),
            'api_calls': len(self.api_calls),
            'branches': len(self.branches),
            'errors': self.errors,
            'logs': self.logs[-100:]  # Last 100 logs
        }


class RemoteDebugger:
    """Remote debugging capabilities"""
    
    def __init__(self):
        self.traces = {}
        self.current_trace = None
        self.breakpoints = set()
        self.watch_variables = {}
        
    @contextmanager
    def trace(self, name: str):
        """Context manager for tracing execution"""
        trace = TraceData(name)
        trace.start_time = datetime.utcnow()
        self.traces[name] = trace
        self.current_trace = trace
        
        try:
            yield trace
        finally:
            trace.end_time = datetime.utcnow()
            trace.duration = (trace.end_time - trace.start_time).total_seconds()
            self.current_trace = None
            
    def log_memory_access(self, operation: str, key: str, value: Any = None):
        """Log memory access"""
        if self.current_trace:
            self.current_trace.memory_calls.append({
                'operation': operation,
                'key': key,
                'value_type': type(value).__name__ if value else None,
                'timestamp': datetime.utcnow().isoformat()
            })
            
    def log_api_call(self, endpoint: str, params: Dict[str, Any], response: Any = None):
        """Log API call"""
        if self.current_trace:
            self.current_trace.api_calls.append({
                'endpoint': endpoint,
                'params': params,
                'response_type': type(response).__name__ if response else None,
                'timestamp': datetime.utcnow().isoformat()
            })
            
    def log_branch(self, condition: str, taken: bool):
        """Log branching decision"""
        if self.current_trace:
            self.current_trace.branches.append({
                'condition': condition,
                'taken': taken,
                'timestamp': datetime.utcnow().isoformat()
            })
            
    def log_error(self, error: Exception):
        """Log error"""
        if self.current_trace:
            self.current_trace.errors.append({
                'type': type(error).__name__,
                'message': str(error),
                'traceback': traceback.format_exc(),
                'timestamp': datetime.utcnow().isoformat()
            })
            
    def add_log(self, level: str, message: str):
        """Add log entry"""
        if self.current_trace:
            self.current_trace.logs.append({
                'level': level,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            })
            
    def get_trace_data(self, name: str) -> Dict[str, Any]:
        """Get trace data by name"""
        if name in self.traces:
            return self.traces[name].to_dict()
        return {}
        
    def set_breakpoint(self, location: str):
        """Set a breakpoint"""
        self.breakpoints.add(location)
        
    def remove_breakpoint(self, location: str):
        """Remove a breakpoint"""
        self.breakpoints.discard(location)
        
    def watch_variable(self, name: str, value: Any):
        """Watch a variable"""
        self.watch_variables[name] = {
            'value': value,
            'type': type(value).__name__,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    async def check_breakpoint(self, location: str):
        """Check if we hit a breakpoint"""
        if location in self.breakpoints:
            logger.info(f"Breakpoint hit at {location}")
            # In production, this would pause and wait for debugger commands
            await asyncio.sleep(0.1)


class ConsciousnessInspector:
    """Deep inspection of consciousness processes"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.debugger = RemoteDebugger()
        self.inspection_history = []
        
    async def inspect_thought_generation(self) -> Dict[str, Any]:
        """Deep inspection of thought generation process"""
        # Enable verbose logging
        original_level = logger.level
        logger.setLevel(logging.DEBUG)
        
        try:
            # Trace thought generation
            with self.debugger.trace('thought_generation'):
                # Hook into consciousness service
                consciousness = self.orchestrator.services.get('consciousness')
                if not consciousness:
                    raise ValueError("Consciousness service not found")
                    
                # Start timing
                start_time = time.perf_counter()
                
                # Monitor memory accesses
                memory_accesses_before = self._count_memory_accesses()
                
                # Generate thought
                thought = await consciousness.generate_thought()
                
                # End timing
                end_time = time.perf_counter()
                generation_time = end_time - start_time
                
                # Count memory accesses
                memory_accesses_after = self._count_memory_accesses()
                memory_accesses = memory_accesses_after - memory_accesses_before
                
            # Analyze trace
            trace_data = self.debugger.get_trace_data('thought_generation')
            
            inspection_result = {
                'thought': thought,
                'generation_time': generation_time,
                'memory_accesses': memory_accesses,
                'api_calls': len(trace_data.get('api_calls', [])),
                'decision_points': len(trace_data.get('branches', [])),
                'errors': trace_data.get('errors', []),
                'metadata': {
                    'timestamp': datetime.utcnow().isoformat(),
                    'orchestrator_state': self.orchestrator.state.value,
                    'service_count': len(self.orchestrator.services),
                    'memory_usage': self._get_memory_usage()
                }
            }
            
            # Store in history
            self.inspection_history.append(inspection_result)
            
            return inspection_result
            
        finally:
            # Restore logging level
            logger.setLevel(original_level)
            
    async def inspect_memory_formation(self) -> Dict[str, Any]:
        """Inspect how memories are formed and stored"""
        with self.debugger.trace('memory_formation'):
            memory_manager = self.orchestrator.services.get('memory')
            if not memory_manager:
                raise ValueError("Memory manager not found")
                
            # Create test memory
            test_content = "This is a test memory for inspection"
            
            # Trace storage process
            memory_id = await memory_manager.store_memory({
                'content': test_content,
                'type': 'debug',
                'timestamp': datetime.utcnow()
            })
            
            # Trace retrieval
            retrieved = await memory_manager.retrieve_memory(memory_id)
            
            # Trace consolidation impact
            await memory_manager.consolidate_memories()
            
        trace_data = self.debugger.get_trace_data('memory_formation')
        
        return {
            'memory_id': memory_id,
            'storage_time': trace_data.get('duration', 0),
            'retrieval_success': retrieved is not None,
            'consolidation_impact': 'unknown',  # Would need more analysis
            'trace_data': trace_data
        }
        
    async def inspect_service_communication(self) -> Dict[str, Any]:
        """Inspect inter-service communication patterns"""
        communication_log = []
        
        # Hook into message passing
        original_publish = self.orchestrator.publish_message
        
        def logged_publish(topic: str, message: Any):
            communication_log.append({
                'timestamp': datetime.utcnow().isoformat(),
                'topic': topic,
                'message_type': type(message).__name__,
                'size': len(str(message))
            })
            return original_publish(topic, message)
            
        # Temporarily replace publish method
        self.orchestrator.publish_message = logged_publish
        
        try:
            # Run for a short period
            await asyncio.sleep(5)
            
            # Analyze patterns
            topics = defaultdict(int)
            for entry in communication_log:
                topics[entry['topic']] += 1
                
            return {
                'total_messages': len(communication_log),
                'unique_topics': len(topics),
                'topic_frequency': dict(topics),
                'message_log': communication_log[-50:],  # Last 50 messages
                'messages_per_second': len(communication_log) / 5
            }
            
        finally:
            # Restore original method
            self.orchestrator.publish_message = original_publish
            
    async def replay_scenario(self, scenario_file: str) -> Dict[str, Any]:
        """Replay a specific scenario for debugging"""
        scenario_path = Path(scenario_file)
        if not scenario_path.exists():
            raise FileNotFoundError(f"Scenario file not found: {scenario_file}")
            
        # Load scenario
        with open(scenario_path) as f:
            scenario = json.load(f)
            
        # Reset to scenario state
        if 'initial_state' in scenario:
            await self.orchestrator.restore_state(scenario['initial_state'])
            
        # Replay events
        results = []
        for i, event in enumerate(scenario.get('events', [])):
            try:
                result = await self.orchestrator.process_event(event)
                results.append({
                    'event_index': i,
                    'event_type': event.get('type'),
                    'success': True,
                    'result': result
                })
                
                # Respect timing
                if 'delay' in event:
                    await asyncio.sleep(event['delay'])
                    
            except Exception as e:
                results.append({
                    'event_index': i,
                    'event_type': event.get('type'),
                    'success': False,
                    'error': str(e)
                })
                
        # Capture final state
        final_state = await self.orchestrator.capture_state()
        
        # Compare with expected
        differences = []
        if 'expected_state' in scenario:
            differences = self._compare_states(
                scenario['expected_state'], 
                final_state
            )
            
        return {
            'scenario': scenario_file,
            'events_processed': len(results),
            'successful_events': sum(1 for r in results if r['success']),
            'final_state': final_state,
            'differences': differences,
            'event_results': results
        }
        
    def _count_memory_accesses(self) -> int:
        """Count memory accesses (simplified)"""
        memory_manager = self.orchestrator.services.get('memory')
        if memory_manager and hasattr(memory_manager, 'access_count'):
            return memory_manager.access_count
        return 0
        
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        try:
            import psutil
            process = psutil.Process()
            return {
                'rss_mb': process.memory_info().rss / 1024 / 1024,
                'vms_mb': process.memory_info().vms / 1024 / 1024,
                'percent': process.memory_percent()
            }
        except ImportError:
            return {'error': 'psutil not available'}
            
    def _compare_states(self, expected: Dict[str, Any], 
                       actual: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compare two states and return differences"""
        differences = []
        
        # Check expected keys
        for key in expected:
            if key not in actual:
                differences.append({
                    'type': 'missing_key',
                    'key': key,
                    'expected': expected[key]
                })
            elif expected[key] != actual[key]:
                differences.append({
                    'type': 'value_mismatch',
                    'key': key,
                    'expected': expected[key],
                    'actual': actual[key]
                })
                
        # Check extra keys
        for key in actual:
            if key not in expected:
                differences.append({
                    'type': 'extra_key',
                    'key': key,
                    'actual': actual[key]
                })
                
        return differences
        
    async def generate_debug_report(self) -> Dict[str, Any]:
        """Generate comprehensive debug report"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'system_state': {
                'orchestrator_state': self.orchestrator.state.value,
                'services': list(self.orchestrator.services.keys()),
                'uptime': self._calculate_uptime()
            },
            'recent_inspections': self.inspection_history[-10:],
            'performance_metrics': await self._collect_performance_metrics(),
            'error_summary': self._summarize_errors(),
            'recommendations': self._generate_recommendations()
        }
        
        return report
        
    def _calculate_uptime(self) -> float:
        """Calculate system uptime"""
        if hasattr(self.orchestrator, 'start_time'):
            return (datetime.utcnow() - self.orchestrator.start_time).total_seconds()
        return 0
        
    async def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect performance metrics"""
        metrics = {}
        
        # Thought generation rate
        consciousness = self.orchestrator.services.get('consciousness')
        if consciousness and hasattr(consciousness, 'thought_count'):
            uptime = self._calculate_uptime()
            if uptime > 0:
                metrics['thoughts_per_second'] = consciousness.thought_count / uptime
                
        # Memory retrieval time (would need actual measurement)
        metrics['avg_memory_retrieval_ms'] = 15.0  # Placeholder
        
        # Service response times
        metrics['service_health'] = {}
        for name, service in self.orchestrator.services.items():
            if hasattr(service, 'is_healthy'):
                metrics['service_health'][name] = await service.is_healthy()
                
        return metrics
        
    def _summarize_errors(self) -> Dict[str, Any]:
        """Summarize errors from traces"""
        error_summary = defaultdict(int)
        
        for trace in self.debugger.traces.values():
            for error in trace.errors:
                error_summary[error['type']] += 1
                
        return dict(error_summary)
        
    def _generate_recommendations(self) -> List[str]:
        """Generate debugging recommendations"""
        recommendations = []
        
        # Check error patterns
        errors = self._summarize_errors()
        if errors:
            recommendations.append(
                f"Address frequent errors: {', '.join(errors.keys())}"
            )
            
        # Check performance
        if self.inspection_history:
            avg_thought_time = sum(
                i['generation_time'] for i in self.inspection_history
            ) / len(self.inspection_history)
            
            if avg_thought_time > 2.0:
                recommendations.append(
                    f"Optimize thought generation (avg: {avg_thought_time:.2f}s)"
                )
                
        # Check memory usage
        memory_usage = self._get_memory_usage()
        if memory_usage.get('percent', 0) > 80:
            recommendations.append(
                "High memory usage detected - consider optimization"
            )
            
        return recommendations


def load_scenario(scenario_file: str) -> Dict[str, Any]:
    """Load a test scenario from file"""
    with open(scenario_file) as f:
        return json.load(f)


def compare_states(expected: Dict[str, Any], 
                  actual: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Compare two states and return differences"""
    inspector = ConsciousnessInspector(None)
    return inspector._compare_states(expected, actual)


async def main():
    """Test the inspector"""
    from src.core.orchestrator import AGIOrchestrator
    
    # Create orchestrator
    orchestrator = AGIOrchestrator()
    
    # Create inspector
    inspector = ConsciousnessInspector(orchestrator)
    
    # Run inspection
    result = await inspector.inspect_thought_generation()
    print("Thought Generation Inspection:", json.dumps(result, indent=2))
    
    # Generate debug report
    report = await inspector.generate_debug_report()
    print("\nDebug Report:", json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())