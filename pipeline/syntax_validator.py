"""
Syntax Validator

Pre-validates generated code before writing to files to catch syntax errors early.
"""

import ast
import re
from typing import Dict, Optional, Tuple
from .logging_setup import get_logger
from .html_entity_decoder import HTMLEntityDecoder

# Polytopic Integration Imports
from pipeline.messaging.message_bus import MessageBus, Message, MessageType, MessagePriority
from pipeline.pattern_recognition import PatternRecognitionSystem
from pipeline.correlation_engine import CorrelationEngine
from pipeline.analytics.optimizer import OptimizationEngine
from pipeline.adaptive_prompts import AdaptivePromptSystem
from pipeline.polytopic.dimensional_space import DimensionalSpace



class SyntaxValidator:
    """Validates Python code syntax before file operations."""
    
    def __init__(self, project_root: str = "."):
        self.logger = get_logger()
        self.html_decoder = HTMLEntityDecoder()
        self.project_root = project_root
    
        # Polytopic Integration
        self.message_bus = MessageBus()
        self.pattern_recognition = PatternRecognitionSystem(self.project_root)
        self.correlation_engine = CorrelationEngine()
        self.optimizer = OptimizationEngine()
        self.adaptive_prompts = AdaptivePromptSystem(
            self.project_root,
            self.pattern_recognition
        )
        self.dimensional_space = DimensionalSpace()
        
        # Validation tracking
        self.validation_count = 0
        self.validator_name = 'SyntaxValidator'

    def validate_python_code(self, code: str, filepath: str = "unknown") -> Tuple[bool, Optional[str]]:
        """
        Validate Python code syntax.
        
        Args:
            code: Python code to validate
            filepath: File path for error reporting
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Skip validation for non-Python files
        if not filepath.endswith('.py'):
            return True, None
        
        if not code or not code.strip():
            return False, "Empty code content"
        
        try:
            # Try to parse the code
            ast.parse(code)
            return True, None
            
        except SyntaxError as e:
            error_msg = self._format_syntax_error(e, code, filepath)
            return False, error_msg
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def _format_syntax_error(self, error: SyntaxError, code: str, filepath: str) -> str:
        """Format syntax error with context."""
        lines = code.split('\n')
        
        error_line = error.lineno if error.lineno else 0
        error_col = error.offset if error.offset else 0
        
        # Get context lines
        start = max(0, error_line - 3)
        end = min(len(lines), error_line + 2)
        
        context = []
        for i in range(start, end):
            line_num = i + 1
            marker = ">>>" if line_num == error_line else "   "
            context.append(f"{marker} {line_num:4d}: {lines[i]}")
        
        # Add column pointer if available
        if error_col > 0 and error_line > 0:
            pointer = " " * (error_col + 10) + "^"
            context.append(pointer)
        
        error_msg = f"""Syntax error in {filepath}:
