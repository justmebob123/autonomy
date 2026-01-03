# Critical Issue: Dict Structure Validator Scoping Bug

## Problem

The dict_structure_validator has a fundamental design flaw:
- It tracks dictionary structures globally by variable name
- It doesn't properly scope structures per-file or per-function
- This causes it to confuse variables with the same name in different contexts

## Example

```python
# File 1: validator code
def validate_all():
    result = {'errors': [], 'total_errors': 0}
    return result

# File 2: team_orchestrator.py  
def validate_tool():
    result = {'issues': [], 'valid': False}
    result['issues'].append("error")  # FALSE POSITIVE!
    return result
```

The validator sees `result` in File 1, records its structure as `{'errors': [], 'total_errors': 0}`, then when it validates File 2, it expects ALL `result` variables to have that same structure.

## Impact

- 23 false positive "high-severity" errors
- All in team_orchestrator.py
- All accessing `result['issues']` which is perfectly valid in that context
- Validator is confusing its own `result` variable with the application's `result` variable

## Root Cause

In `_collect_dict_structures()`:
```python
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        if isinstance(node.value, ast.Dict):
            structure = self._extract_dict_structure(node.value)
            if structure:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.known_structures[target.id] = structure  # GLOBAL!
```

The `self.known_structures` dict uses just the variable name as key, not scoped by file/function.

## Solution Required

The validator needs to:
1. Track structures per-file: `{file: {var_name: structure}}`
2. Track structures per-function: `{file: {function: {var_name: structure}}}`
3. Only validate variables against structures in the same scope
4. Handle local vs global scope properly

## Current Status

- The 23 "high-severity" errors are FALSE POSITIVES
- The actual code in team_orchestrator.py is CORRECT
- The validator itself is BROKEN
- This bug existed BEFORE my integration work
- My integration just exposed it by actually running the validator

## Recommendation

1. Fix the dict_structure_validator scoping issue
2. Re-run validation to get accurate results
3. Only then address real errors (not false positives)