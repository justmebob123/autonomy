"""
Complexity Analyzer - Comprehensive cyclomatic complexity analysis.

Calculates complexity metrics for functions, classes, and modules.
Identifies refactoring candidates and complexity hotspots.
"""

import ast
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class FunctionComplexity:
    """Complexity metrics for a single function."""
    name: str
    line: int
    complexity: int
    args_count: int
    returns: bool
    is_async: bool
    is_private: bool
    decorators: List[str]
    nesting_depth: int
    branches: int
    loops: int


class ComplexityAnalyzer(ast.NodeVisitor):
    """
    Analyzes cyclomatic complexity of Python code.
    
    Complexity is calculated as:
    - Base complexity: 1
    - +1 for each: if, elif, while, for, except, with, assert, and, or
    - +1 for each list/dict/set comprehension
    - +1 for each lambda
    
    Example:
        analyzer = ComplexityAnalyzer(tree, content)
        result = analyzer.analyze()
        print(result['average_complexity'])
    """
    
    def __init__(self, tree: ast.AST, content: str):
        self.tree = tree
        self.content = content
        self.lines = content.split('\n')
        
        # Results
        self.functions: List[FunctionComplexity] = []
        self.classes: Dict[str, List[str]] = {}
        
        # Current context
        self.current_function = None
        self.current_class = None
        self.nesting_depth = 0
    
    def analyze(self) -> Dict[str, Any]:
        """
        Perform complexity analysis.
        
        Returns:
            Dictionary with complexity metrics
        """
        self.visit(self.tree)
        
        if not self.functions:
            return {
                'total_functions': 0,
                'average_complexity': 0,
                'max_complexity': 0,
                'functions': [],
                'complexity_distribution': {},
                'refactoring_candidates': [],
            }
        
        complexities = [f.complexity for f in self.functions]
        
        return {
            'total_functions': len(self.functions),
            'average_complexity': sum(complexities) / len(complexities),
            'max_complexity': max(complexities),
            'min_complexity': min(complexities),
            'functions': [
                {
                    'name': f.name,
                    'line': f.line,
                    'complexity': f.complexity,
                    'args_count': f.args_count,
                    'nesting_depth': f.nesting_depth,
                    'branches': f.branches,
                    'loops': f.loops,
                    'is_async': f.is_async,
                    'is_private': f.is_private,
                }
                for f in sorted(self.functions, key=lambda x: x.complexity, reverse=True)
            ],
            'complexity_distribution': self._get_distribution(complexities),
            'refactoring_candidates': self._get_refactoring_candidates(),
        }
    
    def _get_distribution(self, complexities: List[int]) -> Dict[str, int]:
        """Get complexity distribution."""
        return {
            'excellent (<10)': len([c for c in complexities if c < 10]),
            'good (10-20)': len([c for c in complexities if 10 <= c < 20]),
            'acceptable (20-30)': len([c for c in complexities if 20 <= c < 30]),
            'high (30-50)': len([c for c in complexities if 30 <= c < 50]),
            'critical (>50)': len([c for c in complexities if c >= 50]),
        }
    
    def _get_refactoring_candidates(self) -> List[Dict[str, Any]]:
        """Identify functions that need refactoring."""
        candidates = []
        
        for func in self.functions:
            if func.complexity > 30:
                priority = 'CRITICAL' if func.complexity > 50 else 'HIGH'
                effort_days = max(2, func.complexity // 20)
                
                candidates.append({
                    'name': func.name,
                    'line': func.line,
                    'complexity': func.complexity,
                    'priority': priority,
                    'estimated_effort_days': effort_days,
                    'reasons': self._get_refactoring_reasons(func),
                })
        
        return sorted(candidates, key=lambda x: x['complexity'], reverse=True)
    
    def _get_refactoring_reasons(self, func: FunctionComplexity) -> List[str]:
        """Get specific reasons why function needs refactoring."""
        reasons = []
        
        if func.complexity > 50:
            reasons.append("Extremely high complexity (>50)")
        elif func.complexity > 30:
            reasons.append("High complexity (>30)")
        
        if func.nesting_depth > 4:
            reasons.append(f"Deep nesting ({func.nesting_depth} levels)")
        
        if func.branches > 10:
            reasons.append(f"Too many branches ({func.branches})")
        
        if func.loops > 5:
            reasons.append(f"Too many loops ({func.loops})")
        
        if func.args_count > 7:
            reasons.append(f"Too many parameters ({func.args_count})")
        
        return reasons
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        self._analyze_function(node, is_async=False)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definition."""
        self._analyze_function(node, is_async=True)
    
    def _analyze_function(self, node: ast.FunctionDef, is_async: bool):
        """Analyze a function definition."""
        # Calculate complexity
        complexity = self._calculate_complexity(node)
        
        # Get decorators
        decorators = [ast.unparse(d) for d in node.decorator_list]
        
        # Calculate nesting depth
        max_depth = self._calculate_nesting_depth(node)
        
        # Count branches and loops
        branches = self._count_branches(node)
        loops = self._count_loops(node)
        
        # Create function complexity object
        func_complexity = FunctionComplexity(
            name=node.name,
            line=node.lineno,
            complexity=complexity,
            args_count=len(node.args.args),
            returns=any(isinstance(n, ast.Return) for n in ast.walk(node)),
            is_async=is_async,
            is_private=node.name.startswith('_'),
            decorators=decorators,
            nesting_depth=max_depth,
            branches=branches,
            loops=loops,
        )
        
        self.functions.append(func_complexity)
        
        # Track class methods
        if self.current_class:
            if self.current_class not in self.classes:
                self.classes[self.current_class] = []
            self.classes[self.current_class].append(node.name)
        
        # Continue visiting
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for a node."""
        complexity = 1
        
        for child in ast.walk(node):
            # Control flow
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            
            # Context managers
            elif isinstance(child, ast.With):
                complexity += 1
            
            # Assertions
            elif isinstance(child, ast.Assert):
                complexity += 1
            
            # Boolean operations
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            
            # Comprehensions
            elif isinstance(child, ast.comprehension):
                complexity += 1
            
            # Lambda functions
            elif isinstance(child, ast.Lambda):
                complexity += 1
        
        return complexity
    
    def _calculate_nesting_depth(self, node: ast.AST) -> int:
        """Calculate maximum nesting depth."""
        max_depth = 0
        
        def visit(n, depth=0):
            nonlocal max_depth
            max_depth = max(max_depth, depth)
            
            for child in ast.iter_child_nodes(n):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                    visit(child, depth + 1)
                else:
                    visit(child, depth)
        
        visit(node)
        return max_depth
    
    def _count_branches(self, node: ast.AST) -> int:
        """Count number of branches (if/elif/else)."""
        count = 0
        for child in ast.walk(node):
            if isinstance(child, ast.If):
                count += 1
                count += len(child.orelse) if child.orelse else 0
        return count
    
    def _count_loops(self, node: ast.AST) -> int:
        """Count number of loops (for/while)."""
        return sum(1 for child in ast.walk(node) if isinstance(child, (ast.For, ast.While)))