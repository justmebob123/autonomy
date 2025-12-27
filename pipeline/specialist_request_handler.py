"""
Specialist Request Handler

Detects when a model requests specialist help in conversation
and routes the request to the appropriate specialist.
"""

import re
from typing import Dict, List, Optional, Any
from pathlib import Path

from .logging_setup import get_logger


class SpecialistRequestHandler:
    """
    Handles specialist requests from models during conversation.
    
    Detects phrases like:
    - "I need help with X"
    - "Can you validate this code?"
    - "Please review this for security issues"
    - "I need a specialist to check X"
    
    Routes to appropriate specialist and adds response to conversation.
    """
    
    def __init__(self, specialists: Dict[str, Any]):
        """
        Initialize handler with available specialists.
        
        Args:
            specialists: Dict mapping specialist names to specialist objects
                        e.g., {'coding': coding_specialist, 'reasoning': reasoning_specialist}
        """
        self.specialists = specialists
        self.logger = get_logger()
        
        # Patterns for detecting specialist requests
        self.request_patterns = {
            'coding': [
                r'(?:need|want|can you|please)\s+(?:help|assistance|review|validate|check)\s+(?:with\s+)?(?:the\s+)?code',
                r'(?:coding|implementation)\s+(?:help|specialist|expert)',
                r'validate\s+(?:this\s+)?(?:code|implementation)',
                r'review\s+(?:this\s+)?(?:code|implementation)',
            ],
            'reasoning': [
                r'(?:need|want|can you|please)\s+(?:help|assistance)\s+(?:with\s+)?(?:thinking|reasoning|logic|strategy)',
                r'(?:reasoning|strategic|logic)\s+(?:help|specialist|expert)',
                r'help\s+me\s+(?:think|reason|plan)',
                r'what\s+(?:should|would)\s+(?:be\s+)?(?:the\s+)?(?:best|right)\s+(?:approach|strategy)',
            ],
            'analysis': [
                r'(?:need|want|can you|please)\s+(?:help|assistance)\s+(?:with\s+)?(?:analyzing|analysis|reviewing)',
                r'(?:analysis|review)\s+(?:help|specialist|expert)',
                r'analyze\s+(?:this|the)',
                r'quick\s+(?:check|review|analysis)',
            ]
        }
    
    def detect_request(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Detect if message contains a specialist request.
        
        Args:
            message: The message to analyze
        
        Returns:
            Dict with 'specialist' and 'context' if request detected, None otherwise
        """
        message_lower = message.lower()
        
        for specialist_name, patterns in self.request_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    self.logger.info(f"  🔍 Detected request for {specialist_name} specialist")
                    return {
                        'specialist': specialist_name,
                        'context': message,
                        'pattern_matched': pattern
                    }
        
        return None
    
    def handle_request(self, request: Dict[str, Any], task_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a specialist request.
        
        Args:
            request: Request dict from detect_request()
            task_context: Context about the current task
        
        Returns:
            Dict with specialist response
        """
        specialist_name = request['specialist']
        
        if specialist_name not in self.specialists:
            self.logger.warning(f"  ⚠️ Specialist '{specialist_name}' not available")
            return {
                'success': False,
                'error': f"Specialist '{specialist_name}' not available",
                'response': f"I don't have access to a {specialist_name} specialist right now."
            }
        
        specialist = self.specialists[specialist_name]
        
        self.logger.info(f"  🤝 Consulting {specialist_name} specialist...")
        
        # Call the specialist with context
        try:
            if specialist_name == 'coding':
                result = self._consult_coding_specialist(specialist, request, task_context)
            elif specialist_name == 'reasoning':
                result = self._consult_reasoning_specialist(specialist, request, task_context)
            elif specialist_name == 'analysis':
                result = self._consult_analysis_specialist(specialist, request, task_context)
            else:
                result = {
                    'success': False,
                    'error': f"Unknown specialist type: {specialist_name}"
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"  ❌ Specialist consultation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': f"Specialist consultation failed: {e}"
            }
    
    def _consult_coding_specialist(self, specialist: Any, request: Dict, context: Dict) -> Dict:
        """Consult coding specialist."""
        # Extract relevant context
        file_path = context.get('file_path', 'unknown')
        code = context.get('code', '')
        
        # Call specialist
        result = specialist.validate_code(
            file_path=file_path,
            code=code,
            context={'request': request['context']}
        )
        
        return result
    
    def _consult_reasoning_specialist(self, specialist: Any, request: Dict, context: Dict) -> Dict:
        """Consult reasoning specialist."""
        # Extract relevant context
        question = request['context']
        
        # Call specialist
        result = specialist.reason_about(
            question=question,
            context=context
        )
        
        return result
    
    def _consult_analysis_specialist(self, specialist: Any, request: Dict, context: Dict) -> Dict:
        """Consult analysis specialist."""
        # Extract relevant context
        file_path = context.get('file_path', 'unknown')
        code = context.get('code', '')
        
        # Call specialist
        result = specialist.analyze_code(
            file_path=file_path,
            code=code,
            analysis_type='quick_check',
            context={'request': request['context']}
        )
        
        return result
    
    def format_specialist_response(self, specialist_name: str, result: Dict) -> str:
        """
        Format specialist response for inclusion in conversation.
        
        Args:
            specialist_name: Name of the specialist
            result: Result dict from specialist
        
        Returns:
            Formatted response string
        """
        if not result.get('success', False):
            return f"[{specialist_name.title()} Specialist]: Unable to help - {result.get('error', 'Unknown error')}"
        
        response = result.get('response', '')
        
        # Format as a clear specialist response
        formatted = f"[{specialist_name.title()} Specialist]:\n{response}"
        
        return formatted