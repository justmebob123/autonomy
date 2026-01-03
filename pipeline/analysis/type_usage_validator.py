"""
Type Usage Validator

Validates that objects are used according to their types with proper type inference.
Detects using dict methods on dataclasses, accessing attributes on dicts, etc.
Project-agnostic with configurable validation rules.

Now uses shared SymbolTable for improved accuracy.
"""

import ast
from typing import Dict, List, Set, Optional
from pathlib import Path
from dataclasses import dataclass

from .validation_config import ValidationConfig
from .symbol_table import SymbolTable

# Polytopic Integration Imports
from pipeline.messaging.message_bus import MessageBus, Message, MessageType, MessagePriority
from pipeline.pattern_recognition import PatternRecognitionSystem
from pipeline.correlation_engine import CorrelationEngine
from pipeline.analytics.optimizer import OptimizationEngine
from pipeline.adaptive_prompts import AdaptivePromptSystem
from pipeline.polytopic.dimensional_space import DimensionalSpace



@dataclass
class TypeUsageError:
    """Represents a type usage validation error."""
    file: str
    line: int
    variable: str
    actual_type: str
    attempted_operation: str
    message: str
    severity: str


@dataclass
class LegacyTypeInfo:
    """Information about a variable's type (legacy - for backward compatibility)."""
    type_name: str
    is_dataclass: bool
    is_dict: bool
    is_list: bool
    is_string: bool
    attributes: Dict[str, 'LegacyTypeInfo'] = None
    
    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


