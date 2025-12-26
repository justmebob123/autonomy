"""
Tool Design Phase with Intelligent Analysis

Analyzes existing tools before creating new ones to prevent duplication
and recommend abstractions.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import json

from .base import BasePhase, PhaseResult
from .loop_detection_mixin import LoopDetectionMixin
from ..state.manager import PipelineState
from ..config import PipelineConfig
from ..client import OllamaClient
from ..prompts.tool_designer import get_tool_designer_prompt
from ..tools import get_tools_for_phase
from ..tool_analyzer import ToolAnalyzer, ToolAnalysisResult


class ToolDesignPhase(LoopDetectionMixin, BasePhase):
    """
    Phase for designing custom tools with intelligent analysis.
    
    Features:
    - Analyzes existing tools before creating new ones
    - Detects duplicates and similarities
    - Recommends tool abstractions
    - Suggests modifications to existing tools
    - Comprehensive logging and audit trail
    
    Process:
    1. Receive tool request with context
    2. Analyze existing tools for similarities
    3. Determine if new tool needed or existing can be used/modified
    4. If new tool needed, design specification and implementation
    5. Validate safety and register tool
    6. Make available to all phases
    """
    
    phase_name = "tool_design"
    
    def __init__(self, config: PipelineConfig, client: OllamaClient):
        BasePhase.__init__(self, config, client)
        self.init_loop_detection()
        
        # Initialize tool analyzer
        self.tool_analyzer = ToolAnalyzer(
            handlers_path=str(Path(__file__).parent.parent / "handlers.py"),
            custom_tools_dir=str(Path(__file__).parent.parent / "tools" / "custom")
        )
        
        self.logger.info("Enhanced ToolDesignPhase initialized with ToolAnalyzer")
    
    def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
        """
        Execute enhanced tool design phase with intelligent analysis.
        
        Args:
            state: Current pipeline state
            **kwargs: Context parameters including:
                - tool_name: Name of requested tool
                - tool_description: What the tool should do
                - parameters: Expected parameters
                - usage_context: How the tool will be used
                - error_details: Details if triggered by unknown tool error
                
        Returns:
            PhaseResult with success status and analysis results
        """
        # Extract context parameters
        tool_name = kwargs.get('tool_name')
        tool_description = kwargs.get('tool_description', '')
        parameters = kwargs.get('parameters', {})
        usage_context = kwargs.get('usage_context', '')
        error_details = kwargs.get('error_details', {})
        
        if not tool_name:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="No tool name provided for tool design"
            )
        
        self.logger.info(f"🔧 Enhanced tool design for: {tool_name}")
        self.logger.info(f"   Description: {tool_description}")
        self.logger.info(f"   Parameters: {parameters}")
        
        # Step 1: Analyze existing tools
        self.logger.info("📊 Analyzing existing tools for similarities...")
        
        analysis_context = {
            'description': tool_description,
            'parameters': parameters,
            'usage': usage_context
        }
        
        analysis: ToolAnalysisResult = self.tool_analyzer.analyze_tool_request(
            tool_name, analysis_context
        )
        
        # Log analysis results
        self._log_analysis_results(analysis)
        
        # Step 2: Handle based on analysis
        if analysis.exists:
            return self._handle_existing_tool(tool_name, analysis, state)
        
        elif analysis.should_modify_existing:
            return self._handle_modify_existing(tool_name, analysis, state, kwargs)
        
        elif analysis.should_abstract:
            return self._handle_abstraction(tool_name, analysis, state, kwargs)
        
        elif analysis.should_create_new:
            return self._handle_create_new(tool_name, analysis, state, kwargs)
        
        else:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="Unable to determine appropriate action from analysis",
                data={'analysis': self._analysis_to_dict(analysis)}
            )
    
    def _log_analysis_results(self, analysis: ToolAnalysisResult):
        """Log detailed analysis results."""
        self.logger.info("=" * 70)
        self.logger.info("TOOL ANALYSIS RESULTS")
        self.logger.info("=" * 70)
        
        if analysis.exists:
            self.logger.info(f"✓ Tool exists: {analysis.existing_tool_name}")
        else:
            self.logger.info("✗ Tool does not exist")
        
        self.logger.info(f"Create new: {analysis.should_create_new}")
        self.logger.info(f"Modify existing: {analysis.should_modify_existing}")
        self.logger.info(f"Abstract: {analysis.should_abstract}")
        
        if analysis.similar_tools:
            self.logger.info(f"\nFound {len(analysis.similar_tools)} similar tools:")
            for sim in analysis.similar_tools[:3]:
                self.logger.info(f"  • {sim.tool2}: {sim.similarity_score:.2%} similar")
                self.logger.info(f"    {sim.recommendation}")
        
        self.logger.info("\nRecommendations:")
        for rec in analysis.recommendations:
            self.logger.info(f"  • {rec}")
        
        self.logger.info("=" * 70)
    
    def _handle_existing_tool(self, tool_name: str, analysis: ToolAnalysisResult,
                             state: PipelineState) -> PhaseResult:
        """Handle case where tool already exists."""
        self.logger.info(f"✓ Tool '{analysis.existing_tool_name}' already exists - no action needed")
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message=f"Tool '{analysis.existing_tool_name}' already exists",
            data={
                'action': 'use_existing',
                'existing_tool': analysis.existing_tool_name,
                'recommendations': analysis.recommendations
            }
        )
    
    def _handle_modify_existing(self, tool_name: str, analysis: ToolAnalysisResult,
                               state: PipelineState, kwargs: Dict) -> PhaseResult:
        """Handle case where existing tool should be modified."""
        self.logger.info(f"🔄 Modifying existing tool: {analysis.existing_tool_name}")
        
        # Get the existing tool to modify
        existing_tool = analysis.similar_tools[0].tool2
        
        # Create modification prompt
        modification_prompt = self._create_modification_prompt(
            existing_tool, tool_name, kwargs
        )
        
        # Use AI to generate modifications
        result = self._execute_tool_creation(
            modification_prompt,
            f"Modify {existing_tool} to support {tool_name}",
            state,
            kwargs
        )
        
        if result.success:
            result.data['action'] = 'modified_existing'
            result.data['original_tool'] = existing_tool
            result.data['analysis'] = self._analysis_to_dict(analysis)
        
        return result
    
    def _handle_abstraction(self, tool_name: str, analysis: ToolAnalysisResult,
                           state: PipelineState, kwargs: Dict) -> PhaseResult:
        """Handle case where abstraction is recommended."""
        self.logger.info(f"🎯 Creating abstraction for multiple similar tools")
        
        similar_tools = [s.tool2 for s in analysis.similar_tools[:3]]
        self.logger.info(f"   Abstracting: {', '.join(similar_tools)}")
        
        # Create abstraction prompt
        abstraction_prompt = self._create_abstraction_prompt(
            tool_name, similar_tools, kwargs
        )
        
        # Use AI to generate abstraction
        result = self._execute_tool_creation(
            abstraction_prompt,
            f"Create abstraction for {tool_name} and similar tools",
            state,
            kwargs
        )
        
        if result.success:
            result.data['action'] = 'created_abstraction'
            result.data['abstracted_tools'] = similar_tools
            result.data['analysis'] = self._analysis_to_dict(analysis)
        
        return result
    
    def _handle_create_new(self, tool_name: str, analysis: ToolAnalysisResult,
                          state: PipelineState, kwargs: Dict) -> PhaseResult:
        """Handle case where new tool should be created."""
        self.logger.info(f"✨ Creating new tool: {tool_name}")
        
        if analysis.similar_tools:
            self.logger.info(f"   Note: {len(analysis.similar_tools)} similar tools exist")
            for sim in analysis.similar_tools[:2]:
                self.logger.info(f"   • {sim.tool2}: {sim.similarity_score:.2%} similar")
        
        # Create standard tool design prompt
        tool_description = kwargs.get('tool_description', '')
        creation_prompt = get_tool_designer_prompt(tool_description)
        
        # Use AI to generate new tool
        result = self._execute_tool_creation(
            creation_prompt,
            f"Design a tool for: {tool_description}",
            state,
            kwargs
        )
        
        if result.success:
            result.data['action'] = 'created_new'
            result.data['analysis'] = self._analysis_to_dict(analysis)
        
        return result
    
    def _create_modification_prompt(self, existing_tool: str, new_tool: str,
                                   kwargs: Dict) -> str:
        """Create prompt for modifying existing tool."""
        tool_description = kwargs.get('tool_description', '')
        parameters = kwargs.get('parameters', {})
        
        return f"""You are a tool modification expert. Your task is to modify an existing tool to support a new use case.

