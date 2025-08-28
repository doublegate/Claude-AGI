#!/usr/bin/env python3
"""
Test script for real-time information capabilities
Tests both system time and weather information retrieval
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.web.explorer import WebExplorer
from src.core.orchestrator import AGIOrchestrator


async def test_system_time():
    """Test system time retrieval"""
    print("Testing system time retrieval...")
    
    orchestrator = AGIOrchestrator()
    explorer = WebExplorer(orchestrator)
    
    try:
        time_data = await explorer.get_system_time()
        if time_data.get('success'):
            print(f"✅ System Time: {time_data['current_time']} ({time_data['day_of_week']})")
            print(f"   Date: {time_data['date']}")
            print(f"   Time: {time_data['time']}")
            print(f"   Timezone: {time_data['timezone']}")
        else:
            print(f"❌ Time retrieval failed: {time_data.get('error')}")
    except Exception as e:
        print(f"❌ Exception during time test: {e}")
    finally:
        await explorer.cleanup()


async def test_weather_info():
    """Test weather information retrieval"""
    print("\nTesting weather information retrieval...")
    
    orchestrator = AGIOrchestrator()
    explorer = WebExplorer(orchestrator)
    
    # Test with a location
    test_location = "New York"
    
    try:
        weather_data = await explorer.get_weather_info(test_location)
        if weather_data.get('success'):
            print(f"✅ Weather for {weather_data['location']}:")
            print(f"   Temperature: {weather_data['temperature']}°C (feels like {weather_data['feels_like']}°C)")
            print(f"   Conditions: {weather_data['description']}")
            print(f"   Humidity: {weather_data['humidity']}%")
            print(f"   Wind: {weather_data['wind_speed']} m/s")
        else:
            error = weather_data.get('error')
            if 'API key not configured' in error:
                print(f"⚠️  Weather API key not configured: {error}")
                print("   Set OPENWEATHERMAP_API_KEY environment variable to test weather functionality")
            else:
                print(f"❌ Weather retrieval failed: {error}")
    except Exception as e:
        print(f"❌ Exception during weather test: {e}")
    finally:
        await explorer.cleanup()


async def test_query_preprocessing():
    """Test query preprocessing logic"""
    print("\nTesting query preprocessing logic...")
    
    # Import the main class to test query classification
    import importlib.util
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    claude_agi_path = os.path.join(project_root, "claude-agi.py")
    spec = importlib.util.spec_from_file_location("claude_agi", claude_agi_path)
    claude_agi = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(claude_agi)
    ClaudeAGI = claude_agi.ClaudeAGI
    
    # Create a minimal test instance
    agi = ClaudeAGI()
    
    # Test time queries
    time_queries = [
        "What time is it?",
        "What's the current time?",
        "What date is it today?",
        "What day of the week is it?"
    ]
    
    print("Time query detection:")
    for query in time_queries:
        result = await agi._check_system_information_query(query)
        if result:
            print(f"✅ '{query}' -> Detected as time query")
        else:
            print(f"❌ '{query}' -> NOT detected")
    
    # Test weather queries
    weather_queries = [
        "What's the weather in Paris?",
        "Tell me the temperature in London",
        "Is it raining in Seattle?",
        "Weather forecast for Tokyo"
    ]
    
    print("\nWeather query detection:")
    for query in weather_queries:
        result = await agi._check_system_information_query(query)
        if result and "weather" in result.lower():
            print(f"✅ '{query}' -> Detected as weather query")
        else:
            print(f"❌ '{query}' -> NOT detected or no location")
    
    # Test non-system queries (should return None)
    normal_queries = [
        "How are you doing?",
        "Tell me about consciousness",
        "What is the meaning of life?"
    ]
    
    print("\nNormal query handling:")
    for query in normal_queries:
        result = await agi._check_system_information_query(query)
        if result is None:
            print(f"✅ '{query}' -> Correctly passed to AI")
        else:
            print(f"❌ '{query}' -> Incorrectly intercepted")


async def main():
    """Run all tests"""
    print("🧪 Testing Real-Time Information Capabilities")
    print("=" * 50)
    
    await test_system_time()
    await test_weather_info() 
    await test_query_preprocessing()
    
    print("\n" + "=" * 50)
    print("✅ Real-time information capability testing complete!")
    print("\nTo test with weather API:")
    print("1. Get a free API key from https://openweathermap.org/api")
    print("2. Set environment variable: export OPENWEATHERMAP_API_KEY=your_key_here")
    print("3. Run the TUI: python claude-agi.py")
    print("4. Try queries like: 'What's the weather in your city?' or 'What time is it?'")


if __name__ == "__main__":
    asyncio.run(main())