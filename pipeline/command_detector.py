"""
Intelligent Command Detection System

Automatically detects the correct command to execute for a project by analyzing:
- Project structure (files, directories, configuration)
- Common patterns (package.json, requirements.txt, Makefile, etc.)
- Entry points (main.py, __main__.py, executable scripts)
- Build systems and frameworks
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import subprocess


class CommandDetector:
    """Detects the correct command to run for a project"""
    
    def __init__(self, project_path: str, logger: Optional[logging.Logger] = None):
        self.project_path = Path(project_path).resolve()
        self.logger = logger or logging.getLogger(__name__)
        
    def detect_command(self) -> Tuple[Optional[str], str]:
        """
        Detect the correct command to run the project.
        
        Returns:
            Tuple of (command, reason) where command is the detected command
            and reason explains why this command was chosen.
        """
        self.logger.info(f"Analyzing project structure at: {self.project_path}")
        
        # Check if project path exists
        if not self.project_path.exists():
            return None, f"Project path does not exist: {self.project_path}"
        
        # Try detection methods in priority order
        detectors = [
            self._detect_python_package,
            self._detect_python_script,
            self._detect_nodejs_project,
            self._detect_makefile_project,
            self._detect_docker_project,
            self._detect_shell_script,
            self._detect_executable_files,
        ]
        
        for detector in detectors:
            command, reason = detector()
            if command:
                self.logger.info(f"Detected command: {command}")
                self.logger.info(f"Reason: {reason}")
                return command, reason
        
        return None, "Could not detect appropriate command for this project"
    
    def _detect_python_package(self) -> Tuple[Optional[str], str]:
        """Detect Python package with __main__.py"""
        # Look for __main__.py in subdirectories
        for item in self.project_path.iterdir():
            if item.is_dir():
                main_file = item / "__main__.py"
                if main_file.exists():
                    return f"python -m {item.name}", f"Found Python package with __main__.py: {item.name}"
        
        # Check if current directory is a package
        main_file = self.project_path / "__main__.py"
        if main_file.exists():
            package_name = self.project_path.name
            return f"python -m {package_name}", f"Current directory is a Python package with __main__.py"
        
        return None, ""
    
    def _detect_python_script(self) -> Tuple[Optional[str], str]:
        """Detect Python scripts (main.py, run.py, app.py, etc.)"""
        common_names = [
            "main.py",
            "run.py", 
            "app.py",
            "start.py",
            "__main__.py",
            "server.py",
            "manage.py",  # Django
        ]
        
        for name in common_names:
            script = self.project_path / name
            if script.exists():
                return f"python {name}", f"Found Python entry point: {name}"
        
        # Look for any .py file with if __name__ == "__main__"
        py_files = list(self.project_path.glob("*.py"))
        for py_file in py_files:
            try:
                content = py_file.read_text()
                if 'if __name__ == "__main__"' in content or "if __name__ == '__main__'" in content:
                    return f"python {py_file.name}", f"Found Python script with __main__ block: {py_file.name}"
            except Exception:
                continue
        
        return None, ""
    
    def _detect_nodejs_project(self) -> Tuple[Optional[str], str]:
        """Detect Node.js projects"""
        package_json = self.project_path / "package.json"
        if not package_json.exists():
            return None, ""
        
        try:
            with open(package_json) as f:
                package_data = json.load(f)
            
            # Check for start script
            scripts = package_data.get("scripts", {})
            if "start" in scripts:
                return "npm start", f"Found npm start script in package.json"
            
            # Check for dev script
            if "dev" in scripts:
                return "npm run dev", f"Found npm dev script in package.json"
            
            # Check for main entry point
            main = package_data.get("main")
            if main:
                return f"node {main}", f"Found main entry point in package.json: {main}"
            
        except Exception as e:
            self.logger.warning(f"Error parsing package.json: {e}")
        
        return None, ""
    
    def _detect_makefile_project(self) -> Tuple[Optional[str], str]:
        """Detect projects with Makefile"""
        makefile_names = ["Makefile", "makefile", "GNUmakefile"]
        
        for name in makefile_names:
            makefile = self.project_path / name
            if makefile.exists():
                # Try to find default target or 'run' target
                try:
                    content = makefile.read_text()
                    if "run:" in content:
                        return "make run", f"Found 'run' target in {name}"
                    if "start:" in content:
                        return "make start", f"Found 'start' target in {name}"
                    # Default to just 'make'
                    return "make", f"Found {name} (using default target)"
                except Exception:
                    return "make", f"Found {name}"
        
        return None, ""
    
    def _detect_docker_project(self) -> Tuple[Optional[str], str]:
        """Detect Docker projects"""
        dockerfile = self.project_path / "Dockerfile"
        docker_compose = self.project_path / "docker-compose.yml"
        
        if docker_compose.exists():
            return "docker-compose up", "Found docker-compose.yml"
        
        if dockerfile.exists():
            # Try to extract CMD from Dockerfile
            try:
                content = dockerfile.read_text()
                for line in content.split('\n'):
                    if line.strip().startswith('CMD'):
                        cmd = line.split('CMD', 1)[1].strip()
                        return f"docker build -t app . && docker run app", f"Found Dockerfile with CMD: {cmd}"
            except PermissionError:
                self.logger.warning(f"Permission denied reading Dockerfile at {dockerfile}")
            except Exception as e:
                self.logger.debug(f"Could not parse Dockerfile: {e}")
            return "docker build -t app . && docker run app", "Found Dockerfile"
        
        return None, ""
    
    def _detect_shell_script(self) -> Tuple[Optional[str], str]:
        """Detect shell scripts"""
        common_names = [
            "run.sh",
            "start.sh",
            "launch.sh",
            "execute.sh",
        ]
        
        for name in common_names:
            script = self.project_path / name
            if script.exists() and os.access(script, os.X_OK):
                return f"./{name}", f"Found executable shell script: {name}"
        
        return None, ""
    
    def _detect_executable_files(self) -> Tuple[Optional[str], str]:
        """Detect any executable files"""
        # Look for executable files in project root
        for item in self.project_path.iterdir():
            if item.is_file() and os.access(item, os.X_OK):
                # Skip common non-executable patterns
                if item.suffix in ['.txt', '.md', '.json', '.yml', '.yaml']:
                    continue
                return f"./{item.name}", f"Found executable file: {item.name}"
        
        return None, ""
    
    def get_project_info(self) -> Dict[str, any]:
        """Get detailed information about the project structure"""
        info = {
            "path": str(self.project_path),
            "exists": self.project_path.exists(),
            "is_directory": self.project_path.is_dir(),
            "files": [],
            "directories": [],
            "python_files": [],
            "config_files": [],
        }
        
        if not self.project_path.exists():
            return info
        
        try:
            for item in self.project_path.iterdir():
                if item.is_file():
                    info["files"].append(item.name)
                    if item.suffix == ".py":
                        info["python_files"].append(item.name)
                    if item.name in ["package.json", "requirements.txt", "setup.py", 
                                    "Makefile", "Dockerfile", "docker-compose.yml"]:
                        info["config_files"].append(item.name)
                elif item.is_dir() and not item.name.startswith('.'):
                    info["directories"].append(item.name)
        except Exception as e:
            self.logger.error(f"Error reading project directory: {e}")
        
        return info


def detect_command_for_project(project_path: str, logger: Optional[logging.Logger] = None) -> Tuple[Optional[str], str]:
    """
    Convenience function to detect command for a project.
    
    Args:
        project_path: Path to the project directory
        logger: Optional logger instance
    
    Returns:
        Tuple of (command, reason)
    """
    detector = CommandDetector(project_path, logger)
    return detector.detect_command()