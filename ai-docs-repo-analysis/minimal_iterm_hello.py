#!/usr/bin/env python3
"""
Minimal Hello World: Python interacting with iTerm2
Shows the simplest possible way to read from and write to iTerm
"""

import subprocess
import time

def get_iterm_text():
    """Get text from iTerm2 current session - minimal version"""
    applescript = '''
    tell application "iTerm2"
        try
            set sessionText to contents of current session of current tab of current window
            return sessionText
        on error
            return "Error: Could not get iTerm2 text"
        end try
    end tell
    '''
    
    try:
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() if result.returncode == 0 else "Failed to get text"
    except Exception as e:
        return f"Error: {e}"

def send_text_to_iterm(text):
    """Send text to iTerm2 current session - minimal version"""
    applescript = f'''
    tell application "iTerm2"
        try
            tell current session of current tab of current window
                write text "{text}"
            end tell
            return "Success"
        on error
            return "Error: Could not send text to iTerm2"
        end try
    end tell
    '''
    
    try:
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def is_iterm_running():
    """Check if iTerm2 is running - minimal version"""
    applescript = '''
    tell application "System Events"
        return (name of processes) contains "iTerm2"
    end tell
    '''
    
    try:
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() == "true"
    except Exception as e:
        return False

def main():
    """Minimal hello world demo"""
    print("🚀 Minimal iTerm2 Python Interaction Demo")
    print("=" * 40)
    
    # Check if iTerm2 is running
    if not is_iterm_running():
        print("❌ iTerm2 is not running. Please open iTerm2 first.")
        return
    
    print("✅ iTerm2 is running")
    
    # Get current text from iTerm2
    print("\n📖 Reading current iTerm2 content...")
    current_text = get_iterm_text()
    print(f"Last few lines from iTerm2:")
    print("-" * 30)
    # Show only last 5 lines to keep it manageable
    lines = current_text.split('\n')[-5:]
    for line in lines:
        print(f"  {line}")
    print("-" * 30)
    
    # Send a hello message to iTerm2
    print("\n✍️  Sending 'Hello from Python!' to iTerm2...")
    result = send_text_to_iterm("Hello from Python! This is a minimal demo.")
    print(f"Send result: {result}")
    
    # Wait a moment and read again to see our message
    time.sleep(1)
    print("\n📖 Reading iTerm2 content after sending message...")
    new_text = get_iterm_text()
    new_lines = new_text.split('\n')[-3:]
    print("Last 3 lines:")
    for line in new_lines:
        print(f"  {line}")

if __name__ == "__main__":
    main()