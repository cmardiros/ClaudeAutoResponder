"""Terminal detection and text extraction"""

import time
from typing import Optional, Tuple

try:
    from AppKit import NSWorkspace
    from Cocoa import NSAppleScript
except ImportError as e:
    print(f"⚠️  Missing required dependency: {e}")
    print("\nInstall required packages:")
    print("pip install pyobjc-framework-Cocoa")
    raise

from .incremental_scanner import IncrementalScanner


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
    def get_window_text(max_lines: int = 1000) -> Optional[str]:
        """Get text from the currently focused terminal window
        
        Args:
            max_lines: Maximum number of lines to retrieve (default 1000)
        """
        try:
            # Use AppleScript to get terminal text
            script = NSAppleScript.alloc().initWithSource_(f'''
                tell application "System Events"
                    set frontApp to first application process whose frontmost is true
                    set appName to name of frontApp
                    
                    if appName is "Terminal" then
                        tell application "Terminal"
                            -- Get content and limit to prevent memory issues
                            set allContent to contents of selected tab of front window
                            set lineList to paragraphs of allContent
                            set lineCount to count of lineList
                            
                            -- Get last N lines max to prevent memory issues
                            if lineCount > {max_lines} then
                                set startLine to lineCount - {max_lines - 1}
                                set visibleContent to items startLine through lineCount of lineList
                                -- Join with newlines to preserve line breaks
                                set AppleScript's text item delimiters to "\\n"
                                set resultText to visibleContent as string
                                set AppleScript's text item delimiters to ""
                                return resultText
                            else
                                return allContent
                            end if
                        end tell
                    else if appName is "iTerm2" then
                        tell application "iTerm2"
                            -- Get content from current session
                            set allContent to contents of current session of current tab of current window
                            set lineList to paragraphs of allContent
                            set lineCount to count of lineList
                            
                            -- Limit to last N lines for memory efficiency
                            if lineCount > {max_lines} then
                                set startLine to lineCount - {max_lines - 1}
                                set visibleContent to items startLine through lineCount of lineList
                                -- Join with newlines to preserve line breaks
                                set AppleScript's text item delimiters to "\\n"
                                set resultText to visibleContent as string
                                set AppleScript's text item delimiters to ""
                                return resultText
                            else
                                return allContent
                            end if
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
    
    @staticmethod
    def get_window_text_incremental(debug: bool = False) -> Optional[str]:
        """
        Get terminal text using incremental scanning for maximum memory efficiency.
        Only fetches what's needed to detect prompts.
        Returns just the prompt window text or None.
        """
        # Start with minimal text fetch (50 lines)
        initial_text = TerminalDetector.get_window_text(max_lines=IncrementalScanner.INITIAL_SCAN_LINES)
        if not initial_text:
            return None
            
        # Quick scan for prompt indicators
        prompt_window = IncrementalScanner.find_prompt_window(initial_text, debug)
        
        # If no prompt found in initial scan, return the minimal text for monitoring
        if not prompt_window:
            # Return initial text so responder can still check for changes
            return initial_text
            
        # If we found a prompt but it might be incomplete, fetch more incrementally
        lines_fetched = IncrementalScanner.INITIAL_SCAN_LINES
        max_fetch = IncrementalScanner.MAX_SCAN_LINES
        
        while lines_fetched < max_fetch:
            # Check if we have a complete prompt
            if IncrementalScanner.BOX_TOP_PATTERN.search(prompt_window):
                # We have a complete box, return just the prompt window
                return prompt_window
                
            # Need more lines - fetch incrementally
            lines_to_fetch = min(
                lines_fetched + IncrementalScanner.EXPANSION_INCREMENT,
                max_fetch
            )
            
            if debug:
                print(f"[Terminal] Expanding fetch from {lines_fetched} to {lines_to_fetch} lines")
                
            expanded_text = TerminalDetector.get_window_text(max_lines=lines_to_fetch)
            if not expanded_text:
                return prompt_window  # Return what we have
                
            # Re-scan with more text
            new_window = IncrementalScanner.find_prompt_window(expanded_text, debug)
            if not new_window:
                return prompt_window  # Return previous result
                
            prompt_window = new_window
            lines_fetched = lines_to_fetch
            
        return prompt_window