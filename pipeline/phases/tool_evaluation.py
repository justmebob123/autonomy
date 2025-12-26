"""
Tool Evaluation Phase

Evaluates custom tools to ensure they achieve their objectives.
If tools are insufficient, requests specialist improvements.
"""

from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import json
import importlib.util

from .base import BasePhase, PhaseResult
from .loop_detection_mixin import LoopDetectionMixin
from ..state.manager import PipelineState
from ..tools import get_tools_for_phase
from ..logging_setup import get_logger


class ToolEvaluationPhase(LoopDetectionMixin, BasePhase):
    """
    Tool Evaluation phase that tests and validates custom tools.
    
    Responsibilities:
    - Read custom tool implementations
    - Test tools with sample inputs
    - Validate outputs match expectations
    - Identify deficiencies
    - Request specialist improvements
    - Re-test after improvements
    """
    
    phase_name = "tool_evaluation"
    
    def __init__(self, *args, **kwargs):
        BasePhase.__init__(self, *args, **kwargs)
        self.init_loop_detection()
        self.custom_tools_dir = self.project_dir / "pipeline" / "tools" / "custom"
        self.custom_tools_dir.mkdir(parents=True, exist_ok=True)
        self.evaluation_results_dir = self.project_dir / ".pipeline" / "tool_evaluations"
        self.evaluation_results_dir.mkdir(parents=True, exist_ok=True)
    
    def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
        """
        Execute tool evaluation phase.
        
        Args:
            state: Current pipeline state
            **kwargs: Additional arguments
            
        Returns:
            PhaseResult with evaluation outcomes
        """
        self.logger.info("🔍 Starting tool evaluation phase...")
        
        # Find all custom tools
        custom_tools = self._find_custom_tools()
        
        if not custom_tools:
            self.logger.info("  No custom tools found to evaluate")
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message="No custom tools to evaluate"
            )
        
        self.logger.info(f"  Found {len(custom_tools)} custom tools to evaluate")
        
        # Evaluate each tool
        evaluation_results = []
        tools_needing_improvement = []
        
        for tool_name in custom_tools:
            self.logger.info(f"\n  📋 Evaluating tool: {tool_name}")
            
            result = self._evaluate_tool(tool_name)
            evaluation_results.append(result)
            
            if not result['passed']:
                tools_needing_improvement.append(tool_name)
                self.logger.warning(f"    ⚠️  Tool needs improvement: {result['issues']}")
            else:
                self.logger.info(f"    ✅ Tool passed evaluation")
        
        # Request improvements for failing tools
        if tools_needing_improvement:
            self.logger.info(f"\n  🔧 Requesting improvements for {len(tools_needing_improvement)} tools...")
            
            for tool_name in tools_needing_improvement:
                self._request_tool_improvement(tool_name, evaluation_results)
        
        # Save evaluation results
        self._save_evaluation_results(evaluation_results)
        
        # Generate summary
        passed = len([r for r in evaluation_results if r['passed']])
        failed = len(evaluation_results) - passed
        
        message = f"Evaluated {len(custom_tools)} tools: {passed} passed, {failed} need improvement"
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message=message,
            data={
                'total_tools': len(custom_tools),
                'passed': passed,
                'failed': failed,
                'tools_needing_improvement': tools_needing_improvement,
                'evaluation_results': evaluation_results
            }
        )
    
    def _find_custom_tools(self) -> List[str]:
        """Find all custom tools in the custom tools directory."""
        tools = []
        
        if not self.custom_tools_dir.exists():
            return tools
        
        for spec_file in self.custom_tools_dir.glob("*_spec.json"):
            tool_name = spec_file.stem.replace("_spec", "")
            impl_file = self.custom_tools_dir / f"{tool_name}.py"
            
            if impl_file.exists():
                tools.append(tool_name)
        
        return tools
    
    def _evaluate_tool(self, tool_name: str) -> Dict:
        """
        Evaluate a custom tool.
        
        Args:
            tool_name: Name of the tool to evaluate
            
        Returns:
            Evaluation result dictionary
        """
        result = {
            'tool_name': tool_name,
            'timestamp': datetime.now().isoformat(),
            'passed': False,
            'issues': [],
            'test_results': []
        }
        
        # Read tool specification
        spec_file = self.custom_tools_dir / f"{tool_name}_spec.json"
        impl_file = self.custom_tools_dir / f"{tool_name}.py"
        
        try:
            with open(spec_file, 'r') as f:
                spec = json.load(f)
            
            # Read implementation
            impl_code = impl_file.read_text()
            
            # Use AI to evaluate the tool
            evaluation_prompt = self._get_evaluation_prompt(tool_name, spec, impl_code)
            
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "report_evaluation_result",
                        "description": "Report the evaluation result for a custom tool",
                        "parameters": {
                            "type": "object",
                            "required": ["passed", "issues", "test_results"],
                            "properties": {
                                "passed": {
                                    "type": "boolean",
                                    "description": "Whether the tool passed evaluation"
                                },
                                "issues": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of issues found"
                                },
                                "test_results": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "test_name": {"type": "string"},
                                            "passed": {"type": "boolean"},
                                            "details": {"type": "string"}
                                        }
                                    },
                                    "description": "Results of individual tests"
                                },
                                "recommendations": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Recommendations for improvement"
                                }
                            }
                        }
                    }
                }
            ]
            
            messages = [
                {"role": "system", "content": "You are a tool evaluation specialist."},
                {"role": "user", "content": evaluation_prompt}
            ]
            
            response = self.chat(messages, tools, task_type="tool_evaluation")
            
            # Parse response
            tool_calls, _ = self.parse_response(response, "tool_evaluation")
            
            # Check for loops
            if self.check_for_loops():
                self.logger.warning(f"    Loop detected for tool {tool_name}")
                result['issues'].append('Loop detected during evaluation')
                return result
            
            # Track tool calls
            self.track_tool_calls(tool_calls, results)
            
            if tool_calls:
                for call in tool_calls:
                    if call.get('tool') == 'report_evaluation_result':
                        args = call.get('args', {})
                        result['passed'] = args.get('passed', False)
                        result['issues'] = args.get('issues', [])
                        result['test_results'] = args.get('test_results', [])
                        result['recommendations'] = args.get('recommendations', [])
            
        except Exception as e:
            self.logger.error(f"    Error evaluating tool {tool_name}: {e}")
            result['issues'].append(f"Evaluation error: {str(e)}")
        
        return result
    
    def _get_evaluation_prompt(self, tool_name: str, spec: Dict, impl_code: str) -> str:
        """Generate evaluation prompt for a tool."""
        return f"""# Tool Evaluation Task

You are evaluating a custom tool to ensure it achieves its objectives.

## Tool Information

**Name:** {tool_name}

**Specification:**
```json
{json.dumps(spec, indent=2)}
```

**Implementation:**
```python
{impl_code}
```

## Evaluation Criteria

1. **Correctness:** Does the implementation match the specification?
2. **Completeness:** Are all required parameters handled?
3. **Error Handling:** Does it handle errors gracefully?
4. **Input Validation:** Does it validate inputs properly?
5. **Output Format:** Does it return the expected output format?
6. **Edge Cases:** Does it handle edge cases?
7. **Security:** Does it avoid dangerous operations?
8. **Performance:** Is it reasonably efficient?

## Your Task

Evaluate this tool against the criteria above. For each criterion:
1. Test if it meets the requirement
2. Identify any issues
3. Provide specific recommendations

Use the `report_evaluation_result` tool to report your findings.

**IMPORTANT:** Be thorough and specific. Identify concrete issues and provide actionable recommendations.
"""
    
    def _request_tool_improvement(self, tool_name: str, evaluation_results: List[Dict]) -> None:
        """
        Request specialist improvements for a tool.
        
        Args:
            tool_name: Name of the tool needing improvement
            evaluation_results: All evaluation results for context
        """
        self.logger.info(f"    🔧 Requesting specialist improvement for {tool_name}...")
        
        # Find the evaluation result for this tool
        tool_result = next((r for r in evaluation_results if r['tool_name'] == tool_name), None)
        
        if not tool_result:
            return
        
        # Read current implementation
        impl_file = self.custom_tools_dir / f"{tool_name}.py"
        spec_file = self.custom_tools_dir / f"{tool_name}_spec.json"
        
        impl_code = impl_file.read_text()
        
        with open(spec_file, 'r') as f:
            spec = json.load(f)
        
        # Create improvement request
        improvement_prompt = f"""# Tool Improvement Request

A custom tool needs improvement based on evaluation results.

## Tool Information

**Name:** {tool_name}

**Current Specification:**
```json
{json.dumps(spec, indent=2)}
```

**Current Implementation:**
```python
{impl_code}
```

## Evaluation Results

**Passed:** {tool_result['passed']}

**Issues Found:**
{chr(10).join(f"- {issue}" for issue in tool_result['issues'])}

**Test Results:**
{json.dumps(tool_result['test_results'], indent=2)}

**Recommendations:**
{chr(10).join(f"- {rec}" for rec in tool_result.get('recommendations', []))}

## Your Task

Improve this tool to address all identified issues. You should:

1. Fix all identified issues
2. Implement all recommendations
3. Ensure all tests pass
4. Maintain backward compatibility
5. Add better error handling
6. Improve input validation

Provide the improved implementation that addresses all concerns.
"""
        
        # Consult specialist for improvement
        try:
            # Use Tool Designer specialist
            from ..specialist_agents import SpecialistTeam
            
            specialist_team = SpecialistTeam(self.client, self.logger)
            
            # Create a thread-like context
            context = {
                'tool_name': tool_name,
                'evaluation_result': tool_result,
                'improvement_request': improvement_prompt
            }
            
            # Get improvement from specialist
            # Note: This would ideally use the specialist consultation system
            # For now, we log the request
            self.logger.info(f"      Improvement request created for {tool_name}")
            
            # Save improvement request
            request_file = self.evaluation_results_dir / f"{tool_name}_improvement_request.json"
            with open(request_file, 'w') as f:
                json.dump(context, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"      Error requesting improvement: {e}")
    
    def _save_evaluation_results(self, results: List[Dict]) -> None:
        """Save evaluation results to file."""
        results_file = self.evaluation_results_dir / f"evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': results
            }, f, indent=2)
        
        self.logger.info(f"\n  💾 Evaluation results saved to {results_file.name}")
    
    def generate_state_markdown(self, state: PipelineState) -> str:
        """Generate markdown content for tool evaluation state."""
        lines = [
            "# Tool Evaluation State",
            "",
            f"**Last Updated:** {self.format_timestamp()}",
            "",
            "## Custom Tools",
            ""
        ]
        
        custom_tools = self._find_custom_tools()
        
        if not custom_tools:
            lines.append("No custom tools found.")
        else:
            lines.append(f"**Total Custom Tools:** {len(custom_tools)}")
            lines.append("")
            
            for tool_name in custom_tools:
                lines.append(f"- {tool_name}")
        
        lines.extend([
            "",
            "## Recent Evaluations",
            ""
        ])
        
        # List recent evaluation files
        if self.evaluation_results_dir.exists():
            eval_files = sorted(self.evaluation_results_dir.glob("evaluation_*.json"), reverse=True)[:5]
            
            if eval_files:
                for eval_file in eval_files:
                    lines.append(f"- {eval_file.name}")
            else:
                lines.append("No evaluations yet.")
        else:
            lines.append("No evaluations yet.")
        
        return "\n".join(lines)