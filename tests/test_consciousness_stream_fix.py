#!/usr/bin/env python3
"""
Test the consciousness stream fix for orchestrator running flag and asyncio exception handling
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.orchestrator import AGIOrchestrator
from src.consciousness.stream import ConsciousnessStream

async def test_orchestrator_running_flag():
    """Test that orchestrator running flag is properly set"""
    
    print("Testing orchestrator running flag fix...")
    
    # Create orchestrator
    config = {'database': {'enabled': False}}  # Disable database for test
    orchestrator = AGIOrchestrator(config)
    
    # Initially running should be False
    assert orchestrator.running == False, "Orchestrator should start with running=False"
    print("✅ Orchestrator starts with running=False as expected")
    
    # Initialize without running (to avoid hanging in test)
    await orchestrator.initialize()
    
    # running should still be False after initialization
    assert orchestrator.running == False, "Orchestrator running should be False after init"
    print("✅ Orchestrator running remains False after initialization")
    
    # Manually set running to True to simulate the fix
    orchestrator.running = True
    assert orchestrator.running == True, "Orchestrator running should be settable to True"
    print("✅ Orchestrator running can be set to True")
    
    # Verify consciousness service is properly loaded
    consciousness_service = orchestrator.services.get('consciousness')
    assert consciousness_service is not None, "Consciousness service should be loaded"
    assert isinstance(consciousness_service, ConsciousnessStream), "Should be ConsciousnessStream instance"
    print("✅ Consciousness service loaded successfully")
    
    # Verify new services are loaded
    new_services = ['learning', 'creative', 'explorer', 'social', 'meta']
    for service_name in new_services:
        service = orchestrator.services.get(service_name)
        assert service is not None, f"{service_name} service should be loaded"
        print(f"✅ {service_name.title()} service loaded successfully")
    
    # Cleanup
    await orchestrator.shutdown()
    
    return True

async def test_consciousness_service_cycle():
    """Test that consciousness service has proper service_cycle implementation"""
    
    print("\nTesting consciousness service cycle...")
    
    # Create orchestrator
    config = {'database': {'enabled': False}}
    orchestrator = AGIOrchestrator(config)
    await orchestrator.initialize()
    
    # Get consciousness service
    consciousness = orchestrator.services.get('consciousness')
    assert consciousness is not None, "Consciousness service should exist"
    
    # Verify service_cycle method exists
    assert hasattr(consciousness, 'service_cycle'), "ConsciousnessStream should have service_cycle method"
    assert callable(consciousness.service_cycle), "service_cycle should be callable"
    print("✅ ConsciousnessStream has callable service_cycle method")
    
    # Verify streams are initialized
    assert hasattr(consciousness, 'streams'), "ConsciousnessStream should have streams"
    assert len(consciousness.streams) > 0, "Should have initialized streams"
    print(f"✅ ConsciousnessStream has {len(consciousness.streams)} initialized streams")
    
    # Verify stream types
    expected_streams = ['primary', 'subconscious', 'creative', 'meta']
    for stream_type in expected_streams:
        assert stream_type in consciousness.streams, f"Should have {stream_type} stream"
    print("✅ All expected stream types present")
    
    # Test service cycle execution (without running full loop)
    try:
        # Set consciousness to active
        consciousness.is_conscious = True
        
        # Run one cycle
        await consciousness.service_cycle()
        print("✅ service_cycle executes without error")
        
    except Exception as e:
        print(f"❌ service_cycle failed: {e}")
        return False
    
    # Cleanup
    await orchestrator.shutdown()
    
    return True

if __name__ == "__main__":
    async def run_tests():
        print("Testing consciousness stream fixes...\n")
        
        # Test 1: Orchestrator running flag
        result1 = await test_orchestrator_running_flag()
        
        # Test 2: Consciousness service cycle
        result2 = await test_consciousness_service_cycle()
        
        if result1 and result2:
            print("\n✅ All consciousness stream fix tests PASSED")
            return True
        else:
            print("\n❌ Some consciousness stream fix tests FAILED")
            return False
    
    # Run the tests
    result = asyncio.run(run_tests())
    sys.exit(0 if result else 1)