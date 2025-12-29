"""
Analysis Tools Integration

Provides integration layer for scripts/analysis/ tools.
Supports both module import (fast) and executable fallback (compatible).
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import logging

from ..logging_setup import get_logger


class AnalysisToolsIntegration:
    """
    Integration layer for analysis tools.
    
    Provides access to all scripts/analysis/ tools with:
    - Module import (preferred, fast)
    - Executable fallback (compatible)
    - Structured result parsing
    - Error handling
    
    Example:
        tools = AnalysisToolsIntegration('/project')
        
        # Analyze complexity
        result = tools.analyze_complexity()
        
        # Detect dead code
        dead_code = tools.detect_dead_code()
        
        # Generate call graph
        call_graph = tools.generate_call_graph()
    """
    
    def __init__(self, project_dir: str, logger: Optional[logging.Logger] = None):
        """
        Initialize analysis tools integration.
        
        Args:
            project_dir: Project root directory
            logger: Optional logger instance
        """
        self.project_dir = Path(project_dir)
        self.logger = logger or get_logger()
        
        # Get pipeline root (autonomy/)
        pipeline_root = Path(__file__).parent.parent.parent
        self.scripts_dir = pipeline_root / 'scripts'
        self.analysis_dir = self.scripts_dir / 'analysis'
        
        # Add scripts to path for module imports
        if str(self.scripts_dir) not in sys.path:
            sys.path.insert(0, str(self.scripts_dir))
        
        # Try to import analysis modules
        self._import_modules()
        
        self.logger.info(f"AnalysisToolsIntegration initialized for {project_dir}")
    
    def _import_modules(self):
        """Try to import analysis modules."""
        self.modules = {}
        
        try:
            # Try importing core analyzer
            from analysis.core.analyzer import DeepCodeAnalyzer
            self.modules['deep_analyzer'] = DeepCodeAnalyzer
            self.logger.debug("Imported DeepCodeAnalyzer module")
        except ImportError as e:
            self.logger.warning(f"Could not import DeepCodeAnalyzer: {e}")
        
        try:
            # Try importing complexity analyzer
            from analysis.core.complexity import ComplexityAnalyzer
            self.modules['complexity'] = ComplexityAnalyzer
            self.logger.debug("Imported ComplexityAnalyzer module")
        except ImportError as e:
            self.logger.warning(f"Could not import ComplexityAnalyzer: {e}")
    
    def _run_script(self, script_name: str, *args, **kwargs) -> Dict[str, Any]:
        """
        Run analysis script as executable (fallback).
        
        Args:
            script_name: Name of script (without .py)
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Result dict with success, output, error
        """
        script_path = self.analysis_dir / f"{script_name}.py"
        
        if not script_path.exists():
            return {
                'success': False,
                'error': f'Script not found: {script_path}',
                'error_type': 'script_not_found'
            }
        
        # Build command
        cmd = [sys.executable, str(script_path)]
        cmd.extend(str(arg) for arg in args)
        
        # Add keyword arguments as flags
        for key, value in kwargs.items():
            if isinstance(value, bool):
                if value:
                    cmd.append(f'--{key}')
            else:
                cmd.append(f'--{key}')
                cmd.append(str(value))
        
        try:
            self.logger.debug(f"Running script: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_dir),
                timeout=300  # 5 minute timeout
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None,
                'exit_code': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Script execution timed out (5 minutes)',
                'error_type': 'timeout'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Script execution failed: {e}',
                'error_type': 'execution_error'
            }
    
    def analyze_complexity(self, target: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze code complexity.
        
        Args:
            target: Optional specific file/directory (default: project_dir)
        
        Returns:
            Complexity analysis results
        """
        target = target or str(self.project_dir)
        
        self.logger.info(f"Analyzing complexity: {target}")
        
        # Try module import first
        if 'complexity' in self.modules:
            try:
                analyzer = self.modules['complexity'](target)
                results = analyzer.analyze()
                return {
                    'success': True,
                    'results': results,
                    'method': 'module_import'
                }
            except Exception as e:
                self.logger.warning(f"Module import failed, falling back to executable: {e}")
        
        # Fallback to executable
        result = self._run_script('COMPLEXITY_ANALYZER', target)
        
        if result['success']:
            # Parse output
            return {
                'success': True,
                'output': result['output'],
                'method': 'executable',
                'report_file': 'COMPLEXITY_REPORT.txt'
            }
        
        return result
    
    def detect_dead_code(self, target: Optional[str] = None) -> Dict[str, Any]:
        """
        Detect dead code (unused functions, methods, imports).
        
        Args:
            target: Optional specific file/directory (default: project_dir)
        
        Returns:
            Dead code detection results
        """
        target = target or str(self.project_dir)
        
        self.logger.info(f"Detecting dead code: {target}")
        
        # Run executable (no module version yet)
        result = self._run_script('DEAD_CODE_DETECTOR', target)
        
        if result['success']:
            return {
                'success': True,
                'output': result['output'],
                'method': 'executable',
                'report_file': 'DEAD_CODE_REPORT.txt'
            }
        
        return result
    
    def find_integration_gaps(self, target: Optional[str] = None) -> Dict[str, Any]:
        """
        Find integration gaps and incomplete features.
        
        Args:
            target: Optional specific file/directory (default: project_dir)
        
        Returns:
            Integration gap analysis results
        """
        target = target or str(self.project_dir)
        
        self.logger.info(f"Finding integration gaps: {target}")
        
        # Run executable
        result = self._run_script('INTEGRATION_GAP_FINDER', target)
        
        if result['success']:
            return {
                'success': True,
                'output': result['output'],
                'method': 'executable',
                'report_file': 'INTEGRATION_GAP_REPORT.txt'
            }
        
        return result
    
    def generate_call_graph(self, target: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate call graph.
        
        Args:
            target: Optional specific file/directory (default: project_dir)
        
        Returns:
            Call graph generation results
        """
        target = target or str(self.project_dir)
        
        self.logger.info(f"Generating call graph: {target}")
        
        # Run executable
        result = self._run_script('CALL_GRAPH_GENERATOR', target)
        
        if result['success']:
            return {
                'success': True,
                'output': result['output'],
                'method': 'executable',
                'report_file': 'CALL_GRAPH_REPORT.txt',
                'graph_file': 'call_graph.dot'
            }
        
        return result
    
    def analyze_enhanced(self, target: Optional[str] = None) -> Dict[str, Any]:
        """
        Run enhanced depth-61 analysis.
        
        Args:
            target: Optional specific file/directory (default: project_dir)
        
        Returns:
            Enhanced analysis results
        """
        target = target or str(self.project_dir)
        
        self.logger.info(f"Running enhanced analysis: {target}")
        
        # Run executable
        result = self._run_script('ENHANCED_DEPTH_61_ANALYZER', target)
        
        if result['success']:
            return {
                'success': True,
                'output': result['output'],
                'method': 'executable',
                'report_file': 'analysis_enhanced.txt'
            }
        
        return result
    
    def analyze_improved(self, target: Optional[str] = None) -> Dict[str, Any]:
        """
        Run improved depth-61 analysis (pattern-aware).
        
        Args:
            target: Optional specific file/directory (default: project_dir)
        
        Returns:
            Improved analysis results
        """
        target = target or str(self.project_dir)
        
        self.logger.info(f"Running improved analysis: {target}")
        
        # Run executable
        result = self._run_script('IMPROVED_DEPTH_61_ANALYZER', target)
        
        if result['success']:
            return {
                'success': True,
                'output': result['output'],
                'method': 'executable',
                'report_file': 'improved_analysis.txt'
            }
        
        return result
    
    def deep_analyze(self, target: Optional[str] = None, 
                    checks: Optional[List[str]] = None,
                    output_format: str = 'text',
                    recursive: bool = True) -> Dict[str, Any]:
        """
        Run comprehensive deep analysis (unified interface).
        
        Args:
            target: Optional specific file/directory (default: project_dir)
            checks: Optional list of checks to run (default: all)
            output_format: Output format ('text', 'json', 'markdown')
            recursive: Analyze recursively
        
        Returns:
            Deep analysis results
        """
        target = target or str(self.project_dir)
        
        self.logger.info(f"Running deep analysis: {target}")
        
        # Build arguments
        kwargs = {
            'format': output_format,
        }
        
        if recursive:
            kwargs['recursive'] = True
        
        if checks:
            for check in checks:
                kwargs[f'check'] = check
        
        # Run executable
        result = self._run_script('deep_analyze', target, **kwargs)
        
        if result['success']:
            # Try to parse JSON output
            if output_format == 'json':
                try:
                    parsed = json.loads(result['output'])
                    return {
                        'success': True,
                        'results': parsed,
                        'method': 'executable',
                        'format': 'json'
                    }
                except json.JSONDecodeError:
                    pass
            
            return {
                'success': True,
                'output': result['output'],
                'method': 'executable',
                'format': output_format
            }
        
        return result
    
    def get_available_tools(self) -> List[str]:
        """
        Get list of available analysis tools.
        
        Returns:
            List of tool names
        """
        tools = [
            'analyze_complexity',
            'detect_dead_code',
            'find_integration_gaps',
            'generate_call_graph',
            'analyze_enhanced',
            'analyze_improved',
            'deep_analyze',
        ]
        return tools
    
    def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """
        Get information about a specific tool.
        
        Args:
            tool_name: Name of the tool
        
        Returns:
            Tool information dict
        """
        tool_info = {
            'analyze_complexity': {
                'name': 'Complexity Analyzer',
                'description': 'Analyze code complexity and identify refactoring priorities',
                'output': 'COMPLEXITY_REPORT.txt',
                'runtime': '1-2 minutes',
                'use_cases': [
                    'Planning refactoring efforts',
                    'Identifying technical debt',
                    'Prioritizing code improvements',
                ]
            },
            'detect_dead_code': {
                'name': 'Dead Code Detector',
                'description': 'Find unused functions, methods, and imports',
                'output': 'DEAD_CODE_REPORT.txt',
                'runtime': '1-2 minutes',
                'use_cases': [
                    'Code cleanup',
                    'Before refactoring',
                    'Reducing codebase size',
                ]
            },
            'find_integration_gaps': {
                'name': 'Integration Gap Finder',
                'description': 'Identify incomplete features and architectural gaps',
                'output': 'INTEGRATION_GAP_REPORT.txt',
                'runtime': '1-2 minutes',
                'use_cases': [
                    'Finding incomplete features',
                    'Architectural analysis',
                    'Dependency cleanup',
                ]
            },
            'generate_call_graph': {
                'name': 'Call Graph Generator',
                'description': 'Generate comprehensive call graphs',
                'output': 'CALL_GRAPH_REPORT.txt, call_graph.dot',
                'runtime': '2-3 minutes',
                'use_cases': [
                    'Understanding code flow',
                    'Visualizing dependencies',
                    'Planning refactoring',
                ]
            },
            'analyze_enhanced': {
                'name': 'Enhanced Depth-61 Analyzer',
                'description': 'Full AST analysis with variable tracing',
                'output': 'analysis_enhanced.txt',
                'runtime': '2-3 minutes',
                'use_cases': [
                    'Initial codebase analysis',
                    'Understanding structure',
                    'Dependency mapping',
                ]
            },
            'analyze_improved': {
                'name': 'Improved Depth-61 Analyzer',
                'description': 'Pattern-aware analysis with false positive reduction',
                'output': 'improved_analysis.txt',
                'runtime': '2-3 minutes',
                'use_cases': [
                    'Verifying findings',
                    'Pattern detection',
                    'Reducing false positives',
                ]
            },
            'deep_analyze': {
                'name': 'Deep Analyzer (Unified)',
                'description': 'Comprehensive analysis with multiple output formats',
                'output': 'Configurable',
                'runtime': 'Varies',
                'use_cases': [
                    'Comprehensive analysis',
                    'Report generation',
                    'CI/CD integration',
                ]
            },
        }
        
        return tool_info.get(tool_name, {
            'name': tool_name,
            'description': 'Unknown tool',
        })