"""
Monitoring Integration

Integrates monitoring components into the Claude-AGI system.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import yaml

from .metrics_collector import MetricsCollector
from .prometheus_exporter import PrometheusExporter
from .health_checker import HealthChecker
try:
    from ..core.service_registry import ServiceRegistry
    from ..core.event_bus import EventBus
except ImportError:
    # For standalone testing or when imported directly
    from core.service_registry import ServiceRegistry
    from core.event_bus import EventBus


class MonitoringSystem:
    """
    Integrates all monitoring components into Claude-AGI.
    
    This provides a single entry point for setting up:
    - Metrics collection
    - Prometheus export
    - Health checks
    - Alerting (when configured)
    """
    
    def __init__(
        self,
        service_registry: ServiceRegistry,
        event_bus: EventBus,
        config: Optional[Dict[str, Any]] = None
    ):
        self.service_registry = service_registry
        self.event_bus = event_bus
        self.config = config or {}
        
        self.logger = logging.getLogger(__name__)
        
        # Components
        self.metrics_collector: Optional[MetricsCollector] = None
        self.prometheus_exporter: Optional[PrometheusExporter] = None
        self.health_checker: Optional[HealthChecker] = None
        
        # Load monitoring config if not provided
        if not self.config:
            self._load_default_config()
    
    def _load_default_config(self):
        """Load default monitoring configuration"""
        config_path = Path(__file__).parent.parent.parent / "configs" / "monitoring.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            # Fallback to minimal config
            self.config = {
                "prometheus": {"enabled": True, "port": 9090},
                "metrics": {"collection_interval": 10.0},
                "health": {"enabled": True, "check_interval": 30.0}
            }
    
    async def initialize(self):
        """Initialize the monitoring system"""
        self.logger.info("Initializing Monitoring System")
        
        # Initialize metrics collector
        metrics_config = self.config.get("metrics", {})
        self.metrics_collector = MetricsCollector(
            service_registry=self.service_registry,
            event_bus=self.event_bus,
            collect_interval=metrics_config.get("collection_interval", 10.0)
        )
        await self.metrics_collector.initialize()
        
        # Initialize Prometheus exporter if enabled
        prometheus_config = self.config.get("prometheus", {})
        if prometheus_config.get("enabled", True):
            self.prometheus_exporter = PrometheusExporter(
                metrics_collector=self.metrics_collector,
                service_registry=self.service_registry,
                host=prometheus_config.get("host", "0.0.0.0"),
                port=prometheus_config.get("port", 9090),
                path=prometheus_config.get("path", "/metrics"),
                auth_token=prometheus_config.get("auth_token")
            )
            await self.prometheus_exporter.initialize()
        
        # Initialize health checker if enabled
        health_config = self.config.get("health", {})
        if health_config.get("enabled", True):
            self.health_checker = HealthChecker(
                service_registry=self.service_registry,
                event_bus=self.event_bus,
                metrics_collector=self.metrics_collector,
                check_interval=health_config.get("check_interval", 30.0),
                history_size=health_config.get("history_size", 100)
            )
            await self.health_checker.initialize()
        
        # Register monitoring system itself
        await self.service_registry.register_service(
            "monitoring_system",
            self,
            {
                "prometheus_enabled": prometheus_config.get("enabled", True),
                "health_checks_enabled": health_config.get("enabled", True)
            }
        )
        
        self.logger.info("Monitoring System initialized successfully")
    
    async def shutdown(self):
        """Shutdown the monitoring system"""
        self.logger.info("Shutting down Monitoring System")
        
        # Shutdown components in reverse order
        if self.health_checker:
            await self.health_checker.shutdown()
        
        if self.prometheus_exporter:
            await self.prometheus_exporter.shutdown()
        
        if self.metrics_collector:
            await self.metrics_collector.shutdown()
        
        # Unregister from service registry
        await self.service_registry.unregister_service("monitoring_system")
    
    def get_metrics_collector(self) -> Optional[MetricsCollector]:
        """Get the metrics collector instance"""
        return self.metrics_collector
    
    def get_health_checker(self) -> Optional[HealthChecker]:
        """Get the health checker instance"""
        return self.health_checker
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get current health status.
        
        Returns:
            Dict containing health information
        """
        if self.health_checker:
            return await self.health_checker.check_health()
        return {"status": "unknown", "message": "Health checker not available"}
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current metrics.
        
        Returns:
            Dict containing metrics summary
        """
        if self.metrics_collector:
            return self.metrics_collector.get_all_metrics()
        return {}
    
    def record_custom_metric(
        self,
        metric_name: str,
        value: float,
        metric_type: str = "gauge",
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Record a custom metric.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            metric_type: Type of metric (counter, gauge, histogram)
            labels: Optional labels
        """
        if not self.metrics_collector:
            return
        
        metric = self.metrics_collector.get_metric(metric_name)
        if not metric:
            # Metric doesn't exist, log warning
            self.logger.warning(f"Metric {metric_name} not registered")
            return
        
        if labels:
            metric = metric.labels(**labels)
        
        if metric_type == "counter" and hasattr(metric, "inc"):
            metric.inc(value)
        elif metric_type == "gauge" and hasattr(metric, "set"):
            metric.set(value)
        elif metric_type == "histogram" and hasattr(metric, "observe"):
            metric.observe(value)
    
    def create_custom_health_check(
        self,
        name: str,
        check_function,
        component_type: str = "custom",
        critical: bool = False,
        timeout: float = 5.0
    ):
        """
        Create a custom health check.
        
        Args:
            name: Name of the health check
            check_function: Function to call for health check
            component_type: Type of component
            critical: Whether this is a critical check
            timeout: Timeout for the check
        """
        if not self.health_checker:
            return
        
        from .health_checker import HealthCheck, ComponentType
        
        # Map string to enum
        component_type_map = {
            "service": ComponentType.SERVICE,
            "database": ComponentType.DATABASE,
            "api": ComponentType.API,
            "memory": ComponentType.MEMORY,
            "consciousness": ComponentType.CONSCIOUSNESS,
            "safety": ComponentType.SAFETY
        }
        
        component_type_enum = component_type_map.get(
            component_type.lower(),
            ComponentType.SERVICE
        )
        
        health_check = HealthCheck(
            name=name,
            component_type=component_type_enum,
            check_function=check_function,
            timeout=timeout,
            critical=critical
        )
        
        self.health_checker.register_check(health_check)
    
    def get_monitoring_endpoints(self) -> Dict[str, str]:
        """
        Get URLs for monitoring endpoints.
        
        Returns:
            Dict of endpoint names to URLs
        """
        endpoints = {}
        
        if self.prometheus_exporter:
            prom_config = self.config.get("prometheus", {})
            host = prom_config.get("host", "0.0.0.0")
            port = prom_config.get("port", 9090)
            path = prom_config.get("path", "/metrics")
            
            # Convert 0.0.0.0 to localhost for user-friendly URL
            display_host = "localhost" if host == "0.0.0.0" else host
            
            endpoints["prometheus_metrics"] = f"http://{display_host}:{port}{path}"
            endpoints["health_check"] = f"http://{display_host}:{port}/health"
            endpoints["readiness_check"] = f"http://{display_host}:{port}/ready"
        
        return endpoints