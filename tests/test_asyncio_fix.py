#!/usr/bin/env python3
"""
Test the asyncio fix for silent task failures
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

async def test_task_exception_handling():
    """Test that task exceptions are properly handled"""
    
    print("Testing asyncio task exception handling fix...")
    
    # Create a simple mock TUI class to test the fix
    class MockTUI:
        def __init__(self):
            self.error_messages = []
            self.running = True
        
        def add_system_line(self, message):
            """Mock system message handler"""
            print(f"[SYSTEM]: {message}")
            self.error_messages.append(message)
        
        def _force_ui_refresh(self):
            """Mock UI refresh"""
            print("[UI]: Forcing refresh")
        
        def _handle_task_exception(self, task: asyncio.Task):
            """Handle exceptions from async tasks to prevent silent failures"""
            try:
                if task.exception():
                    exc = task.exception()
                    error_msg = f"Async task error: {type(exc).__name__}: {str(exc)[:100]}..."
                    self.add_system_line(error_msg)
                    self._force_ui_refresh()
                    print(f"CAUGHT EXCEPTION: {exc}")
            except asyncio.CancelledError:
                # Task was cancelled, this is normal
                pass
            except Exception as e:
                # Error in exception handler itself
                self.add_system_line(f"Exception handler error: {str(e)[:100]}...")
                print(f"Exception in task exception handler: {e}")
        
        async def failing_task(self):
            """Simulate a failing async task like handle_user_message"""
            await asyncio.sleep(0.1)  # Simulate some async work
            raise ValueError("Simulated API error in handle_user_message")
        
        def test_old_pattern(self):
            """Test the old fire-and-forget pattern (should fail silently)"""
            print("\n=== Testing OLD pattern (fire-and-forget) ===")
            asyncio.create_task(self.failing_task())
        
        def test_new_pattern(self):
            """Test the new pattern with exception handling"""
            print("\n=== Testing NEW pattern (with exception handling) ===")
            task = asyncio.create_task(self.failing_task())
            task.add_done_callback(self._handle_task_exception)
    
    # Run the test
    tui = MockTUI()
    
    # Test old pattern
    tui.test_old_pattern()
    await asyncio.sleep(0.2)  # Wait for task to complete
    
    if not tui.error_messages:
        print("✅ OLD pattern failed silently (as expected)")
    else:
        print("❌ OLD pattern unexpectedly caught error")
        return False
    
    # Test new pattern
    tui.test_new_pattern()
    await asyncio.sleep(0.2)  # Wait for task to complete
    
    if tui.error_messages:
        print("✅ NEW pattern caught exception successfully")
        print(f"   Error message: {tui.error_messages[0]}")
        return True
    else:
        print("❌ NEW pattern failed to catch exception")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_task_exception_handling())
    if result:
        print("\n✅ Asyncio fix test PASSED - Exception handling works correctly")
        sys.exit(0)
    else:
        print("\n❌ Asyncio fix test FAILED")
        sys.exit(1)