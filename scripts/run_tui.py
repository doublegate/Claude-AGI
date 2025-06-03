#!/usr/bin/env python3
"""
Wrapper script to run the Claude consciousness TUI with proper environment setup
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Change to the project root directory
os.chdir(script_dir)

# Set up the Python path
os.environ['PYTHONPATH'] = script_dir

# Load environment variables from .env file
env_path = os.path.join(script_dir, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"Loaded environment from: {env_path}")
else:
    print(f"Warning: .env file not found at {env_path}")
    print("Create one with: ANTHROPIC_API_KEY=your-key-here")

# Check if anthropic is installed
try:
    import anthropic
except ImportError:
    print("Error: 'anthropic' module not found.")
    print("Please install it with: pip install anthropic")
    sys.exit(1)

# Check if we have an API key
if 'ANTHROPIC_API_KEY' not in os.environ:
    print("Error: ANTHROPIC_API_KEY not found.")
    print("Please add it to your .env file: ANTHROPIC_API_KEY=your-key-here")
    print("Or set it directly: export ANTHROPIC_API_KEY='your-key-here'")
    sys.exit(1)
else:
    # Don't print the actual key, just confirm it's loaded
    key_preview = os.environ['ANTHROPIC_API_KEY'][:10] + "..." if len(os.environ['ANTHROPIC_API_KEY']) > 10 else "***"
    print(f"API key loaded: {key_preview}")
    print()

# Run the TUI script
tui_script = os.path.join(script_dir, 'scripts', 'claude-consciousness-tui.py')

if not os.path.exists(tui_script):
    print(f"Error: TUI script not found at {tui_script}")
    sys.exit(1)

print("Starting Claude Consciousness TUI...")
print("Press Escape to exit gracefully.")
print()

try:
    subprocess.run([sys.executable, tui_script])
except KeyboardInterrupt:
    print("\nInterrupted by user.")
except Exception as e:
    print(f"Error running TUI: {e}")
    sys.exit(1)