"""
Run all validation tools and collect comprehensive results.
"""

import sys
sys.path.insert(0, '.')
import subprocess
from pathlib import Path

def run_validator(name, command):
    """Run a validator and return results."""
    print(f"\n{'='*80}")
    print(f"Running: {name}")
    print(f"{'='*80}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return {
            'name': name,
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'success': result.returncode == 0
        }
    except Exception as e:
        print(f"ERROR: {e}")
        return {
            'name': name,
            'exit_code': -1,
            'error': str(e),
            'success': False
        }

def main():
    """Run all validators."""
    
    validators = [
        ("Type Usage Validator", "python pipeline/analysis/type_usage_validator.py ."),
        ("Method Existence Validator", "python pipeline/analysis/method_existence_validator.py ."),
        ("Method Signature Validator", "python pipeline/analysis/method_signature_validator.py ."),
        ("Function Call Validator", "python pipeline/analysis/function_call_validator.py ."),
        ("Enum Attribute Validator", "python pipeline/analysis/enum_attribute_validator.py ."),
        ("Keyword Argument Validator", "python bin/validators/keyword_argument_validator.py ."),
        ("Dict Structure Validator", "python -c &quot;import sys; sys.path.insert(0, '.'); from pipeline.analysis.dict_structure_validator import DictStructureValidator; v = DictStructureValidator('.'); r = v.validate_all(); print(f'Total: {r[\\&quot;total_errors\\&quot;]} (High: {r[\\&quot;by_severity\\&quot;][\\&quot;high\\&quot;]}, Low: {r[\\&quot;by_severity\\&quot;][\\&quot;low\\&quot;]})')&quot;"),
        ("Strict Method Validator", "python bin/validators/strict_method_validator.py ."),
        ("Syntax Validator", "python pipeline/syntax_validator.py ."),
    ]
    
    results = []
    
    for name, command in validators:
        result = run_validator(name, command)
        results.append(result)
    
    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} - {result['name']}")
    
    # Save detailed report
    with open('COMPLETE_VALIDATION_REPORT.md', 'w') as f:
        f.write("# Complete Validation Report\n\n")
        f.write("## Summary\n\n")
        
        passed = sum(1 for r in results if r['success'])
        total = len(results)
        
        f.write(f"**Total Validators:** {total}\n")
        f.write(f"**Passed:** {passed}\n")
        f.write(f"**Failed:** {total - passed}\n\n")
        
        f.write("## Detailed Results\n\n")
        
        for result in results:
            f.write(f"### {result['name']}\n\n")
            f.write(f"**Status:** {'✅ PASS' if result['success'] else '❌ FAIL'}\n\n")
            
            if 'stdout' in result and result['stdout']:
                f.write("**Output:**\n```\n")
                f.write(result['stdout'][:1000])  # Limit output
                if len(result['stdout']) > 1000:
                    f.write("\n... (truncated)")
                f.write("\n```\n\n")
            
            if 'stderr' in result and result['stderr']:
                f.write("**Errors:**\n```\n")
                f.write(result['stderr'][:1000])
                if len(result['stderr']) > 1000:
                    f.write("\n... (truncated)")
                f.write("\n```\n\n")
            
            if 'error' in result:
                f.write(f"**Error:** {result['error']}\n\n")
    
    print("\n✅ Complete report saved to COMPLETE_VALIDATION_REPORT.md")

if __name__ == '__main__':
    main()