EXISTING TOOL: {existing_tool}
NEW REQUIREMENT: {new_tool}
DESCRIPTION: {tool_description}
REQUIRED PARAMETERS: {json.dumps(parameters, indent=2)}

INSTRUCTIONS:
1. Analyze the existing tool '{existing_tool}'
2. Determine what modifications are needed to support the new use case
3. Create a modified version that:
   - Maintains backward compatibility with existing usage
   - Adds support for the new use case
   - Uses a more general/abstract design if appropriate
   - Follows best practices for tool design

4. Use the create_file tool to save:
   - Modified tool implementation in pipeline/tools/custom/{new_tool}.py
   - Tool specification in pipeline/tools/custom/{new_tool}_spec.json

The specification must include:
- name: Tool name
- description: What the tool does
- parameters: Parameter specifications
- security_level: safe/restricted/dangerous
- version: Version number
- replaces: [{existing_tool}] (list of tools this replaces/extends)
"""
    
    def _create_abstraction_prompt(self, new_tool: str, similar_tools: list,
                                  kwargs: Dict) -> str:
        """Create prompt for creating tool abstraction."""
        tool_description = kwargs.get('tool_description', '')
        parameters = kwargs.get('parameters', {})
        
        return f"""You are a tool abstraction expert. Your task is to create a general tool that handles multiple similar use cases.

