"""
Analyze variable type inconsistencies across the codebase
"""

import ast
from pathlib import Path
from collections import defaultdict


def infer_type(node):
    """Infer the type of a value node"""
    if isinstance(node, ast.Constant):
        return type(node.value).__name__
    elif isinstance(node, ast.List):
        return 'list'
    elif isinstance(node, ast.Dict):
        return 'dict'
    elif isinstance(node, ast.Tuple):
        return 'tuple'
    elif isinstance(node, ast.Set):
        return 'set'
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
    return 'unknown'


def analyze_variables():
    """Analyze all variables in the codebase"""
    var_types = defaultdict(lambda: defaultdict(list))
    
    for py_file in Path('pipeline').rglob('*.py'):
        try:
            with open(py_file, 'r') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id
                            var_type = infer_type(node.value)
                            file_path = str(py_file.relative_to('.'))
                            var_types[var_name][var_type].append({
                                'file': file_path,
                                'line': node.lineno if hasattr(node, 'lineno') else 0
                            })
        except Exception as e:
            pass
    
    # Find variables with multiple types (excluding 'unknown')
    inconsistent = {}
    for var_name, types in var_types.items():
        real_types = {t: locs for t, locs in types.items() if t != 'unknown'}
        if len(real_types) > 1:
            inconsistent[var_name] = {
                'types': list(real_types.keys()),
                'locations': real_types,
                'total_count': sum(len(locs) for locs in real_types.values())
            }
    
    return inconsistent


def main():
    print("="*80)
    print("VARIABLE TYPE INCONSISTENCY ANALYSIS")
    print("="*80)
    print()
    
    inconsistent = analyze_variables()
    
    print(f"Total variables with type inconsistencies: {len(inconsistent)}")
    print()
    
    # Sort by number of occurrences
    sorted_vars = sorted(inconsistent.items(), key=lambda x: x[1]['total_count'], reverse=True)
    
    print("TOP 20 VARIABLES WITH TYPE INCONSISTENCIES:")
    print("-"*80)
    
    for i, (var_name, info) in enumerate(sorted_vars[:20], 1):
        print(f"\n{i}. Variable: '{var_name}'")
        print(f"   Types: {', '.join(info['types'])}")
        print(f"   Total occurrences: {info['total_count']}")
        
        # Show first 3 locations for each type
        for var_type, locations in info['locations'].items():
            print(f"   - Type '{var_type}': {len(locations)} occurrences")
            for loc in locations[:2]:
                print(f"     * {loc['file']}:{loc['line']}")
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()