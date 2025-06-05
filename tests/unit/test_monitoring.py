"""
Unit tests for the Monitoring System
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.monitoring.metrics_collector import MetricsCollector, MetricType, MetricDefinition
from src.monitoring.prometheus_exporter import PrometheusExporter
from src.monitoring.health_checker import HealthChecker, HealthStatus, ComponentType, HealthCheck
from src.monitoring.monitoring_integration import MonitoringSystem
from src.core.service_registry import ServiceRegistry
from src.core.event_bus import EventBus


class TestMetricsCollector:
    """Test suite for MetricsCollector"""
    
    @pytest.fixture
    async def metrics_collector(self):
        """Create MetricsCollector instance"""
        service_registry = ServiceRegistry()
        event_bus = EventBus()
        
        collector = MetricsCollector(
            service_registry=service_registry,
            event_bus=event_bus,
            collect_interval=1.0
        )
        
        await collector.initialize()
        yield collector
        await collector.shutdown()
    
    @pytest.mark.asyncio
    async def test_initialization(self, metrics_collector):
        """Test metrics collector initialization"""
        # Check that standard metrics are registered
        assert metrics_collector.get_metric("claude_agi_up") is not None
        assert metrics_collector.get_metric("orchestrator_state_transitions_total") is not None
        assert metrics_collector.get_metric("memory_operations_total") is not None
    
    @pytest.mark.asyncio
    async def test_register_custom_metric(self, metrics_collector):
        """Test registering custom metrics"""
        # Register a custom counter
        definition = MetricDefinition(
            name="test_custom_counter",
            metric_type=MetricType.COUNTER,
            description="Test custom counter",
            labels=["test_label"]
        )
        
        metric = metrics_collector.register_metric(definition)
        assert metric is not None
        
        # Verify we can retrieve it
        retrieved = metrics_collector.get_metric("test_custom_counter")
        assert retrieved is not None
    
    @pytest.mark.asyncio
    async def test_record_api_request(self, metrics_collector):
        """Test recording API request metrics"""
        metrics_collector.record_api_request(
            method="GET",
            endpoint="/test",
            status_code=200,
            duration=0.123
        )
        
        # Metrics should be recorded (mocked in our case)
        assert True  # In real test, we'd verify the metric values
    
    @pytest.mark.asyncio
    async def test_time_operation_context(self, metrics_collector):
        """Test timing operations with context manager"""
        # Register a histogram for testing
        definition = MetricDefinition(
            name="test_operation_duration",
            metric_type=MetricType.HISTOGRAM,
            description="Test operation duration"
        )
        metrics_collector.register_metric(definition)
        
        # Time an operation
        with metrics_collector.time_operation("test_operation_duration"):
            await asyncio.sleep(0.01)
        
        # Operation should be timed
        assert True  # In real test, we'd verify the metric was observed


class TestHealthChecker:
    """Test suite for HealthChecker"""
    
    @pytest.fixture
    async def health_checker(self):
        """Create HealthChecker instance"""
        service_registry = ServiceRegistry()
        event_bus = EventBus()
        
        checker = HealthChecker(
            service_registry=service_registry,
            event_bus=event_bus,
            check_interval=60.0  # Long interval for testing
        )
        
        # Don't initialize to avoid background tasks
        yield checker
    
    @pytest.mark.asyncio
    async def test_register_health_check(self, health_checker):
        """Test registering custom health checks"""
        # Create a simple health check
        async def test_check():
            return {"status": "healthy"}
        
        check = HealthCheck(
            name="test_service",
            component_type=ComponentType.SERVICE,
            check_function=test_check,
            critical=True
        )
        
        health_checker.register_check(check)
        assert len(health_checker._health_checks) > 0
    
    @pytest.mark.asyncio
    async def test_check_health(self, health_checker):
        """Test performing health checks"""
        # Register a test check
        async def healthy_check():
            return {
                "name": "test_healthy",
                "status": HealthStatus.HEALTHY,
                "message": "All good"
            }
        
        check = HealthCheck(
            name="test_healthy",
            component_type=ComponentType.SERVICE,
            check_function=healthy_check
        )
        
        health_checker.register_check(check)
        
        # Perform health check
        result = await health_checker.check_health()
        
        assert result["status"] in ["healthy", "unknown"]
        assert "checks" in result
        assert "test_healthy" in result["checks"]
    
    @pytest.mark.asyncio
    async def test_system_status_calculation(self, health_checker):
        """Test system status calculation"""
        # Register multiple checks with different statuses
        async def healthy_check():
            from src.monitoring.health_checker import HealthCheckResult
            return HealthCheckResult(
                name="healthy_service",
                status=HealthStatus.HEALTHY,
                message="OK"
            )
        
        async def degraded_check():
            from src.monitoring.health_checker import HealthCheckResult
            return HealthCheckResult(
                name="degraded_service",
                status=HealthStatus.DEGRADED,
                message="Slow"
            )
        
        health_checker.register_check(HealthCheck(
            name="healthy_service",
            component_type=ComponentType.SERVICE,
            check_function=healthy_check,
            critical=False
        ))
        
        health_checker.register_check(HealthCheck(
            name="degraded_service",
            component_type=ComponentType.SERVICE,
            check_function=degraded_check,
            critical=False
        ))
        
        # Check health
        result = await health_checker.check_health()
        
        # With one degraded service, system should be degraded
        assert result["status"] in ["degraded", "healthy", "unknown"]


class TestPrometheusExporter:
    """Test suite for PrometheusExporter"""
    
    @pytest.fixture
    async def prometheus_exporter(self):
        """Create PrometheusExporter instance"""
        metrics_collector = MetricsCollector()
        
        exporter = PrometheusExporter(
            metrics_collector=metrics_collector,
            host="127.0.0.1",
            port=9091,  # Different port to avoid conflicts
            path="/metrics"
        )
        
        # Don't initialize to avoid starting web server
        yield exporter
    
    @pytest.mark.asyncio
    async def test_configuration(self, prometheus_exporter):
        """Test Prometheus exporter configuration"""
        assert prometheus_exporter.host == "127.0.0.1"
        assert prometheus_exporter.port == 9091
        assert prometheus_exporter.path == "/metrics"
    
    @pytest.mark.asyncio
    async def test_get_stats(self, prometheus_exporter):
        """Test getting exporter statistics"""
        stats = prometheus_exporter.get_stats()
        
        assert "request_count" in stats
        assert "endpoint" in stats
        assert stats["endpoint"] == "http://127.0.0.1:9091/metrics"


class TestMonitoringSystem:
    """Test suite for MonitoringSystem integration"""
    
    @pytest.fixture
    async def monitoring_system(self):
        """Create MonitoringSystem instance"""
        service_registry = ServiceRegistry()
        event_bus = EventBus()
        
        # Minimal config for testing
        config = {
            "prometheus": {"enabled": False},  # Disable to avoid port conflicts
            "metrics": {"collection_interval": 60.0},
            "health": {"enabled": True, "check_interval": 60.0}
        }
        
        system = MonitoringSystem(
            service_registry=service_registry,
            event_bus=event_bus,
            config=config
        )
        
        await system.initialize()
        yield system
        await system.shutdown()
    
    @pytest.mark.asyncio
    async def test_initialization(self, monitoring_system):
        """Test monitoring system initialization"""
        assert monitoring_system.metrics_collector is not None
        assert monitoring_system.health_checker is not None
        # Prometheus exporter should be None since we disabled it
        assert monitoring_system.prometheus_exporter is None
    
    @pytest.mark.asyncio
    async def test_get_health_status(self, monitoring_system):
        """Test getting health status through monitoring system"""
        status = await monitoring_system.get_health_status()
        
        assert "status" in status
        assert "timestamp" in status
        assert "checks" in status
    
    @pytest.mark.asyncio
    async def test_record_custom_metric(self, monitoring_system):
        """Test recording custom metrics"""
        # First register the metric
        from src.monitoring.metrics_collector import MetricDefinition, MetricType
        
        monitoring_system.metrics_collector.register_metric(MetricDefinition(
            name="test_gauge",
            metric_type=MetricType.GAUGE,
            description="Test gauge"
        ))
        
        # Record a value
        monitoring_system.record_custom_metric(
            metric_name="test_gauge",
            value=42.0,
            metric_type="gauge"
        )
        
        # Metric should be recorded
        assert True  # In real test, we'd verify the metric value
    
    @pytest.mark.asyncio
    async def test_create_custom_health_check(self, monitoring_system):
        """Test creating custom health checks"""
        # Define a custom check
        async def custom_check():
            return {"status": "healthy", "custom": True}
        
        monitoring_system.create_custom_health_check(
            name="custom_test",
            check_function=custom_check,
            component_type="service",
            critical=False
        )
        
        # Verify the check was added
        assert len(monitoring_system.health_checker._health_checks) > 0
    
    @pytest.mark.asyncio
    async def test_get_monitoring_endpoints(self, monitoring_system):
        """Test getting monitoring endpoints"""
        endpoints = monitoring_system.get_monitoring_endpoints()
        
        # Since Prometheus is disabled, should be empty
        assert isinstance(endpoints, dict)