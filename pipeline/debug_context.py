"""
Debug Context Gathering - Extract comprehensive context for runtime errors.

This module provides functions to gather all relevant context for debugging
runtime errors, including call chains, related files, class definitions, etc.
"""

import re
import ast
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


def extract_call_chain(traceback_lines: List[str]) -> List[Dict]:
    """
    Parse traceback to extract call chain.
    
    Args:
        traceback_lines: Lines from the traceback
        
    Returns:
        List of dicts with file, line, function, and code for each frame
        
    Example:
        [
            {
                'file': '/path/to/file.py',
                'line': 123,
                'function': 'func_name',
                'code': 'self.coordinator.start_phase(...)'
            },
            ...
        ]
    """
    chain = []
    i = 0
    while i < len(traceback_lines):
        line = traceback_lines[i]
        
        # Look for: File "/path/to/file.py", line 123, in function_name
        match = re.search(r'File "([^"]+)", line (\d+)(?:, in (\w+))?', line)
        if match:
            frame = {
                'file': match.group(1),
                'line': int(match.group(2)),
                'function': match.group(3) if match.group(3) else 'module'
            }
            
            # Next line usually contains the code
            if i + 1 < len(traceback_lines):
                code_line = traceback_lines[i + 1].strip()
                if code_line and not code_line.startswith('File'):
                    frame['code'] = code_line
            
            chain.append(frame)
        
        i += 1
    
    return chain


def gather_related_files(error: Dict, project_dir: Path) -> Dict[str, str]:
    """
    Load content of all files in the call chain.
    
    Args:
        error: Error dict with traceback context
        project_dir: Project root directory
        
    Returns:
        Dict mapping file paths to their content
    """
    files = {}
    call_chain = extract_call_chain(error.get('context', []))
    
    for frame in call_chain:
        file_path = frame['file']
        try:
            pass
            # Try absolute path first
            if Path(file_path).exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    files[file_path] = f.read()
            else:
                pass
                # Try relative to project dir
                rel_path = project_dir / file_path
                if rel_path.exists():
                    with open(rel_path, 'r', encoding='utf-8') as f:
                        files[str(rel_path)] = f.read()
        except FileNotFoundError:
            pass
            # File doesn't exist, skip it
            pass
        except PermissionError:
            pass
            # Can't read file due to permissions
            pass
        except Exception as e:
            pass
            # Log unexpected errors
            import logging
            logging.getLogger(__name__).debug(f"Could not read {file_path}: {e}")
    
    return files


