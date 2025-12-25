"""
Runtime testing and monitoring for debug/QA mode.

This module provides classes for executing programs and monitoring their
runtime behavior through log files.
"""

import subprocess
import threading
import time
import re
import os
import signal
from pathlib import Path
from typing import Optional, List, Dict, Callable
from queue import Queue
import logging
from .process_manager import ProcessBaseline, SafeProcessManager, ResourceMonitor


class ProgramRunner:
    """Manages execution of a test program in a separate thread."""
    
    def __init__(self, command: str, working_dir: Path, logger: logging.Logger = None):
        """
        Initialize program runner.
        
        Args:
            command: Command to execute (e.g., "./autonomous ../my_project/")
            working_dir: Directory to run the command in
            logger: Logger instance
        """
        self.command = command
        self.working_dir = working_dir
        self.logger = logger or logging.getLogger(__name__)
        
        # Process management
        self.baseline = ProcessBaseline()
        self.process_manager = SafeProcessManager(self.baseline)
        self.resource_monitor = ResourceMonitor()
        
        self.process: Optional[subprocess.Popen] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self.exit_code: Optional[int] = None
        
        # Output capture
        self.stdout_lines: List[str] = []
        self.stderr_lines: List[str] = []
    
    def start(self):
        """Start the program in a background thread."""
        if self.running:
            self.logger.warning("Program is already running")
            return
        
        self.running = True
        self.exit_code = None
        self.stdout_lines = []
        self.stderr_lines = []
        
        # Block SIGTERM in this thread to prevent it from being killed
        # when we send SIGTERM to child process groups
        try:
            signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTERM})
            self.logger.debug("Blocked SIGTERM in monitoring process")
        except AttributeError:
            # pthread_sigmask not available on all platforms
            self.logger.debug("pthread_sigmask not available, skipping signal blocking")
        
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        
        self.logger.info(f"Started program: {self.command}")
    
    def _run(self):
        """Internal method to run the program."""
        try:
            # Create a new process group so we can kill all children
            self.process = subprocess.Popen(
                self.command,
                shell=True,
                cwd=str(self.working_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Register this process as spawned
            pid = self.process.pid
            pgid = os.getpgid(pid)
            self.baseline.register_spawned_process(pid, pgid)
            self.logger.info(f"Spawned process: PID={pid}, PGID={pgid}")
            
            # Read output in real-time
            while self.running and self.process.poll() is None:
                # Read stdout
                if self.process.stdout:
                    line = self.process.stdout.readline()
                    if line:
                        self.stdout_lines.append(line)
                        if len(self.stdout_lines) > 1000:  # Limit memory
                            self.stdout_lines.pop(0)
                
                # Read stderr
                if self.process.stderr:
                    line = self.process.stderr.readline()
                    if line:
                        self.stderr_lines.append(line)
                        if len(self.stderr_lines) > 1000:  # Limit memory
                            self.stderr_lines.pop(0)
                
                time.sleep(0.01)  # Small delay to prevent busy loop
            
            # Get exit code
            if self.process:
                self.exit_code = self.process.wait()
                
                # CRITICAL: Read any remaining output after process exits
                # This catches error messages that were buffered
                if self.process.stdout:
                    remaining_stdout = self.process.stdout.read()
                    if remaining_stdout:
                        for line in remaining_stdout.splitlines():
                            if line:
                                self.stdout_lines.append(line + '\n')
                
                if self.process.stderr:
                    remaining_stderr = self.process.stderr.read()
                    if remaining_stderr:
                        for line in remaining_stderr.splitlines():
                            if line:
                                self.stderr_lines.append(line + '\n')
                
                self.logger.info(f"Program exited with code: {self.exit_code}")
        
        except Exception as e:
            self.logger.error(f"Error running program: {e}")
            self.exit_code = -1
        
        finally:
            self.running = False
    
    def stop(self, timeout: float = 300.0):
        """
        Stop the running program and all child processes.
        
        Args:
            timeout: Seconds to wait for graceful shutdown (5 minutes)
        """
        if not self.running:
            self.logger.info("Stop called but program not running")
            return
        
        self.logger.info("Stopping program...")
        self.running = False
        
        if self.process:
            try:
                pid = self.process.pid
                pgid = os.getpgid(pid)
                
                self.logger.info(f"Stopping process: PID={pid}, PGID={pgid}")
                
                # Get all processes in the target group
                import subprocess
                try:
                    result = subprocess.run(
                        ['ps', '-g', str(pgid), '-o', 'pid', '--no-headers'],
                        capture_output=True,
                        text=True,
                        timeout=60  # 60 seconds for ps command
                    )
                    if result.returncode == 0:
                        pids_in_group = [int(p.strip()) for p in result.stdout.strip().split('\n') if p.strip()]
                        self.logger.info(f"Found {len(pids_in_group)} processes in group {pgid}")
                        
                        # Kill each process individually, skipping our own and parent
                        killed_count = 0
                        for proc_pid in pids_in_group:
                            if proc_pid == self.baseline.own_pid:
                                self.logger.info(f"Skipping own PID {proc_pid}")
                                continue
                            if proc_pid == self.baseline.parent_pid:
                                self.logger.info(f"Skipping parent PID {proc_pid}")
                                continue
                            
                            try:
                                # Try SIGTERM first
                                os.kill(proc_pid, signal.SIGTERM)
                                self.logger.info(f"Sent SIGTERM to {proc_pid}")
                                killed_count += 1
                            except ProcessLookupError:
                                self.logger.debug(f"Process {proc_pid} already dead")
                            except Exception as e:
                                self.logger.warning(f"Error killing {proc_pid}: {e}")
                        
                        self.logger.info(f"Sent SIGTERM to {killed_count} processes")
                        
                        # Wait a bit for graceful shutdown
                        time.sleep(1)
                        
                        # Force kill any remaining processes
                        for proc_pid in pids_in_group:
                            if proc_pid == self.baseline.own_pid or proc_pid == self.baseline.parent_pid:
                                continue
                            
                            try:
                                # Check if still alive
                                os.kill(proc_pid, 0)
                                # Still alive, force kill
                                os.kill(proc_pid, signal.SIGKILL)
                                self.logger.info(f"Sent SIGKILL to {proc_pid}")
                            except ProcessLookupError:
                                # Already dead, good
                                pass
                            except Exception as e:
                                self.logger.warning(f"Error force killing {proc_pid}: {e}")
                        
                except Exception as e:
                    self.logger.warning(f"Error getting process group: {e}")
                    # Fallback: just kill the main process
                    try:
                        os.kill(pid, signal.SIGKILL)
                        self.logger.info(f"Killed main process {pid}")
                    except:
                        pass
                
                # Wait for process to die
                try:
                    self.process.wait(timeout=timeout)
                    self.logger.info("Process terminated")
                except subprocess.TimeoutExpired:
                    self.logger.warning("Process did not terminate, may still be running")
                except:
                    pass
                    
            except Exception as e:
                self.logger.error(f"Error stopping program: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
            finally:
                self.process = None

    def is_running(self) -> bool:
        """Check if the program is currently running."""
        return self.running
    
    def get_recent_output(self, lines: int = 50) -> Dict[str, List[str]]:
        """
        Get recent output from the program.
        
        Args:
            lines: Number of recent lines to return
        
        Returns:
            Dictionary with 'stdout' and 'stderr' keys
        """
        return {
            'stdout': self.stdout_lines[-lines:],
            'stderr': self.stderr_lines[-lines:]
        }


class LogMonitor:
    """Monitors a log file for runtime errors."""
    
    # Error patterns to detect in logs
    ERROR_PATTERNS = [
        (r'Traceback \(most recent call last\):', 'exception'),
        (r'ERROR:', 'error'),
        (r'CRITICAL:', 'critical'),
        (r'Exception:', 'exception'),
        (r'Error:', 'error'),
        (r'Failed:', 'failure'),
        (r'FAILED:', 'failure'),
        (r'\[ERROR\]', 'error'),
        (r'\[CRITICAL\]', 'critical'),
    ]
    
    def __init__(
        self,
        log_file: Path,
        error_callback: Callable[[Dict], None],
        logger: logging.Logger = None
    ):
        """
        Initialize log monitor.
        
        Args:
            log_file: Path to log file to monitor
            error_callback: Function to call when errors are detected
            logger: Logger instance
        """
        self.log_file = log_file
        self.error_callback = error_callback
        self.logger = logger or logging.getLogger(__name__)
        
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self.last_position = 0
        
        # Compile patterns
        self.compiled_patterns = [
            (re.compile(pattern), error_type)
            for pattern, error_type in self.ERROR_PATTERNS
        ]
    
    def start(self):
        """Start monitoring the log file."""
        if self.running:
            self.logger.warning("Log monitor is already running")
            return
        
        self.running = True
        self.last_position = 0
        
        # If log file exists, start from end
        if self.log_file.exists():
            self.last_position = self.log_file.stat().st_size
        
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()
        
        self.logger.info(f"Started monitoring log file: {self.log_file}")
    
    def _monitor(self):
        """Internal method to monitor the log file."""
        error_buffer = []
        in_traceback = False
        
        while self.running:
            try:
                # Wait for log file to exist
                if not self.log_file.exists():
                    time.sleep(1)
                    continue
                
                # Read new content
                with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(self.last_position)
                    new_lines = f.readlines()
                    self.last_position = f.tell()
                
                # Process new lines
                for line in new_lines:
                    # Check for error patterns
                    for pattern, error_type in self.compiled_patterns:
                        if pattern.search(line):
                            if error_type == 'exception':
                                in_traceback = True
                                error_buffer = [line]
                            else:
                                # Report error immediately
                                self.error_callback({
                                    'type': error_type,
                                    'line': line.strip(),
                                    'context': []
                                })
                            break
                    
                    # Collect traceback lines
                    if in_traceback:
                        error_buffer.append(line)
                        # End of traceback (empty line or new log entry)
                        if not line.strip() or (line[0] not in ' \t' and 'Traceback' not in line):
                            if len(error_buffer) > 1:
                                self.error_callback({
                                    'type': 'exception',
                                    'line': error_buffer[0].strip(),
                                    'context': [l.strip() for l in error_buffer[1:]]
                                })
                            in_traceback = False
                            error_buffer = []
                
                time.sleep(0.5)  # Check every 0.5 seconds
            
            except Exception as e:
                self.logger.error(f"Error monitoring log file: {e}")
                time.sleep(1)
    
    def stop(self):
        """Stop monitoring the log file."""
        if not self.running:
            return
        
        self.logger.info("Stopping log monitor...")
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=60)  # 60 seconds for thread cleanup
        
        self.logger.info("Log monitor stopped")
    
    def is_running(self) -> bool:
        """Check if the monitor is currently running."""
        return self.running
    
    def clear_log(self):
        """Clear the log file."""
        if self.log_file.exists():
            self.log_file.write_text('')
            self.last_position = 0
            self.logger.info(f"Cleared log file: {self.log_file}")


class RuntimeTester:
    """Coordinates program execution and log monitoring."""
    
    def __init__(
        self,
        command: str,
        working_dir: Path,
        log_file: Path,
        logger: logging.Logger = None
    ):
        """
        Initialize runtime tester.
        
        Args:
            command: Command to execute
            working_dir: Directory to run command in
            log_file: Log file to monitor
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.log_file = log_file  # Store log_file as attribute
        
        self.error_queue = Queue()
        
        self.program_runner = ProgramRunner(command, working_dir, logger)
        self.log_monitor = LogMonitor(
            log_file,
            self._on_error_detected,
            logger
        )
    
    def _on_error_detected(self, error: Dict):
        """Callback when an error is detected in logs."""
        self.error_queue.put(error)
    
    def start(self):
        """Start program execution and log monitoring."""
        self.logger.info("Starting runtime testing...")
        
        # Clear log file
        self.log_monitor.clear_log()
        
        # Start monitoring first
        self.log_monitor.start()
        
        # Then start program
        time.sleep(0.5)  # Small delay
        self.program_runner.start()
    
    def stop(self):
        """Stop program execution and log monitoring."""
        self.logger.info("Stopping runtime testing...")
        
        # Stop program first
        self.program_runner.stop()
        
        # Then stop monitoring
        self.log_monitor.stop()
    
    def get_errors(self) -> List[Dict]:
        """Get all detected errors from both log file and stdout/stderr."""
        errors = []
        
        # Get errors from log file monitoring
        while not self.error_queue.empty():
            errors.append(self.error_queue.get())
        
        # CRITICAL: Also check stdout/stderr for errors that didn't make it to log file
        # This catches crashes during initialization before logging starts
        if not self.program_runner.is_running() and self.program_runner.exit_code != 0:
            # Check stderr for tracebacks
            stderr_text = ''.join(self.program_runner.stderr_lines)
            if 'Traceback' in stderr_text or 'Error:' in stderr_text or 'ERROR:' in stderr_text:
                errors.append({
                    'type': 'stderr_exception',
                    'line': 'Program crashed before logging started',
                    'context': self.program_runner.stderr_lines[-50:],  # Last 50 lines
                    'exit_code': self.program_runner.exit_code
                })
            
            # Check stdout for errors too
            stdout_text = ''.join(self.program_runner.stdout_lines)
            if 'Traceback' in stdout_text or 'Error:' in stdout_text or 'ERROR:' in stdout_text:
                errors.append({
                    'type': 'stdout_exception',
                    'line': 'Program crashed before logging started',
                    'context': self.program_runner.stdout_lines[-50:],  # Last 50 lines
                    'exit_code': self.program_runner.exit_code
                })
        
        return errors
    
    def is_running(self) -> bool:
        """Check if testing is currently running."""
        return self.program_runner.is_running()
    
    def get_stdout(self) -> List[str]:
        """Get captured stdout lines."""
        return self.program_runner.stdout_lines.copy()
    
    def get_stderr(self) -> List[str]:
        """Get captured stderr lines."""
        return self.program_runner.stderr_lines.copy()
    
    def get_exit_code(self) -> Optional[int]:
        """Get program exit code."""
        return self.program_runner.exit_code