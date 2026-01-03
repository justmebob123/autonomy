"""
Analysis Orchestrator

Orchestrates analysis tool execution and creates refactoring tasks from results.
Extracted from RefactoringPhase._auto_create_tasks_from_analysis.
"""

from typing import List, Dict, Any
from pathlib import Path
import logging

from pipeline.state.manager import PipelineState
from pipeline.state.refactoring_task import (
    RefactoringTask, RefactoringIssueType, RefactoringPriority, RefactoringApproach
)
from pipeline.phases.base import PhaseResult


class AnalysisOrchestrator:
    """
    Orchestrates analysis and task creation.
    
    Handles:
    - Duplicate detection results
    - Complexity analysis results
    - Dead code detection results
    - Architecture validation results
    - Integration gap detection results
    - Circular import detection results
    - Coding vs refactoring issue detection
    """
    
    def __init__(self, project_dir: Path, logger: logging.Logger):
        """
        Initialize orchestrator.
        
        Args:
            project_dir: Project directory path
            logger: Logger instance
        """
        self.project_dir = Path(project_dir)
        self.logger = logger
    
    def create_tasks_from_analysis(
        self, 
        state: PipelineState, 
        analysis_result: PhaseResult,
        tool_results: List[Dict[str, Any]] = None
    ) -> int:
        """
        Auto-create refactoring tasks from analysis results.
        
        CRITICAL INTELLIGENCE: Detect if issues are actually CODING problems (syntax errors,
        missing imports, missing code) rather than refactoring problems. If so, return
        -1 to signal return to coding phase.
        
        Args:
            state: Pipeline state
            analysis_result: Result from comprehensive analysis
            tool_results: List of tool execution results
            
        Returns:
            Number of tasks created (or -1 if should return to coding phase)
        """
        tasks_created = 0
        
        # Get the refactoring manager
        if not hasattr(state, 'refactoring_manager') or not state.refactoring_manager:
            return 0
        
        manager = state.refactoring_manager
        
        # Track coding issues
        coding_issues_count = 0
        syntax_errors = 0
        import_errors = 0
        
        # Process tool results if provided
        if tool_results:
            for tool_result in tool_results:
                tool_name = tool_result.get('tool', '')
                
                # Count coding-related issues
                if tool_name == 'validate_syntax':
                    result_data = tool_result.get('result', {})
                    errors = result_data.get('errors', [])
                    syntax_errors = len(errors)
                    coding_issues_count += syntax_errors
                
                elif tool_name == 'validate_all_imports':
                    result_data = tool_result.get('result', {})
                    errors = result_data.get('errors', [])
                    import_errors = len(errors)
                    coding_issues_count += import_errors
                
                # Handle duplicate detection
                elif tool_name == 'detect_duplicate_implementations':
                    tasks_created += self._create_duplicate_tasks(manager, tool_result)
                
                # Handle complexity analysis
                elif tool_name == 'analyze_complexity':
                    tasks_created += self._create_complexity_tasks(manager, tool_result)
                
                # Handle dead code detection
                elif tool_name == 'detect_dead_code':
                    tasks_created += self._create_dead_code_tasks(manager, tool_result)
                
                # Handle architecture validation
                elif tool_name == 'validate_architecture':
                    tasks_created += self._create_architecture_tasks(manager, tool_result)
                
                # Handle integration gaps
                elif tool_name == 'detect_integration_gaps':
                    tasks_created += self._create_integration_tasks(manager, tool_result)
                
                # Handle circular imports
                elif tool_name == 'detect_circular_imports':
                    tasks_created += self._create_circular_import_tasks(manager, tool_result)
        
        # CRITICAL INTELLIGENCE: Check if should return to coding phase
        if coding_issues_count > 0 and tasks_created > 0:
            coding_ratio = coding_issues_count / tasks_created
            if coding_ratio > 0.5:
                self.logger.warning(
                    f"  🚨 INTELLIGENCE: {coding_issues_count}/{tasks_created} issues are CODING problems "
                    f"(syntax: {syntax_errors}, imports: {import_errors})"
                )
                self.logger.warning("  🚨 These require CODING phase, not refactoring!")
                self.logger.info("  ➡️  Returning to CODING phase to fix missing code...")
                return -1  # Signal to return to coding phase
        
        return tasks_created
    
    def _create_duplicate_tasks(self, manager, tool_result: Dict[str, Any]) -> int:
        """Create tasks from duplicate detection results."""
        tasks_created = 0
        result_data = tool_result.get('result', {})
        duplicates = result_data.get('duplicate_sets', [])
        
        if not duplicates:
            return 0
        
        self.logger.info(f"  🔍 Found {len(duplicates)} duplicate sets, creating tasks...")
        
        for dup in duplicates:
            files = dup.get('files', [])
            similarity = dup.get('similarity', 0)
            
            if len(files) < 2:
                continue
            
            # Extract short paths for title
            short_paths = [str(Path(f).parent / Path(f).name) for f in files[:2]]
            title = f"Merge duplicates: {short_paths[0]} ↔ {short_paths[1]}"
            
            # Check resolution history
            if manager.was_recently_resolved(
                issue_type='duplicate',
                target_files=files
            ):
                continue
            
            # Check if task already exists
            if manager.task_exists(
                issue_type=RefactoringIssueType.DUPLICATE,
                target_files=files
            ):
                continue
            
            # Create task
            task = manager.create_task(
                issue_type=RefactoringIssueType.DUPLICATE,
                title=title,
                description=f"Files {files[0]} and {files[1]} are {similarity:.0%} similar",
                target_files=files,
                priority=RefactoringPriority.MEDIUM,
                fix_approach=RefactoringApproach.AUTONOMOUS,
                estimated_effort=20,
                analysis_data={
                    'files': files,
                    'similarity': similarity,
                    'action': 'merge_file_implementations'
                }
            )
            tasks_created += 1
        
        return tasks_created
    
    def _create_complexity_tasks(self, manager, tool_result: Dict[str, Any]) -> int:
        """Create tasks from complexity analysis results."""
        tasks_created = 0
        result_data = tool_result.get('result', {})
        critical_functions = result_data.get('critical_functions', [])
        
        for func_info in critical_functions[:5]:  # Limit to top 5
            task = manager.create_task(
                issue_type=RefactoringIssueType.COMPLEXITY,
                title=f"Reduce complexity: {func_info.get('name', 'unknown')}",
                description=f"Function has complexity {func_info.get('complexity', 0)}",
                target_files=[func_info.get('file', 'unknown')],
                priority=RefactoringPriority.LOW,
                fix_approach=RefactoringApproach.AUTONOMOUS,
                estimated_effort=30,
                analysis_data=func_info
            )
            tasks_created += 1
        
        return tasks_created
    
    def _create_dead_code_tasks(self, manager, tool_result: Dict[str, Any]) -> int:
        """Create tasks from dead code detection results."""
        tasks_created = 0
        result_data = tool_result.get('result', {})
        dead_code = result_data.get('unused_items', [])
        
        for item in dead_code[:10]:  # Limit to top 10
            task = manager.create_task(
                issue_type=RefactoringIssueType.DEAD_CODE,
                title=f"Review dead code: {item.get('name', 'unknown')}",
                description=f"Unused {item.get('type', 'code')} in {item.get('file', 'unknown')}",
                target_files=[item.get('file', 'unknown')],
                priority=RefactoringPriority.LOW,
                fix_approach=RefactoringApproach.REPORT,
                estimated_effort=15,
                analysis_data=item
            )
            tasks_created += 1
        
        return tasks_created
    
    def _create_architecture_tasks(self, manager, tool_result: Dict[str, Any]) -> int:
        """Create tasks from architecture validation results."""
        tasks_created = 0
        result_data = tool_result.get('result', {})
        violations = result_data.get('violations', [])
        
        for violation in violations:
            task = manager.create_task(
                issue_type=RefactoringIssueType.ARCHITECTURE,
                title=f"Fix architecture: {violation.get('type', 'unknown')}",
                description=violation.get('description', 'Architecture violation'),
                target_files=violation.get('files', []),
                priority=RefactoringPriority.MEDIUM,
                fix_approach=RefactoringApproach.AUTONOMOUS,
                estimated_effort=25,
                analysis_data=violation
            )
            tasks_created += 1
        
        return tasks_created
    
    def _create_integration_tasks(self, manager, tool_result: Dict[str, Any]) -> int:
        """Create tasks from integration gap detection results."""
        tasks_created = 0
        result_data = tool_result.get('result', {})
        
        # Handle unused classes
        unused_classes = result_data.get('unused_classes', [])
        for cls_info in unused_classes:
            task = manager.create_task(
                issue_type=RefactoringIssueType.INTEGRATION,
                title=f"Review unused class: {cls_info.get('class', 'unknown')}",
                description=f"Class never instantiated in {cls_info.get('file', 'unknown')}",
                target_files=[cls_info.get('file', 'unknown')],
                priority=RefactoringPriority.LOW,
                fix_approach=RefactoringApproach.REPORT,
                estimated_effort=20,
                analysis_data=cls_info
            )
            tasks_created += 1
        
        # Handle classes with unused methods
        classes_with_unused = result_data.get('classes_with_unused_methods', [])
        for cls_info in classes_with_unused:
            unused_methods = cls_info.get('unused_methods', [])
            if unused_methods:
                task = manager.create_task(
                    issue_type=RefactoringIssueType.INTEGRATION,
                    title=f"Review unused methods in {cls_info.get('class', 'unknown')}",
                    description=f"{len(unused_methods)} unused methods",
                    target_files=[cls_info.get('file', 'unknown')],
                    priority=RefactoringPriority.LOW,
                    fix_approach=RefactoringApproach.REPORT,
                    estimated_effort=15,
                    analysis_data=cls_info
                )
                tasks_created += 1
        
        return tasks_created
    
    def _create_circular_import_tasks(self, manager, tool_result: Dict[str, Any]) -> int:
        """Create tasks from circular import detection results."""
        tasks_created = 0
        result_data = tool_result.get('result', {})
        cycles = result_data.get('cycles', [])
        
        for cycle in cycles:
            cycle_path = cycle.get('path', [])
            cycle_files = cycle.get('files', [])
            cycle_desc = cycle.get('description', 'Circular import detected')
            
            task = manager.create_task(
                issue_type=RefactoringIssueType.ARCHITECTURE,
                title=f"Fix circular import: {len(cycle_path)} files",
                description=cycle_desc,
                target_files=cycle_files,
                priority=RefactoringPriority.HIGH,
                fix_approach=RefactoringApproach.AUTONOMOUS,
                estimated_effort=45,
                analysis_data={
                    'type': 'circular_import',
                    'cycle': cycle_path,
                    'files': cycle_files,
                    'description': cycle_desc,
                    'action': 'move_file or restructure_directory'
                }
            )
            tasks_created += 1
        
        return tasks_created