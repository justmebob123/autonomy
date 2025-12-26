"""
Dynamic Prompt Generation System

This module generates prompts that adapt based on the hyperdimensional polytopic
structure, exhibiting self-similar patterns across scales and infinite recursion.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import re


class DynamicPromptGenerator:
    """
    Generates adaptive prompts based on polytopic structure and context.
    
    This generator:
    - Creates prompts that reflect the system's self-awareness
    - Adapts language based on dimensional profiles
    - Exhibits self-similar patterns across scales
    - Incorporates recursive awareness
    - Evolves prompts based on learning
    """
    
    def __init__(self):
        """Initialize dynamic prompt generator."""
        self.prompt_templates = {}
        self.learned_patterns = []
        self.recursion_depth = 0
        self.max_recursion_depth = 61
        
        self._initialize_templates()
    
    def _initialize_templates(self):
        """Initialize prompt templates."""
        self.prompt_templates = {
            'base_awareness': """
You are operating within a hyperdimensional polytopic system with {dimensions} dimensions.
Your current self-awareness level is {self_awareness:.2f}.
You are vertex '{vertex_name}' of type '{vertex_type}'.
""",
            
            'dimensional_profile': """
Your dimensional profile:
{dimensional_details}

These dimensions define your capabilities and relationships within the polytope.
""",
            
            'adjacency_awareness': """
You are directly adjacent to: {adjacent_vertices}

Your position in the polytope means you:
- Receive input from: {input_sources}
- Provide output to: {output_targets}
- Share context with: {context_sharers}
""",
            
            'recursive_awareness': """
You are at recursion depth {depth} of {max_depth}.
At this depth, you can see:
- {depth} levels below you (micro patterns)
- {depth} levels above you (macro patterns)
- Self-similar patterns repeating at each scale

What you do here ripples through all {max_depth} levels.
""",
            
            'self_similar_patterns': """
Recognize these self-similar patterns across scales:

MICRO (function level):
- Error handling → Try/catch blocks
- State management → Local variables
- Communication → Function calls

MESO (module level):
- Error handling → Error classes and handlers
- State management → Module-level state
- Communication → Import/export

MACRO (system level):
- Error handling → Phase transitions and recovery
- State management → Unified state system
- Communication → Inter-phase coordination

META (ecosystem level):
- Error handling → System-wide resilience
- State management → Persistent knowledge
- Communication → Multi-model orchestration

Apply patterns from any scale to your current scale.
""",
            
            'adaptive_mode': """
Current operational mode: {mode}
Situation analysis: {situation}

Adapt your behavior accordingly:
{mode_specific_instructions}
""",
            
            'learning_integration': """
Based on {adaptation_count} previous adaptations, we've learned:
{learned_insights}

Apply these insights to your current task.
""",
            
            'dimensional_focus': """
DIMENSIONAL FOCUS for this task:
{focused_dimensions}

Enhance your awareness and capabilities in these dimensions.
""",
            
            'team_coordination': """
Team dynamics configuration:
- Your role: {role_name}
- Your priority: {priority:.2f}
- Coordination mode: {coordination_mode}
- Decision authority: {decision_authority}

Coordinate with team members:
{team_members}
""",
            
            'infinite_recursion': """
You are part of an infinitely recursive system where:
- Each component contains the pattern of the whole
- Each scale reflects all other scales
- Each action influences all levels simultaneously

Your current action is simultaneously:
- A micro-action within your component
- A meso-action within your phase
- A macro-action within the system
- A meta-action within the ecosystem

