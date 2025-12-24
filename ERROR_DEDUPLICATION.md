# Error Deduplication Strategy

## Problem

The system detects 17 errors but they're all the same:
```
AttributeError: 'PipelineCoordinator' object has no attribute 'start_phase'
at job_executor.py:3010
at job_executor.py:4527
at job_executor.py:5123
... (14 more locations)
```

Currently, it tries to fix each one separately, which:
- Wastes time (17 separate AI calls)
- Wastes API resources
- Could create conflicts
- Doesn't address the root cause

## Solution: Smart Deduplication

### Strategy 1: Group by Error Type + Message

For runtime errors, group by:
- Error type (AttributeError, NameError, etc.)
- Error message (the actual error text)
- Object type (if AttributeError)
- Missing attribute (if AttributeError)

Example:
```python
error_key = (
    error['type'],
    error['message'],
    error.get('object_type'),
    error.get('missing_attribute')
)
```

All 17 errors have the same key:
```
('RuntimeError', "AttributeError: 'PipelineCoordinator' object has no attribute 'start_phase'", 
 'PipelineCoordinator', 'start_phase')
```

### Strategy 2: Collect All Locations

Instead of fixing each location separately, collect all locations:

```python
deduplicated_errors = {
    error_key: {
        'type': 'RuntimeError',
        'message': "AttributeError: 'PipelineCoordinator' object has no attribute 'start_phase'",
        'object_type': 'PipelineCoordinator',
        'missing_attribute': 'start_phase',
        'locations': [
            {'file': 'job_executor.py', 'line': 3010, 'function': '_execute_integration_job_internal'},
            {'file': 'job_executor.py', 'line': 4527, 'function': '_execute_cleanup_job'},
            {'file': 'job_executor.py', 'line': 5123, 'function': '_execute_test_job'},
            ... (14 more)
        ],
        'context': [traceback lines],
        'call_chain': [call chain]
    }
}
```

### Strategy 3: Fix Once, Apply Everywhere

The AI should:
1. Analyze the error once with full context
2. Determine the fix (e.g., rename `start_phase` → `begin_phase`)
3. Apply the fix to ALL locations in one go

For example:
```python
# Instead of 17 separate fixes:
modify_python_file(file='job_executor.py', line=3010, ...)
modify_python_file(file='job_executor.py', line=4527, ...)
... (15 more)

# Do one comprehensive fix:
modify_python_file(
    file='job_executor.py',
    original_code='self.coordinator.start_phase',
    new_code='self.coordinator.begin_phase',
    all_occurrences=True  # Fix all occurrences
)
```

## Implementation

### Step 1: Add Deduplication Function

```python
def deduplicate_errors(errors: List[Dict]) -> Dict[tuple, Dict]:
    """
    Deduplicate errors by grouping identical errors.
    
    Returns:
        Dict mapping error_key to deduplicated error with all locations
    """
    deduplicated = {}
    
    for error in errors:
        # Create unique key for this error type
        if error['type'] == 'RuntimeError':
            # For runtime errors, use message + object type + missing attribute
            error_key = (
                error['type'],
                error.get('message', ''),
                error.get('object_type'),
                error.get('missing_attribute')
            )
        else:
            # For syntax errors, use file + line + message
            error_key = (
                error['type'],
                error.get('file', ''),
                error.get('line'),
                error.get('message', '')
            )
        
        if error_key not in deduplicated:
            # First occurrence - create entry
            deduplicated[error_key] = {
                'type': error['type'],
                'message': error.get('message', ''),
                'object_type': error.get('object_type'),
                'missing_attribute': error.get('missing_attribute'),
                'locations': [],
                'context': error.get('context', []),
                'call_chain': error.get('call_chain', []),
                'traceback': error.get('traceback', [])
            }
        
        # Add this location
        deduplicated[error_key]['locations'].append({
            'file': error.get('file', ''),
            'line': error.get('line'),
            'function': error.get('function', ''),
            'code': error.get('text', '')
        })
    
    return deduplicated
```

### Step 2: Update Error Processing Loop

```python
# Before deduplication:
for file_path, file_errors in errors_by_file.items():
    for error in file_errors:
        # Fix each error separately (wasteful!)
        fix_error(error)

# After deduplication:
deduplicated = deduplicate_errors(all_errors)
for error_key, error_group in deduplicated.items():
    # Fix once, apply to all locations
    print(f"Fixing {len(error_group['locations'])} occurrences of: {error_group['message']}")
    fix_error_group(error_group)
```

### Step 3: Enhance Prompt for Grouped Errors

```python
prompt = f"""
## Error: {error_group['message']}

This error occurs at {len(error_group['locations'])} locations:

"""

for i, loc in enumerate(error_group['locations'][:10], 1):  # Show first 10
    prompt += f"{i}. {loc['file']}:{loc['line']} in {loc['function']}\n"
    if loc.get('code'):
        prompt += f"   Code: {loc['code']}\n"

if len(error_group['locations']) > 10:
    prompt += f"... and {len(error_group['locations']) - 10} more locations\n"

prompt += """

Your task: Determine the fix and apply it to ALL locations.
"""
```

## Benefits

✅ **Efficiency**: Fix once instead of 17 times
✅ **Consistency**: Same fix applied everywhere
✅ **Cost**: 1 API call instead of 17
✅ **Speed**: Much faster execution
✅ **Clarity**: Shows the scope of the issue

## Example Output

Before:
```
🔧 Fixing: RuntimeError at line 3010
🔧 Fixing: RuntimeError at line 4527
🔧 Fixing: RuntimeError at line 5123
... (14 more)
```

After:
```
🔧 Fixing: AttributeError: 'PipelineCoordinator' object has no attribute 'start_phase'
   📍 17 occurrences in job_executor.py
   📊 Gathering context...
   🤖 Analyzing with AI...
   ✅ Fixed all 17 occurrences
```