Line {error_line}: {error.msg}
{chr(10).join(context)}
"""
        return error_msg
    
    def fix_common_syntax_errors(self, code: str, filepath: str = "unknown") -> str:
        """
        Attempt to fix common syntax errors automatically.
        
        Args:
            code: Python code with potential errors
            filepath: File path for language detection
            
        Returns:
            Fixed code (or original if no fixes applied)
        """
        original_code = code
        
        # Fix 0: CRITICAL - Decode HTML entities (HTTP transport artifact)
        # The decoder is context-aware and handles backslash escaping internally
        code, was_decoded = self.html_decoder.decode_html_entities(code, filepath)
        
        # Verify no entities remain
        is_clean, remaining_entities = self.html_decoder.validate_no_entities(code)
        if not is_clean:
            self.logger.warning(f"⚠️  HTML entities still present after decoding: {remaining_entities[:3]}")
        
        # Fix 1: Remove duplicate imports on same line
        # Example: "time from datetime import datetime" -> "from datetime import datetime"
        # Also fixes: "import from typing" -> "from typing"
        code = re.sub(r'\b\w+\s+(from\s+\w+\s+import\s+)', r'\1', code)
        code = re.sub(r'\bimport\s+(from\s+)', r'\1', code)
        
        # Fix 2: Fix malformed string literals in descriptions
        # Example: 'description": "text' -> 'description": "text"'
        code = re.sub(r'(description["\']:[\s]*["\'])([^"\']*?)(["\'],)', r'\1\2\3', code)
        
        # Fix 3: Remove trailing commas in function calls
        code = re.sub(r',(\s*\))', r'\1', code)
        
        # Fix 4: Fix indentation issues (convert tabs to spaces)
        code = code.replace('\t', '    ')
        
        # Fix 5: Remove multiple consecutive blank lines
        code = re.sub(r'\n\n\n+', '\n\n', code)
        
        # Fix 6: Fix escaped triple quotes (common after HTML entity decoding)
        # Example: """ -> """
        code = code.replace(r'"""', '"""')
        code = code.replace(r"\'\'\'", "'''")
        
        if code != original_code:
            self.logger.info("Applied automatic syntax fixes")
        
        return code
    
    def validate_and_fix(self, code: str, filepath: str = "unknown") -> Tuple[bool, str, Optional[str]]:
        """
        Validate code and attempt to fix if invalid.
        
        Args:
            code: Python code to validate
            filepath: File path for error reporting
            
        Returns:
            Tuple of (is_valid, fixed_code, error_message)
        """
        # First try validation
        is_valid, error = self.validate_python_code(code, filepath)
        
        if is_valid:
            return True, code, None
        
        # Try to fix common errors
        self.logger.warning(f"Syntax error detected in {filepath}, attempting auto-fix...")
        fixed_code = self.fix_common_syntax_errors(code, filepath)
        
        # Validate fixed code
        is_valid, error = self.validate_python_code(fixed_code, filepath)
        
        if is_valid:
            self.logger.info(f"Successfully fixed syntax errors in {filepath}")
            return True, fixed_code, None
        else:
            return False, code, error
    
    def _publish_validation_event(self, event_type: str, payload: dict):
        """Publish validation events using existing message types."""
        message_type_map = {
            'validation_started': MessageType.SYSTEM_INFO,
            'validation_completed': MessageType.SYSTEM_INFO,
            'validation_error': MessageType.SYSTEM_WARNING,
            'validation_critical': MessageType.SYSTEM_ALERT,
            'validation_insight': MessageType.SYSTEM_INFO,
        }
        
        message_type = message_type_map.get(event_type, MessageType.SYSTEM_INFO)
        
        message = Message(
            sender=self.validator_name,
            recipient='ALL',
            message_type=message_type,
            priority=MessagePriority.NORMAL,
            payload={
                'event': event_type,
                'validator': self.validator_name,
                **payload
            }
        )
        
        self.message_bus.publish(message)
    
    def _record_validation_pattern(self, errors: list):
        """Record validation patterns for learning."""
        if not errors:
            return
        
        # Record execution data
        execution_data = {
            'phase': 'validation',
            'tool': self.validator_name,
            'success': len([e for e in errors if self._get_severity(e) == 'high']) == 0,
            'error_count': len(errors),
            'validation_count': self.validation_count
        }
        
        self.pattern_recognition.record_execution(execution_data)
        
        # Add findings to correlation engine
        for error in errors:
            component = self._get_error_file(error)
            finding = {
                'type': f'{self.validator_name}_error',
                'error_type': self._get_error_type(error),
                'severity': self._get_severity(error),
                'message': self._get_error_message(error)
            }
            
            self.correlation_engine.add_finding(component, finding)
        
        # Find correlations
        correlations = self.correlation_engine.correlate()
        
        if correlations:
            self._publish_validation_event('validation_insight', {
                'type': 'validation_correlations',
                'correlations': correlations
            })
    
    def _optimize_validation(self, result: dict):
        """Optimize validation based on results."""
        # Record quality metrics
        self.optimizer.record_quality_metric(
            f'{self.validator_name}_errors',
            result.get('total_errors', 0)
        )
        
        if 'by_severity' in result:
            self.optimizer.record_quality_metric(
                f'{self.validator_name}_high_severity',
                result.get('by_severity', {}).get('high', 0)
            )
    
    def _get_error_file(self, error):
        """Extract file path from error."""
        if isinstance(error, dict):
            return error.get('file', 'unknown')
        elif hasattr(error, 'file'):
            return error.file
        elif hasattr(error, 'filepath'):
            return error.filepath
        return 'unknown'
    
    def _get_error_type(self, error):
        """Extract error type from error."""
        if isinstance(error, dict):
            return error.get('error_type', 'unknown')
        elif hasattr(error, 'error_type'):
            return error.error_type
        elif hasattr(error, 'type'):
            return error.type
        return 'unknown'
    
    def _get_severity(self, error):
        """Extract severity from error."""
        if isinstance(error, dict):
            return error.get('severity', 'medium')
        elif hasattr(error, 'severity'):
            return error.severity
        return 'medium'
    
    def _get_error_message(self, error):
        """Extract message from error."""
        if isinstance(error, dict):
            return error.get('message', '')
        elif hasattr(error, 'message'):
            return error.message
        elif hasattr(error, 'msg'):
            return error.msg
        return str(error)

