"""
Project-agnostic validation configuration.

This module provides default configurations for code validators
and allows projects to customize validation behavior.
"""

import json
from pathlib import Path
from typing import Dict, Set, Optional


class ValidationConfig:
    """Configuration for code validators."""
    
    def __init__(self, project_root: Path, config_file: Optional[Path] = None):
        """
        Initialize validation configuration.
        
        Args:
            project_root: Root directory of the project
            config_file: Optional path to custom config file
        """
        self.project_root = project_root
        self.config_file = config_file
        
        # Load default configuration
        self._load_defaults()
        
        # Override with custom config if provided
        if config_file and config_file.exists():
            self._load_custom_config(config_file)
        else:
            # Try to find config in project root
            default_config = project_root / '.validation_config.json'
            if default_config.exists():
                self._load_custom_config(default_config)
    
    def _load_defaults(self):
        """Load default configuration values."""
        
        # Known base classes and their methods
        self.known_base_classes = {
            'ast.NodeVisitor': {'visit', 'generic_visit'},
            'NodeVisitor': {'visit', 'generic_visit'},
            'ABC': {'__init__'},
            'object': {'__init__', '__str__', '__repr__'},
        }
        
        # Known standard library classes (skip validation for these)
        self.stdlib_classes = {
            # pathlib
            'Path', 'PosixPath', 'WindowsPath', 'PurePath',
            # builtins
            'dict', 'list', 'set', 'tuple', 'str', 'int', 'float', 'bool',
            'frozenset', 'bytes', 'bytearray', 'memoryview', 'range',
            'object', 'type', 'super', 'property', 'staticmethod', 'classmethod',
            # collections
            'defaultdict', 'OrderedDict', 'Counter', 'deque', 'ChainMap',
            'namedtuple',
            # datetime
            'datetime', 'date', 'time', 'timedelta', 'timezone',
            # threading
            'Thread', 'Lock', 'RLock', 'Event', 'Queue', 'Semaphore',
            # logging
            'Logger', 'Handler', 'Formatter',
            # http
            'HTTPResponse', 'HTTPConnection', 'HTTPSConnection',
            # socket
            'socket',
            # io
            'StringIO', 'BytesIO', 'TextIOWrapper',
            # re
            'Pattern', 'Match',
            # json
            'JSONEncoder', 'JSONDecoder',
            # pathlib
            'PurePosixPath', 'PureWindowsPath',
        }
        
        # Known function patterns that return objects (not classes)
        self.function_patterns = {
            'getattr', 'hasattr', 'isinstance', 'type', 'len', 'range',
            'open', 'print', 'input', 'enumerate', 'zip', 'map', 'filter',
            'sorted', 'reversed', 'sum', 'min', 'max', 'abs', 'round',
            'all', 'any', 'iter', 'next', 'dir', 'vars', 'locals', 'globals',
        }
        
        # Standard library functions with flexible signatures
        self.stdlib_functions = {
            # HTTP/parsing
            'parse', 'get', 'post', 'put', 'delete', 'patch',
            # String methods
            'format', 'join', 'split', 'replace', 'strip', 'lstrip', 'rstrip',
            'upper', 'lower', 'capitalize', 'title', 'startswith', 'endswith',
            # List methods
            'append', 'extend', 'insert', 'remove', 'pop', 'clear', 'sort',
            'reverse', 'count', 'index', 'copy',
            # Dict methods
            'update', 'setdefault', 'fromkeys', 'keys', 'values', 'items',
            'get', 'pop', 'popitem', 'clear',
            # File methods
            'read', 'write', 'readline', 'readlines', 'writelines',
            'open', 'close', 'flush', 'seek', 'tell',
            # Logging methods
            'error', 'warning', 'info', 'debug', 'critical', 'log',
            'exception', 'addHandler', 'removeHandler',
            # Path methods
            'exists', 'is_file', 'is_dir', 'mkdir', 'rmdir', 'unlink',
            'rename', 'resolve', 'absolute', 'relative_to',
        }
        
        # Project-specific patterns (can be overridden)
        self.project_patterns = {
            'base_classes': {},  # Project-specific base classes
            'custom_functions': set(),  # Project-specific functions
        }
    
    def _load_custom_config(self, config_file: Path):
        """
        Load custom configuration from JSON file.
        
        Args:
            config_file: Path to JSON config file
        """
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Merge known_base_classes
            if 'known_base_classes' in config:
                for cls, methods in config['known_base_classes'].items():
                    self.known_base_classes[cls] = set(methods)
            
            # Merge stdlib_classes
            if 'stdlib_classes' in config:
                self.stdlib_classes.update(config['stdlib_classes'])
            
            # Merge function_patterns
            if 'function_patterns' in config:
                self.function_patterns.update(config['function_patterns'])
            
            # Merge stdlib_functions
            if 'stdlib_functions' in config:
                self.stdlib_functions.update(config['stdlib_functions'])
            
            # Load project patterns
            if 'project_patterns' in config:
                patterns = config['project_patterns']
                if 'base_classes' in patterns:
                    for cls, methods in patterns['base_classes'].items():
                        self.project_patterns['base_classes'][cls] = set(methods)
                if 'custom_functions' in patterns:
                    self.project_patterns['custom_functions'].update(
                        patterns['custom_functions']
                    )
        
        except Exception as e:
            print(f"Warning: Failed to load custom config from {config_file}: {e}")
    
    def get_known_base_classes(self) -> Dict[str, Set[str]]:
        """Get all known base classes (default + project-specific)."""
        result = dict(self.known_base_classes)
        result.update(self.project_patterns['base_classes'])
        return result
    
    def get_stdlib_classes(self) -> Set[str]:
        """Get all standard library classes."""
        return self.stdlib_classes
    
    def get_function_patterns(self) -> Set[str]:
        """Get all known function patterns."""
        result = set(self.function_patterns)
        result.update(self.project_patterns['custom_functions'])
        return result
    
    def get_stdlib_functions(self) -> Set[str]:
        """Get all standard library functions."""
        return self.stdlib_functions
    
    def is_stdlib_class(self, class_name: str) -> bool:
        """Check if a class is from standard library."""
        return class_name in self.stdlib_classes
    
    def is_known_function(self, func_name: str) -> bool:
        """Check if a function is a known pattern."""
        return (func_name in self.function_patterns or 
                func_name in self.project_patterns['custom_functions'])
    
    def save_example_config(self, output_path: Path):
        """
        Save an example configuration file.
        
        Args:
            output_path: Path where to save the example config
        """
        example = {
            "known_base_classes": {
                "CustomBaseClass": ["method1", "method2"],
                "AnotherBase": ["execute", "validate"]
            },
            "stdlib_classes": [
                "CustomClass1",
                "CustomClass2"
            ],
            "function_patterns": [
                "custom_function1",
                "custom_function2"
            ],
            "stdlib_functions": [
                "custom_stdlib_func1",
                "custom_stdlib_func2"
            ],
            "project_patterns": {
                "base_classes": {
                    "ProjectBase": ["run", "stop"]
                },
                "custom_functions": [
                    "project_specific_func"
                ]
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(example, f, indent=2)


def get_project_root(start_path: Path) -> Path:
    """
    Detect project root by looking for common project markers.
    
    Args:
        start_path: Path to start searching from
        
    Returns:
        Path to project root
    """
    current = start_path.resolve()
    
    # Look for common project markers
    markers = [
        'setup.py',
        'pyproject.toml',
        'setup.cfg',
        'requirements.txt',
        '.git',
        'Pipfile',
        'poetry.lock',
    ]
    
    while current != current.parent:
        for marker in markers:
            if (current / marker).exists():
                return current
        current = current.parent
    
    # If no marker found, return the start path
    return start_path


def detect_project_name(project_root: Path) -> Optional[str]:
    """
    Detect the project name from common sources.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Project name if detected, None otherwise
    """
    # Try setup.py
    setup_py = project_root / 'setup.py'
    if setup_py.exists():
        try:
            content = setup_py.read_text()
            # Simple regex to find name= in setup()
            import re
            match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
        except Exception:
            pass
    
    # Try pyproject.toml
    pyproject = project_root / 'pyproject.toml'
    if pyproject.exists():
        try:
            content = pyproject.read_text()
            import re
            match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
        except Exception:
            pass
    
    # Fall back to directory name
    return project_root.name