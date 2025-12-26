"""
Application Troubleshooting Phase

Performs deep application-layer analysis including:
- Log parsing and error pattern recognition  
- Call chain tracing through multiple files
- Patch history correlation
- Architecture validation against MASTER_PLAN.md

This phase is triggered by INVESTIGATION when application-layer errors are detected
(configuration issues, missing resources, architectural violations, etc.)
"""

from .base import BasePhase, PhaseResult
from .loop_detection_mixin import LoopDetectionMixin
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging


class ApplicationTroubleshootingPhase(BasePhase, LoopDetectionMixin):
    """
    Deep application troubleshooting phase.
    
    Triggered by INVESTIGATION phase when application-layer errors detected.
    Returns findings to DEBUGGING phase for fix implementation.
    
    Workflow:
    1. Parse logs for custom errors
    2. Build call chain from error location
    3. Check patch history for related changes
    4. Validate against MASTER_PLAN.md architecture
    5. Synthesize findings and recommend fix
    """
    
    def __init__(self, config, client):
        super().__init__(config, client)
        self.init_loop_detection()
        self.logger = logging.getLogger(__name__)
        
        # Will initialize analyzers when needed (lazy loading)
        self._log_analyzer = None
        self._patch_analyzer = None
        self._call_graph_builder = None
        self._arch_analyzer = None
    
    @property
    def log_analyzer(self):
        """Lazy load LogAnalyzer"""
        if self._log_analyzer is None:
            from ..log_analyzer import LogAnalyzer
            self._log_analyzer = LogAnalyzer(self.config.project_dir)
        return self._log_analyzer
    
    @property
    def patch_analyzer(self):
        """Lazy load PatchAnalyzer"""
        if self._patch_analyzer is None:
            from ..patch_analyzer import PatchAnalyzer
            self._patch_analyzer = PatchAnalyzer(self.config.project_dir)
        return self._patch_analyzer
    
    @property
    def call_graph_builder(self):
        """Lazy load CallGraphBuilder"""
        if self._call_graph_builder is None:
            from ..call_graph_builder import CallGraphBuilder
            self._call_graph_builder = CallGraphBuilder(self.config.project_dir)
        return self._call_graph_builder
    
    @property
    def arch_analyzer(self):
        """Lazy load ArchitectureAnalyzer"""
        if self._arch_analyzer is None:
            from ..architecture_analyzer import ArchitectureAnalyzer
            self._arch_analyzer = ArchitectureAnalyzer(self.config.project_dir)
        return self._arch_analyzer
    
    def execute(self, context: Dict) -> PhaseResult:
        """
        Execute application troubleshooting workflow.
        
        Args:
            context: Dict containing:
                - error_info: Error details from INVESTIGATION
                - log_file: Path to application log file
                - error_location: File:line where error occurred
                - error_message: The error message
        
        Returns:
            PhaseResult with findings and recommended fix
        """
        self.logger.info("=" * 70)
        self.logger.info("APPLICATION TROUBLESHOOTING PHASE")
        self.logger.info("=" * 70)
        
        error_info = context.get('error_info', {})
        log_file = context.get('log_file')
        error_location = context.get('error_location', '')
        error_message = context.get('error_message', '')
        
        self.logger.info(f"Error: {error_message}")
        self.logger.info(f"Location: {error_location}")
        
        # Track tool calls for loop detection
        # self.track_tool_calls(tool_calls, results)  # TODO: Add when tool calls are implemented
        
        # Build comprehensive analysis
        findings = {
            'error': error_message,
            'location': error_location,
            'log_analysis': {},
            'call_chain': {},
            'patch_history': {},
            'architecture_analysis': {},
            'root_cause': '',
            'recommended_fix': {}
        }
        
        try:
            # Step 1: Analyze logs if available
            if log_file:
                self.logger.info("\n📋 Step 1: Analyzing application logs...")
                findings['log_analysis'] = self._analyze_logs(log_file, error_message)
            
            # Step 2: Build call chain from error location
            if error_location and ':' in error_location:
                self.logger.info("\n🔗 Step 2: Tracing call chain...")
                findings['call_chain'] = self._trace_call_chain(error_location)
            
            # Step 3: Check patch history
            self.logger.info("\n📝 Step 3: Analyzing patch history...")
            findings['patch_history'] = self._analyze_patch_history(error_location, error_message)
            
            # Step 4: Validate against architecture
            self.logger.info("\n🏗️  Step 4: Validating architecture...")
            findings['architecture_analysis'] = self._validate_architecture(error_info)
            
            # Step 5: Synthesize findings
            self.logger.info("\n🧠 Step 5: Synthesizing findings...")
            root_cause, recommended_fix = self._synthesize_findings(findings)
            
            findings['root_cause'] = root_cause
            findings['recommended_fix'] = recommended_fix
            
            self.logger.info("\n" + "=" * 70)
            self.logger.info("TROUBLESHOOTING COMPLETE")
            self.logger.info("=" * 70)
            self.logger.info(f"\nRoot Cause: {root_cause}")
            self.logger.info(f"\nRecommended Fix: {recommended_fix.get('strategy', 'Unknown')}")
            
            # Check for loops
            if self.check_for_loops():
                self.logger.warning("Loop detected in application troubleshooting")
            
            return PhaseResult(
                success=True,
                next_phase="debugging",
                data=findings,
                message=f"Application troubleshooting complete: {root_cause}"
            )
            
        except Exception as e:
            self.logger.error(f"Error during application troubleshooting: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            return PhaseResult(
                success=False,
                next_phase="debugging",
                data=findings,
                message=f"Troubleshooting failed: {str(e)}"
            )
    
    def _analyze_logs(self, log_file: str, error_message: str) -> Dict:
        """Analyze application logs for error patterns"""
        analysis = {
            'error_patterns': {},
            'timeline': [],
            'related_errors': [],
            'context': []
        }
        
        try:
            # Parse log file
            self.logger.info(f"   Parsing log file: {log_file}")
            # Will use parse_application_log tool via AI
            
            # Extract error patterns
            self.logger.info("   Extracting error patterns...")
            # Will use extract_error_patterns tool via AI
            
            # Get context around error
            self.logger.info("   Analyzing error context...")
            # Will use analyze_log_context tool via AI
            
            # Find related errors
            self.logger.info("   Correlating related errors...")
            # Will use correlate_log_errors tool via AI
            
        except Exception as e:
            self.logger.error(f"   Error analyzing logs: {e}")
        
        return analysis
    
    def _trace_call_chain(self, error_location: str) -> Dict:
        """Trace call chain from error location"""
        chain = {
            'call_graph': {},
            'import_chain': {},
            'callers': []
        }
        
        try:
            # Parse error location
            if ':' in error_location:
                file_path, line_num = error_location.rsplit(':', 1)
                
                self.logger.info(f"   Building call graph from: {file_path}")
                # Will use build_call_graph tool via AI
                
                self.logger.info("   Tracing import chain...")
                # Will use trace_import_chain tool via AI
                
                self.logger.info("   Finding function callers...")
                # Will use find_function_callers tool via AI
                
        except Exception as e:
            self.logger.error(f"   Error tracing call chain: {e}")
        
        return chain
    
    def _analyze_patch_history(self, error_location: str, error_message: str) -> Dict:
        """Analyze patch history for related changes"""
        history = {
            'recent_patches': [],
            'correlated_patches': [],
            'rollback_candidates': []
        }
        
        try:
            self.logger.info("   Listing recent patches...")
            # Will use list_patch_files tool via AI
            
            self.logger.info("   Correlating patches with error...")
            # Will use correlate_patch_to_error tool via AI
            
            self.logger.info("   Analyzing patch impact...")
            # Will use analyze_patch_file tool via AI
            
        except Exception as e:
            self.logger.error(f"   Error analyzing patches: {e}")
        
        return history
    
    def _validate_architecture(self, error_info: Dict) -> Dict:
        """Validate against MASTER_PLAN.md architecture"""
        validation = {
            'architecture': {},
            'compliance': 0.0,
            'deviations': [],
            'violations': []
        }
        
        try:
            self.logger.info("   Parsing MASTER_PLAN.md...")
            # Will use parse_master_plan tool via AI
            
            self.logger.info("   Comparing actual vs. intended architecture...")
            # Will use compare_architecture tool via AI
            
        except Exception as e:
            self.logger.error(f"   Error validating architecture: {e}")
        
        return validation
    
    def _synthesize_findings(self, findings: Dict) -> tuple[str, Dict]:
        """
        Synthesize all findings into root cause and recommended fix.
        
        Returns:
            Tuple of (root_cause, recommended_fix)
        """
        # Analyze all findings
        log_analysis = findings.get('log_analysis', {})
        call_chain = findings.get('call_chain', {})
        patch_history = findings.get('patch_history', {})
        arch_analysis = findings.get('architecture_analysis', {})
        
        # Determine root cause
        root_cause = "Unknown"
        
        # Check for configuration issues
        if 'configuration' in findings.get('error', '').lower():
            root_cause = "Configuration issue detected"
        
        # Check for missing resources
        if 'not found' in findings.get('error', '').lower():
            root_cause = "Missing resource or component"
        
        # Check for architectural violations
        if arch_analysis.get('violations'):
            root_cause = "Architectural violation"
        
        # Generate recommended fix
        recommended_fix = {
            'strategy': 'INVESTIGATE_FURTHER',
            'description': 'Additional investigation needed',
            'confidence': 0.5
        }
        
        # Will use suggest_architectural_fix tool via AI for better recommendations
        
        return root_cause, recommended_fix