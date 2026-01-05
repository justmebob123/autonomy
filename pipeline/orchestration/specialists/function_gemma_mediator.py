"""
FunctionGemma Mediator

Specialist for interpreting ambiguous tool calls and responses.
Uses FunctionGemma model on ollama01 for tool call clarification.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class InterpretationRequest:
    """Request to interpret ambiguous output"""
    original_response: str
    context: Dict[str, Any]
    available_tools: List[Dict[str, Any]]
    expected_format: str = "tool_call"  # or "decision", "answer"


class FunctionGemmaMediator:
    """
    Mediator for interpreting ambiguous model outputs.
    
    Capabilities:
    - Parse ambiguous tool calls
    - Fix malformed JSON
    - Clarify vague responses
    - Convert natural language to tool calls
    - Validate tool call parameters
    """
    
    def __init__(self, model_tool):
        """
        Initialize FunctionGemma mediator.
        
        Args:
            model_tool: ModelTool instance configured for FunctionGemma
        """
        self.model_tool = model_tool
        self.interpretation_patterns = self._load_interpretation_patterns()
        
    def _load_interpretation_patterns(self) -> Dict[str, Any]:
        """Load common interpretation patterns"""
        return {
            "empty_tool_name": {
                "pattern": r'"name":\s*""',
                "fix": "extract_intent_from_context"
            },
            "malformed_json": {
                "pattern": r'[^{]*{.*}[^}]*',
                "fix": "extract_and_repair_json"
            },
            "natural_language": {
                "pattern": r'^[A-Z].*[.!?]$',
                "fix": "convert_to_tool_call"
            },
            "missing_parameters": {
                "pattern": r'"parameters":\s*{}',
                "fix": "infer_parameters_from_context"
            }
        }
    
    def get_system_prompt(self, request: InterpretationRequest) -> str:
        """
        Generate system prompt for interpretation.
        
        Args:
            request: Interpretation request
            
        Returns:
            System prompt for FunctionGemma
        """
        tools_description = self._format_tools(request.available_tools)
        
        prompt = f"""You are FunctionGemma, an expert at interpreting ambiguous model outputs and converting them to proper tool calls.

Your task: Analyze the model's response and convert it to a valid tool call in JSON format.

Available Tools:
{tools_description}

Expected Format: {request.expected_format}

Guidelines:
1. If the response contains a tool call attempt, fix and complete it
2. If the response is natural language, convert it to the appropriate tool call
3. If tool name is empty, infer the intended tool from context
4. If parameters are missing, infer them from context
5. Always return valid JSON with proper structure
6. If truly ambiguous, return a clarification request

Output Format:
{{
    "tool_call": {{
        "name": "tool_name",
        "parameters": {{...}}
    }},
    "confidence": "high|medium|low",
    "reasoning": "why this interpretation"
}}

OR if clarification needed:
{{
    "clarification_needed": true,
    "question": "what needs clarification",
    "suggestions": ["option1", "option2"]
}}
"""
        return prompt
    
    def _format_tools(self, tools: List[Dict[str, Any]]) -> str:
        """Format tools for prompt"""
        lines = []
        for tool in tools:
            name = tool.get("name", "unknown")
            desc = tool.get("description", "")
            params = tool.get("parameters", {})
            
            lines.append(f"\n- {name}: {desc}")
            
            if params and "properties" in params:
                lines.append("  Parameters:")
                for param_name, param_info in params["properties"].items():
                    param_type = param_info.get("type", "any")
                    param_desc = param_info.get("description", "")
                    required = param_name in params.get("required", [])
                    req_marker = " (required)" if required else ""
                    lines.append(f"    - {param_name} ({param_type}){req_marker}: {param_desc}")
        
        return "\n".join(lines)
    
    def interpret(self, request: InterpretationRequest) -> Dict[str, Any]:
        """
        Interpret ambiguous model output.
        
        Args:
            request: Interpretation request
            
        Returns:
            Interpreted result with tool call or clarification request
        """
        logger.info("FunctionGemmaMediator interpreting ambiguous output")
        
        # Build interpretation message
        message = f"""Original Response:
{request.original_response}

Context:
{self._format_context(request.context)}

