# ClaudeAutoResponder - Implementation Guide

## 🚀 Quick Start Strategy

### Minimal Setup
**Fastest path to get running:**
```bash
# 1. Clone and navigate
git clone https://github.com/yourusername/ClaudeAutoResponder
cd ClaudeAutoResponder

# 2. Auto-setup (handles dependencies)
python3 setup.py

# 3. Start monitoring
python3 claude_auto_responder.py
```

### First Win
**Simplest working example:**
```bash
# Start with default settings - monitors all windows, responds instantly
python3 claude_auto_responder.py

# Then in any terminal window, run Claude Code
# Watch as prompts get automatically answered with "Yes, and don't ask again"
```

### Common Pitfalls
- **Python Version**: Requires Python 3.9+ (setup.py will check this)
- **macOS Only**: Currently only supports macOS - will exit gracefully on other platforms
- **Swift Missing**: Tool will monitor but keystrokes will fail without Swift (built into macOS)
- **No Accessibility**: Unlike other automation tools, this requires NO accessibility permissions

### Best Practices
- **Start Simple**: Begin with `--delay 3` to see what's happening
- **Use Debug Mode**: Add `--debug` to understand detection behavior
- **Single Window First**: Use `--single` for focused-window-only monitoring when learning
- **Escape to Cancel**: Always remember you can press Escape during countdown

## 📋 Integration Patterns

### Best Practices
```bash
# Development workflow - see what's happening
python3 claude_auto_responder.py --debug --delay 5

# Production workflow - instant response
python3 claude_auto_responder.py --all

# Conservative approach - only focused window
python3 claude_auto_responder.py --single --delay 2

# Custom tool filtering
python3 claude_auto_responder.py --tools "Edit file,Read file,Bash command"
```

### Anti-patterns
```bash
# DON'T: Run without understanding tool filtering
python3 claude_auto_responder.py  # Will respond to ALL whitelisted tools

# DON'T: Set very long delays in production
python3 claude_auto_responder.py --delay 30  # Defeats the purpose

# DON'T: Ignore debug output when troubleshooting
python3 claude_auto_responder.py  # Use --debug to understand issues
```

### Architecture Fit
**Hybrid Python/Swift Design:**
- **Python**: Handles monitoring, detection, parsing, and logic
- **Swift**: Handles reliable keystroke sending via Core Graphics
- **Subprocess AppleScript**: Terminal text reading with zero memory leaks
- **No pyobjc NSAppleScript**: Uses isolated subprocesses for memory safety

### Scaling Considerations
- **Multi-Window Monitoring**: Designed to handle dozens of terminal windows simultaneously
- **Memory Efficiency**: Aggressive garbage collection every 50-100 cycles
- **Subprocess Isolation**: No memory leaks from AppleScript execution
- **Focus Management**: Automatic window switching with smart restoration

## 💡 Detailed Examples

### Example 1: Basic Single-Window Usage
```bash
# Input: You have one terminal with Claude Code running
python3 claude_auto_responder.py --single

# Process:
# 1. Tool monitors only the focused terminal window
# 2. When Claude shows a prompt, countdown begins
# 3. After delay (default 0s), sends "Yes, and don't ask again" or "Yes"
# 4. Returns focus to original app

# Output: Claude continues working without manual confirmation
# Why it matters: Eliminates repetitive clicking for file operations
```

### Example 2: Advanced Multi-Window Pattern
```bash
# Scenario: Multiple Claude sessions in different terminals
python3 claude_auto_responder.py --debug

# Implementation:
# 1. Scans ALL terminal windows every 0.5 seconds
# 2. Detects prompts in background windows
# 3. Automatically switches to window with prompt
# 4. Sends response and restores original focus
# 5. Continues monitoring other windows

# Gotchas:
# - Requires window focus switching (might be visible)
# - Uses more CPU/memory than single window mode
# - Can interfere if you're actively using multiple terminals

# Benefits:
# - True "fire and forget" - work in any app while Claude runs
# - Handles multiple simultaneous Claude sessions
# - No need to manually switch between terminal windows
```

### Example 3: Custom Tool Integration
```bash
# Context: You only want to auto-respond to file operations, not bash commands
# Create custom tools file:
echo "Edit file
Read file
Write file
MultiEdit" > my_safe_tools.txt

python3 claude_auto_responder.py --tools-file my_safe_tools.txt

# Integration: Tool will only respond to whitelisted operations
# Before/After: 
# - Before: Responds to ALL tools including potentially dangerous bash commands
# - After: Only responds to safe file operations

# ROI: Safer automation - avoids accidentally confirming destructive commands
```