class TypeTracker(ast.NodeVisitor):
    """
    Tracks variable types through code with proper type inference.
    Handles assignments, function returns, loops, and attribute access.
    """
    
    def __init__(self, source: str, dataclasses: Set[str], filepath: str):
        self.source = source
        self.dataclasses = dataclasses
        self.filepath = filepath
        
        # Symbol tables for different scopes
        self.global_types: Dict[str, TypeInfo] = {}
        self.local_types: Dict[str, TypeInfo] = {}
        self.function_returns: Dict[str, TypeInfo] = {}
        
        # Dataclass attribute types
        self.dataclass_attributes: Dict[str, Dict[str, TypeInfo]] = {}
        
        # Track current scope
        self.current_function = None
        
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
        self.validator_name = 'TypeUsageValidator'

    def get_type(self, var_name: str) -> Optional[LegacyTypeInfo]:
        """Get type of a variable, checking local then global scope."""
        if var_name in self.local_types:
            return self.local_types[var_name]
        if var_name in self.global_types:
            return self.global_types[var_name]
        return None
    
    def set_type(self, var_name: str, type_info: LegacyTypeInfo):
        """Set type of a variable in current scope."""
        if self.current_function:
            self.local_types[var_name] = type_info
        else:
            self.global_types[var_name] = type_info
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Track dataclass attributes."""
        is_dataclass = any(
            isinstance(d, ast.Name) and d.id == 'dataclass'
            for d in node.decorator_list
        )
        
        if is_dataclass:
            attributes = {}
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    attr_name = item.target.id
                    attr_type = self._get_annotation_type(item.annotation)
                    attributes[attr_name] = attr_type
            
            self.dataclass_attributes[node.name] = attributes
        
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Track function and analyze return types."""
        old_function = self.current_function
        old_local_types = self.local_types.copy()
        
        self.current_function = node.name
        
        # Track parameter types
        for arg in node.args.args:
            if arg.annotation:
                param_type = self._get_annotation_type(arg.annotation)
                self.set_type(arg.arg, param_type)
        
        # Analyze function body
        self.generic_visit(node)
        
        # Track return type
        if node.returns:
            return_type = self._get_annotation_type(node.returns)
            self.function_returns[node.name] = return_type
        
        # Restore scope
        self.current_function = old_function
        self.local_types = old_local_types
    
    def visit_Assign(self, node: ast.Assign):
        """Track variable assignments."""
        # Get type from value
        value_type = self._infer_type(node.value)
        
        # Assign to all targets
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.set_type(target.id, value_type)
            elif isinstance(target, ast.Tuple):
                # Handle tuple unpacking
                if isinstance(node.value, ast.Tuple):
                    for t, v in zip(target.elts, node.value.elts):
                        if isinstance(t, ast.Name):
                            elem_type = self._infer_type(v)
                            self.set_type(t.id, elem_type)
        
        self.generic_visit(node)
    
    def visit_For(self, node: ast.For):
        """Track loop variable types."""
        # Infer type of iterable
        iter_type = self._infer_type(node.iter)
        
        # Infer type of loop variable
        if isinstance(node.target, ast.Name):
            loop_var_type = self._infer_element_type(iter_type)
            self.set_type(node.target.id, loop_var_type)
        
        self.generic_visit(node)
    
    def _infer_type(self, node: ast.AST) -> LegacyTypeInfo:
        """Infer type from an AST node."""
        # Direct instantiation: ClassName()
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                class_name = node.func.id
                return LegacyTypeInfo(
                    type_name=class_name,
                    is_dataclass=class_name in self.dataclasses,
                    is_dict=False,
                    is_list=False,
                    is_string=False
                )
        
        # Function call: func()
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                # Method call: obj.method()
                if isinstance(node.func.value, ast.Name):
                    obj_name = node.func.value.id
                    method_name = node.func.attr
                    obj_type = self.get_type(obj_name)
                    
                    # Check if method returns known type
                    if obj_type and method_name in self.function_returns:
                        return self.function_returns[method_name]
            elif isinstance(node.func, ast.Name):
                # Function call: func()
                func_name = node.func.id
                if func_name in self.function_returns:
                    return self.function_returns[func_name]
        
        # Dictionary literal: {}
        if isinstance(node, ast.Dict):
            return LegacyTypeInfo(
                type_name='dict',
                is_dataclass=False,
                is_dict=True,
                is_list=False,
                is_string=False
            )
        
        # List literal: []
        if isinstance(node, ast.List):
            return LegacyTypeInfo(
                type_name='list',
                is_dataclass=False,
                is_dict=False,
                is_list=True,
                is_string=False
            )
        
        # String literal: "..."
        if isinstance(node, (ast.Str, ast.Constant)) and isinstance(getattr(node, 'value', None), str):
            return LegacyTypeInfo(
                type_name='str',
                is_dataclass=False,
                is_dict=False,
                is_list=False,
                is_string=True
            )
        
        # Variable reference
        if isinstance(node, ast.Name):
            var_type = self.get_type(node.id)
            if var_type:
                return var_type
        
        # Attribute access: obj.attr
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                obj_name = node.value.id
                attr_name = node.attr
                obj_type = self.get_type(obj_name)
                
                if obj_type and obj_type.is_dataclass:
                    # Get attribute type from dataclass
                    if obj_type.type_name in self.dataclass_attributes:
                        attrs = self.dataclass_attributes[obj_type.type_name]
                        if attr_name in attrs:
                            return attrs[attr_name]
        
        # Unknown type
        return LegacyTypeInfo(
            type_name='unknown',
            is_dataclass=False,
            is_dict=False,
            is_list=False,
            is_string=False
        )
    
    def _infer_element_type(self, container_type: LegacyTypeInfo) -> LegacyTypeInfo:
        """Infer type of elements in a container."""
        if container_type.is_list:
            # For now, assume unknown element type
            # Could be enhanced with more sophisticated analysis
            return LegacyTypeInfo(
                type_name='unknown',
                is_dataclass=False,
                is_dict=False,
                is_list=False,
                is_string=False
            )
        
        return LegacyTypeInfo(
            type_name='unknown',
            is_dataclass=False,
            is_dict=False,
            is_list=False,
            is_string=False
        )
    
    def _get_annotation_type(self, annotation: ast.AST) -> LegacyTypeInfo:
        """Get type from type annotation."""
        if isinstance(annotation, ast.Name):
            type_name = annotation.id
            return LegacyTypeInfo(
                type_name=type_name,
                is_dataclass=type_name in self.dataclasses,
                is_dict=type_name in ('dict', 'Dict'),
                is_list=type_name in ('list', 'List'),
                is_string=type_name == 'str',
            )
        
        if isinstance(annotation, ast.Subscript):
            # Handle Dict[str, int], List[str], etc.
            if isinstance(annotation.value, ast.Name):
                type_name = annotation.value.id
                return LegacyTypeInfo(
                    type_name=type_name,
                    is_dataclass=False,
                    is_dict=type_name in ('Dict', 'dict'),
                    is_list=type_name in ('List', 'list'),
                    is_string=False,
                )
        
        return LegacyTypeInfo(
            type_name='unknown',
            is_dataclass=False,
            is_dict=False,
            is_list=False,
            is_string=False
        )


