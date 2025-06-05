"""
Monitoring Hooks for Core Components

Provides monitoring integration for core Claude-AGI components.
"""

import time
import functools
from typing import Optional, Dict, Any, Callable
from datetime import datetime


class MonitoringHooks:
    """
    Provides monitoring hooks that can be integrated into any component.
    """
    
    def __init__(self, metrics_collector=None):
        self.metrics_collector = metrics_collector
    
    def track_operation(self, operation_name: str, labels: Optional[Dict[str, str]] = None):
        """
        Decorator to track operation metrics.
        
        Usage:
            @monitoring_hooks.track_operation("memory_store")
            async def store_memory(self, data):
                # ... operation code ...
        """
        def decorator(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    raise
                finally:
                    duration = time.time() - start_time
                    
                    if self.metrics_collector:
                        # Record operation counter
                        counter_labels = labels or {}
                        counter_labels.update({
                            "operation": operation_name,
                            "status": "success" if success else "failure"
                        })
                        
                        counter = self.metrics_collector.get_metric("operations_total")
                        if counter:
                            counter.labels(**counter_labels).inc()
                        
                        # Record operation duration
                        histogram_labels = labels or {}
                        histogram_labels["operation"] = operation_name
                        
                        histogram = self.metrics_collector.get_metric("operation_duration_seconds")
                        if histogram:
                            histogram.labels(**histogram_labels).observe(duration)
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    raise
                finally:
                    duration = time.time() - start_time
                    
                    if self.metrics_collector:
                        # Record metrics (same as async)
                        counter_labels = labels or {}
                        counter_labels.update({
                            "operation": operation_name,
                            "status": "success" if success else "failure"
                        })
                        
                        counter = self.metrics_collector.get_metric("operations_total")
                        if counter:
                            counter.labels(**counter_labels).inc()
                        
                        histogram_labels = labels or {}
                        histogram_labels["operation"] = operation_name
                        
                        histogram = self.metrics_collector.get_metric("operation_duration_seconds")
                        if histogram:
                            histogram.labels(**histogram_labels).observe(duration)
            
            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def update_gauge(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Update a gauge metric."""
        if self.metrics_collector:
            metric = self.metrics_collector.get_metric(metric_name)
            if metric:
                if labels:
                    metric = metric.labels(**labels)
                metric.set(value)
    
    def increment_counter(self, metric_name: str, amount: float = 1, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        if self.metrics_collector:
            metric = self.metrics_collector.get_metric(metric_name)
            if metric:
                if labels:
                    metric = metric.labels(**labels)
                metric.inc(amount)
    
    def observe_histogram(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value in a histogram."""
        if self.metrics_collector:
            metric = self.metrics_collector.get_metric(metric_name)
            if metric:
                if labels:
                    metric = metric.labels(**labels)
                metric.observe(value)
    
    def time_operation(self, metric_name: str, labels: Optional[Dict[str, str]] = None):
        """Context manager for timing operations."""
        if self.metrics_collector:
            return self.metrics_collector.time_operation(metric_name, labels)
        else:
            # Return a no-op context manager
            class NoOpTimer:
                def __enter__(self): return self
                def __exit__(self, *args): pass
            return NoOpTimer()


# Example integration into a service
class MonitoredService:
    """Example of how to integrate monitoring into a service."""
    
    def __init__(self, monitoring_hooks: Optional[MonitoringHooks] = None):
        self.monitoring = monitoring_hooks or MonitoringHooks()
    
    @property
    def monitoring_hooks(self) -> MonitoringHooks:
        """Get monitoring hooks for this service."""
        return self.monitoring
    
    async def initialize(self):
        """Initialize the service with monitoring."""
        # Update service status gauge
        self.monitoring.update_gauge("service_status", 1.0, {"service": self.__class__.__name__})
    
    async def shutdown(self):
        """Shutdown the service with monitoring."""
        # Update service status gauge
        self.monitoring.update_gauge("service_status", 0.0, {"service": self.__class__.__name__})
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get service-specific metrics.
        
        Services can override this to provide custom metrics.
        """
        return {}
    
    def get_health_check(self) -> Callable:
        """
        Get health check function for this service.
        
        Services can override this to provide custom health checks.
        """
        async def default_health_check():
            return {
                "status": "healthy",
                "service": self.__class__.__name__,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return default_health_check


# Import asyncio for the decorator
import asyncio