def extract_class_context(file_path: str, line_num: int) -> Dict:
    """
    Find the class and method containing the error line.
    
    Args:
        file_path: Path to the file
        line_num: Line number of the error
        
    Returns:
        Dict with class_name, method_name, class_start, class_end
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)
        
        # Find the class containing this line
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if hasattr(node, 'end_lineno') and node.lineno <= line_num <= node.end_lineno:
                    pass
                    # Find the method containing this line
                    method_name = None
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            if hasattr(item, 'end_lineno') and item.lineno <= line_num <= item.end_lineno:
                                method_name = item.name
                                break
                    
                    return {
                        'class_name': node.name,
                        'method_name': method_name,
                        'class_start': node.lineno,
                        'class_end': node.end_lineno if hasattr(node, 'end_lineno') else None
                    }
    except SyntaxError:
        pass
        # File has syntax errors, can't parse
        return {}
    except Exception as e:
        pass
        # Log unexpected errors
        import logging
        logging.getLogger(__name__).debug(f"Could not extract class context from {file_path}: {e}")
        return {}


def extract_object_type(error_message: str) -> Optional[str]:
    """
    Extract object type from AttributeError.
    
    Args:
        error_message: Error message string
        
    Returns:
        Object type name or None
        
    Example:
        "'PipelineCoordinator' object has no attribute 'start_phase'"
        → 'PipelineCoordinator'
    """
    match = re.search(r"'(\w+)' object has no attribute", error_message)
    return match.group(1) if match else None


def extract_missing_attr(error_message: str) -> Optional[str]:
    """
    Extract missing attribute from AttributeError.
    
    Args:
        error_message: Error message string
        
    Returns:
        Missing attribute name or None
        
    Example:
        "'PipelineCoordinator' object has no attribute 'start_phase'"
        → 'start_phase'
    """
    match = re.search(r"has no attribute '(\w+)'", error_message)
    return match.group(1) if match else None


def find_class_definition(project_dir: Path, class_name: str) -> Dict:
    """
    Search project for class definition.
    
    Args:
        project_dir: Project root directory
        class_name: Name of the class to find
        
    Returns:
        Dict with file, line, methods list
    """
    try:
        pass
        # Use grep to find the class definition
        result = subprocess.run(
            ['grep', '-r', '-n', f'class {class_name}', str(project_dir), '--include=*.py'],
            capture_output=True,
            text=True,
            timeout=None  # UNLIMITED
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pass
            # Parse first match
            first_line = result.stdout.split('\n')[0]
            parts = first_line.split(':', 2)
            if len(parts) >= 2:
                file_path = parts[0]
                line_num = int(parts[1])
                
                # Load file and extract class methods
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and node.name == class_name:
                        methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                        return {
                            'file': file_path,
                            'line': node.lineno,
                            'methods': methods,
                            'found': True
                        }
    except subprocess.TimeoutExpired:
        pass
        # Search timed out
        return {'found': False, 'error': 'search_timeout'}
    except SyntaxError:
        pass
        # Found file but has syntax errors
        return {'found': False, 'error': 'syntax_error'}
    except Exception as e:
        pass
        # Log unexpected errors
        import logging
        logging.getLogger(__name__).debug(f"Could not find class {class_name}: {e}")
        return {'found': False, 'error': str(e)}


def search_similar_methods(project_dir: Path, class_name: str, missing_method: str) -> List[str]:
    """
    Search for methods with similar names in the class.
    
    Args:
        project_dir: Project root directory
        class_name: Name of the class
        missing_method: Name of the missing method
        
    Returns:
        List of similar method names
    """
    class_def = find_class_definition(project_dir, class_name)
    if not class_def.get('found'):
        return []
    
    methods = class_def.get('methods', [])
    
    # Find similar method names using simple string matching
    similar = []
    missing_lower = missing_method.lower()
    
    for method in methods:
        method_lower = method.lower()
        # Check for partial matches
        if missing_lower in method_lower or method_lower in missing_lower:
            similar.append(method)
        # Check for similar prefixes (start_, begin_, init_, etc.)
        elif missing_lower.split('_')[0] == method_lower.split('_')[0]:
            similar.append(method)
    
    return similar


def build_comprehensive_context(error: Dict, project_dir: Path) -> Dict:
    """
    Build comprehensive context for debugging.
    
    Args:
        error: Error dict with all error information
        project_dir: Project root directory
        
    Returns:
        Dict with all gathered context
    """
    context = {
        'error': error,
        'call_chain': extract_call_chain(error.get('context', [])),
        'related_files': {},
        'class_context': {},
        'class_definition': {},
        'similar_methods': []
    }
    
    # Gather related files
    context['related_files'] = gather_related_files(error, project_dir)
    
    # Extract class context from error location
    if error.get('file'):
        context['class_context'] = extract_class_context(
            error['file'],
            error.get('line', 0)
        )
    
    # For AttributeError, find the class definition
    if 'AttributeError' in error.get('message', ''):
        obj_type = extract_object_type(error['message'])
        missing_attr = extract_missing_attr(error['message'])
        
        if obj_type:
            context['object_type'] = obj_type
            context['class_definition'] = find_class_definition(project_dir, obj_type)
            
            if missing_attr:
                context['missing_attribute'] = missing_attr
                context['similar_methods'] = search_similar_methods(
                    project_dir, obj_type, missing_attr
                )
    
    return context


def format_context_for_prompt(context: Dict) -> str:
    """
    Format the gathered context into a readable prompt section.
    
    Args:
        context: Context dict from build_comprehensive_context
        
    Returns:
        Formatted string for inclusion in AI prompt
    """
    sections = []
    
    # Call chain
    if context.get('call_chain'):
        sections.append("## Call Chain\n")
        for i, frame in enumerate(context['call_chain'], 1):
            sections.append(f"{i}. {frame['file']}:{frame['line']} in {frame.get('function', '?')}")
            if frame.get('code'):
                sections.append(f"   Code: {frame['code']}")
        sections.append("")
    
    # Object type and class info
    if context.get('object_type'):
        sections.append(f"## Object Type: {context['object_type']}\n")
        
        class_def = context.get('class_definition', {})
        if class_def.get('found'):
            sections.append(f"- Defined in: {class_def['file']}:{class_def['line']}")
            sections.append(f"- Available methods: {', '.join(class_def.get('methods', []))}")
        else:
            sections.append("- Class definition not found in project")
        sections.append("")
    
    # Missing attribute and similar methods
    if context.get('missing_attribute'):
        sections.append(f"## Missing Attribute: {context['missing_attribute']}\n")
        
        if context.get('similar_methods'):
            sections.append("Similar methods found:")
            for method in context['similar_methods']:
                sections.append(f"  - {method}")
        else:
            sections.append("No similar methods found")
        sections.append("")
    
    # Related files (show snippets)
    if context.get('related_files'):
        sections.append("## Related Files\n")
        for file_path, content in list(context['related_files'].items())[:3]:  # Limit to 3 files
            sections.append(f"### {file_path}")
            # Show first 50 lines or 2000 chars
            lines = content.split('\n')[:50]
            snippet = '\n'.join(lines)
            if len(snippet) > 2000:
                snippet = snippet[:2000] + "\n... (truncated)"
            sections.append(f"```python\n{snippet}\n```\n")
    
    return '\n'.join(sections)