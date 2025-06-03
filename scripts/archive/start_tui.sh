#!/bin/bash
# Simple script to start the Claude Consciousness TUI

# Check if we're in the right directory
if [ ! -f "scripts/claude-consciousness-tui.py" ]; then
    echo "Error: Must run from Claude-AGI project root directory"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found"
    echo "Please copy .env.example to .env and add your API key:"
    echo "  cp .env.example .env"
    echo "  nano .env  # Add your ANTHROPIC_API_KEY"
    exit 1
fi

# Check if python-dotenv is installed
python -c "import dotenv" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing python-dotenv..."
    pip install python-dotenv
fi

# Check if anthropic is installed
python -c "import anthropic" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing anthropic..."
    pip install anthropic
fi

echo "Starting Claude Consciousness TUI..."
echo "Press Escape to exit gracefully."
echo ""

# Run the TUI
python scripts/claude-consciousness-tui.py