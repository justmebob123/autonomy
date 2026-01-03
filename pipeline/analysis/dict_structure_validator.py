"""
Dictionary Structure Validator (FIXED VERSION)

Validates that dictionary access patterns match actual data structures.
Detects accessing keys that don't exist or wrong nested paths.

FIXES:
1. Tracks instance variables (self.attribute)
2. Follows .copy() operations
3. Tracks dynamic key assignments
4. Properly analyzes return statements that return variables
"""

import ast
import json
from typing import Dict, List, Set, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass


@dataclass
class DictStructureError:
    """Represents a dictionary structure validation error."""
    file: str
    line: int
    variable: str
    key_path: str
    error_type: str  # 'missing_key', 'wrong_nesting', 'type_mismatch'
    message: str
    severity: str



# Polytopic Integration Imports
from pipeline.messaging.message_bus import MessageBus, Message, MessageType, MessagePriority
from pipeline.pattern_recognition import PatternRecognitionSystem
from pipeline.correlation_engine import CorrelationEngine
from pipeline.analytics.optimizer import OptimizationEngine
from pipeline.adaptive_prompts import AdaptivePromptSystem
from pipeline.polytopic.dimensional_space import DimensionalSpace


class DictStructureValidator:
    """Validates dictionary access patterns against known structures."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.errors: List[DictStructureError] = []
        self.known_structures: Dict[str, Dict] = {}
        self.instance_vars: Dict[str, Dict[str, Dict]] = {}
        
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
        
        # Subscribe to file change events for real-time validation
        # Note: Using existing message types from the system
  # class_name -> {var_name: structure}
        
    def validate_all(self) -> Dict:
        """
        Validate all dictionary access patterns in the project.
        
        Returns:
            Dict with validation results
        """
        self.errors = []
        
        # First pass: collect known dictionary structures
        self._collect_dict_structures()
        
        # Second pass: validate dictionary access
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
                    'key_path': err.key_path,
                    'error_type': err.error_type,
                    'message': err.message,
                    'severity': err.severity
                }
                for err in self.errors
            ],
            'total_errors': len(self.errors),
            'structures_analyzed': len(self.known_structures),
            'instance_vars_tracked': sum(len(v) for v in self.instance_vars.values()),
            'by_severity': self._count_by_severity(),
            'by_type': self._count_by_type()
        }
        
        # Polytopic Integration: Record patterns and optimize
        self._record_validation_pattern(self.errors)
        self._optimize_validation(result)
        
        # Publish validation completed event
        self._publish_validation_event('validation_completed', {
            'total_errors': result['total_errors'],
            'by_severity': result['by_severity'],
            'structures_analyzed': result['structures_analyzed']
        })
        
        return result
    
    def _collect_dict_structures(self):
        """Collect dictionary structures from return statements, assignments, and instance vars."""
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                tree = ast.parse(source)
                
                # Track current class context
                current_class = None
                
                for node in ast.walk(tree):
                    # Track class definitions
                    if isinstance(node, ast.ClassDef):
                        current_class = node.name
                        if current_class not in self.instance_vars:
                            self.instance_vars[current_class] = {}
                    
                    # Look for instance variable assignments in __init__
                    if isinstance(node, ast.FunctionDef) and node.name == "__init__":
                        if current_class:
                            self._collect_instance_vars(node, current_class)
                    
                    # Analyze entire functions to track dynamic dict modifications
                    if isinstance(node, ast.FunctionDef):
                        structure = self._analyze_function_return(node, current_class)
                        if structure:
                            func_name = node.name
                            key = f"{current_class}.{func_name}" if current_class else func_name
                            self.known_structures[key] = structure
                    
                    # Look for assignments with dicts
                    if isinstance(node, ast.Assign):
                        if isinstance(node.value, ast.Dict):
                            structure = self._extract_dict_structure(node.value)
                            if structure:
                                for target in node.targets:
                                    if isinstance(target, ast.Name):
                                        self.known_structures[target.id] = structure
                        
            except Exception as e:
                # Silently skip files with parse errors
                continue
    
    def _analyze_function_return(self, func_node: ast.FunctionDef, current_class: Optional[str]) -> Optional[Dict]:
        """
        Analyze a function to determine the structure it returns.
        Tracks variable assignments and dynamic key additions within the function.
        """
        # Track local variables and their structures within this function
        local_vars = {}
        
        # Process ALL nodes in the function (including nested if/for/while blocks)
        for node in ast.walk(func_node):
            # Track assignments
            if isinstance(node, ast.Assign):
                # Check if this is a subscript assignment (dict[key] = value)
                is_subscript = any(isinstance(t, ast.Subscript) for t in node.targets)
                
                if is_subscript:
                    # Track dynamic key assignments: var[key] = value
                    for target in node.targets:
                        if isinstance(target, ast.Subscript):
                            if isinstance(target.value, ast.Name):
                                dict_var = target.value.id
                                if dict_var in local_vars:
                                    if isinstance(target.slice, ast.Constant):
                                        key = target.slice.value
                                        # Add this key to the structure
                                        if isinstance(local_vars[dict_var], dict):
                                            local_vars[dict_var][key] = 'unknown'
                else:
                    # Regular variable assignment
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id
                            
                            # Direct dict literal
                            if isinstance(node.value, ast.Dict):
                                local_vars[var_name] = self._extract_dict_structure(node.value)
                            
                            # Copy from instance variable
                            elif isinstance(node.value, ast.Call):
                                if isinstance(node.value.func, ast.Attribute) and node.value.func.attr == "copy":
                                    source_structure = self._resolve_structure(node.value.func.value, current_class, {})
                                    if source_structure:
                                        # Make a copy so we can modify it
                                        local_vars[var_name] = source_structure.copy()
        
        # Find return statement
        for node in ast.walk(func_node):
            if isinstance(node, ast.Return) and node.value:
                # If returning a local variable, return its tracked structure
                if isinstance(node.value, ast.Name):
                    var_name = node.value.id
                    if var_name in local_vars:
                        return local_vars[var_name]
                
                # If returning a direct dict or other expression
                return self._extract_return_structure(node.value, current_class)
        
        return None
    
    def _collect_instance_vars(self, init_node: ast.FunctionDef, class_name: str):
        """Collect instance variable dictionary structures from __init__."""
        for stmt in init_node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Attribute):
                        if isinstance(target.value, ast.Name) and target.value.id == "self":
                            var_name = target.attr
                            
                            # Extract structure if it's a dict
                            if isinstance(stmt.value, ast.Dict):
                                structure = self._extract_dict_structure(stmt.value)
                                if structure:
                                    self.instance_vars[class_name][var_name] = structure
    
    def _extract_return_structure(self, return_value: ast.AST, current_class: Optional[str]) -> Optional[Dict]:
        """Extract structure from a return statement, following variables and .copy()."""
        
        # Direct dict literal
        if isinstance(return_value, ast.Dict):
            return self._extract_dict_structure(return_value)
        
        # Variable return - need to trace it
        if isinstance(return_value, ast.Name):
            var_name = return_value.id
            # Check if we know this variable's structure
            if var_name in self.known_structures:
                return self.known_structures[var_name]
        
        # self.attribute return
        if isinstance(return_value, ast.Attribute):
            if isinstance(return_value.value, ast.Name) and return_value.value.id == "self":
                attr_name = return_value.attr
                if current_class and current_class in self.instance_vars:
                    if attr_name in self.instance_vars[current_class]:
                        return self.instance_vars[current_class][attr_name]
        
        # .copy() call - follow the source
        if isinstance(return_value, ast.Call):
            if isinstance(return_value.func, ast.Attribute) and return_value.func.attr == "copy":
                # Recursively extract from the source
                return self._extract_return_structure(return_value.func.value, current_class)
        
        return None
    
    def _extract_dict_structure(self, dict_node: ast.Dict) -> Optional[Dict]:
        """Extract the structure of a dictionary literal."""
        structure = {}
        
        for key, value in zip(dict_node.keys, dict_node.values):
            if isinstance(key, ast.Constant):
                key_name = key.value
                
                # Determine value type
                if isinstance(value, ast.Dict):
                    structure[key_name] = self._extract_dict_structure(value)
                elif isinstance(value, ast.List):
                    structure[key_name] = 'list'
                elif isinstance(value, ast.Constant):
                    structure[key_name] = type(value.value).__name__
                else:
                    structure[key_name] = 'unknown'
        
        return structure if structure else None
    
    def _get_parent_function(self, node: ast.AST, tree: ast.AST) -> Optional[str]:
        """Get the name of the function containing this node."""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.FunctionDef):
                if any(child is node for child in ast.walk(parent)):
                    return parent.name
        return None
    
    def _validate_file(self, filepath: Path):
        """Validate all dictionary access in a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            # Track variable assignments to known structures
            var_structures = {}
            current_class = None
            
            for node in ast.walk(tree):
                # Track class context
                if isinstance(node, ast.ClassDef):
                    current_class = node.name
                
                # Track assignments from function calls
                if isinstance(node, ast.Assign):
                    # Assignment from method call
                    if isinstance(node.value, ast.Call):
                        structure = self._resolve_call_structure(node.value, current_class)
                        if structure:
                            for target in node.targets:
                                if isinstance(target, ast.Name):
                                    var_structures[target.id] = structure
                    
                    # Assignment from .copy()
                    elif isinstance(node.value, ast.Call):
                        if isinstance(node.value.func, ast.Attribute) and node.value.func.attr == "copy":
                            source_structure = self._resolve_structure(node.value.func.value, current_class, var_structures)
                            if source_structure:
                                for target in node.targets:
                                    if isinstance(target, ast.Name):
                                        var_structures[target.id] = source_structure
                    
                    # Track dynamic key additions: dict[key] = value
                    for target in node.targets:
                        if isinstance(target, ast.Subscript):
                            if isinstance(target.value, ast.Name):
                                dict_var = target.value.id
                                if dict_var in var_structures:
                                    if isinstance(target.slice, ast.Constant):
                                        key = target.slice.value
                                        # Add this key to the known structure
                                        if isinstance(var_structures[dict_var], dict):
                                            var_structures[dict_var][key] = 'unknown'
                
                # Check dictionary access with .get()
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute) and node.func.attr == 'get':
                        self._validate_dict_get(node, filepath, var_structures, current_class)
                
                # Check dictionary subscript access (but skip if it's an assignment target)
                if isinstance(node, ast.Subscript):
                    # Check if this subscript is being assigned to (left side of =)
                    is_assignment_target = False
                    for assign_node in ast.walk(tree):
                        if isinstance(assign_node, ast.Assign):
                            for target in assign_node.targets:
                                if target is node:
                                    is_assignment_target = True
                                    break
                    
                    # Only validate if it's a READ, not a WRITE
                    if not is_assignment_target:
                        self._validate_dict_subscript(node, filepath, var_structures, current_class)
                        
        except Exception:
            pass
    
    def _resolve_call_structure(self, call_node: ast.Call, current_class: Optional[str]) -> Optional[Dict]:
        """Resolve the structure returned by a function call."""
        if isinstance(call_node.func, ast.Attribute):
            func_name = call_node.func.attr
            
            # Check with class context
            if current_class:
                key = f"{current_class}.{func_name}"
                if key in self.known_structures:
                    return self.known_structures[key]
            
            # Check without class context
            if func_name in self.known_structures:
                return self.known_structures[func_name]
        
        return None
    
    def _resolve_structure(self, node: ast.AST, current_class: Optional[str], var_structures: Dict) -> Optional[Dict]:
        """Resolve the structure of a node (variable, attribute, etc.)."""
        
        # Variable
        if isinstance(node, ast.Name):
            var_name = node.id
            if var_name in var_structures:
                return var_structures[var_name]
        
        # self.attribute
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == "self":
                attr_name = node.attr
                if current_class and current_class in self.instance_vars:
                    if attr_name in self.instance_vars[current_class]:
                        return self.instance_vars[current_class][attr_name]
        
        return None
    
    def _validate_dict_get(self, node: ast.Call, filepath: Path, var_structures: Dict, current_class: Optional[str]):
        """Validate a .get() call on a dictionary."""
        if not isinstance(node.func, ast.Attribute):
            return
        
        # Resolve the structure being accessed
        structure = self._resolve_structure(node.func.value, current_class, var_structures)
        
        if structure:
            # Get the key being accessed
            if node.args and isinstance(node.args[0], ast.Constant):
                key = node.args[0].value
                
                # Check if key exists in structure
                if isinstance(structure, dict) and key not in structure:
                    var_name = self._get_var_name(node.func.value)
                    
                    # Using .get() is SAFE but indicates inconsistent structure
                    # This is a WARNING, not an ERROR
                    self.errors.append(DictStructureError(
                        file=str(filepath.relative_to(self.project_root)),
                        line=node.lineno,
                        variable=var_name,
                        key_path=key,
                        error_type='missing_key_safe',
                        message=f"Key '{key}' not found in {var_name} structure (using .get() is safe). Available keys: {list(structure.keys())}",
                        severity='low'
                    ))
    
    def _validate_dict_subscript(self, node: ast.Subscript, filepath: Path, var_structures: Dict, current_class: Optional[str]):
        """Validate dictionary subscript access."""
        # Resolve the structure being accessed
        structure = self._resolve_structure(node.value, current_class, var_structures)
        
        if structure:
            # Get the key being accessed
            if isinstance(node.slice, ast.Constant):
                key = node.slice.value
                
                # Check if key exists in structure
                if isinstance(structure, dict) and key not in structure:
                    var_name = self._get_var_name(node.value)
                    
                    # Check if this access is protected by an if-check
                    # Pattern: if dict.get('key'): ... dict['key']
                    is_protected = self._is_protected_by_if_check(node, var_name, key)
                    
                    if is_protected:
                        # Protected by if-check - this is safe but could be cleaner
                        self.errors.append(DictStructureError(
                            file=str(filepath.relative_to(self.project_root)),
                            line=node.lineno,
                            variable=var_name,
                            key_path=key,
                            error_type='missing_key_protected',
                            message=f"Key '{key}' not found in {var_name} structure (protected by if-check). Available keys: {list(structure.keys())}",
                            severity='low'
                        ))
                    else:
                        # Unprotected access - this could crash!
                        self.errors.append(DictStructureError(
                            file=str(filepath.relative_to(self.project_root)),
                            line=node.lineno,
                            variable=var_name,
                            key_path=key,
                            error_type='missing_key',
                            message=f"Key '{key}' not found in {var_name} structure. Available keys: {list(structure.keys())}",
                            severity='high'
                        ))
    
    def _is_protected_by_if_check(self, node: ast.Subscript, var_name: str, key: str) -> bool:
        """
        Check if a subscript access is protected by an if-check.
        Pattern: if dict.get('key'): ... dict['key']
        """
        # This is a simplified check - in a real implementation, we'd need to
        # walk up the AST to find parent if statements and check their conditions
        # For now, we'll return False to be conservative
        return False
    
    def _get_var_name(self, node: ast.AST) -> str:
        """Get a readable variable name from a node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_var_name(node.value)}.{node.attr}"
        else:
            return "unknown"
    
    def _count_by_severity(self) -> Dict[str, int]:
        """Count errors by severity."""
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for err in self.errors:
            counts[err.severity] += 1
        return counts
    
    def _count_by_type(self) -> Dict[str, int]:
        """Count errors by type."""
        counts = {}
        for err in self.errors:
            counts[err.error_type] = counts.get(err.error_type, 0) + 1
        return counts
    
    def _publish_validation_event(self, event_type: str, payload: dict):
        """Publish validation events using existing message types."""
        # Map validation events to existing system message types
        message_type_map = {
            'validation_started': MessageType.SYSTEM_INFO,
            'validation_completed': MessageType.SYSTEM_INFO,
            'validation_error': MessageType.SYSTEM_WARNING,
            'validation_critical': MessageType.SYSTEM_ALERT,
            'validation_insight': MessageType.SYSTEM_INFO,
        }
        
        message_type = message_type_map.get(event_type, MessageType.SYSTEM_INFO)
        
        message = Message(
            sender='DictStructureValidator',
            recipient='ALL',
            message_type=message_type,
            priority=MessagePriority.NORMAL,
            payload={
                'event': event_type,
                'validator': 'dict_structure',
                **payload
            }
        )
        
        self.message_bus.publish(message)
    
    def _record_validation_pattern(self, errors: list):
        """Record validation patterns for learning."""
        if not errors:
            return
        
        # Record execution data for pattern recognition
        execution_data = {
            'phase': 'validation',
            'tool': 'dict_structure_validator',
            'success': len([e for e in errors if (e.severity if hasattr(e, 'severity') else e.get('severity')) == 'high']) == 0,
            'error_count': len(errors),
            'timestamp': str(Path.cwd())  # Use as context
        }
        
        self.pattern_recognition.record_execution(execution_data)
        
        # Add findings to correlation engine
        for error in errors:
            # Handle both dict and DictStructureError objects
            if isinstance(error, dict):
                component = error['file']
                finding = {
                    'type': 'dict_validation_error',
                    'error_type': error['error_type'],
                    'severity': error['severity'],
                    'variable': error['variable'],
                    'key_path': error['key_path']
                }
            else:
                # DictStructureError object
                component = error.file
                finding = {
                    'type': 'dict_validation_error',
                    'error_type': error.error_type,
                    'severity': error.severity,
                    'variable': error.variable,
                    'key_path': error.key_path
                }
            
            self.correlation_engine.add_finding(component, finding)
        
        # Find correlations
        correlations = self.correlation_engine.correlate()
        
        if correlations:
            # Publish correlation insights
            self._publish_validation_event('validation_insight', {
                'type': 'validation_correlations',
                'correlations': correlations
            })
    
    def _optimize_validation(self, result: dict):
        """Optimize validation based on results."""
        # Record quality metrics for optimization
        self.optimizer.record_quality_metric(
            'dict_structure_errors',
            result['total_errors']
        )
        
        self.optimizer.record_quality_metric(
            'dict_structure_high_severity',
            result['by_severity']['high']
        )
        
        # Track in dimensional space (if it has the right methods)
        try:
            if hasattr(self.dimensional_space, 'record_metric'):
                self.dimensional_space.record_metric(
                    dimension='validation_quality',
                    metric='dict_structure_errors',
                    value=result['total_errors']
                )
        except Exception:
            pass  # Dimensional space may not support this yet
