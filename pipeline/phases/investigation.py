import time
"""
Investigation Phase

Diagnoses problems before attempting fixes.
Gathers comprehensive context and generates diagnostic reports.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from .base import BasePhase, PhaseResult
from ..state.manager import PipelineState
from ..tools import get_tools_for_phase
from ..handlers import ToolCallHandler


class InvestigationPhase(BasePhase):
    """
    Investigation phase that diagnoses problems before fixing.
    
    Responsibilities:
    - Gather comprehensive context about the error
    - Examine related files and dependencies
    - Test hypotheses about the root cause
    - Generate diagnostic report
    - Recommend fix strategies
    """
    
    phase_name = "investigation"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # ARCHITECTURE CONFIG - Load project architecture configuration
        from ..architecture_parser import get_architecture_config
        self.architecture_config = get_architecture_config(self.project_dir)
        self.logger.info(f"  📐 Architecture config loaded: {len(self.architecture_config.library_dirs)} library dirs")
        
        # CRITICAL: Investigation needs ALL analysis tools
        from ..analysis.complexity import ComplexityAnalyzer
        from ..analysis.dead_code import DeadCodeDetector
        from ..analysis.integration_gaps import IntegrationGapFinder
        from ..analysis.call_graph import CallGraphGenerator
        from ..analysis.bug_detection import BugDetector
        from ..analysis.antipatterns import AntiPatternDetector
        from ..analysis.dataflow import DataFlowAnalyzer
        
        self.complexity_analyzer = ComplexityAnalyzer(str(self.project_dir), self.logger)
        self.dead_code_detector = DeadCodeDetector(str(self.project_dir), self.logger, self.architecture_config)
        self.gap_finder = IntegrationGapFinder(str(self.project_dir), self.logger)
        self.call_graph = CallGraphGenerator(str(self.project_dir), self.logger)
        self.bug_detector = BugDetector(str(self.project_dir), self.logger)
        self.antipattern_detector = AntiPatternDetector(str(self.project_dir), self.logger)
        self.dataflow_analyzer = DataFlowAnalyzer(str(self.project_dir), self.logger)
        
        # MESSAGE BUS: Subscribe to relevant events
        if self.message_bus:
            from ..messaging import MessageType
            self._subscribe_to_messages([
                MessageType.ISSUE_FOUND,
                MessageType.PHASE_STARTED,  # Use PHASE_STARTED instead of DEBUG_STARTED
                MessageType.SYSTEM_ALERT,
            ])
            self.logger.info("  📡 Message bus subscriptions configured")
        
        self.logger.info("  🔍 Investigation phase initialized with ALL analysis capabilities and IPC integration")
    
    def execute(self, state: PipelineState,
                issue: Dict = None, **kwargs) -> PhaseResult:
        """Execute investigation phase"""
        
        # ADAPTIVE PROMPTS: Update system prompt based on recent investigations
        if self.adaptive_prompts:
            self.update_system_prompt_with_adaptation({
                'state': state,
                'phase': self.phase_name,
                'recent_investigations': [],  # Could track recent investigations
                'recent_issues': state.get_recent_issues(self.phase_name, limit=5) if hasattr(state, 'get_recent_issues') else []
            })
        
        # CORRELATION ENGINE: Get cross-phase correlations
        correlations = self.get_cross_phase_correlation({
            'phase': self.phase_name
        })
        if correlations:
            self.logger.debug(f"  🔗 Found {len(correlations)} cross-phase correlations")
        
        # PATTERN OPTIMIZER: Get optimization suggestions
        optimization = self.get_optimization_suggestion({
            'current_strategy': 'phase_execution'
        })
        if optimization and optimization.get('suggestions'):
            self.logger.debug(f"  💡 Optimization suggestions available")
        
        # MESSAGE BUS: Publish phase start event
        self._publish_message('PHASE_STARTED', {
            'phase': self.phase_name,
            'timestamp': datetime.now().isoformat(),
            'issue': issue.get('description') if issue else None,
            'correlations': correlations,
            'optimization': optimization
        })
        
        """Execute investigation for an issue"""
        
        # ARCHITECTURE INTEGRATION: Read architecture for design context
        architecture = self._read_architecture()
        if architecture:
            self.logger.info(f"  📐 Architecture loaded: {len(architecture.get('components', {}))} components defined")
        
        # IPC INTEGRATION: Read objectives for investigation priorities
        objectives = self._read_objectives()
        if objectives:
            self.logger.info(f"  🎯 Objectives loaded: PRIMARY={bool(objectives.get('primary'))}, SECONDARY={len(objectives.get('secondary', []))}")
        
        # IPC INTEGRATION: Write status at start
        self._write_status({
            "status": "Starting investigation",
            "action": "start",
            "issue": issue.get('description') if issue else None,
            "filepath": issue.get('filepath') if issue else None
        })
        
        # INITIALIZE IPC DOCUMENTS (if first run)
        self.initialize_ipc_documents()
        
        # READ STRATEGIC DOCUMENTS for context
        strategic_docs = self.read_strategic_docs()
        
        # READ OWN TASKS
        tasks_from_doc = self.read_own_tasks()
        
        # READ OTHER PHASES' OUTPUTS for context
        debugging_output = self.read_phase_output('debugging')
        qa_output = self.read_phase_output('qa')
        
        if issue is None:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="No issue provided for investigation"
            )
        
        filepath = issue.get("filepath")
        if not filepath:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="Issue has no filepath"
            )
        
        # Normalize filepath
        filepath = filepath.lstrip('/').replace('\\', '/')
        if filepath.startswith('./'):
            filepath = filepath[2:]
        
        self.logger.info(f"  🔍 Investigating: {filepath}")
        self.logger.info(f"  Issue: [{issue.get('type')}] {issue.get('message', '')[:80]}")
        
        # Read current content
        content = self.read_file(filepath)
        if not content:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"File not found: {filepath}"
            )
        
        # Build investigation prompt
        investigation_prompt = self._build_investigation_prompt(filepath, content, issue)
        
        # Build simple investigation message
        user_message = self._build_investigation_message(filepath, content, issue)
        
        # Get tools for investigation phase
        tools = get_tools_for_phase("investigation")
        
        # Call model with conversation history
        self.logger.info("  Calling model with conversation history")
        response = self.chat_with_history(user_message, tools)
        
        # Extract tool calls and content
        tool_calls = response.get("tool_calls", [])
        response_content = response.get("content", "")
        
        # Execute tool calls to gather context
        if tool_calls:
            verbose = getattr(self.config, 'verbose', 0) if hasattr(self, 'config') else 0
            activity_log = self.project_dir / 'ai_activity.log'
            handler = ToolCallHandler(self.project_dir, verbose=verbose, activity_log_file=str(activity_log))
            results = handler.process_tool_calls(tool_calls)
            
            self.logger.info(f"  ✓ Gathered context using {len(tool_calls)} tool calls")
        
        # Extract findings from response
        findings = self._extract_findings(content, issue)
        
        self.logger.info(f"  📋 Investigation complete")
        if findings.get('root_cause'):
            self.logger.info(f"  Root cause: {findings['root_cause']}")
        if findings.get('recommended_fix'):
            self.logger.info(f"  Recommended fix: {findings['recommended_fix']}")
        
        # WRITE STATUS to INVESTIGATION_WRITE.md
        from datetime import datetime
        status_content = f"""# Investigation Phase Status

