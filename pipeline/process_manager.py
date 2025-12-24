"""
Process Management and Awareness System

Provides safe process management with awareness of:
- Own process and process group
- Spawned vs pre-existing processes
- Process relationships and hierarchies
- Resource monitoring capabilities
"""

import os
import signal
import psutil
import time
from typing import Set, Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging


@dataclass
class ProcessInfo:
    """Information about a process"""
    pid: int
    ppid: int
    pgid: int
    name: str
    cmdline: List[str]
    create_time: float
    memory_mb: float
    cpu_percent: float


class ProcessBaseline:
    """Capture and maintain baseline of system processes"""
    
    def __init__(self):
        self.own_pid = os.getpid()
        self.own_pgid = os.getpgid(self.own_pid)
        self.parent_pid = os.getppid()
        self.baseline_pids = self._capture_current_pids()
        self.spawned_pids: Set[int] = set()
        self.spawned_pgids: Set[int] = set()
        self.logger = logging.getLogger(__name__)
        
        # Protect critical processes
        self.protected_pids = {self.own_pid, self.parent_pid, 1}  # Include init
        self.protected_pgids = {self.own_pgid}
        
        self.logger.info(f"Process baseline established:")
        self.logger.info(f"  Own PID: {self.own_pid}")
        self.logger.info(f"  Own PGID: {self.own_pgid}")
        self.logger.info(f"  Parent PID: {self.parent_pid}")
        self.logger.info(f"  Baseline processes: {len(self.baseline_pids)}")
    
    def _capture_current_pids(self) -> Set[int]:
        """Capture all currently running PIDs"""
        try:
            return {p.pid for p in psutil.process_iter(['pid'])}
        except Exception as e:
            self.logger.error(f"Error capturing baseline PIDs: {e}")
            return set()
    
    def register_spawned_process(self, pid: int, pgid: Optional[int] = None):
        """Register a process as spawned by us"""
        self.spawned_pids.add(pid)
        if pgid:
            self.spawned_pgids.add(pgid)
        self.logger.debug(f"Registered spawned process: PID={pid}, PGID={pgid}")
    
    def is_own_process(self, pid: int) -> bool:
        """Check if PID is our own process"""
        return pid == self.own_pid
    
    def is_parent_process(self, pid: int) -> bool:
        """Check if PID is our parent"""
        return pid == self.parent_pid
    
    def is_protected(self, pid: int) -> bool:
        """Check if PID is protected from killing"""
        return pid in self.protected_pids
    
    def is_spawned(self, pid: int) -> bool:
        """Check if we spawned this process"""
        return pid in self.spawned_pids
    
    def is_baseline(self, pid: int) -> bool:
        """Check if process existed in baseline"""
        return pid in self.baseline_pids
    
    def is_safe_to_kill(self, pid: int) -> bool:
        """Check if it's safe to kill this process"""
        if self.is_protected(pid):
            return False
        if self.is_own_process(pid):
            return False
        if self.is_parent_process(pid):
            return False
        # Only safe to kill if we spawned it
        return self.is_spawned(pid)
    
    def get_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """Get detailed information about a process"""
        try:
            proc = psutil.Process(pid)
            return ProcessInfo(
                pid=pid,
                ppid=proc.ppid(),
                pgid=os.getpgid(pid),
                name=proc.name(),
                cmdline=proc.cmdline(),
                create_time=proc.create_time(),
                memory_mb=proc.memory_info().rss / 1024 / 1024,
                cpu_percent=proc.cpu_percent(interval=0.1)
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError) as e:
            self.logger.debug(f"Cannot get info for PID {pid}: {e}")
            return None


