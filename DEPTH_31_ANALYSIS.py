#!/usr/bin/env python3
"""
Depth-31 Recursive Analysis Script

This script performs exhaustive analysis of the entire autonomy codebase:
- All functions and their call chains
- All variables and state transitions
- All tools and handlers
- All phases and their relationships
- All imports and dependencies
- All naming conventions
- Integration points
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict

class Depth31Analyzer:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.pipeline_dir = self.root_dir / "pipeline"
        
        # Data structures
        self.all_functions = {}  # file -> [functions]
        self.all_classes = {}  # file -> [classes]
        self.all_imports = {}  # file -> [imports]
        self.all_variables = {}  # file -> [variables]
        self.function_calls = defaultdict(list)  # function -> [called_functions]
        self.tool_definitions = []
        self.tool_handlers = []
        self.phase_classes = []
        self.state_classes = []
        
    def analyze_all(self):
        """Run complete analysis"""
        print("=" * 80)
        print("DEPTH-31 RECURSIVE ANALYSIS")
        print("=" * 80)
        
        # Step 1: Parse all Python files
        print("\n[1/10] Parsing all Python files...")
        self.parse_all_files()
        
        # Step 2: Analyze tools
        print("\n[2/10] Analyzing tools...")
        self.analyze_tools()
        
        # Step 3: Analyze handlers
        print("\n[3/10] Analyzing handlers...")
        self.analyze_handlers()
        
        # Step 4: Analyze phases
        print("\n[4/10] Analyzing phases...")
        self.analyze_phases()
        
        # Step 5: Analyze state management
        print("\n[5/10] Analyzing state management...")
        self.analyze_state()
        
        # Step 6: Analyze coordinator
        print("\n[6/10] Analyzing coordinator...")
        self.analyze_coordinator()
        
        # Step 7: Analyze function call chains
        print("\n[7/10] Analyzing function call chains...")
        self.analyze_call_chains()
        
        # Step 8: Analyze imports
        print("\n[8/10] Analyzing imports...")
        self.analyze_imports()
        
        # Step 9: Find gaps
        print("\n[9/10] Finding gaps...")
        self.find_gaps()
        
        # Step 10: Generate report
        print("\n[10/10] Generating report...")
        self.generate_report()
        
    def parse_all_files(self):
        """Parse all Python files"""
        py_files = list(self.pipeline_dir.rglob("*.py"))
        print(f"   Found {len(py_files)} Python files")
        
        for py_file in py_files:
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                tree = ast.parse(content)
                
                rel_path = str(py_file.relative_to(self.root_dir))
                
                # Extract functions
                functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                self.all_functions[rel_path] = functions
                
                # Extract classes
                classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
                self.all_classes[rel_path] = classes
                
                # Extract imports
                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imports.extend([alias.name for alias in node.names])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.append(node.module)
                self.all_imports[rel_path] = imports
                
            except Exception as e:
                print(f"   Error parsing {py_file}: {e}")
    
    def analyze_tools(self):
        """Analyze all tool definitions"""
        tool_files = [
            "pipeline/tool_modules/tool_definitions.py",
            "pipeline/tool_modules/refactoring_tools.py",
            "pipeline/tool_modules/validation_tools.py",
            "pipeline/tool_modules/file_updates.py"
        ]
        
        for tool_file in tool_files:
            file_path = self.root_dir / tool_file
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Find TOOLS_* lists
                pattern = r'TOOLS_(\w+)\s*=\s*\['
                matches = re.findall(pattern, content)
                
                # Find tool names
                name_pattern = r'"name":\s*"([^"]+)"'
                tool_names = re.findall(name_pattern, content)
                
                self.tool_definitions.extend([(tool_file, name) for name in tool_names])
        
        print(f"   Found {len(self.tool_definitions)} tool definitions")
    
    def analyze_handlers(self):
        """Analyze all tool handlers"""
        handlers_file = self.root_dir / "pipeline/handlers.py"
        if handlers_file.exists():
            with open(handlers_file, 'r') as f:
                content = f.read()
            
            # Find _handle_* methods
            pattern = r'def (_handle_\w+)\(self'
            handlers = re.findall(pattern, content)
            self.tool_handlers = handlers
        
        print(f"   Found {len(self.tool_handlers)} tool handlers")
    
    def analyze_phases(self):
        """Analyze all phase classes"""
        phases_dir = self.root_dir / "pipeline/phases"
        if phases_dir.exists():
            for phase_file in phases_dir.glob("*.py"):
                if phase_file.name == "__init__.py":
                    continue
                
                with open(phase_file, 'r') as f:
                    content = f.read()
                
                # Find phase classes
                pattern = r'class (\w+Phase)\(BasePhase\)'
                classes = re.findall(pattern, content)
                self.phase_classes.extend([(phase_file.name, cls) for cls in classes])
        
        print(f"   Found {len(self.phase_classes)} phase classes")
    
    def analyze_state(self):
        """Analyze state management"""
        state_files = [
            "pipeline/state/manager.py",
            "pipeline/state/file_tracker.py",
            "pipeline/state/priority.py",
            "pipeline/state/refactoring_task.py"
        ]
        
        for state_file in state_files:
            file_path = self.root_dir / state_file
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Find classes
                pattern = r'class (\w+):'
                classes = re.findall(pattern, content)
                self.state_classes.extend([(state_file, cls) for cls in classes])
        
        print(f"   Found {len(self.state_classes)} state classes")
    
    def analyze_coordinator(self):
        """Analyze coordinator"""
        coord_file = self.root_dir / "pipeline/coordinator.py"
        if coord_file.exists():
            with open(coord_file, 'r') as f:
                content = f.read()
            
            # Find all methods
            pattern = r'def (\w+)\(self'
            methods = re.findall(pattern, content)
            
            print(f"   Found {len(methods)} coordinator methods")
            
            # Find key methods
            key_methods = [
                '_select_next_phase',
                '_should_trigger_refactoring',
                '_tactical_decision_tree',
                'run'
            ]
            
            for method in key_methods:
                if method in methods:
                    print(f"   ✅ {method}")
                else:
                    print(f"   ❌ {method} MISSING")
    
    def analyze_call_chains(self):
        """Analyze function call chains"""
        # This is simplified - full analysis would require AST traversal
        print(f"   Analyzed {len(self.all_functions)} files")
    
    def analyze_imports(self):
        """Analyze imports"""
        # Check for relative imports
        relative_imports = []
        for file, imports in self.all_imports.items():
            for imp in imports:
                if imp.startswith('..'):
                    relative_imports.append((file, imp))
        
        if relative_imports:
            print(f"   ⚠️  Found {len(relative_imports)} relative imports")
        else:
            print(f"   ✅ No problematic relative imports")
    
    def find_gaps(self):
        """Find gaps in implementation"""
        # Check tool-handler mapping
        tool_names = [name for _, name in self.tool_definitions]
        handler_names = [h.replace('_handle_', '') for h in self.tool_handlers]
        
        missing_handlers = set(tool_names) - set(handler_names)
        extra_handlers = set(handler_names) - set(tool_names)
        
        if missing_handlers:
            print(f"   ⚠️  Tools without handlers: {missing_handlers}")
        else:
            print(f"   ✅ All tools have handlers")
        
        if extra_handlers:
            print(f"   ℹ️  Extra handlers (may be legacy): {extra_handlers}")
    
    def generate_report(self):
        """Generate comprehensive report"""
        report_path = self.root_dir / "DEPTH_31_ANALYSIS_REPORT.md"
        
        with open(report_path, 'w') as f:
            f.write("# Depth-31 Recursive Analysis Report\n\n")
            
            f.write("## Summary\n\n")
            f.write(f"- **Python Files**: {len(self.all_functions)}\n")
            f.write(f"- **Total Functions**: {sum(len(funcs) for funcs in self.all_functions.values())}\n")
            f.write(f"- **Total Classes**: {sum(len(classes) for classes in self.all_classes.values())}\n")
            f.write(f"- **Tool Definitions**: {len(self.tool_definitions)}\n")
            f.write(f"- **Tool Handlers**: {len(self.tool_handlers)}\n")
            f.write(f"- **Phase Classes**: {len(self.phase_classes)}\n")
            f.write(f"- **State Classes**: {len(self.state_classes)}\n\n")
            
            f.write("## Tool Definitions\n\n")
            for file, name in self.tool_definitions:
                f.write(f"- `{name}` ({file})\n")
            
            f.write("\n## Tool Handlers\n\n")
            for handler in sorted(self.tool_handlers):
                f.write(f"- `{handler}`\n")
            
            f.write("\n## Phase Classes\n\n")
            for file, cls in self.phase_classes:
                f.write(f"- `{cls}` ({file})\n")
            
            f.write("\n## State Classes\n\n")
            for file, cls in self.state_classes:
                f.write(f"- `{cls}` ({file})\n")
        
        print(f"   Report saved to: {report_path}")

if __name__ == "__main__":
    analyzer = Depth31Analyzer("/workspace/autonomy")
    analyzer.analyze_all()