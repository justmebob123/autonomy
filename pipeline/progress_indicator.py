"""
Progress indicator for long-running model operations.

Provides visual feedback during model calls that may take minutes or hours.
"""

import threading
import time
from typing import Optional
import logging


class ProgressIndicator:
    """Shows progress during long-running operations"""
    
    def __init__(self, logger: logging.Logger, operation: str = "Processing"):
        self.logger = logger
        self.operation = operation
        self.start_time: Optional[float] = None
        self.stop_flag = threading.Event()
        self.thread: Optional[threading.Thread] = None
        self.update_interval = 30  # Update every 30 seconds
        
    def start(self):
        """Start showing progress updates"""
        self.start_time = time.time()
        self.stop_flag.clear()
        self.thread = threading.Thread(target=self._show_progress, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Stop showing progress updates"""
        if self.thread:
            self.stop_flag.set()
            self.thread.join(timeout=1.0)
            self.thread = None
            
    def _show_progress(self):
        """Background thread that shows periodic updates"""
        while not self.stop_flag.is_set():
            # Wait for update interval or stop signal
            if self.stop_flag.wait(self.update_interval):
                break
                
            # Calculate elapsed time
            elapsed = time.time() - self.start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            
            # Show progress update
            if minutes > 0:
                self.logger.info(f"  ⏳ {self.operation}... {minutes}m {seconds}s elapsed")
            else:
                self.logger.info(f"  ⏳ {self.operation}... {seconds}s elapsed")
                
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
        return False