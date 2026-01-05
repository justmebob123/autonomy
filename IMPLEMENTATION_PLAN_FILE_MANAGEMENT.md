# Implementation Plan: Multi-Step File Management System

## Overview
This document provides a detailed, step-by-step implementation plan for adding comprehensive file management and multi-step AI collaboration to the autonomy pipeline.

## Phase 1: Foundation (Week 1)

### Task 1.1: Create File Discovery Utilities
**File:** `pipeline/file_discovery.py`

```python
"""
File Discovery Utilities

Provides tools for finding similar files, detecting conflicts,
and extracting naming conventions.
"""

from pathlib import Path
from typing import List, Dict, Optional
from difflib import SequenceMatcher
import re
import ast

class FileDiscovery:
    """Discovers and analyzes files in the project"""
    
    def __init__(self, project_dir: Path, logger):
        self.project_dir = Path(project_dir)
        self.logger = logger
        self._cache = {}
    
    def find_similar_files(self, target_file: str, 
                          similarity_threshold: float = 0.6) -> List[Dict]:
        """
        Find files with similar names or functionality.
        
        Args:
            target_file: Proposed filename
            similarity_threshold: Minimum similarity (0.0-1.0)
            
        Returns:
            List of similar files with metadata
        """
        target_name = Path(target_file).stem
        similar = []
        
        for py_file in self.project_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            file_name = py_file.stem
            similarity = SequenceMatcher(None, target_name, file_name).ratio()
            
            if similarity >= similarity_threshold:
                similar.append({
                    'path': str(py_file.relative_to(self.project_dir)),
                    'name': file_name,
                    'similarity': similarity,
                    'size': py_file.stat().st_size,
                    'directory': str(py_file.parent.relative_to(self.project_dir)),
                    'purpose': self._extract_file_purpose(py_file),
                    'classes': self._extract_classes(py_file),
                    'functions': self._extract_functions(py_file)
                })
        
        return sorted(similar, key=lambda x: x['similarity'], reverse=True)
    
    def find_conflicting_files(self) -> List[Dict]:
        """
        Find groups of files that may be duplicates or conflicts.
        
        Returns:
            List of conflict groups
        """
        from collections import defaultdict
        
        groups = defaultdict(list)
        all_files = list(self.project_dir.rglob("*.py"))
        
        # Group by stem similarity
        for i, file1 in enumerate(all_files):
            if file1.name == "__init__.py":
                continue
                
            name1 = file1.stem
            
            for file2 in all_files[i+1:]:
                if file2.name == "__init__.py":
                    continue
                    
                name2 = file2.stem
                similarity = SequenceMatcher(None, name1, name2).ratio()
                
                if similarity > 0.7:
                    group_key = min(name1, name2)
                    groups[group_key].extend([
                        str(file1.relative_to(self.project_dir)),
                        str(file2.relative_to(self.project_dir))
                    ])
        
        # Convert to conflict groups
        conflicts = []
        for pattern, files in groups.items():
            unique_files = list(set(files))
            if len(unique_files) > 1:
                conflicts.append({
                    'pattern': pattern,
                    'files': unique_files,
                    'count': len(unique_files),
                    'severity': self._assess_conflict_severity(unique_files)
                })
        
        return conflicts
    
    def _extract_file_purpose(self, filepath: Path) -> str:
        """Extract purpose from docstring or comments"""
        try:
            content = filepath.read_text()
            tree = ast.parse(content)
            docstring = ast.get_docstring(tree)
            if docstring:
                # Return first line of docstring
                return docstring.split('\n')[0][:100]
        except:
            pass
        return "Unknown"
    
    def _extract_classes(self, filepath: Path) -> List[str]:
        """Extract class names from file"""
        try:
            content = filepath.read_text()
            tree = ast.parse(content)
            return [node.name for node in ast.walk(tree) 
                   if isinstance(node, ast.ClassDef)]
        except:
            return []
    
    def _extract_functions(self, filepath: Path) -> List[str]:
        """Extract function names from file"""
        try:
            content = filepath.read_text()
            tree = ast.parse(content)
            return [node.name for node in ast.walk(tree) 
                   if isinstance(node, ast.FunctionDef) 
                   and not node.name.startswith('_')]
        except:
            return []
    
    def _assess_conflict_severity(self, files: List[str]) -> str:
        """Assess how severe a file conflict is"""
        # Check if files are in same directory
        directories = set(Path(f).parent for f in files)
        
        if len(directories) == 1:
            return "high"  # Same directory = likely duplicates
        elif len(directories) == 2:
            return "medium"  # Different directories = may be intentional
        else:
            return "low"  # Many directories = likely different purposes
```

