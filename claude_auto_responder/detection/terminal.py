"""Terminal detection using subprocess to completely eliminate memory leaks"""

import subprocess
import time
from typing import Optional, List, Dict, Any


class TerminalDetector:
    """
    Terminal detector that runs ALL AppleScript via subprocess.
    This completely eliminates memory leaks at the cost of some performance.
    """
    
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
    
    def __init__(self):
        self._last_error_time = 0
        
    def _run_applescript(self, script: str, timeout: float = 5.0) -> Optional[str]:
        """
        Run AppleScript in a subprocess. 
        Memory is completely freed when the subprocess exits!
        """
        try:
            # Use osascript to run the AppleScript
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                # Only log errors once per second to avoid spam
                current_time = time.time()
                if current_time - self._last_error_time > 1.0:
                    if result.stderr:
                        print(f"🔍 DEBUG: AppleScript error: {result.stderr.strip()}")
                    self._last_error_time = current_time
                return None
                
        except subprocess.TimeoutExpired:
            # Only print timeout messages occasionally to reduce spam
            current_time = time.time()
            if current_time - self._last_error_time > 30.0:  # Only show every 30 seconds
                print(f"🔍 DEBUG: AppleScript timed out after {timeout}s")
                self._last_error_time = current_time
            return None
        except Exception as e:
            current_time = time.time()
            if current_time - self._last_error_time > 1.0:
                print(f"🔍 DEBUG: Error running AppleScript: {e}")
                self._last_error_time = current_time
            return None
    
    @staticmethod
    def get_frontmost_app() -> Optional[str]:
        """Get bundle ID of frontmost application"""
        detector = TerminalDetector()
        script = '''
        tell application "System Events"
            set frontApp to first application process whose frontmost is true
            return bundle identifier of frontApp
        end tell
        '''
        
        result = detector._run_applescript(script, timeout=2.0)
        if result:
            return result
            
        # Fallback to NSWorkspace if needed
        try:
            from AppKit import NSWorkspace
            workspace = NSWorkspace.sharedWorkspace()
            app = workspace.frontmostApplication()
            if app:
                return app.bundleIdentifier()
        except:
            pass
            
        return None
    
    @classmethod
    def is_terminal_focused(cls) -> bool:
        """Check if a terminal app is currently focused"""
        bundle_id = cls.get_frontmost_app()
        return bundle_id in cls.TERMINAL_BUNDLE_IDS if bundle_id else False
    
    @staticmethod
    def get_window_text(max_lines: int = 1000) -> Optional[str]:
        """Get text from the currently focused terminal window"""
        detector = TerminalDetector()
        script = f'''
        tell application "System Events"
            set frontApp to first application process whose frontmost is true
            set appName to name of frontApp
            
            if appName is "Terminal" then
                tell application "Terminal"
                    set allContent to contents of selected tab of front window
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
                end tell
            else if appName is "iTerm2" then
                tell application "iTerm2"
                    set allContent to contents of current session of current tab of current window
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
                end tell
            else
                return ""
            end if
        end tell
        '''
        
        return detector._run_applescript(script)
    
    @staticmethod
    def get_window_text_incremental(debug: bool = False) -> Optional[str]:
        """
        For compatibility - just calls get_window_text with reasonable defaults
        """
        # Without incremental scanning, fetch enough for large prompts
        return TerminalDetector.get_window_text(max_lines=1000)
    
    @classmethod
    def get_all_terminal_windows(cls, debug: bool = False) -> List[Dict[str, Any]]:
        """Get all open terminal windows with their information"""
        detector = TerminalDetector()
        script = '''
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
        
        -- Return as newline-separated string
        set AppleScript's text item delimiters to "\\n"
        set resultText to windowList as string
        set AppleScript's text item delimiters to ""
        return resultText
        '''
        
        result = detector._run_applescript(script)
        windows = []
        
        if result:
            for line in result.split('\n'):
                if line.strip():
                    parts = line.split('|')
                    if len(parts) >= 4:
                        try:
                            windows.append({
                                'app': parts[0],
                                'id': int(parts[1]),
                                'index': int(parts[2]),
                                'name': '|'.join(parts[3:])
                            })
                        except:
                            if debug:
                                print(f"🔍 DEBUG: Error parsing window: {line}")
        
        return windows
    
    @staticmethod
    def get_window_text_by_id(app_name: str, window_id: int, max_lines: int = 1000) -> Optional[str]:
        """Get text from a specific terminal window by ID"""
        detector = TerminalDetector()
        
        if app_name == "Terminal":
            script = f'''
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
            script = f'''
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
            
        return detector._run_applescript(script)
    
    @staticmethod
    def focus_window(app_name: str, window_id: int) -> bool:
        """Focus a specific terminal window"""
        detector = TerminalDetector()
        script = f'''
        tell application "{app_name}"
            repeat with w in windows
                if id of w is {window_id} then
                    set index of w to 1
                    activate
                    return "true"
                end if
            end repeat
        end tell
        return "false"
        '''
        
        result = detector._run_applescript(script)
        return result == "true"
    
    @staticmethod
    def get_focused_window_info() -> Optional[Dict[str, Any]]:
        """Get information about the currently focused window/app"""
        detector = TerminalDetector()
        script = '''
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
        '''
        
        result = detector._run_applescript(script)
        if result:
            parts = result.split('|')
            if len(parts) >= 5:
                return {
                    'app': parts[0],
                    'bundle_id': parts[1],
                    'app_type': parts[2],  # 'terminal' or 'other'
                    'window_id': int(parts[3]) if parts[3].isdigit() else 0,
                    'window_name': '|'.join(parts[4:])  # Handle names with | in them
                }
        
        return None
    
    @staticmethod
    def restore_focus(window_info: Dict[str, Any]) -> bool:
        """Restore focus to a previously focused window/app"""
        if not window_info:
            return False
            
        detector = TerminalDetector()
        
        if window_info.get('app_type') == 'terminal' and window_info.get('window_id', 0) > 0:
            # For terminal windows, use the specific window focus method
            return TerminalDetector.focus_window(window_info['app'], window_info['window_id'])
        else:
            # For non-terminal apps, just activate the app
            script = f'''
            tell application "{window_info['app']}"
                activate
            end tell
            '''
            result = detector._run_applescript(script)
            return result is not None