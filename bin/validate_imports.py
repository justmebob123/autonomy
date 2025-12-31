#!/usr/bin/env python3
"""
Import Validation Script

Validates all imports in the pipeline codebase to catch errors before runtime.
Run this before every commit to prevent import-related failures.
"""

import ast
import os
import re
import sys
from pathlib import Path
from collections import defaultdict


class ImportValidator:
    def __init__(self, root_dir='pipeline'):
        self.root_dir = root_dir
        self.errors = []
        self.warnings = []
        self.actual_modules = set()
        self.imports_found = defaultdict(list)
        
    def scan_modules(self):
        """Scan directory to find all actual Python modules."""
        print(f"📁 Scanning {self.root_dir} for Python modules...")
        
        for root, dirs, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    # Convert file path to module path
                    module_path = os.path.join(root, file[:-3]).replace('/', '.')
                    self.actual_modules.add(module_path)
                    
        print(f"   Found {len(self.actual_modules)} modules\n")
        
    def check_syntax(self):
        """Check syntax of all Python files."""
        print("🔍 Checking syntax of all Python files...")
        
        syntax_errors = []
        file_count = 0
        
        for root, dirs, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    file_count += 1
                    try:
                        with open(filepath, 'r') as f:
                            ast.parse(f.read())
                    except SyntaxError as e:
                        syntax_errors.append(f"{filepath}:{e.lineno} - {e.msg}")
                    except Exception as e:
                        syntax_errors.append(f"{filepath} - {str(e)}")
        
        if syntax_errors:
            self.errors.extend(syntax_errors)
            print(f"   ❌ Found {len(syntax_errors)} syntax errors")
        else:
            print(f"   ✅ All {file_count} files have valid syntax\n")
            
    def check_imports(self):
        """Check all import statements for validity."""
        print("🔍 Checking import statements...")
        
        import_errors = []
        
        for root, dirs, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r') as f:
                        for i, line in enumerate(f, 1):
                            # Check for non-existent module imports
                            if 'from pipeline.state.task import' in line:
                                import_errors.append(
                                    f"{filepath}:{i} - Imports from non-existent 'pipeline.state.task'"
                                )
                            
                            # Check for relative imports that might fail
                            if re.match(r'^\s*from \.task import', line):
                                import_errors.append(
                                    f"{filepath}:{i} - Relative import from '.task' (should be '.manager')"
                                )
                            
                            # Collect all imports for further analysis
                            match = re.match(r'^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))', line)
                            if match:
                                module = match.group(1) or match.group(2)
                                if module.startswith('pipeline.'):
                                    self.imports_found[module].append(f"{filepath}:{i}")
        
        if import_errors:
            self.errors.extend(import_errors)
            print(f"   ❌ Found {len(import_errors)} import errors")
        else:
            print(f"   ✅ No obvious import errors found\n")
            
    def check_module_existence(self):
        """Check if all imported modules actually exist."""
        print("🔍 Checking if imported modules exist...")
        
        missing_modules = []
        
        for module, locations in sorted(self.imports_found.items()):
            if module not in self.actual_modules:
                # Check if it's a package (directory with __init__.py)
                package_path = module.replace('.', '/').replace('pipeline/', 'pipeline/')
                if not os.path.exists(package_path) and not os.path.exists(package_path + '.py'):
                    # Check if it's a submodule import (e.g., pipeline.state imports from pipeline.state.manager)
                    parent_exists = any(m.startswith(module + '.') for m in self.actual_modules)
                    if not parent_exists and module.startswith('pipeline.'):
                        missing_modules.append({
                            'module': module,
                            'locations': locations[:5]  # First 5 locations
                        })
        
        if missing_modules:
            for item in missing_modules:
                self.errors.append(f"\n❌ Module '{item['module']}' does not exist")
                self.errors.append("   Imported in:")
                for loc in item['locations']:
                    self.errors.append(f"     - {loc}")
            print(f"   ❌ Found {len(missing_modules)} missing modules")
        else:
            print(f"   ✅ All imported modules exist\n")
            
    def check_typing_imports(self):
        """Check for missing typing imports."""
        print("🔍 Checking typing imports...")
        
        typing_errors = []
        
        for root, dirs, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r') as f:
                        content = f.read()
                        lines = content.split('\n')
                        
                        # Find typing imports
                        typing_imports = set()
                        for line in lines:
                            match = re.match(r'from typing import (.+)', line)
                            if match:
                                imports = match.group(1).split(',')
                                typing_imports.update(i.strip() for i in imports)
                        
                        # Check for usage of typing types
                        typing_types = ['Any', 'Union', 'Optional', 'List', 'Dict', 'Tuple', 'Set', 'Callable']
                        for type_name in typing_types:
                            # Look for type hints using this type
                            pattern = rf'(?:->|:)\s*{type_name}[\[\s,\)]'
                            if re.search(pattern, content) and type_name not in typing_imports:
                                # Find line number
                                for i, line in enumerate(lines, 1):
                                    if re.search(pattern, line):
                                        typing_errors.append(
                                            f"{filepath}:{i} - Uses '{type_name}' but doesn't import it"
                                        )
                                        break
        
        if typing_errors:
            self.warnings.extend(typing_errors)
            print(f"   ⚠️  Found {len(typing_errors)} potential typing import issues")
        else:
            print(f"   ✅ All typing imports look correct\n")
            
    def run(self):
        """Run all validation checks."""
        print("=" * 70)
        print("  IMPORT VALIDATION")
        print("=" * 70)
        print()
        
        self.scan_modules()
        self.check_syntax()
        self.check_imports()
        self.check_module_existence()
        self.check_typing_imports()
        
        print("=" * 70)
        print("  RESULTS")
        print("=" * 70)
        print()
        
        if self.errors:
            print(f"❌ ERRORS FOUND ({len(self.errors)}):\n")
            for error in self.errors:
                print(error)
            print()
            
        if self.warnings:
            print(f"⚠️  WARNINGS ({len(self.warnings)}):\n")
            for warning in self.warnings:
                print(warning)
            print()
            
        if not self.errors and not self.warnings:
            print("✅ ALL CHECKS PASSED!")
            print()
            return 0
        elif not self.errors:
            print("✅ No errors, but some warnings found")
            print()
            return 0
        else:
            print("❌ VALIDATION FAILED")
            print()
            return 1


if __name__ == '__main__':
    validator = ImportValidator()
    sys.exit(validator.run())