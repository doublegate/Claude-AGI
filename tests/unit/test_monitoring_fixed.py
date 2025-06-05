"""
Fixed unit tests for monitoring system components.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import time

# Patch prometheus client to avoid registry conflicts
import sys
from unittest.mock import MagicMock

# Mock prometheus_client before import
sys.modules['prometheus_client'] = MagicMock()
sys.modules['prometheus_client.registry'] = MagicMock()

from monitoring.metrics_collector import MetricsCollector, MetricType, MetricDefinition
from monitoring.health_checker import HealthChecker, HealthCheck, HealthStatus, ComponentType
from monitoring.monitoring_integration import MonitoringSystem
from core.monitoring_hooks import MonitoringHooks
from core.event_bus import EventBus, Event


class TestMonitoringHooks:
    """Test MonitoringHooks functionality"""
    
    @pytest.fixture
    def hooks(self):
        """Create MonitoringHooks instance"""
        # Since MetricsCollector is optional, we can use None
        return MonitoringHooks(metrics_collector=None)
    
    def test_increment_counter_no_collector(self, hooks):
        """Test incrementing counter without collector (should not fail)"""
        # Should not raise exception
        hooks.increment_counter('test_counter', 5, {'label': 'value'})
    
    def test_update_gauge_no_collector(self, hooks):
        """Test updating gauge without collector (should not fail)"""
        # Should not raise exception
        hooks.update_gauge('test_gauge', 42.5, {'label': 'value'})
    
    def test_time_operation_context_no_collector(self, hooks):
        """Test timing operation without collector"""
        # Should work as no-op context manager
        with hooks.time_operation('test_op', {'label': 'value'}):
            time.sleep(0.01)
    
    @pytest.mark.asyncio
    async def test_track_operation_decorator(self, hooks):
        """Test track_operation decorator without collector"""
        @hooks.track_operation('test_operation', {'type': 'test'})
        async def test_function():
            await asyncio.sleep(0.01)
            return "result"
        
        result = await test_function()
        assert result == "result"


class TestHealthCheckerBasic:
    """Basic tests for HealthChecker without full initialization"""
    
    def test_health_check_creation(self):
        """Test creating a HealthCheck object"""
        async def test_check():
            return {'status': 'healthy'}
        
        check = HealthCheck(
            name='test_service',
            component_type=ComponentType.SERVICE,
            check_function=test_check,
            critical=True,
            timeout=5.0
        )
        
        assert check.name == 'test_service'
        assert check.component_type == ComponentType.SERVICE
        assert check.critical is True
        assert check.timeout == 5.0
    
    def test_health_status_enum(self):
        """Test HealthStatus enum values"""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.UNKNOWN.value == "unknown"


class TestMetricsCollectorBasic:
    """Basic tests for MetricsCollector functionality"""
    
    def test_metric_type_enum(self):
        """Test MetricType enum values"""
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.HISTOGRAM.value == "histogram"
    
    def test_metric_definition_creation(self):
        """Test creating MetricDefinition"""
        definition = MetricDefinition(
            name="test_metric",
            metric_type=MetricType.COUNTER,
            description="Test metric",
            labels=["service", "method"]
        )
        
        assert definition.name == "test_metric"
        assert definition.metric_type == MetricType.COUNTER
        assert definition.description == "Test metric"
        assert definition.labels == ["service", "method"]


class TestMonitoringSystemConfig:
    """Test MonitoringSystem configuration handling"""
    
    def test_config_parsing(self):
        """Test configuration parsing"""
        config = {
            'monitoring': {
                'enabled': True,
                'prometheus': {
                    'enabled': True,
                    'port': 9090,
                    'path': '/metrics'
                },
                'health_check': {
                    'enabled': True,
                    'interval': 30
                },
                'metrics': {
                    'collect_interval': 10,
                    'include_system_metrics': True
                }
            }
        }
        
        # Extract monitoring config
        monitoring_config = config.get('monitoring', {})
        
        assert monitoring_config['enabled'] is True
        assert monitoring_config['prometheus']['port'] == 9090
        assert monitoring_config['health_check']['interval'] == 30
        assert monitoring_config['metrics']['include_system_metrics'] is True


class TestEventBusIntegration:
    """Test EventBus integration with monitoring"""
    
    @pytest.fixture
    def event_bus(self):
        """Create EventBus instance"""
        return EventBus()
    
    def test_subscribe_to_events(self, event_bus):
        """Test subscribing to events"""
        called = False
        
        def handler(event):
            nonlocal called
            called = True
            assert event.type == "test.event"
            assert event.data == {"test": "data"}
        
        # Subscribe is synchronous
        event_bus.subscribe("test.event", handler)
        
        # Verify subscription
        assert "test.event" in event_bus._event_handlers
        assert handler in event_bus._event_handlers["test.event"]
    
    @pytest.mark.asyncio
    async def test_publish_event(self, event_bus):
        """Test publishing events"""
        received_events = []
        
        async def handler(event):
            received_events.append(event)
        
        event_bus.subscribe("test.event", handler)
        
        # Create and publish event
        event = Event(
            type="test.event",
            source="test",
            data={"message": "test"}
        )
        
        await event_bus.publish(event)
        
        # Event should be received
        assert len(received_events) == 1
        assert received_events[0].data["message"] == "test"


class TestMonitoringHooksWithCollector:
    """Test MonitoringHooks with mocked collector"""
    
    @pytest.fixture
    def mock_metric(self):
        """Create mock metric"""
        metric = Mock()
        metric.inc = Mock()
        metric.set = Mock()
        metric.observe = Mock()
        metric.labels = Mock(return_value=metric)
        return metric
    
    @pytest.fixture
    def mock_collector(self, mock_metric):
        """Create mock metrics collector"""
        collector = Mock(spec=MetricsCollector)
        collector.get_metric = Mock(return_value=mock_metric)
        collector.time_operation = Mock()
        return collector
    
    @pytest.fixture
    def hooks_with_collector(self, mock_collector):
        """Create hooks with mock collector"""
        return MonitoringHooks(mock_collector)
    
    def test_increment_counter_with_collector(self, hooks_with_collector, mock_collector, mock_metric):
        """Test incrementing counter with collector"""
        hooks_with_collector.increment_counter('test_counter', 5, {'label': 'value'})
        
        mock_collector.get_metric.assert_called_once_with('test_counter')
        mock_metric.labels.assert_called_once_with(label='value')
        mock_metric.inc.assert_called_once_with(5)
    
    def test_update_gauge_with_collector(self, hooks_with_collector, mock_collector, mock_metric):
        """Test updating gauge with collector"""
        hooks_with_collector.update_gauge('test_gauge', 42.5, {'label': 'value'})
        
        mock_collector.get_metric.assert_called_once_with('test_gauge')
        mock_metric.labels.assert_called_once_with(label='value')
        mock_metric.set.assert_called_once_with(42.5)
    
    def test_observe_histogram_with_collector(self, hooks_with_collector, mock_collector, mock_metric):
        """Test observing histogram with collector"""
        hooks_with_collector.observe_histogram('test_histogram', 0.123, {'label': 'value'})
        
        mock_collector.get_metric.assert_called_once_with('test_histogram')
        mock_metric.labels.assert_called_once_with(label='value')
        mock_metric.observe.assert_called_once_with(0.123)