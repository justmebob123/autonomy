"""
Symbol Collector

Collects all symbols (classes, functions, variables, imports, enums, calls)
from the project and populates the unified symbol table.

This is the first phase of validation - collect all data once, then
all validators can use it.
"""

import ast
from pathlib import Path
from typing import Optional, Set
import logging

from .symbol_table import (
    SymbolTable, TypeInfo, FunctionInfo, ClassInfo, ImportInfo,
    TypeCategory, CallGraphNode
)


class SymbolCollectorVisitor(ast.NodeVisitor):
    """
    AST visitor that collects all symbols from a Python file.
    
    Collects:
    - Class definitions with methods and attributes
    - Function definitions with signatures
    - Variable assignments with type inference
    - Import statements
    - Enum definitions
    - Function calls (for call graph)
    """
    
    def __init__(self, filepath: str, symbol_table: SymbolTable):
        self.filepath = filepath
        self.symbol_table = symbol_table
        
        # Track current context
        self.current_class: Optional[str] = None
        self.current_function: Optional[str] = None
        
        # Track local variables in current function
        self.local_variables: dict = {}
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Collect class definition."""
        # Check if it's an enum
        is_enum = any(
            base.id == 'Enum' if isinstance(base, ast.Name) else False
            for base in node.bases
        )
        
        # If it's an enum, collect it separately
        if is_enum:
            self._collect_enum(node)
            return  # Don't process as regular class
        
        # Check if it's a dataclass
        is_dataclass = any(
            isinstance(d, ast.Name) and d.id == 'dataclass'
            for d in node.decorator_list
        )
        
        # Collect decorators
        decorators = []
        for d in node.decorator_list:
            if isinstance(d, ast.Name):
                decorators.append(d.id)
            elif isinstance(d, ast.Call) and isinstance(d.func, ast.Name):
                decorators.append(d.func.id)
        
        # Collect parent classes
        parent_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                parent_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                if isinstance(base.value, ast.Name):
                    parent_classes.append(f"{base.value.id}.{base.attr}")
        
        # Create ClassInfo
        class_info = ClassInfo(
            name=node.name,
            file=self.filepath,
            line=node.lineno,
            parent_classes=parent_classes,
            is_dataclass=is_dataclass,
            decorators=decorators
        )
        
        # Collect attributes (for dataclasses)
        if is_dataclass:
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    attr_name = item.target.id
                    attr_type = self._get_type_from_annotation(item.annotation)
                    class_info.attributes[attr_name] = attr_type
        
        # Visit class body to collect methods
        old_class = self.current_class
        self.current_class = node.name
        
        # Collect methods
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = self._collect_function(item, is_method=True)
                if method_info:
                    class_info.methods[method_info.name] = method_info
                    # Also add to global functions dict with qualified name
                    self.symbol_table.add_function(method_info)
        
        # Add to symbol table
        self.symbol_table.add_class(class_info)
        
        # Continue visiting (with current_class still set for nested classes)
        self.generic_visit(node)
        
        self.current_class = old_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Collect function definition."""
        if not self.current_class:  # Only collect top-level functions here
            func_info = self._collect_function(node, is_method=False)
            if func_info:
                self.symbol_table.add_function(func_info)
        
        # Visit function body for calls (methods already collected in visit_ClassDef)
        old_function = self.current_function
        if self.current_class:
            self.current_function = f"{self.current_class}.{node.name}"
        else:
            self.current_function = node.name
        
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Collect async function definition."""
        self.visit_FunctionDef(node)
    
    def visit_Import(self, node: ast.Import):
        """Collect import statement."""
        for alias in node.names:
            import_info = ImportInfo(
                module=alias.name,
                name=alias.name.split('.')[-1],
                alias=alias.asname,
                file=self.filepath,
                line=node.lineno
            )
            self.symbol_table.add_import(import_info)
        
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Collect from-import statement."""
        if node.module:
            for alias in node.names:
                import_info = ImportInfo(
                    module=node.module,
                    name=alias.name,
                    alias=alias.asname,
                    file=self.filepath,
                    line=node.lineno
                )
                self.symbol_table.add_import(import_info)
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Collect function call for call graph."""
        if self.current_function:
            callee = None
            
            if isinstance(node.func, ast.Name):
                callee = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee = node.func.attr
                # For method calls, try to get qualified name
                if isinstance(node.func.value, ast.Name):
                    obj_name = node.func.value.id
                    # Check if we know the type
                    var_type = self.symbol_table.get_variable_type(obj_name, self.filepath)
                    if var_type:
                        callee = f"{var_type.type_name}.{callee}"
            
            if callee:
                self.symbol_table.add_call(
                    caller=self.current_function,
                    callee=callee,
                    file=self.filepath,
                    line=node.lineno
                )
        
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign):
        """Collect variable assignments for type inference."""
        # Simple type inference: var = ClassName()
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                type_name = node.value.func.id
                
                # Check if it's a known class
                class_info = self.symbol_table.get_class(type_name)
                if class_info:
                    type_info = TypeInfo(
                        type_name=type_name,
                        category=TypeCategory.DATACLASS if class_info.is_dataclass else TypeCategory.CLASS,
                        file=self.filepath,
                        line=node.lineno,
                        attributes=class_info.attributes,
                        methods=set(class_info.methods.keys())
                    )
                    
                    # Set type for all targets
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            self.symbol_table.set_variable_type(
                                target.id,
                                type_info,
                                self.filepath
                            )
        
        self.generic_visit(node)
    
    def _collect_function(self, node: ast.FunctionDef, is_method: bool) -> Optional[FunctionInfo]:
        """Collect function/method information."""
        # Build qualified name
        if self.current_class:
            qualified_name = f"{self.current_class}.{node.name}"
        else:
            qualified_name = node.name
        
        # Collect decorators
        decorators = []
        for d in node.decorator_list:
            if isinstance(d, ast.Name):
                decorators.append(d.id)
            elif isinstance(d, ast.Call) and isinstance(d.func, ast.Name):
                decorators.append(d.func.id)
        
        # Skip if has signature-modifying decorators
        signature_modifiers = {'property', 'staticmethod', 'classmethod', 'cached_property'}
        if any(d in signature_modifiers for d in decorators):
            return None
        
        # Collect parameters
        args = node.args
        required_params = []
        optional_params = []
        
        num_defaults = len(args.defaults)
        num_args = len(args.args)
        num_required = num_args - num_defaults
        
        for i, arg in enumerate(args.args):
            # Skip 'self' and 'cls' for methods
            if is_method and arg.arg in ('self', 'cls'):
                continue
            
            if i < num_required:
                required_params.append(arg.arg)
            else:
                optional_params.append(arg.arg)
        
        # Check for *args and **kwargs
        has_varargs = args.vararg is not None
        has_kwargs = args.kwarg is not None
        
        # Try to infer return type
        return_type = None
        if node.returns:
            return_type = self._get_type_from_annotation(node.returns)
        
        return FunctionInfo(
            name=node.name,
            qualified_name=qualified_name,
            file=self.filepath,
            line=node.lineno,
            required_params=required_params,
            optional_params=optional_params,
            has_varargs=has_varargs,
            has_kwargs=has_kwargs,
            return_type=return_type,
            decorators=decorators
        )
    
    def _collect_enum(self, node: ast.ClassDef):
        """Collect enum definition."""
        enum_name = node.name
        attributes = set()
        
        # Collect enum members
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        # Skip special attributes
                        if not target.id.startswith('_'):
                            attributes.add(target.id)
        
        # Add to symbol table
        self.symbol_table.add_enum(enum_name, attributes, self.filepath, node.lineno)
    
    def _get_type_from_annotation(self, annotation) -> TypeInfo:
        """Extract type information from type annotation."""
        type_name = "Unknown"
        category = TypeCategory.UNKNOWN
        
        if isinstance(annotation, ast.Name):
            type_name = annotation.id
            # Determine category
            if type_name == "dict":
                category = TypeCategory.DICT
            elif type_name == "list":
                category = TypeCategory.LIST
            elif type_name == "str":
                category = TypeCategory.STRING
            elif type_name == "int":
                category = TypeCategory.INT
            elif type_name == "float":
                category = TypeCategory.FLOAT
            elif type_name == "bool":
                category = TypeCategory.BOOL
            else:
                # Check if it's a known class
                class_info = self.symbol_table.get_class(type_name)
                if class_info:
                    category = TypeCategory.DATACLASS if class_info.is_dataclass else TypeCategory.CLASS
                else:
                    category = TypeCategory.CLASS
        
        elif isinstance(annotation, ast.Subscript):
            # Handle Dict[str, int], List[str], etc.
            if isinstance(annotation.value, ast.Name):
                type_name = annotation.value.id
                if type_name == "Dict":
                    category = TypeCategory.DICT
                elif type_name == "List":
                    category = TypeCategory.LIST
        
        return TypeInfo(
            type_name=type_name,
            category=category,
            file=self.filepath,
            line=getattr(annotation, 'lineno', 0)
        )


class SymbolCollector:
    """
    Collects all symbols from a project and populates the symbol table.
    
    This is the first phase of validation - collect all data once,
    then all validators can use the shared symbol table.
    """
    
    def __init__(self, symbol_table: SymbolTable, logger: Optional[logging.Logger] = None):
        self.symbol_table = symbol_table
        self.logger = logger or logging.getLogger(__name__)
    
    def collect_from_project(self, project_root: Path) -> None:
        """
        Collect all symbols from a project.
        
        Args:
            project_root: Root directory of the project
        """
        self.logger.info(f"Collecting symbols from {project_root}")
        
        # Clear existing data
        self.symbol_table.clear()
        
        # Collect from all Python files
        python_files = list(project_root.rglob("*.py"))
        self.logger.info(f"Found {len(python_files)} Python files")
        
        for py_file in python_files:
            # Skip hidden files and common directories
            if py_file.name.startswith('.'):
                continue
            
            if any(part.startswith('.') or part in ['__pycache__', 'venv', '.venv', 'node_modules'] 
                   for part in py_file.parts):
                continue
            
            self.collect_from_file(py_file)
        
        # Log statistics
        stats = self.symbol_table.get_statistics()
        self.logger.info(f"Symbol collection complete:")
        self.logger.info(f"  Classes: {stats['total_classes']}")
        self.logger.info(f"  Functions: {stats['total_functions']}")
        self.logger.info(f"  Methods: {stats['total_methods']}")
        self.logger.info(f"  Enums: {stats['total_enums']}")
        self.logger.info(f"  Imports: {stats['total_imports']}")
        self.logger.info(f"  Call edges: {stats['total_call_edges']}")
        if stats['duplicate_classes'] > 0:
            self.logger.warning(f"  Duplicate classes: {stats['duplicate_classes']}")
    
    def collect_from_file(self, filepath: Path) -> None:
        """
        Collect symbols from a single file.
        
        Args:
            filepath: Path to Python file
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source, filename=str(filepath))
            
            # Get relative path
            rel_path = str(filepath.relative_to(self.symbol_table.project_root))
            
            # Visit AST
            visitor = SymbolCollectorVisitor(rel_path, self.symbol_table)
            visitor.visit(tree)
            
        except SyntaxError as e:
            self.logger.warning(f"Syntax error in {filepath}: {e}")
        except Exception as e:
            self.logger.error(f"Error collecting from {filepath}: {e}")