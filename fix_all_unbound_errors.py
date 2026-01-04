#!/usr/bin/env python3
"""
Fix all UnboundLocalError issues found by variable_initialization_validator.
"""

import re
from pathlib import Path

# All errors found:
errors = [
    {
        'file': 'autonomy/pipeline/phases/prompt_design.py',
        'line': 217,
        'variable': 'results',
        'first_use': 217,
        'first_definition': 222
    },
    {
        'file': 'autonomy/pipeline/phases/qa.py',
        'line': 137,
        'variable': 'state_manager',
        'first_use': 137,
        'first_definition': 504
    },
    {
        'file': 'autonomy/pipeline/phases/qa.py',
        'line': 603,
        'variable': 'f',
        'first_use': 603,
        'first_definition': 610
    },
    {
        'file': 'autonomy/pipeline/phases/refactoring.py',
        'line': 2357,
        'variable': 'task',
        'first_use': 2357,
        'first_definition': 2364
    },
    {
        'file': 'autonomy/pipeline/phases/debugging.py',
        'line': 1343,
        'variable': 'attempt',
        'first_use': 1343,
        'first_definition': 1465
    },
    {
        'file': 'autonomy/pipeline/phases/debugging.py',
        'line': 1541,
        'variable': 'r',
        'first_use': 1541,
        'first_definition': 1770
    },
    {
        'file': 'autonomy/pipeline/phases/debugging.py',
        'line': 1595,
        'variable': 'error_message',
        'first_use': 1595,
        'first_definition': 1630
    },
    {
        'file': 'autonomy/pipeline/phases/base.py',
        'line': 748,
        'variable': 'model_name',
        'first_use': 748,
        'first_definition': 751
    },
    {
        'file': 'autonomy/pipeline/phases/base.py',
        'line': 748,
        'variable': 'host',
        'first_use': 748,
        'first_definition': 752
    }
]

print("=" * 80)
print("UNBOUND LOCAL ERROR ANALYSIS")
print("=" * 80)
print()

for error in errors:
    print(f"📁 {error['file']}")
    print(f"   Line {error['first_use']}: Variable '{error['variable']}' used before definition")
    print(f"   First use: line {error['first_use']}, First definition: line {error['first_definition']}")
    print()
    
    # Read the file and show context
    with open(error['file'], 'r') as f:
        lines = f.readlines()
    
    print(f"   Context at line {error['first_use']}:")
    start = max(0, error['first_use'] - 3)
    end = min(len(lines), error['first_use'] + 2)
    for i in range(start, end):
        marker = ">>>" if i == error['first_use'] - 1 else "   "
        print(f"   {marker} {i+1:4d}: {lines[i].rstrip()}")
    print()

print("=" * 80)
print(f"Total: {len(errors)} errors to fix")
print("=" * 80)