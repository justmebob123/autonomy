"""
Reasoning Specialist

Expert model for strategic analysis and decision-making.
Uses qwen2.5:32b on ollama02 for deep reasoning capability.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ReasoningType(Enum):
    """Types of reasoning tasks"""
    STRATEGIC_PLANNING = "strategic_planning"
    PROBLEM_ANALYSIS = "problem_analysis"
    DECISION_MAKING = "decision_making"
    FAILURE_DIAGNOSIS = "failure_diagnosis"
    OPTIMIZATION = "optimization"
    RISK_ASSESSMENT = "risk_assessment"


@dataclass
class ReasoningTask:
    """Represents a reasoning task"""
    reasoning_type: ReasoningType
    question: str
    context: Dict[str, Any]
    constraints: List[str] = None
    options: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.constraints is None:
            self.constraints = []
        if self.options is None:
            self.options = []


class ReasoningSpecialist:
    """
    Specialist for strategic analysis and decision-making.
    
    Capabilities:
    - Strategic planning and roadmap creation
    - Complex problem analysis
    - Multi-criteria decision making
    - Failure diagnosis and root cause analysis
    - Optimization recommendations
    - Risk assessment and mitigation
    """
    
    def __init__(self, model_tool):
        """
        Initialize reasoning specialist.
        
        Args:
            model_tool: ModelTool instance configured for reasoning
        """
        self.model_tool = model_tool
        self.reasoning_frameworks = self._load_reasoning_frameworks()
        
    def _load_reasoning_frameworks(self) -> Dict[str, Any]:
        """Load reasoning frameworks and methodologies"""
        return {
            "strategic_planning": {
                "framework": "SWOT + Roadmap",
                "steps": [
                    "Analyze current state",
                    "Identify goals and constraints",
                    "Evaluate options",
                    "Create phased plan",
                    "Define success metrics"
                ]
            },
            "problem_analysis": {
                "framework": "5 Whys + Root Cause",
                "steps": [
                    "Define the problem clearly",
                    "Gather relevant data",
                    "Ask 'why' iteratively",
                    "Identify root causes",
                    "Propose solutions"
                ]
            },
            "decision_making": {
                "framework": "Multi-Criteria Analysis",
                "steps": [
                    "Define decision criteria",
                    "Weight criteria by importance",
                    "Evaluate each option",
                    "Calculate scores",
                    "Recommend best option"
                ]
            },
            "failure_diagnosis": {
                "framework": "Systematic Debugging",
                "steps": [
                    "Reproduce the failure",
                    "Analyze symptoms",
                    "Form hypotheses",
                    "Test hypotheses",
                    "Identify root cause",
                    "Recommend fix"
                ]
            }
        }
    
    def get_system_prompt(self, task: ReasoningTask) -> str:
        """
        Generate specialized system prompt for reasoning task.
        
        Args:
            task: The reasoning task to perform
            
        Returns:
            Specialized system prompt
        """
        base_prompt = """You are an expert reasoning specialist with deep analytical and strategic thinking capabilities.

Your approach:
1. Think systematically and methodically
2. Consider multiple perspectives and alternatives
3. Use structured reasoning frameworks
4. Base conclusions on evidence and logic
5. Identify assumptions and validate them
6. Consider both short-term and long-term implications
7. Provide clear, actionable recommendations

"""
        
        # Add reasoning type specific guidance
        framework_guidance = self._get_framework_guidance(task.reasoning_type)
        
        # Add constraints if any
        constraints_text = ""
        if task.constraints:
            constraints_text = "\nConstraints to consider:\n" + "\n".join(f"- {c}" for c in task.constraints)
        
        return base_prompt + framework_guidance + constraints_text
    
    def _get_framework_guidance(self, reasoning_type: ReasoningType) -> str:
        """Get framework-specific guidance"""
        framework_key = reasoning_type.value
        framework = self.reasoning_frameworks.get(framework_key, {})
        
        if not framework:
            return ""
        
        guidance = f"""
Reasoning Framework: {framework.get('framework', 'General Analysis')}

