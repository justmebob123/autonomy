#!/usr/bin/env python3
"""
Fix the config_file variable bug in all validators.
"""

from pathlib import Path

def fix_validator(filepath: Path):
    """Fix config_file variable issue."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find "project_dir = sys.argv[1]" and add config_file initialization after it
    for i, line in enumerate(lines):
        if 'project_dir = sys.argv[1]' in line:
            # Check if config_file is already defined
            has_config = False
            for j in range(i+1, min(i+10, len(lines))):
                if 'config_file' in lines[j] and '=' in lines[j]:
                    has_config = True
                    break
            
            if not has_config:
                # Add config_file initialization
                indent = '    '
                lines.insert(i+1, f'{indent}config_file = None\n')
                print(f"   ✅ Added config_file initialization")
                break
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def main():
    print("=" * 80)
    print("FIXING config_file VARIABLE BUG")
    print("=" * 80)
    print()
    
    validators = [
        'bin/validate_all.py',
        'bin/validate_type_usage.py',
        'bin/validate_method_existence.py',
        'bin/validate_function_calls.py',
    ]
    
    for validator in validators:
        filepath = Path(validator)
        if filepath.exists():
            print(f"📝 Fixing: {filepath.name}")
            fix_validator(filepath)
        else:
            print(f"⚠️  Not found: {filepath.name}")
    
    print()
    print("=" * 80)
    print("✅ ALL VALIDATORS FIXED")
    print("=" * 80)

if __name__ == "__main__":
    main()