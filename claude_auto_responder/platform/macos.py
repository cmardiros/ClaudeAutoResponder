"""macOS-specific platform implementations"""

import subprocess
import time
from ..core.utils import _timestamp


class MacOSKeystrokeSender:
    """Handles keystroke sending on macOS using Swift utility"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.script_path = "/Users/fahad/Developer/ClaudeAutoResponder/send_keys.swift"

    def send_key(self, key_name: str) -> bool:
        """Send a key press using Swift utility"""
        try:
            cmd = ['swift', self.script_path, key_name]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                print(f"{_timestamp()} ⚠️  Swift keystroke error: {result.stderr}")
                return False
            
            if self.debug:
                print(f"{_timestamp()} Sent {key_name} via Swift")
            return True
        except subprocess.TimeoutExpired:
            print(f"{_timestamp()} ⚠️  Swift keystroke timeout")
            return False
        except FileNotFoundError:
            print(f"{_timestamp()} ⚠️  Swift not found")
            return False
        except Exception as e:
            print(f"{_timestamp()} ⚠️  Swift keystroke failed: {e}")
            return False

    def send_response(self, option: str, final_validation_callback=None) -> bool:
        """Send keyboard response for Claude prompt with final validation"""
        try:
            # Small delay to ensure terminal is ready
            time.sleep(0.5)
            
            # CRITICAL: Final validation right before sending keystroke
            if final_validation_callback:
                if not final_validation_callback():
                    print(f"{_timestamp()} 🚫 Final validation failed - aborting keystroke")
                    return False
                    
            if option == "2":
                print(f"{_timestamp()} Selecting option 2...")
                success = self.send_key("2")
                if not success:
                    print(f"{_timestamp()} Trying down arrow instead...")
                    self.send_key("down")
                time.sleep(0.3)
            else:
                print(f"{_timestamp()} Selecting option 1 (default)")
            
            # Press enter to confirm
            print(f"{_timestamp()} Pressing Enter to confirm...")
            time.sleep(0.3)
            self.send_key("enter")
            
            time.sleep(0.2)
            
            print(f"{_timestamp()} Response sent successfully!")
            print(f"{_timestamp()} Waiting for next prompt...\n")
            return True
            
        except Exception as e:
            print(f"{_timestamp()} ⚠️  Error sending response: {e}")
            print(f"{_timestamp()} ⚠️  Swift utility error")
            return False