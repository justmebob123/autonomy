#!/usr/bin/env python3
"""
Fix all high-severity dictionary access errors.

Changes unsafe dict[key] access to safe dict.get(key, default) access.
"""

import re
from pathlib import Path
from typing import List, Tuple

# List of all high-severity errors to fix
# Format: (file_path, line_number, variable_name, key_name, appropriate_default)
ERRORS_TO_FIX = [
    # handlers.py errors
    ("pipeline/handlers.py", 2220, "result", "isolated_phases", "[]"),
    ("pipeline/handlers.py", 2294, "result", "found", "False"),
    ("pipeline/handlers.py", 2324, "result", "warning", "None"),
    ("pipeline/handlers.py", 2301, "result", "found", "False"),
    ("pipeline/handlers.py", 2216, "result", "connected_vertices", "0"),
    ("pipeline/handlers.py", 2216, "result", "total_vertices", "0"),
    ("pipeline/handlers.py", 2217, "result", "total_edges", "0"),
    ("pipeline/handlers.py", 2218, "result", "avg_reachability", "0.0"),
    ("pipeline/handlers.py", 2321, "result", "total_recursive", "0"),
    ("pipeline/handlers.py", 2322, "result", "total_circular", "0"),
    ("pipeline/handlers.py", 3582, "result", "total_lines", "0"),
    ("pipeline/handlers.py", 2258, "result", "total_integration_points", "0"),
    ("pipeline/handlers.py", 2296, "result", "flows_through", "[]"),
    ("pipeline/handlers.py", 2297, "result", "criticality", "'unknown'"),
    ("pipeline/handlers.py", 2363, "result", "quality_score", "0.0"),
    ("pipeline/handlers.py", 2364, "result", "lines", "0"),
    ("pipeline/handlers.py", 2365, "result", "comment_ratio", "0.0"),
    ("pipeline/handlers.py", 3502, "result", "estimated_reduction", "0"),
    ("pipeline/handlers.py", 3848, "result", "valid", "False"),
    ("pipeline/handlers.py", 2221, "result", "isolated_phases", "[]"),
    
    # team_orchestrator.py error
    ("pipeline/team_orchestrator.py", 450, "result", "findings", "[]"),
    
    # tool_evaluation.py errors (all accessing 'error' key)
    ("pipeline/phases/tool_evaluation.py", 172, "impl_result", "error", "None"),
    ("pipeline/phases/tool_evaluation.py", 182, "sig_result", "error", "None"),
    ("pipeline/phases/tool_evaluation.py", 194, "security_result", "error", "None"),
    ("pipeline/phases/tool_evaluation.py", 225, "integration_result", "error", "None"),
    ("pipeline/phases/tool_evaluation.py", 236, "registry_result", "error", "None"),
    ("pipeline/phases/tool_evaluation.py", 171, "impl_result", "error", "None"),
    ("pipeline/phases/tool_evaluation.py", 183, "sig_result", "error", "None"),
    ("pipeline/phases/tool_evaluation.py", 193, "security_result", "error", "None"),
    ("pipeline/phases/tool_evaluation.py", 213, "exec_result", "error", "None"),
    ("pipeline/phases/tool_evaluation.py", 215, "exec_result", "error", "None"),
    ("pipeline/phases/tool_evaluation.py", 226, "integration_result", "error", "None"),
    ("pipeline/phases/tool_evaluation.py", 237, "registry_result", "error", "None"),
    
    # custom_tools/handler.py error
    ("pipeline/custom_tools/handler.py", 137, "processed_result", "success", "False"),
    
    # orchestration/arbiter.py error
    ("pipeline/orchestration/arbiter.py", 702, "decision", "decision", "None"),
]

def fix_dict_access(file_path: str, line_num: int, var_name: str, key_name: str, default: str) -> bool:
    """
    Fix a single dictionary access error.
    
    Changes: var_name[key_name] -> var_name.get(key_name, default)
    """
    path = Path(file_path)
    if not path.exists():
        print(f"  ❌ File not found: {file_path}")
        return False
    
    # Read file
    with open(path, 'r') as f:
        lines = f.readlines()
    
    if line_num > len(lines):
        print(f"  ❌ Line {line_num} out of range in {file_path}")
        return False
    
    # Get the line (0-indexed)
    line = lines[line_num - 1]
    
    # Pattern to match: var_name['key_name'] or var_name["key_name"]
    pattern1 = f"{re.escape(var_name)}\\['{re.escape(key_name)}'\\]"
    pattern2 = f'{re.escape(var_name)}\\["{re.escape(key_name)}"\\]'
    
    # Replacement: var_name.get('key_name', default)
    replacement = f"{var_name}.get('{key_name}', {default})"
    
    # Try both patterns
    new_line = line
    if re.search(pattern1, line):
        new_line = re.sub(pattern1, replacement, line)
    elif re.search(pattern2, line):
        new_line = re.sub(pattern2, replacement, line)
    else:
        print(f"  ⚠️  Pattern not found on line {line_num} in {file_path}")
        print(f"      Line: {line.strip()}")
        print(f"      Looking for: {var_name}['{key_name}']")
        return False
    
    # Update the line
    lines[line_num - 1] = new_line
    
    # Write back
    with open(path, 'w') as f:
        f.writelines(lines)
    
    print(f"  ✅ Fixed line {line_num}: {var_name}['{key_name}'] -> {var_name}.get('{key_name}', {default})")
    return True

def main():
    print("=" * 80)
    print("FIXING HIGH-SEVERITY DICTIONARY ACCESS ERRORS")
    print("=" * 80)
    print(f"\nTotal errors to fix: {len(ERRORS_TO_FIX)}")
    print()
    
    # Group by file
    by_file = {}
    for error in ERRORS_TO_FIX:
        file_path = error[0]
        if file_path not in by_file:
            by_file[file_path] = []
        by_file[file_path].append(error)
    
    fixed = 0
    failed = 0
    
    for file_path, errors in sorted(by_file.items()):
        print(f"\n📁 {file_path} ({len(errors)} errors)")
        print("-" * 80)
        
        # Sort by line number (descending) to avoid line number shifts
        errors_sorted = sorted(errors, key=lambda x: x[1], reverse=True)
        
        for error in errors_sorted:
            _, line_num, var_name, key_name, default = error
            if fix_dict_access(file_path, line_num, var_name, key_name, default):
                fixed += 1
            else:
                failed += 1
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Fixed: {fixed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {len(ERRORS_TO_FIX)}")
    
    if fixed == len(ERRORS_TO_FIX):
        print("\n🎉 ALL ERRORS FIXED SUCCESSFULLY!")
    elif failed > 0:
        print(f"\n⚠️  {failed} errors require manual fixing")
    
    print("\nNext steps:")
    print("1. Review the changes")
    print("2. Run validation: python3 -c &quot;from pipeline.analysis.dict_structure_validator import DictStructureValidator; print(DictStructureValidator('.').validate_all())&quot;")
    print("3. Test the pipeline")
    print("4. Commit the fixes")

if __name__ == "__main__":
    main()