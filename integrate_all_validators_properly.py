"""
COMPLETE VALIDATOR INTEGRATION - NO SHORTCUTS
Integrate ALL 12 validators with full polytopic features.
"""

import sys
sys.path.insert(0, '.')
from pathlib import Path
import re

# Correct imports based on actual module structure
POLYTOPIC_IMPORTS = '''
# Polytopic Integration Imports
from pipeline.messaging.message_bus import MessageBus, Message, MessageType, MessagePriority
from pipeline.pattern_recognition import PatternRecognitionSystem
from pipeline.correlation_engine import CorrelationEngine
from pipeline.analytics.optimizer import OptimizationEngine
from pipeline.adaptive_prompts import AdaptivePromptSystem
from pipeline.polytopic.dimensional_space import DimensionalSpace
'''

def get_init_integration(validator_name):
    """Get the __init__ integration code for a validator."""
    return f'''
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
        self.validator_name = '{validator_name}'
'''

def get_helper_methods():
    """Get helper methods for polytopic integration."""
    return '''
    
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
'''

def integrate_validator(filepath, validator_name):
    """Integrate a single validator with polytopic features."""
    
    print(f"\n{'='*80}")
    print(f"INTEGRATING: {filepath}")
    print(f"{'='*80}")
    
    if not Path(filepath).exists():
        print(f"❌ File not found: {filepath}")
        return False
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if already integrated
    if 'MessageBus' in content and 'PatternRecognitionSystem' in content and 'self.validation_count' in content:
        print(f"✅ Already fully integrated")
        return True
    
    # Backup original
    backup_path = Path(filepath).with_suffix('.py.backup')
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"📦 Backup created: {backup_path}")
    
    # Add imports if not present
    if 'from pipeline.messaging.message_bus import' not in content:
        # Find the last import
        import_lines = []
        for line in content.split('\n'):
            if line.startswith('import ') or line.startswith('from '):
                import_lines.append(line)
        
        if import_lines:
            last_import = import_lines[-1]
            content = content.replace(last_import, last_import + '\n' + POLYTOPIC_IMPORTS)
            print("✅ Added polytopic imports")
    
    # Find the main validator class
    class_match = re.search(r'class (\w+Validator):', content)
    if not class_match:
        print("❌ Could not find validator class")
        return False
    
    class_name = class_match.group(1)
    print(f"📝 Found class: {class_name}")
    
    # Find __init__ method
    init_pattern = r'(    def __init__\(self[^)]*\):.*?)((?=\n    def )|(?=\nclass )|$)'
    init_match = re.search(init_pattern, content, re.DOTALL)
    
    if not init_match:
        print("❌ Could not find __init__ method")
        return False
    
    init_content = init_match.group(1)
    
    # Add polytopic initialization if not present
    if 'self.message_bus' not in init_content:
        # Find the last line of __init__ (before next method or class)
        init_end = init_match.end(1)
        integration_code = get_init_integration(validator_name)
        content = content[:init_end] + integration_code + content[init_end:]
        print("✅ Added polytopic initialization to __init__")
    
    # Add helper methods if not present
    if '_publish_validation_event' not in content:
        # Find the end of the class (before main() or end of file)
        main_match = re.search(r'\ndef main\(\):', content)
        if main_match:
            insert_pos = main_match.start()
        else:
            # Find last method of the class
            class_start = content.find(f'class {class_name}:')
            next_class = content.find('\nclass ', class_start + 1)
            if next_class != -1:
                insert_pos = next_class
            else:
                insert_pos = len(content)
        
        helper_methods = get_helper_methods()
        content = content[:insert_pos] + helper_methods + '\n' + content[insert_pos:]
        print("✅ Added helper methods")
    
    # Find validate_all method and add polytopic calls
    validate_pattern = r'(    def validate_all\(self\)[^:]*:.*?)(return \{)'
    validate_match = re.search(validate_pattern, content, re.DOTALL)
    
    if validate_match:
        # Add polytopic calls before return
        polytopic_calls = '''
        
        # Polytopic Integration: Record patterns and optimize
        self.validation_count += 1
        self._record_validation_pattern(self.errors if hasattr(self, 'errors') else [])
        self._optimize_validation(result)
        
        # Publish validation completed event
        self._publish_validation_event('validation_completed', {
            'total_errors': result.get('total_errors', 0),
            'validation_count': self.validation_count
        })
        
        '''
        
        return_pos = validate_match.start(2)
        content = content[:return_pos] + polytopic_calls + content[return_pos:]
        print("✅ Added polytopic calls to validate_all")
    
    # Save integrated version
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"✅ Successfully integrated {validator_name}")
    return True

def main():
    """Integrate all validators."""
    
    validators = [
        ('pipeline/analysis/type_usage_validator.py', 'TypeUsageValidator'),
        ('pipeline/analysis/method_existence_validator.py', 'MethodExistenceValidator'),
        ('pipeline/analysis/method_signature_validator.py', 'MethodSignatureValidator'),
        ('pipeline/analysis/function_call_validator.py', 'FunctionCallValidator'),
        ('pipeline/analysis/enum_attribute_validator.py', 'EnumAttributeValidator'),
        ('bin/validators/keyword_argument_validator.py', 'KeywordArgumentValidator'),
        ('bin/validators/strict_method_validator.py', 'StrictMethodValidator'),
        ('pipeline/syntax_validator.py', 'SyntaxValidator'),
        ('pipeline/tool_validator.py', 'ToolValidator'),
        ('pipeline/validation/filename_validator.py', 'FilenameValidator'),
        ('pipeline/analysis/architecture_validator.py', 'ArchitectureValidator'),
        ('pipeline/analysis/validator_coordinator.py', 'ValidatorCoordinator'),
    ]
    
    success_count = 0
    failed = []
    
    for filepath, validator_name in validators:
        try:
            if integrate_validator(filepath, validator_name):
                success_count += 1
            else:
                failed.append(filepath)
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed.append(filepath)
    
    print(f"\n{'='*80}")
    print("INTEGRATION SUMMARY")
    print(f"{'='*80}")
    print(f"\n✅ Successfully integrated: {success_count}/{len(validators)}")
    
    if failed:
        print(f"\n❌ Failed to integrate:")
        for f in failed:
            print(f"   - {f}")
    else:
        print(f"\n🎉 ALL VALIDATORS SUCCESSFULLY INTEGRATED!")
    
    print(f"\n📝 Backups created with .backup extension")
    print(f"   To restore: mv file.py.backup file.py")

if __name__ == '__main__':
    main()