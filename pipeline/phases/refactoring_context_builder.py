"""
Context builder for refactoring phase decisions.

This module builds comprehensive context for AI to make informed refactoring decisions,
including strategic documents, analysis reports, code context, and project state.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class RefactoringContext:
    """Complete context for a refactoring decision."""
    
    # Strategic documents
    master_plan: str
    architecture: str
    roadmap: Optional[str]
    primary_objectives: Optional[str]
    secondary_objectives: Optional[str]
    tertiary_objectives: Optional[str]
    
    # Analysis reports
    dead_code_report: str
    complexity_report: str
    antipattern_report: str
    integration_gaps: str
    bug_report: str
    call_graph: str
    
    # Code context
    target_file_content: str
    related_files: Dict[str, str]
    test_files: Dict[str, str]
    
    # Project state
    current_phase: str
    completion_percentage: float
    recent_changes: List[str]
    pending_tasks: List[str]
    
    # Issue details
    issue_type: str
    issue_description: str
    affected_code: str


class RefactoringContextBuilder:
    """
    Builds comprehensive context for refactoring decisions.
    
    This ensures AI has all necessary information to make informed decisions
    about whether to remove, integrate, refactor, or preserve code.
    """
    
    def __init__(self, project_dir: Path, logger):
        self.project_dir = project_dir
        self.logger = logger
    
    def build_context(self, 
                     issue_type: str,
                     issue_description: str,
                     target_file: str,
                     affected_code: str,
                     project_state: Dict) -> RefactoringContext:
        """
        Build complete context for a refactoring decision.
        
        Args:
            issue_type: Type of issue (dead_code, complexity, etc.)
            issue_description: Description of the issue
            target_file: File containing the issue
            affected_code: The specific code in question
            project_state: Current project state information
        
        Returns:
            RefactoringContext with all necessary information
        """
        self.logger.debug(f"  📦 Building refactoring context for {target_file}")
        
        # Load strategic documents
        master_plan = self._load_document('MASTER_PLAN.md')
        architecture = self._load_document('ARCHITECTURE.md')
        roadmap = self._load_document('ROADMAP.md', optional=True)
        primary_objectives = self._load_document('PRIMARY_OBJECTIVES.md', optional=True)
        secondary_objectives = self._load_document('SECONDARY_OBJECTIVES.md', optional=True)
        tertiary_objectives = self._load_document('TERTIARY_OBJECTIVES.md', optional=True)
        
        # Load analysis reports
        dead_code_report = self._load_document('DEAD_CODE_REPORT.txt', optional=True)
        complexity_report = self._load_document('COMPLEXITY_REPORT.txt', optional=True)
        antipattern_report = self._load_document('ANTIPATTERN_REPORT.txt', optional=True)
        integration_gaps = self._load_document('INTEGRATION_GAP_REPORT.txt', optional=True)
        bug_report = self._load_document('BUG_DETECTION_REPORT.txt', optional=True)
        call_graph = self._load_document('CALL_GRAPH_REPORT.txt', optional=True)
        
        # Load code context
        target_file_content = self._load_file_content(target_file)
        related_files = self._find_related_files(target_file)
        test_files = self._find_test_files(target_file)
        
        # Extract project state
        current_phase = project_state.get('phase', 'unknown')
        completion = project_state.get('completion', 0.0)
        recent_changes = project_state.get('recent_changes', [])
        pending_tasks = project_state.get('pending_tasks', [])
        
        return RefactoringContext(
            master_plan=master_plan,
            architecture=architecture,
            roadmap=roadmap,
            primary_objectives=primary_objectives,
            secondary_objectives=secondary_objectives,
            tertiary_objectives=tertiary_objectives,
            dead_code_report=dead_code_report or "No report available",
            complexity_report=complexity_report or "No report available",
            antipattern_report=antipattern_report or "No report available",
            integration_gaps=integration_gaps or "No report available",
            bug_report=bug_report or "No report available",
            call_graph=call_graph or "No report available",
            target_file_content=target_file_content,
            related_files=related_files,
            test_files=test_files,
            current_phase=current_phase,
            completion_percentage=completion,
            recent_changes=recent_changes,
            pending_tasks=pending_tasks,
            issue_type=issue_type,
            issue_description=issue_description,
            affected_code=affected_code
        )
    
    def format_context_for_prompt(self, context: RefactoringContext) -> str:
        """
        Format context into a comprehensive prompt for AI.
        
        This creates a structured prompt that guides AI through the decision process
        with all necessary information.
        """
        prompt = f"""# Refactoring Decision Required

## Project Context
- **Current Phase**: {context.current_phase}
- **Completion**: {context.completion_percentage:.1f}%
- **Recent Changes**: {len(context.recent_changes)} files modified recently
- **Pending Tasks**: {len(context.pending_tasks)} tasks in queue

## Issue Details
- **Type**: {context.issue_type}
- **Description**: {context.issue_description}

## Affected Code
```python
{context.affected_code}
```

## Strategic Documents

### MASTER_PLAN.md (Project Vision & Roadmap)
```
{self._truncate(context.master_plan, 3000)}
```

### ARCHITECTURE.md (Design Patterns & Conventions)
```
{self._truncate(context.architecture, 2000)}
```

{f"### ROADMAP.md (Timeline & Priorities)```{self._truncate(context.roadmap, 1000)}```" if context.roadmap else ""}

## Objectives Hierarchy

{f"### PRIMARY_OBJECTIVES.md (Core Features)```{self._truncate(context.primary_objectives, 1000)}```" if context.primary_objectives else ""}

{f"### SECONDARY_OBJECTIVES.md (Architectural Changes & Quality)```{self._truncate(context.secondary_objectives, 1500)}```" if context.secondary_objectives else ""}

