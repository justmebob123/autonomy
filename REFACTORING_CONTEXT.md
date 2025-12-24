# Refactoring Context Detection

## Problem

When debugging errors during a refactoring:
- The error might be one of many similar issues
- Related code exists in other files
- The AI needs to see the full scope of the refactoring
- The AI needs tools to explore the codebase

## Example Scenario

Error: `AttributeError: 'PipelineCoordinator' object has no attribute 'start_phase'`

This could mean:
1. Method was renamed: `start_phase` → `begin_phase`
2. There are 50+ calls to `start_phase` across 10 files
3. Only some files were updated during refactoring
4. AI needs to see ALL files using `start_phase`

## Solution: Comprehensive Code Search

### Step 1: Search for the Broken Reference

When we detect an AttributeError:
```python
missing_attr = 'start_phase'
object_type = 'PipelineCoordinator'

# Search for all uses of this attribute
grep -r "\.start_phase\(" project_dir --include="*.py"

# Results:
# job_executor.py:3010: self.coordinator.start_phase('integration', ...)
# job_executor.py:4527: self.coordinator.start_phase('deadcode', ...)
# test_runner.py:123: coordinator.start_phase('test', ...)
# integration.py:456: self.coord.start_phase('setup', ...)
# ... (50+ more)
```

### Step 2: Find Related Files

```python
related_files = {
    'job_executor.py': [3010, 4527, 5123, ...],  # 17 occurrences
    'test_runner.py': [123, 456, 789],            # 3 occurrences
    'integration.py': [456, 890],                 # 2 occurrences
    # ... more files
}
```

### Step 3: Provide to AI

```
## Refactoring Context

The missing attribute `start_phase` is used in 22 locations across 5 files:

1. job_executor.py (17 occurrences)
   - Line 3010: self.coordinator.start_phase('integration', ...)
   - Line 4527: self.coordinator.start_phase('deadcode', ...)
   - ... (15 more)

2. test_runner.py (3 occurrences)
   - Line 123: coordinator.start_phase('test', ...)
   - ... (2 more)

3. integration.py (2 occurrences)
   - Line 456: self.coord.start_phase('setup', ...)
   - ... (1 more)

This appears to be a refactoring in progress. You may need to:
- Update ALL files to use the new method name
- Or create the missing method in PipelineCoordinator
- Use the read_file tool to examine other files if needed
```

## Tools the AI Needs

### 1. read_file
```python
{
    'name': 'read_file',
    'description': 'Read the contents of a file in the project',
    'parameters': {
        'file_path': {
            'type': 'string',
            'description': 'Path to the file relative to project root'
        }
    }
}
```

### 2. search_code
```python
{
    'name': 'search_code',
    'description': 'Search for code patterns across the project',
    'parameters': {
        'pattern': {
            'type': 'string',
            'description': 'Pattern to search for (supports regex)'
        },
        'file_pattern': {
            'type': 'string',
            'description': 'File pattern to search in (e.g., "*.py")',
            'default': '*.py'
        }
    }
}
```

### 3. list_class_methods
```python
{
    'name': 'list_class_methods',
    'description': 'List all methods in a class',
    'parameters': {
        'class_name': {
            'type': 'string',
            'description': 'Name of the class'
        }
    }
}
```

### 4. find_definition
```python
{
    'name': 'find_definition',
    'description': 'Find where a class, function, or variable is defined',
    'parameters': {
        'symbol': {
            'type': 'string',
            'description': 'Name of the symbol to find'
        }
    }
}
```

### 5. modify_python_file (already exists)
```python
{
    'name': 'modify_python_file',
    'description': 'Modify a Python file by replacing code',
    'parameters': {
        'file_path': {...},
        'original_code': {...},
        'new_code': {...}
    }
}
```

## Implementation Plan

### Phase 1: Enhanced Code Search

