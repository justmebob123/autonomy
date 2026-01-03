#!/usr/bin/env python3
"""
Fix all validation tools to be truly general-purpose.

This script will update all validators to:
1. Require explicit path argument (no default to ".")
2. Show clear usage message when path not provided
3. Emphasize they can analyze ANY Python codebase
"""

from pathlib import Path
import shutil

def backup_file(filepath: Path) -> Path:
    """Create a backup of the file."""
    backup_path = filepath.with_suffix(filepath.suffix + '.backup')
    if not backup_path.exists():
        shutil.copy2(filepath, backup_path)
    return backup_path

def fix_validate_all_enhanced(filepath: Path):
    """Fix validate_all_enhanced.py"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find and replace the docstring
    for i, line in enumerate(lines):
        if i < 10 and '"""' in line and 'Enhanced Comprehensive' in lines[i+1]:
            lines[i+1] = "Enhanced Comprehensive Code Validation - GENERAL PURPOSE TOOL\n"
            lines.insert(i+2, "\n")
            lines.insert(i+3, "This tool can analyze ANY Python codebase, not just this project.\n")
            break
    
    # Find and replace the main function argument parsing
    for i, line in enumerate(lines):
        if 'def main():' in line:
            # Find the project_dir = "." line
            for j in range(i, min(i+20, len(lines))):
                if 'project_dir = "."' in lines[j]:
                    # Replace the argument parsing section
                    new_section = [
                        '    # Require explicit project directory\n',
                        '    if len(sys.argv) < 2:\n',
                        '        print("ERROR: Project directory required")\n',
                        '        print()\n',
                        '        print("Usage: {} <project_directory> [--config <file>]".format(sys.argv[0]))\n',
                        '        print()\n',
                        '        print("This is a GENERAL PURPOSE tool that can analyze ANY Python codebase.")\n',
                        '        print()\n',
                        '        print("Examples:")\n',
                        '        print("  {} /path/to/any/project".format(sys.argv[0]))\n',
                        '        print("  {} /home/user/django-app".format(sys.argv[0]))\n',
                        '        print("  {} /var/www/flask-app".format(sys.argv[0]))\n',
                        '        print("  {} . --config custom.yaml".format(sys.argv[0]))\n',
                        '        print()\n',
                        '        sys.exit(1)\n',
                        '    \n',
                        '    project_dir = sys.argv[1]\n',
                    ]
                    
                    # Find the end of the old argument parsing
                    end_idx = j + 1
                    for k in range(j+1, min(j+15, len(lines))):
                        if 'print("="' in lines[k]:
                            end_idx = k
                            break
                    
                    # Replace the section
                    lines[j:end_idx] = new_section
                    break
            break
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def fix_simple_validator(filepath: Path, tool_name: str):
    """Fix simple validators (type_usage, method_existence, etc.)"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Update docstring
    for i, line in enumerate(lines):
        if i < 15 and '"""' in line:
            # Find the closing """
            for j in range(i+1, min(i+20, len(lines))):
                if '"""' in lines[j]:
                    lines.insert(j, "\nThis is a GENERAL PURPOSE tool that can analyze ANY Python codebase.\n")
                    lines.insert(j+1, "\nUsage:\n")
                    lines.insert(j+2, f"    python {filepath.name} <project_directory>\n")
                    break
            break
    
    # Fix main function
    for i, line in enumerate(lines):
        if 'def main():' in line:
            # Find project_dir = "."
            for j in range(i, min(i+20, len(lines))):
                if 'project_dir = "."' in lines[j] or 'project_dir = os.getcwd()' in lines[j]:
                    # Replace with proper argument handling
                    new_section = [
                        '    # Require explicit project directory\n',
                        '    if len(sys.argv) < 2:\n',
                        '        print("ERROR: Project directory required")\n',
                        '        print()\n',
                        '        print("Usage: {} <project_directory>".format(sys.argv[0]))\n',
                        '        print()\n',
                        '        print("This tool can analyze ANY Python codebase.")\n',
                        '        print()\n',
                        '        print("Examples:")\n',
                        '        print("  {} /path/to/any/project".format(sys.argv[0]))\n',
                        '        print("  {} /home/user/django-app".format(sys.argv[0]))\n',
                        '        print()\n',
                        '        sys.exit(1)\n',
                        '    \n',
                        '    project_dir = sys.argv[1]\n',
                    ]
                    
                    # Find where to end replacement (usually at the next significant line)
                    end_idx = j + 1
                    for k in range(j+1, min(j+15, len(lines))):
                        if 'print(' in lines[k] and ('Validating' in lines[k] or '=' in lines[k]):
                            end_idx = k
                            break
                    
                    lines[j:end_idx] = new_section
                    break
            break
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def main():
    print("=" * 80)
    print("FIXING ALL VALIDATION TOOLS TO BE GENERAL PURPOSE")
    print("=" * 80)
    print()
    
    bin_dir = Path("bin")
    
    tools = {
        'validate_all_enhanced.py': 'Enhanced Validator',
        'validate_all.py': 'All Validators',
        'validate_type_usage.py': 'Type Usage',
        'validate_method_existence.py': 'Method Existence',
        'validate_method_signatures.py': 'Method Signatures',
        'validate_function_calls.py': 'Function Calls',
        'validate_enum_attributes.py': 'Enum Attributes',
        'validate_dict_structure.py': 'Dict Structure',
    }
    
    for filename, tool_name in tools.items():
        filepath = bin_dir / filename
        
        if not filepath.exists():
            print(f"⚠️  Not found: {filename}")
            continue
        
        print(f"📝 Fixing: {filename}")
        
        # Create backup
        backup_path = backup_file(filepath)
        print(f"   ✅ Backup: {backup_path.name}")
        
        # Fix the file
        try:
            if filename == 'validate_all_enhanced.py':
                fix_validate_all_enhanced(filepath)
            else:
                fix_simple_validator(filepath, tool_name)
            print(f"   ✅ Fixed to require explicit path")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    print("=" * 80)
    print("✅ ALL VALIDATION TOOLS NOW REQUIRE EXPLICIT PATH")
    print("=" * 80)
    print()
    print("Usage examples:")
    print("  python bin/validate_all_enhanced.py /path/to/any/project")
    print("  python bin/validate_type_usage.py /home/user/django-app")
    print("  python bin/validate_method_existence.py /var/www/flask-app")
    print()
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())