**Last Updated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Issue Investigated
- File: {filepath}
- Issue: {issue.get('description', 'No description')}

## Findings
{chr(10).join(f"- {key}: {value}" for key, value in findings.items() if key != 'recommended_fix')}

## Recommended Fix
{findings.get('recommended_fix', 'No specific fix recommended')}

## Next Steps
- Debugging phase should implement the recommended fix
"""
        self.write_own_status(status_content)
        
        # SEND MESSAGES to other phases
        if findings.get('recommended_fix'):
            self.send_message_to_phase('debugging', f"Investigation complete for {filepath}: {findings.get('recommended_fix')}")
            
            # PATTERN RECOGNITION: Record investigation pattern
            self.record_execution_pattern({
                'pattern_type': 'investigation_complete',
                'success': True
            })
            
            # ANALYTICS: Track investigation metric
            self.track_phase_metric({
                'metric': 'investigation_completed'
            })
        
        # RECOMMEND SPECIALIZED PHASES (but don't activate them)
        # The coordinator will decide whether to activate based on failure loops
        specialized_recommendation = None
        if "missing tool" in response_content.lower() or "need tool" in response_content.lower():
            specialized_recommendation = "tool_design"
            self.logger.info("  💡 Recommendation: Consider tool_design phase (missing capability)")
        elif "unclear prompt" in response_content.lower() or "prompt issue" in response_content.lower():
            specialized_recommendation = "prompt_improvement"
            self.logger.info("  💡 Recommendation: Consider prompt_improvement phase")
        elif "missing specialist" in response_content.lower() or "need expert" in response_content.lower():
            specialized_recommendation = "role_design"
            self.logger.info("  💡 Recommendation: Consider role_design phase")
        
        # IPC INTEGRATION: Write completion status
        self._write_status({
            "status": "Investigation completed",
            "action": "complete",
            "filepath": filepath,
            "findings_count": len(findings),
            "specialized_recommendation": specialized_recommendation
        })
        
        # ARCHITECTURE INTEGRATION: Record investigation findings in architecture
        if architecture and findings:
            self._update_architecture(
                'investigations',
                f"Investigation of {filepath}: {len(findings)} findings",
                f"Investigation: {issue.get('type')} in {filepath}"
            )
        
        # MESSAGE BUS: Publish phase completion
        self._publish_message('PHASE_COMPLETED', {
            'phase': self.phase_name,
            'timestamp': datetime.now().isoformat(),
            'success': True,
            'findings_count': len(findings),
            'filepath': filepath
        })
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message="Investigation complete",
            data={
                "findings": findings,
                "issue": issue,
                "filepath": filepath,
                "specialized_recommendation": specialized_recommendation  # Recommendation, not activation
            }
        )
    
    def _get_system_prompt(self, phase_name: str = None) -> str:
        """Get system prompt for investigation phase"""
        # Use centralized prompt from prompts.py
        from ..prompts import SYSTEM_PROMPTS
        return SYSTEM_PROMPTS.get('investigation', '')
    
    def _build_investigation_prompt(self, filepath: str, content: str, issue: Dict) -> str:
        """Build investigation prompt"""
        
        error_type = issue.get('type', 'Unknown')
        error_msg = issue.get('message', '')
        line_num = issue.get('line', 'unknown')
        
        # Check if this is a function call error
        is_function_call_error = any(keyword in error_msg.lower() for keyword in [
            'unexpected keyword argument',
            'missing required positional argument',
            'takes', 'positional argument',
            'got an unexpected'
        ])
        
        prompt = f"""Investigate this code issue:

