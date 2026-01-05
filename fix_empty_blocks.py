#!/usr/bin/env python3
"""Fix all empty if/for/except blocks in coordinator.py"""

import re

def fix_empty_blocks(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        fixed_lines.append(line)
        
        # Check if this is a block statement (if/for/while/except/try/with/def/class)
        stripped = line.strip()
        if stripped and (
            stripped.endswith(':') and 
            any(stripped.startswith(kw) for kw in ['if ', 'elif ', 'else:', 'for ', 'while ', 'except', 'try:', 'with ', 'def ', 'class '])
        ):
            # Get indentation of current line
            indent = len(line) - len(line.lstrip())
            
            # Check next line
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                next_stripped = next_line.strip()
                next_indent = len(next_line) - len(next_line.lstrip())
                
                # If next line is another block statement at same or lower indent, or is empty/comment
                # then current block is empty
                if (not next_stripped or 
                    next_stripped.startswith('#') or
                    (next_indent <= indent and next_stripped)):
                    # Add pass statement
                    fixed_lines.append(' ' * (indent + 4) + 'pass\n')
        
        i += 1
    
    with open(file_path, 'w') as f:
        f.writelines(fixed_lines)

if __name__ == '__main__':
    fix_empty_blocks('pipeline/coordinator.py')
    print("Fixed empty blocks in coordinator.py")