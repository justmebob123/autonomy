"""
Architecture Formatter

Formats architecture violation analysis data.
Handles multiple sub-types of architecture issues.
"""

from .base import IssueFormatter


class ArchitectureFormatter(IssueFormatter):
    """Formats architecture violation issues with sub-type handling."""
    
    def format(self, data: dict) -> str:
        """Format architecture violation data based on sub-type."""
        # Check what type of architecture issue this is
        data_type = data.get('type', '') if isinstance(data, dict) else ''
        
        # Dictionary key error
        if 'key_path' in data:
            return self._format_dict_key_error(data)
        
        # Missing method error
        elif 'method_name' in data and 'class_name' in data:
            return self._format_missing_method(data)
        
        # Bug (bugs are categorized as ARCHITECTURE issues)
        elif 'message' in data and 'line' in data and 'file' in data and 'type' in data:
            return self._format_bug(data)
        
        # Anti-pattern
        elif data_type == 'antipattern':
            return self._format_antipattern(data)
        
        # Architecture violation
        elif data_type == 'architecture_violation':
            return self._format_architecture_violation(data)
        
        # Circular import
        elif data_type == 'circular_import':
            return self._format_circular_import(data)
        
        # Generic architecture issue
        else:
            return self._format_generic_architecture(data)
    
    def _format_dict_key_error(self, data: dict) -> str:
        """Format dictionary key error."""
        key_path = data.get('key_path', 'unknown')
        file_path = data.get('file', 'unknown')
        line = data.get('line', '?')
        message = data.get('message', 'Dictionary key error')
        suggestion = data.get('suggestion', 'Add default value or check if key exists')
        
        return f"""
DICTIONARY KEY ERROR DETECTED:
- Key path: {key_path}
- File: {file_path}
- Line: {line}
- Error: {message}
- Suggestion: {suggestion}

ACTION REQUIRED:
1. Read the file to understand the context
2. Fix the dictionary access to handle missing keys
3. If the fix is complex, create an issue report

EXAMPLE (simple fix):
read_file(filepath="{file_path}")
# Then use modify_file or replace_between to add:
# - .get() with default value: dict.get('key', default_value)
# - Check if key exists: if 'key' in dict:
# - Try/except: try: value = dict['key'] except KeyError: value = default

EXAMPLE (complex fix):
create_issue_report(
    title="Dictionary key error: {key_path}",
    description="Line {line} in {file_path}: {message}",
    severity="high",
    suggested_fix="{suggestion}",
    files_affected=["{file_path}"]
)

⚠️ DO NOT try to fix errors in files that don't exist - verify file path first!
"""
    
    def _format_missing_method(self, data: dict) -> str:
        """Format missing method error."""
        method_name = data.get('method_name', 'unknown')
        class_name = data.get('class_name', 'unknown')
        file_path = data.get('file', 'unknown')
        line = data.get('line', '?')
        message = data.get('message', 'Method not found')
        
        return f"""
MISSING METHOD DETECTED:
- Class: {class_name}
- Method: {method_name}
- File: {file_path}
- Line: {line}
- Error: {message}

ACTION REQUIRED:
1. Read the file to see the class definition
2. Implement the missing method in the class
3. If implementation requires domain knowledge, create an issue report

EXAMPLE (implement method):
read_file(filepath="{file_path}")
# Then use insert_after or modify_file to add the method to the class

EXAMPLE (if complex):
create_issue_report(
    title="Missing method: {class_name}.{method_name}",
    description="Method {method_name} is called but not defined in {class_name} at line {line}",
    severity="critical",
    suggested_fix="Implement the {method_name} method in {class_name} class",
    files_affected=["{file_path}"]
)

✅ PREFER implementing the method if it's straightforward (e.g., getter/setter, simple utility)
⚠️ CREATE REPORT only if implementation requires business logic or domain knowledge
"""
    
    def _format_bug(self, data: dict) -> str:
        """Format bug detection."""
        bug_type = data.get('type', 'unknown')
        bug_message = data.get('message', 'Unknown error')
        bug_file = data.get('file', 'unknown')
        bug_line = data.get('line', '?')
        bug_suggestion = data.get('suggestion', 'Fix the issue')
        
        return f"""
BUG DETECTED:
- Type: {bug_type}
- File: {bug_file}
- Line: {bug_line}
- Error: {bug_message}
- Suggestion: {bug_suggestion}

ACTION REQUIRED:
1. Read the file to understand the context
2. Fix the bug using appropriate file modification tools
3. If the bug is complex, create an issue report

EXAMPLE (simple fix):
read_file(filepath="{bug_file}")
# Then use modify_file, replace_between, or str_replace to fix the issue

EXAMPLE (complex fix):
create_issue_report(
    title="Bug: {bug_type}",
    description="Line {bug_line} in {bug_file}: {bug_message}",
    severity="high",
    suggested_fix="{bug_suggestion}",
    files_affected=["{bug_file}"]
)

⚠️ DO NOT try to fix bugs in files that don't exist - verify file path first!
"""
    
    def _format_antipattern(self, data: dict) -> str:
        """Format anti-pattern detection."""
        pattern_name = data.get('pattern_name', 'Unknown')
        pattern_file = data.get('file', 'unknown')
        pattern_desc = data.get('description', '')
        pattern_suggestion = data.get('suggestion', '')
        
        return f"""
ANTI-PATTERN DETECTED:
- Pattern: {pattern_name}
- File: {pattern_file}
- Description: {pattern_desc}
- Suggestion: {pattern_suggestion}

ACTION REQUIRED:
Create a detailed issue report for developer review:

EXAMPLE:
create_issue_report(
    title="Anti-pattern: {pattern_name}",
    description="Detected {pattern_name} in {pattern_file}. {pattern_desc}",
    severity="medium",
    suggested_fix="{pattern_suggestion}",
    files_affected=["{pattern_file}"]
)

⚠️ Anti-patterns usually require careful refactoring - create a detailed report.
"""
    
    def _format_architecture_violation(self, data: dict) -> str:
        """Format architecture violation."""
        violation_type = data.get('violation_type', 'unknown')
        violation_file = data.get('file', 'unknown')
        violation_desc = data.get('description', '')
        violation_suggestion = data.get('suggestion', '')
        
        return f"""
ARCHITECTURE VIOLATION DETECTED:
- Type: {violation_type}
- File: {violation_file}
- Description: {violation_desc}
- Suggestion: {violation_suggestion}

ACTION REQUIRED:
1. If file is in wrong location → use move_file
2. If violation is complex → use create_issue_report

EXAMPLE (if file misplaced):
move_file(
    file_path="{violation_file}",
    new_path="correct/location/file.py",
    reason="Fix architecture violation: {violation_type}"
)

EXAMPLE (if complex):
create_issue_report(
    title="Architecture violation: {violation_type}",
    description="{violation_desc}",
    suggested_fix="{violation_suggestion}"
)
"""
    
    def _format_circular_import(self, data: dict) -> str:
        """Format circular import detection."""
        cycle_path = data.get('cycle', [])
        cycle_files = data.get('files', [])
        cycle_desc = data.get('description', '')
        
        cycle_str = ' → '.join(cycle_path) if cycle_path else 'unknown'
        files_str = ', '.join(cycle_files) if cycle_files else 'unknown'
        
        return f"""
CIRCULAR IMPORT DETECTED:
- Cycle: {cycle_str}
- Files involved: {files_str}

ACTION REQUIRED:
Create a detailed issue report - circular imports require careful analysis:

EXAMPLE:
create_issue_report(
    title="Circular import: {len(cycle_files)} files",
    description="{cycle_desc}",
    severity="high",
    suggested_fix="Restructure imports or move shared code to separate module",
    files_affected={cycle_files}
)

⚠️ Circular imports are complex - create a detailed report for developer review.
"""
    
    def _format_generic_architecture(self, data: dict) -> str:
        """Format generic architecture issue."""
        return f"""
ARCHITECTURE ISSUE DETECTED:
{data}

ACTION REQUIRED:
Analyze the issue and use appropriate tools:
- move_file: If files are in wrong locations
- create_issue_report: If issue requires developer decision
"""