class SafeProcessManager:
    """Safely manage processes with awareness and protection"""
    
    def __init__(self, baseline: ProcessBaseline):
        self.baseline = baseline
        self.logger = logging.getLogger(__name__)
    
    def safe_kill(self, pid: int, sig: int = signal.SIGTERM, force: bool = False) -> bool:
        """
        Safely kill a process with protection checks
        
        Args:
            pid: Process ID to kill
            sig: Signal to send
            force: If True, skip safety checks (dangerous!)
        
        Returns:
            True if killed, False if protected or failed
        """
        if not force and not self.baseline.is_safe_to_kill(pid):
            self.logger.warning(f"Refusing to kill protected/unspawned process {pid}")
            return False
        
        try:
            os.kill(pid, sig)
            self.logger.info(f"Sent signal {sig} to process {pid}")
            return True
        except ProcessLookupError:
            self.logger.debug(f"Process {pid} already gone")
            return False
        except PermissionError:
            self.logger.error(f"Permission denied to kill process {pid}")
            return False
        except Exception as e:
            self.logger.error(f"Error killing process {pid}: {e}")
            return False
    
    def safe_killpg(self, pgid: int, sig: int = signal.SIGTERM, force: bool = False) -> bool:
        """
        Safely kill a process group with protection checks
        
        Args:
            pgid: Process group ID to kill
            sig: Signal to send
            force: If True, skip safety checks (dangerous!)
        
        Returns:
            True if killed, False if protected or failed
        """
        if not force and pgid in self.baseline.protected_pgids:
            self.logger.error(f"CRITICAL: Refusing to kill protected process group {pgid}")
            self.logger.error(f"  This is our own process group!")
            return False
        
        if not force and pgid not in self.baseline.spawned_pgids:
            self.logger.warning(f"Refusing to kill unspawned process group {pgid}")
            return False
        
        try:
            os.killpg(pgid, sig)
            self.logger.info(f"Sent signal {sig} to process group {pgid}")
            return True
        except ProcessLookupError:
            self.logger.debug(f"Process group {pgid} already gone")
            return False
        except PermissionError:
            self.logger.error(f"Permission denied to kill process group {pgid}")
            return False
        except Exception as e:
            self.logger.error(f"Error killing process group {pgid}: {e}")
            return False
    
    def kill_spawned_processes(self, timeout: float = 5.0) -> Tuple[int, int]:
        """
        Kill all spawned processes
        
        Returns:
            Tuple of (killed_count, failed_count)
        """
        killed = 0
        failed = 0
        
        for pid in list(self.baseline.spawned_pids):
            if self.safe_kill(pid, signal.SIGTERM):
                killed += 1
            else:
                failed += 1
        
        # Wait for processes to terminate
        time.sleep(min(timeout, 2.0))
        
        # Force kill any remaining
        for pid in list(self.baseline.spawned_pids):
            try:
                proc = psutil.Process(pid)
                if proc.is_running():
                    self.logger.warning(f"Process {pid} still running, force killing")
                    self.safe_kill(pid, signal.SIGKILL)
            except psutil.NoSuchProcess:
                pass
        
        return killed, failed
    
    def get_spawned_processes(self) -> List[ProcessInfo]:
        """Get information about all spawned processes"""
        processes = []
        for pid in self.baseline.spawned_pids:
            info = self.baseline.get_process_info(pid)
            if info:
                processes.append(info)
        return processes
    
    def show_process_tree(self, root_pid: Optional[int] = None, depth: int = 3) -> str:
        """
        Show process tree starting from root_pid
        
        Args:
            root_pid: Root process (defaults to own PID)
            depth: Maximum depth to show
        
        Returns:
            String representation of process tree
        """
        if root_pid is None:
            root_pid = self.baseline.own_pid
        
        try:
            root = psutil.Process(root_pid)
            return self._format_process_tree(root, depth=depth)
        except psutil.NoSuchProcess:
            return f"Process {root_pid} not found"
    
    def _format_process_tree(self, proc: psutil.Process, depth: int, indent: str = "") -> str:
        """Recursively format process tree"""
        if depth <= 0:
            return ""
        
        try:
            pid = proc.pid
            name = proc.name()
            cmdline = " ".join(proc.cmdline()[:3])  # First 3 args
            
            # Mark special processes
            marker = ""
            if pid == self.baseline.own_pid:
                marker = " [OWN]"
            elif pid in self.baseline.spawned_pids:
                marker = " [SPAWNED]"
            elif pid in self.baseline.protected_pids:
                marker = " [PROTECTED]"
            
            result = f"{indent}├─ {pid} {name}{marker}: {cmdline}\n"
            
            # Add children
            children = proc.children()
            for child in children:
                result += self._format_process_tree(child, depth - 1, indent + "│  ")
            
            return result
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return f"{indent}├─ [Process no longer accessible]\n"


