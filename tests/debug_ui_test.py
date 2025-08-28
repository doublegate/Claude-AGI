#!/usr/bin/env python3
"""
Debug test to verify UI updates from async tasks
"""

import asyncio
import curses
import logging

# Disable logging for cleaner test output
logging.disable(logging.CRITICAL)

class SimpleUITest:
    def __init__(self):
        self.running = True
        self.messages = []
        self.needs_update = False
        
    def add_message(self, msg):
        """Add message to display"""
        self.messages.append(msg)
        self.needs_update = True
        print(f"DEBUG: Message added: {msg}, needs_update: {self.needs_update}")
        
    async def simulate_async_response(self):
        """Simulate async response generation like handle_user_message"""
        print("DEBUG: Starting async task...")
        await asyncio.sleep(0.1)  # Simulate API call
        response = "AI: This is a test response from async task"
        self.add_message(response)
        print("DEBUG: Async task completed")
        
    async def main_loop(self, stdscr):
        """Simplified main loop like the TUI app"""
        stdscr.clear()
        stdscr.addstr(0, 0, "Simple UI Test - Press 'q' to quit, 't' to test async")
        stdscr.refresh()
        
        # Set non-blocking input
        stdscr.nodelay(True)
        
        line_count = 2
        
        while self.running:
            try:
                # Check for input
                ch = stdscr.getch()
                if ch == ord('q'):
                    self.running = False
                elif ch == ord('t'):
                    # Trigger async task
                    print("DEBUG: User pressed 't', creating async task")
                    asyncio.create_task(self.simulate_async_response())
                
                # Check for UI updates
                if self.needs_update:
                    print("DEBUG: Processing UI update")
                    # Display all messages
                    for i, msg in enumerate(self.messages):
                        if line_count + i < curses.LINES - 1:
                            stdscr.addstr(line_count + i, 0, msg[:curses.COLS-1])
                    
                    stdscr.refresh()
                    self.needs_update = False
                    print("DEBUG: UI update completed")
                
                await asyncio.sleep(0.1)
                
            except curses.error:
                pass
            except Exception as e:
                stdscr.addstr(1, 0, f"Error: {e}")
                stdscr.refresh()
                await asyncio.sleep(1)

def run_test(stdscr):
    """Run the test"""
    test = SimpleUITest()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(test.main_loop(stdscr))
    finally:
        loop.close()

if __name__ == "__main__":
    print("Starting simple UI test...")
    print("This will test if async tasks can update the UI properly")
    print("Press Ctrl+C to exit if needed")
    
    try:
        curses.wrapper(run_test)
        print("Test completed successfully")
    except KeyboardInterrupt:
        print("\nTest interrupted")
    except Exception as e:
        print(f"Test error: {e}")