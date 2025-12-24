# Debug Mode Implementation Plan

## Immediate Actions (What We Can Do Now)

### 1. Enhance Context Gathering in run.py

The current code only provides the error line. We need to provide:

```python
# Current (insufficient):
issue = {
    'filepath': file_path,
    'type': error['type'],
    'message': error['message'],
    'line': error_line,
    'offset': error.get('offset'),
    'text': error.get('text'),
    'description': f"{error['type']} at line {error_line}: {error['message']}\n\nContext:\n{context}"
}

# Enhanced (what we need):
issue = {
    'filepath': file_path,
    'type': error['type'],
    'message': error['message'],
    'line': error_line,
    'traceback': error.get('context', []),  # Full traceback
    'call_chain': extract_call_chain(error.get('context', [])),  # Parsed call chain
    'related_files': gather_related_files(error),  # All files in traceback
    'class_context': extract_class_context(file_path, error_line),  # Class being used
    'object_type': extract_object_type(error['message']),  # e.g., 'PipelineCoordinator'
    'missing_attribute': extract_missing_attr(error['message']),  # e.g., 'start_phase'
    'description': build_comprehensive_description(error)
}
```

### 2. Add Helper Functions

```python
def extract_call_chain(traceback_lines: List[str]) -> List[Dict]:
    """
    Parse traceback to extract call chain.
    
    Returns:
        [
            {'file': '/path/to/file.py', 'line': 123, 'function': 'func_name', 'code': 'code line'},
            ...
        ]
    """
    import re
    chain = []
    for line in traceback_lines:
        match = re.search(r'File "([^"]+)", line (\d+), in (\w+)', line)
        if match:
            chain.append({
                'file': match.group(1),
                'line': int(match.group(2)),
                'function': match.group(3)
            })
    return chain

def gather_related_files(error: Dict) -> Dict[str, str]:
    """
    Load content of all files in the call chain.
    
    Returns:
        {'file_path': 'file_content', ...}
    """
    files = {}
    call_chain = extract_call_chain(error.get('context', []))
    for frame in call_chain:
        try:
            with open(frame['file'], 'r') as f:
                files[frame['file']] = f.read()
        except:
            pass
    return files

def extract_class_context(file_path: str, line_num: int) -> Dict:
    """
    Find the class and method containing the error line.
    
    Returns:
        {
            'class_name': 'ClassName',
            'method_name': 'method_name',
            'class_definition': 'full class code'
        }
    """
    import ast
    try:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.lineno <= line_num <= node.end_lineno:
                    return {
                        'class_name': node.name,
                        'class_start': node.lineno,
                        'class_end': node.end_lineno
                    }
    except:
        pass
    return {}

def extract_object_type(error_message: str) -> str:
    """
    Extract object type from AttributeError.
    
    'PipelineCoordinator' object has no attribute 'start_phase'
    → 'PipelineCoordinator'
    """
    import re
    match = re.search(r"'(\w+)' object has no attribute", error_message)
    return match.group(1) if match else None

def extract_missing_attr(error_message: str) -> str:
    """
    Extract missing attribute from AttributeError.
    
    'PipelineCoordinator' object has no attribute 'start_phase'
    → 'start_phase'
    """
    import re
    match = re.search(r"has no attribute '(\w+)'", error_message)
    return match.group(1) if match else None

def find_class_definition(project_dir: Path, class_name: str) -> Dict:
    """
    Search project for class definition.
    
    Returns:
        {
            'file': '/path/to/file.py',
            'line': 123,
            'code': 'class definition code',
            'methods': ['method1', 'method2', ...]
        }
    """
    import subprocess
    result = subprocess.run(
        ['grep', '-r', '-n', f'class {class_name}', str(project_dir), '--include=*.py'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        # Parse first match
        first_line = result.stdout.split('\n')[0]
        file_path, line_num, _ = first_line.split(':', 2)
        
        # Load file and extract class
        with open(file_path, 'r') as f:
            content = f.read()
        
        import ast
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                return {
                    'file': file_path,
                    'line': node.lineno,
                    'methods': methods
                }
    
    return {}
```

### 3. Enhanced Prompt for Debugging Phase

```python
def build_comprehensive_debug_prompt(error: Dict, context: Dict) -> str:
    """Build a comprehensive prompt with all context."""
    
    prompt = f"""# Runtime Error Debug Task

## Error Information
- **Type**: {error['type']}
- **Message**: {error['message']}
- **File**: {error['filepath']}
- **Line**: {error['line']}

## Call Chain
"""
    
    for i, frame in enumerate(context.get('call_chain', []), 1):
        prompt += f"{i}. {frame['file']}:{frame['line']} in {frame['function']}\n"
    
    if context.get('object_type'):
        prompt += f"\n## Object Type: {context['object_type']}\n"
        
        class_def = context.get('class_definition', {})
        if class_def:
            prompt += f"- Defined in: {class_def['file']}:{class_def['line']}\n"
            prompt += f"- Available methods: {', '.join(class_def['methods'])}\n"
    
    if context.get('missing_attribute'):
        prompt += f"\n## Missing Attribute: {context['missing_attribute']}\n"
        prompt += "This attribute is being called but doesn't exist.\n"
    
    prompt += "\n## Related Files\n"
    for file_path, content in context.get('related_files', {}).items():
        prompt += f"\n### {file_path}\n```python\n{content[:2000]}...\n```\n"
    
    prompt += """
## Your Task

Analyze this error and determine the best fix:

1. **If the method is missing**: Create it in the target class
2. **If the method was renamed**: Update all calling code
3. **If the object type is wrong**: Fix the object creation
4. **If this is a design issue**: Explain and suggest refactoring

Provide your analysis and the fix.
"""
    
    return prompt
```

## Implementation Steps

### Step 1: Add Helper Functions to run.py
- Add all the helper functions above
- Import necessary modules (ast, re, subprocess)

### Step 2: Enhance Error Context Building
- Modify the code that builds the `issue` dict
- Add call chain extraction
- Add related files gathering
- Add class context extraction

### Step 3: Enhance Debugging Phase Prompt
- Modify `pipeline/phases/debugging.py`
- Use the comprehensive prompt builder
- Include all context in the prompt

### Step 4: Test and Iterate
- Run on the current error
- Verify AI gets full context
- Check if fix is correct
- Iterate based on results

## Quick Win: Immediate Improvement

Even without tool calling, we can dramatically improve by:

1. **Extracting the call chain** from traceback
2. **Loading all files** in the chain
3. **Finding the class definition** being referenced
4. **Listing available methods** in that class
5. **Providing all this to the AI** in the prompt

This gives the AI enough context to make smart decisions without needing tool calling.

## Future Enhancement: Tool Calling

Once the basic context gathering works, we can add tool calling:

```python
tools = [
    {
        'name': 'read_file',
        'description': 'Read a file from the project',
        'parameters': {'file_path': 'string'}
    },
    {
        'name': 'search_code',
        'description': 'Search for code patterns',
        'parameters': {'pattern': 'string'}
    },
    {
        'name': 'list_class_methods',
        'description': 'List all methods in a class',
        'parameters': {'class_name': 'string'}
    }
]
```

But this requires modifying the AI client to support tool calling, which is a bigger change.