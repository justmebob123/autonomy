"""
Unified Symbol Table for All Validators

Provides a shared data structure for all validation tools to eliminate
duplicate work and enable cross-validator communication.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
from enum import Enum


class TypeCategory(Enum):
    """Categories of types."""
    DATACLASS = "dataclass"
    CLASS = "class"
    DICT = "dict"
    LIST = "list"
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    NONE = "none"
    UNKNOWN = "unknown"


@dataclass
class TypeInfo:
    """Information about a variable's type."""
    type_name: str
    category: TypeCategory
    file: str
    line: int
    attributes: Dict[str, 'TypeInfo'] = field(default_factory=dict)
    methods: Set[str] = field(default_factory=set)
    parent_classes: List[str] = field(default_factory=list)
    
    def is_dataclass(self) -> bool:
        return self.category == TypeCategory.DATACLASS
    
    def is_dict(self) -> bool:
        return self.category == TypeCategory.DICT
    
    def is_class(self) -> bool:
        return self.category in (TypeCategory.CLASS, TypeCategory.DATACLASS)


@dataclass
class FunctionInfo:
    """Information about a function/method."""
    name: str
    qualified_name: str  # e.g., "ClassName.method_name"
    file: str
    line: int
    required_params: List[str] = field(default_factory=list)
    optional_params: List[str] = field(default_factory=list)
    has_varargs: bool = False
    has_kwargs: bool = False
    return_type: Optional[TypeInfo] = None
    decorators: List[str] = field(default_factory=list)
    
    @property
    def min_args(self) -> int:
        """Minimum number of arguments required."""
        return len(self.required_params)
    
    @property
    def max_args(self) -> Optional[int]:
        """Maximum number of arguments (None if unlimited)."""
        if self.has_varargs or self.has_kwargs:
            return None
        return len(self.required_params) + len(self.optional_params)


@dataclass
class ClassInfo:
    """Information about a class."""
    name: str
    file: str
    line: int
    methods: Dict[str, FunctionInfo] = field(default_factory=dict)
    attributes: Dict[str, TypeInfo] = field(default_factory=dict)
    parent_classes: List[str] = field(default_factory=list)
    is_dataclass: bool = False
    decorators: List[str] = field(default_factory=list)
    
    def has_method(self, method_name: str) -> bool:
        """Check if class has a method (including inherited)."""
        return method_name in self.methods
    
    def get_method(self, method_name: str) -> Optional[FunctionInfo]:
        """Get method info (including inherited)."""
        return self.methods.get(method_name)


@dataclass
class ImportInfo:
    """Information about an import."""
    module: str
    name: str
    alias: Optional[str]
    file: str
    line: int
    
    @property
    def local_name(self) -> str:
        """Name used in the importing file."""
        return self.alias if self.alias else self.name


@dataclass
class CallGraphNode:
    """Node in the call graph."""
    function: str
    file: str
    line: int
    calls: Set[str] = field(default_factory=set)
    called_by: Set[str] = field(default_factory=set)


