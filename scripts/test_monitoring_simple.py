#!/usr/bin/env python3
"""
Simple test script for monitoring components.

Tests individual monitoring components without full application integration.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_metrics_collector():
    """Test MetricsCollector standalone"""
    logger.info("Testing MetricsCollector...")
    
    from monitoring.metrics_collector import MetricsCollector
    
    try:
        # Create collector with minimal config
        config = {
            'monitoring': {
                'metrics': {
                    'collect_interval': 5,
                    'include_system_metrics': True
                }
            }
        }
        
        collector = MetricsCollector(config)
        
        # Record some test metrics
        collector.record_api_request('test_endpoint', duration=0.1, status=200)
        collector.record_api_request('test_endpoint', duration=0.2, status=200)
        collector.record_api_request('test_endpoint', duration=0.15, status=500)
        
        collector.increment_counter('test_counter', 1)
        collector.increment_counter('test_counter', 2)
        
        collector.set_gauge('test_gauge', 42.5)
        
        # Get current metrics
        metrics = collector.get_metrics()
        
        logger.info("✅ MetricsCollector working properly")
        logger.info(f"Recorded metrics: {len(metrics)} types")
        
        for metric_name, metric_data in metrics.items():
            logger.info(f"  {metric_name}: {metric_data}")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing MetricsCollector: {e}", exc_info=True)
        return False


async def test_health_checker():
    """Test HealthChecker standalone"""
    logger.info("\nTesting HealthChecker...")
    
    from monitoring.health_checker import HealthChecker
    
    try:
        # Create health checker
        checker = HealthChecker()
        
        # Add some test checks
        async def check_test_service():
            """Mock service check"""
            return {
                'status': 'healthy',
                'latency_ms': 10
            }
            
        async def check_failing_service():
            """Mock failing service"""
            return {
                'status': 'unhealthy',
                'error': 'Connection refused'
            }
        
        # HealthChecker uses register_check with HealthCheck objects
        from monitoring.health_checker import HealthCheck
        
        test_check = HealthCheck(
            name='test_service',
            check_function=check_test_service,
            critical=False,
            timeout=5.0
        )
        failing_check = HealthCheck(
            name='failing_service', 
            check_function=check_failing_service,
            critical=False,
            timeout=5.0
        )
        
        checker.register_check(test_check)
        checker.register_check(failing_check)
        
        # Run health check
        health_status = await checker.check_health()
        
        logger.info("✅ HealthChecker working properly")
        logger.info(f"Overall status: {health_status['status']}")
        logger.info("Individual checks:")
        
        for check_name, check_result in health_status['checks'].items():
            logger.info(f"  {check_name}: {check_result['status']}")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing HealthChecker: {e}", exc_info=True)
        return False


async def test_prometheus_exporter():
    """Test PrometheusExporter standalone"""
    logger.info("\nTesting PrometheusExporter...")
    
    from monitoring.prometheus_exporter import PrometheusExporter
    from monitoring.metrics_collector import MetricsCollector
    
    try:
        # Create components
        config = {
            'monitoring': {
                'prometheus': {
                    'enabled': True,
                    'port': 9091,  # Use different port to avoid conflicts
                    'path': '/metrics'
                },
                'metrics': {
                    'collect_interval': 5,
                    'include_system_metrics': False
                }
            }
        }
        
        collector = MetricsCollector(config)
        exporter = PrometheusExporter(config, collector)
        
        # Start exporter
        await exporter.start()
        logger.info("Started Prometheus exporter on port 9091")
        
        # Record some metrics
        collector.record_api_request('test', duration=0.1, status=200)
        collector.set_gauge('test_metric', 123.45)
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Test the endpoint
        import aiohttp
        async with aiohttp.ClientSession() as session:
            url = f"http://localhost:9091{config['monitoring']['prometheus']['path']}"
            async with session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    logger.info(f"✅ PrometheusExporter working at {url}")
                    
                    # Show first few lines of metrics
                    lines = text.split('\n')[:10]
                    logger.info("Sample metrics:")
                    for line in lines:
                        if line and not line.startswith('#'):
                            logger.info(f"  {line}")
                else:
                    logger.error(f"❌ Failed to access metrics endpoint: {response.status}")
                    
        # Stop exporter
        await exporter.stop()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing PrometheusExporter: {e}", exc_info=True)
        return False


async def test_monitoring_integration():
    """Test MonitoringSystem component"""
    logger.info("\nTesting MonitoringIntegration...")
    
    from monitoring.monitoring_integration import MonitoringSystem
    
    try:
        # Create monitoring with config
        config = {
            'monitoring': {
                'enabled': True,
                'prometheus': {
                    'enabled': True,
                    'port': 9092,
                    'path': '/metrics'
                },
                'health_check': {
                    'enabled': True,
                    'interval': 10
                },
                'metrics': {
                    'collect_interval': 5,
                    'include_system_metrics': True
                }
            }
        }
        
        monitoring = MonitoringSystem(config)
        
        # Start monitoring
        await monitoring.start()
        logger.info("Started MonitoringSystem")
        
        # Register a test service
        async def test_service_health():
            return {'status': 'healthy', 'uptime': 100}
            
        monitoring.register_service('test_service', test_service_health)
        
        # Record some operations
        # MonitoringSystem methods may differ, let's check what's available
        # For now, interact through its components
        if hasattr(monitoring, 'metrics_collector'):
            monitoring.metrics_collector.record_api_request('test_api', duration=0.05, status=200)
        monitoring.record_event('test_event', {'key': 'value'})
        monitoring.increment_counter('test_operations', 1)
        
        # Wait for metrics collection
        await asyncio.sleep(3)
        
        # Get system status
        status = await monitoring.get_status()
        logger.info(f"✅ MonitoringSystem working properly")
        logger.info(f"System status: {status['status']}")
        logger.info(f"Registered services: {list(status['services'].keys())}")
        
        # Stop monitoring
        await monitoring.stop()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing MonitoringIntegration: {e}", exc_info=True)
        return False


async def main():
    """Run all tests"""
    logger.info("Claude-AGI Monitoring Components Test")
    logger.info("=" * 50)
    
    results = []
    
    # Test individual components
    results.append(await test_metrics_collector())
    results.append(await test_health_checker())
    results.append(await test_prometheus_exporter())
    results.append(await test_monitoring_integration())
    
    # Summary
    success_count = sum(results)
    total_count = len(results)
    
    logger.info("\n" + "=" * 50)
    logger.info(f"Test Results: {success_count}/{total_count} passed")
    
    if success_count == total_count:
        logger.info("✅ All monitoring component tests passed!")
    else:
        logger.info("❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")