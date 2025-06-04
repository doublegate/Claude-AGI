# Running the Claude-AGI TUI

This guide explains how to run both the basic Claude Consciousness TUI and the enhanced Claude-AGI Terminal User Interface.

## Prerequisites

1. **Python 3.11+** installed
2. **Terminal environment** (the TUI requires a proper terminal, not an IDE console)
   - Minimum size: 80x20 for enhanced TUI, 40x10 for basic TUI
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

### Enhanced Claude-AGI TUI (Recommended)

The enhanced TUI provides multiple panes for consciousness streams, memory, emotional state, and goals:

```bash
python claude-agi.py
```

Or with a specific configuration:

```bash
python claude-agi.py --config configs/development.yaml
```

### Basic Consciousness TUI

For a simpler experience, use the basic consciousness demo:

```bash
python scripts/enhanced_consciousness_tui.py
```

## Using the Enhanced TUI

The enhanced TUI displays multiple panes:

- **Consciousness Pane**: Shows multi-stream thoughts (primary, creative, subconscious, meta)
- **Memory Pane**: Displays recent memories and allows browsing
- **Emotional State**: Visual representation of current emotional state
- **Goals Pane**: Active goals and achievements
- **Chat Pane**: Interactive conversation
- **System Pane**: Status messages and metrics

### Controls

- **Tab**: Switch between panes (active pane highlighted)
- **Arrow Keys**: Scroll up/down in active pane
- **Page Up/Down**: Scroll by page
- **Home/End**: Jump to top/bottom
- **Enter**: Send chat messages
- **ESC**: Exit (press twice to confirm)
- **/command**: Use slash commands (type /help for list)

### Slash Commands

- `/help` - Show available commands
- `/memory` - Memory operations (search, stats, consolidate)
- `/stream` - Control consciousness streams (pause, resume, focus)
- `/emotional` - Set emotional state
- `/goals` - Manage goals
- `/layout` - Switch UI layouts
- `/metrics` - View system metrics
- `/safety` - Check safety framework status

## Troubleshooting

### TUI Screen Goes Gray/Blank

If the TUI displays correctly for a second then goes gray:
- This was a logging issue that has been fixed in the latest version
- Make sure you're using the updated `claude-agi.py`
- Check `logs/claude-agi.log` for any errors

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