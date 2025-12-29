#!/usr/bin/env python3
"""
analyze_imports - Analyze import statements in a Python file

This is an example custom tool demonstrating the BaseTool pattern.

Category: analysis
Version: 1.0.0
Author: SuperNinja AI
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any
import ast

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.base import BaseTool, ToolResult


class AnalyzeImports(BaseTool):
    """
    Analyze import statements in a Python file.
    
    Extracts and categorizes all imports:
    - Standard library imports
    - Third-party imports
    - Local imports
    - Unused imports (basic detection)
    
    Parameters:
        filepath: Path to Python file to analyze (relative to project root)
    
    Returns:
        ToolResult with import analysis
    
    Usage:
        Use when you need to understand a file's dependencies,
        detect circular imports, or identify unused imports.
    
    Examples:
        analyze_imports(filepath='pipeline/phases/qa.py')
        analyze_imports(filepath='src/main.py')
    """
    
    # Tool metadata
    name = "analyze_imports"
    description = "Analyze import statements in a Python file"
    version = "1.0.0"
    category = "analysis"
    author = "SuperNinja AI"
    
    # Security settings
    requires_filesystem = True
    requires_network = False
    requires_subprocess = False
    timeout_seconds = 30
    max_file_size_mb = 10
    
    def validate_inputs(self, **kwargs) -> tuple:
        """Validate tool inputs."""
        if 'filepath' not in kwargs:
            return False, "filepath is required"
        
        filepath = kwargs['filepath']
        if not isinstance(filepath, str):
            return False, "filepath must be a string"
        
        if not filepath.endswith('.py'):
            return False, "filepath must be a Python file (.py)"
        
        full_path = self.project_dir / filepath
        if not full_path.exists():
            return False, f"File not found: {filepath}"
        
        # Check file size
        file_size_mb = full_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            return False, f"File too large: {file_size_mb:.1f}MB (max: {self.max_file_size_mb}MB)"
        
        return True, None
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        try:
            # Extract parameters
            filepath = kwargs.get('filepath')
            full_path = self.project_dir / filepath
            
            # Read and parse file
            with open(full_path, 'r') as f:
                content = f.read()
            
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                return ToolResult(
                    success=False,
                    error=f"Syntax error in file: {e}"
                )
            
            # Extract imports
            imports = self._extract_imports(tree)
            
            # Categorize imports
            categorized = self._categorize_imports(imports)
            
            # Detect potential issues
            issues = self._detect_issues(imports, content)
            
            result = {
                "filepath": filepath,
                "total_imports": len(imports),
                "imports": imports,
                "categorized": categorized,
                "issues": issues,
                "summary": {
                    "stdlib": len(categorized['stdlib']),
                    "third_party": len(categorized['third_party']),
                    "local": len(categorized['local']),
                    "total_issues": len(issues)
                }
            }
            
            return ToolResult(
                success=True,
                result=result,
                metadata={
                    "tool": self.name,
                    "version": self.version,
                    "filepath": filepath
                }
            )
            
        except FileNotFoundError as e:
            return ToolResult(
                success=False,
                error=f"File not found: {e}"
            )
        
        except PermissionError as e:
            return ToolResult(
                success=False,
                error=f"Permission denied: {e}"
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Analysis failed: {e}"
            )
    
    def _extract_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract all import statements."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'type': 'import',
                        'module': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno
                    })
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append({
                        'type': 'from_import',
                        'module': module,
                        'name': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno
                    })
        
        return imports
    
    def _categorize_imports(self, imports: List[Dict]) -> Dict[str, List[str]]:
        """Categorize imports into stdlib, third-party, and local."""
        import sys
        stdlib_modules = set(sys.stdlib_module_names) if hasattr(sys, 'stdlib_module_names') else set()
        
        categorized = {
            'stdlib': [],
            'third_party': [],
            'local': []
        }
        
        for imp in imports:
            module = imp['module']
            base_module = module.split('.')[0]
            
            if base_module in stdlib_modules:
                categorized['stdlib'].append(module)
            elif module.startswith('.') or base_module in ['pipeline', 'scripts']:
                categorized['local'].append(module)
            else:
                categorized['third_party'].append(module)
        
        return categorized
    
    def _detect_issues(self, imports: List[Dict], content: str) -> List[Dict[str, Any]]:
        """Detect potential import issues."""
        issues = []
        
        # Check for duplicate imports
        seen = set()
        for imp in imports:
            key = (imp['module'], imp.get('name', ''))
            if key in seen:
                issues.append({
                    'type': 'duplicate_import',
                    'module': imp['module'],
                    'line': imp['line'],
                    'message': f"Duplicate import: {imp['module']}"
                })
            seen.add(key)
        
        # Check for unused imports (basic check)
        for imp in imports:
            module = imp['module']
            name = imp.get('name', module.split('.')[-1])
            
            # Simple check: is the name used in the code?
            if name not in content.replace(f"import {name}", ""):
                issues.append({
                    'type': 'potentially_unused',
                    'module': module,
                    'name': name,
                    'line': imp['line'],
                    'message': f"Potentially unused import: {name}"
                })
        
        return issues


def main():
    """CLI entry point for subprocess execution."""
    parser = argparse.ArgumentParser(description="Analyze import statements in a Python file")
    parser.add_argument("--project-dir", required=True, help="Project directory")
    parser.add_argument("--args", required=True, help="Tool arguments (JSON)")
    
    args = parser.parse_args()
    
    try:
        # Parse arguments
        tool_args = json.loads(args.args)
        
        # Execute tool
        tool = AnalyzeImports(args.project_dir)
        result = tool.run(**tool_args)
        
        # Output result as JSON
        output = result.to_dict()
        print(json.dumps(output))
        
        sys.exit(0 if result.success else 1)
    
    except json.JSONDecodeError as e:
        print(json.dumps({
            "success": False,
            "error": f"Invalid arguments JSON: {e}"
        }))
        sys.exit(1)
    
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": f"Tool initialization failed: {e}"
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()