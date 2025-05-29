# Claude Code Auto Responder

*Written by Claude for Claude*

Tired of returning to the terminal only to find Claude Code was waiting for confirmation? No more.

This tool automatically responds to Claude Code confirmation prompts, perfect for when you want to leave Claude some autonomous work while you step away. Just keep your terminal as the focused window, and Claude will continue working without interruption.

## How it works

This tool monitors your terminal with [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) running and automatically:
- Detects Claude Code confirmation prompts
- Chooses **Yes, and don't ask again** when available
- Falls back to **Yes** for simple confirmations
- Shows a countdown before responding (so you can cancel if needed)
- Uses a Swift utility for reliable keystroke sending

Perfect for those times when you:
- Give Claude a complex task and want to grab coffee
- Need to step away but want Claude to keep working
- Don't want to babysit the terminal for every file read/edit confirmation

## Installation

### Quick Start

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/ClaudeAutoResponder
   cd ClaudeAutoResponder
   ```

2. Install Python dependencies:
   ```bash
   python3 setup.py
   ```

3. Run the tool:
   ```bash
   python3 claude_auto_responder.py
   ```

### Manual Installation

If the setup script doesn't work, install dependencies manually:

```bash
pip3 install --user pyobjc-framework-Cocoa
```

## Requirements

- **macOS**: 10.15 or later (for Swift support)
- **Python**: 3.7 or later
- **Swift**: Built into macOS (no installation needed)
- **Terminal**: One of the supported terminal apps

No accessibility permissions required! The tool uses a Swift utility for reliable keystroke sending without permission hassles.

## Configuration

The tool uses whitelisted tools from `whitelisted_tools.txt` by default. Edit this file to customize which Claude tools will trigger auto-response:

```
Read file
Edit file
Bash command
Write
MultiEdit
Grep
Glob
LS
WebFetch
WebSearch
```

## Command Line Options

```bash
# Run with default settings (5 second delay)
python3 claude_auto_responder.py

# Override timeout
python3 claude_auto_responder.py --delay 3

# Enable debug mode
python3 claude_auto_responder.py --debug

# Override tools via command line
python3 claude_auto_responder.py --tools "Read file,Edit file"

# Use custom tools file
python3 claude_auto_responder.py --tools-file my_tools.txt

# Combine options
python3 claude_auto_responder.py --delay 3 --debug
```

## How it Works

1. **Python monitors your terminal** when it's in focus using AppleScript
2. **Detects Claude prompts** with whitelisted tools using pattern matching
3. **Shows a countdown** giving you time to cancel (Press Ctrl+C)
4. **Swift utility sends keystrokes** using Core Graphics for reliable input
5. **Automatically selects the best option** ("Yes, and don't ask again" when available)
6. **Cancels if focus is lost** or the prompt disappears

The tool only responds to prompts with Claude's specific box format (╭─╮│╰─╯) to avoid false positives.

## Architecture

This is a hybrid Python/Swift application:
- **Python (`claude_auto_responder.py`)**: Handles monitoring, detection, and logic
- **Swift (`send_keys.swift`)**: Handles reliable keystroke sending using Core Graphics
- **AppleScript**: Used for terminal text reading (built into macOS)

### Running Tests

```bash
python3 run_tests.py
```

## Supported Terminals

- Terminal
- iTerm2
- Warp
- Hyper
- WezTerm
- Kitty
- Alacritty
- Tabby
- Termius
- Ghostty

## Swift Utility

The `send_keys.swift` utility handles keystroke sending using Core Graphics:

```swift
// Sends the "2" key for selecting option 2
swift send_keys.swift 2

// Sends down arrow key (alternative method)  
swift send_keys.swift down

// Sends enter key to confirm selection
swift send_keys.swift enter
```

This approach provides reliable keystroke delivery without requiring accessibility permissions for most users.

## License

MIT - Use freely!