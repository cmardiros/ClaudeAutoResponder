# Claude Code Auto Responder

*Written by Claude for Claude*

Tired of Claude Code waiting for your confirmation? This tool automatically responds to ALL Claude prompts across ALL your terminal windows - instantly.

```
╭─────────────────────────────────────────────────────────────────────────────────────╮
│ Edit file                                                                           │
│ ╭─────────────────────────────────────────────────────────────────────────────────╮ │
│ │ SharedCode/Additions.swift                                                      │ │
│ │                                                                                 │ │
│ │ 200    }                                                                        │ │
│ │ 201                                                                             │ │
│ │ 223      // Also check for items that need to be re-linked after updates        │ │
│ │ 224      var itemsNeedingRelinking = [(updated: T, shouldBeLinkedTo: T)]()      │ │
│ │ 225                                                                             │ │
│ │ ...                                                                             │ │
│ │ 260              } else {                                                       │ │
│ ╰─────────────────────────────────────────────────────────────────────────────────╯ │
│ Do you want to make this edit to Additions.swift?                                   │
│ ❯ 1. Yes                                                                            │
│   2. Yes, and don't ask again this session (shift+tab)                              │
│   3. No, and tell Claude what to do differently (esc)                               │
│                                                                                     │
╰─────────────────────────────────────────────────────────────────────────────────────╯
```

This tool automatically responds to Claude Code confirmation prompts, perfect for when you want to leave Claude some autonomous work while you step away. It monitors ALL your terminal windows by default and responds instantly (0 second delay), so Claude continues working without any interruption.

## Key Features

- **Instant Response**: 0 second delay by default - Claude never waits
- **Multi-Window Monitoring**: Watches ALL terminal windows simultaneously
- **Auto-Focus Switching**: Automatically switches to windows needing response
- **Focus Restoration**: Returns you to your original app after responding
- **Memory Safe**: Uses subprocess isolation - no memory leaks, runs forever
- **Escape to Cancel**: Press Escape during countdown to skip a response

## How it works

This tool monitors your terminals with [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) running and automatically:
- Detects Claude Code confirmation prompts across ALL windows
- Instantly responds with **"Yes, and don't ask again"** when available
- Falls back to **"Yes"** for simple confirmations
- Switches window focus only when needed, then restores it
- Uses subprocess-based AppleScript for zero memory leaks

Perfect for:
- Running multiple Claude sessions simultaneously
- Leaving Claude to work autonomously while you do other things
- Never having to manually confirm file operations again

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
- **Python**: 3.9 or later (required by pyobjc)
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
# Run with default settings (monitors all windows, 0 second delay)
python3 claude_auto_responder.py

# Monitor only the focused window
python3 claude_auto_responder.py --single

# Add a delay before responding (useful for reading the prompt)
python3 claude_auto_responder.py --delay 3

# Enable debug mode
python3 claude_auto_responder.py --debug

# Override tools via command line
python3 claude_auto_responder.py --tools "Read file,Edit file"

# Use custom tools file
python3 claude_auto_responder.py --tools-file my_tools.txt

# Combine options
python3 claude_auto_responder.py --single --delay 5 --debug
```

## How it Works

1. **Python monitors your terminal windows** using subprocess-based AppleScript execution
2. **Detects Claude prompts** with whitelisted tools using pattern matching
3. **Shows a countdown** giving you time to cancel (Press Escape) - default 0 seconds
4. **Swift utility sends keystrokes** using Core Graphics for reliable input
5. **Automatically selects the best option** ("Yes, and don't ask again" when available)
6. **Switches focus when needed** and restores original focus after responding

The tool only responds to prompts with Claude's specific box format (╭─╮│╰─╯) to avoid false positives.

### Multi-Window Monitoring (Default Behavior)

By default, the tool monitors ALL terminal windows simultaneously:

1. **Scans all terminal windows** every 0.5 seconds
2. **Detects prompts in any window** even if it's not currently focused
3. **Automatically switches focus** to the window with the prompt
4. **Sends the response** instantly (0 second default delay)
5. **Restores original focus** to whatever app you were using

#### Auto-Focus Behavior

The auto-focus system is designed to be seamless and non-disruptive:

- **Smart Focus Detection**: Captures your current focus (any app, not just terminal) right before switching
- **Temporary Window Switch**: Only switches to the terminal window that needs a response
- **Universal Focus Restoration**: Returns focus to your original app after responding, whether it was:
  - Another terminal window
  - A text editor (VS Code, Xcode, etc.)
  - A web browser
  - Any other macOS application
- **Memory Optimized**: Uses efficient AppleScript calls and aggressive memory cleanup to prevent growth
- **Escape Override**: Press Escape during countdown to cancel and restore focus immediately

This means you can be working in any application while multiple Claude Code sessions run in the background. When a prompt appears, the tool will briefly switch to handle it, then return you to exactly where you were working.

#### Example Workflow

```bash
# Start monitoring all terminal windows
python3 claude_auto_responder.py --all

# Now you can:
# 1. Work in VS Code while Claude processes files in Terminal window 1
# 2. Have another Claude session debugging in iTerm2 window 2  
# 3. Browse documentation in Safari
# 4. When any Claude session needs confirmation, the tool will:
#    - Detect the prompt in the background
#    - Show countdown notification
#    - Switch to that terminal window
#    - Send the response
#    - Return focus to your VS Code/Safari/etc.
```

This is perfect when you have multiple Claude Code sessions running in different terminal windows and want to monitor them all without manually switching between them.

## Architecture

This is a hybrid Python/Swift application with subprocess isolation:
- **Python (`claude_auto_responder.py`)**: Handles monitoring, detection, and logic
- **Swift (`send_keys.swift`)**: Handles reliable keystroke sending using Core Graphics
- **Subprocess AppleScript**: Terminal text reading via `osascript` (zero memory leaks)
- **No pyobjc NSAppleScript**: All AppleScript runs in isolated subprocesses that free memory on exit

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

## Contributing

### Reporting Issues

When reporting bugs or issues, please use our GitHub issue template to provide complete technical context. This helps us debug and resolve problems quickly.

**Before submitting an issue:**
1. Check if it's already reported in [existing issues](https://github.com/yourusername/ClaudeAutoResponder/issues)
2. Test with `--debug` flag to gather additional information
3. Include your exact environment details (macOS version, terminal app, Python/Swift versions)

**Common troubleshooting:**
- Ensure Swift is available: `swift --version`
- Verify Python dependencies: `pip show pyobjc-framework-Cocoa`
- Test with single window first: `python3 claude_auto_responder.py --single --debug`

### Issue Template

Our bug report template automatically collects:
- Complete environment context (macOS, Python, Swift, terminal app)
- Exact reproduction steps with command lines
- Debug output and system state
- Clear verification criteria for fixes

This ensures we can quickly reproduce and resolve issues.

## License

MIT - Use freely!
