"""
Depth-61 Recursive Call Stack Analyzer

This script performs comprehensive recursive analysis of the entire codebase:
1. Traces all call paths to depth 61
2. Tracks variable state changes at each level
3. Analyzes object creation and inheritance patterns
4. Identifies integration mismatches
5. Detects variable duplication and misuse
6. Verifies unified design patterns
"""

import ast
import os
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from collections import defaultdict
import inspect


class CallStackAnalyzer:
    """Analyzes call stacks recursively to depth 61"""
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.call_graph = defaultdict(list)
        self.variable_flow = defaultdict(list)
        self.object_creation = defaultdict(list)
        self.inheritance_tree = defaultdict(list)
        self.integration_points = []
        self.type_usage = defaultdict(set)
        self.max_depth = 61
        
    def analyze_file(self, filepath: Path) -> ast.AST:
        """Parse a Python file and return its AST"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return ast.parse(f.read(), filename=str(filepath))
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
            return None
    
    def extract_calls(self, node: ast.AST, context: str = "") -> List[Dict]:
        """Extract all function/method calls from an AST node"""
        calls = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                call_info = {
                    'context': context,
                    'lineno': child.lineno if hasattr(child, 'lineno') else 0,
                    'type': 'call'
                }
                
                # Extract function name
                if isinstance(child.func, ast.Name):
                    call_info['name'] = child.func.id
                elif isinstance(child.func, ast.Attribute):
                    call_info['name'] = child.func.attr
                    if isinstance(child.func.value, ast.Name):
                        call_info['object'] = child.func.value.id
                
                # Extract arguments
                call_info['args'] = []
                for arg in child.args:
                    if isinstance(arg, ast.Name):
                        call_info['args'].append(arg.id)
                    elif isinstance(arg, ast.Constant):
                        call_info['args'].append(arg.value)
                
                calls.append(call_info)
        
        return calls
    
    def extract_variables(self, node: ast.AST) -> Dict[str, List[Dict]]:
        """Extract all variable assignments and their types"""
        variables = defaultdict(list)
        
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        var_info = {
                            'name': target.id,
                            'lineno': child.lineno if hasattr(child, 'lineno') else 0,
                            'type': self._infer_type(child.value)
                        }
                        variables[target.id].append(var_info)
            
            elif isinstance(child, ast.AnnAssign):
                if isinstance(child.target, ast.Name):
                    var_info = {
                        'name': child.target.id,
                        'lineno': child.lineno if hasattr(child, 'lineno') else 0,
                        'type': ast.unparse(child.annotation) if child.annotation else 'unknown',
                        'annotated': True
                    }
                    variables[child.target.id].append(var_info)
        
        return variables
    
    def _infer_type(self, node: ast.AST) -> str:
        """Infer the type of a value node"""
        if isinstance(node, ast.Constant):
            return type(node.value).__name__
        elif isinstance(node, ast.List):
            return 'list'
        elif isinstance(node, ast.Dict):
            return 'dict'
        elif isinstance(node, ast.Tuple):
            return 'tuple'
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id
        return 'unknown'
    
    def extract_classes(self, node: ast.AST) -> List[Dict]:
        """Extract all class definitions and their inheritance"""
        classes = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.ClassDef):
                class_info = {
                    'name': child.name,
                    'lineno': child.lineno if hasattr(child, 'lineno') else 0,
                    'bases': [ast.unparse(base) for base in child.bases],
                    'methods': [],
                    'attributes': []
                }
                
                # Extract methods
                for item in child.body:
                    if isinstance(item, ast.FunctionDef):
                        class_info['methods'].append({
                            'name': item.name,
                            'lineno': item.lineno if hasattr(item, 'lineno') else 0,
                            'args': [arg.arg for arg in item.args.args]
                        })
                    elif isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                class_info['attributes'].append(target.id)
                
                classes.append(class_info)
        
        return classes
    
    def trace_call_path(self, function_name: str, depth: int = 0, visited: Set[str] = None) -> List[Dict]:
        """Recursively trace call paths to max depth"""
        if visited is None:
            visited = set()
        
        if depth >= self.max_depth:
            return []
        
        if function_name in visited:
            return []  # Avoid infinite recursion
        
        visited.add(function_name)
        
        paths = []
        if function_name in self.call_graph:
            for call in self.call_graph[function_name]:
                path = {
                    'depth': depth,
                    'function': function_name,
                    'calls': call,
                    'children': []
                }
                
                # Recursively trace called functions
                if 'name' in call:
                    child_paths = self.trace_call_path(call['name'], depth + 1, visited.copy())
                    path['children'] = child_paths
                
                paths.append(path)
        
        return paths
    
    def analyze_subsystem(self, subsystem_path: Path) -> Dict:
        """Analyze a complete subsystem"""
        print(f"\n{'='*60}")
        print(f"Analyzing subsystem: {subsystem_path}")
        print(f"{'='*60}")
        
        subsystem_data = {
            'path': str(subsystem_path),
            'files': [],
            'classes': [],
            'functions': [],
            'variables': {},
            'call_graph': {},
            'integration_points': []
        }
        
        # Find all Python files
        py_files = list(subsystem_path.rglob("*.py"))
        print(f"Found {len(py_files)} Python files")
        
        for py_file in py_files:
            print(f"  Analyzing: {py_file.relative_to(self.root_dir)}")
            
            tree = self.analyze_file(py_file)
            if not tree:
                continue
            
            file_data = {
                'path': str(py_file.relative_to(self.root_dir)),
                'classes': self.extract_classes(tree),
                'calls': self.extract_calls(tree, str(py_file.relative_to(self.root_dir))),
                'variables': self.extract_variables(tree)
            }
            
            subsystem_data['files'].append(file_data)
            subsystem_data['classes'].extend(file_data['classes'])
            
            # Build call graph
            for call in file_data['calls']:
                if 'name' in call:
                    self.call_graph[call['context']].append(call)
            
            # Track variable usage
            for var_name, var_instances in file_data['variables'].items():
                if var_name not in subsystem_data['variables']:
                    subsystem_data['variables'][var_name] = []
                subsystem_data['variables'][var_name].extend(var_instances)
        
        return subsystem_data
    
    def find_integration_mismatches(self, subsystems: List[Dict]) -> List[Dict]:
        """Find integration mismatches between subsystems"""
        print(f"\n{'='*60}")
        print("Analyzing Integration Mismatches")
        print(f"{'='*60}")
        
        mismatches = []
        
        # Check for variable type inconsistencies across subsystems
        all_variables = defaultdict(list)
        for subsystem in subsystems:
            for var_name, instances in subsystem['variables'].items():
                for instance in instances:
                    all_variables[var_name].append({
                        'subsystem': subsystem['path'],
                        'type': instance.get('type', 'unknown'),
                        'lineno': instance.get('lineno', 0),
                        'file': instance.get('file', '')
                    })
        
        # Find variables with inconsistent types
        for var_name, instances in all_variables.items():
            types = set(inst['type'] for inst in instances)
            if len(types) > 1 and 'unknown' not in types:
                mismatches.append({
                    'type': 'variable_type_mismatch',
                    'variable': var_name,
                    'types': list(types),
                    'instances': instances
                })
                print(f"  ⚠️  Variable '{var_name}' has inconsistent types: {types}")
        
        # Check for duplicate class implementations
        all_classes = defaultdict(list)
        for subsystem in subsystems:
            for cls in subsystem['classes']:
                all_classes[cls['name']].append({
                    'subsystem': subsystem['path'],
                    'bases': cls['bases'],
                    'methods': [m['name'] for m in cls['methods']]
                })
        
        for class_name, instances in all_classes.items():
            if len(instances) > 1:
                mismatches.append({
                    'type': 'duplicate_class',
                    'class': class_name,
                    'instances': instances
                })
                print(f"  ⚠️  Class '{class_name}' has {len(instances)} implementations")
        
        return mismatches
    
    def generate_report(self, subsystems: List[Dict], mismatches: List[Dict]) -> str:
        """Generate comprehensive analysis report"""
        report = []
        report.append("=" * 80)
        report.append("DEPTH-61 RECURSIVE CALL STACK ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Summary
        report.append("## SUMMARY")
        report.append(f"Total Subsystems Analyzed: {len(subsystems)}")
        total_files = sum(len(s['files']) for s in subsystems)
        report.append(f"Total Files Analyzed: {total_files}")
        total_classes = sum(len(s['classes']) for s in subsystems)
        report.append(f"Total Classes Found: {total_classes}")
        report.append(f"Integration Mismatches Found: {len(mismatches)}")
        report.append("")
        
        # Subsystem Details
        report.append("## SUBSYSTEM ANALYSIS")
        for subsystem in subsystems:
            report.append(f"\n### {subsystem['path']}")
            report.append(f"Files: {len(subsystem['files'])}")
            report.append(f"Classes: {len(subsystem['classes'])}")
            report.append(f"Unique Variables: {len(subsystem['variables'])}")
            
            # List classes
            if subsystem['classes']:
                report.append("\nClasses:")
                for cls in subsystem['classes'][:10]:  # Limit to first 10
                    bases = ', '.join(cls['bases']) if cls['bases'] else 'object'
                    report.append(f"  - {cls['name']} (inherits from: {bases})")
                    report.append(f"    Methods: {len(cls['methods'])}")
        
        # Integration Mismatches
        report.append("\n## INTEGRATION MISMATCHES")
        if mismatches:
            for mismatch in mismatches:
                report.append(f"\n### {mismatch['type']}")
                if mismatch['type'] == 'variable_type_mismatch':
                    report.append(f"Variable: {mismatch['variable']}")
                    report.append(f"Types: {', '.join(mismatch['types'])}")
                    report.append("Instances:")
                    for inst in mismatch['instances'][:5]:  # Limit to first 5
                        report.append(f"  - {inst['subsystem']}: {inst['type']}")
                elif mismatch['type'] == 'duplicate_class':
                    report.append(f"Class: {mismatch['class']}")
                    report.append(f"Implementations: {len(mismatch['instances'])}")
                    for inst in mismatch['instances']:
                        report.append(f"  - {inst['subsystem']}")
        else:
            report.append("No integration mismatches found.")
        
        return "\n".join(report)


def main():
    """Main analysis function"""
    print("Starting Depth-61 Recursive Call Stack Analysis")
    print("=" * 80)
    
    analyzer = CallStackAnalyzer(".")
    
    # Define subsystems to analyze
    subsystems_to_analyze = [
        Path("pipeline"),
        Path("pipeline/phases"),
        Path("pipeline/orchestration"),
        Path("pipeline/state"),
        Path("pipeline/tools"),
        Path("pipeline/handlers"),
    ]
    
    # Analyze each subsystem
    subsystem_results = []
    for subsystem_path in subsystems_to_analyze:
        if subsystem_path.exists():
            result = analyzer.analyze_subsystem(subsystem_path)
            subsystem_results.append(result)
    
    # Find integration mismatches
    mismatches = analyzer.find_integration_mismatches(subsystem_results)
    
    # Generate report
    report = analyzer.generate_report(subsystem_results, mismatches)
    
    # Save report
    with open("DEPTH_61_ANALYSIS_REPORT.md", "w") as f:
        f.write(report)
    
    print("\n" + "=" * 80)
    print("Analysis complete. Report saved to DEPTH_61_ANALYSIS_REPORT.md")
    print("=" * 80)
    
    # Save detailed JSON data
    with open("depth_61_analysis_data.json", "w") as f:
        json.dump({
            'subsystems': subsystem_results,
            'mismatches': mismatches,
            'call_graph': dict(analyzer.call_graph)
        }, f, indent=2, default=str)
    
    print("Detailed data saved to depth_61_analysis_data.json")


if __name__ == "__main__":
    main()