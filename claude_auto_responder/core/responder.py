"""Main AutoResponder class"""

import signal
import sys
import select
import termios
import tty
import time
from threading import Event

from ..config.settings import Config
from ..models.prompt import ClaudePrompt
from ..detection.terminal import TerminalDetector
from ..detection.parser import PromptParser
from ..platform.macos import MacOSKeystrokeSender
from ..core.utils import _timestamp, _extract_recent_text


class AutoResponder:
    """Main auto responder class"""
    
    def __init__(self, config: Config, debug: bool = False):
        self.config = config
        self.debug = debug
        self.parser = PromptParser(config.whitelisted_tools)
        self.detector = TerminalDetector()
        self.keystroke_sender = MacOSKeystrokeSender(debug)
        self.running = False
        self.stop_event = Event()
        self.last_processed_text = ""
        self.last_response_time = 0
        self.is_in_countdown = False
        self.current_window_id = ""
        self.countdown_start_time = 0
        self.countdown_prompt = None
        self.last_focus_state = None  # Track focus state changes

    def start_monitoring(self):
        """Start monitoring for Claude prompts"""
        self.running = True
        
        print(f"\n📋 Whitelisted tools: {', '.join(self.config.whitelisted_tools)}")
        print(f"⏱  Response delay: {int(self.config.default_timeout)}s")
        
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

        try:
            while self.running and not self.stop_event.is_set():
                self._monitoring_cycle()
                time.sleep(self.config.check_interval)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_monitoring()

    def stop_monitoring(self):
        """Stop monitoring"""
        if self.running:  # Only print message if we were actually running
            self.running = False
            self.stop_event.set()
            print(f"\n{_timestamp()} 🛑 Stopped monitoring")

    def _monitoring_cycle(self):
        """Single monitoring cycle - ALWAYS check, handle countdown non-blockingly"""
        current_time = time.time()
        
        if self.debug:
            print(f"{_timestamp()} 🔄 Monitoring cycle... (countdown: {self.is_in_countdown})")
            
        # Check if terminal is focused and get the frontmost app
        frontmost_app = self.detector.get_frontmost_app()
        is_focused = frontmost_app in self.detector.TERMINAL_BUNDLE_IDS if frontmost_app else False
        
        # Show focus state changes with colored indicators
        if self.last_focus_state != is_focused:
            if is_focused:
                print(f"{_timestamp()} 🟢 Monitoring: {frontmost_app}")
            else:
                print(f"{_timestamp()} 🔴 Not monitoring: {frontmost_app or 'Unknown app'}")
            self.last_focus_state = is_focused
        
        if not is_focused:
            if self.is_in_countdown:
                self._cancel_countdown("Terminal lost focus")
            return

        # Get window text every time
        window_text = self.detector.get_window_text()
        if not window_text:
            if self.debug:
                print(f"{_timestamp()} 🔍 DEBUG: No window text available")
            if self.is_in_countdown:
                self._cancel_countdown("No window text available")
            return
        
        if self.debug:
            lines = window_text.split('\n')
            print(f"{_timestamp()} 🔍 DEBUG: Got {len(lines)} lines of text, {len(window_text)} chars total")

        # Handle active countdown
        if self.is_in_countdown:
            self._handle_active_countdown(window_text, current_time)
        else:
            self._check_text_for_prompt(window_text)

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
                print(f"{_timestamp()} 🔍 DEBUG: Same prompt hash ({prompt_hash}), skipping")
            return

        # Parse prompt
        prompt = self.parser.parse_prompt(recent_text, self.debug)

        if prompt.is_valid:
            self._last_prompt_hash = prompt_hash
            self.last_processed_text = recent_text
            self._handle_claude_prompt(prompt)
        elif self.debug:
            print(f"{_timestamp()} 🔍 DEBUG: Prompt hash {prompt_hash}, but prompt validation failed")
            print(f"  Prompt elements found: {prompt_elements[-10:]}")

    def _handle_claude_prompt(self, prompt: ClaudePrompt):
        """Handle detected Claude prompt - start non-blocking countdown"""
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
            # Countdown completed - send response
            # Clear the countdown line and print completion message
            print(f"\r{' ' * 80}\r{_timestamp()} Sending response...")
            self.keystroke_sender.send_response(self.countdown_prompt.option_to_select)
            self._clear_detection_state()
            self.is_in_countdown = False
            self.countdown_prompt = None
            return
        
        # Check if prompt still exists
        recent_text = _extract_recent_text(window_text)
        current_prompt = self.parser.parse_prompt(recent_text, debug=False)
        
        if not current_prompt.is_valid:
            # Debug why the prompt disappeared
            if self.debug:
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
            print(f"\r{' ' * 80}\r{_timestamp()} 🚫 {reason} - action cancelled")
            self.is_in_countdown = False
            self.countdown_prompt = None
            self.countdown_start_time = 0
            
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
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        print(f"\n{_timestamp()} 🛑 Stopping Claude Auto Responder...")
        self.stop_monitoring()