#!/usr/bin/env python3
"""
Debug test to verify Anthropic API integration
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.core.ai_integration import ThoughtGenerator

async def test_api_integration():
    """Test if API integration is working"""
    print("Testing Anthropic API integration...")
    
    # Check API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ No ANTHROPIC_API_KEY found in environment")
        return False
    
    print(f"✅ API key found: {api_key[:10]}...")
    
    # Create ThoughtGenerator
    try:
        thought_gen = ThoughtGenerator()
        print(f"✅ ThoughtGenerator created, use_api: {thought_gen.use_api}")
    except Exception as e:
        print(f"❌ Error creating ThoughtGenerator: {e}")
        return False
    
    # Test simple response generation
    try:
        print("\n🔄 Testing generate_response...")
        response = await thought_gen.generate_response(
            user_input="Hello, can you respond?",
            conversation_history=None,
            emotional_state=None
        )
        print(f"✅ API Response received: {response[:100]}...")
        return True
    except Exception as e:
        print(f"❌ API Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        if hasattr(thought_gen, 'close'):
            await thought_gen.close()

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the test
    result = asyncio.run(test_api_integration())
    if result:
        print("\n✅ API integration test PASSED")
        sys.exit(0)
    else:
        print("\n❌ API integration test FAILED")
        sys.exit(1)