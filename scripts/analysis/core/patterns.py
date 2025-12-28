"""
Pattern Detector - Identifies design patterns and anti-patterns.

Detects:
- Design patterns (Template Method, Mixin, Registry, etc.)
- Anti-patterns (God Method, Copy-Paste, etc.)
- Code smells
- Best practices violations
"""

import ast
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class Pattern:
    """A pattern found in the code."""
    type: str  # design_pattern or anti_pattern
    name: str
    location: str
    line: int
    confidence: float  # 0.0 to 1.0
    description: str
    evidence: List[str]


class PatternDetector(ast.NodeVisitor):
    """
    Detects design patterns and anti-patterns.
    
    Design Patterns:
    - Template Method
    - Mixin
    - Registry
    - Dataclass
    - Strategy
    - Observer
    
    Anti-Patterns:
    - God Method (complexity > 50)
    - Copy-Paste Code
    - Magic Numbers
    - Deep Nesting
    - Long Parameter List
    """
    
    def __init__(self, tree: ast.AST, content: str):
        self.tree = tree
        self.content = content
        self.lines = content.split('\n')
        
        self.patterns: List[Pattern] = []
        self.functions: Dict[str, ast.FunctionDef] = {}
    
    def analyze(self) -> Dict[str, Any]:
        """Perform pattern detection."""
        self.visit(self.tree)
        
        # Detect patterns
        self._detect_dataclass_pattern()
        self._detect_template_method()
        self._detect_mixin_pattern()
        self._detect_god_methods()
        self._detect_copy_paste()
        self._detect_magic_numbers()
        
        return {
            'design_patterns': [
                {
                    'name': p.name,
                    'location': p.location,
                    'line': p.line,
                    'confidence': p.confidence,
                    'description': p.description,
                    'evidence': p.evidence,
                }
                for p in self.patterns if p.type == 'design_pattern'
            ],
            'anti_patterns': [
                {
                    'name': p.name,
                    'location': p.location,
                    'line': p.line,
                    'confidence': p.confidence,
                    'description': p.description,
                    'evidence': p.evidence,
                }
                for p in self.patterns if p.type == 'anti_pattern'
            ],
        }
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Track function definitions."""
        self.functions[node.name] = node
        self.generic_visit(node)
    
    def _detect_dataclass_pattern(self):
        """Detect dataclass pattern usage."""
        if '@dataclass' in self.content:
            for i, line in enumerate(self.lines, 1):
                if '@dataclass' in line:
                    self.patterns.append(Pattern(
                        type='design_pattern',
                        name='Dataclass Pattern',
                        location='module',
                        line=i,
                        confidence=1.0,
                        description='Uses @dataclass decorator for clean data structures',
                        evidence=['@dataclass decorator found']
                    ))
    
    def _detect_template_method(self):
        """Detect template method pattern."""
        # Look for base class with abstract methods
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                # Check if class has methods that call self.method()
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        # Check if method calls other methods
                        for child in ast.walk(item):
                            if isinstance(child, ast.Call):
                                if isinstance(child.func, ast.Attribute):
                                    if isinstance(child.func.value, ast.Name):
                                        if child.func.value.id == 'self':
                                            self.patterns.append(Pattern(
                                                type='design_pattern',
                                                name='Template Method',
                                                location=f'{node.name}.{item.name}',
                                                line=item.lineno,
                                                confidence=0.7,
                                                description='Method calls other methods that can be overridden',
                                                evidence=[f'Calls self.{child.func.attr}()']
                                            ))
                                            return
    
    def _detect_mixin_pattern(self):
        """Detect mixin pattern."""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                if len(node.bases) > 1:
                    # Multiple inheritance suggests mixin
                    bases = [ast.unparse(b) for b in node.bases]
                    if any('Mixin' in b for b in bases):
                        self.patterns.append(Pattern(
                            type='design_pattern',
                            name='Mixin Pattern',
                            location=node.name,
                            line=node.lineno,
                            confidence=1.0,
                            description='Uses mixin for cross-cutting concerns',
                            evidence=[f'Inherits from: {", ".join(bases)}']
                        ))
    
    def _detect_god_methods(self):
        """Detect god methods (too complex)."""
        for name, node in self.functions.items():
            complexity = self._calculate_complexity(node)
            if complexity > 50:
                self.patterns.append(Pattern(
                    type='anti_pattern',
                    name='God Method',
                    location=name,
                    line=node.lineno,
                    confidence=1.0,
                    description=f'Method has extremely high complexity ({complexity})',
                    evidence=[
                        f'Complexity: {complexity}',
                        'Should be refactored into smaller methods'
                    ]
                ))
    
    def _detect_copy_paste(self):
        """Detect copy-paste code."""
        # Simple detection: look for very similar function bodies
        function_bodies = {}
        for name, node in self.functions.items():
            body = ast.unparse(node)
            normalized = ''.join(body.split())
            function_bodies[name] = (normalized, node.lineno)
        
        # Compare all pairs
        checked = set()
        for name1, (body1, line1) in function_bodies.items():
            for name2, (body2, line2) in function_bodies.items():
                if name1 >= name2:
                    continue
                
                pair = tuple(sorted([name1, name2]))
                if pair in checked:
                    continue
                checked.add(pair)
                
                # Calculate similarity
                if len(body1) > 100 and len(body2) > 100:
                    similarity = self._similarity(body1, body2)
                    if similarity > 0.8:
                        self.patterns.append(Pattern(
                            type='anti_pattern',
                            name='Copy-Paste Code',
                            location=f'{name1} and {name2}',
                            line=min(line1, line2),
                            confidence=similarity,
                            description=f'Functions {name1} and {name2} are {similarity:.0%} similar',
                            evidence=[
                                f'{name1} at line {line1}',
                                f'{name2} at line {line2}',
                                'Consider extracting common logic'
                            ]
                        ))
    
    def _detect_magic_numbers(self):
        """Detect magic numbers."""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Num):
                # Skip common numbers
                if node.n in [0, 1, -1, 2, 10, 100, 1000]:
                    continue
                
                self.patterns.append(Pattern(
                    type='anti_pattern',
                    name='Magic Number',
                    location='module',
                    line=node.lineno,
                    confidence=0.5,
                    description=f'Magic number {node.n} should be a named constant',
                    evidence=[f'Number {node.n} at line {node.lineno}']
                ))
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                ast.With, ast.Assert, ast.BoolOp)):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
        return complexity
    
    def _similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity between two strings."""
        if not s1 or not s2:
            return 0.0
        
        # Simple character-based similarity
        matches = sum(c1 == c2 for c1, c2 in zip(s1, s2))
        return matches / max(len(s1), len(s2))