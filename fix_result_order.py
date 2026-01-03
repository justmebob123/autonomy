"""
Fix validators where result is used before it's defined.
"""

import sys
sys.path.insert(0, '.')
from pathlib import Path
import re

def fix_validator_result_order(filepath):
    """Fix result variable order in validator."""
    
    print(f"\nFixing: {filepath}")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find the pattern: polytopic calls before return
    pattern = r'(\s+# Polytopic Integration:.*?self\._publish_validation_event.*?\n\s+\})\s*\)\s*\n\s+(return \{)'
    
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        print(f"  ✅ No fix needed or pattern not found")
        return
    
    # Find where the return statement starts
    return_start = content.find('return {', match.start())
    if return_start == -1:
        print(f"  ❌ Could not find return statement")
        return
    
    # Find the end of the return dict
    brace_count = 0
    i = return_start + len('return {')
    while i < len(content):
        if content[i] == '{':
            brace_count += 1
        elif content[i] == '}':
            if brace_count == 0:
                break
            brace_count -= 1
        i += 1
    
    return_end = i + 1
    
    # Extract the return statement
    return_statement = content[return_start:return_end]
    
    # Extract the polytopic calls
    polytopic_start = content.find('# Polytopic Integration:', 0, return_start)
    if polytopic_start == -1:
        print(f"  ❌ Could not find polytopic integration")
        return
    
    polytopic_end = content.find('return {', polytopic_start)
    polytopic_calls = content[polytopic_start:polytopic_end]
    
    # Build the fixed version
    # 1. Build result dict first
    # 2. Then do polytopic calls
    # 3. Then return result
    
    fixed_section = f'''
        # Build result dict first
        result = {return_statement[len('return '):]}
        
{polytopic_calls}
        return result
'''
    
    # Replace the section
    content = content[:polytopic_start] + fixed_section + content[return_end:]
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"  ✅ Fixed result variable order")

def main():
    """Fix all validators."""
    
    validators = [
        'pipeline/analysis/type_usage_validator.py',
        'pipeline/analysis/method_existence_validator.py',
        'pipeline/analysis/method_signature_validator.py',
        'pipeline/analysis/function_call_validator.py',
        'pipeline/analysis/enum_attribute_validator.py',
        'bin/validators/keyword_argument_validator.py',
        'pipeline/analysis/architecture_validator.py',
    ]
    
    for validator in validators:
        if Path(validator).exists():
            fix_validator_result_order(validator)

if __name__ == '__main__':
    main()