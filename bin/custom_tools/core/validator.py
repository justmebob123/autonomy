#!/usr/bin/env python3
"""
Tool Validator - Validates custom tools for safety and correctness.
"""

import ast
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class CustomToolValidator:
    """
    Validates custom tools for safety and correctness.
    
    Checks:
    - Syntax validity
    - BaseTool inheritance
    - Required methods implemented
    - No dangerous operations
    - Proper error handling
    """
    
    # Dangerous operations to detect
    DANGEROUS_PATTERNS = [
        'eval(',
        'exec(',
        'os.system(',
        '__import__(',
        'subprocess.call(',
        'shell=True',
        'compile(',
    ]
    
    def __init__(self):
        """Initialize validator."""
        pass
    
    def validate_tool(self, tool_file: Path) -> Tuple[bool, List[str]]:
        """
        Validate a tool file.
        
        Args:
            tool_file: Path to tool file
            
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        if not tool_file.exists():
            return False, [f"Tool file not found: {tool_file}"]
        
        try:
            content = tool_file.read_text()
        except Exception as e:
            return False, [f"Failed to read tool file: {e}"]
        
        # Check 1: Syntax validity
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return False, [f"Syntax error: {e}"]
        
        # Check 2: BaseTool inheritance
        has_basetool = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == 'BaseTool':
                        has_basetool = True
                        break
        
        if not has_basetool:
            issues.append("Tool class must inherit from BaseTool")
        
        # Check 3: Required methods
        has_execute = 'def execute(' in content
        if not has_execute:
            issues.append("Tool must implement execute() method")
        
        # Check 4: Dangerous operations
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in content:
                issues.append(f"Dangerous operation detected: {pattern}")
        
        # Check 5: Error handling
        if 'try:' not in content or 'except' not in content:
            issues.append("Tool should have error handling (try/except)")
        
        # Check 6: Return type
        if 'return ToolResult(' not in content:
            issues.append("Tool should return ToolResult")
        
        is_valid = len(issues) == 0
        return is_valid, issues