class SymbolTable:
    """
    Unified symbol table shared by all validators.
    
    Provides centralized tracking of:
    - Class definitions and their methods
    - Function/method signatures
    - Variable types (per file and global)
    - Call graph (caller -> callee relationships)
    - Import statements
    - Enum definitions
    
    This eliminates duplicate work across validators and enables
    cross-validator communication and type propagation.
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        
        # Class definitions: qualified_name -> ClassInfo
        self.classes: Dict[str, ClassInfo] = {}
        
        # Track duplicate class names: class_name -> [files]
        self.duplicate_classes: Dict[str, List[str]] = {}
        
        # Function/method signatures: qualified_name -> FunctionInfo
        self.functions: Dict[str, FunctionInfo] = {}
        
        # Variable types per file: file -> {var_name -> TypeInfo}
        self.file_variables: Dict[str, Dict[str, TypeInfo]] = {}
        
        # Global variable types: var_name -> TypeInfo
        self.global_variables: Dict[str, TypeInfo] = {}
        
        # Call graph: function_name -> CallGraphNode
        self.call_graph: Dict[str, CallGraphNode] = {}
        
        # Imports per file: file -> [ImportInfo]
        self.file_imports: Dict[str, List[ImportInfo]] = {}
        
        # Enum definitions: enum_name -> Set[valid_attributes]
        self.enums: Dict[str, Set[str]] = {}
        
        # Enum locations: enum_name -> (file, line)
        self.enum_locations: Dict[str, Tuple[str, int]] = {}
    
    def add_class(self, class_info: ClassInfo) -> None:
        """Add a class definition to the symbol table."""
        qualified_name = f"{class_info.file}:{class_info.name}"
        self.classes[qualified_name] = class_info
        
        # Also store by simple name for quick lookup
        self.classes[class_info.name] = class_info
        
        # Track duplicates
        if class_info.name not in self.duplicate_classes:
            self.duplicate_classes[class_info.name] = []
        self.duplicate_classes[class_info.name].append(class_info.file)
    
    def get_class(self, class_name: str, file: Optional[str] = None) -> Optional[ClassInfo]:
        """
        Get class info by name.
        
        Args:
            class_name: Name of the class
            file: Optional file path for disambiguation
        
        Returns:
            ClassInfo if found, None otherwise
        """
        if file:
            qualified_name = f"{file}:{class_name}"
            if qualified_name in self.classes:
                return self.classes[qualified_name]
        
        # Fall back to simple name
        return self.classes.get(class_name)
    
    def add_function(self, func_info: FunctionInfo) -> None:
        """Add a function/method definition to the symbol table."""
        self.functions[func_info.qualified_name] = func_info
        
        # Also store by simple name for quick lookup
        simple_name = func_info.name
        if simple_name not in self.functions:
            self.functions[simple_name] = func_info
    
    def get_function(self, func_name: str) -> Optional[FunctionInfo]:
        """Get function info by name."""
        return self.functions.get(func_name)
    
    def set_variable_type(self, var_name: str, type_info: TypeInfo, file: Optional[str] = None) -> None:
        """
        Set the type of a variable.
        
        Args:
            var_name: Variable name
            type_info: Type information
            file: Optional file path (for file-local variables)
        """
        if file:
            if file not in self.file_variables:
                self.file_variables[file] = {}
            self.file_variables[file][var_name] = type_info
        else:
            self.global_variables[var_name] = type_info
    
    def get_variable_type(self, var_name: str, file: Optional[str] = None) -> Optional[TypeInfo]:
        """
        Get the type of a variable.
        
        Args:
            var_name: Variable name
            file: Optional file path (checks file-local first, then global)
        
        Returns:
            TypeInfo if found, None otherwise
        """
        # Check file-local first
        if file and file in self.file_variables:
            if var_name in self.file_variables[file]:
                return self.file_variables[file][var_name]
        
        # Fall back to global
        return self.global_variables.get(var_name)
    
    def add_call(self, caller: str, callee: str, file: str, line: int) -> None:
        """
        Add a function call to the call graph.
        
        Args:
            caller: Name of the calling function
            callee: Name of the called function
            file: File where the call occurs
            line: Line number of the call
        """
        # Ensure caller node exists
        if caller not in self.call_graph:
            self.call_graph[caller] = CallGraphNode(
                function=caller,
                file=file,
                line=line
            )
        
        # Ensure callee node exists
        if callee not in self.call_graph:
            self.call_graph[callee] = CallGraphNode(
                function=callee,
                file="",  # Unknown until we see its definition
                line=0
            )
        
        # Add the call relationship
        self.call_graph[caller].calls.add(callee)
        self.call_graph[callee].called_by.add(caller)
    
    def get_callers(self, function: str) -> Set[str]:
        """Get all functions that call the given function."""
        if function in self.call_graph:
            return self.call_graph[function].called_by
        return set()
    
    def get_callees(self, function: str) -> Set[str]:
        """Get all functions called by the given function."""
        if function in self.call_graph:
            return self.call_graph[function].calls
        return set()
    
    def add_import(self, import_info: ImportInfo) -> None:
        """Add an import statement to the symbol table."""
        if import_info.file not in self.file_imports:
            self.file_imports[import_info.file] = []
        self.file_imports[import_info.file].append(import_info)
    
    def get_imports(self, file: str) -> List[ImportInfo]:
        """Get all imports for a file."""
        return self.file_imports.get(file, [])
    
    def resolve_import(self, name: str, file: str) -> Optional[str]:
        """
        Resolve an imported name to its full module path.
        
        Args:
            name: Name used in the file
            file: File where the name is used
        
        Returns:
            Full module path if found, None otherwise
        """
        imports = self.get_imports(file)
        for imp in imports:
            if imp.local_name == name:
                return f"{imp.module}.{imp.name}"
        return None
    
    def add_enum(self, enum_name: str, attributes: Set[str], file: str, line: int) -> None:
        """Add an enum definition to the symbol table."""
        self.enums[enum_name] = attributes
        self.enum_locations[enum_name] = (file, line)
    
    def get_enum_attributes(self, enum_name: str) -> Optional[Set[str]]:
        """Get valid attributes for an enum."""
        return self.enums.get(enum_name)
    
    def is_valid_enum_attribute(self, enum_name: str, attribute: str) -> bool:
        """Check if an attribute is valid for an enum."""
        if enum_name in self.enums:
            return attribute in self.enums[enum_name]
        return False
    
    def get_duplicate_classes(self) -> Dict[str, List[str]]:
        """Get all classes defined in multiple files."""
        return {
            name: files
            for name, files in self.duplicate_classes.items()
            if len(files) > 1
        }
    
    def get_statistics(self) -> Dict:
        """Get statistics about the symbol table."""
        return {
            'total_classes': len([c for c in self.classes.values() if ':' not in c.name]),
            'total_functions': len([f for f in self.functions.values() if '.' not in f.name]),
            'total_methods': len([f for f in self.functions.values() if '.' in f.name]),
            'total_enums': len(self.enums),
            'total_imports': sum(len(imports) for imports in self.file_imports.values()),
            'total_call_edges': sum(len(node.calls) for node in self.call_graph.values()),
            'duplicate_classes': len(self.get_duplicate_classes()),
        }
    
    def clear(self) -> None:
        """Clear all data from the symbol table."""
        self.classes.clear()
        self.duplicate_classes.clear()
        self.functions.clear()
        self.file_variables.clear()
        self.global_variables.clear()
        self.call_graph.clear()
        self.file_imports.clear()
        self.enums.clear()
        self.enum_locations.clear()