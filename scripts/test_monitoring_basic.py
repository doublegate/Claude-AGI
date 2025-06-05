#!/usr/bin/env python3
"""
Basic monitoring test - tests individual components in isolation.
"""

import asyncio
import logging
import sys
from pathlib import Path
import time

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_metrics_basic():
    """Test basic metric recording functionality"""
    logger.info("Testing basic metrics...")
    
    try:
        # Test Counter
        from prometheus_client import Counter
        test_counter = Counter('test_requests_total', 'Test request counter')
        test_counter.inc()
        test_counter.inc(2)
        
        logger.info(f"✅ Counter working: {test_counter._value.get()}")
        
        # Test Gauge
        from prometheus_client import Gauge
        test_gauge = Gauge('test_temperature', 'Test temperature gauge')
        test_gauge.set(23.5)
        
        logger.info(f"✅ Gauge working: {test_gauge._value.get()}")
        
        # Test Histogram
        from prometheus_client import Histogram
        test_histogram = Histogram('test_duration', 'Test duration histogram')
        test_histogram.observe(0.1)
        test_histogram.observe(0.2)
        test_histogram.observe(0.15)
        
        logger.info("✅ Histogram working")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in basic metrics test: {e}")
        return False


def test_system_metrics():
    """Test system metrics collection"""
    logger.info("\nTesting system metrics...")
    
    try:
        import psutil
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        logger.info(f"CPU Usage: {cpu_percent}%")
        
        # Memory usage
        memory = psutil.virtual_memory()
        logger.info(f"Memory Usage: {memory.percent}% ({memory.used / 1024**3:.2f} GB used)")
        
        # Disk usage
        disk = psutil.disk_usage('/')
        logger.info(f"Disk Usage: {disk.percent}% ({disk.used / 1024**3:.2f} GB used)")
        
        logger.info("✅ System metrics working")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in system metrics test: {e}")
        return False


async def test_health_check_basic():
    """Test basic health check functionality"""
    logger.info("\nTesting basic health checks...")
    
    try:
        # Simple health check structure
        health_status = {
            'status': 'healthy',
            'timestamp': time.time(),
            'checks': {
                'database': {'status': 'healthy', 'latency_ms': 5},
                'redis': {'status': 'healthy', 'latency_ms': 2},
                'api': {'status': 'degraded', 'error': 'High latency'}
            }
        }
        
        # Determine overall status
        all_healthy = all(
            check['status'] == 'healthy' 
            for check in health_status['checks'].values()
        )
        
        if all_healthy:
            logger.info("✅ All services healthy")
        else:
            logger.info("⚠️  Some services degraded")
            
        for service, status in health_status['checks'].items():
            logger.info(f"  {service}: {status['status']}")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in health check test: {e}")
        return False


async def test_prometheus_format():
    """Test Prometheus metric formatting"""
    logger.info("\nTesting Prometheus format...")
    
    try:
        from prometheus_client import Counter, Gauge, Histogram, generate_latest
        from prometheus_client.registry import CollectorRegistry
        
        # Create a new registry to avoid conflicts
        registry = CollectorRegistry()
        
        # Create metrics with the registry
        requests = Counter('app_requests_total', 'Total requests', registry=registry)
        temperature = Gauge('app_temperature', 'Current temperature', registry=registry)
        duration = Histogram('app_duration_seconds', 'Request duration', registry=registry)
        
        # Record some data
        requests.inc()
        requests.inc()
        temperature.set(25.3)
        duration.observe(0.05)
        duration.observe(0.1)
        
        # Generate Prometheus format
        metrics_output = generate_latest(registry).decode('utf-8')
        
        logger.info("Prometheus format output:")
        for line in metrics_output.split('\n')[:10]:
            if line:
                logger.info(f"  {line}")
                
        logger.info("✅ Prometheus formatting working")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in Prometheus format test: {e}")
        return False


async def test_monitoring_hooks():
    """Test monitoring hooks integration"""
    logger.info("\nTesting monitoring hooks...")
    
    try:
        from core.monitoring_hooks import MonitoringHooks
        
        # Create hooks instance
        hooks = MonitoringHooks()
        
        # Test recording metrics
        hooks.increment_counter('service_starts', labels={'service': 'test_service'})
        hooks.observe_histogram('api_request_duration', 0.05, labels={'endpoint': '/test', 'status': '200'})
        hooks.increment_counter('memory_operations', labels={'type': 'store', 'success': 'true'})
        
        # Test gauge
        hooks.update_gauge('active_connections', 5)
        
        # Test timing context
        with hooks.time_operation('test_operation'):
            await asyncio.sleep(0.01)
        
        logger.info("✅ Monitoring hooks working")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in monitoring hooks test: {e}")
        return False


async def main():
    """Run all tests"""
    logger.info("Claude-AGI Basic Monitoring Test")
    logger.info("=" * 50)
    
    results = []
    
    # Run tests
    results.append(test_metrics_basic())
    results.append(test_system_metrics())
    results.append(await test_health_check_basic())
    results.append(await test_prometheus_format())
    results.append(await test_monitoring_hooks())
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    logger.info("\n" + "=" * 50)
    logger.info(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("✅ All tests passed!")
    else:
        logger.info("❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nTest interrupted")