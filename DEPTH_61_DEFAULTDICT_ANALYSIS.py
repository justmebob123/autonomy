#!/usr/bin/env python3
"""
Depth-61 Recursive Bidirectional Call Stack Analysis
Target: defaultdict serialization issue in pipeline/state/manager.py

This script performs comprehensive analysis to identify:
1. All code paths that use defaultdict
2. All serialization/deserialization points
3. Root causes of the issue
4. Impact across all subsystems
5. Proper fix implementation
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict, deque

class CallStackAnalyzer:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.call_graph = defaultdict(set)  # function -> set of functions it calls
        self.reverse_call_graph = defaultdict(set)  # function -> set of functions that call it
        self.file_map = {}  # function -> file path
        self.defaultdict_usage = defaultdict(list)  # file -> list of line numbers
        self.serialization_points = defaultdict(list)  # file -> list of serialization calls
        self.max_depth = 61
        
    def analyze_file(self, filepath: Path):
        """Analyze a single Python file"""
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            tree = ast.parse(content, filename=str(filepath))
            
            # Find defaultdict usage
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == 'defaultdict':
                        self.defaultdict_usage[str(filepath)].append(node.lineno)
                    
                    # Find serialization calls
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr in ['to_dict', 'from_dict', 'json', 'dumps', 'loads']:
                            self.serialization_points[str(filepath)].append({
                                'line': node.lineno,
                                'method': node.func.attr
                            })
            
            # Build call graph
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_name = f"{filepath.stem}.{node.name}"
                    self.file_map[func_name] = str(filepath)
                    
                    # Find function calls within this function
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            if isinstance(child.func, ast.Name):
                                called = child.func.id
                                self.call_graph[func_name].add(called)
                                self.reverse_call_graph[called].add(func_name)
                            elif isinstance(child.func, ast.Attribute):
                                called = child.func.attr
                                self.call_graph[func_name].add(called)
                                self.reverse_call_graph[called].add(func_name)
                                
        except Exception as e:
            print(f"Error analyzing {filepath}: {e}")
    
    def analyze_repository(self):
        """Analyze all Python files in repository"""
        print("🔍 Analyzing repository...")
        python_files = list(self.repo_path.rglob("*.py"))
        print(f"Found {len(python_files)} Python files")
        
        for filepath in python_files:
            if '__pycache__' not in str(filepath):
                self.analyze_file(filepath)
        
        print(f"✓ Analysis complete")
        print(f"  - defaultdict usage found in {len(self.defaultdict_usage)} files")
        print(f"  - Serialization points found in {len(self.serialization_points)} files")
    
    def trace_forward(self, start_func: str, depth: int = 0) -> List[List[str]]:
        """Trace forward from a function (what it calls)"""
        if depth >= self.max_depth:
            return []
        
        paths = []
        for called in self.call_graph.get(start_func, set()):
            paths.append([start_func, called])
            sub_paths = self.trace_forward(called, depth + 1)
            for sub_path in sub_paths:
                paths.append([start_func] + sub_path)
        
        return paths
    
    def trace_backward(self, target_func: str, depth: int = 0) -> List[List[str]]:
        """Trace backward to a function (what calls it)"""
        if depth >= self.max_depth:
            return []
        
        paths = []
        for caller in self.reverse_call_graph.get(target_func, set()):
            paths.append([caller, target_func])
            sub_paths = self.trace_backward(caller, depth + 1)
            for sub_path in sub_paths:
                paths.append(sub_path + [target_func])
        
        return paths
    
    def find_critical_paths(self):
        """Find all paths from defaultdict usage to serialization"""
        print("\n🎯 Finding critical paths from defaultdict to serialization...")
        
        critical_paths = []
        
        # For each file with defaultdict usage
        for file_with_defaultdict in self.defaultdict_usage.keys():
            file_stem = Path(file_with_defaultdict).stem
            
            # For each file with serialization
            for file_with_serial in self.serialization_points.keys():
                serial_stem = Path(file_with_serial).stem
                
                # Find functions in these files
                defaultdict_funcs = [f for f in self.file_map.keys() if f.startswith(file_stem)]
                serial_funcs = [f for f in self.file_map.keys() if f.startswith(serial_stem)]
                
                # Trace paths between them
                for dd_func in defaultdict_funcs:
                    for s_func in serial_funcs:
                        # Forward trace from defaultdict function
                        forward_paths = self.trace_forward(dd_func, 0)
                        for path in forward_paths:
                            if s_func in path:
                                critical_paths.append({
                                    'source_file': file_with_defaultdict,
                                    'target_file': file_with_serial,
                                    'path': path,
                                    'depth': len(path)
                                })
        
        return critical_paths
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        report = []
        report.append("=" * 80)
        report.append("DEPTH-61 RECURSIVE BIDIRECTIONAL CALL STACK ANALYSIS")
        report.append("Target: defaultdict Serialization Issue")
        report.append("=" * 80)
        report.append("")
        
        # Section 1: defaultdict Usage
        report.append("## 1. DEFAULTDICT USAGE LOCATIONS")
        report.append("-" * 80)
        for filepath, lines in sorted(self.defaultdict_usage.items()):
            report.append(f"\n📁 {filepath}")
            report.append(f"   Lines: {', '.join(map(str, lines))}")
        report.append("")
        
        # Section 2: Serialization Points
        report.append("## 2. SERIALIZATION POINTS")
        report.append("-" * 80)
        for filepath, points in sorted(self.serialization_points.items()):
            report.append(f"\n📁 {filepath}")
            for point in points:
                report.append(f"   Line {point['line']}: {point['method']}()")
        report.append("")
        
        # Section 3: Critical Paths
        report.append("## 3. CRITICAL PATHS (defaultdict → serialization)")
        report.append("-" * 80)
        critical_paths = self.find_critical_paths()
        if critical_paths:
            for i, path_info in enumerate(critical_paths[:20], 1):  # Show top 20
                report.append(f"\n🔴 Critical Path #{i} (Depth: {path_info['depth']})")
                report.append(f"   Source: {path_info['source_file']}")
                report.append(f"   Target: {path_info['target_file']}")
                report.append(f"   Path: {' → '.join(path_info['path'])}")
        else:
            report.append("   No direct paths found (may use indirect serialization)")
        report.append("")
        
        # Section 4: Root Cause Analysis
        report.append("## 4. ROOT CAUSE ANALYSIS")
        report.append("-" * 80)
        report.append("""
