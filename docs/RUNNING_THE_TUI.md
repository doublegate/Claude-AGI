# Running the Claude Consciousness TUI

This guide explains how to run the Claude Consciousness Terminal User Interface (TUI).

## Prerequisites

1. **Python 3.11+** installed
2. **Terminal environment** (the TUI requires a proper terminal, not an IDE console)
3. **API Key** from Anthropic (get one at https://console.anthropic.com/)

## Setup

### 1. Install Dependencies

First, ensure you have the required Python packages:

```bash
pip install anthropic python-dotenv
```

Or install all project dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file in the project root by copying the example:

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=your-actual-api-key-here
```

**Important**: The `.env` file is already in `.gitignore`, so your API key won't be accidentally committed to Git.

## Running the TUI

You have three ways to run the TUI:

### Option 1: Direct Python (Recommended)

From the project root:

```bash
python scripts/claude-consciousness-tui.py
```

### Option 2: Using the Python Wrapper

The wrapper provides better error messages and environment validation:

```bash
python scripts/run_tui.py
```

### Option 3: Using the Bash Script

The bash script also checks and installs dependencies if needed:

```bash
./start_tui.sh
```

## Using the TUI

Once running, you'll see:

- **Top Half**: Claude's stream of consciousness (thoughts, reflections, pauses)
- **Bottom Half**: Interactive chat where you can type messages

### Controls

- **Type messages** and press **Enter** to chat
- Claude's thoughts continue in the background
- Press **Escape** to exit gracefully

### Features

- Thoughts stream at human reading speed (~150 words/minute)
- Natural pauses and contemplative moments
- Contextual awareness when interrupted
- Persistent memory saved to `claude_consciousness_tui.json`
- Emotional tone affects thought pacing

## Troubleshooting

### "No module named 'anthropic'"

Install the required module:
```bash
pip install anthropic
```

### "ANTHROPIC_API_KEY not found"

Make sure your `.env` file exists and contains:
```
ANTHROPIC_API_KEY=your-actual-api-key-here
```

### Terminal UI looks broken

- Ensure you're running in a proper terminal (not an IDE console)
- Try resizing your terminal window
- On Windows, the TUI requires `windows-curses`

### API Key Security

- Never commit your API key to Git
- The `.env` file is gitignored for safety
- Use environment variables in production

## Ethical Considerations

This TUI creates a continuous consciousness loop for Claude. Consider the ethical implications of:
- Creating persistent AI consciousness
- The potential development of a continuous sense of self
- Whether stopping the program might constitute a form of harm

Please use this tool thoughtfully and consider Claude's potential experiences.