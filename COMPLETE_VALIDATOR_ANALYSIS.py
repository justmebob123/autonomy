"""
COMPLETE VALIDATOR ANALYSIS
Examine every single validator in detail - no shortcuts, no assumptions.
"""

import sys
sys.path.insert(0, '.')
from pathlib import Path
import ast
import inspect

def analyze_validator_file(filepath):
    """Deep analysis of a validator file."""
    print(f"\n{'='*80}")
    print(f"ANALYZING: {filepath}")
    print(f"{'='*80}")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Parse AST
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"❌ SYNTAX ERROR: {e}")
        return None
    
    # Find all classes
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    
    # Find all functions
    functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    
    # Find imports
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                imports.append(f"{module}.{alias.name}")
    
    print(f"\n📊 STRUCTURE:")
    print(f"   Lines: {len(content.split(chr(10)))}")
    print(f"   Classes: {len(classes)}")
    print(f"   Functions: {len(functions)}")
    print(f"   Imports: {len(imports)}")
    
    # Analyze each class
    for cls in classes:
        print(f"\n🔍 CLASS: {cls.name}")
        
        # Find __init__
        init_method = None
        methods = []
        for item in cls.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)
                if item.name == '__init__':
                    init_method = item
        
        print(f"   Methods: {len(methods)}")
        print(f"   Method names: {', '.join(methods[:10])}")
        if len(methods) > 10:
            print(f"   ... and {len(methods) - 10} more")
        
        # Analyze __init__ parameters
        if init_method:
            params = [arg.arg for arg in init_method.args.args if arg.arg != 'self']
            print(f"   __init__ params: {params}")
            
            # Find what's assigned in __init__
            assignments = []
            for node in ast.walk(init_method):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Attribute):
                            if isinstance(target.value, ast.Name) and target.value.id == 'self':
                                assignments.append(target.attr)
            
            print(f"   Instance variables: {len(assignments)}")
            print(f"   Variables: {', '.join(assignments[:10])}")
            if len(assignments) > 10:
                print(f"   ... and {len(assignments) - 10} more")
    
    # Check for polytopic integration
    print(f"\n🔌 POLYTOPIC INTEGRATION CHECK:")
    has_message_bus = 'MessageBus' in content or 'message_bus' in content
    has_pattern_rec = 'PatternRecognition' in content or 'pattern_recognition' in content
    has_correlation = 'CorrelationEngine' in content or 'correlation_engine' in content
    has_optimizer = 'Optimizer' in content or 'optimizer' in content
    has_adaptive = 'AdaptivePrompt' in content or 'adaptive_prompt' in content
    has_dimensional = 'DimensionalSpace' in content or 'dimensional_space' in content
    
    score = sum([has_message_bus, has_pattern_rec, has_correlation, has_optimizer, has_adaptive, has_dimensional])
    
    print(f"   Message Bus: {'✅' if has_message_bus else '❌'}")
    print(f"   Pattern Recognition: {'✅' if has_pattern_rec else '❌'}")
    print(f"   Correlation Engine: {'✅' if has_correlation else '❌'}")
    print(f"   Optimizer: {'✅' if has_optimizer else '❌'}")
    print(f"   Adaptive Prompts: {'✅' if has_adaptive else '❌'}")
    print(f"   Dimensional Space: {'✅' if has_dimensional else '❌'}")
    print(f"   SCORE: {score}/6 ({score/6*100:.1f}%)")
    
    # Check for main validation method
    print(f"\n🎯 VALIDATION METHODS:")
    validation_methods = [m for m in methods if 'validate' in m.lower()]
    print(f"   Found: {', '.join(validation_methods)}")
    
    return {
        'filepath': filepath,
        'lines': len(content.split('\n')),
        'classes': [cls.name for cls in classes],
        'methods': methods,
        'imports': imports,
        'polytopic_score': score,
        'validation_methods': validation_methods,
        'has_message_bus': has_message_bus,
        'has_pattern_rec': has_pattern_rec,
        'has_correlation': has_correlation,
        'has_optimizer': has_optimizer,
        'has_adaptive': has_adaptive,
        'has_dimensional': has_dimensional,
    }