## 🔧 Troubleshooting Guide

### Common Issues

**1. "Swift not found" Error**
```bash
# Problem: Swift not available (rare on modern macOS)
# Solution: Swift is built into macOS 10.15+, check your version
sw_vers  # Should show macOS 10.15 or later

# Debug: Check Swift manually  
swift --version  # Should show Swift version
```

**2. "No terminal windows found"**
```bash
# Problem: Tool doesn't detect your terminal
# Solution: Check if your terminal is supported
python3 claude_auto_responder.py --debug

# Supported terminals:
# Terminal, iTerm2, Warp, Hyper, WezTerm, Kitty, Alacritty, Tabby, Termius, Ghostty
```

**3. "Prompt validation failed"**
```bash
# Problem: Tool detects prompts but validation fails
# Solution: Use debug mode to see what's happening
python3 claude_auto_responder.py --debug --delay 5

# Look for:
# - Box drawing characters (╭─╮│╰─╯)
# - "Do you want" text
# - Options with ❯ cursor
```

### Debug Strategies
```bash
# Enable comprehensive debugging
python3 claude_auto_responder.py --debug --single --delay 10

# What you'll see:
# - Window text extraction details
# - Prompt parsing steps
# - Focus switching events
# - Keystroke sending attempts
# - Memory cleanup cycles
```

### Performance Tips
```bash
# Optimize for memory usage
python3 claude_auto_responder.py --single  # Uses ~50% less memory

# Optimize for CPU usage  
python3 claude_auto_responder.py --delay 1  # Reduces checking frequency during countdown

# Balance performance and coverage
python3 claude_auto_responder.py --tools "Edit file,Read file"  # Fewer tools to check
```

### Troubleshooting Examples
```python
# Config validation (Python code)
from claude_auto_responder.config.settings import Config

# Validate your tools file
config = Config.load_whitelisted_tools("my_tools.txt")
print(f"Loaded {len(config)} tools: {config}")

# Debug mode programmatically
responder = AutoResponder(config, debug=True)
```

```bash
# Test keystroke sending directly
swift send_keys.swift 2      # Send option 2
swift send_keys.swift enter  # Send enter key
swift send_keys.swift down   # Send down arrow

# Memory monitoring
python3 monitor_memory.py &  # Run memory monitor in background
python3 claude_auto_responder.py --debug
```

```bash
# Batch validation of terminal windows
python3 -c "
from claude_auto_responder.detection.terminal import TerminalDetector
detector = TerminalDetector()
windows = detector.get_all_terminal_windows(debug=True)
print(f'Found {len(windows)} windows')
for w in windows: print(f'  - {w[\"app\"]}: {w[\"name\"]}')
"
```

## 📚 Next Steps

### Recommended Learning Path
1. **Start Simple**: Run with `--single --debug --delay 5` to understand basics
2. **Add Complexity**: Try `--debug` with multi-window monitoring  
3. **Customize Tools**: Create your own whitelisted tools file
4. **Production Usage**: Remove debug flags, set delay to 0
5. **Advanced Features**: Experiment with sleep detection (`--enable-sleep-detection`)

### Advanced Resources
- **Test Suite**: Run `python3 run_tests.py` to understand expected behavior
- **Memory Monitoring**: Use `python3 monitor_memory.py` for memory usage analysis
- **Source Code**: Study `claude_auto_responder/core/responder.py` for advanced customization
- **Swift Utility**: Examine `send_keys.swift` for keystroke sending mechanisms

### Community
- **GitHub Issues**: Check repository issues for known problems and solutions
- **Debugging**: Use `--debug` flag and share output when reporting issues
- **Feature Requests**: The codebase is well-structured for adding new terminal support
- **Testing**: Comprehensive test suite in `Tests/` directory covers main functionality

### Architecture Deep Dive
- **Config System** (`claude_auto_responder/config/`): Handles settings and tool whitelisting
- **Detection System** (`claude_auto_responder/detection/`): Parser and terminal detection logic  
- **Platform Layer** (`claude_auto_responder/platform/`): macOS-specific implementations
- **Core Logic** (`claude_auto_responder/core/`): Main responder and utility functions
- **Models** (`claude_auto_responder/models/`): Data structures for prompts and configuration

The tool is designed for maximum reliability and memory efficiency, making it suitable for long-running automation tasks with multiple Claude Code sessions.