Systematic Steps:
"""
        steps = framework.get('steps', [])
        for i, step in enumerate(steps, 1):
            guidance += f"{i}. {step}\n"
        
        return guidance
    
    def get_available_tools(self, task: ReasoningTask) -> List[Dict[str, Any]]:
        """
        Get tools available for this reasoning task.
        
        Args:
            task: The reasoning task
            
        Returns:
            List of tool definitions
        """
        # Base analysis tools
        base_tools = [
            {
                "name": "gather_data",
                "description": "Gather additional data or context needed for analysis",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data_type": {
                            "type": "string",
                            "description": "Type of data to gather (e.g., 'metrics', 'logs', 'history')"
                        },
                        "query": {
                            "type": "string",
                            "description": "Specific query or filter"
                        }
                    },
                    "required": ["data_type"]
                }
            },
            {
                "name": "analyze_pattern",
                "description": "Analyze patterns in data or behavior",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "string",
                            "description": "Data to analyze"
                        },
                        "pattern_type": {
                            "type": "string",
                            "description": "Type of pattern to look for"
                        }
                    },
                    "required": ["data", "pattern_type"]
                }
            }
        ]
        
        # Add task-specific tools
        if task.reasoning_type == ReasoningType.FAILURE_DIAGNOSIS:
            base_tools.extend([
                {
                    "name": "get_error_logs",
                    "description": "Retrieve error logs for analysis",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "time_range": {
                                "type": "string",
                                "description": "Time range for logs"
                            },
                            "filter": {
                                "type": "string",
                                "description": "Filter pattern"
                            }
                        }
                    }
                },
                {
                    "name": "test_hypothesis",
                    "description": "Test a hypothesis about the failure",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "hypothesis": {
                                "type": "string",
                                "description": "Hypothesis to test"
                            },
                            "test_method": {
                                "type": "string",
                                "description": "Method to test hypothesis"
                            }
                        },
                        "required": ["hypothesis"]
                    }
                }
            ])
        
        if task.reasoning_type == ReasoningType.DECISION_MAKING:
            base_tools.append({
                "name": "evaluate_option",
                "description": "Evaluate an option against criteria",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "option": {
                            "type": "string",
                            "description": "Option to evaluate"
                        },
                        "criteria": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Evaluation criteria"
                        }
                    },
                    "required": ["option", "criteria"]
                }
            })
        
        return base_tools
    
    def execute_task(self, task: ReasoningTask) -> Dict[str, Any]:
        """
        Execute a reasoning task.
        
        Args:
            task: The reasoning task to execute
            
        Returns:
            Result with analysis, recommendations, and tool calls
        """
        logger.info(f"ReasoningSpecialist executing {task.reasoning_type.value} task")
        
        # Build context message
        context_parts = [
            f"Reasoning Task: {task.reasoning_type.value.upper().replace('_', ' ')}",
            f"\nQuestion: {task.question}"
        ]
        
        if task.context:
            context_parts.append(f"\nContext:\n{self._format_context(task.context)}")
        
        if task.options:
            context_parts.append(f"\nOptions to consider:\n{self._format_options(task.options)}")
        
        context_message = "\n".join(context_parts)
        
        # Get system prompt and tools
        system_prompt = self.get_system_prompt(task)
        tools = self.get_available_tools(task)
        
        # Execute with model tool
        result = self.model_tool.execute(
            messages=[{"role": "user", "content": context_message}],
            system_prompt=system_prompt,
            tools=tools
        )
        
        # Extract structured reasoning
        structured_reasoning = self._extract_reasoning(result, task)
        
        return {
            "success": result.get("success", False),
            "analysis": result.get("response", ""),
            "tool_calls": result.get("tool_calls", []),
            "structured_reasoning": structured_reasoning,
            "task": task
        }
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary for prompt"""
        lines = []
        for key, value in context.items():
            if isinstance(value, (list, dict)):
                lines.append(f"{key}:")
                if isinstance(value, list):
                    for item in value:
                        lines.append(f"  - {item}")
                else:
                    for k, v in value.items():
                        lines.append(f"  {k}: {v}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)
    
    def _format_options(self, options: List[Dict[str, Any]]) -> str:
        """Format options for prompt"""
        lines = []
        for i, option in enumerate(options, 1):
            lines.append(f"\nOption {i}:")
            for key, value in option.items():
                lines.append(f"  {key}: {value}")
        return "\n".join(lines)
    
    def _extract_reasoning(self, result: Dict[str, Any], task: ReasoningTask) -> Dict[str, Any]:
        """
        Extract structured reasoning from result.
        
        Args:
            result: Result from model execution
            task: Original task
            
        Returns:
            Structured reasoning with key insights
        """
        response = result.get("response", "")
        
        structured = {
            "reasoning_type": task.reasoning_type.value,
            "key_insights": [],
            "recommendations": [],
            "confidence": "medium",
            "assumptions": [],
            "risks": []
        }
        
        # Simple keyword-based extraction (could be enhanced with NLP)
        response_lower = response.lower()
        
        # Extract insights (lines with "insight", "finding", "observation")
        for line in response.split('\n'):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['insight', 'finding', 'observation', 'key point']):
                structured["key_insights"].append(line.strip())
        
        # Extract recommendations (lines with "recommend", "suggest", "should")
        for line in response.split('\n'):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['recommend', 'suggest', 'should', 'propose']):
                structured["recommendations"].append(line.strip())
        
        # Assess confidence based on language
        if any(word in response_lower for word in ['certain', 'definitely', 'clearly', 'obviously']):
            structured["confidence"] = "high"
        elif any(word in response_lower for word in ['uncertain', 'possibly', 'might', 'unclear']):
            structured["confidence"] = "low"
        
        # Extract assumptions
        for line in response.split('\n'):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['assume', 'assuming', 'assumption']):
                structured["assumptions"].append(line.strip())
        
        # Extract risks
        for line in response.split('\n'):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['risk', 'concern', 'issue', 'problem']):
                structured["risks"].append(line.strip())
        
        return structured
    
    def diagnose_failure(self, failure_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Diagnose a failure and recommend fixes.
        
        Args:
            failure_description: Description of the failure
            context: Context including logs, state, history
            
        Returns:
            Diagnosis with root cause and recommendations
        """
        logger.info("ReasoningSpecialist diagnosing failure")
        
        task = ReasoningTask(
            reasoning_type=ReasoningType.FAILURE_DIAGNOSIS,
            question=f"Diagnose this failure and recommend fixes: {failure_description}",
            context=context
        )
        
        result = self.execute_task(task)
        
        return {
            "failure": failure_description,
            "diagnosis": result.get("analysis", ""),
            "root_cause": self._extract_root_cause(result.get("analysis", "")),
            "recommendations": result.get("structured_reasoning", {}).get("recommendations", []),
            "confidence": result.get("structured_reasoning", {}).get("confidence", "medium")
        }
    
    def _extract_root_cause(self, analysis: str) -> str:
        """Extract root cause from analysis"""
        # Look for explicit root cause statement
        for line in analysis.split('\n'):
            line_lower = line.lower()
            if 'root cause' in line_lower:
                return line.strip()
        
        # If no explicit statement, return first significant finding
        for line in analysis.split('\n'):
            if len(line.strip()) > 50:  # Substantial line
                return line.strip()
        
        return "Root cause not clearly identified"
    
    def make_decision(
        self,
        question: str,
        options: List[Dict[str, Any]],
        criteria: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make a decision between multiple options.
        
        Args:
            question: Decision question
            options: List of options with details
            criteria: Decision criteria
            context: Additional context
            
        Returns:
            Decision with reasoning and scores
        """
        logger.info(f"ReasoningSpecialist making decision: {question}")
        
        # Add criteria to context
        context["criteria"] = criteria
        
        task = ReasoningTask(
            reasoning_type=ReasoningType.DECISION_MAKING,
            question=question,
            context=context,
            options=options
        )
        
        result = self.execute_task(task)
        
        return {
            "question": question,
            "decision": result.get("analysis", ""),
            "recommended_option": self._extract_recommendation(result.get("analysis", ""), options),
            "reasoning": result.get("structured_reasoning", {}),
            "confidence": result.get("structured_reasoning", {}).get("confidence", "medium")
        }
    
    def _extract_recommendation(self, analysis: str, options: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract recommended option from analysis"""
        analysis_lower = analysis.lower()
        
        # Look for explicit recommendation
        for i, option in enumerate(options):
            option_name = option.get("name", f"Option {i+1}").lower()
            if f"recommend {option_name}" in analysis_lower or f"choose {option_name}" in analysis_lower:
                return option
        
        return None


def create_reasoning_specialist(model_tool) -> ReasoningSpecialist:
    """
    Factory function to create a reasoning specialist.
    
    Args:
        model_tool: ModelTool instance configured for reasoning
        
    Returns:
        ReasoningSpecialist instance
    """
    return ReasoningSpecialist(model_tool)