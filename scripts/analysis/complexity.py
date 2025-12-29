#!/usr/bin/env python3
"""
Cyclomatic Complexity Analyzer

Calculates cyclomatic complexity for all functions and methods,
identifies refactoring priorities, and estimates effort.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class ComplexityResult:
    name: str
    file: str
    line: int
    complexity: int
    lines: int
    
    @property
    def priority(self) -> str:
        if self.complexity >= 50:
            return "CRITICAL"
        elif self.complexity >= 30:
            return "URGENT"
        elif self.complexity >= 20:
            return "HIGH"
        elif self.complexity >= 10:
            return "MEDIUM"
        else:
            return "LOW"
    
    @property
    def effort_days(self) -> str:
        if self.complexity >= 100:
            return "7-10 days"
        elif self.complexity >= 50:
            return "5-7 days"
        elif self.complexity >= 30:
            return "3-5 days"
        elif self.complexity >= 20:
            return "2-3 days"
        elif self.complexity >= 10:
            return "1-2 days"
        else:
            return "<1 day"

class ComplexityAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.results: List[ComplexityResult] = []
        self.current_file = None
        self.current_class = None
        
    def calculate_complexity(self, node) -> int:
        """Calculate cyclomatic complexity for a function/method"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With, ast.AsyncWith):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            # Logical operators
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            # Comprehensions
            elif isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                complexity += 1
                
        return complexity
    
    def count_lines(self, node) -> int:
        """Count lines of code in a function"""
        if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
            return node.end_lineno - node.lineno + 1
        return 0
        
    def visit_FunctionDef(self, node):
        complexity = self.calculate_complexity(node)
        lines = self.count_lines(node)
        
        if self.current_class:
            name = f"{self.current_class}.{node.name}"
        else:
            name = node.name
            
        result = ComplexityResult(
            name=name,
            file=self.current_file,
            line=node.lineno,
            complexity=complexity,
            lines=lines
        )
        self.results.append(result)
        
        self.generic_visit(node)
        
    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)
        
    def visit_ClassDef(self, node):
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
        
    def analyze_file(self, filepath: str):
        self.current_file = filepath
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=filepath)
                self.visit(tree)
        except Exception as e:
            print(f"Error analyzing {filepath}: {e}")

def analyze_directory(directory: str = "autonomy") -> ComplexityAnalyzer:
    """Analyze all Python files in directory"""
    analyzer = ComplexityAnalyzer()
    
    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ and .git
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', '.venv']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                analyzer.analyze_file(filepath)
    
    return analyzer

def generate_report(analyzer: ComplexityAnalyzer):
    """Generate comprehensive complexity report"""
    report = []
    report.append("=" * 80)
    report.append("CYCLOMATIC COMPLEXITY ANALYSIS REPORT")
    report.append("=" * 80)
    report.append("")
    
    # Sort by complexity (highest first)
    sorted_results = sorted(analyzer.results, key=lambda x: x.complexity, reverse=True)
    
    # Top 20 most complex functions
    report.append("## TOP 20 MOST COMPLEX FUNCTIONS")
    report.append("")
    report.append(f"{'Rank':<6} {'Complexity':<12} {'Priority':<12} {'Effort':<15} {'Function':<50} {'File:Line'}")
    report.append("-" * 150)
    
    for i, result in enumerate(sorted_results[:20], 1):
        report.append(f"{i:<6} {result.complexity:<12} {result.priority:<12} {result.effort_days:<15} {result.name:<50} {result.file}:{result.line}")
    report.append("")
    
    # Complexity distribution
    report.append("## COMPLEXITY DISTRIBUTION")
    report.append("")
    
    critical = [r for r in sorted_results if r.complexity >= 50]
    urgent = [r for r in sorted_results if 30 <= r.complexity < 50]
    high = [r for r in sorted_results if 20 <= r.complexity < 30]
    medium = [r for r in sorted_results if 10 <= r.complexity < 20]
    low = [r for r in sorted_results if r.complexity < 10]
    
    report.append(f"CRITICAL (>=50): {len(critical)} functions")
    report.append(f"URGENT (30-49): {len(urgent)} functions")
    report.append(f"HIGH (20-29): {len(high)} functions")
    report.append(f"MEDIUM (10-19): {len(medium)} functions")
    report.append(f"LOW (<10): {len(low)} functions")
    report.append("")
    
    # Refactoring priorities
    report.append("## REFACTORING PRIORITIES")
    report.append("")
    
    if critical:
        report.append("### CRITICAL PRIORITY (Complexity >= 50)")
        for result in critical:
            report.append(f"- {result.name} (complexity {result.complexity}, {result.effort_days})")
            report.append(f"  Location: {result.file}:{result.line}")
            report.append(f"  Lines: {result.lines}")
            report.append("")
    
    if urgent:
        report.append("### URGENT PRIORITY (Complexity 30-49)")
        for result in urgent:
            report.append(f"- {result.name} (complexity {result.complexity}, {result.effort_days})")
            report.append(f"  Location: {result.file}:{result.line}")
            report.append(f"  Lines: {result.lines}")
            report.append("")
    
    # Effort estimation
    report.append("## EFFORT ESTIMATION")
    report.append("")
    
    total_critical_days = len(critical) * 7  # Average 7 days per critical function
    total_urgent_days = len(urgent) * 5  # Average 5 days per urgent function
    total_high_days = len(high) * 2.5  # Average 2.5 days per high function
    
    report.append(f"Critical functions: {len(critical)} × 7 days = {total_critical_days} days")
    report.append(f"Urgent functions: {len(urgent)} × 5 days = {total_urgent_days} days")
    report.append(f"High priority functions: {len(high)} × 2.5 days = {total_high_days} days")
    report.append(f"Total estimated effort: {total_critical_days + total_urgent_days + total_high_days} days")
    report.append("")
    
    # Summary statistics
    report.append("=" * 80)
    report.append("SUMMARY STATISTICS")
    report.append("=" * 80)
    
    total_functions = len(sorted_results)
    avg_complexity = sum(r.complexity for r in sorted_results) / total_functions if total_functions > 0 else 0
    max_complexity = sorted_results[0].complexity if sorted_results else 0
    
    report.append(f"Total functions analyzed: {total_functions}")
    report.append(f"Average complexity: {avg_complexity:.2f}")
    report.append(f"Maximum complexity: {max_complexity}")
    report.append(f"Functions needing refactoring (>=10): {len(critical) + len(urgent) + len(high) + len(medium)}")
    report.append("")
    
    return "\n".join(report)

if __name__ == "__main__":
    print("Starting complexity analysis...")
    analyzer = analyze_directory()
    report = generate_report(analyzer)
    
    # Save report
    with open("COMPLEXITY_REPORT.txt", "w") as f:
        f.write(report)
    
    print(report)
    print("\nReport saved to COMPLEXITY_REPORT.txt")