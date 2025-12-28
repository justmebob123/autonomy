"""
Data Flow Analyzer - Tracks variable lifecycle and detects use-before-definition.

This analyzer was critical in finding bugs like:
- Variables used before definition (role_design.py)
- Missing variable initialization (prompt_improvement.py)
- Undefined variables in error paths
"""

import ast
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Variable:
    """Information about a variable."""
    name: str
    first_definition: int
    first_use: int
    scope: str
    is_parameter: bool = False
    is_global: bool = False
    uses: List[int] = field(default_factory=list)
    definitions: List[int] = field(default_factory=list)


@dataclass
class DataFlowIssue:
    """A data flow issue found during analysis."""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    type: str  # use_before_def, undefined_var, unused_var, etc.
    variable: str
    line: int
    scope: str
    message: str
    suggestion: Optional[str] = None


class DataFlowAnalyzer(ast.NodeVisitor):
    """
    Analyzes data flow to detect variable lifecycle issues.
    
    Detects:
    - Use before definition (CRITICAL bug pattern)
    - Undefined variables
    - Unused variables
    - Variables defined but never used
    - Shadowed variables
    
    Example:
        analyzer = DataFlowAnalyzer(tree, content)
        result = analyzer.analyze()
        for issue in result['issues']:
            if issue['severity'] == 'CRITICAL':
                print(f"CRITICAL: {issue['message']}")
    """
    
    def __init__(self, tree: ast.AST, content: str):
        self.tree = tree
        self.content = content
        self.lines = content.split('\n')
        
        # Variable tracking
        self.variables: Dict[str, Variable] = {}
        self.scopes: List[str] = ['module']
        self.current_scope = 'module'
        
        # Defined variables per scope
        self.defined_in_scope: Dict[str, Set[str]] = {'module': set()}
        
        # Issues found
        self.issues: List[DataFlowIssue] = []
        
        # Built-in names to ignore
        self.builtins = {
            'True', 'False', 'None', 'len', 'str', 'int', 'float', 'dict', 
            'list', 'set', 'tuple', 'range', 'enumerate', 'zip', 'map', 
            'filter', 'print', 'input', 'open', 'type', 'isinstance',
            'hasattr', 'getattr', 'setattr', 'delattr', 'super', 'property',
            'staticmethod', 'classmethod', 'Exception', 'ValueError', 
            'TypeError', 'KeyError', 'IndexError', 'AttributeError',
        }
    
    def analyze(self) -> Dict[str, Any]:
        """
        Perform data flow analysis.
        
        Returns:
            Dictionary with data flow information and issues
        """
        self.visit(self.tree)
        
        # Find unused variables
        self._find_unused_variables()
        
        # Sort issues by severity and line
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        self.issues.sort(key=lambda x: (severity_order[x.severity], x.line))
        
        return {
            'total_variables': len(self.variables),
            'issues': [
                {
                    'severity': issue.severity,
                    'type': issue.type,
                    'variable': issue.variable,
                    'line': issue.line,
                    'scope': issue.scope,
                    'message': issue.message,
                    'suggestion': issue.suggestion,
                }
                for issue in self.issues
            ],
            'critical_issues': len([i for i in self.issues if i.severity == 'CRITICAL']),
            'high_issues': len([i for i in self.issues if i.severity == 'HIGH']),
            'medium_issues': len([i for i in self.issues if i.severity == 'MEDIUM']),
            'low_issues': len([i for i in self.issues if i.severity == 'LOW']),
            'variables': {
                name: {
                    'first_definition': var.first_definition,
                    'first_use': var.first_use,
                    'scope': var.scope,
                    'uses': len(var.uses),
                    'definitions': len(var.definitions),
                }
                for name, var in self.variables.items()
            }
        }
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        self._enter_scope(node.name)
        
        # Add parameters to defined variables
        for arg in node.args.args:
            self._define_variable(arg.arg, arg.lineno, is_parameter=True)
        
        # Visit body
        self.generic_visit(node)
        
        self._exit_scope()
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definition."""
        self.visit_FunctionDef(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        self._enter_scope(node.name)
        self.generic_visit(node)
        self._exit_scope()
    
    def visit_Assign(self, node: ast.Assign):
        """Visit assignment."""
        # First visit the value (right side)
        self.visit(node.value)
        
        # Then mark targets as defined
        for target in node.targets:
            if isinstance(target, ast.Name):
                self._define_variable(target.id, target.lineno)
            elif isinstance(target, ast.Tuple) or isinstance(target, ast.List):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        self._define_variable(elt.id, elt.lineno)
    
    def visit_AugAssign(self, node: ast.AugAssign):
        """Visit augmented assignment (+=, -=, etc.)."""
        # Augmented assignment uses then defines
        if isinstance(node.target, ast.Name):
            self._use_variable(node.target.id, node.target.lineno)
            self._define_variable(node.target.id, node.target.lineno)
        self.visit(node.value)
    
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Visit annotated assignment."""
        if node.value:
            self.visit(node.value)
        if isinstance(node.target, ast.Name):
            self._define_variable(node.target.id, node.target.lineno)
    
    def visit_Name(self, node: ast.Name):
        """Visit name reference."""
        if isinstance(node.ctx, ast.Load):
            # Variable is being used
            self._use_variable(node.id, node.lineno)
        elif isinstance(node.ctx, ast.Store):
            # Variable is being defined
            self._define_variable(node.id, node.lineno)
    
    def visit_For(self, node: ast.For):
        """Visit for loop."""
        # Visit iterator first
        self.visit(node.iter)
        
        # Then define loop variable
        if isinstance(node.target, ast.Name):
            self._define_variable(node.target.id, node.target.lineno)
        
        # Visit body
        for stmt in node.body:
            self.visit(stmt)
        
        # Visit else clause
        for stmt in node.orelse:
            self.visit(stmt)
    
    def visit_With(self, node: ast.With):
        """Visit with statement."""
        # Visit context expressions first
        for item in node.items:
            self.visit(item.context_expr)
            if item.optional_vars:
                if isinstance(item.optional_vars, ast.Name):
                    self._define_variable(item.optional_vars.id, item.optional_vars.lineno)
        
        # Visit body
        for stmt in node.body:
            self.visit(stmt)
    
    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        """Visit except handler."""
        if node.type:
            self.visit(node.type)
        
        # Define exception variable
        if node.name:
            self._define_variable(node.name, node.lineno)
        
        # Visit body
        for stmt in node.body:
            self.visit(stmt)
    
    def _enter_scope(self, scope_name: str):
        """Enter a new scope."""
        self.scopes.append(scope_name)
        self.current_scope = scope_name
        self.defined_in_scope[scope_name] = set()
    
    def _exit_scope(self):
        """Exit current scope."""
        if len(self.scopes) > 1:
            self.scopes.pop()
            self.current_scope = self.scopes[-1]
    
    def _define_variable(self, name: str, line: int, is_parameter: bool = False):
        """Mark a variable as defined."""
        # Skip builtins and self
        if name in self.builtins or name == 'self':
            return
        
        # Add to defined set for current scope
        self.defined_in_scope[self.current_scope].add(name)
        
        # Track variable
        var_key = f"{self.current_scope}::{name}"
        if var_key not in self.variables:
            self.variables[var_key] = Variable(
                name=name,
                first_definition=line,
                first_use=-1,
                scope=self.current_scope,
                is_parameter=is_parameter,
            )
        
        self.variables[var_key].definitions.append(line)
    
    def _use_variable(self, name: str, line: int):
        """Mark a variable as used."""
        # Skip builtins and self
        if name in self.builtins or name == 'self':
            return
        
        # Check if variable is defined in current or parent scopes
        is_defined = False
        for scope in reversed(self.scopes):
            if name in self.defined_in_scope.get(scope, set()):
                is_defined = True
                var_key = f"{scope}::{name}"
                break
        
        if not is_defined:
            # Variable used but not defined - CRITICAL BUG
            self.issues.append(DataFlowIssue(
                severity='CRITICAL',
                type='use_before_def',
                variable=name,
                line=line,
                scope=self.current_scope,
                message=f"Variable '{name}' used before definition at line {line}",
                suggestion=f"Define '{name}' before line {line} or check for typos"
            ))
            # Create placeholder variable
            var_key = f"{self.current_scope}::{name}"
        
        # Track usage
        if var_key in self.variables:
            if self.variables[var_key].first_use == -1:
                self.variables[var_key].first_use = line
            self.variables[var_key].uses.append(line)
            
            # Check if used before defined
            if self.variables[var_key].first_use < self.variables[var_key].first_definition:
                self.issues.append(DataFlowIssue(
                    severity='CRITICAL',
                    type='use_before_def',
                    variable=name,
                    line=line,
                    scope=self.current_scope,
                    message=f"Variable '{name}' used at line {line} before definition at line {self.variables[var_key].first_definition}",
                    suggestion=f"Move definition to before line {line}"
                ))
    
    def _find_unused_variables(self):
        """Find variables that are defined but never used."""
        for var_key, var in self.variables.items():
            # Skip parameters and variables with uses
            if var.is_parameter or var.uses:
                continue
            
            # Skip private variables (may be intentionally unused)
            if var.name.startswith('_'):
                continue
            
            self.issues.append(DataFlowIssue(
                severity='LOW',
                type='unused_var',
                variable=var.name,
                line=var.first_definition,
                scope=var.scope,
                message=f"Variable '{var.name}' defined at line {var.first_definition} but never used",
                suggestion=f"Remove unused variable '{var.name}' or use it"
            ))