{f"### TERTIARY_OBJECTIVES.md (Specific Implementation Steps)```{self._truncate(context.tertiary_objectives, 2000)}```" if context.tertiary_objectives else ""}

## Analysis Reports

### Dead Code Analysis
```
{self._truncate(context.dead_code_report, 1500)}
```

### Complexity Analysis
```
{self._truncate(context.complexity_report, 1500)}
```

### Anti-Pattern Detection
```
{self._truncate(context.antipattern_report, 1500)}
```

### Integration Gaps
```
{self._truncate(context.integration_gaps, 1500)}
```

### Bug Detection
```
{self._truncate(context.bug_report, 1500)}
```

### Call Graph (Dependencies)
```
{self._truncate(context.call_graph, 1000)}
```

## Code Context

### Target File: {context.target_file_content[:100] if context.target_file_content else "N/A"}
```python
{self._truncate(context.target_file_content, 2000)}
```

### Related Files ({len(context.related_files)} files)
{self._format_related_files(context.related_files)}

### Test Coverage ({len(context.test_files)} test files)
{self._format_test_files(context.test_files)}

## Decision Framework

Based on ALL the context above, determine the appropriate action:

### Option A: AUTO-FIX (Simple, clear-cut cases)
Use when:
- Dead imports with no references in MASTER_PLAN
- Obvious bugs with clear fixes
- Exact duplicate code
- Standard formatting issues

### Option B: CREATE INTEGRATION TASK (Needs connection)
Use when:
- Code is mentioned in MASTER_PLAN but not integrated
- Useful functionality not yet connected
- Infrastructure ready but features not using it
- Helper functions that should be leveraged

### Option C: CREATE REFACTORING TASK (Needs improvement)
Use when:
- Good concept but poor implementation
- Overlapping with other code (needs consolidation)
- Violates ARCHITECTURE patterns
- Correct functionality but wrong location

### Option D: CREATE DEVELOPER REPORT (Complex decision)
Use when:
- Multiple valid approaches exist
- Architectural implications unclear
- Requires domain knowledge
- Trade-offs need human judgment

### Option E: PRESERVE WITH DOCUMENTATION (Future feature)
Use when:
- Explicitly mentioned in MASTER_PLAN roadmap
- Part of "Phase 2", "Phase 3", etc.
- Preparatory code for future capabilities
- Well-structured and ready for future use

## Your Task

1. **Analyze the issue** against MASTER_PLAN and ARCHITECTURE
2. **Check relationships** using call graph and related files
3. **Consider project phase** - early stage means more integration opportunities
4. **Choose ONE action** (A, B, C, D, or E)
5. **Provide clear reasoning** based on the context
6. **Specify implementation** steps if applicable

Remember: In early development ({context.completion_percentage:.1f}% complete), 
code may appear unused because features aren't fully integrated yet. Consider 
whether code should be INTEGRATED rather than REMOVED.
"""
        return prompt
    
    def _load_document(self, filename: str, optional: bool = False) -> Optional[str]:
        """Load a document from project directory."""
        filepath = self.project_dir / filename
        if not filepath.exists():
            if optional:
                return None
            return f"Document {filename} not found"
        
        try:
            return filepath.read_text()
        except Exception as e:
            return f"Error loading {filename}: {e}"
    
    def _load_file_content(self, filepath: str) -> str:
        """Load content of a specific file."""
        full_path = self.project_dir / filepath
        if not full_path.exists():
            return f"File {filepath} not found"
        
        try:
            return full_path.read_text()
        except Exception as e:
            return f"Error loading {filepath}: {e}"
    
    def _find_related_files(self, target_file: str) -> Dict[str, str]:
        """Find files that import or are imported by target file."""
        related = {}
        
        # Simple heuristic: files in same directory
        target_path = Path(target_file)
        if target_path.parent != Path('.'):
            directory = self.project_dir / target_path.parent
            if directory.exists():
                for file in directory.glob('*.py'):
                    if file.name != target_path.name:
                        try:
                            content = file.read_text()
                            # Only include first 500 chars as preview
                            related[str(file.relative_to(self.project_dir))] = content[:500]
                        except:
                            pass
        
        return related
    
    def _find_test_files(self, target_file: str) -> Dict[str, str]:
        """Find test files related to target file."""
        tests = {}
        
        # Look for test files
        test_patterns = ['test_*.py', '*_test.py']
        for pattern in test_patterns:
            for test_file in self.project_dir.rglob(pattern):
                try:
                    content = test_file.read_text()
                    # Check if it references target file
                    if Path(target_file).stem in content:
                        tests[str(test_file.relative_to(self.project_dir))] = content[:500]
                except:
                    pass
        
        return tests
    
    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max length with ellipsis."""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "\n... (truncated)"
    
    def _format_related_files(self, related_files: Dict[str, str]) -> str:
        """Format related files for display."""
        if not related_files:
            return "No related files found"
        
        output = []
        for filepath, content in list(related_files.items())[:5]:  # Limit to 5
            output.append(f"#### {filepath}")
            output.append(f"```python\n{content}\n```\n")
        
        if len(related_files) > 5:
            output.append(f"... and {len(related_files) - 5} more files")
        
        return "\n".join(output)
    
    def _format_test_files(self, test_files: Dict[str, str]) -> str:
        """Format test files for display."""
        if not test_files:
            return "No test files found"
        
        output = []
        for filepath, content in list(test_files.items())[:3]:  # Limit to 3
            output.append(f"#### {filepath}")
            output.append(f"```python\n{content}\n```\n")
        
        if len(test_files) > 3:
            output.append(f"... and {len(test_files) - 3} more test files")
        
        return "\n".join(output)