class TypeUsageChecker(ast.NodeVisitor):
    """Checks type usage with enhanced type information."""
    
    def __init__(self, filepath: Path, project_root: Path, tracker: TypeTracker, dataclasses: Set[str]):
        self.filepath = filepath
        self.project_root = project_root
        self.tracker = tracker
        self.dataclasses = dataclasses
        self.errors: List[TypeUsageError] = []
    
    def visit_Call(self, node: ast.Call):
        """Check method calls for type mismatches."""
        if isinstance(node.func, ast.Attribute):
            self._check_method_call(node)
        self.generic_visit(node)
    
    def _check_method_call(self, node: ast.Call):
        """Check if method call is valid for the object's type."""
        if not isinstance(node.func.value, ast.Name):
            return
        
        var_name = node.func.value.id
        method_name = node.func.attr
        
        # Get type information from tracker
        var_type = self.tracker.get_type(var_name)
        
        if not var_type:
            # Unknown type - skip validation
            return
        
        # Dict methods that shouldn't be used on dataclasses
        dict_methods = {'get', 'items', 'keys', 'values', 'pop', 'update', 'setdefault'}
        
        # Only report error if we're CERTAIN it's a dataclass (not a dict)
        if var_type.is_dataclass and not var_type.is_dict and method_name in dict_methods:
            self.errors.append(TypeUsageError(
                file=str(self.filepath.relative_to(self.project_root)),
                line=node.lineno,
                variable=var_name,
                actual_type=f"dataclass {var_type.type_name}",
                attempted_operation=f".{method_name}()",
                message=f"Cannot use dict method '.{method_name}()' on dataclass {var_type.type_name}. Use attribute access or asdict() instead.",
                severity='critical'
            ))


class TypeUsageValidator:
    """Validates that objects are used according to their types with proper type inference."""
    
    def __init__(self, project_root: str, config_file: Optional[str] = None, symbol_table: Optional[SymbolTable] = None):
        self.project_root = Path(project_root)
        self.errors: List[TypeUsageError] = []
        self.symbol_table = symbol_table
        self.dataclasses: Set[str] = set()
        self.regular_classes: Set[str] = set()
        
        # Load configuration (project-agnostic)
        config_path = Path(config_file) if config_file else None
        self.config = ValidationConfig(self.project_root, config_path)
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
        self.validator_name = 'TypeUsageValidator'

        
    def validate_all(self) -> Dict:
        """
        Validate all type usage in the project.
        
        Returns:
            Dict with validation results
        """
        self.errors = []
        
        # Use SymbolTable if available, otherwise collect ourselves
        if self.symbol_table:
            # Extract class types from SymbolTable
            for class_info in self.symbol_table.classes.values():
                if ':' in class_info.name:  # Skip qualified names
                    continue
                
                if class_info.is_dataclass:
                    self.dataclasses.add(class_info.name)
                else:
                    self.regular_classes.add(class_info.name)
        else:
            # Fallback: identify dataclasses and regular classes ourselves
            self._collect_class_types()
        
        # Validate type usage with enhanced tracking
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
                    'variable': err.variable,
                    'actual_type': err.actual_type,
                    'attempted_operation': err.attempted_operation,
                    'message': err.message,
                    'severity': err.severity
                }
                for err in self.errors
            ],
            'total_errors': len(self.errors),
            'dataclasses_found': len(self.dataclasses),
            'classes_found': len(self.regular_classes),
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

    
    def _collect_class_types(self):
        """Collect dataclasses and regular classes."""
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                tree = ast.parse(source)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_name = node.name
                        
                        # Check if it's a dataclass
                        is_dataclass = False
                        for decorator in node.decorator_list:
                            if isinstance(decorator, ast.Name) and decorator.id == 'dataclass':
                                is_dataclass = True
                                break
                        
                        if is_dataclass:
                            self.dataclasses.add(class_name)
                        else:
                            self.regular_classes.add(class_name)
                        
            except Exception:
                continue
    
    def _validate_file(self, filepath: Path):
        """Validate all type usage in a file with enhanced tracking."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            # Use enhanced type tracker
            tracker = TypeTracker(source, self.dataclasses, str(filepath))
            tracker.visit(tree)
            
            # Now validate method calls with proper type information
            checker = TypeUsageChecker(
                filepath,
                self.project_root,
                tracker,
                self.dataclasses
            )
            checker.visit(tree)
            
            self.errors.extend(checker.errors)
                        
        except Exception:
            pass
    
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

