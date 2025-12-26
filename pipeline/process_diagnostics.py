"""
Process Diagnostics System

Analyzes why processes fail to start or exit prematurely.
Provides detailed diagnostic information for debugging.
"""

import os
import subprocess
import shlex
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging


class ProcessDiagnostics:
    """Diagnoses process startup and execution issues"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def diagnose_command(self, command: str, working_dir: Path) -> Dict[str, any]:
        """
        Comprehensive diagnosis of why a command might fail.
        
        Returns:
            Dictionary with diagnostic information
        """
        diagnostics = {
            'command': command,
            'working_dir': str(working_dir),
            'issues': [],
            'warnings': [],
            'recommendations': [],
            'executable_info': {},
            'environment_info': {},
        }
        
        # Parse command to get executable
        try:
            parts = shlex.split(command)
            executable = parts[0] if parts else None
        except Exception as e:
            diagnostics['issues'].append(f"Failed to parse command: {e}")
            return diagnostics
        
        if not executable:
            diagnostics['issues'].append("Empty command")
            return diagnostics
        
        # Check if executable exists
        executable_path = self._find_executable(executable, working_dir)
        diagnostics['executable_info']['name'] = executable
        diagnostics['executable_info']['found'] = executable_path is not None
        
        if executable_path:
            diagnostics['executable_info']['path'] = str(executable_path)
            diagnostics['executable_info']['is_file'] = executable_path.is_file()
            diagnostics['executable_info']['is_executable'] = os.access(executable_path, os.X_OK)
            diagnostics['executable_info']['size'] = executable_path.stat().st_size if executable_path.exists() else 0
            
            # Check permissions
            if not os.access(executable_path, os.X_OK):
                diagnostics['issues'].append(f"Executable not executable: {executable_path}")
                diagnostics['recommendations'].append(f"Run: chmod +x {executable_path}")
        else:
            diagnostics['issues'].append(f"Executable not found: {executable}")
            diagnostics['recommendations'].append(f"Check if '{executable}' is installed or in PATH")
        
        # Check working directory
        if not working_dir.exists():
            diagnostics['issues'].append(f"Working directory does not exist: {working_dir}")
        elif not working_dir.is_dir():
            diagnostics['issues'].append(f"Working directory is not a directory: {working_dir}")
        else:
            diagnostics['environment_info']['working_dir_exists'] = True
            diagnostics['environment_info']['working_dir_readable'] = os.access(working_dir, os.R_OK)
            diagnostics['environment_info']['working_dir_writable'] = os.access(working_dir, os.W_OK)
        
        # Check for common issues
        self._check_common_issues(command, working_dir, diagnostics)
        
        return diagnostics
    
    def _find_executable(self, executable: str, working_dir: Path) -> Optional[Path]:
        """Find the executable in various locations"""
        
        # Check if it's a relative path
        if '/' in executable or '\\' in executable:
            # Relative or absolute path
            if executable.startswith('/'):
                # Absolute path
                path = Path(executable)
            else:
                # Relative to working directory
                path = working_dir / executable
            
            if path.exists():
                return path
            return None
        
        # Check in working directory
        local_path = working_dir / executable
        if local_path.exists():
            return local_path
        
        # Check in PATH
        path_env = os.environ.get('PATH', '').split(os.pathsep)
        for path_dir in path_env:
            path = Path(path_dir) / executable
            if path.exists():
                return path
        
        return None
    
    def _check_common_issues(self, command: str, working_dir: Path, diagnostics: Dict):
        """Check for common issues that cause process failures"""
        
        # Check for shell-specific syntax
        if any(char in command for char in ['|', '>', '<', '&', ';', '&&', '||']):
            diagnostics['warnings'].append("Command contains shell operators - ensure shell=True is used")
        
        # Check for environment variables
        if '$' in command:
            diagnostics['warnings'].append("Command contains environment variables - ensure they are expanded")
        
        # Check for quotes
        if command.count('"') % 2 != 0 or command.count("'") % 2 != 0:
            diagnostics['issues'].append("Unmatched quotes in command")
        
        # Check for Python scripts
        if command.startswith('python') or '.py' in command:
            # Check if Python is available
            try:
                result = subprocess.run(['python', '--version'], capture_output=True, text=True, timeout=5)
                diagnostics['environment_info']['python_available'] = result.returncode == 0
                diagnostics['environment_info']['python_version'] = result.stdout.strip()
            except Exception:
                diagnostics['issues'].append("Python not available in PATH")
        
        # Check for Node.js scripts
        if command.startswith('node') or command.startswith('npm'):
            try:
                result = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=5)
                diagnostics['environment_info']['node_available'] = result.returncode == 0
                diagnostics['environment_info']['node_version'] = result.stdout.strip()
            except Exception:
                diagnostics['warnings'].append("Node.js not available in PATH")
    
    def analyze_exit_code(self, exit_code: int) -> Dict[str, any]:
        """
        Analyze exit code to determine what went wrong.
        
        Returns:
            Dictionary with analysis
        """
        analysis = {
            'exit_code': exit_code,
            'meaning': '',
            'category': '',
            'likely_causes': [],
            'recommendations': [],
        }
        
        if exit_code == 0:
            analysis['meaning'] = "Success"
            analysis['category'] = "SUCCESS"
        elif exit_code == -1:
            analysis['meaning'] = "Process failed to start or was killed before starting"
            analysis['category'] = "STARTUP_FAILURE"
            analysis['likely_causes'] = [
                "Executable not found",
                "Permission denied",
                "Invalid command syntax",
                "Missing dependencies",
                "Working directory doesn't exist",
            ]
            analysis['recommendations'] = [
                "Check if executable exists and is executable",
                "Verify working directory exists",
                "Check command syntax",
                "Review stderr output for error messages",
            ]
        elif exit_code == 1:
            analysis['meaning'] = "General error"
            analysis['category'] = "RUNTIME_ERROR"
            analysis['likely_causes'] = [
                "Application error",
                "Invalid arguments",
                "Configuration error",
            ]
        elif exit_code == 2:
            analysis['meaning'] = "Misuse of shell command"
            analysis['category'] = "USAGE_ERROR"
        elif exit_code == 126:
            analysis['meaning'] = "Command cannot execute (permission problem)"
            analysis['category'] = "PERMISSION_ERROR"
            analysis['recommendations'] = ["Run: chmod +x <executable>"]
        elif exit_code == 127:
            analysis['meaning'] = "Command not found"
            analysis['category'] = "NOT_FOUND"
            analysis['recommendations'] = [
                "Check if command is in PATH",
                "Verify executable name is correct",
            ]
        elif exit_code == 128:
            analysis['meaning'] = "Invalid exit argument"
            analysis['category'] = "INVALID_EXIT"
        elif 129 <= exit_code <= 192:
            signal_num = exit_code - 128
            analysis['meaning'] = f"Terminated by signal {signal_num}"
            analysis['category'] = "SIGNAL"
            
            signal_names = {
                1: "SIGHUP (Hangup)",
                2: "SIGINT (Interrupt - Ctrl+C)",
                3: "SIGQUIT (Quit)",
                6: "SIGABRT (Abort)",
                9: "SIGKILL (Kill - cannot be caught)",
                11: "SIGSEGV (Segmentation fault)",
                13: "SIGPIPE (Broken pipe)",
                15: "SIGTERM (Termination)",
            }
            
            if signal_num in signal_names:
                analysis['meaning'] += f" - {signal_names[signal_num]}"
        elif exit_code == 255:
            analysis['meaning'] = "Exit status out of range"
            analysis['category'] = "OUT_OF_RANGE"
        else:
            analysis['meaning'] = f"Application-specific error code {exit_code}"
            analysis['category'] = "APPLICATION_ERROR"
        
        return analysis
    
    def format_diagnostic_report(self, diagnostics: Dict, exit_code: Optional[int] = None) -> str:
        """Format diagnostic information as a readable report"""
        
        lines = []
        lines.append("=" * 70)
        lines.append("🔍 PROCESS DIAGNOSTIC REPORT")
        lines.append("=" * 70)
        lines.append("")
        
        # Command info
        lines.append(f"Command: {diagnostics['command']}")
        lines.append(f"Working Directory: {diagnostics['working_dir']}")
        lines.append("")
        
        # Executable info
        if diagnostics['executable_info']:
            lines.append("📦 Executable Information:")
            exe_info = diagnostics['executable_info']
            lines.append(f"  Name: {exe_info.get('name', 'unknown')}")
            lines.append(f"  Found: {'✅ Yes' if exe_info.get('found') else '❌ No'}")
            if exe_info.get('path'):
                lines.append(f"  Path: {exe_info['path']}")
                lines.append(f"  Is File: {'✅ Yes' if exe_info.get('is_file') else '❌ No'}")
                lines.append(f"  Executable: {'✅ Yes' if exe_info.get('is_executable') else '❌ No'}")
                lines.append(f"  Size: {exe_info.get('size', 0)} bytes")
            lines.append("")
        
        # Environment info
        if diagnostics['environment_info']:
            lines.append("🌍 Environment Information:")
            for key, value in diagnostics['environment_info'].items():
                lines.append(f"  {key}: {value}")
            lines.append("")
        
        # Issues
        if diagnostics['issues']:
            lines.append("❌ Issues Found:")
            for issue in diagnostics['issues']:
                lines.append(f"  • {issue}")
            lines.append("")
        
        # Warnings
        if diagnostics['warnings']:
            lines.append("⚠️  Warnings:")
            for warning in diagnostics['warnings']:
                lines.append(f"  • {warning}")
            lines.append("")
        
        # Recommendations
        if diagnostics['recommendations']:
            lines.append("💡 Recommendations:")
            for rec in diagnostics['recommendations']:
                lines.append(f"  • {rec}")
            lines.append("")
        
        # Exit code analysis
        if exit_code is not None:
            analysis = self.analyze_exit_code(exit_code)
            lines.append("🔢 Exit Code Analysis:")
            lines.append(f"  Code: {analysis['exit_code']}")
            lines.append(f"  Meaning: {analysis['meaning']}")
            lines.append(f"  Category: {analysis['category']}")
            
            if analysis['likely_causes']:
                lines.append("  Likely Causes:")
                for cause in analysis['likely_causes']:
                    lines.append(f"    • {cause}")
            
            if analysis['recommendations']:
                lines.append("  Recommendations:")
                for rec in analysis['recommendations']:
                    lines.append(f"    • {rec}")
            lines.append("")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)