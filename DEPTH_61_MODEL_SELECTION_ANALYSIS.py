#!/usr/bin/env python3
"""
Depth-61 Analysis: Model Selection Issue
The model qwen2.5-coder:32b exists on ollama02 but planning phase is trying to use ollama01
"""

import ast
import re
from pathlib import Path
from collections import defaultdict

class ModelSelectionAnalyzer:
    def __init__(self):
        self.findings = []
        
    def analyze_config(self):
        """Analyze config.py for model assignments"""
        print("=" * 80)
        print("DEPTH-61 ANALYSIS: Model Selection Issue")
        print("=" * 80)
        print()
        
        config_path = Path("pipeline/config.py")
        content = config_path.read_text()
        
        print("## 1. CONFIGURED MODEL ASSIGNMENTS")
        print("-" * 80)
        
        # Extract model_assignments
        assignments = {}
        in_assignments = False
        for line in content.split('\n'):
            if 'model_assignments:' in line:
                in_assignments = True
            elif in_assignments:
                if '})' in line:
                    break
                match = re.search(r'"(\w+)":\s*\("([^"]+)",\s*"([^"]+)"\)', line)
                if match:
                    phase, model, host = match.groups()
                    assignments[phase] = (model, host)
                    print(f"  {phase:20s} -> {model:25s} on {host}")
        
        print()
        print("## 2. ACTUAL MODEL AVAILABILITY")
        print("-" * 80)
        
        # From user's curl output
        ollama01_models = [
            "qwen2.5:14b",
            "qwen2.5-coder:7b",
            "phi4:latest",
            "llama3.2:3b",
            "llama3.1:latest",
            "deepseek-v2:latest",
            "functiongemma:latest",
            "phi3:mini"
        ]
        
        ollama02_models = [
            "qwen2.5:32b",
            "llama3.1:70b",
            "qwen2.5-coder:32b",  # ✓ EXISTS HERE
            "qwen2.5-coder:14b",
            "codellama:13b",
            "deepseek-coder-v2:latest",
            "deepseek-coder-v2:16b",
            "phi4:latest",
            "qwen2.5:14b",
            "llama3.2:3b",
            "llama3.1:latest",
            "deepseek-v2:latest",
            "deepseek-ocr:latest",
            "qwen3-coder:30b",
            "gpt-oss:120b",
            "functiongemma:latest"
        ]
        
        print("ollama01.thiscluster.net:")
        for model in ollama01_models:
            print(f"  ✓ {model}")
        
        print()
        print("ollama02.thiscluster.net:")
        for model in ollama02_models:
            marker = "  🎯" if "qwen2.5-coder:32b" in model else "  ✓"
            print(f"{marker} {model}")
        
        print()
        print("## 3. PROBLEM IDENTIFICATION")
        print("-" * 80)
        
        # Check for mismatches
        problems = []
        for phase, (model, host) in assignments.items():
            host_short = host.split('.')[0]
            
            if host_short == "ollama01":
                available = ollama01_models
            else:
                available = ollama02_models
            
            # Check if model exists
            model_exists = any(model in m for m in available)
            
            if not model_exists:
                problems.append({
                    'phase': phase,
                    'model': model,
                    'configured_host': host,
                    'available': available
                })
                print(f"❌ PROBLEM: {phase} phase")
                print(f"   Configured: {model} on {host}")
                print(f"   Status: Model NOT available on {host_short}")
                print()
        
        print("## 4. ROOT CAUSE")
        print("-" * 80)
        print("""
The configuration in pipeline/config.py line 78 specifies:
    "planning": ("qwen2.5-coder:32b", "ollama01.thiscluster.net")

But qwen2.5-coder:32b is ONLY available on ollama02, not ollama01!

The model exists and works fine on ollama02 (as used by coding, qa, debugging phases).
The planning phase is simply configured to use the wrong server.
""")
        
        print("## 5. CALL STACK TRACE")
        print("-" * 80)
        print("""
1. run.py calls PhaseCoordinator.run()
2. Coordinator determines next action -> planning phase
3. Planning phase calls chat_with_history()
4. chat_with_history() gets model assignment from config
5. Config returns ("qwen2.5-coder:32b", "ollama01.thiscluster.net")
6. Client tries to call ollama01 with qwen2.5-coder:32b
7. ollama01 returns 404 - model not found
8. No fallback attempted because preferred host is "available"
9. Loop continues with same error
""")
        
        print("## 6. WHY FALLBACK DOESN'T WORK")
        print("-" * 80)
        print("""
In pipeline/client.py, get_model_for_task():
- Line ~65: Checks if preferred_host is in available_models
- ollama01 IS available (has 8 models)
- So it tries to find qwen2.5-coder:32b on ollama01
- Model not found on ollama01
- Tries other hosts for same model
- Should find it on ollama02!

BUT: There may be an issue with the model matching logic or
the fallback is not being triggered properly.
""")
        
        print("## 7. SOLUTION")
        print("-" * 80)
        print("""
IMMEDIATE FIX: Change line 78 in pipeline/config.py

BEFORE:
    "planning": ("qwen2.5-coder:32b", "ollama01.thiscluster.net"),

AFTER:
    "planning": ("qwen2.5-coder:32b", "ollama02.thiscluster.net"),

This aligns planning with the other phases that successfully use this model.

DEEPER FIX: Investigate why the fallback logic in client.py doesn't
automatically try ollama02 when the model isn't found on ollama01.
""")
        
        print("## 8. VERIFICATION NEEDED")
        print("-" * 80)
        print("""
After fixing config.py, verify:
1. Planning phase uses ollama02
2. Model is found and works
3. Fallback logic works for future cases
4. All phases can access their assigned models
""")
        
        print()
        print("=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)

if __name__ == "__main__":
    analyzer = ModelSelectionAnalyzer()
    analyzer.analyze_config()