```python
def search_for_broken_reference(project_dir: Path, error_group: Dict) -> Dict:
    """
    Search for all uses of a broken reference across the project.
    
    Returns:
        {
            'pattern': 'start_phase',
            'total_occurrences': 22,
            'files': {
                'job_executor.py': [
                    {'line': 3010, 'code': 'self.coordinator.start_phase(...)'},
                    ...
                ],
                ...
            }
        }
    """
    if error_group.get('missing_attribute'):
        attr = error_group['missing_attribute']
        
        # Search for .attribute_name( or .attribute_name)
        patterns = [
            f'\\.{attr}\\(',  # Method call
            f'\\.{attr}\\)',  # Method reference
            f'\\.{attr}\\s',  # Attribute access
        ]
        
        results = {}
        for pattern in patterns:
            result = subprocess.run(
                ['grep', '-r', '-n', pattern, str(project_dir), '--include=*.py'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Parse results
                for line in result.stdout.split('\n'):
                    if ':' in line:
                        file_path, line_num, code = line.split(':', 2)
                        # Add to results...
        
        return results
```

### Phase 2: Add Tools to Debugging Phase

```python
# In pipeline/phases/debugging.py

def get_debug_tools():
    """Get tools available during debugging."""
    return [
        {
            'name': 'read_file',
            'description': 'Read a file from the project to examine its contents',
            'parameters': {
                'file_path': {
                    'type': 'string',
                    'description': 'Path to file relative to project root'
                }
            }
        },
        {
            'name': 'search_code',
            'description': 'Search for code patterns across the project',
            'parameters': {
                'pattern': {
                    'type': 'string',
                    'description': 'Pattern to search for'
                }
            }
        },
        # ... more tools
    ]
```

### Phase 3: Tool Handlers

```python
# In pipeline/handlers.py or new file

class DebugToolHandler:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
    
    def handle_read_file(self, file_path: str) -> str:
        """Handle read_file tool call."""
        full_path = self.project_dir / file_path
        if full_path.exists():
            with open(full_path, 'r') as f:
                return f.read()
        return f"Error: File not found: {file_path}"
    
    def handle_search_code(self, pattern: str, file_pattern: str = '*.py') -> str:
        """Handle search_code tool call."""
        result = subprocess.run(
            ['grep', '-r', '-n', pattern, str(self.project_dir), f'--include={file_pattern}'],
            capture_output=True,
            text=True
        )
        return result.stdout if result.returncode == 0 else "No matches found"
    
    def handle_list_class_methods(self, class_name: str) -> str:
        """Handle list_class_methods tool call."""
        # Use AST to find and list methods
        # ...
```

### Phase 4: Enhanced Prompt

```python
def build_refactoring_context(error_group: Dict, project_dir: Path) -> str:
    """Build context showing this might be a refactoring."""
    
    if not error_group.get('missing_attribute'):
        return ""
    
    # Search for all uses
    search_results = search_for_broken_reference(project_dir, error_group)
    
    if search_results['total_occurrences'] > len(error_group['locations']):
        # There are MORE occurrences than we're fixing!
        return f"""
## ⚠️ Refactoring Context Detected

The missing attribute `{error_group['missing_attribute']}` is used in 
{search_results['total_occurrences']} locations across {len(search_results['files'])} files.

You are only seeing errors from {len(error_group['locations'])} locations in the current file.

**This appears to be a refactoring in progress.**

Other files using this attribute:
{format_search_results(search_results)}

**Important**: 
- You may need to fix ALL files, not just the current one
- Use the `read_file` tool to examine other files
- Use the `search_code` tool to find more occurrences
- Consider whether to update all calls or create the missing method
"""
```

## Benefits

✅ **Full scope visibility** - AI sees all related code
✅ **Refactoring awareness** - AI knows it's mid-refactoring
✅ **Tool access** - AI can explore as needed
✅ **Comprehensive fixes** - Fix all related files at once
✅ **Smart decisions** - AI chooses best strategy

## Example Workflow

1. Error detected: `start_phase` doesn't exist
2. Search finds 50+ uses across 10 files
3. AI sees: "This is used in 10 files, you're only fixing 1"
4. AI uses `read_file` to check other files
5. AI uses `search_code` to find all occurrences
6. AI decides: "Rename all calls to `begin_phase`"
7. AI fixes all 10 files in one go