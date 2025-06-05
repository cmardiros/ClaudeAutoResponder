"""Main AutoResponder class"""

import signal
import sys
import select
import termios
import tty
import time
import gc
from threading import Event
from typing import Optional

from ..config.settings import Config
from ..models.prompt import ClaudePrompt
from ..detection.terminal import TerminalDetector
from ..detection.parser import PromptParser
from ..platform.macos import MacOSKeystrokeSender
from ..platform.sleep_detector import SleepDetector
from ..core.utils import _timestamp, _extract_recent_text


class AutoResponder:
    """Main auto responder class"""
    
    def __init__(self, config: Config, debug: bool = False, monitor_all: bool = False):
        self.config = config
        self.debug = debug
        self.monitor_all = monitor_all
        self.parser = PromptParser(config.whitelisted_tools)
        self.detector = TerminalDetector()
        self.keystroke_sender = MacOSKeystrokeSender(debug)
        self.sleep_detector = SleepDetector()
        self.running = False
        self.stop_event = Event()
        self.last_processed_text = ""
        self.last_response_time = 0
        self.is_in_countdown = False
        self.countdown_start_time = 0
        self.countdown_prompt = None
        self.countdown_window_info = None  # Store which window has the prompt
        self.original_focused_window = None  # Store original focus to restore
        self.last_focus_state = None  # Track focus state changes
        self.last_was_monitoring_status = False  # Track if last output was monitoring status
        self.is_paused_for_sleep = False  # Track if monitoring is paused due to sleep

    def start_monitoring(self):
        """Start monitoring for Claude prompts"""
        self.running = True
        
        print(f"\n📋 Whitelisted tools: {', '.join(self.config.whitelisted_tools)}")
        print(f"⏱  Response delay: {int(self.config.default_timeout)}s")
        print(f"🖥  Monitoring mode: {'All terminal windows' if self.monitor_all else 'Focused window only'}")
        
        # Check if Swift is available
        try:
            import subprocess
            result = subprocess.run(['swift', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0] if result.stdout else "Unknown version"
                print(f"Swift found: {version_line}")
            else:
                print(f"⚠️  Swift installation issue")
        except FileNotFoundError:
            print(f"\n⚠️  Swift not found!")
            print(f"Swift is required for sending keystrokes")
            print(f"Continuing to monitor (keystrokes will fail until Swift available)...")
        except Exception as e:
            print(f"⚠️  Could not check Swift: {e}")
        
        print(f"\nMonitoring for Claude prompts... Press Ctrl+C to stop\n")

        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Set up sleep detection callbacks
        def on_sleep():
            self.is_paused_for_sleep = True
            print(f"\n{_timestamp()} 😴 System going to sleep, pausing monitoring...")
            
        def on_wake():
            self.is_paused_for_sleep = False
            print(f"\n{_timestamp()} 👀 System woke up, resuming monitoring...")
            # Clear any stale state from before sleep
            self.is_in_countdown = False
            self.countdown_prompt = None
            self.countdown_window_info = None
            
        self.sleep_detector.set_callbacks(on_sleep, on_wake)
        
        # Start sleep detection if enabled
        if self.config.enable_sleep_detection:
            self.sleep_detector.start_monitoring()
            print(f"💤 Sleep detection enabled")

        cycle_count = 0
        try:
            while self.running and not self.stop_event.is_set():
                # Skip monitoring cycle if system is sleeping
                if not self.is_paused_for_sleep:
                    self._monitoring_cycle()
                else:
                    # Just sleep longer when paused
                    time.sleep(5.0)
                    continue
                    
                time.sleep(self.config.check_interval)
                
                # Periodic garbage collection to prevent memory buildup
                cycle_count += 1
                # More frequent GC for multi-window mode since it uses more memory
                gc_interval = 50 if self.monitor_all else 100
                if cycle_count % gc_interval == 0:
                    gc.collect()
                    if self.debug:
                        print(f"\n{_timestamp()} 🧹 Performed garbage collection (cycle {cycle_count})")
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_monitoring()

    def stop_monitoring(self):
        """Stop monitoring"""
        if self.running:  # Only print message if we were actually running
            self.running = False
            self.stop_event.set()
            
            # Stop sleep detection
            if self.config.enable_sleep_detection:
                self.sleep_detector.stop_monitoring()
            
            # If we're in multi-window mode and have switched focus, restore it
            if (self.monitor_all and self.is_in_countdown and self.original_focused_window):
                try:
                    self.detector.restore_focus(self.original_focused_window)
                except:
                    pass  # Best effort
            
            print(f"\n{_timestamp()} 🛑 Stopped monitoring")

    def _monitoring_cycle(self):
        """Single monitoring cycle - ALWAYS check, handle countdown non-blockingly"""
        current_time = time.time()
        
        if self.monitor_all:
            # Multi-window monitoring mode
            self._monitor_all_windows(current_time)
        else:
            # Single window monitoring mode (original behavior)
            self._monitor_focused_window(current_time)
    
    def _monitor_focused_window(self, current_time: float):
        """Monitor only the focused terminal window (original behavior)"""
        if self.debug:
            if self.last_was_monitoring_status:
                print()  # Add newline
                self.last_was_monitoring_status = False
            print(f"{_timestamp()} 🔄 Monitoring cycle... (countdown: {self.is_in_countdown})")
            
        # Check if terminal is focused and get the frontmost app
        frontmost_app = self.detector.get_frontmost_app()
        is_focused = frontmost_app in self.detector.TERMINAL_BUNDLE_IDS if frontmost_app else False
        
        # Show focus state changes with colored indicators
        if self.last_focus_state != is_focused:
            if is_focused:
                if self.last_was_monitoring_status:
                    # Replace the previous line
                    print(f"\r{' ' * 80}\r{_timestamp()} 🟢 Monitoring: {frontmost_app}", end="", flush=True)
                else:
                    # New line
                    print(f"\n{_timestamp()} 🟢 Monitoring: {frontmost_app}", end="", flush=True)
            else:
                if self.last_was_monitoring_status:
                    # Replace the previous line
                    print(f"\r{' ' * 80}\r{_timestamp()} 🔴 Not monitoring: {frontmost_app or 'Unknown app'}", end="", flush=True)
                else:
                    # New line
                    print(f"\n{_timestamp()} 🔴 Not monitoring: {frontmost_app or 'Unknown app'}", end="", flush=True)
            self.last_focus_state = is_focused
            self.last_was_monitoring_status = True
        else:
            # If this iteration produces non-monitoring output, we need to ensure proper newline
            if self.last_was_monitoring_status and self.debug:
                # Any debug output should start on a new line after monitoring status
                self.last_was_monitoring_status = False
        
        if not is_focused:
            if self.is_in_countdown:
                self._cancel_countdown("Terminal lost focus")
            return

        # Use incremental scanning for maximum memory efficiency
        window_text = self.detector.get_window_text_incremental(debug=self.debug)
        if not window_text:
            if self.debug:
                if self.last_was_monitoring_status:
                    print()  # Add newline
                    self.last_was_monitoring_status = False
                print(f"{_timestamp()} 🔍 DEBUG: No window text available")
            if self.is_in_countdown:
                self._cancel_countdown("No window text available")
            return
        
        if self.debug:
            if self.last_was_monitoring_status:
                print()  # Add newline
                self.last_was_monitoring_status = False
            lines = window_text.split('\n')
            print(f"{_timestamp()} 🔍 DEBUG: Got {len(lines)} lines of text, {len(window_text)} chars total")

        # Handle active countdown - need full text for validation
        if self.is_in_countdown:
            # For countdown validation, we need more complete text
            full_text = self.detector.get_window_text(max_lines=500)
            if full_text:
                self._handle_active_countdown(full_text, current_time)
            else:
                self._cancel_countdown("Lost terminal text during countdown")
        else:
            # For normal monitoring, use the incremental text
            self._check_text_for_prompt(window_text)
        
        # Explicitly clear window_text to help garbage collection
        window_text = None
        # Force collection of any AppleScript descriptors
        gc.collect(0)  # Gen 0 only for speed

    def _check_text_for_prompt(self, text: str):
        """Check text for Claude prompts - simple bottom-up scan"""
        # Skip if we're already in countdown
        if self.is_in_countdown:
            return

        # Rate limiting
        current_time = time.time()
        if current_time - self.last_response_time < 2.0:
            return

        # Extract recent lines for analysis  
        lines = text.split('\n')
        recent_text = _extract_recent_text(text)

        # Create prompt hash for duplicate detection
        prompt_elements = []
        for line in lines[-100:]:
            if any(indicator in line.lower() for indicator in [
                "do you want", "❯", "yes", "don't ask again", "edit file", "read file", 
                "bash", "write", "multiedit", "grep", "glob", "ls", "webfetch", "websearch"
            ]):
                clean_line = ' '.join(line.strip().split())
                if not any(debug_marker in clean_line for debug_marker in [
                    "🔍 DEBUG:", "🔄 Monitoring cycle", "🟢 Monitoring", "🔴 Not monitoring"
                ]):
                    prompt_elements.append(clean_line)
        
        prompt_hash = hash('\n'.join(prompt_elements[-20:]))
        
        # Skip duplicate prompts
        if (hasattr(self, '_last_prompt_hash') and 
            prompt_hash == self._last_prompt_hash and
            not self._recently_cancelled()):
            if self.debug:
                if self.last_was_monitoring_status:
                    print()  # Add newline
                    self.last_was_monitoring_status = False
                print(f"{_timestamp()} 🔍 DEBUG: Same prompt hash ({prompt_hash}), skipping")
            return

        # Parse prompt
        prompt = self.parser.parse_prompt(recent_text, self.debug)

        if prompt.is_valid:
            self._last_prompt_hash = prompt_hash
            self.last_processed_text = recent_text
            self._handle_claude_prompt(prompt)
        elif self.debug:
            if self.last_was_monitoring_status:
                print()  # Add newline
                self.last_was_monitoring_status = False
            print(f"{_timestamp()} 🔍 DEBUG: Prompt hash {prompt_hash}, but prompt validation failed")
            print(f"  Prompt elements found: {prompt_elements[-10:]}")

    def _handle_claude_prompt(self, prompt: ClaudePrompt):
        """Handle detected Claude prompt - start non-blocking countdown"""
        # Ensure we start on a new line if previous output was monitoring status
        if self.last_was_monitoring_status:
            print()  # Add newline
            self.last_was_monitoring_status = False
        
        print(f"{_timestamp()} Detected Claude Code prompt!")
        print(f"{_timestamp()} Tool: {prompt.detected_tool}")
        
        option_desc = "'Yes, and don't ask again'" if prompt.option_to_select == "2" else "'Yes'"
        print(f"{_timestamp()} Will select: {option_desc}")

        # Start non-blocking countdown
        self.is_in_countdown = True
        self.countdown_start_time = time.time()
        self.countdown_prompt = prompt
        print(f"Auto-responding in {int(self.config.default_timeout)}s... (Press Escape to cancel)", end="", flush=True)
    
    def _handle_active_countdown(self, window_text: str, current_time: float):
        """Handle active countdown - check if we should cancel or complete"""
        elapsed = current_time - self.countdown_start_time
        remaining = max(0, self.config.default_timeout - elapsed)
        
        if elapsed >= self.config.default_timeout:
            # Countdown completed - send response with final validation
            # Clear the countdown line and print completion message
            if self.last_was_monitoring_status:
                print()  # Add newline
                self.last_was_monitoring_status = False
            print(f"\r{' ' * 80}\r{_timestamp()} Sending response...")
            
            # Create final validation callback
            def final_validation():
                return self._final_pre_keystroke_validation()
            
            success = self.keystroke_sender.send_response(
                self.countdown_prompt.option_to_select, 
                final_validation_callback=final_validation
            )
            
            if success:
                self._clear_detection_state()
                self.last_was_monitoring_status = False
            else:
                # If validation failed, cancel countdown and restart detection
                self._cancel_countdown("Final validation failed before keystroke")
                
            self.is_in_countdown = False
            self.countdown_prompt = None
            return
        
        # Check if prompt still exists
        recent_text = _extract_recent_text(window_text)
        current_prompt = self.parser.parse_prompt(recent_text, debug=False)
        
        if not current_prompt.is_valid:
            # Debug why the prompt disappeared
            if self.debug:
                if self.last_was_monitoring_status:
                    print()  # Add newline
                    self.last_was_monitoring_status = False
                print(f"\r{_timestamp()} 🔍 DEBUG: Prompt validation failed during countdown")
                self.parser.parse_prompt(recent_text, debug=True)
            self._cancel_countdown("Claude prompt disappeared")
            return
        
        # Check for escape key press
        if self._check_escape_key():
            self._cancel_countdown("User cancelled with Escape key")
            return
            
        remaining_int = int(remaining)
        print(f"\rAuto-responding in {remaining_int + 1}s... (Press Escape to cancel)", end="", flush=True)

    def _cancel_countdown(self, reason: str):
        """Cancel active countdown and reset state for immediate re-detection"""
        if self.is_in_countdown:
            # Clear the countdown line and print cancellation message
            if self.last_was_monitoring_status:
                print()  # Add newline
                self.last_was_monitoring_status = False
            print(f"\r{' ' * 80}\r{_timestamp()} 🚫 {reason} - action cancelled")
            
            # Restore focus if we're in multi-window mode
            if (self.monitor_all and self.original_focused_window and self.countdown_window_info):
                # Only restore if we're not already on the original window
                current_focus = self.detector.get_focused_window_info()
                needs_restore = False
                
                if current_focus and self.original_focused_window:
                    # For terminal windows, compare window IDs
                    if (self.original_focused_window.get('app_type') == 'terminal' and 
                        current_focus.get('window_id') != self.original_focused_window.get('window_id')):
                        needs_restore = True
                    # For non-terminal apps, compare app names
                    elif (self.original_focused_window.get('app_type') == 'other' and 
                          current_focus.get('app') != self.original_focused_window.get('app')):
                        needs_restore = True
                
                if needs_restore:
                    if self.detector.restore_focus(self.original_focused_window):
                        print(f"{_timestamp()} ✅ Restored focus to {self.original_focused_window['app']}")
                    else:
                        print(f"{_timestamp()} ⚠️  Could not restore original focus")
            
            # Reset all countdown state
            self.is_in_countdown = False
            self.countdown_prompt = None
            self.countdown_start_time = 0
            self.countdown_window_info = None
            self.original_focused_window = None
            
            self._clear_detection_state()
            self._last_cancellation_time = time.time()
    
    def _clear_detection_state(self):
        """Clear detection state to allow immediate re-detection"""
        self.last_processed_text = ""
        if hasattr(self, '_last_prompt_hash'):
            delattr(self, '_last_prompt_hash')
        self.last_response_time = 0

    def _recently_cancelled(self) -> bool:
        """Check if we recently cancelled a countdown (within 5 seconds)"""
        if not hasattr(self, '_last_cancellation_time'):
            return False
        return time.time() - self._last_cancellation_time < 5.0

    def _send_response(self, option: str):
        """Send keyboard response (delegates to keystroke sender)"""
        self.keystroke_sender.send_response(option)

    def _check_escape_key(self) -> bool:
        """Check if escape key was pressed (non-blocking)"""
        try:
            # Check if there's input available
            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                # Set terminal to raw mode to read single characters
                old_settings = termios.tcgetattr(sys.stdin)
                try:
                    tty.setraw(sys.stdin.fileno())
                    char = sys.stdin.read(1)
                    # Escape key is ASCII 27 (\x1b)
                    if ord(char) == 27:
                        return True
                finally:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        except (OSError, ValueError, termios.error):
            # If we can't check keyboard input, just return False
            pass
        return False
    
    def _final_pre_keystroke_validation(self) -> bool:
        """
        Critical final validation right before sending keystroke.
        Checks:
        1. Terminal is still focused  
        2. Same window/app is still active
        3. The Claude prompt is still present and valid
        """
        try:
            # Check 1: Is terminal still focused?
            frontmost_app = self.detector.get_frontmost_app()
            is_focused = frontmost_app in self.detector.TERMINAL_BUNDLE_IDS if frontmost_app else False
            
            if not is_focused:
                if self.debug:
                    print(f"{_timestamp()} 🔍 DEBUG: Final validation failed - terminal not focused (frontmost: {frontmost_app})")
                return False
            
            # Check 2: Can we still get window text?
            # For final validation, get enough text to ensure prompt is still there
            window_text = self.detector.get_window_text(max_lines=500)
            if not window_text:
                if self.debug:
                    print(f"{_timestamp()} 🔍 DEBUG: Final validation failed - no window text available")
                return False
            
            # Check 3: Is the Claude prompt still valid?
            recent_text = _extract_recent_text(window_text)
            current_prompt = self.parser.parse_prompt(recent_text, debug=False)
            
            if not current_prompt.is_valid:
                if self.debug:
                    print(f"{_timestamp()} 🔍 DEBUG: Final validation failed - prompt no longer valid")
                return False
            
            # Check 4: Is it the same tool we originally detected?
            if current_prompt.detected_tool != self.countdown_prompt.detected_tool:
                if self.debug:
                    print(f"{_timestamp()} 🔍 DEBUG: Final validation failed - tool changed from {self.countdown_prompt.detected_tool} to {current_prompt.detected_tool}")
                return False
            
            if self.debug:
                print(f"{_timestamp()} 🔍 DEBUG: Final validation passed - safe to send keystroke")
            return True
            
        except Exception as e:
            print(f"{_timestamp()} ⚠️  Final validation error: {e}")
            return False

    def _signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        print(f"\n{_timestamp()} 🛑 Stopping Claude Auto Responder...")
        self.stop_monitoring()
    
    def _monitor_all_windows(self, current_time: float):
        """Monitor all terminal windows for prompts"""
        if self.debug:
            if self.last_was_monitoring_status:
                print()  # Add newline
                self.last_was_monitoring_status = False
                
        # If in countdown, handle it first (avoid getting window list)
        if self.is_in_countdown and self.countdown_window_info:
            self._handle_multi_window_countdown(current_time)
            return
            
        # Get all terminal windows
        windows = self.detector.get_all_terminal_windows(debug=self.debug)
        
        if not windows:
            if self.debug:
                print(f"{_timestamp()} 🔍 DEBUG: No terminal windows found")
            return
            
        # Process windows one at a time to minimize memory usage
        num_windows = len(windows)
        for i in range(num_windows):
            # Extract just the window we need
            window = windows[i]
            
            if self.debug:
                print(f"\n{_timestamp()} 🔍 Checking window {i+1}/{num_windows}: {window['name'][:30]}...")
            
            # Get minimal text for this window using incremental scanner
            window_text = self._get_window_text_incremental(window, debug=self.debug)
            
            if not window_text:
                if self.debug:
                    print(f"{_timestamp()}   ⚠️  No text retrieved from window")
                continue
            
            if self.debug:
                lines = window_text.split('\n')
                print(f"{_timestamp()}   📄 Got {len(lines)} lines, {len(window_text)} chars")
                # Quick indicators check
                has_box = '╭─' in window_text or '╰─' in window_text
                has_caret = '❯' in window_text
                has_do_you_want = 'do you want' in window_text.lower()
                if has_box or has_caret or has_do_you_want:
                    print(f"{_timestamp()}   🎯 Found indicators: box={has_box}, caret={has_caret}, do_you_want={has_do_you_want}")
                
            # Check for prompt
            # For multi-window mode, use the full window text since we already limited it
            prompt = self.parser.parse_prompt(window_text, debug=False)
            
            if prompt.is_valid:
                # Found a prompt! Start countdown for this window
                print(f"\n{_timestamp()} 🎯 Found prompt in {window['app']} window: {window['name']}")
                    
                self._start_multi_window_countdown(prompt, window, current_time)
                # Clear everything before returning
                window_text = None
                window = None
                windows = None
                # Force garbage collection after finding prompt
                gc.collect()
                return  # Process one prompt at a time
            
            # Clear window text immediately after use
            window_text = None
            # Clear the window reference
            window = None
                
        # Update monitoring status (only if not debug)
        if not self.debug and current_time % 5 < 0.5:  # Show status every 5 seconds
            print(f"\r{_timestamp()} 🔍 Monitoring {num_windows} terminal windows...", end="", flush=True)
            self.last_was_monitoring_status = True
            
        # Clear windows list and force collection
        windows = None
        
        # Force garbage collection periodically in multi-window mode
        if hasattr(self, '_multi_window_gc_counter'):
            self._multi_window_gc_counter += 1
        else:
            self._multi_window_gc_counter = 1
            
        if self._multi_window_gc_counter >= 10:  # Every 10 cycles
            gc.collect()
            self._multi_window_gc_counter = 0
    
    def _get_window_text_incremental(self, window: dict, debug: bool = False) -> Optional[str]:
        """Get text from a specific window - simplified for subprocess approach"""
        # Without incremental scanning, we need to fetch enough lines to capture
        # even very large prompts (e.g., long file edits with many lines)
        return self.detector.get_window_text_by_id(
            window['app'], 
            window['id'], 
            max_lines=1000  # Large enough for big prompts
        )
    
    def _start_multi_window_countdown(self, prompt: ClaudePrompt, window: dict, current_time: float):
        """Start countdown for a prompt in a specific window"""
        # Don't save focused window here - we'll do it right before switching
        
        print(f"{_timestamp()} Detected Claude Code prompt in {window['app']}!")
        print(f"{_timestamp()} Window: {window['name']}")
        print(f"{_timestamp()} Tool: {prompt.detected_tool}")
        
        option_desc = "'Yes, and don't ask again'" if prompt.option_to_select == "2" else "'Yes'"
        print(f"{_timestamp()} Will select: {option_desc}")
        
        # Start countdown
        self.is_in_countdown = True
        self.countdown_start_time = current_time
        self.countdown_prompt = prompt
        self.countdown_window_info = window
        
        print(f"Auto-responding in {int(self.config.default_timeout)}s... (Press Escape to cancel)", end="", flush=True)
    
    def _handle_multi_window_countdown(self, current_time: float):
        """Handle countdown for multi-window mode"""
        elapsed = current_time - self.countdown_start_time
        remaining = max(0, self.config.default_timeout - elapsed)
        
        if elapsed >= self.config.default_timeout:
            # Time to respond! 
            print(f"\r{' ' * 80}\r{_timestamp()} Switching to window and sending response...")
            
            # Get current focused window right before switching (not at countdown start)
            self.original_focused_window = self.detector.get_focused_window_info()
            
            if self.debug and self.original_focused_window:
                print(f"{_timestamp()} 🔍 Current focus: {self.original_focused_window['app']} (type: {self.original_focused_window.get('app_type', 'unknown')})")
            
            # Check if we're already on the target window
            if (self.original_focused_window and 
                self.original_focused_window.get('app_type') == 'terminal' and
                self.original_focused_window.get('window_id') == self.countdown_window_info['id']):
                # Already on the right window, no need to switch
                if self.debug:
                    print(f"{_timestamp()} Already on target window")
                self.original_focused_window = None  # Don't restore since we didn't switch
            
            # Switch to the window with the prompt
            if self.detector.focus_window(self.countdown_window_info['app'], self.countdown_window_info['id']):
                # Small delay to ensure focus switch completes
                time.sleep(0.1)
                
                # Validate prompt is still there
                if self._validate_window_prompt(self.countdown_window_info):
                    # Send the response
                    success = self.keystroke_sender.send_response(self.countdown_prompt.option_to_select)
                    
                    if success:
                        print(f"{_timestamp()} ✅ Response sent successfully")
                        
                        # Restore original focus (only if we actually switched)
                        if self.original_focused_window:
                            time.sleep(0.1)  # Small delay before switching back
                            if self.detector.restore_focus(self.original_focused_window):
                                print(f"{_timestamp()} ✅ Restored focus to {self.original_focused_window['app']} - {self.original_focused_window['window_name']}")
                            else:
                                print(f"{_timestamp()} ⚠️  Could not restore original focus")
                else:
                    print(f"{_timestamp()} ❌ Prompt no longer valid in target window")
            else:
                print(f"{_timestamp()} ❌ Failed to focus target window")
                
            # Reset countdown state
            self.is_in_countdown = False
            self.countdown_prompt = None
            self.countdown_window_info = None
            self.original_focused_window = None
            self._clear_detection_state()
            return
            
        # Check if escape was pressed
        if self._check_escape_key():
            self._cancel_countdown("User cancelled with Escape key")
            return
            
        # Update countdown display
        remaining_int = int(remaining)
        print(f"\rAuto-responding in {remaining_int + 1}s... (Press Escape to cancel)", end="", flush=True)
    
    def _validate_window_prompt(self, window: dict) -> bool:
        """Validate that the prompt still exists in the specified window"""
        try:
            # Get fresh text from the window
            window_text = self.detector.get_window_text_by_id(
                window['app'],
                window['id'],
                max_lines=500
            )
            
            if not window_text:
                return False
                
            # Check if prompt is still valid
            recent_text = _extract_recent_text(window_text)
            current_prompt = self.parser.parse_prompt(recent_text, debug=False)
            
            return (current_prompt.is_valid and 
                    current_prompt.detected_tool == self.countdown_prompt.detected_tool)
                    
        except Exception as e:
            if self.debug:
                print(f"\n{_timestamp()} 🔍 DEBUG: Error validating window prompt: {e}")
            return False