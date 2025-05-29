"""Terminal detection and text extraction"""

import time
from typing import Optional

try:
    from AppKit import NSWorkspace
    from Cocoa import NSAppleScript
except ImportError as e:
    print(f"⚠️  Missing required dependency: {e}")
    print("\nInstall required packages:")
    print("pip install pyobjc-framework-Cocoa")
    raise


class TerminalDetector:
    """Detects and monitors terminal applications"""
    
    TERMINAL_BUNDLE_IDS = {
        'com.apple.Terminal',
        'com.googlecode.iterm2', 
        'dev.warp.Warp-Stable',
        'co.zeit.hyper',
        'com.github.wez.wezterm',
        'net.kovidgoyal.kitty',
        'io.alacritty',
        'com.tabby.app',
        'com.termius-dmg',
        'com.mitchellh.ghostty'
    }

    @staticmethod
    def get_frontmost_app() -> Optional[str]:
        """Get bundle ID of frontmost application"""
        try:
            # Try AppleScript first - more reliable for focus detection
            script = NSAppleScript.alloc().initWithSource_('''
                tell application "System Events"
                    set frontApp to first application process whose frontmost is true
                    return bundle identifier of frontApp
                end tell
            ''')
            
            result = script.executeAndReturnError_(None)
            if result[0]:
                return str(result[0].stringValue())
            
            # Fallback to NSWorkspace
            workspace = NSWorkspace.sharedWorkspace()
            app = workspace.frontmostApplication()
            if app:
                bundle_id = app.bundleIdentifier()
                return bundle_id
            return None
        except Exception as e:
            print(f"🔍 DEBUG: Error getting frontmost app: {e}")
            return None

    @classmethod
    def is_terminal_focused(cls) -> bool:
        """Check if a terminal app is currently focused"""
        bundle_id = cls.get_frontmost_app()
        
        # If we get None, try once more after a small delay
        if bundle_id is None:
            time.sleep(0.05)
            bundle_id = cls.get_frontmost_app()
        
        return bundle_id in cls.TERMINAL_BUNDLE_IDS if bundle_id else False

    @staticmethod
    def get_window_text() -> Optional[str]:
        """Get text from the currently focused terminal window"""
        try:
            # Use AppleScript to get terminal text
            script = NSAppleScript.alloc().initWithSource_('''
                tell application "System Events"
                    set frontApp to first application process whose frontmost is true
                    set appName to name of frontApp
                    
                    if appName is "Terminal" then
                        tell application "Terminal"
                            return contents of selected tab of front window
                        end tell
                    else if appName is "iTerm2" then
                        tell application "iTerm2"
                            -- Try to get all contents including scrollback
                            return contents of current session of current tab of current window
                        end tell
                    else
                        return ""
                    end if
                end tell
            ''')
            
            result = script.executeAndReturnError_(None)
            if result[0]:
                return str(result[0].stringValue())
            return None
            
        except Exception as e:
            print(f"🔍 DEBUG: Error getting window text: {e}")
            return None