### Task 1.2: Create Naming Convention Manager
**File:** `pipeline/naming_conventions.py`

```python
"""
Naming Convention Manager

Extracts, validates, and enforces naming conventions from ARCHITECTURE.md
"""

from pathlib import Path
from typing import Dict, List, Optional
import re

class NamingConventionManager:
    """Manages naming conventions for the project"""
    
    def __init__(self, project_dir: Path, logger):
        self.project_dir = Path(project_dir)
        self.logger = logger
        self.conventions = self._load_conventions()
    
    def _load_conventions(self) -> Dict:
        """Load conventions from ARCHITECTURE.md"""
        arch_file = self.project_dir / "ARCHITECTURE.md"
        
        if not arch_file.exists():
            self.logger.warning("ARCHITECTURE.md not found, using defaults")
            return self._get_default_conventions()
        
        content = arch_file.read_text()
        conventions = self._parse_conventions(content)
        
        if not conventions:
            self.logger.warning("No conventions found in ARCHITECTURE.md, using defaults")
            return self._get_default_conventions()
        
        return conventions
    
    def _parse_conventions(self, content: str) -> Dict:
        """Parse conventions from ARCHITECTURE.md content"""
        conventions = {
            'directories': {},
            'file_patterns': {},
            'class_patterns': {},
            'function_patterns': {}
        }
        
        # Look for Naming Conventions section
        pattern = r'##\s+Naming Conventions(.*?)(?=##|\Z)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        
        if not match:
            return conventions
        
        section = match.group(1)
        
        # Parse directory conventions
        dir_pattern = r'-\s+\*\*([^/]+)/\*\*:\s+(.+?)(?=\n|$)'
        for match in re.finditer(dir_pattern, section):
            directory = match.group(1)
            purpose = match.group(2).strip()
            conventions['directories'][directory] = {
                'purpose': purpose,
                'pattern': self._extract_pattern(purpose)
            }
        
        # Parse file patterns
        file_pattern = r'-\s+Pattern:\s+`([^`]+)`'
        for match in re.finditer(file_pattern, section):
            pattern = match.group(1)
            conventions['file_patterns'][pattern] = True
        
        return conventions
    
    def _get_default_conventions(self) -> Dict:
        """Get default conventions if none defined"""
        return {
            'directories': {
                'api': {'purpose': 'REST API endpoints', 'pattern': 'api/{resource}.py'},
                'services': {'purpose': 'Business logic', 'pattern': 'services/*_service.py'},
                'models': {'purpose': 'Data models', 'pattern': 'models/{entity}.py'},
                'core': {'purpose': 'Core utilities', 'pattern': 'core/{utility}.py'},
            },
            'file_patterns': {
                '*_service.py': 'Business logic services',
                '*_manager.py': 'Resource managers',
                '*_generator.py': 'Content generators',
                '*_engine.py': 'Processing engines',
            },
            'class_patterns': {
                '*Service': 'Service classes',
                '*Manager': 'Manager classes',
                '*Generator': 'Generator classes',
                '*Engine': 'Engine classes',
            },
            'function_patterns': {
                'create_*': 'Creation functions',
                'get_*': 'Retrieval functions',
                'update_*': 'Update functions',
                'delete_*': 'Deletion functions',
            }
        }
    
    def _extract_pattern(self, purpose: str) -> Optional[str]:
        """Extract file pattern from purpose description"""
        # Look for pattern in parentheses or after "Pattern:"
        pattern_match = re.search(r'Pattern:\s*`([^`]+)`', purpose)
        if pattern_match:
            return pattern_match.group(1)
        
        pattern_match = re.search(r'\(([^)]+\.py)\)', purpose)
        if pattern_match:
            return pattern_match.group(1)
        
        return None
    
    def validate_filename(self, filepath: str) -> Dict:
        """
        Validate filename against conventions.
        
        Returns:
            Dict with 'valid', 'issues', 'suggestions'
        """
        path = Path(filepath)
        issues = []
        suggestions = []
        
        # Check directory
        directory = str(path.parent)
        if directory in self.conventions['directories']:
            dir_info = self.conventions['directories'][directory]
            expected_pattern = dir_info.get('pattern')
            
            if expected_pattern and not self._matches_pattern(path.name, expected_pattern):
                issues.append(f"Filename doesn't match directory pattern: {expected_pattern}")
                suggestions.append(self._suggest_name(path.name, expected_pattern))
        
        # Check file pattern
        matched_pattern = False
        for pattern, purpose in self.conventions['file_patterns'].items():
            if self._matches_pattern(path.name, pattern):
                matched_pattern = True
                break
        
        if not matched_pattern and path.suffix == '.py':
            issues.append("Filename doesn't match any known pattern")
            suggestions.append("Consider using a standard pattern like *_service.py or *_manager.py")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'suggestions': suggestions
        }
    
    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches pattern"""
        # Convert glob pattern to regex
        regex_pattern = pattern.replace('*', '.*').replace('.', r'\.')
        return bool(re.match(regex_pattern, filename))
    
    def _suggest_name(self, filename: str, pattern: str) -> str:
        """Suggest correct name based on pattern"""
        # Extract base name
        base = Path(filename).stem
        
        # Apply pattern
        if '*' in pattern:
            return pattern.replace('*', base)
        else:
            return pattern
    
    def get_expected_directory(self, filepath: str) -> Optional[str]:
        """Get expected directory for a file based on its name"""
        filename = Path(filepath).name
        
        # Check file patterns
        for pattern, purpose in self.conventions['file_patterns'].items():
            if self._matches_pattern(filename, pattern):
                # Find directory that uses this pattern
                for directory, info in self.conventions['directories'].items():
                    if info.get('pattern') and pattern in info['pattern']:
                        return directory
        
        return None
    
    def generate_conventions_markdown(self) -> str:
        """Generate markdown documentation of conventions"""
        lines = ["## Naming Conventions\n"]
        
        lines.append("### Directory Structure\n")
        for directory, info in sorted(self.conventions['directories'].items()):
            lines.append(f"- **{directory}/**: {info['purpose']}")
            if info.get('pattern'):
                lines.append(f"  - Pattern: `{info['pattern']}`")
        
        lines.append("\n### File Naming Patterns\n")
        for pattern, purpose in sorted(self.conventions['file_patterns'].items()):
            lines.append(f"- **{pattern}**: {purpose}")
        
        return "\n".join(lines)
```

### Task 1.3: Update Coding Phase with File Discovery
**File:** `pipeline/phases/coding.py` (modifications)

```python
# Add to imports
from ..file_discovery import FileDiscovery
from ..naming_conventions import NamingConventionManager

# Add to __init__
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.init_loop_detection()
    
    # NEW: File management utilities
    self.file_discovery = FileDiscovery(self.project_dir, self.logger)
    self.naming_conventions = NamingConventionManager(self.project_dir, self.logger)

# Modify _build_user_message
def _build_user_message(self, task: TaskState, context: str, error_context: str) -> str:
    """Build user message with file discovery"""
    parts = []
    
    # STEP 1: FILE DISCOVERY
    if task.target_file:
        similar_files = self.file_discovery.find_similar_files(task.target_file)
        
        if similar_files:
            parts.append("## ⚠️ Similar Files Found\n")
            parts.append("Before creating a new file, please review these existing files:\n")
            
            for i, file_info in enumerate(similar_files[:5], 1):
                parts.append(f"\n### {i}. {file_info['path']}")
                parts.append(f"- **Similarity:** {file_info['similarity']:.0%}")
                parts.append(f"- **Size:** {file_info['size']} bytes")
                parts.append(f"- **Purpose:** {file_info['purpose']}")
                
                if file_info['classes']:
                    parts.append(f"- **Classes:** {', '.join(file_info['classes'][:3])}")
                
                if file_info['functions']:
                    funcs = ', '.join(file_info['functions'][:5])
                    parts.append(f"- **Functions:** {funcs}")
            
            parts.append("\n## 🤔 Decision Required\n")
            parts.append("Please decide:")
            parts.append("1. **Modify existing file** - If one of the above files should be updated")
            parts.append("2. **Create new file** - If this is genuinely new functionality")
            parts.append("3. **Use different name** - If the name conflicts with conventions")
            parts.append("\nUse `read_file` to examine existing files before deciding.")
    
    # STEP 2: NAMING CONVENTIONS
    if task.target_file:
        validation = self.naming_conventions.validate_filename(task.target_file)
        
        if not validation['valid']:
            parts.append("\n## ⚠️ Naming Convention Issues\n")
            for issue in validation['issues']:
                parts.append(f"- {issue}")
            
            if validation['suggestions']:
                parts.append("\n**Suggestions:**")
                for suggestion in validation['suggestions']:
                    parts.append(f"- {suggestion}")
    
    # STEP 3: TASK DETAILS (existing code)
    parts.append(f"\n## Task Details\n")
    parts.append(f"**Description:** {task.description}")
    parts.append(f"**Target file:** {task.target_file}")
    
    # ... rest of existing code ...
    
    return "\n".join(parts)
```

## Phase 2: Refactoring Enhancement (Week 2)

### Task 2.1: Create File Conflict Resolver
**File:** `pipeline/file_conflict_resolver.py`

```python
"""
File Conflict Resolver

Handles detection and resolution of conflicting/duplicate files
through multi-step AI collaboration.
"""

from pathlib import Path
from typing import List, Dict, Optional
import ast

class FileConflictResolver:
    """Resolves file conflicts through AI collaboration"""
    
    def __init__(self, project_dir: Path, logger, file_discovery):
        self.project_dir = Path(project_dir)
        self.logger = logger
        self.file_discovery = file_discovery
    
    def find_conflicts(self) -> List[Dict]:
        """Find all file conflicts in the project"""
        return self.file_discovery.find_conflicting_files()
    
    def build_conflict_review_message(self, conflict_group: Dict) -> str:
        """Build message for AI to review a conflict group"""
        parts = []
        
        parts.append(f"# File Conflict Review: {conflict_group['pattern']}\n")
        parts.append(f"**Severity:** {conflict_group['severity']}")
        parts.append(f"**Files involved:** {conflict_group['count']}\n")
        
        # Load and analyze each file
        for i, filepath in enumerate(conflict_group['files'], 1):
            parts.append(f"\n## File {i}: `{filepath}`\n")
            
            file_path = self.project_dir / filepath
            if not file_path.exists():
                parts.append("*File not found*")
                continue
            
            # Get file info
            content = file_path.read_text()
            size = len(content)
            lines = content.split('\n')
            
            parts.append(f"- **Size:** {size} bytes ({len(lines)} lines)")
            
            # Extract structure
            try:
                tree = ast.parse(content)
                
                # Get docstring
                docstring = ast.get_docstring(tree)
                if docstring:
                    first_line = docstring.split('\n')[0]
                    parts.append(f"- **Purpose:** {first_line}")
                
                # Get classes
                classes = [node.name for node in ast.walk(tree) 
                          if isinstance(node, ast.ClassDef)]
                if classes:
                    parts.append(f"- **Classes:** {', '.join(classes)}")
                
                # Get functions
                functions = [node.name for node in ast.walk(tree) 
                            if isinstance(node, ast.FunctionDef) 
                            and not node.name.startswith('_')]
                if functions:
                    funcs = ', '.join(functions[:10])
                    if len(functions) > 10:
                        funcs += f" ... and {len(functions) - 10} more"
                    parts.append(f"- **Public Functions:** {funcs}")
                
            except SyntaxError:
                parts.append("- **Error:** File has syntax errors")
            
            # Show preview
            parts.append("\n**Content Preview:**")
            parts.append("```python")
            parts.append('\n'.join(lines[:30]))
            if len(lines) > 30:
                parts.append("... (truncated)")
            parts.append("```")
        
        # Add decision prompt
        parts.append("\n## 🎯 Resolution Required\n")
        parts.append("Please analyze these files and provide a resolution plan:")
        parts.append("\n1. **Which file should be the PRIMARY implementation?**")
        parts.append("   - Consider: completeness, code quality, location")
        parts.append("\n2. **What functionality should be MERGED?**")
        parts.append("   - List specific classes/functions to preserve")
        parts.append("   - Identify any advanced features that must not be lost")
        parts.append("\n3. **Which files should be ARCHIVED?**")
        parts.append("   - Files will be moved to `archive/deprecated/` (not deleted)")
        parts.append("\n4. **Are there DIFFERENT PURPOSES?**")
        parts.append("   - If files serve different purposes, explain and suggest renaming")
        parts.append("\nUse the `resolve_file_conflict` tool to provide your decision.")
        
        return "\n".join(parts)
    
    def execute_resolution(self, resolution: Dict) -> Dict:
        """Execute the conflict resolution plan"""
        keep_file = resolution.get('keep_file')
        merge_from = resolution.get('merge_from', [])
        archive_files = resolution.get('archive_files', [])
        merge_plan = resolution.get('merge_plan', '')
        
        results = {
            'success': True,
            'actions': [],
            'errors': []
        }
        
        self.logger.info(f"Executing conflict resolution:")
        self.logger.info(f"  Keep: {keep_file}")
        self.logger.info(f"  Merge from: {', '.join(merge_from)}")
        self.logger.info(f"  Archive: {', '.join(archive_files)}")
        
        # Create archive directory
        archive_dir = self.project_dir / "archive" / "deprecated"
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Archive files
        for filepath in archive_files:
            try:
                source = self.project_dir / filepath
                if source.exists():
                    # Preserve directory structure in archive
                    rel_path = Path(filepath)
                    dest = archive_dir / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    
                    source.rename(dest)
                    results['actions'].append(f"Archived: {filepath}")
                    self.logger.info(f"  ✓ Archived {filepath}")
            except Exception as e:
                results['errors'].append(f"Failed to archive {filepath}: {e}")
                results['success'] = False
        
        # Note: Actual merging would be done by AI through file modification tools
        results['actions'].append(f"Merge plan documented: {merge_plan}")
        
        return results
```

### Task 2.2: Add Conflict Resolution to Refactoring Phase
**File:** `pipeline/phases/refactoring.py` (modifications)

```python
# Add to imports
from ..file_conflict_resolver import FileConflictResolver

# Add to __init__
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    
    # NEW: File conflict resolution
    from ..file_discovery import FileDiscovery
    self.file_discovery = FileDiscovery(self.project_dir, self.logger)
    self.conflict_resolver = FileConflictResolver(
        self.project_dir, 
        self.logger, 
        self.file_discovery
    )

# Add new method
def _handle_file_conflicts(self, state: PipelineState) -> PhaseResult:
    """Handle file conflicts through multi-step AI collaboration"""
    
    # Find conflicts
    conflicts = self.conflict_resolver.find_conflicts()
    
    if not conflicts:
        self.logger.info("  ✓ No file conflicts detected")
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message="No file conflicts found"
        )
    
    self.logger.info(f"  ⚠️  Found {len(conflicts)} file conflict groups")
    
    # Process each conflict group
    for conflict in conflicts:
        if conflict['severity'] == 'low':
            continue  # Skip low-severity conflicts
        
        self.logger.info(f"  Reviewing conflict: {conflict['pattern']}")
        
        # Build review message
        review_message = self.conflict_resolver.build_conflict_review_message(conflict)
        
        # Get resolution tools
        tools = self._get_conflict_resolution_tools()
        
        # Ask AI for resolution
        response = self.chat_with_history(review_message, tools)
        
        # Execute resolution if provided
        if response.get('tool_calls'):
            for call in response['tool_calls']:
                if call.get('function', {}).get('name') == 'resolve_file_conflict':
                    resolution = call.get('function', {}).get('arguments', {})
                    result = self.conflict_resolver.execute_resolution(resolution)
                    
                    if result['success']:
                        self.logger.info(f"  ✓ Resolved conflict: {conflict['pattern']}")
                    else:
                        self.logger.error(f"  ✗ Failed to resolve: {', '.join(result['errors'])}")
    
    return PhaseResult(
        success=True,
        phase=self.phase_name,
        message=f"Processed {len(conflicts)} file conflicts"
    )

def _get_conflict_resolution_tools(self) -> List[Dict]:
    """Get tools for conflict resolution"""
    return [
        {
            "type": "function",
            "function": {
                "name": "resolve_file_conflict",
                "description": "Resolve file conflict by specifying resolution plan",
                "parameters": {
                    "type": "object",
                    "required": ["keep_file", "merge_plan"],
                    "properties": {
                        "keep_file": {
                            "type": "string",
                            "description": "Path to file to keep as primary"
                        },
                        "merge_from": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Files to merge functionality from"
                        },
                        "archive_files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Files to archive after merging"
                        },
                        "merge_plan": {
                            "type": "string",
                            "description": "Detailed plan of what to merge and why"
                        },
                        "preserve_features": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific features that must be preserved"
                        },
                        "rename_suggestions": {
                            "type": "object",
                            "description": "Suggested renames if files serve different purposes"
                        }
                    }
                }
            }
        }
    ]
```

## Phase 3: Planning Enhancement (Week 3)

### Task 3.1: Add Convention Enforcement to Planning
**File:** `pipeline/phases/planning.py` (modifications)

```python
# Add to imports
from ..naming_conventions import NamingConventionManager

# Add to __init__
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    
    # NEW: Naming convention management
    self.naming_conventions = NamingConventionManager(self.project_dir, self.logger)

# Add new method
def _update_architecture_with_conventions(self):
    """Update ARCHITECTURE.md with current naming conventions"""
    
    arch_file = self.project_dir / "ARCHITECTURE.md"
    
    # Generate conventions markdown
    conventions_md = self.naming_conventions.generate_conventions_markdown()
    
    # Read existing content
    if arch_file.exists():
        content = arch_file.read_text()
    else:
        content = "# Project Architecture\n\n"
    
    # Replace or append conventions section
    import re
    if "## Naming Conventions" in content:
        # Replace existing
        content = re.sub(
            r'## Naming Conventions.*?(?=##|\Z)',
            conventions_md,
            content,
            flags=re.DOTALL
        )
    else:
        # Append new
        content += f"\n\n{conventions_md}"
    
    # Write back
    arch_file.write_text(content)
    self.logger.info("  ✓ Updated ARCHITECTURE.md with naming conventions")

# Modify execute method
def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
    # ... existing code ...
    
    # NEW: Update architecture with conventions
    self._update_architecture_with_conventions()
    
    # ... rest of existing code ...
```

## Phase 4: Tool Integration (Week 4)

### Task 4.1: Add New Tools to Tool Registry
**File:** `pipeline/tools.py` (additions)

```python
# Add new tool category
TOOLS_FILE_MANAGEMENT = [
    {
        "type": "function",
        "function": {
            "name": "find_similar_files",
            "description": "Find files with similar names or functionality before creating new file. Use this to avoid creating duplicate files.",
            "parameters": {
                "type": "object",
                "required": ["target_file"],
                "properties": {
                    "target_file": {
                        "type": "string",
                        "description": "Proposed filename to check for conflicts"
                    },
                    "similarity_threshold": {
                        "type": "number",
                        "description": "Similarity threshold (0.0-1.0, default 0.6)",
                        "default": 0.6
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "validate_filename",
            "description": "Validate proposed filename against project naming conventions from ARCHITECTURE.md",
            "parameters": {
                "type": "object",
                "required": ["filename"],
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Proposed filename to validate"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_files",
            "description": "Compare multiple files to identify duplicates and merge candidates",
            "parameters": {
                "type": "object",
                "required": ["files"],
                "properties": {
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file paths to compare"
                    }
                }
            }
        }
    }
]

# Update phase tools
def get_tools_for_phase(phase: str, tool_registry=None) -> List[Dict]:
    phase_tools = {
        "coding": TOOLS_CODING + TOOLS_FILE_MANAGEMENT + TOOLS_ANALYSIS,
        "refactoring": TOOLS_REFACTORING + TOOLS_FILE_MANAGEMENT + TOOLS_ANALYSIS,
        "planning": TOOLS_PLANNING + TOOLS_FILE_MANAGEMENT + TOOLS_ANALYSIS,
        # ... rest of phases ...
    }
    # ... rest of function ...
```

### Task 4.2: Add Tool Handlers
**File:** `pipeline/handlers.py` (additions)

```python
# Add to _handlers dictionary
self._handlers = {
    # ... existing handlers ...
    'find_similar_files': self._handle_find_similar_files,
    'validate_filename': self._handle_validate_filename,
    'compare_files': self._handle_compare_files,
}

# Add handler methods
def _handle_find_similar_files(self, args: Dict) -> Dict:
    """Handle find_similar_files tool call"""
    from .file_discovery import FileDiscovery
    
    discovery = FileDiscovery(self.project_dir, self.logger)
    
    target_file = args.get('target_file')
    threshold = args.get('similarity_threshold', 0.6)
    
    similar = discovery.find_similar_files(target_file, threshold)
    
    return {
        'success': True,
        'similar_files': similar,
        'count': len(similar)
    }

def _handle_validate_filename(self, args: Dict) -> Dict:
    """Handle validate_filename tool call"""
    from .naming_conventions import NamingConventionManager
    
    conventions = NamingConventionManager(self.project_dir, self.logger)
    
    filename = args.get('filename')
    validation = conventions.validate_filename(filename)
    
    return {
        'success': True,
        'validation': validation
    }

def _handle_compare_files(self, args: Dict) -> Dict:
    """Handle compare_files tool call"""
    files = args.get('files', [])
    
    comparison = {
        'files': [],
        'similarities': [],
        'recommendations': []
    }
    
    for filepath in files:
        file_path = self.project_dir / filepath
        if not file_path.exists():
            continue
        
        content = file_path.read_text()
        
        # Extract structure
        import ast
        try:
            tree = ast.parse(content)
            classes = [node.name for node in ast.walk(tree) 
                      if isinstance(node, ast.ClassDef)]
            functions = [node.name for node in ast.walk(tree) 
                        if isinstance(node, ast.FunctionDef)]
            
            comparison['files'].append({
                'path': filepath,
                'classes': classes,
                'functions': functions,
                'size': len(content)
            })
        except:
            pass
    
    # Analyze similarities
    if len(comparison['files']) >= 2:
        # Compare class/function overlap
        for i in range(len(comparison['files'])):
            for j in range(i + 1, len(comparison['files'])):
                file1 = comparison['files'][i]
                file2 = comparison['files'][j]
                
                classes1 = set(file1['classes'])
                classes2 = set(file2['classes'])
                common_classes = classes1 & classes2
                
                funcs1 = set(file1['functions'])
                funcs2 = set(file2['functions'])
                common_funcs = funcs1 & funcs2
                
                if common_classes or common_funcs:
                    comparison['similarities'].append({
                        'file1': file1['path'],
                        'file2': file2['path'],
                        'common_classes': list(common_classes),
                        'common_functions': list(common_funcs)
                    })
    
    return {
        'success': True,
        'comparison': comparison
    }
```

## Testing Plan

### Test 1: File Discovery
```bash
# Create test files
mkdir -p test_project/services
mkdir -p test_project/core
echo "class ChartGenerator: pass" > test_project/services/chart_generator.py
echo "class ChartGen: pass" > test_project/core/chart_gen.py

# Run discovery
python3 -c "
from pipeline.file_discovery import FileDiscovery
from pathlib import Path
import logging

logger = logging.getLogger()
discovery = FileDiscovery(Path('test_project'), logger)
similar = discovery.find_similar_files('services/chart_generator.py')
print(f'Found {len(similar)} similar files')
for file in similar:
    print(f'  - {file[&quot;path&quot;]} ({file[&quot;similarity&quot;]:.0%})')
"
```

### Test 2: Naming Conventions
```bash
# Create ARCHITECTURE.md
cat > test_project/ARCHITECTURE.md << 'EOF'
## Naming Conventions

### Directory Structure
- **services/**: Business logic services
  - Pattern: `services/*_service.py`
EOF

# Test validation
python3 -c "
from pipeline.naming_conventions import NamingConventionManager
from pathlib import Path
import logging

logger = logging.getLogger()
conventions = NamingConventionManager(Path('test_project'), logger)
result = conventions.validate_filename('services/chart_generator.py')
print(f'Valid: {result[&quot;valid&quot;]}')
print(f'Issues: {result[&quot;issues&quot;]}')
"
```

## Rollout Strategy

### Week 1: Foundation
- Deploy file discovery utilities
- Deploy naming convention manager
- Update coding phase with discovery
- Test with small projects

### Week 2: Refactoring
- Deploy conflict resolver
- Update refactoring phase
- Test conflict resolution
- Monitor for issues

### Week 3: Planning
- Update planning phase
- Deploy convention enforcement
- Test architecture updates
- Validate conventions

### Week 4: Integration
- Add all new tools
- Deploy tool handlers
- Full system testing
- Documentation updates

## Success Metrics

1. **Duplicate Prevention**
   - Measure: % of new files that are duplicates
   - Target: < 5% (down from current ~15%)

2. **Convention Compliance**
   - Measure: % of files following conventions
   - Target: > 90%

3. **Conflict Resolution**
   - Measure: Number of conflicting files
   - Target: < 10 per project

4. **AI Decision Quality**
   - Measure: % of correct file decisions
   - Target: > 85%

## Conclusion

This implementation plan provides a comprehensive, phased approach to adding multi-step file management to the autonomy pipeline. Each phase builds on the previous one, allowing for incremental testing and validation.

The key innovation is the **multi-step collaboration** with AI:
1. **Discovery** - Show AI what exists
2. **Decision** - Let AI choose the right action
3. **Execution** - Implement the decision
4. **Verification** - Confirm it worked

This transforms the pipeline from a reactive system into a proactive, intelligent file management system.