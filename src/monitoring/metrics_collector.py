"""
Metrics Collector

Collects metrics from all system components for monitoring.
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timezone
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

try:
    from prometheus_client import Counter, Gauge, Histogram, Summary, Info
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False
    # Mock classes for when prometheus_client is not available
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, amount=1): pass
        def labels(self, **kwargs): return self
    
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, value): pass
        def inc(self, amount=1): pass
        def dec(self, amount=1): pass
        def labels(self, **kwargs): return self
    
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, amount): pass
        def labels(self, **kwargs): return self
    
    class Summary:
        def __init__(self, *args, **kwargs): pass
        def observe(self, amount): pass
        def labels(self, **kwargs): return self
    
    class Info:
        def __init__(self, *args, **kwargs): pass
        def info(self, value): pass

try:
    from ..core.service_registry import ServiceRegistry
    from ..core.event_bus import EventBus
except ImportError:
    # For standalone testing or when imported directly
    from core.service_registry import ServiceRegistry
    from core.event_bus import EventBus


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    INFO = "info"


@dataclass
class MetricDefinition:
    """Definition of a metric"""
    name: str
    metric_type: MetricType
    description: str
    labels: List[str] = field(default_factory=list)
    buckets: Optional[List[float]] = None  # For histograms
    
    
class MetricsCollector:
    """
    Central metrics collection system for all Claude-AGI components.
    
    Features:
    - Automatic metric discovery from services
    - Standard metrics for all components
    - Custom metric registration
    - Prometheus export format
    - Performance tracking
    """
    
    def __init__(
        self,
        service_registry: Optional[ServiceRegistry] = None,
        event_bus: Optional[EventBus] = None,
        collect_interval: float = 10.0
    ):
        self.service_registry = service_registry
        self.event_bus = event_bus
        self.collect_interval = collect_interval
        
        self.logger = logging.getLogger(__name__)
        
        # Metric storage
        self._metrics: Dict[str, Any] = {}
        self._metric_definitions: Dict[str, MetricDefinition] = {}
        
        # Collection task
        self._collection_task: Optional[asyncio.Task] = None
        
        # Initialize standard metrics
        self._initialize_standard_metrics()
        
    def _initialize_standard_metrics(self):
        """Initialize standard metrics for all components"""
        
        # System metrics
        self.register_metric(MetricDefinition(
            name="claude_agi_up",
            metric_type=MetricType.GAUGE,
            description="Whether Claude-AGI is up and running"
        ))
        
        self.register_metric(MetricDefinition(
            name="claude_agi_info",
            metric_type=MetricType.INFO,
            description="Claude-AGI version and configuration info"
        ))
        
        # Orchestrator metrics
        self.register_metric(MetricDefinition(
            name="orchestrator_state_transitions_total",
            metric_type=MetricType.COUNTER,
            description="Total number of state transitions",
            labels=["from_state", "to_state"]
        ))
        
        self.register_metric(MetricDefinition(
            name="orchestrator_current_state",
            metric_type=MetricType.GAUGE,
            description="Current orchestrator state",
            labels=["state"]
        ))
        
        self.register_metric(MetricDefinition(
            name="orchestrator_services_registered",
            metric_type=MetricType.GAUGE,
            description="Number of registered services"
        ))
        
        # Memory metrics
        self.register_metric(MetricDefinition(
            name="memory_operations_total",
            metric_type=MetricType.COUNTER,
            description="Total memory operations",
            labels=["operation", "status"]
        ))
        
        self.register_metric(MetricDefinition(
            name="memory_store_size",
            metric_type=MetricType.GAUGE,
            description="Size of memory stores",
            labels=["store_type"]
        ))
        
        self.register_metric(MetricDefinition(
            name="memory_operation_duration_seconds",
            metric_type=MetricType.HISTOGRAM,
            description="Memory operation duration",
            labels=["operation"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
        ))
        
        # Consciousness metrics
        self.register_metric(MetricDefinition(
            name="consciousness_thoughts_generated_total",
            metric_type=MetricType.COUNTER,
            description="Total thoughts generated",
            labels=["stream_type"]
        ))
        
        self.register_metric(MetricDefinition(
            name="consciousness_thought_generation_duration_seconds",
            metric_type=MetricType.HISTOGRAM,
            description="Thought generation duration",
            labels=["stream_type"],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        ))
        
        self.register_metric(MetricDefinition(
            name="consciousness_active_streams",
            metric_type=MetricType.GAUGE,
            description="Number of active consciousness streams"
        ))
        
        # Safety metrics
        self.register_metric(MetricDefinition(
            name="safety_validations_total",
            metric_type=MetricType.COUNTER,
            description="Total safety validations",
            labels=["validator", "result"]
        ))
        
        self.register_metric(MetricDefinition(
            name="safety_violations_total",
            metric_type=MetricType.COUNTER,
            description="Total safety violations detected",
            labels=["violation_type", "severity"]
        ))
        
        self.register_metric(MetricDefinition(
            name="safety_validation_duration_seconds",
            metric_type=MetricType.HISTOGRAM,
            description="Safety validation duration",
            labels=["validator"],
            buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1]
        ))
        
        # API metrics
        self.register_metric(MetricDefinition(
            name="api_requests_total",
            metric_type=MetricType.COUNTER,
            description="Total API requests",
            labels=["method", "endpoint", "status_code"]
        ))
        
        self.register_metric(MetricDefinition(
            name="api_request_duration_seconds",
            metric_type=MetricType.HISTOGRAM,
            description="API request duration",
            labels=["method", "endpoint"],
            buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        ))
        
        self.register_metric(MetricDefinition(
            name="api_active_connections",
            metric_type=MetricType.GAUGE,
            description="Active API connections",
            labels=["connection_type"]
        ))
        
        # Database metrics
        self.register_metric(MetricDefinition(
            name="database_connections_active",
            metric_type=MetricType.GAUGE,
            description="Active database connections",
            labels=["database_type"]
        ))
        
        self.register_metric(MetricDefinition(
            name="database_queries_total",
            metric_type=MetricType.COUNTER,
            description="Total database queries",
            labels=["database_type", "query_type", "status"]
        ))
        
        self.register_metric(MetricDefinition(
            name="database_query_duration_seconds",
            metric_type=MetricType.HISTOGRAM,
            description="Database query duration",
            labels=["database_type", "query_type"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
        ))
        
        # Event bus metrics
        self.register_metric(MetricDefinition(
            name="event_bus_messages_total",
            metric_type=MetricType.COUNTER,
            description="Total messages published",
            labels=["event_type"]
        ))
        
        self.register_metric(MetricDefinition(
            name="event_bus_subscribers",
            metric_type=MetricType.GAUGE,
            description="Number of event subscribers",
            labels=["event_type"]
        ))
        
        # Resource metrics
        self.register_metric(MetricDefinition(
            name="resource_cpu_usage_percent",
            metric_type=MetricType.GAUGE,
            description="CPU usage percentage"
        ))
        
        self.register_metric(MetricDefinition(
            name="resource_memory_usage_bytes",
            metric_type=MetricType.GAUGE,
            description="Memory usage in bytes"
        ))
        
        self.register_metric(MetricDefinition(
            name="resource_disk_usage_bytes",
            metric_type=MetricType.GAUGE,
            description="Disk usage in bytes",
            labels=["path"]
        ))
        
    def register_metric(self, definition: MetricDefinition) -> Any:
        """
        Register a new metric.
        
        Args:
            definition: Metric definition
            
        Returns:
            Prometheus metric object
        """
        if definition.name in self._metrics:
            return self._metrics[definition.name]
        
        self._metric_definitions[definition.name] = definition
        
        if HAS_PROMETHEUS:
            # Create actual Prometheus metric
            if definition.metric_type == MetricType.COUNTER:
                metric = Counter(
                    definition.name,
                    definition.description,
                    labelnames=definition.labels
                )
            elif definition.metric_type == MetricType.GAUGE:
                metric = Gauge(
                    definition.name,
                    definition.description,
                    labelnames=definition.labels
                )
            elif definition.metric_type == MetricType.HISTOGRAM:
                metric = Histogram(
                    definition.name,
                    definition.description,
                    labelnames=definition.labels,
                    buckets=definition.buckets or Histogram.DEFAULT_BUCKETS
                )
            elif definition.metric_type == MetricType.SUMMARY:
                metric = Summary(
                    definition.name,
                    definition.description,
                    labelnames=definition.labels
                )
            elif definition.metric_type == MetricType.INFO:
                metric = Info(
                    definition.name,
                    definition.description
                )
            else:
                raise ValueError(f"Unknown metric type: {definition.metric_type}")
        else:
            # Create mock metric
            if definition.metric_type == MetricType.COUNTER:
                metric = Counter()
            elif definition.metric_type == MetricType.GAUGE:
                metric = Gauge()
            elif definition.metric_type == MetricType.HISTOGRAM:
                metric = Histogram()
            elif definition.metric_type == MetricType.SUMMARY:
                metric = Summary()
            elif definition.metric_type == MetricType.INFO:
                metric = Info()
        
        self._metrics[definition.name] = metric
        return metric
    
    def get_metric(self, name: str) -> Any:
        """
        Get a registered metric.
        
        Args:
            name: Metric name
            
        Returns:
            Metric object
        """
        return self._metrics.get(name)
    
    async def initialize(self):
        """Initialize the metrics collector"""
        self.logger.info("Initializing Metrics Collector")
        
        # Set system up metric
        self.get_metric("claude_agi_up").set(1)
        
        # Set version info
        if HAS_PROMETHEUS:
            self.get_metric("claude_agi_info").info({
                "version": "1.3.0",
                "phase": "1",
                "prometheus_available": "true"
            })
        
        # Start collection task
        self._collection_task = asyncio.create_task(self._collection_loop())
        
        # Subscribe to events if event bus available
        if self.event_bus:
            await self._subscribe_to_events()
        
        # Register with service registry
        if self.service_registry:
            await self.service_registry.register_service(
                "metrics_collector",
                self,
                {"prometheus_available": HAS_PROMETHEUS}
            )
    
    async def shutdown(self):
        """Shutdown the metrics collector"""
        self.logger.info("Shutting down Metrics Collector")
        
        # Set system down metric
        self.get_metric("claude_agi_up").set(0)
        
        # Cancel collection task
        if self._collection_task:
            self._collection_task.cancel()
        
        # Unregister from service registry
        if self.service_registry:
            await self.service_registry.unregister_service("metrics_collector")
    
    async def collect_metrics(self):
        """
        Collect metrics from all registered services.
        
        This is called periodically and on-demand.
        """
        if not self.service_registry:
            return
        
        # Get all services
        services = await self.service_registry.list_services()
        
        for service_name, service_info in services.items():
            service = service_info["instance"]
            
            # Check if service has get_stats method
            if hasattr(service, "get_stats"):
                try:
                    stats = service.get_stats()
                    await self._process_service_stats(service_name, stats)
                except Exception as e:
                    self.logger.error(f"Failed to collect stats from {service_name}: {e}")
            
            # Check if service has get_metrics method
            if hasattr(service, "get_metrics"):
                try:
                    metrics = await service.get_metrics()
                    await self._process_service_metrics(service_name, metrics)
                except Exception as e:
                    self.logger.error(f"Failed to collect metrics from {service_name}: {e}")
        
        # Collect resource metrics
        await self._collect_resource_metrics()
    
    async def _collection_loop(self):
        """Background task for periodic metric collection"""
        while True:
            try:
                await asyncio.sleep(self.collect_interval)
                await self.collect_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Collection loop error: {e}")
    
    async def _subscribe_to_events(self):
        """Subscribe to events for metric updates"""
        # State transitions
        await self.event_bus.subscribe(
            "orchestrator.state_changed",
            self._handle_state_change
        )
        
        # Memory operations
        await self.event_bus.subscribe(
            "memory.thought_stored",
            self._handle_thought_stored
        )
        
        # Safety events
        await self.event_bus.subscribe(
            "safety.validation_complete",
            self._handle_safety_validation
        )
        
        await self.event_bus.subscribe(
            "safety.violation_detected",
            self._handle_safety_violation
        )
        
        # Service events
        await self.event_bus.subscribe(
            "service.registered",
            self._handle_service_registered
        )
        
        await self.event_bus.subscribe(
            "service.unregistered",
            self._handle_service_unregistered
        )
    
    async def _handle_state_change(self, event_data: Dict[str, Any]):
        """Handle state change events"""
        from_state = event_data.get("from_state", "unknown")
        to_state = event_data.get("to_state", "unknown")
        
        # Increment transition counter
        self.get_metric("orchestrator_state_transitions_total").labels(
            from_state=from_state,
            to_state=to_state
        ).inc()
        
        # Update current state gauge
        # Reset all state gauges to 0
        for state in ["IDLE", "THINKING", "EXPLORING", "CREATING", "REFLECTING", "SLEEPING"]:
            self.get_metric("orchestrator_current_state").labels(state=state).set(0)
        
        # Set current state to 1
        self.get_metric("orchestrator_current_state").labels(state=to_state).set(1)
    
    async def _handle_thought_stored(self, event_data: Dict[str, Any]):
        """Handle thought stored events"""
        stream_type = event_data.get("stream_type", "unknown")
        
        self.get_metric("consciousness_thoughts_generated_total").labels(
            stream_type=stream_type
        ).inc()
    
    async def _handle_safety_validation(self, event_data: Dict[str, Any]):
        """Handle safety validation events"""
        validator = event_data.get("validator", "unknown")
        result = "passed" if event_data.get("passed", False) else "failed"
        
        self.get_metric("safety_validations_total").labels(
            validator=validator,
            result=result
        ).inc()
    
    async def _handle_safety_violation(self, event_data: Dict[str, Any]):
        """Handle safety violation events"""
        violation_type = event_data.get("violation_type", "unknown")
        severity = event_data.get("severity", "unknown")
        
        self.get_metric("safety_violations_total").labels(
            violation_type=violation_type,
            severity=severity
        ).inc()
    
    async def _handle_service_registered(self, event_data: Dict[str, Any]):
        """Handle service registration events"""
        current = self.get_metric("orchestrator_services_registered")
        current.inc()
    
    async def _handle_service_unregistered(self, event_data: Dict[str, Any]):
        """Handle service unregistration events"""
        current = self.get_metric("orchestrator_services_registered")
        current.dec()
    
    async def _process_service_stats(self, service_name: str, stats: Dict[str, Any]):
        """Process stats from a service"""
        # Map common stat patterns to metrics
        
        # Memory stats
        if "memory" in service_name.lower():
            for key, value in stats.items():
                if "size" in key or "count" in key:
                    metric_name = f"{service_name}_{key}".lower().replace(" ", "_")
                    
                    # Try to use existing metric or create new one
                    metric = self.get_metric(metric_name)
                    if not metric:
                        metric = self.register_metric(MetricDefinition(
                            name=metric_name,
                            metric_type=MetricType.GAUGE,
                            description=f"{service_name} {key}"
                        ))
                    
                    if isinstance(value, (int, float)):
                        metric.set(value)
    
    async def _process_service_metrics(self, service_name: str, metrics: Dict[str, Any]):
        """Process metrics from a service"""
        # Services can provide their own metric updates
        for metric_name, metric_data in metrics.items():
            metric = self.get_metric(metric_name)
            if metric and isinstance(metric_data, dict):
                value = metric_data.get("value")
                labels = metric_data.get("labels", {})
                
                if labels:
                    metric = metric.labels(**labels)
                
                if "inc" in metric_data:
                    metric.inc(metric_data["inc"])
                elif "set" in metric_data and hasattr(metric, "set"):
                    metric.set(value)
                elif "observe" in metric_data and hasattr(metric, "observe"):
                    metric.observe(metric_data["observe"])
    
    async def _collect_resource_metrics(self):
        """Collect system resource metrics"""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.get_metric("resource_cpu_usage_percent").set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.get_metric("resource_memory_usage_bytes").set(memory.used)
            
            # Disk usage
            disk = psutil.disk_usage("/")
            self.get_metric("resource_disk_usage_bytes").labels(path="/").set(disk.used)
            
        except ImportError:
            # psutil not available
            pass
        except Exception as e:
            self.logger.error(f"Failed to collect resource metrics: {e}")
    
    def record_api_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float
    ):
        """
        Record an API request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            status_code: Response status code
            duration: Request duration in seconds
        """
        # Increment request counter
        self.get_metric("api_requests_total").labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        # Record duration
        self.get_metric("api_request_duration_seconds").labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_database_query(
        self,
        database_type: str,
        query_type: str,
        duration: float,
        success: bool = True
    ):
        """
        Record a database query.
        
        Args:
            database_type: Type of database (postgres, redis, etc)
            query_type: Type of query (select, insert, etc)
            duration: Query duration in seconds
            success: Whether query succeeded
        """
        status = "success" if success else "failure"
        
        # Increment query counter
        self.get_metric("database_queries_total").labels(
            database_type=database_type,
            query_type=query_type,
            status=status
        ).inc()
        
        # Record duration
        self.get_metric("database_query_duration_seconds").labels(
            database_type=database_type,
            query_type=query_type
        ).observe(duration)
    
    def time_operation(self, metric_name: str, labels: Optional[Dict[str, str]] = None):
        """
        Context manager for timing operations.
        
        Usage:
            with metrics_collector.time_operation("my_operation_duration_seconds", {"operation": "test"}):
                # Do operation
                pass
        """
        return MetricTimer(self, metric_name, labels)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics in a format suitable for export.
        
        Returns:
            Dict of metric names to current values
        """
        metrics_data = {}
        
        for name, definition in self._metric_definitions.items():
            metric = self._metrics.get(name)
            if metric:
                # This is simplified - real implementation would handle labels
                metrics_data[name] = {
                    "type": definition.metric_type.value,
                    "description": definition.description,
                    "labels": definition.labels
                }
        
        return metrics_data


class MetricTimer:
    """Context manager for timing operations"""
    
    def __init__(
        self,
        collector: MetricsCollector,
        metric_name: str,
        labels: Optional[Dict[str, str]] = None
    ):
        self.collector = collector
        self.metric_name = metric_name
        self.labels = labels or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            metric = self.collector.get_metric(self.metric_name)
            
            if metric:
                if self.labels:
                    metric = metric.labels(**self.labels)
                
                if hasattr(metric, "observe"):
                    metric.observe(duration)
                elif hasattr(metric, "set"):
                    metric.set(duration)