FILE: {filepath}
ERROR TYPE: {error_type}
ERROR MESSAGE: {error_msg}
LINE: {line_num}

FILE CONTENT:
```python
{content}
```

YOUR TASK:
"""
        
        if is_function_call_error:
            prompt += """
⚠️ CRITICAL: This appears to be a FUNCTION CALL ERROR (invalid parameters)

MANDATORY INVESTIGATION STEPS:
1. **FIRST**: Use get_function_signature to extract the target function's signature
   - Identify the function being called (e.g., JobExecutor.__init__)
   - Find the file where it's defined (e.g., src/execution/job_executor.py)
   - Call: get_function_signature(filepath="...", function_name="__init__", class_name="JobExecutor")
   
2. **SECOND**: Compare the function signature with the actual call
   - What parameters does the function ACTUALLY accept?
   - What parameters is the code trying to pass?
   - Which parameters are invalid?
   
3. **THIRD**: Use read_file to examine the target function if needed
   - Verify the signature extraction is correct
   - Check if there are any *args or **kwargs
   
4. **FOURTH**: Determine the fix strategy
   - Should invalid parameters be REMOVED from the call?
   - Should the function signature be MODIFIED to accept them?
   - Are the parameters being passed with wrong names?

5. **REPORT YOUR FINDINGS**:
   - Root cause: Exactly which parameters are invalid and why
   - Recommended fix: Remove invalid parameters OR modify function signature
   - Complications: Any dependencies or side effects

START BY CALLING get_function_signature - This is CRITICAL for function call errors!
"""
        else:
            prompt += """
1. Use read_file to examine any imported modules or related files
2. Use search_code to find similar patterns or related code
3. If the error involves function calls, use get_function_signature to verify parameters
4. Analyze the error in context
5. Identify the root cause
6. Recommend a fix strategy

