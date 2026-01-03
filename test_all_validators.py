"""
Test ALL validators to ensure polytopic integration works correctly.
"""

import sys
sys.path.insert(0, '.')
from pathlib import Path

def test_validator(validator_class, validator_path, *args):
    """Test a single validator."""
    print(f"\n{'='*80}")
    print(f"TESTING: {validator_path}")
    print(f"{'='*80}")
    
    try:
        # Import the validator
        module_path = validator_path.replace('/', '.').replace('.py', '')
        if module_path.startswith('.'):
            module_path = module_path[1:]
        
        # Dynamic import
        parts = module_path.split('.')
        module = __import__(module_path, fromlist=[validator_class])
        ValidatorClass = getattr(module, validator_class)
        
        print(f"✅ Import successful: {validator_class}")
        
        # Create instance
        validator = ValidatorClass(*args)
        print(f"✅ Instance created")
        
        # Check polytopic attributes
        checks = {
            'message_bus': hasattr(validator, 'message_bus'),
            'pattern_recognition': hasattr(validator, 'pattern_recognition'),
            'correlation_engine': hasattr(validator, 'correlation_engine'),
            'optimizer': hasattr(validator, 'optimizer'),
            'adaptive_prompts': hasattr(validator, 'adaptive_prompts'),
            'dimensional_space': hasattr(validator, 'dimensional_space'),
            'validation_count': hasattr(validator, 'validation_count'),
            'validator_name': hasattr(validator, 'validator_name'),
        }
        
        score = sum(checks.values())
        print(f"\n📊 Polytopic Integration: {score}/8")
        for attr, present in checks.items():
            status = "✅" if present else "❌"
            print(f"   {status} {attr}")
        
        # Check helper methods
        helper_methods = [
            '_publish_validation_event',
            '_record_validation_pattern',
            '_optimize_validation',
            '_get_error_file',
            '_get_error_type',
            '_get_severity',
            '_get_error_message',
        ]
        
        print(f"\n🔧 Helper Methods:")
        for method in helper_methods:
            has_method = hasattr(validator, method)
            status = "✅" if has_method else "❌"
            print(f"   {status} {method}")
        
        return score == 8
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Test all validators."""
    
    validators = [
        ('TypeUsageValidator', 'pipeline/analysis/type_usage_validator.py', '.', None, None),
        ('MethodExistenceValidator', 'pipeline/analysis/method_existence_validator.py', '.', None, None),
        ('MethodSignatureValidator', 'pipeline/analysis/method_signature_validator.py', '.', None),
        ('FunctionCallValidator', 'pipeline/analysis/function_call_validator.py', '.', None, None),
        ('EnumAttributeValidator', 'pipeline/analysis/enum_attribute_validator.py', '.', None),
        ('DictStructureValidator', 'pipeline/analysis/dict_structure_validator.py', '.'),
        ('KeywordArgumentValidator', 'bin/validators/keyword_argument_validator.py', '.', None),
        ('ValidatorCoordinator', 'pipeline/analysis/validator_coordinator.py', '.', None, None),
    ]
    
    results = []
    
    for validator_info in validators:
        validator_class = validator_info[0]
        validator_path = validator_info[1]
        args = validator_info[2:]
        
        success = test_validator(validator_class, validator_path, *args)
        results.append((validator_class, success))
    
    # Summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n✅ Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    for validator_class, success in results:
        status = "✅" if success else "❌"
        print(f"   {status} {validator_class}")
    
    if passed == total:
        print(f"\n🎉 ALL VALIDATORS PASSED!")
    else:
        print(f"\n⚠️  {total - passed} validators need attention")

if __name__ == '__main__':
    main()