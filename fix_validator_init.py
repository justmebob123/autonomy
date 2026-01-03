"""
Fix validators where polytopic integration was added to wrong class.
"""

import sys
sys.path.insert(0, '.')
from pathlib import Path
import re

POLYTOPIC_INIT = '''
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

def fix_validator(filepath, main_class_name, validator_name):
    """Fix a validator by adding polytopic init to the correct class."""
    
    print(f"\n{'='*80}")
    print(f"FIXING: {filepath}")
    print(f"Main class: {main_class_name}")
    print(f"{'='*80}")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if already has polytopic in main class
    class_start = content.find(f'class {main_class_name}:')
    if class_start == -1:
        print(f"❌ Could not find class {main_class_name}")
        return False
    
    # Find the __init__ of the main class
    init_start = content.find('def __init__(self', class_start)
    if init_start == -1:
        print(f"❌ Could not find __init__ in {main_class_name}")
        return False
    
    # Check if this __init__ already has polytopic
    next_def = content.find('\n    def ', init_start + 1)
    init_section = content[init_start:next_def] if next_def != -1 else content[init_start:]
    
    if 'self.message_bus' in init_section:
        print(f"✅ Already has polytopic integration in correct location")
        return True
    
    # Find where to insert (after last self.xxx = line in __init__)
    lines = init_section.split('\n')
    last_assignment_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('self.') and '=' in line:
            last_assignment_idx = i
    
    if last_assignment_idx == -1:
        print(f"❌ Could not find assignment in __init__")
        return False
    
    # Insert polytopic code after last assignment
    insert_line = lines[last_assignment_idx]
    polytopic_code = POLYTOPIC_INIT.format(validator_name=validator_name)
    
    content = content.replace(insert_line, insert_line + polytopic_code)
    
    # Save
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"✅ Added polytopic integration to {main_class_name}.__init__")
    return True

def main():
    """Fix all validators."""
    
    validators = [
        ('pipeline/analysis/type_usage_validator.py', 'TypeUsageValidator', 'TypeUsageValidator'),
        ('pipeline/analysis/method_signature_validator.py', 'MethodSignatureValidator', 'MethodSignatureValidator'),
        ('pipeline/analysis/enum_attribute_validator.py', 'EnumAttributeValidator', 'EnumAttributeValidator'),
        ('bin/validators/keyword_argument_validator.py', 'KeywordArgumentValidator', 'KeywordArgumentValidator'),
    ]
    
    for filepath, main_class, validator_name in validators:
        fix_validator(filepath, main_class, validator_name)
    
    print(f"\n{'='*80}")
    print("FIXES COMPLETE")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()