Please interpret this response and convert it to a proper tool call."""
        
        # Get system prompt
        system_prompt = self.get_system_prompt(request)
        
        # Execute with FunctionGemma
        result = self.model_tool.execute(
            messages=[{"role": "user", "content": message}],
            system_prompt=system_prompt
        )
        
        # Parse interpretation
        interpretation = self._parse_interpretation(result.get("response", ""))
        
        return {
            "success": result.get("success", False),
            "interpretation": interpretation,
            "original_response": request.original_response,
            "confidence": interpretation.get("confidence", "low")
        }
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for prompt"""
        lines = []
        for key, value in context.items():
            if isinstance(value, (list, dict)):
                lines.append(f"{key}: {json.dumps(value, indent=2)}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)
    
    def _parse_interpretation(self, response: str) -> Dict[str, Any]:
        """
        Parse FunctionGemma's interpretation response.
        
        Args:
            response: Response from FunctionGemma
            
        Returns:
            Parsed interpretation
        """
        try:
            pass
            # Try to parse as JSON
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError:
            pass
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                    return parsed
                except json.JSONDecodeError:
                    pass
            
            # Fallback: return as clarification needed
            return {
                "clarification_needed": True,
                "question": "Could not parse interpretation",
                "original_response": response
            }
    
    def fix_empty_tool_name(
        self,
        malformed_call: Dict[str, Any],
        context: Dict[str, Any],
        available_tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fix a tool call with empty name.
        
        Args:
            malformed_call: Tool call with empty name
            context: Context to infer intent
            available_tools: Available tools
            
        Returns:
            Fixed tool call or clarification request
        """
        logger.info("FunctionGemmaMediator fixing empty tool name")
        
        request = InterpretationRequest(
            original_response=json.dumps(malformed_call),
            context=context,
            available_tools=available_tools,
            expected_format="tool_call"
        )
        
        result = self.interpret(request)
        interpretation = result.get("interpretation", {})
        
        if interpretation.get("clarification_needed"):
            return {
                "success": False,
                "error": "clarification_needed",
                "clarification": interpretation
            }
        
        tool_call = interpretation.get("tool_call", {})
        if tool_call.get("name"):
            return {
                "success": True,
                "tool_call": tool_call,
                "confidence": interpretation.get("confidence", "medium")
            }
        
        return {
            "success": False,
            "error": "could_not_fix",
            "interpretation": interpretation
        }
    
    def repair_malformed_json(self, malformed_json: str) -> Dict[str, Any]:
        """
        Repair malformed JSON.
        
        Args:
            malformed_json: Malformed JSON string
            
        Returns:
            Repaired JSON or error
        """
        logger.info("FunctionGemmaMediator repairing malformed JSON")
        
        repair_prompt = f"""Repair this malformed JSON and return valid JSON:

{malformed_json}

Return only the repaired JSON, nothing else."""
        
        result = self.model_tool.execute(
            messages=[{"role": "user", "content": repair_prompt}],
            system_prompt="You are an expert at repairing malformed JSON. Return only valid JSON."
        )
        
        response = result.get("response", "")
        
        try:
            repaired = json.loads(response)
            return {
                "success": True,
                "repaired_json": repaired
            }
        except json.JSONDecodeError:
            pass
            # Try to extract JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    repaired = json.loads(json_match.group())
                    return {
                        "success": True,
                        "repaired_json": repaired
                    }
                except json.JSONDecodeError:
                    pass
            
            return {
                "success": False,
                "error": "could_not_repair",
                "original": malformed_json,
                "attempt": response
            }
    
    def convert_natural_language_to_tool_call(
        self,
        natural_language: str,
        available_tools: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert natural language response to tool call.
        
        Args:
            natural_language: Natural language response
            available_tools: Available tools
            context: Context for conversion
            
        Returns:
            Tool call or clarification request
        """
        logger.info("FunctionGemmaMediator converting natural language to tool call")
        
        request = InterpretationRequest(
            original_response=natural_language,
            context=context,
            available_tools=available_tools,
            expected_format="tool_call"
        )
        
        result = self.interpret(request)
        interpretation = result.get("interpretation", {})
        
        if interpretation.get("clarification_needed"):
            return {
                "success": False,
                "error": "clarification_needed",
                "clarification": interpretation
            }
        
        tool_call = interpretation.get("tool_call", {})
        if tool_call.get("name"):
            return {
                "success": True,
                "tool_call": tool_call,
                "confidence": interpretation.get("confidence", "medium"),
                "reasoning": interpretation.get("reasoning", "")
            }
        
        return {
            "success": False,
            "error": "could_not_convert",
            "interpretation": interpretation
        }
    
    def validate_and_fix_parameters(
        self,
        tool_call: Dict[str, Any],
        tool_definition: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate tool call parameters and fix if needed.
        
        Args:
            tool_call: Tool call to validate
            tool_definition: Tool definition with parameter schema
            context: Context for inferring missing parameters
            
        Returns:
            Validated/fixed tool call or error
        """
        logger.info(f"FunctionGemmaMediator validating parameters for {tool_call.get('name')}")
        
        tool_name = tool_call.get("name", "")
        parameters = tool_call.get("parameters", {})
        
        # Get required parameters
        param_schema = tool_definition.get("parameters", {})
        required_params = param_schema.get("required", [])
        param_properties = param_schema.get("properties", {})
        
        # Check for missing required parameters
        missing_params = [p for p in required_params if p not in parameters]
        
        if not missing_params:
            return {
                "success": True,
                "tool_call": tool_call,
                "validation": "passed"
            }
        
        # Try to infer missing parameters
        infer_prompt = f"""The tool call is missing required parameters.

Tool: {tool_name}
Current Parameters: {json.dumps(parameters, indent=2)}
Missing Required Parameters: {missing_params}

Parameter Definitions:
{json.dumps({p: param_properties.get(p, {}) for p in missing_params}, indent=2)}

Context:
{self._format_context(context)}

Please infer the missing parameters from context and return the complete tool call:
{{
    "name": "{tool_name}",
    "parameters": {{...complete parameters...}}
}}"""
        
        result = self.model_tool.execute(
            messages=[{"role": "user", "content": infer_prompt}],
            system_prompt="You are an expert at inferring missing parameters from context."
        )
        
        # Parse fixed tool call
        response = result.get("response", "")
        try:
            fixed_call = json.loads(response)
            
            # Validate fixed call has all required params
            fixed_params = fixed_call.get("parameters", {})
            still_missing = [p for p in required_params if p not in fixed_params]
            
            if not still_missing:
                return {
                    "success": True,
                    "tool_call": fixed_call,
                    "validation": "fixed",
                    "inferred_parameters": missing_params
                }
            else:
                return {
                    "success": False,
                    "error": "could_not_infer_all_parameters",
                    "still_missing": still_missing,
                    "partial_fix": fixed_call
                }
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "could_not_parse_fix",
                "missing_parameters": missing_params
            }


def create_function_gemma_mediator(model_tool) -> FunctionGemmaMediator:
    """
    Factory function to create a FunctionGemma mediator.
    
    Args:
        model_tool: ModelTool instance configured for FunctionGemma
        
    Returns:
        FunctionGemmaMediator instance
    """
    return FunctionGemmaMediator(model_tool)