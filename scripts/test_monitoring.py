#!/usr/bin/env python3
"""
Test script for monitoring system integration.

This verifies that the monitoring system is properly integrated and working.
"""

import asyncio
import logging
import sys
from pathlib import Path
import aiohttp

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_prometheus_endpoint():
    """Test that Prometheus metrics endpoint is accessible"""
    logger.info("Testing Prometheus metrics endpoint...")
    
    url = "http://localhost:9090/metrics"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    logger.info(f"✅ Prometheus endpoint is accessible at {url}")
                    
                    # Check for some expected metrics
                    expected_metrics = [
                        "claude_agi_up",
                        "orchestrator_state_transitions_total",
                        "memory_operations_total",
                        "consciousness_thoughts_generated_total"
                    ]
                    
                    found_metrics = []
                    for metric in expected_metrics:
                        if metric in text:
                            found_metrics.append(metric)
                    
                    logger.info(f"Found metrics: {found_metrics}")
                    
                    # Print a sample of the metrics
                    lines = text.split('\n')[:20]
                    logger.info("Sample metrics output:")
                    for line in lines:
                        if line and not line.startswith('#'):
                            logger.info(f"  {line}")
                            
                    return True
                else:
                    logger.error(f"❌ Prometheus endpoint returned status {response.status}")
                    return False
                    
    except aiohttp.ClientError as e:
        logger.error(f"❌ Failed to connect to Prometheus endpoint: {e}")
        logger.info("Make sure the monitoring system is running")
        return False


async def test_health_endpoint():
    """Test that health check endpoint is accessible"""
    logger.info("\nTesting health check endpoint...")
    
    url = "http://localhost:9090/health"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Health endpoint is accessible at {url}")
                    logger.info(f"System status: {data.get('status', 'unknown')}")
                    
                    # Print health check details
                    if 'checks' in data:
                        logger.info("Health checks:")
                        for check_name, check_data in data['checks'].items():
                            status = check_data.get('status', 'unknown')
                            logger.info(f"  {check_name}: {status}")
                            
                    return True
                else:
                    logger.error(f"❌ Health endpoint returned status {response.status}")
                    return False
                    
    except aiohttp.ClientError as e:
        logger.error(f"❌ Failed to connect to health endpoint: {e}")
        return False


async def test_monitoring_integration():
    """Test full monitoring integration with Claude-AGI"""
    logger.info("\nTesting monitoring integration with Claude-AGI...")
    
    from main import ClaudeAGI
    
    try:
        # Create Claude-AGI instance
        app = ClaudeAGI()
        
        # Start the system in a background task
        app_task = asyncio.create_task(app.start())
        
        # Wait for system to initialize
        await asyncio.sleep(5)
        
        # Test endpoints
        prometheus_ok = await test_prometheus_endpoint()
        health_ok = await test_health_endpoint()
        
        # Perform some operations to generate metrics
        if app.orchestrator:
            logger.info("\nPerforming test operations...")
            
            # Send a test message
            from core.event_bus import Message
            test_message = Message(
                source="test",
                target="memory",
                type="store_thought",
                content={
                    "content": "This is a test thought for monitoring",
                    "importance": 7,
                    "stream_type": "primary"
                }
            )
            
            await app.orchestrator.send_message(test_message)
            
            # Wait for processing
            await asyncio.sleep(2)
            
            # Check metrics again
            logger.info("\nChecking metrics after operations...")
            await test_prometheus_endpoint()
        
        # Shutdown
        logger.info("\nShutting down system...")
        await app.shutdown()
        app_task.cancel()
        
        try:
            await app_task
        except asyncio.CancelledError:
            pass
            
        return prometheus_ok and health_ok
        
    except Exception as e:
        logger.error(f"Error during monitoring integration test: {e}", exc_info=True)
        return False


async def main():
    """Main test function"""
    logger.info("Claude-AGI Monitoring System Test")
    logger.info("=" * 50)
    
    # Check if we should run full integration or just endpoint tests
    if "--endpoints-only" in sys.argv:
        # Just test endpoints (assumes system is already running)
        prometheus_ok = await test_prometheus_endpoint()
        health_ok = await test_health_endpoint()
        success = prometheus_ok and health_ok
    else:
        # Run full integration test
        success = await test_monitoring_integration()
    
    if success:
        logger.info("\n✅ All monitoring tests passed!")
    else:
        logger.info("\n❌ Some monitoring tests failed")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")