"""
Add full polytopic integration to dict_structure_validator.py

This adds:
1. Message bus integration for validation events
2. Pattern recognition for common error patterns
3. Correlation engine for error relationships
4. Optimizer for validation improvements
5. Dimension tracking for validation metrics
6. Adaptive prompts based on validation patterns
"""

import sys
sys.path.insert(0, '.')
from pathlib import Path

def integrate_dict_validator():
    """Add polytopic integration to dict_structure_validator.py"""
    
    validator_path = Path('pipeline/analysis/dict_structure_validator.py')
    
    with open(validator_path, 'r') as f:
        content = f.read()
    
    # Check if already integrated
    if 'MessageBus' in content and 'PatternRecognition' in content:
        print("✅ dict_structure_validator.py already has polytopic integration")
        return
    
    # Add imports at the top (after existing imports)
    import_section = '''
# Polytopic Integration Imports
from pipeline.message_bus import MessageBus, Message, MessageType, MessagePriority
from pipeline.pattern_recognition import PatternRecognition
from pipeline.correlation_engine import CorrelationEngine
from pipeline.analytics.optimizer import Optimizer
from pipeline.adaptive_prompts import AdaptivePrompts
from pipeline.polytopic.dimensional_space import DimensionTracker
'''
    
    # Find the end of imports
    import_end = content.find('class DictStructureValidator:')
    if import_end == -1:
        print("❌ Could not find class definition")
        return
    
    # Insert imports before class
    content = content[:import_end] + import_section + '\n\n' + content[import_end:]
    
    # Add polytopic attributes to __init__
    init_additions = '''
        
        # Polytopic Integration
        self.message_bus = MessageBus()
        self.pattern_recognition = PatternRecognition()
        self.correlation_engine = CorrelationEngine()
        self.optimizer = Optimizer()
        self.adaptive_prompts = AdaptivePrompts()
        self.dimension_tracker = DimensionTracker()
        
        # Subscribe to validation events
        self.message_bus.subscribe(MessageType.VALIDATION_REQUESTED, self._on_validation_requested)
        self.message_bus.subscribe(MessageType.CODE_CHANGED, self._on_code_changed)
'''
    
    # Find __init__ method and add after self.instance_vars line
    init_marker = "self.instance_vars: Dict[str, Dict[str, Dict]] = {}"
    if init_marker in content:
        content = content.replace(
            init_marker,
            init_marker + init_additions
        )
    else:
        print("⚠️  Could not find __init__ marker, trying alternative")
        # Try alternative marker
        init_marker = "def __init__(self, project_root: str):"
        if init_marker in content:
            # Find the end of __init__ (next method or class end)
            init_start = content.find(init_marker)
            next_def = content.find('\n    def ', init_start + len(init_marker))
            if next_def != -1:
                content = content[:next_def] + init_additions + '\n' + content[next_def:]
    
    # Add event handlers
    event_handlers = '''
    
    def _on_validation_requested(self, message: Message):
        """Handle validation request events."""
        if message.payload.get('validator_type') == 'dict_structure':
            result = self.validate_all()
            
            # Publish validation result
            self.message_bus.publish(Message(
                sender='DictStructureValidator',
                recipient='ValidationOrchestrator',
                message_type=MessageType.VALIDATION_COMPLETED,
                priority=MessagePriority.HIGH,
                payload={
                    'validator': 'dict_structure',
                    'result': result,
                    'timestamp': message.payload.get('timestamp')
                }
            ))
    
    def _on_code_changed(self, message: Message):
        """Handle code change events - validate changed files."""
        changed_files = message.payload.get('files', [])
        
        # Validate only changed files
        errors = []
        for file_path in changed_files:
            if file_path.endswith('.py'):
                file_errors = self._validate_file(Path(file_path))
                errors.extend(file_errors)
        
        if errors:
            # Publish validation errors
            self.message_bus.publish(Message(
                sender='DictStructureValidator',
                recipient='ALL',
                message_type=MessageType.VALIDATION_ERROR,
                priority=MessagePriority.HIGH,
                payload={
                    'validator': 'dict_structure',
                    'errors': errors,
                    'file_count': len(changed_files)
                }
            ))
    
    def _record_validation_pattern(self, errors: list):
        """Record validation patterns for learning."""
        if not errors:
            return
        
        # Extract patterns from errors
        for error in errors:
            pattern = {
                'error_type': error['error_type'],
                'severity': error['severity'],
                'variable': error['variable'],
                'key_path': error['key_path'],
                'file': error['file']
            }
            
            # Record pattern
            self.pattern_recognition.record_pattern(
                pattern_type='dict_validation_error',
                pattern_data=pattern,
                context={'validator': 'dict_structure'}
            )
        
        # Find correlations
        correlations = self.correlation_engine.find_correlations(
            'dict_validation_errors',
            [e['file'] for e in errors]
        )
        
        if correlations:
            # Publish correlation insights
            self.message_bus.publish(Message(
                sender='DictStructureValidator',
                recipient='ALL',
                message_type=MessageType.INSIGHT_DISCOVERED,
                priority=MessagePriority.MEDIUM,
                payload={
                    'type': 'validation_correlations',
                    'correlations': correlations,
                    'validator': 'dict_structure'
                }
            ))
    
    def _optimize_validation(self, result: dict):
        """Optimize validation based on results."""
        # Track validation metrics
        self.dimension_tracker.record_metric(
            dimension='validation_quality',
            metric='dict_structure_errors',
            value=result['total_errors']
        )
        
        self.dimension_tracker.record_metric(
            dimension='validation_quality',
            metric='dict_structure_high_severity',
            value=result['by_severity']['high']
        )
        
        # Get optimization suggestions
        optimization = self.optimizer.optimize(
            'dict_structure_validation',
            {
                'total_errors': result['total_errors'],
                'by_severity': result['by_severity'],
                'structures_analyzed': result['structures_analyzed']
            }
        )
        
        if optimization.get('suggestions'):
            # Update adaptive prompts
            self.adaptive_prompts.update_from_optimization(
                'dict_structure_validation',
                optimization['suggestions']
            )
'''
    
    # Add event handlers before the last line of the class
    # Find the end of the class (before main function or end of file)
    main_marker = '\ndef main():'
    if main_marker in content:
        content = content.replace(main_marker, event_handlers + '\n' + main_marker)
    else:
        # Add at end of file
        content += event_handlers
    
    # Modify validate_all to use polytopic features
    validate_all_marker = 'def validate_all(self) -> Dict:'
    if validate_all_marker in content:
        # Find the return statement in validate_all
        validate_start = content.find(validate_all_marker)
        return_marker = 'return {'
        return_pos = content.find(return_marker, validate_start)
        
        if return_pos != -1:
            # Add polytopic calls before return
            polytopic_calls = '''
        
        # Polytopic Integration: Record patterns and optimize
        self._record_validation_pattern(self.errors)
        self._optimize_validation(result)
        
        # Publish validation completed event
        self.message_bus.publish(Message(
            sender='DictStructureValidator',
            recipient='ALL',
            message_type=MessageType.VALIDATION_COMPLETED,
            priority=MessagePriority.MEDIUM,
            payload={
                'validator': 'dict_structure',
                'total_errors': result['total_errors'],
                'by_severity': result['by_severity']
            }
        ))
        
        '''
            # Insert before return
            content = content[:return_pos] + polytopic_calls + content[return_pos:]
    
    # Save the integrated version
    with open(validator_path, 'w') as f:
        f.write(content)
    
    print("✅ Successfully integrated polytopic features into dict_structure_validator.py")
    print("   - Message bus integration")
    print("   - Pattern recognition")
    print("   - Correlation engine")
    print("   - Optimizer")
    print("   - Adaptive prompts")
    print("   - Dimension tracking")
    print("   - Event subscriptions")

if __name__ == '__main__':
    integrate_dict_validator()