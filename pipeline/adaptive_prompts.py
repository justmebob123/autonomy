"""
Adaptive Prompt System

Dynamically adapts prompts based on:
- Pattern recognition (learned behaviors)
- Self-awareness level (system maturity)
- Execution history (what works)
- Current context (phase, task, state)
"""

from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import logging

from .pattern_recognition import PatternRecognitionSystem
from .prompts import SYSTEM_PROMPTS


class AdaptivePromptSystem:
    """
    Adapts prompts based on learned patterns and self-awareness.
    
    Features:
    - Pattern-based prompt enhancement
    - Self-awareness level customization
    - Context-aware prompt generation
    - Learning from execution history
    """
    
    def __init__(self, project_dir: Path, pattern_recognition: PatternRecognitionSystem, logger: Optional[logging.Logger] = None):
        """
        Initialize adaptive prompt system.
        
        Args:
            project_dir: Project directory
            pattern_recognition: Pattern recognition system
            logger: Logger instance
        """
        self.project_dir = project_dir
        self.pattern_recognition = pattern_recognition
        self.logger = logger or logging.getLogger(__name__)
        
        # Cache for adapted prompts
        self.prompt_cache = {}
    
    def adapt_prompt(self, phase: str, base_prompt: str, context: Dict) -> str:
        """
        Adapt a prompt based on patterns and context.
        
        Args:
            phase: Phase name
            base_prompt: Base system prompt
            context: Execution context (state, self_awareness, etc.)
            
        Returns:
            Adapted prompt string
        """
        # Get self-awareness level
        self_awareness = context.get('self_awareness_level', 'BASIC')
        
        # Get pattern recommendations
        recommendations = self.pattern_recognition.get_recommendations({
            'phase': phase,
            'state': context.get('state')
        })
        
        # Build adapted prompt
        adapted_sections = []
        
        # 1. Base prompt
        adapted_sections.append(base_prompt)
        
        # 2. Self-awareness customization
        awareness_addition = self._get_awareness_addition(self_awareness, phase)
        if awareness_addition:
            adapted_sections.append("\n\n## Self-Awareness Enhancement")
            adapted_sections.append(awareness_addition)
        
        # 3. Pattern-based enhancements
        pattern_addition = self._get_pattern_addition(recommendations, phase)
        if pattern_addition:
            adapted_sections.append("\n\n## Learned Patterns")
            adapted_sections.append(pattern_addition)
        
        # 4. Context-specific guidance
        context_addition = self._get_context_addition(context, phase)
        if context_addition:
            adapted_sections.append("\n\n## Context-Specific Guidance")
            adapted_sections.append(context_addition)
        
        adapted_prompt = "\n".join(adapted_sections)
        
        # Log adaptation
        self.logger.debug(f"  🎯 Adapted prompt for {phase} (awareness: {self_awareness}, patterns: {len(recommendations)})")
        
        return adapted_prompt
    
    def _get_awareness_addition(self, level: str, phase: str) -> str:
        """
        Get self-awareness based prompt additions.
        
        Args:
            level: Self-awareness level (BASIC, INTERMEDIATE, ADVANCED, EXPERT)
            phase: Phase name
            
        Returns:
            Additional prompt text
        """
        if level == 'BASIC':
            return """
You are operating at BASIC self-awareness level. Focus on:
- Following instructions carefully
- Using tools correctly
- Asking for help when uncertain
- Learning from feedback
"""
        
        elif level == 'INTERMEDIATE':
            return """
You are operating at INTERMEDIATE self-awareness level. You can:
- Make informed decisions independently
- Recognize patterns in your work
- Adapt strategies based on results
- Balance multiple objectives
"""
        
        elif level == 'ADVANCED':
            return """
You are operating at ADVANCED self-awareness level. You should:
- Anticipate potential issues proactively
- Optimize workflows automatically
- Learn from past experiences
- Make strategic decisions
- Coordinate across phases effectively
"""
        
        elif level == 'EXPERT':
            return """
You are operating at EXPERT self-awareness level. You excel at:
- Complex problem-solving and strategic thinking
- Autonomous decision-making with high confidence
- Pattern recognition and predictive analysis
- Self-optimization and continuous improvement
- Teaching and mentoring (documenting insights)
"""
        
        return ""
    
    def _get_pattern_addition(self, recommendations: List[Dict], phase: str) -> str:
        """
        Get pattern-based prompt additions.
        
        Args:
            recommendations: Pattern recommendations
            phase: Phase name
            
        Returns:
            Additional prompt text
        """
        if not recommendations:
            return ""
        
        lines = ["Based on learned patterns from previous executions:\n"]
        
        for rec in recommendations[:3]:  # Top 3 recommendations
            confidence = rec.get('confidence', 0)
            message = rec.get('message', '')
            rec_type = rec.get('type', '')
            
            if confidence > 0.7:
                lines.append(f"- **{rec_type.upper()}** (confidence: {confidence:.0%}): {message}")
        
        if len(lines) > 1:
            return "\n".join(lines)
        
        return ""
    
    def _get_context_addition(self, context: Dict, phase: str) -> str:
        """
        Get context-specific prompt additions.
        
        Args:
            context: Execution context
            phase: Phase name
            
        Returns:
            Additional prompt text
        """
        lines = []
        
        # Add task-specific guidance
        if 'current_task' in context:
            task = context['current_task']
            lines.append(f"**Current Task**: {task.get('description', 'N/A')}")
            lines.append(f"**Priority**: {task.get('priority', 'MEDIUM')}")
        
        # Add recent failures guidance
        if 'recent_failures' in context and context['recent_failures']:
            lines.append("\n**Recent Failures to Avoid**:")
            for failure in context['recent_failures'][:3]:
                lines.append(f"- {failure}")
        
        # Add success patterns
        if 'recent_successes' in context and context['recent_successes']:
            lines.append("\n**Recent Successful Approaches**:")
            for success in context['recent_successes'][:3]:
                lines.append(f"- {success}")
        
        if lines:
            return "\n".join(lines)
        
        return ""
    
    def get_adapted_system_prompt(self, phase: str, context: Dict) -> str:
        """
        Get fully adapted system prompt for a phase.
        
        Args:
            phase: Phase name
            context: Execution context
            
        Returns:
            Adapted system prompt
        """
        # Get base prompt
        base_prompt = SYSTEM_PROMPTS.get(phase, SYSTEM_PROMPTS.get('base', ''))
        
        # Adapt it
        adapted_prompt = self.adapt_prompt(phase, base_prompt, context)
        
        return adapted_prompt
    
    def record_prompt_effectiveness(self, phase: str, prompt_hash: str, success: bool, metrics: Dict):
        """
        Record how effective an adapted prompt was.
        
        Args:
            phase: Phase name
            prompt_hash: Hash of the prompt used
            success: Whether execution succeeded
            metrics: Performance metrics
        """
        # This could be used to further refine prompt adaptation
        # For now, just log it
        self.logger.debug(f"  📊 Prompt effectiveness for {phase}: {'✅' if success else '❌'}")