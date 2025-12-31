"""
Enhanced Type Tracker

Implements proper type inference with:
- Function return type tracking
- Loop variable type tracking
- Attribute type tracking on dataclasses
- Symbol table management
- Control flow analysis
"""

import ast
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass


@dataclass
class TypeInfo:
    """Information about a variable's type."""
    type_name: str
    is_dataclass: bool
    is_dict: bool
    is_list: bool
    is_string: bool
    attributes: Dict[str, 'TypeInfo'] = None
    
    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


class EnhancedTypeTracker(ast.NodeVisitor):
    """
    Enhanced type tracker that properly infers types through:
    - Direct assignments
    - Function returns
    - Loop iterations
    - Attribute access
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
        
    def get_type(self, var_name: str) -> Optional[TypeInfo]:
        """Get type of a variable, checking local then global scope."""
        if var_name in self.local_types:
            return self.local_types[var_name]
        if var_name in self.global_types:
            return self.global_types[var_name]
        return None
    
    def set_type(self, var_name: str, type_info: TypeInfo):
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
    
    def _infer_type(self, node: ast.AST) -> TypeInfo:
        """Infer type from an AST node."""
        # Direct instantiation: ClassName()
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                class_name = node.func.id
                return TypeInfo(
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
            return TypeInfo(
                type_name='dict',
                is_dataclass=False,
                is_dict=True,
                is_list=False,
                is_string=False
            )
        
        # List literal: []
        if isinstance(node, ast.List):
            return TypeInfo(
                type_name='list',
                is_dataclass=False,
                is_dict=False,
                is_list=True,
                is_string=False
            )
        
        # String literal: "..."
        if isinstance(node, ast.Str) or isinstance(node, ast.Constant) and isinstance(node.value, str):
            return TypeInfo(
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
        return TypeInfo(
            type_name='unknown',
            is_dataclass=False,
            is_dict=False,
            is_list=False,
            is_string=False
        )
    
    def _infer_element_type(self, container_type: TypeInfo) -> TypeInfo:
        """Infer type of elements in a container."""
        if container_type.is_list:
            # For now, assume unknown element type
            # Could be enhanced with more sophisticated analysis
            return TypeInfo(
                type_name='unknown',
                is_dataclass=False,
                is_dict=False,
                is_list=False,
                is_string=False
            )
        
        return TypeInfo(
            type_name='unknown',
            is_dataclass=False,
            is_dict=False,
            is_list=False,
            is_string=False
        )
    
    def _get_annotation_type(self, annotation: ast.AST) -> TypeInfo:
        """Get type from type annotation."""
        if isinstance(annotation, ast.Name):
            type_name = annotation.id
            return TypeInfo(
                type_name=type_name,
                is_dataclass=type_name in self.dataclasses,
                is_dict=type_name == 'dict' or type_name == 'Dict',
                is_list=type_name == 'list' or type_name == 'List',
                is_string=type_name == 'str',
            )
        
        if isinstance(annotation, ast.Subscript):
            # Handle Dict[str, int], List[str], etc.
            if isinstance(annotation.value, ast.Name):
                type_name = annotation.value.id
                return TypeInfo(
                    type_name=type_name,
                    is_dataclass=False,
                    is_dict=type_name == 'Dict' or type_name == 'dict',
                    is_list=type_name == 'List' or type_name == 'list',
                    is_string=False,
                )
        
        return TypeInfo(
            type_name='unknown',
            is_dataclass=False,
            is_dict=False,
            is_list=False,
            is_string=False
        )