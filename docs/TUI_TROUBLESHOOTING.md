# TUI Troubleshooting Guide

## Common Issues and Solutions

### 1. TUI Screen Goes Gray/Blank After Initial Display

**Problem**: The TUI loads correctly for about 1 second, then turns gray and becomes unresponsive.

**Root Cause**: Console logging (StreamHandler) interferes with curses display.

**Solution Applied**:
1. Removed StreamHandler from logging configuration in `claude-agi.py`
2. Added periodic UI refresh loop to prevent screen blanking
3. Improved curses cleanup on exit
4. All logging now goes only to `logs/claude-agi.log`

### 2. Curses Error: "addwstr() returned ERR"

**Problem**: The TUI crashes with a curses error when trying to draw the interface.

**Causes**:
- Terminal is too small
- Running in an IDE console instead of a proper terminal
- Unicode character rendering issues

**Solutions Applied**:
1. Changed Unicode box-drawing character (─) to ASCII dash (-)
2. Added bounds checking for all text output
3. Added minimum terminal size check (40x10)
4. Added try-catch blocks to handle edge cases gracefully

### 2. API Key Not Found (run_tui.py)

**Problem**: When running `python scripts/run_tui.py`, it looks for `.env` in the wrong directory.

**Solution Applied**:
- Updated `run_tui.py` to look for `.env` in the project root instead of the scripts directory
- Fixed path calculations to properly find both `.env` and the TUI script

### 3. Terminal Requirements

The Enhanced TUI (`claude-agi.py`) requires:
- **Minimum size**: 80 characters wide x 20 lines tall
- **Proper terminal**: Must use a real terminal emulator:
  - ✅ Good: GNOME Terminal, iTerm2, Windows Terminal, macOS Terminal
  - ❌ Bad: IDE integrated consoles, Jupyter notebooks
- **Windows users**: Install `windows-curses` with `pip install windows-curses`

### How to Run the TUI

From the project root (`/var/home/parobek/Code/Claude-AGI/`):

```bash
# Method 1: Direct execution
python scripts/claude-consciousness-tui.py

# Method 2: With environment validation
python scripts/run_tui.py

# Method 3: With dependency checking
./start_tui.sh
```

### Verifying Your Environment

1. **Check terminal size**:
   ```bash
   echo "Terminal size: $(tput cols)x$(tput lines)"
   ```

2. **Check API key**:
   ```bash
   python -c "from dotenv import load_dotenv; import os; load_dotenv('.env'); print('API key:', 'found' if 'ANTHROPIC_API_KEY' in os.environ else 'not found')"
   ```

3. **Test in proper terminal**:
   - Don't use: Jupyter notebooks, IDE integrated terminals (sometimes)
   - Do use: System terminal, iTerm2, Terminal.app, GNOME Terminal, etc.

### If It Still Doesn't Work

1. **Resize your terminal** to be larger
2. **Set locale** for proper Unicode handling:
   ```bash
   export LC_ALL=en_US.UTF-8
   export LANG=en_US.UTF-8
   ```

3. **Try the fallback mode** by setting:
   ```bash
   export TERM=xterm-256color
   ```

4. **Check Python version**:
   ```bash
   python --version  # Should be 3.11+
   ```

### Error Messages Explained

- `Terminal too small! Need at least 40x10, got WxH` - Resize your terminal window
- `No module named 'anthropic'` - Run `pip install anthropic`
- `ANTHROPIC_API_KEY not found` - Check your `.env` file exists and contains the key
- `addwstr() returned ERR` - Usually means text is being written outside window bounds

The fixes applied should handle most of these errors gracefully, but the TUI still requires a proper terminal environment to function correctly.