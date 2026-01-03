"""
QA Analysis Orchestrator.

Handles comprehensive analysis orchestration for the QA phase,
extracted from the QAPhase class to reduce complexity.
"""

from typing import Dict, List
import logging


class QAAnalysisOrchestrator:
    """
    Orchestrates comprehensive analysis for QA phase.
    
    Coordinates multiple analysis tools (complexity, dead code, integration gaps,
    conflicts) and aggregates their results into a unified issue list.
    """
    
    def __init__(
        self,
        complexity_analyzer,
        dead_code_detector,
        gap_finder,
        conflict_detector,
        architecture_config,
        logger: logging.Logger = None
    ):
        """
        Initialize QA analysis orchestrator.
        
        Args:
            complexity_analyzer: Tool for analyzing code complexity
            dead_code_detector: Tool for detecting dead/unused code
            gap_finder: Tool for finding integration gaps
            conflict_detector: Tool for detecting integration conflicts
            architecture_config: Architecture configuration for context
            logger: Optional logger instance
        """
        self.complexity_analyzer = complexity_analyzer
        self.dead_code_detector = dead_code_detector
        self.gap_finder = gap_finder
        self.conflict_detector = conflict_detector
        self.architecture_config = architecture_config
        self.logger = logger or logging.getLogger('QAAnalysisOrchestrator')
    
    def run_comprehensive_analysis(self, filepath: str) -> Dict:
        """
        Run comprehensive analysis on a file using native analysis tools.
        
        This is CORE QA functionality - not external tools.
        
        Args:
            filepath: Path to file to analyze
        
        Returns:
            Dict with analysis results and quality issues
        """
        issues = []
        
        # Use architecture config to check if this is a library module
        # Library modules are meant to be imported, not executed directly
        is_library_module = self.architecture_config.is_library_module(filepath)
        
        try:
            # 1. Complexity Analysis
            self.logger.info(f"  📊 Analyzing complexity...")
            complexity_result = self.complexity_analyzer.analyze(target=filepath)
            
            # Check for high complexity functions
            for func in complexity_result.results:
                if func.complexity >= 30:
                    issues.append({
                        'type': 'high_complexity',
                        'severity': 'high' if func.complexity >= 50 else 'medium',
                        'function': func.name,
                        'complexity': func.complexity,
                        'line': func.line,
                        'description': f"Function {func.name} has complexity {func.complexity} (threshold: 30)",
                        'recommendation': f"Refactor to reduce complexity. Estimated effort: {func.effort_days}"
                    })
            
            # 2. Dead Code Detection (skip for library modules)
            if not is_library_module:
                self.logger.info(f"  🔍 Detecting dead code...")
                dead_code_result = self.dead_code_detector.analyze(target=filepath)
                
                # Check for unused functions
                if dead_code_result.unused_functions:
                    for func_name, file, line in dead_code_result.unused_functions:
                        if file == filepath or filepath in file:
                            issues.append({
                                'type': 'dead_code',
                                'severity': 'medium',
                                'function': func_name,
                                'line': line,
                                'description': f"Function {func_name} is defined but never called",
                                'recommendation': "Remove if truly unused, or add usage"
                            })
            else:
                self.logger.info(f"  ⏭️  Skipping dead code detection for library module")
            
            # Check for unused methods
            if dead_code_result.unused_methods:
                for method_key, file, line in dead_code_result.unused_methods:
                    if file == filepath or filepath in file:
                        issues.append({
                            'type': 'dead_code',
                            'severity': 'low',
                            'method': method_key,
                            'line': line,
                            'description': f"Method {method_key} is defined but never called",
                            'recommendation': "Verify if method is needed"
                        })
            
            # 3. Integration Gap Analysis
            self.logger.info(f"  🔗 Checking integration gaps...")
            gap_result = self.gap_finder.analyze(target=filepath)
            
            # Check for unused classes
            if gap_result.unused_classes:
                for class_name, file, line in gap_result.unused_classes:
                    if file == filepath or filepath in file:
                        issues.append({
                            'type': 'integration_gap',
                            'severity': 'medium',
                            'class': class_name,
                            'line': line,
                            'description': f"Class {class_name} is defined but never instantiated",
                            'recommendation': "Complete integration or remove if not needed"
                        })
            
            # 4. Integration Conflict Detection (project-wide)
            self.logger.info(f"  🔀 Checking for integration conflicts...")
            conflict_result = self.conflict_detector.analyze(target=filepath)
            
            # Add conflicts as issues
            for conflict in conflict_result.conflicts:
                # Only include if this file is involved
                if filepath in conflict.files or any(filepath in f for f in conflict.files):
                    issues.append({
                        'type': 'integration_conflict',
                        'severity': conflict.severity,
                        'conflict_type': conflict.conflict_type,
                        'files': conflict.files,
                        'description': conflict.description,
                        'recommendation': conflict.recommendation,
                        'details': conflict.details
                    })
            
            # 5. Dead Code Review Issues (enhanced with context)
            if dead_code_result.review_issues:
                self.logger.info(f"  📋 Processing dead code review issues...")
                for issue in dead_code_result.review_issues:
                    if issue.file == filepath or filepath in issue.file:
                        issues.append({
                            'type': 'dead_code_review',
                            'severity': issue.severity,
                            'name': issue.name,
                            'line': issue.line,
                            'issue_type': issue.issue_type,
                            'description': f"{issue.reason}: {issue.context}",
                            'recommendation': issue.context,
                            'similar_code': issue.similar_code
                        })
            
            # Log summary
            if issues:
                self.logger.warning(f"  ⚠️  Found {len(issues)} quality issues via analysis")
                complexity_issues = [i for i in issues if i['type'] == 'high_complexity']
                dead_code_issues = [i for i in issues if i['type'] == 'dead_code']
                gap_issues = [i for i in issues if i['type'] == 'integration_gap']
                conflict_issues = [i for i in issues if i['type'] == 'integration_conflict']
                review_issues = [i for i in issues if i['type'] == 'dead_code_review']
                
                if complexity_issues:
                    self.logger.warning(f"    - {len(complexity_issues)} high complexity functions")
                if dead_code_issues:
                    self.logger.warning(f"    - {len(dead_code_issues)} dead code instances")
                if gap_issues:
                    self.logger.warning(f"    - {len(gap_issues)} integration gaps")
                if conflict_issues:
                    self.logger.warning(f"    - {len(conflict_issues)} integration conflicts")
                if review_issues:
                    self.logger.warning(f"    - {len(review_issues)} items marked for review")
            else:
                self.logger.info(f"  ✅ No quality issues found via analysis")
            
            return {
                'success': True,
                'issues': issues,
                'complexity': complexity_result.to_dict(),
                'dead_code': dead_code_result.to_dict(),
                'gaps': gap_result.to_dict(),
                'conflicts': conflict_result.to_dict()
            }
            
        except Exception as e:
            self.logger.error(f"  ❌ Analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'issues': []
            }