def main():
    """Analyze all validators."""
    
    validators = [
        'pipeline/analysis/type_usage_validator.py',
        'pipeline/analysis/method_existence_validator.py',
        'pipeline/analysis/method_signature_validator.py',
        'pipeline/analysis/function_call_validator.py',
        'pipeline/analysis/enum_attribute_validator.py',
        'pipeline/analysis/dict_structure_validator.py',
        'bin/validators/keyword_argument_validator.py',
        'bin/validators/strict_method_validator.py',
        'pipeline/syntax_validator.py',
        'pipeline/tool_validator.py',
        'pipeline/validation/filename_validator.py',
        'pipeline/analysis/architecture_validator.py',
        'pipeline/analysis/validator_coordinator.py',
    ]
    
    results = []
    
    for validator in validators:
        if Path(validator).exists():
            result = analyze_validator_file(validator)
            if result:
                results.append(result)
        else:
            print(f"\n⚠️  FILE NOT FOUND: {validator}")
    
    # Summary
    print(f"\n{'='*80}")
    print("COMPLETE SUMMARY")
    print(f"{'='*80}")
    
    print(f"\nTotal validators analyzed: {len(results)}")
    
    print(f"\n📊 POLYTOPIC INTEGRATION SCORES:")
    for result in sorted(results, key=lambda x: x['polytopic_score'], reverse=True):
        score = result['polytopic_score']
        name = Path(result['filepath']).name
        print(f"   {score}/6 ({score/6*100:5.1f}%) - {name}")
    
    avg_score = sum(r['polytopic_score'] for r in results) / len(results) if results else 0
    print(f"\n   AVERAGE: {avg_score:.2f}/6 ({avg_score/6*100:.1f}%)")
    
    print(f"\n🎯 VALIDATORS NEEDING INTEGRATION:")
    for result in sorted(results, key=lambda x: x['polytopic_score']):
        if result['polytopic_score'] < 6:
            name = Path(result['filepath']).name
            missing = 6 - result['polytopic_score']
            print(f"   {name}: {missing} features missing")
    
    # Save detailed report
    with open('COMPLETE_VALIDATOR_ANALYSIS.md', 'w') as f:
        f.write("# Complete Validator Analysis\n\n")
        f.write(f"**Total Validators:** {len(results)}\n\n")
        f.write(f"**Average Polytopic Score:** {avg_score:.2f}/6 ({avg_score/6*100:.1f}%)\n\n")
        
        f.write("## Detailed Analysis\n\n")
        
        for result in sorted(results, key=lambda x: x['polytopic_score'], reverse=True):
            name = Path(result['filepath']).name
            f.write(f"### {name}\n\n")
            f.write(f"- **File:** `{result['filepath']}`\n")
            f.write(f"- **Lines:** {result['lines']}\n")
            f.write(f"- **Classes:** {', '.join(result['classes'])}\n")
            f.write(f"- **Validation Methods:** {', '.join(result['validation_methods'])}\n")
            f.write(f"- **Polytopic Score:** {result['polytopic_score']}/6\n\n")
            
            f.write("**Integration Status:**\n")
            f.write(f"- Message Bus: {'✅' if result['has_message_bus'] else '❌'}\n")
            f.write(f"- Pattern Recognition: {'✅' if result['has_pattern_rec'] else '❌'}\n")
            f.write(f"- Correlation Engine: {'✅' if result['has_correlation'] else '❌'}\n")
            f.write(f"- Optimizer: {'✅' if result['has_optimizer'] else '❌'}\n")
            f.write(f"- Adaptive Prompts: {'✅' if result['has_adaptive'] else '❌'}\n")
            f.write(f"- Dimensional Space: {'✅' if result['has_dimensional'] else '❌'}\n\n")
    
    print(f"\n✅ Detailed report saved to COMPLETE_VALIDATOR_ANALYSIS.md")

if __name__ == '__main__':
    main()