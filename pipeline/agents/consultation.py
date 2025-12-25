"""
Consultation Manager

Manages multi-agent consultations for complex problems.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class ConsultationManager:
    """
    Manages consultations between multiple AI agents.
    
    Allows the primary debugging AI to consult specialists:
    - Code Analysis Specialist (deepseek-coder-v2)
    - Problem Solving Specialist (phi4 or qwen2.5:14b)
    - Tool Calling Advisor (functiongemma)
    """
    
    def __init__(self, client, config):
        """
        Initialize consultation manager.
        
        Args:
            client: OllamaClient instance
            config: PipelineConfig instance
        """
        self.client = client
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.consultation_history = []
    
    def consult_code_analyst(self, code: str, issue: Dict) -> Dict:
        """
        Consult the code analysis specialist.
        
        Args:
            code: The code to analyze
            issue: The issue description
            
        Returns:
            Analysis results
        """
        self.logger.info("  🤝 Consulting Code Analysis Specialist...")
        
        prompt = f"""Analyze this code issue from a code quality perspective:

ISSUE: {issue.get('type')} - {issue.get('message', '')}
FILE: {issue.get('filepath', 'unknown')}
LINE: {issue.get('line', 'unknown')}

CODE:
```python
{code}
```

Provide:
1. Root cause analysis
2. Code quality assessment
3. Potential side effects of fixing
4. Best practices recommendation"""
        
        messages = [
            {"role": "system", "content": "You are a senior code analyst specializing in Python code quality and debugging."},
            {"role": "user", "content": prompt}
        ]
        
        # Use deepseek-coder-v2 or best available code model
        response = self._call_specialist(messages, "code_analysis")
        
        result = {
            "specialist": "code_analyst",
            "timestamp": datetime.now().isoformat(),
            "response": response.get('content', '') if response else "No response",
            "model": response.get('model', 'unknown') if response else "unknown"
        }
        
        self.consultation_history.append(result)
        return result
    
    def consult_problem_solver(self, problem_description: str, context: Dict) -> Dict:
        """
        Consult the problem solving specialist.
        
        Args:
            problem_description: Description of the problem
            context: Additional context
            
        Returns:
            Problem solving recommendations
        """
        self.logger.info("  🤝 Consulting Problem Solving Specialist...")
        
        prompt = f"""Help solve this complex problem:

PROBLEM: {problem_description}

CONTEXT:
{self._format_context(context)}

Provide:
1. Multiple solution approaches
2. Pros and cons of each approach
3. Recommended approach with reasoning
4. Step-by-step implementation plan"""
        
        messages = [
            {"role": "system", "content": "You are a senior software engineer specializing in problem solving and system design."},
            {"role": "user", "content": prompt}
        ]
        
        # Use phi4 or qwen2.5:14b
        response = self._call_specialist(messages, "problem_solving")
        
        result = {
            "specialist": "problem_solver",
            "timestamp": datetime.now().isoformat(),
            "response": response.get('content', '') if response else "No response",
            "model": response.get('model', 'unknown') if response else "unknown"
        }
        
        self.consultation_history.append(result)
        return result
    
    def synthesize_consultations(self, consultations: List[Dict]) -> str:
        """
        Synthesize multiple consultation results into a coherent recommendation.
        
        Args:
            consultations: List of consultation results
            
        Returns:
            Synthesized recommendation
        """
        if not consultations:
            return "No consultations available"
        
        synthesis = "SPECIALIST CONSULTATIONS:\n\n"
        
        for i, consultation in enumerate(consultations, 1):
            specialist = consultation.get('specialist', 'unknown')
            response = consultation.get('response', '')
            model = consultation.get('model', 'unknown')
            
            synthesis += f"{i}. {specialist.upper()} ({model}):\n"
            synthesis += f"{response[:500]}...\n\n"
        
        synthesis += "\nBased on these consultations, proceed with the fix that addresses the root cause while maintaining code quality."
        
        return synthesis
    
    def _call_specialist(self, messages: List[Dict], specialist_type: str) -> Optional[Dict]:
        """
        Call a specialist model.
        
        Args:
            messages: List of message dicts
            specialist_type: Type of specialist (code_analysis, problem_solving)
            
        Returns:
            Response dict or None
        """
        # Determine best model for specialist type
        if specialist_type == "code_analysis":
            # Prefer deepseek-coder-v2, fallback to qwen2.5-coder
            preferred_models = ["deepseek-coder-v2", "qwen2.5-coder:14b", "qwen2.5-coder:7b"]
        elif specialist_type == "problem_solving":
            # Prefer phi4 or large qwen2.5
            preferred_models = ["phi4", "qwen2.5:14b", "llama3.1"]
        else:
            preferred_models = ["qwen2.5:14b"]
        
        # Find best available model
        selected_host = None
        selected_model = None
        
        for preferred in preferred_models:
            for host, models in self.client.available_models.items():
                for model in models:
                    if preferred.lower() in model.lower():
                        selected_host = host
                        selected_model = model
                        break
                if selected_model:
                    break
            if selected_model:
                break
        
        if not selected_host or not selected_model:
            self.logger.warning(f"No suitable model found for {specialist_type}")
            return None
        
        try:
            self.logger.debug(f"  Using {selected_model} on {selected_host} for {specialist_type}")
            response = self.client.chat(
                selected_host,
                selected_model,
                messages,
                tools=None,
                temperature=0.3,
                timeout=None  # UNLIMITED
            )
            return response
        except Exception as e:
            self.logger.error(f"Specialist call failed: {e}")
            return None
    
    def _format_context(self, context: Dict) -> str:
        """Format context dict as readable text"""
        lines = []
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                lines.append(f"- {key}: {value}")
            elif isinstance(value, list):
                lines.append(f"- {key}: {len(value)} items")
            elif isinstance(value, dict):
                lines.append(f"- {key}: {len(value)} entries")
        return "\n".join(lines)
    
    def get_consultation_summary(self) -> str:
        """Get a summary of all consultations"""
        if not self.consultation_history:
            return "No consultations performed"
        
        summary = f"CONSULTATION HISTORY ({len(self.consultation_history)} consultations):\n\n"
        
        for consultation in self.consultation_history[-5:]:  # Last 5
            specialist = consultation.get('specialist', 'unknown')
            timestamp = consultation.get('timestamp', '')
            model = consultation.get('model', 'unknown')
            
            summary += f"- {specialist} ({model}) at {timestamp}\n"
        
        return summary