NEW TOOL: {new_tool}
DESCRIPTION: {tool_description}
SIMILAR EXISTING TOOLS: {', '.join(similar_tools)}
REQUIRED PARAMETERS: {json.dumps(parameters, indent=2)}

INSTRUCTIONS:
1. Analyze the similar tools: {', '.join(similar_tools)}
2. Identify common patterns and functionality
3. Create a general abstraction that:
   - Handles all the use cases of the similar tools
   - Supports the new use case as well
   - Uses a clean, flexible design
   - Reduces code duplication
   - Follows best practices

4. Use the create_file tool to save:
   - Abstracted tool implementation in pipeline/tools/custom/{new_tool}.py
   - Tool specification in pipeline/tools/custom/{new_tool}_spec.json

The specification must include:
- name: Tool name
- description: What the tool does (mention it's an abstraction)
- parameters: Parameter specifications (should be flexible)
- security_level: safe/restricted/dangerous
- version: Version number
- abstracts: [{', '.join(similar_tools)}] (list of tools this abstracts)
"""
    
    def _execute_tool_creation(self, system_prompt: str, user_message: str,
                              state: PipelineState, kwargs: Dict) -> PhaseResult:
        """Execute the actual tool creation with AI."""
        # Get tools for this phase
        tools = get_tools_for_phase(self.phase_name, self.tool_registry)
        
        # Ensure create_file tool is available
        create_file_tool = {
            "type": "function",
            "function": {
                "name": "create_file",
                "description": "Create a new file with content",
                "parameters": {
                    "type": "object",
                    "required": ["filepath", "content"],
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "Path to the file to create (relative to project root)"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file"
                        }
                    }
                }
            }
        }
        
        if not any(t.get("function", {}).get("name") == "create_file" for t in tools):
            tools.append(create_file_tool)
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # Call the AI
        self.logger.info("🤖 Calling AI for tool creation...")
        response = self.chat(messages, tools, task_type="tool_design")
        
        if "error" in response:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"AI call failed: {response['error']}"
            )
        
        # Parse response
        tool_calls, text_response = self.parser.parse_response(response, tools)
        
        if not tool_calls:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="AI did not make any tool calls to create the tool",
                data={"response": text_response}
            )
        
        # Check for loops
        if self.check_for_loops():
            self.logger.warning("  Loop detected in tool design phase")
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="Loop detected - stopping to prevent infinite cycle"
            )
        
        # Process tool calls
        from ..handlers import ToolCallHandler
        handler = ToolCallHandler(
            self.project_dir,
            verbose=self.config.verbose,
            tool_registry=self.tool_registry
        )
        results = handler.process_tool_calls(tool_calls)
        
        # Track for loop detection
        self.track_tool_calls(tool_calls, results)
        
        # Check if tool files were created
        created_files = [r.get("filepath") for r in results if r.get("success")]
        
        if not created_files:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="Failed to create tool files",
                data={"results": results}
            )
        
        # Find spec and implementation files
        spec_file = None
        impl_file = None
        
        for filepath in created_files:
            if filepath.endswith('_spec.json'):
                spec_file = filepath
            elif filepath.endswith('.py'):
                impl_file = filepath
        
        if not spec_file or not impl_file:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="Missing spec file or implementation file",
                files_created=created_files
            )
        
        # Load and register the tool
        try:
            full_spec_path = self.project_dir / spec_file
            
            if full_spec_path.exists():
                with open(full_spec_path, 'r') as f:
                    spec = json.load(f)
                
                # Register with ToolRegistry
                if self.tool_registry.register_tool(spec):
                    self.logger.info(f"✅ Successfully registered tool: {spec['name']}")
                    
                    return PhaseResult(
                        success=True,
                        phase=self.phase_name,
                        message=f"Created and registered tool: {spec['name']}",
                        files_created=created_files,
                        data={
                            "tool_name": spec['name'],
                            "description": spec.get('description', ''),
                            "category": spec.get('category', 'unknown'),
                            "spec_file": spec_file,
                            "impl_file": impl_file
                        }
                    )
                else:
                    return PhaseResult(
                        success=False,
                        phase=self.phase_name,
                        message="Tool files created but registration failed",
                        files_created=created_files
                    )
            else:
                return PhaseResult(
                    success=False,
                    phase=self.phase_name,
                    message=f"Tool spec file not found: {spec_file}"
                )
        
        except Exception as e:
            self.logger.error(f"Error registering tool: {e}")
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Error registering tool: {e}",
                files_created=created_files
            )
    
    def _analysis_to_dict(self, analysis: ToolAnalysisResult) -> Dict:
        """Convert analysis result to dictionary for serialization."""
        return {
            'exists': analysis.exists,
            'should_create_new': analysis.should_create_new,
            'should_modify_existing': analysis.should_modify_existing,
            'should_abstract': analysis.should_abstract,
            'recommendations': analysis.recommendations,
            'existing_tool_name': analysis.existing_tool_name,
            'similar_tools': [
                {
                    'tool': sim.tool2,
                    'similarity': sim.similarity_score,
                    'recommendation': sim.recommendation
                }
                for sim in analysis.similar_tools
            ]
        }
    
    def generate_state_markdown(self, state: PipelineState) -> str:
        """Generate markdown state file for this phase."""
        phase_state = state.phases.get(self.phase_name)
        
        md = f"""# Tool Design Phase State

## Statistics
- Runs: {phase_state.run_count if phase_state else 0}
- Successes: {phase_state.success_count if phase_state else 0}
- Failures: {phase_state.failure_count if phase_state else 0}

## Tool Analysis Statistics
"""
        
        # Get tool statistics from analyzer
        stats = self.tool_analyzer.get_tool_statistics()
        md += f"""
- Total Tools: {stats['total_tools']}
- Built-in Tools: {stats['builtin_tools']}
- Custom Tools: {stats['custom_tools']}

## Registered Tools
"""
        
        # List registered tools
        if hasattr(self, 'tool_registry'):
            tools = self.tool_registry.list_tools()
            if tools:
                by_category = {}
                for tool in tools:
                    category = tool.get('category', 'unknown')
                    if category not in by_category:
                        by_category[category] = []
                    by_category[category].append(tool)
                
                for category, category_tools in sorted(by_category.items()):
                    md += f"\n### {category.title()}\n"
                    for tool in category_tools:
                        md += f"\n#### {tool['name']}\n"
                        md += f"- **Description**: {tool['description']}\n"
                        md += f"- **Version**: {tool.get('version', '1.0')}\n"
                        
                        if 'replaces' in tool:
                            md += f"- **Replaces**: {', '.join(tool['replaces'])}\n"
                        if 'abstracts' in tool:
                            md += f"- **Abstracts**: {', '.join(tool['abstracts'])}\n"
            else:
                md += "\nNo tools registered yet.\n"
        
        return md