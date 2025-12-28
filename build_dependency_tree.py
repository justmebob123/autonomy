#!/usr/bin/env python3
"""
Build complete dependency tree from entry points
"""

import os
import re
from pathlib import Path
from collections import defaultdict, deque

def get_imports(filepath):
    """Extract pipeline imports from a Python file"""
    imports = set()
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Match: from .module import ...
        # Match: from ..module import ...
        # Match: from pipeline.module import ...
        patterns = [
            r'from\s+(\.[.\w]+)\s+import',  # Relative imports
            r'from\s+(pipeline[.\w]*)\s+import',  # Absolute imports
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                imports.add(match)
    
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    
    return imports

def resolve_relative_import(current_module, relative_import):
    """Resolve relative import to absolute module path"""
    # current_module: pipeline.phases.base
    # relative_import: ..client -> pipeline.client
    # relative_import: .investigation -> pipeline.phases.investigation
    
    parts = current_module.split('.')
    
    # Count leading dots
    level = len(relative_import) - len(relative_import.lstrip('.'))
    module_name = relative_import.lstrip('.')
    
    # Go up 'level' directories
    if level > 0:
        parts = parts[:-level]
    
    if module_name:
        parts.append(module_name)
    
    return '.'.join(parts)

def module_to_filepath(module):
    """Convert module path to file path"""
    # pipeline.phases.base -> pipeline/phases/base.py
    # pipeline.phases -> pipeline/phases/__init__.py
    
    path = module.replace('.', '/')
    
    # Try as file first
    if os.path.exists(f"{path}.py"):
        return f"{path}.py"
    
    # Try as package
    if os.path.exists(f"{path}/__init__.py"):
        return f"{path}/__init__.py"
    
    return None

def build_dependency_tree(entry_points):
    """Build complete dependency tree from entry points"""
    
    # Map of module -> set of modules it imports
    dependencies = defaultdict(set)
    
    # Set of all reachable modules
    reachable = set(entry_points)
    
    # Queue for BFS
    queue = deque(entry_points)
    
    visited = set()
    
    while queue:
        current_module = queue.popleft()
        
        if current_module in visited:
            continue
        
        visited.add(current_module)
        
        # Get file path
        filepath = module_to_filepath(current_module)
        if not filepath:
            continue
        
        # Get imports
        imports = get_imports(filepath)
        
        for imp in imports:
            # Resolve relative imports
            if imp.startswith('.'):
                resolved = resolve_relative_import(current_module, imp)
            else:
                resolved = imp
            
            # Only track pipeline modules
            if not resolved.startswith('pipeline'):
                continue
            
            dependencies[current_module].add(resolved)
            
            if resolved not in reachable:
                reachable.add(resolved)
                queue.append(resolved)
            
            # Also mark the __init__.py as reachable if this is a package import
            # e.g., pipeline.phases -> pipeline.phases.__init__
            init_module = resolved + '.__init__'
            if init_module not in reachable:
                init_filepath = module_to_filepath(init_module)
                if init_filepath:
                    reachable.add(init_module)
                    queue.append(init_module)
    
    return dependencies, reachable

def find_all_modules():
    """Find all pipeline modules"""
    modules = set()
    
    for root, dirs, files in os.walk('pipeline'):
        # Skip __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                # Convert to module path
                module = filepath.replace('/', '.').replace('.py', '')
                modules.add(module)
    
    return modules

if __name__ == '__main__':
    # Entry points - need to include what run.py imports
    entry_points = [
        'pipeline.__init__',  # Main package entry point
        'pipeline.coordinator',
        'pipeline.config',
        'pipeline.error_signature',
        'pipeline.progress_display',
        'pipeline.command_detector',
        'pipeline.user_proxy',
        'pipeline.code_search',
        'pipeline.debug_context',
        'pipeline.line_fixer',
        'pipeline.runtime_tester',
        'pipeline.error_dedup',
        'pipeline.phases.qa',
        'pipeline.phases.debugging',
        'pipeline.phases.investigation',
        'pipeline.state.priority',
    ]
    
    print("Building dependency tree...")
    dependencies, reachable = build_dependency_tree(entry_points)
    
    print(f"\nReachable modules: {len(reachable)}")
    print("\nReachable modules list:")
    for mod in sorted(reachable):
        print(f"  {mod}")
    
    # Find all modules
    all_modules = find_all_modules()
    print(f"\nTotal modules: {len(all_modules)}")
    
    # Find unreachable
    unreachable = all_modules - reachable
    print(f"\nUnreachable modules: {len(unreachable)}")
    print("\nUnreachable modules list:")
    for mod in sorted(unreachable):
        print(f"  {mod}")
    
    # Calculate percentage
    if all_modules:
        percent_dead = len(unreachable) / len(all_modules) * 100
        print(f"\nPercentage of dead code: {percent_dead:.1f}%")