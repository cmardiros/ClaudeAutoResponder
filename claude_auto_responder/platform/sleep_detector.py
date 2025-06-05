"""macOS sleep/wake detection module."""

import subprocess
import threading
import time
from typing import Callable, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SleepDetector:
    """Detects system sleep/wake events on macOS."""
    
    def __init__(self):
        self._is_sleeping = False
        self._sleep_callback: Optional[Callable] = None
        self._wake_callback: Optional[Callable] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        self._last_wake_time = 0
        self._last_sleep_time = 0
        
    @property
    def is_sleeping(self) -> bool:
        """Return whether the system is currently sleeping."""
        return self._is_sleeping
        
    def set_callbacks(self, sleep_callback: Optional[Callable] = None, 
                     wake_callback: Optional[Callable] = None):
        """Set callbacks for sleep and wake events."""
        self._sleep_callback = sleep_callback
        self._wake_callback = wake_callback
        
    def start_monitoring(self):
        """Start monitoring for sleep/wake events."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            logger.warning("Sleep detection already running")
            return
            
        self._stop_monitoring.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_sleep_events,
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("Started sleep/wake detection")
        
    def stop_monitoring(self):
        """Stop monitoring for sleep/wake events."""
        self._stop_monitoring.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
        logger.info("Stopped sleep/wake detection")
        
    def _monitor_sleep_events(self):
        """Monitor system sleep/wake events using caffeinate."""
        try:
            # Use caffeinate with -s flag to monitor sleep events
            # It will exit when the system goes to sleep
            while not self._stop_monitoring.is_set():
                # Start caffeinate process
                process = subprocess.Popen(
                    ['caffeinate', '-s', '-w', str(threading.get_ident())],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Wait for process to exit (which happens on sleep)
                while not self._stop_monitoring.is_set():
                    try:
                        # Check if process is still running
                        retcode = process.poll()
                        if retcode is not None:
                            # Process exited, system went to sleep
                            current_time = time.time()
                            if current_time - self._last_sleep_time > 5:  # Debounce
                                self._last_sleep_time = current_time
                                if not self._is_sleeping:
                                    self._is_sleeping = True
                                    logger.info("System entering sleep")
                                    if self._sleep_callback:
                                        try:
                                            self._sleep_callback()
                                        except Exception as e:
                                            logger.error(f"Sleep callback error: {e}")
                            break
                        
                        # If we were sleeping and caffeinate is running, we woke up
                        if self._is_sleeping and retcode is None:
                            current_time = time.time()
                            if current_time - self._last_wake_time > 5:  # Debounce
                                self._last_wake_time = current_time
                                self._is_sleeping = False
                                logger.info("System waking up")
                                if self._wake_callback:
                                    try:
                                        self._wake_callback()
                                    except Exception as e:
                                        logger.error(f"Wake callback error: {e}")
                        
                        time.sleep(1)
                        
                    except Exception as e:
                        logger.debug(f"Error in sleep monitor loop: {e}")
                        break
                
                # Clean up process
                if process.poll() is None:
                    process.terminate()
                    process.wait()
                
                # Wait a bit before restarting
                if not self._stop_monitoring.is_set():
                    time.sleep(2)
                    
        except Exception as e:
            logger.error(f"Error monitoring sleep events: {e}")
            
    def check_if_just_woke(self) -> bool:
        """Check if the system just woke from sleep."""
        # Simple check based on our last wake time
        if self._last_wake_time > 0:
            return time.time() - self._last_wake_time < 60
        return False