"""
Enum Attribute Validator

Validates that Enum attributes exist before they are accessed.
Detects invalid enum member access like MessageType.INVALID_ATTRIBUTE.
"""

import ast
from typing import Dict, List, Set, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


@dataclass
class EnumAttributeError:
    """Represents an enum attribute validation error."""
    file: str
    line: int
    enum_name: str
    attribute: str
    valid_attributes: List[str]
    message: str
    severity: str


class EnumCollector(ast.NodeVisitor):
    """Collects all Enum definitions in a file."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.enums: Dict[str, Set[str]] = {}  # enum_name -> set of valid attributes
        
    def visit_ClassDef(self, node: ast.ClassDef):
        """Check if class is an Enum and collect its members."""
        # Check if class inherits from Enum
        is_enum = False
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == 'Enum':
                is_enum = True
                break
        
        if is_enum:
            # Collect enum members
            members = set()
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            members.add(target.id)
                elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    members.add(item.target.id)
            
            self.enums[node.name] = members
        
        self.generic_visit(node)


class EnumUsageChecker(ast.NodeVisitor):
    """Checks that Enum attributes are valid."""
    
    def __init__(self, filepath: Path, project_root: Path, all_enums: Dict[str, Set[str]]):
        self.filepath = filepath
        self.project_root = project_root
        self.all_enums = all_enums
        self.errors: List[EnumAttributeError] = []
        self.imports: Dict[str, str] = {}  # alias -> original_name
        
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track imports to resolve enum names."""
        if node.module:
            for alias in node.names:
                imported_name = alias.name
                alias_name = alias.asname if alias.asname else imported_name
                self.imports[alias_name] = imported_name
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute):
        """Check enum attribute access."""
        # Check if this is accessing an attribute on a Name (e.g., MessageType.SOMETHING)
        if isinstance(node.value, ast.Name):
            enum_name = node.value.id
            attribute = node.attr
            
            # Resolve import alias
            if enum_name in self.imports:
                enum_name = self.imports[enum_name]
            
            # Check if this is a known enum
            if enum_name in self.all_enums:
                valid_attrs = self.all_enums[enum_name]
                
                # Check if attribute exists
                if attribute not in valid_attrs:
                    # Get suggestions (similar names)
                    suggestions = self._get_suggestions(attribute, valid_attrs)
                    suggestion_text = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
                    
                    self.errors.append(EnumAttributeError(
                        file=str(self.filepath.relative_to(self.project_root)),
                        line=node.lineno,
                        enum_name=enum_name,
                        attribute=attribute,
                        valid_attributes=sorted(valid_attrs),
                        message=f"Enum '{enum_name}' has no attribute '{attribute}'.{suggestion_text}",
                        severity='critical'
                    ))
        
        self.generic_visit(node)
    
    def _get_suggestions(self, attr: str, valid_attrs: Set[str], max_suggestions: int = 3) -> List[str]:
        """Get suggestions for similar attribute names."""
        attr_lower = attr.lower()
        suggestions = []
        
        # Find attributes with similar names
        for valid_attr in valid_attrs:
            if attr_lower in valid_attr.lower() or valid_attr.lower() in attr_lower:
                suggestions.append(valid_attr)
                if len(suggestions) >= max_suggestions:
                    break
        
        return suggestions


class EnumAttributeValidator:
    """Validates that Enum attributes exist before they are accessed."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.errors: List[EnumAttributeError] = []
        self.all_enums: Dict[str, Set[str]] = {}
        
    def validate_all(self) -> Dict:
        """
        Validate all enum attribute usage in the project.
        
        Returns:
            Dict with validation results
        """
        self.errors = []
        
        # First pass: collect all enum definitions
        self._collect_enums()
        
        # Second pass: validate enum usage
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            self._validate_file(py_file)
        
        return {
            'errors': [
                {
                    'file': e.file,
                    'line': e.line,
                    'enum_name': e.enum_name,
                    'attribute': e.attribute,
                    'valid_attributes': e.valid_attributes,
                    'message': e.message,
                    'severity': e.severity
                }
                for e in self.errors
            ],
            'total_errors': len(self.errors),
            'enums_found': len(self.all_enums),
            'by_severity': self._count_by_severity()
        }
    
    def _collect_enums(self):
        """Collect all enum definitions in the project."""
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                tree = ast.parse(source, filename=str(py_file))
                
                collector = EnumCollector(str(py_file))
                collector.visit(tree)
                
                # Merge enums from this file
                self.all_enums.update(collector.enums)
                
            except Exception as e:
                # Skip files that can't be parsed
                pass
    
    def _validate_file(self, filepath: Path):
        """Validate enum usage in a single file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=str(filepath))
            
            checker = EnumUsageChecker(filepath, self.project_root, self.all_enums)
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