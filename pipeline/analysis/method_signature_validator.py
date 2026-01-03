"""
Method Signature Validator

Validates that method calls match the actual method signatures.
Detects wrong number of arguments, missing methods, and signature mismatches.

Now uses shared SymbolTable for improved accuracy.
"""

import ast
import inspect
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from .symbol_table import SymbolTable

# Polytopic Integration Imports
from pipeline.messaging.message_bus import MessageBus, Message, MessageType, MessagePriority
from pipeline.pattern_recognition import PatternRecognitionSystem
from pipeline.correlation_engine import CorrelationEngine
from pipeline.analytics.optimizer import OptimizationEngine
from pipeline.adaptive_prompts import AdaptivePromptSystem
from pipeline.polytopic.dimensional_space import DimensionalSpace



@dataclass
class MethodSignatureError:
    """Represents a method signature validation error."""
    file: str
    line: int
    class_name: str
    method_name: str
    expected_args: int
    provided_args: int
    message: str
    severity: str


class MethodCollector(ast.NodeVisitor):
    """Collects all method definitions with their signatures."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.methods: Dict[Tuple[str, str], int] = {}  # (class_name, method_name) -> arg_count
        self.current_class = None
        
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
        self.validator_name = 'MethodSignatureValidator'

    def visit_ClassDef(self, node: ast.ClassDef):
        """Track current class."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
        
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Collect method signature."""
        if self.current_class:
            # Count arguments (excluding self)
            arg_count = len(node.args.args) - 1  # Subtract 'self'
            
            # Add defaults count
            if node.args.defaults:
                # Arguments with defaults are optional
                required_args = arg_count - len(node.args.defaults)
            else:
                required_args = arg_count
            
            # Store minimum required args
            self.methods[(self.current_class, node.name)] = required_args
        
        self.generic_visit(node)


class MethodCallChecker(ast.NodeVisitor):
    """Checks that method calls match signatures."""
    
    def __init__(self, filepath: Path, project_root: Path, all_methods: Dict[Tuple[str, str], int]):
        self.filepath = filepath
        self.project_root = project_root
        self.all_methods = all_methods
        self.errors: List[MethodSignatureError] = []
        self.variable_types: Dict[str, str] = {}  # variable -> class_name
        
    def visit_Assign(self, node: ast.Assign):
        """Track variable types from assignments."""
        # Simple type tracking: var = ClassName()
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                class_name = node.value.func.id
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.variable_types[target.id] = class_name
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Check method calls."""
        if isinstance(node.func, ast.Attribute):
            self._check_method_call(node)
        self.generic_visit(node)
    
    def _check_method_call(self, node: ast.Call):
        """Check if method call matches signature."""
        method_name = node.func.attr
        
        # Try to determine the class
        class_name = None
        if isinstance(node.func.value, ast.Name):
            var_name = node.func.value.id
            # Check if we know the type
            if var_name in self.variable_types:
                class_name = self.variable_types[var_name]
            # Check if it's self.something
            elif var_name == 'self':
                # Would need to track current class
                pass
        elif isinstance(node.func.value, ast.Attribute):
            # self.something.method() - get the attribute name
            if isinstance(node.func.value.value, ast.Name) and node.func.value.value.id == 'self':
                # This is self.attribute.method()
                attr_name = node.func.value.attr
                # Common patterns
                if 'manager' in attr_name.lower():
                    class_name = attr_name.title().replace('_', '') + 'Manager'
                elif 'engine' in attr_name.lower():
                    class_name = attr_name.title().replace('_', '') + 'Engine'
                elif 'analytics' in attr_name.lower():
                    class_name = 'AnalyticsIntegration'
                elif 'optimizer' in attr_name.lower():
                    class_name = 'PatternOptimizer'
        
        if not class_name:
            return
        
        # Check if we have signature info for this method
        key = (class_name, method_name)
        if key in self.all_methods:
            expected_args = self.all_methods[key]
            
            # Count provided arguments
            provided_args = len(node.args) + len(node.keywords)
            
            # Check if mismatch
            if provided_args < expected_args:
                self.errors.append(MethodSignatureError(
                    file=str(self.filepath.relative_to(self.project_root)),
                    line=node.lineno,
                    class_name=class_name,
                    method_name=method_name,
                    expected_args=expected_args,
                    provided_args=provided_args,
                    message=f"Method {class_name}.{method_name}() expects at least {expected_args} arguments, but {provided_args} were provided",
                    severity='critical'
                ))


class MethodSignatureValidator:
    """Validates that method calls match actual method signatures."""
    
    def __init__(self, project_root: str, symbol_table: Optional[SymbolTable] = None):
        self.project_root = Path(project_root)
        self.errors: List[MethodSignatureError] = []
        self.symbol_table = symbol_table
        self.all_methods: Dict[Tuple[str, str], int] = {}
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
        self.validator_name = 'MethodSignatureValidator'

        
    def validate_all(self) -> Dict:
        """
        Validate all method signatures in the project.
        
        Returns:
            Dict with validation results
        """
        self.errors = []
        
        # Use SymbolTable if available, otherwise collect methods
        if self.symbol_table:
            # Extract method signatures from SymbolTable
            for class_info in self.symbol_table.classes.values():
                if ':' in class_info.name:  # Skip qualified names
                    continue
                for method_name, method_info in class_info.methods.items():
                    key = (class_info.name, method_name)
                    self.all_methods[key] = method_info.min_args
        else:
            # Fallback: collect methods ourselves
            self._collect_methods()
        
        # Validate method calls
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            self._validate_file(py_file)
        
        
        
        
        # Build result dict first
        result = {
            'errors': [
                {
                    'file': e.file,
                    'line': e.line,
                    'class_name': e.class_name,
                    'method_name': e.method_name,
                    'expected_args': e.expected_args,
                    'provided_args': e.provided_args,
                    'message': e.message,
                    'severity': e.severity
                }
                for e in self.errors
            ],
            'total_errors': len(self.errors),
            'methods_found': len(self.all_methods),
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

    
    def _collect_methods(self):
        """Collect all method signatures in the project (fallback when no SymbolTable)."""
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                tree = ast.parse(source, filename=str(py_file))
                
                collector = MethodCollector(str(py_file))
                collector.visit(tree)
                
                # Merge methods from this file
                self.all_methods.update(collector.methods)
                
            except Exception as e:
                # Skip files that can't be parsed
                pass
    
    def _validate_file(self, filepath: Path):
        """Validate method calls in a single file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=str(filepath))
            
            checker = MethodCallChecker(filepath, self.project_root, self.all_methods)
            checker.visit(tree)
            
            self.errors.extend(checker.errors)
            
        except Exception as e:
            # Skip files that can't be parsed
            pass
    
    def _count_by_severity(self) -> Dict[str, int]:
        """Count errors by severity."""
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for error in self.errors:
            counts[error.severity] = counts.get(error.severity, 0) + 1
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

