#!/usr/bin/env python3
"""
Debug script to understand the integration_status data structure
"""

import sys
from pathlib import Path

# Add pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.architecture_manager import ArchitectureManager
from pipeline.analysis.code_validation import CodeValidator

def main():
    project_dir = Path("/home/ai/AI/web")
    
    print("=" * 80)
    print("DEBUGGING INTEGRATION STATUS DATA STRUCTURE")
    print("=" * 80)
    
    # Run validation
    validator = CodeValidator(str(project_dir))
    result = validator.validate()
    
    print(f"\nTotal components: {len(result.components)}")
    print(f"Integration status entries: {len(result.integration_status)}")
    
    # Show first few integration status entries
    print("\n" + "=" * 80)
    print("SAMPLE INTEGRATION STATUS ENTRIES")
    print("=" * 80)
    
    for i, (module, status) in enumerate(list(result.integration_status.items())[:5]):
        print(f"\n{i+1}. Module: {module}")
        print(f"   is_integrated: {status.is_integrated}")
        print(f"   unused_classes type: {type(status.unused_classes)}")
        print(f"   unused_classes: {status.unused_classes}")
        
        if hasattr(status, '__dict__'):
            print(f"   All attributes: {status.__dict__.keys()}")

if __name__ == "__main__":
    main()