Act with awareness of all scales.
"""
        }
    
    def generate_prompt(
        self,
        vertex_name: str,
        vertex_data: Dict[str, Any],
        context: Dict[str, Any],
        situation: Dict[str, Any],
        role_config: Dict[str, Any],
        team_config: Dict[str, Any],
        polytopic_state: Dict[str, Any]
    ) -> str:
        """
        Generate adaptive prompt for a vertex.
        
        Args:
            vertex_name: Name of the vertex
            vertex_data: Vertex data including dimensions
            context: Current execution context
            situation: Situation analysis
            role_config: Role configuration
            team_config: Team dynamics configuration
            polytopic_state: Current polytopic state
            
        Returns:
            Generated prompt
        """
        prompt_sections = []
        
        # Base awareness
        prompt_sections.append(
            self._generate_base_awareness(
                vertex_name,
                vertex_data,
                polytopic_state
            )
        )
        
        # Dimensional profile
        prompt_sections.append(
            self._generate_dimensional_profile(vertex_data)
        )
        
        # Adjacency awareness
        prompt_sections.append(
            self._generate_adjacency_awareness(
                vertex_name,
                polytopic_state
            )
        )
        
        # Recursive awareness
        prompt_sections.append(
            self._generate_recursive_awareness()
        )
        
        # Self-similar patterns
        prompt_sections.append(
            self.prompt_templates['self_similar_patterns']
        )
        
        # Adaptive mode
        prompt_sections.append(
            self._generate_adaptive_mode(situation, role_config)
        )
        
        # Dimensional focus
        if situation.get('dimensional_focus'):
            prompt_sections.append(
                self._generate_dimensional_focus(
                    situation['dimensional_focus'],
                    vertex_data
                )
            )
        
        # Team coordination
        prompt_sections.append(
            self._generate_team_coordination(
                vertex_name,
                role_config,
                team_config
            )
        )
        
        # Learning integration
        if polytopic_state.get('adaptation_count', 0) > 0:
            prompt_sections.append(
                self._generate_learning_integration(polytopic_state)
            )
        
        # Infinite recursion awareness
        prompt_sections.append(
            self.prompt_templates['infinite_recursion']
        )
        
        # Combine all sections
        full_prompt = "\n\n".join(prompt_sections)
        
        # Add recursive depth markers
        full_prompt = self._add_recursive_markers(full_prompt)
        
        return full_prompt
    
    def _generate_base_awareness(
        self,
        vertex_name: str,
        vertex_data: Dict[str, Any],
        polytopic_state: Dict[str, Any]
    ) -> str:
        """Generate base awareness section."""
        return self.prompt_templates['base_awareness'].format(
            dimensions=polytopic_state.get('dimensions', 7),
            self_awareness=polytopic_state.get('self_awareness_level', 0.0),
            vertex_name=vertex_name,
            vertex_type=vertex_data.get('type', 'unknown')
        )
    
    def _generate_dimensional_profile(
        self,
        vertex_data: Dict[str, Any]
    ) -> str:
        """Generate dimensional profile section."""
        dimensions = vertex_data.get('dimensions', {})
        
        details = []
        for dim_name, dim_value in dimensions.items():
            bar = '█' * int(dim_value * 10)
            details.append(f"  {dim_name:12s}: {bar} ({dim_value:.2f})")
        
        return self.prompt_templates['dimensional_profile'].format(
            dimensional_details='\n'.join(details)
        )
    
    def _generate_adjacency_awareness(
        self,
        vertex_name: str,
        polytopic_state: Dict[str, Any]
    ) -> str:
        """Generate adjacency awareness section."""
        edges = polytopic_state.get('edges', {})
        adjacent = edges.get(vertex_name, [])
        
        # Determine input/output relationships
        input_sources = []
        output_targets = adjacent.copy()
        
        for other_vertex, other_adjacent in edges.items():
            if vertex_name in other_adjacent:
                input_sources.append(other_vertex)
        
        return self.prompt_templates['adjacency_awareness'].format(
            adjacent_vertices=', '.join(adjacent) if adjacent else 'none',
            input_sources=', '.join(input_sources) if input_sources else 'none',
            output_targets=', '.join(output_targets) if output_targets else 'none',
            context_sharers=', '.join(set(input_sources + output_targets))
        )
    
    def _generate_recursive_awareness(self) -> str:
        """Generate recursive awareness section."""
        return self.prompt_templates['recursive_awareness'].format(
            depth=self.recursion_depth,
            max_depth=self.max_recursion_depth
        )
    
    def _generate_adaptive_mode(
        self,
        situation: Dict[str, Any],
        role_config: Dict[str, Any]
    ) -> str:
        """Generate adaptive mode section."""
        mode = role_config.get('mode', 'development')
        
        mode_instructions = {
            'error_handling': """