Start your investigation now by using the available tools."""
        
        return prompt
    
    def _get_investigation_tools(self) -> List[Dict]:
        """Get tools available for investigation"""
        # Use debugging phase tools which include signature validation
        return get_tools_for_phase("debugging")
    
    def _extract_findings(self, content: str, issue: Dict) -> Dict:
        """Extract findings from investigation response"""
        
        findings = {
            "root_cause": None,
            "recommended_fix": None,
            "related_files": [],
            "complications": []
        }
        
        if not content:
            return findings
        
        content_lower = content.lower()
        
        # Try to extract root cause - get the full section, not just one sentence
        if "root cause" in content_lower:
            # Find the section containing "root cause"
            import re
            # Look for "Root Cause" section (case insensitive)
            match = re.search(r'(?:###?\s*)?(?:Step \d+:?\s*)?(?:Identify the )?Root Cause[:\s]*\n+(.*?)(?=\n\n|###|$)', content, re.IGNORECASE | re.DOTALL)
            if match:
                findings["root_cause"] = match.group(1).strip()
            else:
                # Fallback: Find sentences containing "root cause"
                sentences = content.split('.')
                root_cause_sentences = []
                for i, sentence in enumerate(sentences):
                    if "root cause" in sentence.lower():
                        # Take this sentence and the next 2-3 sentences for context
                        root_cause_sentences = sentences[i:min(i+3, len(sentences))]
                        break
                if root_cause_sentences:
                    findings["root_cause"] = '. '.join(s.strip() for s in root_cause_sentences if s.strip())
        
        # Try to extract recommended fix - get the full section
        if "recommend" in content_lower or "fix" in content_lower:
            import re
            # Look for "Recommended Fix" or "Fix Strategy" section
            match = re.search(r'(?:###?\s*)?(?:Step \d+:?\s*)?(?:Recommend a )?Fix Strategy[:\s]*\n+(.*?)(?=\n\n|###|$)', content, re.IGNORECASE | re.DOTALL)
            if match:
                findings["recommended_fix"] = match.group(1).strip()
            else:
                # Fallback: Find sentences containing "recommend" or "fix"
                sentences = content.split('.')
                fix_sentences = []
                for i, sentence in enumerate(sentences):
                    if "recommend" in sentence.lower() or "should fix" in sentence.lower():
                        # Take this sentence and the next 2-3 sentences for context
                        fix_sentences = sentences[i:min(i+3, len(sentences))]
                        break
                if fix_sentences:
                    findings["recommended_fix"] = '. '.join(s.strip() for s in fix_sentences if s.strip())
        
        # Look for file mentions
        import re
        file_pattern = r'`([^`]+\.py)`'
        files = re.findall(file_pattern, content)
        findings["related_files"] = list(set(files))
        
        return findings
    
    def _build_investigation_message(self, filepath: str, content: str, issue: Dict) -> str:
        """
        Build a simple, focused investigation message.
        
        The conversation history provides context, so we keep this simple.
        """
        parts = []
        
        # Issue description
        issue_type = issue.get('type', 'unknown')
        issue_desc = issue.get('description', 'No description')
        parts.append(f"Investigate this issue in {filepath}:")
        parts.append(f"Issue type: {issue_type}")
        parts.append(f"Description: {issue_desc}")
        
        # Current code
        parts.append(f"\nCurrent code:\n```\n{content}\n```")
        
        # Instructions
        parts.append("\nPlease investigate the issue and use tools to gather relevant context.")
        parts.append("Look for related files, dependencies, and potential causes.")
        
        return "\n".join(parts)
    
    def generate_state_markdown(self, state: PipelineState) -> str:
        """
        Generate markdown content for investigation phase state.
        
        Args:
            state: Current pipeline state
            
        Returns:
            Markdown string
        """
        lines = ["# Investigation Phase State\n"]
        
        if self.phase_name in state.phases:
            phase_state = state.phases[self.phase_name]
            lines.append(f"**Run Count:** {phase_state.run_count}\n")
            lines.append(f"**Last Run:** {phase_state.last_run}\n")
            lines.append(f"**Success Rate:** {phase_state.success_count}/{phase_state.run_count}\n")
        else:
            lines.append("No investigation runs yet.\n")
        
        return "\n".join(lines)