"""
Method Existence Validator

Validates that methods exist on classes, checking parent and base classes.
Properly handles inheritance, stdlib classes, and function patterns.
Project-agnostic with configurable validation rules.

Now uses shared SymbolTable for improved accuracy.
"""

import ast
from typing import Dict, List, Set, Optional
from pathlib import Path
from dataclasses import dataclass

from .validation_config import ValidationConfig, get_project_root, detect_project_name
from .symbol_table import SymbolTable

# Polytopic Integration Imports
from pipeline.messaging.message_bus import MessageBus, Message, MessageType, MessagePriority
from pipeline.pattern_recognition import PatternRecognitionSystem
from pipeline.correlation_engine import CorrelationEngine
from pipeline.analytics.optimizer import OptimizationEngine
from pipeline.adaptive_prompts import AdaptivePromptSystem
from pipeline.polytopic.dimensional_space import DimensionalSpace



@dataclass
class MethodExistenceError:
    """Represents a method existence validation error."""
    file: str
    line: int
    class_name: str
    method_name: str
    message: str
    severity: str


class MethodExistenceValidator:
    """Validates method existence with inheritance and stdlib awareness."""
    
    def __init__(self, project_root: str, config_file: Optional[str] = None, symbol_table: Optional[SymbolTable] = None):
        self.project_root = Path(project_root)
        self.errors: List[MethodExistenceError] = []
        self.symbol_table = symbol_table
        
        # Load configuration (project-agnostic)
        config_path = Path(config_file) if config_file else None
        self.config = ValidationConfig(self.project_root, config_path)
        
        # Detect project name dynamically
        self.project_name = detect_project_name(self.project_root)
        
        # Track class definitions and their methods with file paths
        # Key format: "filepath:classname" to handle duplicate class names
        self.class_methods: Dict[str, Set[str]] = {}
        self.class_parents: Dict[str, List[str]] = {}
        
        # Track which files define which classes (for duplicate detection)
        self.class_locations: Dict[str, List[str]] = {}  # classname -> [filepaths]
        
        # Polytopic Integration
        self.message_bus = MessageBus()
        self.pattern_recognition = PatternRecognitionSystem(self.project_root)
        self.correlation_engine = CorrelationEngine()
        self.optimizer = OptimizationEngine()
        self.adaptive_prompts = AdaptivePromptSystem(
            self.project_root,
            self.pattern_recognition
        )
        self.dimensional_space = DimensionalSpace()
        
        # Validation tracking
        self.validation_count = 0
        self.validator_name = 'MethodExistenceValidator'

    def validate_all(self) -> Dict:
        """
        Validate all method existence in the project.
        
        Returns:
            Dict with validation results
        """
        self.errors = []
        
        # Use SymbolTable if available, otherwise collect ourselves
        if self.symbol_table:
            # Extract class methods from SymbolTable
            for class_info in self.symbol_table.classes.values():
                if ':' in class_info.name:  # Skip qualified names
                    continue
                
                # Store methods
                self.class_methods[class_info.name] = set(class_info.methods.keys())
                
                # Store parent classes
                self.class_parents[class_info.name] = class_info.parent_classes
                
                # Track locations
                if class_info.name not in self.class_locations:
                    self.class_locations[class_info.name] = []
                self.class_locations[class_info.name].append(class_info.file)
        else:
            # Fallback: collect class definitions ourselves
            self._collect_class_definitions()
        
        # Detect duplicate class names
        duplicates = self._detect_duplicate_classes()
        
        # Validate method calls
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            self._validate_file(py_file)
        
        
        
        
        # Build result dict first
        result = {
            'errors': [
                {
                    'file': err.file,
                    'line': err.line,
                    'class_name': err.class_name,
                    'method_name': err.method_name,
                    'message': err.message,
                    'severity': err.severity
                }
                for err in self.errors
            ],
            'total_errors': len(self.errors),
            'classes_analyzed': len(self.class_methods),
            'duplicate_classes': duplicates,
            'by_severity': self._count_by_severity()
        }
        