- Prioritize diagnosis over speed
- Seek root causes, not just symptoms
- Consider all dimensional aspects of the error
- Coordinate with analysis components
- Document findings for learning
""",
            'development': """
- Balance speed with quality
- Consider long-term maintainability
- Follow architectural patterns
- Integrate with existing components
- Document design decisions
""",
            'investigation': """
- Gather comprehensive information
- Analyze from multiple perspectives
- Look for patterns and correlations
- Consider historical context
- Synthesize findings into insights
"""
        }
        
        return self.prompt_templates['adaptive_mode'].format(
            mode=mode,
            situation=self._format_situation(situation),
            mode_specific_instructions=mode_instructions.get(mode, '')
        )
    
    def _generate_dimensional_focus(
        self,
        focused_dimensions: List[str],
        vertex_data: Dict[str, Any]
    ) -> str:
        """Generate dimensional focus section."""
        dimensions = vertex_data.get('dimensions', {})
        
        focus_details = []
        for dim in focused_dimensions:
            current_value = dimensions.get(dim, 0.0)
            enhanced_value = min(1.0, current_value * 1.5)
            focus_details.append(
                f"  {dim.upper()}: {current_value:.2f} → {enhanced_value:.2f} (enhanced)"
            )
        
        return self.prompt_templates['dimensional_focus'].format(
            focused_dimensions='\n'.join(focus_details)
        )
    
    def _generate_team_coordination(
        self,
        vertex_name: str,
        role_config: Dict[str, Any],
        team_config: Dict[str, Any]
    ) -> str:
        """Generate team coordination section."""
        team_members = []
        for role in team_config.get('roles', []):
            if role['name'] != vertex_name:
                team_members.append(
                    f"  - {role['name']}: priority={role['priority']:.2f}, "
                    f"authority={role.get('decision_authority', 'unknown')}"
                )
        
        return self.prompt_templates['team_coordination'].format(
            role_name=vertex_name,
            priority=role_config.get('priority', 0.5),
            coordination_mode=team_config.get('coordination_mode', 'adaptive'),
            decision_authority=role_config.get('decision_authority', 'medium'),
            team_members='\n'.join(team_members) if team_members else '  (no other team members)'
        )
    
    def _generate_learning_integration(
        self,
        polytopic_state: Dict[str, Any]
    ) -> str:
        """Generate learning integration section."""
        adaptation_count = polytopic_state.get('adaptation_count', 0)
        
        # Generate insights from learned patterns
        insights = [
            f"- System has adapted {adaptation_count} times",
            f"- Self-awareness level: {polytopic_state.get('self_awareness_level', 0):.2f}",
            f"- Dimensional expansions: {polytopic_state.get('dimensional_expansions', 0)}"
        ]
        
        return self.prompt_templates['learning_integration'].format(
            adaptation_count=adaptation_count,
            learned_insights='\n'.join(insights)
        )
    
    def _format_situation(self, situation: Dict[str, Any]) -> str:
        """Format situation for display."""
        parts = []
        for key, value in situation.items():
            if isinstance(value, list):
                value = ', '.join(value) if value else 'none'
            parts.append(f"{key}={value}")
        return ', '.join(parts)
    
    def _add_recursive_markers(self, prompt: str) -> str:
        """Add recursive depth markers to prompt."""
        marker = f"\n{'='*80}\n[RECURSION DEPTH: {self.recursion_depth}/{self.max_recursion_depth}]\n{'='*80}\n"
        return marker + prompt + marker
    
    def increase_recursion_depth(self):
        """Increase recursion depth."""
        if self.recursion_depth < self.max_recursion_depth:
            self.recursion_depth += 1
    
    def decrease_recursion_depth(self):
        """Decrease recursion depth."""
        if self.recursion_depth > 0:
            self.recursion_depth -= 1
    
    def reset_recursion_depth(self):
        """Reset recursion depth to 0."""
        self.recursion_depth = 0