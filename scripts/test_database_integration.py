#!/usr/bin/env python3
"""
Test Database Integration
========================

This script tests the database connections and memory manager integration.
"""

import asyncio
import sys
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database.connections import DatabaseManager, DatabaseConfig
from memory.manager import MemoryManager
from database.models import StreamType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_connections():
    """Test basic database connections"""
    print("\n=== Testing Database Connections ===")
    
    db_manager = DatabaseManager()
    
    try:
        await db_manager.initialize()
        print("✓ Database connections initialized")
        
        # Test Redis
        await db_manager.set_working_memory("test_key", "test_value")
        value = await db_manager.get_working_memory("test_key")
        assert value == "test_value", "Redis test failed"
        print("✓ Redis connection working")
        
        # Test PostgreSQL
        memory_id = await db_manager.store_memory({
            'memory_type': 'episodic',
            'content': 'Test memory for database integration',
            'importance': 0.8
        })
        print(f"✓ PostgreSQL connection working (stored memory ID: {memory_id})")
        
        # Test FAISS
        if db_manager.faiss_index:
            print(f"✓ FAISS index initialized (dimension: {db_manager.config.faiss_dimension})")
        
        await db_manager.close()
        return True
        
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

async def test_memory_manager_integration():
    """Test memory manager with database integration"""
    print("\n=== Testing Memory Manager Integration ===")
    
    memory_manager = MemoryManager()
    
    try:
        # Initialize with database
        await memory_manager.initialize(use_database=True)
        print("✓ Memory manager initialized with database")
        
        # Test storing thoughts
        thoughts = [
            {
                'content': 'I am testing my database integration capabilities',
                'stream_type': StreamType.PRIMARY,
                'emotional_tone': 'excited',
                'importance': 8
            },
            {
                'content': 'This is a background process monitoring the system',
                'stream_type': StreamType.SUBCONSCIOUS,
                'emotional_tone': 'neutral',
                'importance': 5
            },
            {
                'content': 'I feel confident about this integration working properly',
                'stream_type': StreamType.EMOTIONAL,
                'emotional_tone': 'confident',
                'importance': 7
            }
        ]
        
        thought_ids = []
        for thought in thoughts:
            thought_id = await memory_manager.store_thought(thought)
            thought_ids.append(thought_id)
            print(f"✓ Stored thought: {thought_id}")
        
        # Test recall
        recent_thoughts = await memory_manager.recall_recent(5)
        print(f"✓ Recalled {len(recent_thoughts)} recent thoughts")
        
        # Test context
        await memory_manager.update_context("test_mode", True)
        context_value = await memory_manager.get_context("test_mode")
        assert context_value == True, "Context test failed"
        print("✓ Context storage working")
        
        # Test similarity search (if embedder is available)
        if memory_manager.embedder:
            similar = await memory_manager.recall_similar("database integration", k=3)
            print(f"✓ Similarity search returned {len(similar)} results")
        
        # Close connections
        await memory_manager.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Memory manager integration test failed: {e}")
        return False

async def test_fallback_mode():
    """Test that memory manager works without database"""
    print("\n=== Testing Fallback Mode ===")
    
    memory_manager = MemoryManager()
    
    try:
        # Initialize without database
        await memory_manager.initialize(use_database=False)
        print("✓ Memory manager initialized in fallback mode")
        
        # Test basic operations
        thought_id = await memory_manager.store_thought({
            'content': 'Testing fallback mode',
            'importance': 5
        })
        print(f"✓ Stored thought in memory: {thought_id}")
        
        recent = await memory_manager.recall_recent(1)
        assert len(recent) == 1, "Fallback recall failed"
        print("✓ Fallback mode working correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"Fallback mode test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("Claude-AGI Database Integration Tests")
    print("=" * 50)
    
    # Test fallback mode first (always works)
    fallback_ok = await test_fallback_mode()
    
    # Test database connections
    db_ok = await test_database_connections()
    
    # Test full integration if databases are available
    integration_ok = False
    if db_ok:
        integration_ok = await test_memory_manager_integration()
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"  Fallback Mode: {'✓ Passed' if fallback_ok else '✗ Failed'}")
    print(f"  Database Connections: {'✓ Passed' if db_ok else '✗ Failed'}")
    print(f"  Memory Integration: {'✓ Passed' if integration_ok else '✗ Failed'}")
    
    if not db_ok:
        print("\n⚠ Database connections failed. Please ensure:")
        print("  1. PostgreSQL and Redis are installed and running")
        print("  2. Run: python scripts/setup/setup_databases.py")
        print("  3. Check your .env file has correct database URLs")
    
    return all([fallback_ok, db_ok, integration_ok])

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)