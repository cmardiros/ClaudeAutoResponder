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
from typing import List, Dict, Any


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
    
    @classmethod
    def get_all_terminal_windows(cls, debug: bool = False) -> List[Dict[str, Any]]:
        """Get all open terminal windows with their information"""
        windows = []
        
        try:
            # Simpler approach - get windows as strings and parse
            terminal_script = NSAppleScript.alloc().initWithSource_('''
                set windowList to {}
                
                -- Check Terminal.app
                if application "Terminal" is running then
                    tell application "Terminal"
                        repeat with w in windows
                            set windowInfo to "Terminal|" & (id of w) & "|" & (index of w) & "|" & (name of w)
                            set end of windowList to windowInfo
                        end repeat
                    end tell
                end if
                
                -- Check iTerm2
                if application "iTerm2" is running then
                    tell application "iTerm2"
                        repeat with w in windows
                            set windowInfo to "iTerm2|" & (id of w) & "|" & (index of w) & "|" & (name of w)
                            set end of windowList to windowInfo
                        end repeat
                    end tell
                end if
                
                return windowList
            ''')
            
            result = terminal_script.executeAndReturnError_(None)
            if result[0]:
                # Parse the AppleScript result
                window_list = result[0]
                # Convert AppleScript list to Python list
                for i in range(window_list.numberOfItems()):
                    item = window_list.descriptorAtIndex_(i + 1)
                    try:
                        # Parse the string format
                        window_str = str(item.stringValue())
                        parts = window_str.split('|')
                        if len(parts) >= 4:
                            window_info = {
                                'app': parts[0],
                                'id': int(parts[1]),
                                'index': int(parts[2]),
                                'name': '|'.join(parts[3:])  # Handle names with | in them
                            }
                            windows.append(window_info)
                    except Exception as e:
                        if debug:
                            print(f"🔍 DEBUG: Error parsing window item: {e}")
                        continue
                    
        except Exception as e:
            if debug:
                print(f"🔍 DEBUG: Error getting terminal windows: {e}")
            
        return windows
    
    @staticmethod
    def get_window_text_by_id(app_name: str, window_id: int, max_lines: int = 1000) -> Optional[str]:
        """Get text from a specific terminal window by ID"""
        try:
            if app_name == "Terminal":
                script_source = f'''
                    tell application "Terminal"
                        repeat with w in windows
                            if id of w is {window_id} then
                                set allContent to contents of selected tab of w
                                set lineList to paragraphs of allContent
                                set lineCount to count of lineList
                                
                                if lineCount > {max_lines} then
                                    set startLine to lineCount - {max_lines - 1}
                                    set visibleContent to items startLine through lineCount of lineList
                                    set AppleScript's text item delimiters to "\\n"
                                    set resultText to visibleContent as string
                                    set AppleScript's text item delimiters to ""
                                    return resultText
                                else
                                    return allContent
                                end if
                            end if
                        end repeat
                    end tell
                '''
            elif app_name == "iTerm2":
                script_source = f'''
                    tell application "iTerm2"
                        repeat with w in windows
                            if id of w is {window_id} then
                                set allContent to contents of current session of current tab of w
                                set lineList to paragraphs of allContent
                                set lineCount to count of lineList
                                
                                if lineCount > {max_lines} then
                                    set startLine to lineCount - {max_lines - 1}
                                    set visibleContent to items startLine through lineCount of lineList
                                    set AppleScript's text item delimiters to "\\n"
                                    set resultText to visibleContent as string
                                    set AppleScript's text item delimiters to ""
                                    return resultText
                                else
                                    return allContent
                                end if
                            end if
                        end repeat
                    end tell
                '''
            else:
                return None
                
            script = NSAppleScript.alloc().initWithSource_(script_source)
            result = script.executeAndReturnError_(None)
            
            if result[0]:
                return str(result[0].stringValue())
                
        except Exception as e:
            print(f"🔍 DEBUG: Error getting window text by ID: {e}")
            
        return None
    
    @staticmethod
    def focus_window(app_name: str, window_id: int) -> bool:
        """Focus a specific terminal window"""
        try:
            script_source = f'''
                tell application "{app_name}"
                    repeat with w in windows
                        if id of w is {window_id} then
                            set index of w to 1
                            activate
                            return true
                        end if
                    end repeat
                end tell
                return false
            '''
            
            script = NSAppleScript.alloc().initWithSource_(script_source)
            result = script.executeAndReturnError_(None)
            
            if result[0]:
                return result[0].booleanValue()
                
        except Exception as e:
            print(f"🔍 DEBUG: Error focusing window: {e}")
            
        return False
    
    @staticmethod  
    def get_focused_window_info() -> Optional[Dict[str, Any]]:
        """Get information about the currently focused window/app"""
        try:
            script = NSAppleScript.alloc().initWithSource_('''
                tell application "System Events"
                    set frontApp to first application process whose frontmost is true
                    set appName to name of frontApp
                    set appBundle to bundle identifier of frontApp
                    
                    if appName is "Terminal" then
                        tell application "Terminal"
                            set w to front window
                            return appName & "|" & appBundle & "|terminal|" & (id of w) & "|" & (name of w)
                        end tell
                    else if appName is "iTerm2" then
                        tell application "iTerm2"
                            set w to current window
                            return appName & "|" & appBundle & "|terminal|" & (id of w) & "|" & (name of w)
                        end tell
                    else
                        -- For non-terminal apps, just return app info
                        return appName & "|" & appBundle & "|other|0|" & appName
                    end if
                end tell
            ''')
            
            result = script.executeAndReturnError_(None)
            if result[0]:
                # Parse string result
                result_str = str(result[0].stringValue())
                parts = result_str.split('|')
                if len(parts) >= 5:
                    return {
                        'app': parts[0],
                        'bundle_id': parts[1],
                        'app_type': parts[2],  # 'terminal' or 'other'
                        'window_id': int(parts[3]) if parts[3].isdigit() else 0,
                        'window_name': '|'.join(parts[4:])  # Handle names with | in them
                    }
                
        except Exception as e:
            print(f"🔍 DEBUG: Error getting focused window info: {e}")
            
        return None
    
    @staticmethod
    def restore_focus(window_info: Dict[str, Any]) -> bool:
        """Restore focus to a previously focused window/app"""
        if not window_info:
            return False
            
        try:
            if window_info.get('app_type') == 'terminal' and window_info.get('window_id', 0) > 0:
                # For terminal windows, use the specific window focus method
                return TerminalDetector.focus_window(window_info['app'], window_info['window_id'])
            else:
                # For non-terminal apps, just activate the app
                script_source = f'''
                    tell application "{window_info['app']}"
                        activate
                    end tell
                '''
                script = NSAppleScript.alloc().initWithSource_(script_source)
                result = script.executeAndReturnError_(None)
                return result[0] is not None
                
        except Exception as e:
            print(f"🔍 DEBUG: Error restoring focus: {e}")
            return False