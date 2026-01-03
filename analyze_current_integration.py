"""
Analyze current polytopic integration status.
Understand what validation tools are integrated and what's missing.
"""

import sys
sys.path.insert(0, '.')
from pathlib import Path
import ast
import re

def analyze_phase_integration(phase_file):
    """Analyze a phase file for polytopic integration."""
    
    with open(phase_file, 'r') as f:
        content = f.read()
    
    integration_features = {
        'message_bus': bool(re.search(r'self\._publish_message|MessageBus', content)),
        'adaptive_prompts': bool(re.search(r'self\.adaptive_prompts|AdaptivePrompts', content)),
        'pattern_recognition': bool(re.search(r'self\.pattern_recognition|PatternRecognition', content)),
        'correlation_engine': bool(re.search(r'self\.correlation_engine|CorrelationEngine', content)),
        'optimizer': bool(re.search(r'self\.optimizer|Optimizer', content)),
        'dimension_tracking': bool(re.search(r'self\.dimension_tracker|DimensionTracker', content)),
        'event_subscriptions': bool(re.search(r'subscribe|on_message', content)),
        'validation_integration': bool(re.search(r'validator|validate', content, re.IGNORECASE)),
    }
    
    return integration_features

def analyze_validation_tools():
    """Analyze validation tools for integration opportunities."""
    
    validators = [
        'pipeline/analysis/dict_structure_validator.py',
        'bin/validators/keyword_argument_validator.py',
        'pipeline/analysis/type_usage_validator.py',
        'pipeline/analysis/method_existence_validator.py',
        'pipeline/analysis/method_signature_validator.py',
        'pipeline/analysis/function_call_validator.py',
        'pipeline/analysis/enum_attribute_validator.py',
        'bin/validators/strict_method_validator.py',
    ]
    
    validator_info = {}
    
    for validator_path in validators:
        if not Path(validator_path).exists():
            continue
            
        with open(validator_path, 'r') as f:
            content = f.read()
        
        validator_info[validator_path] = {
            'has_message_bus': bool(re.search(r'MessageBus|message_bus', content)),
            'has_learning': bool(re.search(r'pattern_recognition|correlation|optimizer', content)),
            'has_dimensions': bool(re.search(r'dimension|DimensionTracker', content)),
            'has_adaptive': bool(re.search(r'adaptive_prompts|AdaptivePrompts', content)),
            'lines': len(content.split('\n')),
        }
    
    return validator_info

def main():
    """Analyze current integration status."""
    
    print("="*80)
    print("CURRENT POLYTOPIC INTEGRATION ANALYSIS")
    print("="*80)
    print()
    
    # Analyze phases
    print("1. PHASE INTEGRATION STATUS")
    print("-"*80)
    
    phase_files = list(Path('pipeline/phases').glob('*.py'))
    phase_files = [f for f in phase_files if f.name not in ['__init__.py', 'loop_detection_mixin.py']]
    
    phase_integration = {}
    for phase_file in sorted(phase_files):
        features = analyze_phase_integration(phase_file)
        phase_integration[phase_file.name] = features
        
        score = sum(features.values())
        print(f"\n{phase_file.name}: {score}/8")
        for feature, present in features.items():
            status = "✅" if present else "❌"
            print(f"  {status} {feature}")
    
    print()
    print("="*80)
    print("2. VALIDATION TOOL INTEGRATION STATUS")
    print("-"*80)
    
    validator_info = analyze_validation_tools()
    
    for validator_path, info in validator_info.items():
        print(f"\n{Path(validator_path).name}:")
        print(f"  Lines: {info['lines']}")
        print(f"  Message Bus: {'✅' if info['has_message_bus'] else '❌'}")
        print(f"  Learning Systems: {'✅' if info['has_learning'] else '❌'}")
        print(f"  Dimension Tracking: {'✅' if info['has_dimensions'] else '❌'}")
        print(f"  Adaptive Prompts: {'✅' if info['has_adaptive'] else '❌'}")
    
    print()
    print("="*80)
    print("3. INTEGRATION OPPORTUNITIES")
    print("-"*80)
    print()
    
    # Calculate totals
    total_phases = len(phase_integration)
    total_validators = len(validator_info)
    
    phase_scores = {name: sum(features.values()) for name, features in phase_integration.items()}
    avg_phase_score = sum(phase_scores.values()) / len(phase_scores) if phase_scores else 0
    
    validator_scores = {
        name: sum([
            info['has_message_bus'],
            info['has_learning'],
            info['has_dimensions'],
            info['has_adaptive']
        ])
        for name, info in validator_info.items()
    }
    avg_validator_score = sum(validator_scores.values()) / len(validator_scores) if validator_scores else 0
    
    print(f"Phase Integration: {avg_phase_score:.1f}/8 average ({avg_phase_score/8*100:.1f}%)")
    print(f"Validator Integration: {avg_validator_score:.1f}/4 average ({avg_validator_score/4*100:.1f}%)")
    print()
    
    print("KEY OPPORTUNITIES:")
    print()
    print("1. INTEGRATE VALIDATORS INTO PHASES")
    print("   - Phases should use validators during execution")
    print("   - Real-time validation of code changes")
    print("   - Validation results feed into learning systems")
    print()
    
    print("2. ADD POLYTOPIC FEATURES TO VALIDATORS")
    print("   - Message bus for validation events")
    print("   - Pattern recognition for common errors")
    print("   - Correlation of validation results")
    print("   - Adaptive validation based on patterns")
    print()
    
    print("3. CREATE VALIDATION ORCHESTRATION")
    print("   - Coordinate multiple validators")
    print("   - Cross-validate results")
    print("   - Learn from validation patterns")
    print("   - Provide validation insights to phases")
    print()
    
    # Save report
    with open('INTEGRATION_STATUS_ANALYSIS.md', 'w') as f:
        f.write("# Current Polytopic Integration Status\n\n")
        f.write("## Phase Integration\n\n")
        
        for name, features in sorted(phase_integration.items()):
            score = sum(features.values())
            f.write(f"### {name} ({score}/8)\n\n")
            for feature, present in features.items():
                status = "✅" if present else "❌"
                f.write(f"- {status} {feature}\n")
            f.write("\n")
        
        f.write("## Validator Integration\n\n")
        
        for validator_path, info in validator_info.items():
            f.write(f"### {Path(validator_path).name}\n\n")
            f.write(f"- Lines: {info['lines']}\n")
            f.write(f"- Message Bus: {'✅' if info['has_message_bus'] else '❌'}\n")
            f.write(f"- Learning Systems: {'✅' if info['has_learning'] else '❌'}\n")
            f.write(f"- Dimension Tracking: {'✅' if info['has_dimensions'] else '❌'}\n")
            f.write(f"- Adaptive Prompts: {'✅' if info['has_adaptive'] else '❌'}\n")
            f.write("\n")
        
        f.write("## Summary\n\n")
        f.write(f"- **Phase Integration:** {avg_phase_score:.1f}/8 average ({avg_phase_score/8*100:.1f}%)\n")
        f.write(f"- **Validator Integration:** {avg_validator_score:.1f}/4 average ({avg_validator_score/4*100:.1f}%)\n")
        f.write("\n")
        
        f.write("## Key Opportunities\n\n")
        f.write("1. Integrate validators into phases for real-time validation\n")
        f.write("2. Add polytopic features to validators\n")
        f.write("3. Create validation orchestration layer\n")
        f.write("4. Enable learning from validation patterns\n")
    
    print("✅ Report saved to INTEGRATION_STATUS_ANALYSIS.md")

if __name__ == '__main__':
    main()