# Polytopic Integration: Record patterns and optimize
        self.validation_count += 1
        self._record_validation_pattern(self.errors if hasattr(self, 'errors') else [])
        self._optimize_validation(result)
        
        # Publish validation completed event
        self._publish_validation_event('validation_completed', {
            'total_errors': result.get('total_errors', 0),
            'validation_count': self.validation_count
        })
        
        
        return result

    
    def _detect_duplicate_classes(self) -> Dict[str, List[str]]:
        """Detect classes defined in multiple files."""
        duplicates = {}
        for class_name, locations in self.class_locations.items():
            if len(locations) > 1:
                duplicates[class_name] = locations
        return duplicates
    
    def _collect_class_definitions(self):
        """Collect all class definitions and their methods."""
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                tree = ast.parse(source)
                
                # Get relative path for tracking
                rel_path = str(py_file.relative_to(self.project_root))
                
                # Use proper visitor pattern instead of ast.walk
                for node in tree.body:
                    self._collect_from_node(node, rel_path)
                        
            except Exception:
                continue
    
    def _collect_from_node(self, node, filepath: str):
        """Recursively collect class definitions from AST nodes."""
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            
            # Create unique key with filepath
            class_key = f"{filepath}:{class_name}"
            
            # Collect methods
            methods = set()
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.add(item.name)
                elif isinstance(item, ast.ClassDef):
                    # Nested class - recurse
                    self._collect_from_node(item, filepath)
            
            # Store with filepath key
            self.class_methods[class_key] = methods
            
            # Also store simple name for backward compatibility
            # But track all locations for duplicate detection
            if class_name not in self.class_locations:
                self.class_locations[class_name] = []
            self.class_locations[class_name].append(filepath)
            
            # For simple lookups, use the most recent definition
            # (This maintains backward compatibility while tracking duplicates)
            self.class_methods[class_name] = methods
            
            # Collect parent classes
            parents = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    parents.append(base.id)
                elif isinstance(base, ast.Attribute):
                    # Handle ast.NodeVisitor, etc.
                    if isinstance(base.value, ast.Name):
                        parents.append(f"{base.value.id}.{base.attr}")
            
            self.class_parents[class_name] = parents
            self.class_parents[class_key] = parents
            
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Check for nested classes in functions
            for item in node.body:
                if isinstance(item, ast.ClassDef):
                    self._collect_from_node(item, filepath)
    
    def _validate_file(self, filepath: Path):
        """Validate method calls in a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            # Use visitor to track types and validate
            visitor = MethodCallVisitor(filepath, self.project_root, self)
            visitor.visit(tree)
            
            self.errors.extend(visitor.errors)
                        
        except Exception:
            pass
    
    def _method_exists(self, class_name: str, method_name: str) -> bool:
        """Check if method exists on class or any of its parents."""
        # Check direct class
        if class_name in self.class_methods:
            if method_name in self.class_methods[class_name]:
                return True
        
        # Check parent classes
        if class_name in self.class_parents:
            for parent in self.class_parents[class_name]:
                # Check known base classes
                known_bases = self.config.get_known_base_classes()
                if parent in known_bases:
                    if method_name in known_bases[parent]:
                        return True
                
                # Recursively check parent
                if self._method_exists(parent, method_name):
                    return True
        
        return False
    
    def _count_by_severity(self) -> Dict[str, int]:
        """Count errors by severity."""
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for err in self.errors:
            counts[err.severity] += 1
        return counts


    
    def _publish_validation_event(self, event_type: str, payload: dict):
        """Publish validation events using existing message types."""
        message_type_map = {
            'validation_started': MessageType.SYSTEM_INFO,
            'validation_completed': MessageType.SYSTEM_INFO,
            'validation_error': MessageType.SYSTEM_WARNING,
            'validation_critical': MessageType.SYSTEM_ALERT,
            'validation_insight': MessageType.SYSTEM_INFO,
        }
        
        message_type = message_type_map.get(event_type, MessageType.SYSTEM_INFO)
        
        message = Message(
            sender=self.validator_name,
            recipient='ALL',
            message_type=message_type,
            priority=MessagePriority.NORMAL,
            payload={
                'event': event_type,
                'validator': self.validator_name,
                **payload
            }
        )
        
        self.message_bus.publish(message)
    
    def _record_validation_pattern(self, errors: list):
        """Record validation patterns for learning."""
        if not errors:
            return
        
        # Record execution data
        execution_data = {
            'phase': 'validation',
            'tool': self.validator_name,
            'success': len([e for e in errors if self._get_severity(e) == 'high']) == 0,
            'error_count': len(errors),
            'validation_count': self.validation_count
        }
        
        self.pattern_recognition.record_execution(execution_data)
        
        # Add findings to correlation engine
        for error in errors:
            component = self._get_error_file(error)
            finding = {
                'type': f'{self.validator_name}_error',
                'error_type': self._get_error_type(error),
                'severity': self._get_severity(error),
                'message': self._get_error_message(error)
            }
            
            self.correlation_engine.add_finding(component, finding)
        
        # Find correlations
        correlations = self.correlation_engine.correlate()
        
        if correlations:
            self._publish_validation_event('validation_insight', {
                'type': 'validation_correlations',
                'correlations': correlations
            })
    
    def _optimize_validation(self, result: dict):
        """Optimize validation based on results."""
        # Record quality metrics
        self.optimizer.record_quality_metric(
            f'{self.validator_name}_errors',
            result.get('total_errors', 0)
        )
        
        if 'by_severity' in result:
            self.optimizer.record_quality_metric(
                f'{self.validator_name}_high_severity',
                result.get('by_severity', {}).get('high', 0)
            )
    
    def _get_error_file(self, error):
        """Extract file path from error."""
        if isinstance(error, dict):
            return error.get('file', 'unknown')
        elif hasattr(error, 'file'):
            return error.file
        elif hasattr(error, 'filepath'):
            return error.filepath
        return 'unknown'
    
    def _get_error_type(self, error):
        """Extract error type from error."""
        if isinstance(error, dict):
            return error.get('error_type', 'unknown')
        elif hasattr(error, 'error_type'):
            return error.error_type
        elif hasattr(error, 'type'):
            return error.type
        return 'unknown'
    
    def _get_severity(self, error):
        """Extract severity from error."""
        if isinstance(error, dict):
            return error.get('severity', 'medium')
        elif hasattr(error, 'severity'):
            return error.severity
        return 'medium'
    
    def _get_error_message(self, error):
        """Extract message from error."""
        if isinstance(error, dict):
            return error.get('message', '')
        elif hasattr(error, 'message'):
            return error.message
        elif hasattr(error, 'msg'):
            return error.msg
        return str(error)


class MethodCallVisitor(ast.NodeVisitor):
    """Visitor to track variable types and validate method calls."""
    
    def __init__(self, filepath: Path, project_root: Path, validator: MethodExistenceValidator):
        self.filepath = filepath
        self.project_root = project_root
        self.validator = validator
        self.var_types: Dict[str, str] = {}  # var_name -> class_name
        self.var_type_sources: Dict[str, str] = {}  # var_name -> source_file
        self.imports: Dict[str, str] = {}  # class_name -> imported_from
        self.errors: List[MethodExistenceError] = []
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track imports to resolve class sources."""
        if node.module:
            for alias in node.names:
                class_name = alias.asname if alias.asname else alias.name
                
                # Handle relative imports
                module_path = node.module
                if node.level > 0:
                    # Relative import (e.g., from .analysis.complexity)
                    # Get current file's directory
                    current_dir = str(self.filepath.parent.relative_to(self.project_root))
                    
                    # Go up 'level' directories
                    parts = current_dir.split('/')
                    for _ in range(node.level - 1):
                        if parts:
                            parts.pop()
                    
                    # Add module path
                    if parts:
                        module_path = '/'.join(parts) + '/' + module_path.replace('.', '/')
                    else:
                        module_path = module_path.replace('.', '/')
                else:
                    # Absolute import (e.g., from myproject.pipeline.tool_validator)
                    # Remove project name prefix if present
                    if self.validator.project_name and module_path.startswith(f'{self.validator.project_name}.'):
                        # Remove project name prefix
                        prefix_len = len(self.validator.project_name) + 1
                        module_path = module_path[prefix_len:]
                    module_path = module_path.replace('.', '/')
                
                self.imports[class_name] = module_path
        
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign):
        """Track variable assignments to class instances."""
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                func_name = node.value.func.id
                # Only track if it looks like a class (starts with uppercase)
                # AND exists in our class registry
                if func_name and func_name[0].isupper() and func_name in self.validator.class_methods:
                    for target in node.targets:
                        # Track simple variable assignments (e.g., x = MyClass())
                        if isinstance(target, ast.Name):
                            self.var_types[target.id] = func_name
                            # Track source file
                            if func_name in self.imports:
                                # Use imported source
                                self.var_type_sources[target.id] = self.imports[func_name]
                            else:
                                # No import found - assume local definition (same file)
                                rel_path = str(self.filepath.relative_to(self.project_root))
                                self.var_type_sources[target.id] = rel_path.replace('.py', '')
                        
                        # Track instance variable assignments (e.g., self.x = MyClass())
                        elif isinstance(target, ast.Attribute):
                            if isinstance(target.value, ast.Name) and target.value.id == 'self':
                                # Track self.attribute = MyClass()
                                var_key = f"self.{target.attr}"
                                self.var_types[var_key] = func_name
                                # Track source file
                                if func_name in self.imports:
                                    self.var_type_sources[var_key] = self.imports[func_name]
                                else:
                                    rel_path = str(self.filepath.relative_to(self.project_root))
                                    self.var_type_sources[var_key] = rel_path.replace('.py', '')
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Check method calls."""
        if isinstance(node.func, ast.Attribute):
            self._check_method_call(node)
        
        self.generic_visit(node)
    
    def _check_method_call(self, node: ast.Call):
        """Check if a method exists on a class (including parent classes)."""
        # Handle both simple variables (x.method()) and self attributes (self.x.method())
        var_name = None
        method_name = node.func.attr
        
        if isinstance(node.func.value, ast.Name):
            # Simple variable: x.method()
            var_name = node.func.value.id
        elif isinstance(node.func.value, ast.Attribute):
            # Attribute access: self.x.method()
            if isinstance(node.func.value.value, ast.Name) and node.func.value.value.id == 'self':
                var_name = f"self.{node.func.value.attr}"
            else:
                # Other attribute access (e.g., obj.attr.method()) - skip for now
                return
        else:
            return
        
        # Skip common safe patterns (dict/list/string methods)
        safe_methods = {
            'get', 'items', 'keys', 'values', 'append', 'extend', 'pop',
            'split', 'join', 'strip', 'replace', 'format', 'splitlines',
            'lower', 'upper', 'startswith', 'endswith', 'find', 'index',
            'read', 'write', 'close', 'open', 'exists', 'mkdir', 'rmdir',
            'read_text', 'write_text', 'unlink', 'rename', 'copy',
        }
        
        if method_name in safe_methods:
            return
        
        # Get class name
        if var_name not in self.var_types:
            # Unknown type - skip validation
            return
        
        class_name = self.var_types[var_name]
        
        # Skip standard library classes
        if self.validator.config.is_stdlib_class(class_name):
            return
        
        # Skip function patterns (not actual classes)
        if self.validator.config.is_known_function(class_name):
            return
        
        # Check if method exists, preferring the imported source
        source_file = self.var_type_sources.get(var_name)
        if source_file:
            # Try to find the class from the specific source file
            class_key = f"{source_file}.py:{class_name}"
            if class_key in self.validator.class_methods:
                if method_name in self.validator.class_methods[class_key]:
                    return  # Method exists in the correct source
        
        # Fall back to general check
        if self.validator._method_exists(class_name, method_name):
            return
        
        # Method doesn't exist - report error
        self.errors.append(MethodExistenceError(
            file=str(self.filepath.relative_to(self.project_root)),
            line=node.lineno,
            class_name=class_name,
            method_name=method_name,
            message=f"Method '{method_name}' does not exist on class '{class_name}'",
            severity='critical'
        ))