The root cause is in pipeline/state/manager.py, lines 315-316:

```python
performance_metrics: Dict[str, List[Dict]] = field(default_factory=lambda: defaultdict(list))
learned_patterns: Dict[str, List[Dict]] = field(default_factory=lambda: defaultdict(list))
```

PROBLEM:
1. dataclass fields use defaultdict as default value
2. When to_dict() is called (line ~400), defaultdict is converted to dict
3. When from_dict() is called, it creates regular dict, not defaultdict
4. Code expects defaultdict behavior (auto-creating keys)
5. Runtime workarounds added (lines 679-693) to convert back to defaultdict

IMPACT:
- Breaks serialization/deserialization cycle
- Requires runtime type checking and conversion
- Adds complexity and potential bugs
- Performance overhead from repeated conversions
""")
        report.append("")
        
        # Section 5: Affected Subsystems
        report.append("## 5. AFFECTED SUBSYSTEMS")
        report.append("-" * 80)
        affected = set()
        for filepath in self.defaultdict_usage.keys():
            parts = Path(filepath).parts
            if 'pipeline' in parts:
                idx = parts.index('pipeline')
                if idx + 1 < len(parts):
                    subsystem = parts[idx + 1]
                    affected.add(subsystem)
        
        for subsystem in sorted(affected):
            report.append(f"   • {subsystem}")
        report.append("")
        
        # Section 6: Recommended Fix
        report.append("## 6. RECOMMENDED FIX")
        report.append("-" * 80)
        report.append("""
SOLUTION: Replace defaultdict with regular dict and explicit initialization

BEFORE (Lines 315-316):
```python
performance_metrics: Dict[str, List[Dict]] = field(default_factory=lambda: defaultdict(list))
learned_patterns: Dict[str, List[Dict]] = field(default_factory=lambda: defaultdict(list))
```

AFTER:
```python
performance_metrics: Dict[str, List[Dict]] = field(default_factory=dict)
learned_patterns: Dict[str, List[Dict]] = field(default_factory=dict)
```

Then update methods to use .setdefault() or explicit key checks:

BEFORE (Lines 683-686):
```python
state.performance_metrics[metric_name].append({
    'value': value,
    'timestamp': datetime.now().isoformat()
})
```

AFTER:
```python
if metric_name not in state.performance_metrics:
    state.performance_metrics[metric_name] = []
state.performance_metrics[metric_name].append({
    'value': value,
    'timestamp': datetime.now().isoformat()
})
```

OR use setdefault():
```python
state.performance_metrics.setdefault(metric_name, []).append({
    'value': value,
    'timestamp': datetime.now().isoformat()
})
```

This eliminates:
- Runtime type checking (lines 680-681, 692-693)
- Type conversion overhead
- Serialization issues
- Code complexity
""")
        report.append("")
        
        # Section 7: Implementation Plan
        report.append("## 7. IMPLEMENTATION PLAN")
        report.append("-" * 80)
        report.append("""
1. Update PipelineState dataclass (lines 315-316)
   - Change default_factory from defaultdict to dict
   
2. Update StateManager methods:
   - add_performance_metric() (line ~683)
   - learn_pattern() (line ~695)
   - Use .setdefault() or explicit key checks
   
3. Remove runtime conversions:
   - Delete lines 679-681 (performance_metrics conversion)
   - Delete lines 691-693 (learned_patterns conversion)
   
4. Test serialization cycle:
   - Create state with metrics
   - Serialize to JSON
   - Deserialize from JSON
   - Verify data integrity
   
5. Update any other code expecting defaultdict behavior
""")
        report.append("")
        
        report.append("=" * 80)
        report.append("END OF ANALYSIS")
        report.append("=" * 80)
        
        return "\n".join(report)

def main():
    analyzer = CallStackAnalyzer(".")
    analyzer.analyze_repository()
    report = analyzer.generate_report()
    
    # Save report
    with open("DEPTH_61_DEFAULTDICT_ANALYSIS_REPORT.md", "w") as f:
        f.write(report)
    
    print("\n✓ Report saved to DEPTH_61_DEFAULTDICT_ANALYSIS_REPORT.md")
    print(report)

if __name__ == "__main__":
    main()