class ResourceMonitor:
    """Monitor system and process resources"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_memory_profile(self, pid: Optional[int] = None, include_children: bool = False) -> Dict:
        """Get memory usage profile"""
        try:
            if pid is None:
                # System-wide memory
                mem = psutil.virtual_memory()
                return {
                    'total_mb': mem.total / 1024 / 1024,
                    'available_mb': mem.available / 1024 / 1024,
                    'used_mb': mem.used / 1024 / 1024,
                    'percent': mem.percent
                }
            else:
                # Process-specific memory
                proc = psutil.Process(pid)
                mem_info = proc.memory_info()
                result = {
                    'pid': pid,
                    'rss_mb': mem_info.rss / 1024 / 1024,
                    'vms_mb': mem_info.vms / 1024 / 1024,
                    'percent': proc.memory_percent()
                }
                
                if include_children:
                    children_mem = sum(
                        child.memory_info().rss 
                        for child in proc.children(recursive=True)
                    )
                    result['children_rss_mb'] = children_mem / 1024 / 1024
                
                return result
        except Exception as e:
            self.logger.error(f"Error getting memory profile: {e}")
            return {}
    
    def get_cpu_profile(self, pid: Optional[int] = None, duration: float = 1.0) -> Dict:
        """Get CPU usage profile"""
        try:
            if pid is None:
                # System-wide CPU
                cpu_percent = psutil.cpu_percent(interval=duration, percpu=True)
                return {
                    'overall_percent': sum(cpu_percent) / len(cpu_percent),
                    'per_cpu': cpu_percent,
                    'cpu_count': psutil.cpu_count()
                }
            else:
                # Process-specific CPU
                proc = psutil.Process(pid)
                cpu_percent = proc.cpu_percent(interval=duration)
                cpu_times = proc.cpu_times()
                return {
                    'pid': pid,
                    'percent': cpu_percent,
                    'user_time': cpu_times.user,
                    'system_time': cpu_times.system,
                    'num_threads': proc.num_threads()
                }
        except Exception as e:
            self.logger.error(f"Error getting CPU profile: {e}")
            return {}
    
    def get_system_resources(self, metrics: Optional[List[str]] = None) -> Dict:
        """Get overall system resource usage"""
        if metrics is None:
            metrics = ['cpu', 'memory', 'disk']
        
        result = {}
        
        try:
            if 'cpu' in metrics:
                result['cpu'] = {
                    'percent': psutil.cpu_percent(interval=0.1),
                    'count': psutil.cpu_count(),
                    'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else None
                }
            
            if 'memory' in metrics:
                mem = psutil.virtual_memory()
                result['memory'] = {
                    'total_gb': mem.total / 1024 / 1024 / 1024,
                    'available_gb': mem.available / 1024 / 1024 / 1024,
                    'percent': mem.percent
                }
            
            if 'disk' in metrics:
                disk = psutil.disk_usage('/')
                result['disk'] = {
                    'total_gb': disk.total / 1024 / 1024 / 1024,
                    'free_gb': disk.free / 1024 / 1024 / 1024,
                    'percent': disk.percent
                }
            
            if 'network' in metrics:
                net = psutil.net_io_counters()
                result['network'] = {
                    'bytes_sent_mb': net.bytes_sent / 1024 / 1024,
                    'bytes_recv_mb': net.bytes_recv / 1024 / 1024,
                    'packets_sent': net.packets_sent,
                    'packets_recv': net.packets_recv
                }
        
        except Exception as e:
            self.logger.error(f"Error getting system resources: {e}")
        
        return result