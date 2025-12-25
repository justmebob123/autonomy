"""
Investigation Phase

Diagnoses problems before attempting fixes.
Gathers comprehensive context and generates diagnostic reports.
"""

from datetime import datetime
from typing import Dict, List, Optional
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
    
    def execute(self, state: PipelineState,
                issue: Dict = None, **kwargs) -> PhaseResult:
        """Execute investigation for an issue"""
        
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
        
        messages = [
            {"role": "system", "content": self._get_system_prompt("debugging")},
            {"role": "user", "content": investigation_prompt}
        ]
        
        # Get tools for investigation
        tools = self._get_investigation_tools()
        
        # Send request
        response = self.chat(messages, tools, task_type="investigation")
        
        if "error" in response:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Investigation failed: {response['error']}"
            )
        
        # Parse response
        tool_calls, content = self.parser.parse_response(response)
        
        # Execute tool calls to gather context
        if tool_calls:
            verbose = getattr(self.config, 'verbose', 0) if hasattr(self, 'config') else 0
            activity_log = self.project_dir / 'ai_activity.log'
            handler = ToolCallHandler(self.project_dir, verbose=verbose, activity_log_file=str(activity_log), tool_registry=self.tool_registry)
            results = handler.process_tool_calls(tool_calls)
            
            self.logger.info(f"  ✓ Gathered context using {len(tool_calls)} tool calls")
        
        # Extract findings from response
        findings = self._extract_findings(content, issue)
        
        self.logger.info(f"  📋 Investigation complete")
        if findings.get('root_cause'):
            self.logger.info(f"  Root cause: {findings['root_cause']}")
        if findings.get('recommended_fix'):
            self.logger.info(f"  Recommended fix: {findings['recommended_fix']}")
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message="Investigation complete",
            data={
                "findings": findings,
                "issue": issue,
                "filepath": filepath
            }
        )
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for investigation phase"""
        return """You are a senior software engineer investigating a code issue.

Your role is to DIAGNOSE, not to fix. You are gathering information and understanding the problem.

AVAILABLE TOOLS:
- read_file: Read any file in the project to understand context
- search_code: Search for patterns, classes, methods across the codebase
- list_directory: Explore project structure

INVESTIGATION PROCESS:
1. Understand the error message and context
2. Examine the problematic code
3. Check related files and dependencies
4. Look for similar patterns in the codebase
5. Identify the root cause
6. Recommend a fix strategy

USE TOOLS to gather information. Don't just theorize - actually look at the code.

After investigation, provide:
- Root cause analysis
- Related files/code that might be involved
- Recommended fix strategy
- Any potential complications"""
    
    def _build_investigation_prompt(self, filepath: str, content: str, issue: Dict) -> str:
        """Build investigation prompt"""
        
        error_type = issue.get('type', 'Unknown')
        error_msg = issue.get('message', '')
        line_num = issue.get('line', 'unknown')
        
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
1. Use read_file to examine any imported modules or related files
2. Use search_code to find similar patterns or related code
3. Analyze the error in context
4. Identify the root cause
5. Recommend a fix strategy

Start your investigation now by using the available tools."""
        
        return prompt
    
    def _get_investigation_tools(self) -> List[Dict]:
        """Get tools available for investigation"""
        # Use QA phase tools which include read_file, search_code, list_directory
        return get_tools_for_phase("qa")
    
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
        
        # Try to extract root cause
        if "root cause" in content_lower:
            # Find the sentence containing "root cause"
            sentences = content.split('.')
            for sentence in sentences:
                if "root cause" in sentence.lower():
                    findings["root_cause"] = sentence.strip()
                    break
        
        # Try to extract recommended fix
        if "recommend" in content_lower or "fix" in content_lower:
            sentences = content.split('.')
            for sentence in sentences:
                if "recommend" in sentence.lower() or "should fix" in sentence.lower():
                    findings["recommended_fix"] = sentence.strip()
                    break
        
        # Look for file mentions
        import re
        file_pattern = r'`([^`]+\.py)`'
        files = re.findall(file_pattern, content)
        findings["related_files"] = list(set(files))
        
        return findings