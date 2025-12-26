#!/usr/bin/env python3
"""
Audit all Python files in the autonomy project for unused imports.
"""

import os
import re
import ast
from pathlib import Path
from collections import defaultdict

def get_python_files(directory):
    """Get all Python files in directory."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ and .git
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'env']]
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def extract_imports(content):
    """Extract all imports from Python content."""
    imports = []
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith(('import ', 'from ')):
            imports.append(line)
    return imports

def get_imported_names(import_line):
    """Extract names imported from an import statement."""
    names = []
    
    if import_line.startswith('import '):
        # import module or import module as alias
        parts = import_line[7:].split(' as ')
        module = parts[0].strip()
        alias = parts[1].strip() if len(parts) > 1 else module
        names.append((module, alias.split('.')[-1]))
    
    elif import_line.startswith('from '):
        # from module import name1, name2
        match = re.match(r'from\s+[\w.]+\s+import\s+(.+)', import_line)
        if match:
            imports_part = match.group(1)
            for item in imports_part.split(','):
                item = item.strip()
                if ' as ' in item:
                    name, alias = item.split(' as ')
                    names.append((name.strip(), alias.strip()))
                else:
                    names.append((item, item))
    
    return names

def check_usage(content, name):
    """Check if a name is used in the content (excluding import line)."""
    # Remove import lines
    lines = content.split('\n')
    code_lines = [l for l in lines if not l.strip().startswith(('import ', 'from '))]
    code = '\n'.join(code_lines)
    
    # Check for usage
    pattern = rf'\b{re.escape(name)}\b'
    return len(re.findall(pattern, code)) > 0

def audit_file(filepath):
    """Audit a single file for unused imports."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return None
    
    imports = extract_imports(content)
    unused = []
    
    for import_line in imports:
        names = get_imported_names(import_line)
        for original, used_name in names:
            if not check_usage(content, used_name):
                unused.append((import_line, used_name))
    
    return unused if unused else None

def main():
    """Main audit function."""
    print("="*80)
    print("AUTONOMY PROJECT - UNUSED IMPORTS AUDIT")
    print("="*80)
    
    directory = 'autonomy'
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' not found")
        return
    
    python_files = get_python_files(directory)
    print(f"\nScanning {len(python_files)} Python files...\n")
    
    files_with_unused = {}
    total_unused = 0
    
    for filepath in sorted(python_files):
        unused = audit_file(filepath)
        if unused:
            files_with_unused[filepath] = unused
            total_unused += len(unused)
    
    if not files_with_unused:
        print("✅ No unused imports found!")
        return
    
    print(f"Found {total_unused} unused imports in {len(files_with_unused)} files:\n")
    print("="*80)
    
    for filepath, unused_list in sorted(files_with_unused.items()):
        rel_path = filepath.replace('autonomy/', '')
        print(f"\n📄 {rel_path}")
        print("-"*80)
        for import_line, name in unused_list:
            print(f"  ❌ {import_line}")
            print(f"     Unused: {name}")
    
    print("\n" + "="*80)
    print(f"SUMMARY: {total_unused} unused imports in {len(files_with_unused)} files")
    print("="*80)

if __name__ == '__main__':
    main()